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
            new_status = dict(self.workflow_status)
            new_status.update(update)
            self.workflow_status = new_status
            
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
        
        if any(word in query_lower for word in ['market', 'stock', 'price', 'trading']):
            agents['market'] = agent_registry.get_agent("MarketAnalyst", provider)
        
        if any(word in query_lower for word in ['economy', 'gdp', 'inflation', 'rates']):
            agents['economic'] = agent_registry.get_agent("EconomicAnalyst", provider)
        
        if any(word in query_lower for word in ['risk', 'volatility', 'beta']):
            agents['risk'] = agent_registry.get_agent("RiskAssessment", provider)
        
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
        
        agent_positions = {
            'market': {'x': 350, 'y': 100},
            'economic': {'x': 350, 'y': 300},
            'risk': {'x': 650, 'y': 200}
        }
        
        # Add nodes for each agent
        for agent_key, position in agent_positions.items():
            if agent_key in agents:
                nodes.append({
                    'id': f'{agent_key}_analysis', 'type': 'default', 'position': position,
                    'data': {'label': f'{agent_key.title()} Analyst', 'status': 'pending', 'toolCalls': []}
                })
                edges.append({'id': f'e_{agent_key}', 'source': 'query_input', 'target': f'{agent_key}_analysis', 'animated': False})

        # Add risk node connections from market and economic if they exist
        if 'risk' in agents:
            if 'market' in agents:
                edges.append({'id': 'e_market_risk', 'source': 'market_analysis', 'target': 'risk_assessment', 'animated': False})
            if 'economic' in agents:
                edges.append({'id': 'e_economic_risk', 'source': 'economic_analysis', 'target': 'risk_assessment', 'animated': False})
        
        # Add final synthesis node
        nodes.append({'id': 'final_synthesis', 'type': 'output', 'position': {'x': 950, 'y': 200}, 
                      'data': {'label': 'Final Report', 'status': 'pending'}})

        # Connect final synthesis to its dependencies
        synthesis_dependencies = [f'{agent_key}_analysis' for agent_key in agents if agent_key != 'coordinator']
        for dep in synthesis_dependencies:
            edges.append({'id': f'e_{dep}_final', 'source': dep, 'target': 'final_synthesis', 'animated': False})
            
        self.workflow_status.update({
            'nodes': nodes, 'edges': edges, 'start_time': datetime.now().isoformat(), 'query': query
        })
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
        
        agents = self._get_agents_for_query(query, provider)
        self._initialize_workflow_nodes(query, agents)
        self._update_status({'status': 'running'})
        
        logger.info(f"Executing workflow for query: {query} with agents: {list(agents.keys())}")
        
        try:
            from backend.utils.observability import FintelEventHandler
            
            event_handler = FintelEventHandler()
            
            with cf.Flow(name="financial_analysis_flow") as flow:
                self._update_node_status('query_input', 'completed')
                
                ticker = self._extract_ticker_from_query(query)
                ticker_hint = f"The ticker symbol is: {ticker}" if ticker else "Extract the ticker from the query"
                
                tasks = {}
                
                if 'market' in agents:
                    self._update_node_status('market_analysis', 'running')
                    tasks['market'] = cf.Task(
                        objective=f"""Analyze market data for: '{query}'
                                    {ticker_hint}
                                    You MUST:
                                    1. Call get_market_data(ticker="{ticker or '[TICKER]'}")
                                    2. Call get_company_overview(ticker="{ticker or '[TICKER]'}")
                                    3. Use ONLY the data from these tool calls""",
                        agents=[agents['market']], result_type=str
                    )

                if 'economic' in agents:
                    self._update_node_status('economic_analysis', 'running')
                    tasks['economic'] = cf.Task(
                        objective=f"""Provide economic context for: '{query}'
                                    REQUIRED STEPS:
                                    1. Call get_economic_data_from_fred(series_id="GDP") for GDP data
                                    2. Call get_economic_data_from_fred(series_id="UNRATE") for unemployment data
                                    3. Call get_economic_data_from_fred(series_id="FEDFUNDS") for interest rate data
                                    4. Analyze the economic indicators in context of the investment query""",
                        agents=[agents['economic']], result_type=str
                    )

                # Run parallel tasks first
                parallel_tasks = [task for key, task in tasks.items() if key in ['market', 'economic']]
                if parallel_tasks:
                    cf.run_tasks(parallel_tasks, handlers=[event_handler])

                if 'market' in tasks:
                    market_result = tasks['market'].result
                    market_tool_calls = self._extract_tool_calls(event_handler.events, 'MarketAnalyst')
                    self._update_node_status('market_analysis', 'completed', result=market_result, tool_calls=market_tool_calls)

                if 'economic' in tasks:
                    economic_result = tasks['economic'].result
                    economic_tool_calls = self._extract_tool_calls(event_handler.events, 'EconomicAnalyst')
                    self._update_node_status('economic_analysis', 'completed', result=economic_result, tool_calls=economic_tool_calls)

                if 'risk' in agents:
                    self._update_node_status('risk_assessment', 'running')
                    risk_dependencies = [tasks[key] for key in ['market', 'economic'] if key in tasks]
                    tasks['risk'] = cf.Task(
                        objective="Assess investment risks based on market and economic analysis",
                        depends_on=risk_dependencies,
                        agents=[agents['risk']], result_type=str
                    )
                    risk_result = tasks['risk'].run(handlers=[event_handler])
                    self._update_node_status('risk_assessment', 'completed', result=risk_result)

                self._update_node_status('final_synthesis', 'running')
                final_dependencies = list(tasks.values())
                final_synthesis_task = cf.Task(
                    objective=f"Provide comprehensive investment recommendation for: {query}",
                    depends_on=final_dependencies,
                    agents=[agents['coordinator']], result_type=str
                )
                
                final_result = final_synthesis_task.run(handlers=[event_handler])
                self._update_node_status('final_synthesis', 'completed', result=final_result)

            execution_time = time.time() - start_time
            self._update_status({'status': 'completed', 'execution_time': execution_time})
            
            logger.info(f"Workflow completed in {execution_time:.2f} seconds")
            
            return WorkflowResult(
                success=True, result=str(final_result),
                trace={"events": event_handler.events},
                agent_invocations=[], execution_time=execution_time, workflow_name=self.name,
                workflow_status=self.workflow_status
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._update_status({'status': 'failed', 'error': str(e)})
            logger.error(f"Workflow failed: {e}", exc_info=True)
            return WorkflowResult(
                success=False, result=f"Analysis failed: {str(e)}",
                agent_invocations=[], trace={}, execution_time=execution_time, 
                error=str(e), workflow_name=self.name,
                workflow_status=self.workflow_status
            )
    
    def _extract_tool_calls(self, events: List[Dict], agent_name: str) -> List[Dict]:
        """Extract tool calls from events for a specific agent"""
        tool_calls = []
        
        # Track tool calls and their results
        pending_calls = {}
        
        for event in events:
            if event.get('event_type') == 'agent_tool_call' and event.get('agent_name') == agent_name:
                tool_name = event.get('tool_name', 'unknown')
                # Store the tool call info
                pending_calls[tool_name] = {
                    'name': tool_name,
                    'parameters': event.get('tool_input', {}),
                    'result': None
                }
                
            elif event.get('event_type') == 'tool_result':
                tool_name = event.get('tool_name', 'unknown')
                if tool_name in pending_calls:
                    # Update with the result
                    result_str = event.get('result', 'No result')
                    try:
                        # Try to parse if it's JSON string
                        result_obj = json.loads(result_str) if isinstance(result_str, str) and result_str.startswith('{') else result_str
                    except:
                        result_obj = result_str
                        
                    pending_calls[tool_name]['result'] = result_obj
        
        # Convert to frontend format
        for tool_name, call_data in pending_calls.items():
            # Skip internal ControlFlow tools
            if tool_name.startswith('mark_task_'):
                continue
                
            tool_calls.append({
                'toolName': tool_name,  # Changed from 'name' to 'toolName'
                'toolInput': json.dumps(call_data['parameters']) if isinstance(call_data['parameters'], dict) else str(call_data['parameters']),
                'toolOutput': call_data['result'] or {},
                'toolOutputSummary': self._generate_tool_summary(tool_name, call_data['result'])
            })
        
        return tool_calls

    def _generate_tool_summary(self, tool_name: str, result: Any) -> str:
        """Generate a summary for tool output"""
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
            return f"[INFO] Tool executed successfully"
        
        return "[INFO] Tool result received"
        
    def _update_node_status(self, node_id: str, status: str, result: str = None, error: str = None, tool_calls: list = None):
        """Update a specific node's status and optionally its result."""
        for node in self.workflow_status.get('nodes', []):
            if node['id'] == node_id:
                node['data']['status'] = status
                if result:
                    node['data']['result'] = result
                if error:
                    node['data']['error'] = error
                if tool_calls is not None:
                    # Ensure we're setting toolCalls with the correct structure
                    node['data']['toolCalls'] = tool_calls
                break
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
