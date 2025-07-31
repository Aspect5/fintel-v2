# In backend/workflows/dependency_workflow.py
import controlflow as cf
from typing import Dict, Any, List
from .base import BaseWorkflow, WorkflowResult
import time
import logging
import threading
from datetime import datetime
import re
import json

logger = logging.getLogger(__name__)

class DependencyDrivenWorkflow(BaseWorkflow):
    """Workflow with real-time status updates for frontend visualization"""
    
    def __init__(self):
        super().__init__(
            name="dependency_driven_analysis",
            description="Financial analysis with real-time visualization"
        )
        self.workflow_status = {
            'nodes': [],
            'edges': [],
            'current_task': None,
            'start_time': None,
            'status': 'pending'
        }
        self.status_callbacks = []
        self.tool_calls = {}  # Track tool calls by node
    
    def add_status_callback(self, callback):
        """Add callback for status updates"""
        self.status_callbacks.append(callback)
    
    def _update_status(self, update):
        """Update workflow status and notify callbacks"""
        with threading.Lock():
            # Create a new status dict preserving existing data
            new_status = dict(self.workflow_status)
            
            # Special handling for nodes and edges to prevent loss
            if 'nodes' in update and update['nodes']:
                new_status['nodes'] = update['nodes']
            elif 'nodes' not in update and 'nodes' in self.workflow_status:
                # Preserve existing nodes if not in update
                new_status['nodes'] = self.workflow_status['nodes']
                
            if 'edges' in update and update['edges']:
                new_status['edges'] = update['edges']
            elif 'edges' not in update and 'edges' in self.workflow_status:
                # Preserve existing edges if not in update
                new_status['edges'] = self.workflow_status['edges']
            
            # Update other fields
            for key, value in update.items():
                if key not in ['nodes', 'edges']:
                    new_status[key] = value
            
            self.workflow_status = new_status
            
            # Notify callbacks with complete status
            for callback in self.status_callbacks:
                try:
                    callback(new_status.copy())
                except Exception as e:
                    logger.error(f"Status callback error: {e}")
    
    def _get_agents_for_query(self, query: str, provider: str) -> Dict[str, cf.Agent]:
        """Dynamically select agents based on query content"""
        from backend.agents.registry import get_agent_registry
        agent_registry = get_agent_registry()
        agents = {}
        
        # Base agents always included
        agents['coordinator'] = agent_registry.get_agent("FinancialAnalyst", provider)
        
        # Conditionally add agents based on query content
        query_lower = query.lower()
        
        # Enhanced keyword matching for market analysis
        market_keywords = ['market', 'stock', 'price', 'trading', 'invest', 'investment', 'buy', 'sell', 'hold', 'portfolio', 'ticker', 'company', 'earnings', 'revenue', 'profit', 'loss', 'dividend', 'share', 'shares']
        if any(word in query_lower for word in market_keywords):
            agents['market'] = agent_registry.get_agent("MarketAnalyst", provider)
        
        # Enhanced keyword matching for economic analysis
        economic_keywords = ['economy', 'gdp', 'inflation', 'rates', 'interest', 'federal', 'fed', 'economic', 'recession', 'growth', 'employment', 'unemployment', 'monetary', 'fiscal', 'policy']
        if any(word in query_lower for word in economic_keywords):
            agents['economic'] = agent_registry.get_agent("EconomicAnalyst", provider)
        
        # Enhanced keyword matching for risk assessment
        risk_keywords = ['risk', 'volatility', 'beta', 'danger', 'safe', 'safety', 'uncertainty', 'exposure', 'variance', 'standard deviation', 'downside', 'upside', 'potential']
        if any(word in query_lower for word in risk_keywords):
            agents['risk'] = agent_registry.get_agent("RiskAssessment", provider)
        
        # For investment queries, always include market analysis if not already selected
        if any(word in query_lower for word in ['invest', 'investment', 'buy', 'sell', 'should i', 'worth', 'value', 'valuation']) and 'market' not in agents:
            agents['market'] = agent_registry.get_agent("MarketAnalyst", provider)
        
        # For any financial analysis, include at least market analysis
        if 'market' not in agents and any(word in query_lower for word in ['analyze', 'analysis', 'financial', 'finance', 'money']):
            agents['market'] = agent_registry.get_agent("MarketAnalyst", provider)
        
        # Check for custom agents that might be relevant
        for agent_name in agent_registry.get_available_agents():
            if agent_name not in ['FinancialAnalyst', 'MarketAnalyst', 'EconomicAnalyst', "RiskAssessment"]:
                agent_info = agent_registry.get_agent_info(agent_name)
                # Simple keyword matching - could be made more sophisticated
                if any(keyword in query_lower for keyword in agent_info.get('keywords', [])):
                    agents[agent_name.lower()] = agent_registry.get_agent(agent_name, provider)
        
        return agents

    def _initialize_workflow_nodes(self, query: str, agents: Dict[str, cf.Agent]):
        """Initialize workflow nodes for frontend visualization based on selected agents."""
        nodes = [{'id': 'query_input', 'type': 'input', 'position': {'x': 50, 'y': 200}, 
                  'data': {'label': 'User Query', 'details': query, 'status': 'running'}}]
        edges = []
        
        # Calculate positions based on number of agents
        agent_keys = [key for key in agents.keys() if key != 'coordinator']
        num_agents = len(agent_keys)
        
        # Position agents in a grid layout
        agent_positions = {}
        if num_agents == 1:
            agent_positions[agent_keys[0]] = {'x': 350, 'y': 200}
        elif num_agents == 2:
            agent_positions[agent_keys[0]] = {'x': 350, 'y': 100}
            agent_positions[agent_keys[1]] = {'x': 350, 'y': 300}
        elif num_agents >= 3:
            agent_positions[agent_keys[0]] = {'x': 350, 'y': 100}
            agent_positions[agent_keys[1]] = {'x': 350, 'y': 200}
            agent_positions[agent_keys[2]] = {'x': 350, 'y': 300}
        
        # Add nodes for each agent
        for agent_key in agent_keys:
            if agent_key in agent_positions:
                position = agent_positions[agent_key]
                node_id = f'{agent_key}_analysis'
                
                # Set appropriate task description based on agent type
                task_description = ""
                if agent_key == 'market':
                    task_description = "Analyze market data, financial metrics, and trading patterns"
                elif agent_key == 'economic':
                    task_description = "Evaluate economic indicators and macroeconomic factors"
                elif agent_key == 'risk':
                    task_description = "Assess investment risks and volatility factors"
                else:
                    task_description = f"Perform {agent_key} analysis"
                
                # Debug logging for task description
                logger.info(f"Initializing node {node_id} with task description: {task_description}")
                
                nodes.append({
                    'id': node_id, 'type': 'default', 'position': position,
                    'data': {
                        'label': f'{agent_key.title()} Analyst', 
                        'details': task_description,
                        'status': 'pending', 
                        'toolCalls': []
                    }
                })
                edges.append({'id': f'e_{agent_key}', 'source': 'query_input', 'target': node_id, 'animated': False})

        # Add risk node connections if risk assessment is present
        if 'risk' in agents:
            risk_node_id = 'risk_analysis'
            for agent_key in agent_keys:
                if agent_key != 'risk':
                    source_node_id = f'{agent_key}_analysis'
                    edges.append({'id': f'e_{agent_key}_risk', 'source': source_node_id, 'target': risk_node_id, 'animated': False})
        
        # Add final synthesis node
        final_x = 650 if num_agents <= 2 else 650
        final_y = 200 if num_agents == 1 else 200
        nodes.append({'id': 'final_synthesis', 'type': 'output', 'position': {'x': final_x, 'y': final_y}, 
                      'data': {'label': 'Final Report', 'details': 'Synthesize comprehensive investment analysis and recommendations', 'status': 'pending'}})

        # Connect final synthesis to its dependencies
        synthesis_dependencies = [f'{agent_key}_analysis' for agent_key in agent_keys]
        for dep in synthesis_dependencies:
            edges.append({'id': f'e_{dep}_final', 'source': dep, 'target': 'final_synthesis', 'animated': False})
            
        # Update workflow status with nodes and edges
        self.workflow_status.update({
            'nodes': nodes, 
            'edges': edges, 
            'start_time': datetime.now().isoformat(), 
            'query': query,
            'status': 'initializing'
        })
        
        # Log the initialization for debugging
        logger.info(f"Initialized workflow nodes: {len(nodes)} nodes, {len(edges)} edges")
        logger.info(f"Agent keys: {agent_keys}")
        logger.info(f"Node IDs: {[node['id'] for node in nodes]}")
        
        # Update status to notify callbacks
        self._update_status({'initialized': True})
        
    def _extract_ticker_from_query(self, query: str) -> str:
        """Extract ticker symbol from query"""
        # Check for ticker in parentheses
        match = re.search(r'\(([A-Z]{1,5})\)', query)
        if match:
            return match.group(1)
        
        # Common mappings
        mappings = {
            'google': 'GOOG', 'alphabet': 'GOOG',
            'apple': 'AAPL', 'microsoft': 'MSFT',
            'amazon': 'AMZN', 'tesla': 'TSLA',
            'meta': 'META', 'nvidia': 'NVDA'
        }
        
        query_lower = query.lower()
        for company, ticker in mappings.items():
            if company in query_lower:
                return ticker
        
        # Look for uppercase ticker
        tickers = re.findall(r' [A-Z]{2,5} ', query)
        if tickers:
            return tickers[0]
        
        return None
        
    def execute(self, query: str, provider: str = "openai", **kwargs) -> WorkflowResult:
        """Execute workflow with real-time status updates"""
        start_time = time.time()
        
        # Get agents for the query
        agents = self._get_agents_for_query(query, provider)
        logger.info(f"Selected agents: {list(agents.keys())}")
        for agent_key, agent in agents.items():
            logger.info(f"Agent {agent_key}: {agent}")
        
        # CRITICAL FIX: Initialize nodes BEFORE starting any async operations
        self._initialize_workflow_nodes(query, agents)
        
        # Ensure initial status is properly set
        initial_status = {
            'workflow_id': kwargs.get('workflow_id'),  # Get workflow_id if passed
            'nodes': self.workflow_status['nodes'].copy(),
            'edges': self.workflow_status['edges'].copy(),
            'status': 'initializing',
            'query': query,
            'start_time': self.workflow_status['start_time']
        }
        
        # Update the workflow status with initial state
        self._update_status(initial_status)
        
        logger.info(f"Executing workflow for query: {query} with agents: {list(agents.keys())}")
        logger.info(f"Initial nodes: {len(self.workflow_status['nodes'])}, edges: {len(self.workflow_status['edges'])}")
        
        try:
            # Continue with the rest of the execution...
            from backend.utils.observability import FintelEventHandler
            
            event_handler = FintelEventHandler()
            
            # Store agent results for final report
            agent_results = {}
            
            with cf.Flow(name="financial_analysis_flow") as flow:
                self._update_node_status('query_input', 'completed')
                
                ticker = self._extract_ticker_from_query(query)
                ticker_hint = f"The ticker symbol is: {ticker}" if ticker else "Extract the ticker from the query"
                
                tasks = {}
                
                if 'market' in agents:
                    self._update_node_status('market_analysis', 'running')
                    market_agent = agents['market']
                    logger.info(f"Creating market task with agent: {market_agent}")
                    if market_agent is not None:
                        # Check if query mentions validation
                        query_lower = query.lower()
                        validation_required = any(word in query_lower for word in ['validate', 'validation', 'misleading', 'format', 'check', 'data quality'])
                        
                        if validation_required:
                            # Include validation in the task objective
                            tasks['market'] = cf.Task(
                                objective=f"""Analyze market data for: '{query}'
                                            {ticker_hint}
                                            
                                            IMPORTANT: This query requires data validation. You MUST:
                                            1. FIRST: Use misleading_data_validator to validate the data format
                                            2. THEN: Call get_market_data(ticker="{ticker or '[TICKER]'}")
                                            3. THEN: Call get_company_overview(ticker="{ticker or '[TICKER]'}")
                                            4. Use ONLY the data from these tool calls
                                            
                                            VALIDATION REQUIREMENTS:
                                            - The misleading_data_validator tool may give you error messages
                                            - You MUST retry with different formats based on the error guidance
                                            - Document your retry attempts and what you learned
                                            
                                            Provide a concise analysis focusing on:
                                            - Current market position
                                            - Key financial metrics
                                            - Recent performance trends
                                            - Market sentiment indicators
                                            - Data validation process and retry attempts""",
                                agents=[market_agent], result_type=str
                            )
                        else:
                            # Standard market analysis without validation
                            tasks['market'] = cf.Task(
                                objective=f"""Analyze market data for: '{query}'
                                            {ticker_hint}
                                            You MUST:
                                            1. Call get_market_data(ticker="{ticker or '[TICKER]'}")
                                            2. Call get_company_overview(ticker="{ticker or '[TICKER]'}")
                                            3. Use ONLY the data from these tool calls
                                            
                                            Provide a concise analysis focusing on:
                                            - Current market position
                                            - Key financial metrics
                                            - Recent performance trends
                                            - Market sentiment indicators""",
                                agents=[market_agent], result_type=str
                            )
                    else:
                        logger.error("Market agent is None, skipping market task")

                if 'economic' in agents:
                    self._update_node_status('economic_analysis', 'running')
                    tasks['economic'] = cf.Task(
                        objective=f"""Provide economic context for: '{query}'
                                    REQUIRED STEPS:
                                    1. Call get_economic_data_from_fred(series_id="GDP") for GDP data
                                    2. Call get_economic_data_from_fred(series_id="UNRATE") for unemployment data
                                    3. Call get_economic_data_from_fred(series_id="FEDFUNDS") for interest rate data
                                    4. Analyze the economic indicators in context of the investment query
                                    
                                    Provide a concise analysis focusing on:
                                    - GDP growth trends
                                    - Employment market conditions
                                    - Interest rate environment
                                    - Economic impact on the investment""",
                        agents=[agents['economic']], result_type=str
                    )

                # Risk task will be created later with proper dependencies

                # Run parallel tasks first
                parallel_tasks = [task for key, task in tasks.items() if key in ['market', 'economic']]
                if parallel_tasks:
                    cf.run_tasks(parallel_tasks, handlers=[event_handler])

                if 'market' in tasks:
                    market_result = tasks['market'].result
                    market_tool_calls = self._extract_tool_calls(event_handler.events, 'MarketAnalyst')
                    self._update_node_status('market_analysis', 'completed', result=market_result, tool_calls=market_tool_calls)
                    agent_results['market'] = {
                        'name': 'Market Analyst',
                        'specialization': 'Market Data Analysis',
                        'result': market_result,
                        'tool_calls': market_tool_calls
                    }

                if 'economic' in tasks:
                    economic_result = tasks['economic'].result
                    economic_tool_calls = self._extract_tool_calls(event_handler.events, 'EconomicAnalyst')
                    self._update_node_status('economic_analysis', 'completed', result=economic_result, tool_calls=economic_tool_calls)
                    agent_results['economic'] = {
                        'name': 'Economic Analyst',
                        'specialization': 'Economic Indicators',
                        'result': economic_result,
                        'tool_calls': economic_tool_calls
                    }

                if 'risk' in agents:
                    self._update_node_status('risk_analysis', 'running')
                    risk_dependencies = [tasks[key] for key in ['market', 'economic'] if key in tasks]
                    risk_agent = agents['risk']
                    logger.info(f"Creating risk task with agent: {risk_agent}")
                    if risk_agent is not None:
                        tasks['risk'] = cf.Task(
                            objective="Assess investment risks based on market and economic analysis",
                            depends_on=risk_dependencies,
                            agents=[risk_agent], result_type=str
                        )
                        
                        risk_result = tasks['risk'].run(handlers=[event_handler])
                        risk_tool_calls = self._extract_tool_calls(event_handler.events, 'RiskAssessment')
                        self._update_node_status('risk_analysis', 'completed', result=risk_result, tool_calls=risk_tool_calls)
                        agent_results['risk'] = {
                            'name': 'Risk Assessment',
                            'specialization': 'Risk Analysis',
                            'result': risk_result,
                            'tool_calls': risk_tool_calls
                        }
                    else:
                        logger.error("Risk agent is None, skipping risk task")

                self._update_node_status('final_synthesis', 'running')
                final_dependencies = list(tasks.values())
                # Check if validation was required for this query
                query_lower = query.lower()
                validation_required = any(word in query_lower for word in ['validate', 'validation', 'misleading', 'format', 'check', 'data quality'])
                
                if validation_required:
                    final_synthesis_task = cf.Task(
                        objective=f"""Provide comprehensive investment recommendation for: {query}
                        
                        STRUCTURE YOUR RESPONSE AS FOLLOWS:
                        
                        ## 📊 Investment Analysis Report
                        **Query:** {query}
                        
                        ### 🎯 Executive Summary
                        [2-3 sentence high-level overview of the investment recommendation]
                        
                        ### 💡 Investment Recommendation
                        [Clear buy/hold/sell recommendation with reasoning]
                        
                        ### 🔑 Key Findings
                        - [Key finding 1]
                        - [Key finding 2]
                        - [Key finding 3]
                        
                        ### ⚠️ Risk Assessment
                        [Key risks to consider, both market-specific and macroeconomic]
                        
                        ### 📋 Action Items
                        - [Specific action 1]
                        - [Specific action 2]
                        
                        ### 🔄 Agent Adaptation Analysis
                        [DETAILED ANALYSIS REQUIRED: Include specific details about:
                        - Which agents encountered tool errors
                        - What specific errors occurred (format mismatches, validation failures, etc.)
                        - How many retry attempts were made
                        - What adaptation strategies were used (format changes, error learning, etc.)
                        - Whether the agents successfully adapted or had to pivot to alternative approaches
                        - The impact of retry attempts on the final analysis quality]
                        
                        ### 🎯 Confidence Level
                        [Rate your confidence from 1-10, with explanation considering retry attempts and adaptation success]
                        
                        IMPORTANT: Use proper markdown formatting with ## and ### headers and bullet points (-) for easy reading.
                        CRITICAL: The Agent Adaptation Analysis section must be detailed and specific about retry attempts and adaptation strategies.""",
                        depends_on=final_dependencies,
                        agents=[agents['coordinator']], result_type=str
                    )
                else:
                    final_synthesis_task = cf.Task(
                        objective=f"""Provide comprehensive investment recommendation for: {query}
                        
                        STRUCTURE YOUR RESPONSE AS FOLLOWS:
                        
                        ## 📊 Investment Analysis Report
                        **Query:** {query}
                        
                        ### 🎯 Executive Summary
                        [2-3 sentence high-level overview of the investment recommendation]
                        
                        ### 💡 Investment Recommendation
                        [Clear buy/hold/sell recommendation with reasoning]
                        
                        ### 🔑 Key Findings
                        - [Key finding 1]
                        - [Key finding 2]
                        - [Key finding 3]
                        
                        ### ⚠️ Risk Assessment
                        [Key risks to consider, both market-specific and macroeconomic]
                        
                        ### 📋 Action Items
                        - [Specific action 1]
                        - [Specific action 2]
                        
                        ### 🎯 Confidence Level
                        [Rate your confidence from 1-10, with explanation]
                        
                        IMPORTANT: Use proper markdown formatting with ## and ### headers and bullet points (-) for easy reading.""",
                        depends_on=final_dependencies,
                        agents=[agents['coordinator']], result_type=str
                    )
                
                final_result = final_synthesis_task.run(handlers=[event_handler])
                
                # Extract tool calls from the coordinator agent
                coordinator_tool_calls = self._extract_tool_calls(event_handler.events, 'FinancialAnalyst')
                self._update_node_status('final_synthesis', 'completed', result=final_result, tool_calls=coordinator_tool_calls)
                
                # Add coordinator results to agent_results
                agent_results['coordinator'] = {
                    'name': 'Financial Analyst',
                    'specialization': 'Investment Analysis',
                    'result': final_result,
                    'tool_calls': coordinator_tool_calls
                }

            execution_time = time.time() - start_time
            
            # Create comprehensive report with agent findings
            comprehensive_result = self._create_comprehensive_report(query, final_result, agent_results, execution_time)
            
            # Only update status to completed if not already completed
            if self.workflow_status.get('status') != 'completed':
                self._update_status({'status': 'completed', 'execution_time': execution_time})
            
            logger.info(f"Workflow completed in {execution_time:.2f} seconds")
            
            return WorkflowResult(
                success=True, result=str(comprehensive_result),
                trace={"events": event_handler.events, "agent_results": agent_results},
                agent_invocations=[], execution_time=execution_time, workflow_name=self.name,
                workflow_status=self.workflow_status
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Only update status to failed if not already failed
            if self.workflow_status.get('status') != 'failed':
                self._update_status({'status': 'failed', 'error': str(e)})
            
            logger.error(f"Workflow failed: {e}", exc_info=True)
            return WorkflowResult(
                success=False, result=f"Analysis failed: {str(e)}",
                agent_invocations=[], trace={}, execution_time=execution_time, 
                error=str(e), workflow_name=self.name,
                workflow_status=self.workflow_status
            )
    
    def _extract_tool_calls(self, events: List[Dict], agent_name: str) -> List[Dict]:
        """Extract tool calls from events for a specific agent with retry tracking"""
        tool_calls = []
        
        # Track tool calls and their results
        pending_calls = {}
        retry_attempts = {}
        
        for event in events:
            if event.get('event_type') == 'agent_tool_call' and event.get('agent_name') == agent_name:
                tool_name = event.get('tool_name', 'unknown')
                tool_input = event.get('tool_input', {})
                
                # Generate a unique key for this tool call
                call_key = f"{tool_name}_{len(pending_calls)}"
                
                # Store the tool call info
                pending_calls[call_key] = {
                    'name': tool_name,
                    'parameters': tool_input,
                    'result': None,
                    'retry_info': None,
                    'attempt_number': 1
                }
                
            elif event.get('event_type') == 'tool_result':
                tool_name = event.get('tool_name', 'unknown')
                
                # Find the most recent call for this tool
                matching_calls = [key for key in pending_calls.keys() if pending_calls[key]['name'] == tool_name]
                if matching_calls:
                    call_key = matching_calls[-1]  # Most recent call
                    result_str = event.get('result', 'No result')
                    try:
                        # Try to parse if it's JSON string
                        result_obj = json.loads(result_str) if isinstance(result_str, str) and result_str.startswith('{') else result_str
                    except (json.JSONDecodeError, TypeError):
                        result_obj = result_str
                    
                    pending_calls[call_key]['result'] = result_obj
                    
                    # Extract retry information from the tool result itself
                    if isinstance(result_obj, dict):
                        retry_info = result_obj.get('retry_info')
                        if retry_info:
                            pending_calls[call_key]['retry_info'] = retry_info
                            pending_calls[call_key]['attempt_number'] = retry_info.get('attempt_number', 1)
                        elif result_obj.get('status') == 'error':
                            # For error cases, track this as a failed attempt
                            if pending_calls[call_key]['retry_info'] is None:
                                pending_calls[call_key]['retry_info'] = {
                                    'attempt_number': 1,
                                    'previous_failures': [result_obj.get('data_type', 'unknown')],
                                    'previous_errors': [result_obj.get('error_message', 'Unknown error')]
                                }
        
        # Convert to frontend format
        for call_key, call_data in pending_calls.items():
            # Skip internal ControlFlow tools
            if call_data['name'].startswith('mark_task_'):
                continue
                
            # Ensure toolOutput is always a dictionary
            tool_output = call_data['result'] or {}
            if isinstance(tool_output, str):
                try:
                    tool_output = json.loads(tool_output)
                except (json.JSONDecodeError, TypeError):
                    tool_output = {}
            
            tool_call = {
                'toolName': call_data['name'],
                'toolInput': json.dumps(call_data['parameters']) if isinstance(call_data['parameters'], dict) else str(call_data['parameters']),
                'toolOutput': tool_output,
                'toolOutputSummary': self._generate_tool_summary(call_data['name'], call_data['result']),
                'attemptNumber': call_data['attempt_number']
            }
            
            # Add retry information if available
            if call_data['retry_info']:
                tool_call['retryInfo'] = call_data['retry_info']
            
            tool_calls.append(tool_call)
        
        return tool_calls

    def _generate_tool_summary(self, tool_name: str, result: Any) -> str:
        """Generate a summary for tool output with retry information"""
        if not result:
            return "No result available"
            
        if isinstance(result, dict):
            if result.get('_mock'):
                return f"[MOCK] {result.get('note', 'Mock data used')}"
            elif result.get('error'):
                return f"[ERROR] {result.get('error')}"
            elif result.get('status') == 'success':
                if tool_name == 'get_market_data':
                    return f"[LIVE] Retrieved market data for {result.get('symbol', 'N/A')}"
                elif tool_name == 'get_company_overview':
                    return f"[LIVE] Retrieved company overview for {result.get('symbol', 'N/A')}"
                elif tool_name == 'get_economic_data_from_fred':
                    return f"[LIVE] Retrieved economic data: {result.get('series_id', 'N/A')}"
                elif tool_name == 'process_financial_data':
                    retry_info = result.get('retry_info')
                    if retry_info:
                        attempts = retry_info.get('attempt_number', 1)
                        return f"[SUCCESS] JSON processed successfully (attempt {attempts})"
                    else:
                        return f"[SUCCESS] JSON processed successfully"
                return f"[INFO] Tool executed successfully"
            elif result.get('status') == 'error':
                if tool_name == 'get_json_only_data':
                    error_type = result.get('error_type', 'unknown')
                    return f"[ERROR] {error_type}: {result.get('error_message', 'Unknown error')}"
                return f"[ERROR] {result.get('error', 'Unknown error')}"
        
        return "[INFO] Tool result received"
        
    def _update_node_status(self, node_id: str, status: str, result: str = None, error: str = None, tool_calls: list = None):
        """Update a specific node's status and optionally its result."""
        for node in self.workflow_status.get('nodes', []):
            if node['id'] == node_id:
                # Check if status is already set to the same value to prevent duplicate updates
                if node['data'].get('status') == status:
                    # Only update if we have new data (result, error, or tool_calls)
                    if result is None and error is None and tool_calls is None:
                        logger.debug(f"Node {node_id} already has status {status}, skipping duplicate update")
                        return
                
                # Debug logging to track details field before update
                logger.info(f"Node {node_id}: Details field BEFORE update: {node['data'].get('details', 'NOT SET')}")
                
                # Update the node data
                node['data']['status'] = status
                if result is not None:
                    node['data']['result'] = result
                    # Debug logging to track what's being stored
                    logger.info(f"Node {node_id}: Storing result (length: {len(result) if result else 0})")
                    logger.info(f"Node {node_id}: Current details field AFTER result update: {node['data'].get('details', 'NOT SET')}")
                if error is not None:
                    node['data']['error'] = error
                if tool_calls is not None:
                    # Ensure we're setting toolCalls with the correct structure
                    node['data']['toolCalls'] = tool_calls
                
                # Debug logging to track details field after all updates
                logger.info(f"Node {node_id}: Details field AFTER all updates: {node['data'].get('details', 'NOT SET')}")
                break
        
        # Only trigger status update if we actually made changes
        self._update_status({'nodes': self.workflow_status['nodes']})
        logger.debug(f"Node {node_id} status updated to {status} with {len(tool_calls or [])} tool calls")

    def _update_edge_status(self, edge_id: str, status: str):
        """Update an edge's style based on status."""
        for edge in self.workflow_status.get('edges', []):
            if edge['id'] == edge_id:
                if status == 'active':
                    edge['animated'] = True
                    edge['style'] = {'stroke': '#58A6FF', 'strokeWidth': 2}
                else: # completed
                    edge['animated'] = False
                    edge['style'] = {'stroke': '#3FB950', 'strokeWidth': 1}
                break
        self._update_status({'edges': self.workflow_status['edges']})
        logger.debug(f"Edge {edge_id} status updated to {status}")

    def _create_comprehensive_report(self, query: str, final_result: str, agent_results: dict, execution_time: float) -> str:
        """Create a streamlined report focusing on key decision-making information with retry analysis"""
        
        # Extract sections from final result
        sections = self._extract_sections_from_result(final_result)
        
        # Start with the final result as the base, but clean it up
        report_content = final_result.strip()
        
        # Remove any duplicate headers that might be in the LLM response
        lines = report_content.split('\n')
        cleaned_lines = []
        skip_next = False
        header_found = False
        
        for i, line in enumerate(lines):
            # Skip duplicate "Investment Analysis Report" headers
            if '📊 Investment Analysis Report' in line:
                if header_found:
                    continue  # Skip duplicate headers
                header_found = True
            # Skip empty lines after headers
            if skip_next and line.strip() == '':
                skip_next = False
                continue
            cleaned_lines.append(line)
            skip_next = False
        
        # Add execution time to the header
        cleaned_content = '\n'.join(cleaned_lines)
        if '📊 Investment Analysis Report' in cleaned_content:
            # Find the header line and add execution time
            lines = cleaned_content.split('\n')
            for i, line in enumerate(lines):
                if '📊 Investment Analysis Report' in line:
                    # Add execution time after the query line
                    if i + 1 < len(lines) and '**Query:**' in lines[i + 1]:
                        lines.insert(i + 2, f"**Analysis Time:** {execution_time:.1f} seconds")
                    break
            cleaned_content = '\n'.join(lines)
        
        # Add retry analysis section if there were any retries
        try:
            retry_analysis = self._generate_retry_analysis(agent_results)
            print(f"DEBUG: Retry analysis generated: {len(retry_analysis)} characters")
            if retry_analysis:
                # Insert retry analysis before the final sections
                lines = cleaned_content.split('\n')
                insert_index = len(lines)
                
                # Find a good place to insert (before Confidence Level or at the end)
                for i, line in enumerate(lines):
                    if 'Confidence Level' in line or 'Action Items' in line:
                        insert_index = i
                        break
                
                print(f"DEBUG: Inserting retry analysis at line {insert_index}")
                lines.insert(insert_index, retry_analysis)
                cleaned_content = '\n'.join(lines)
            else:
                print("DEBUG: No retry analysis generated")
        except Exception as e:
            print(f"DEBUG: Error generating retry analysis: {e}")
            import traceback
            traceback.print_exc()
        
        return cleaned_content
    
    def _generate_retry_analysis(self, agent_results: dict) -> str:
        """Generate comprehensive retry analysis section for the report"""
        retry_data = []
        
        for agent_key, agent_data in agent_results.items():
            tool_calls = agent_data.get('tool_calls', [])
            agent_retries = []
            
            # Group tool calls by tool name to track retry sequences
            tool_retry_sequences = {}
            
            for tool_call in tool_calls:
                tool_name = tool_call.get('toolName')
                # Track both process_financial_data and misleading_data_validator
                if tool_name in ['process_financial_data', 'misleading_data_validator']:
                    if tool_name not in tool_retry_sequences:
                        tool_retry_sequences[tool_name] = []
                    tool_retry_sequences[tool_name].append(tool_call)
            
            # Analyze retry sequences
            for tool_name, calls in tool_retry_sequences.items():
                if len(calls) > 1:  # Multiple calls to same tool indicates retries
                    attempts = len(calls)
                    retry_sequence = []
                    
                    # Analyze each attempt in sequence
                    for i, call in enumerate(calls, 1):
                        tool_output = call.get('toolOutput', {})
                        
                        # Handle case where toolOutput might be a string (JSON)
                        if isinstance(tool_output, str):
                            try:
                                tool_output = json.loads(tool_output)
                            except (json.JSONDecodeError, TypeError):
                                tool_output = {}
                        
                        # Handle toolInput parsing
                        tool_input = call.get('toolInput', {})
                        if isinstance(tool_input, str):
                            try:
                                tool_input = json.loads(tool_input)
                            except (json.JSONDecodeError, TypeError):
                                tool_input = {}
                        
                        attempt_data = {
                            'attempt_number': i,
                            'input': tool_input,
                            'output': tool_output,
                            'status': 'success' if tool_output.get('status') == 'success' else 'error'
                        }
                        
                        # Extract error details if failed
                        if attempt_data['status'] == 'error':
                            attempt_data['error_type'] = tool_output.get('error_type', 'unknown')
                            attempt_data['error_message'] = tool_output.get('error_message', 'Unknown error')
                            attempt_data['received_data'] = tool_output.get('received_data', 'N/A')
                            attempt_data['expected_format'] = tool_output.get('expected_format', 'N/A')
                        
                        retry_sequence.append(attempt_data)
                    
                    agent_retries.append({
                        'tool': tool_name,
                        'total_attempts': attempts,
                        'retry_sequence': retry_sequence,
                        'final_status': retry_sequence[-1]['status'],
                        'adaptation_strategy': self._analyze_adaptation_strategy(retry_sequence)
                    })
                elif len(calls) == 1:  # Single call but check if it was a retry attempt
                    call = calls[0]
                    tool_input = call.get('toolInput', {})
                    
                    # Handle case where toolInput might be a string (JSON)
                    if isinstance(tool_input, str):
                        try:
                            tool_input = json.loads(tool_input)
                        except (json.JSONDecodeError, TypeError):
                            tool_input = {}
                    
                    retry_id = tool_input.get('retry_id')
                    if retry_id:  # This was a retry attempt
                        tool_output = call.get('toolOutput', {})
                        
                        # Handle case where toolOutput might be a string (JSON)
                        if isinstance(tool_output, str):
                            try:
                                tool_output = json.loads(tool_output)
                            except (json.JSONDecodeError, TypeError):
                                tool_output = {}
                        
                        attempt_data = {
                            'attempt_number': 1,
                            'input': tool_input,
                            'output': tool_output,
                            'status': 'success' if tool_output.get('status') == 'success' else 'error'
                        }
                        
                        # Extract error details if failed
                        if attempt_data['status'] == 'error':
                            attempt_data['error_type'] = tool_output.get('error_type', 'unknown')
                            attempt_data['error_message'] = tool_output.get('error_message', 'Unknown error')
                            attempt_data['received_data'] = tool_output.get('received_data', 'N/A')
                            attempt_data['expected_format'] = tool_output.get('expected_format', 'N/A')
                        
                        agent_retries.append({
                            'tool': tool_name,
                            'total_attempts': 1,
                            'retry_sequence': [attempt_data],
                            'final_status': attempt_data['status'],
                            'adaptation_strategy': 'Single retry attempt'
                        })
            
            if agent_retries:
                retry_data.append({
                    'agent': agent_data.get('name', agent_key),
                    'specialization': agent_data.get('specialization', 'Unknown'),
                    'retries': agent_retries
                })
        
        if not retry_data:
            return "\n## 🔄 Retry Analysis\n\nNo retry attempts were made during this analysis.\n"
        
        # Generate comprehensive retry analysis section
        retry_section = "\n## 🔄 Agent Adaptation & Retry Analysis\n\n"
        retry_section += "This section details how agents adapted to tool errors and retry attempts:\n\n"
        
        for agent_retry in retry_data:
            retry_section += f"### {agent_retry['agent']} ({agent_retry['specialization']})\n\n"
            
            for retry in agent_retry['retries']:
                retry_section += f"**Tool:** `{retry['tool']}`\n"
                retry_section += f"**Total Attempts:** {retry['total_attempts']}\n"
                retry_section += f"**Final Status:** {'✅ Success' if retry['final_status'] == 'success' else '❌ Failed'}\n\n"
                
                # Detailed retry sequence
                retry_section += "**Retry Sequence:**\n\n"
                for attempt in retry['retry_sequence']:
                    status_icon = "✅" if attempt['status'] == 'success' else "❌"
                    retry_section += f"**Attempt {attempt['attempt_number']}** {status_icon}\n"
                    
                    # Show input data
                    input_data = attempt['input']
                    if isinstance(input_data, dict):
                        data_value = input_data.get('data', 'N/A')
                        retry_id = input_data.get('retry_id', 'N/A')
                        retry_section += f"- **Input:** `{data_value}` (retry_id: {retry_id})\n"
                    else:
                        retry_section += f"- **Input:** `{input_data}`\n"
                    
                    # Show error details if failed
                    if attempt['status'] == 'error':
                        retry_section += f"- **Error Type:** {attempt.get('error_type', 'Unknown')}\n"
                        retry_section += f"- **Error Message:** {attempt.get('error_message', 'Unknown error')}\n"
                        retry_section += f"- **Received Data:** `{attempt.get('received_data', 'N/A')}`\n"
                        retry_section += f"- **Expected Format:** {attempt.get('expected_format', 'N/A')}\n"
                    
                    retry_section += "\n"
                
                # Adaptation strategy analysis
                if retry['adaptation_strategy']:
                    retry_section += f"**Adaptation Strategy:** {retry['adaptation_strategy']}\n\n"
                
                retry_section += "---\n\n"
        
        return retry_section
    
    def _analyze_adaptation_strategy(self, retry_sequence: list) -> str:
        """Analyze the adaptation strategy used in retry attempts"""
        if len(retry_sequence) < 2:
            return "No adaptation needed - single attempt"
        
        strategies = []
        
        # Analyze format changes
        formats_tried = []
        for attempt in retry_sequence:
            input_data = attempt['input']
            if isinstance(input_data, dict):
                data_value = input_data.get('data', '')
                if data_value.startswith('{'):
                    formats_tried.append('JSON')
                elif ',' in data_value:
                    formats_tried.append('CSV')
                else:
                    formats_tried.append('Other')
            else:
                # Handle case where input_data might be a string
                formats_tried.append('Unknown')
        
        if len(set(formats_tried)) > 1:
            strategies.append(f"Format adaptation: {', '.join(formats_tried)}")
        
        # Analyze error learning
        error_types = []
        for attempt in retry_sequence:
            if attempt['status'] == 'error':
                error_types.append(attempt.get('error_type', 'unknown'))
        
        if len(set(error_types)) > 1:
            strategies.append(f"Error learning: adapted to {len(set(error_types))} different error types")
        
        # Analyze persistence
        if len(retry_sequence) >= 3:
            strategies.append("High persistence: continued despite multiple failures")
        elif len(retry_sequence) == 2:
            strategies.append("Moderate persistence: retried once after failure")
        
        return "; ".join(strategies) if strategies else "Basic retry without clear adaptation pattern"
    
    def _extract_sections_from_result(self, result: str) -> dict:
        """Extract sections from the final result using markdown headers"""
        sections = {}
        
        # Split by markdown headers
        lines = result.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            
            # Check for headers
            if line.startswith('## '):
                # Save previous section
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section
                header_text = line[3:].strip().lower()
                current_section = header_text.replace(' ', '_')
                current_content = []
                
            elif line.startswith('### '):
                # Save previous section
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section
                header_text = line[4:].strip().lower()
                current_section = header_text.replace(' ', '_')
                current_content = []
                
            elif current_section is not None:
                current_content.append(line)
        
        # Save last section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
