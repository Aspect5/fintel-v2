# In backend/workflows/dependency_workflow.py
import controlflow as cf
from typing import Dict, Any, List
from .base import BaseWorkflow, WorkflowResult
import time
import logging
import threading
from datetime import datetime

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
    
    def _initialize_workflow_nodes(self, query):
        """Initialize workflow nodes for frontend visualization."""
        nodes = [
            {'id': 'query_input', 'type': 'input', 'position': {'x': 50, 'y': 200}, 
             'data': {'label': 'User Query', 'details': query, 'status': 'running'}},
            {'id': 'market_analysis', 'type': 'default', 'position': {'x': 350, 'y': 100}, 
             'data': {'label': 'Market Analyst', 'status': 'pending', 'toolCalls': []}},
            {'id': 'economic_analysis', 'type': 'default', 'position': {'x': 350, 'y': 300}, 
             'data': {'label': 'Economic Analyst', 'status': 'pending', 'toolCalls': []}},
            {'id': 'risk_assessment', 'type': 'default', 'position': {'x': 650, 'y': 200}, 
             'data': {'label': 'Risk Assessment', 'status': 'pending', 'toolCalls': []}},
            {'id': 'final_synthesis', 'type': 'output', 'position': {'x': 950, 'y': 200}, 
             'data': {'label': 'Final Report', 'status': 'pending'}},
        ]
        
        edges = [
            {'id': 'e1', 'source': 'query_input', 'target': 'market_analysis', 'animated': False},
            {'id': 'e2', 'source': 'query_input', 'target': 'economic_analysis', 'animated': False},
            {'id': 'e3', 'source': 'market_analysis', 'target': 'risk_assessment', 'animated': False},
            {'id': 'e4', 'source': 'economic_analysis', 'target': 'risk_assessment', 'animated': False},
            {'id': 'e5', 'source': 'risk_assessment', 'target': 'final_synthesis', 'animated': False},
        ]
        
        self.workflow_status.update({
            'nodes': nodes, 
            'edges': edges, 
            'start_time': datetime.now().isoformat(),
            'query': query
        })
        self._update_status({'initialized': True})
    
    def execute(self, query: str, provider: str = "openai", **kwargs) -> WorkflowResult:
        """Execute workflow with real-time status updates"""
        start_time = time.time()
        
        self._initialize_workflow_nodes(query)
        self._update_status({'status': 'running'})
        
        logger.info(f"Executing workflow for query: {query}")
        
        try:
            from backend.agents.registry import get_agent_registry
            from backend.utils.observability import FintelEventHandler
            agent_registry = get_agent_registry()
            
            # Create event handler to capture tool calls
            event_handler = FintelEventHandler()
            
            market_agent = agent_registry.get_agent("MarketAnalyst", provider)
            economic_agent = agent_registry.get_agent("EconomicAnalyst", provider)
            financial_agent = agent_registry.get_agent("FinancialAnalyst", provider)
            
            with cf.Flow(name="financial_analysis_flow") as flow:
                self._update_node_status('query_input', 'completed')
                self._update_edge_status('e1', 'active')
                self._update_edge_status('e2', 'active')
                
                # Market Analysis Task
                self._update_node_status('market_analysis', 'running')
                market_analysis_task = cf.Task(
                    objective=f"Analyze market data for the stock mentioned in: {query}. You MUST use get_market_data and get_company_overview tools.",
                    agents=[market_agent], 
                    result_type=str
                )
                
                # Economic Analysis Task
                self._update_node_status('economic_analysis', 'running')
                economic_analysis_task = cf.Task(
                    objective=f"Provide economic context for the investment query: {query}. You MUST use get_economic_data_from_fred tool to get GDP, UNRATE, and FEDFUNDS data.",
                    agents=[economic_agent], 
                    result_type=str
                )
                
                logger.info("Executing market and economic analysis...")
                market_result = market_analysis_task.run(handlers=[event_handler])
                
                # Extract tool calls for market analysis
                market_tool_calls = self._extract_tool_calls(event_handler.events, 'MarketAnalyst')
                self._update_node_status('market_analysis', 'completed', 
                                       result=market_result, 
                                       tool_calls=market_tool_calls)
                self._update_edge_status('e1', 'completed')
                self._update_edge_status('e3', 'active')
                
                economic_result = economic_analysis_task.run(handlers=[event_handler])
                
                # Extract tool calls for economic analysis
                economic_tool_calls = self._extract_tool_calls(event_handler.events, 'EconomicAnalyst')
                self._update_node_status('economic_analysis', 'completed', 
                                       result=economic_result,
                                       tool_calls=economic_tool_calls)
                self._update_edge_status('e2', 'completed')
                self._update_edge_status('e4', 'active')
                
                # Risk Assessment
                self._update_node_status('risk_assessment', 'running')
                risk_assessment_task = cf.Task(
                    objective="Assess investment risks based on market and economic analysis",
                    depends_on=[market_analysis_task, economic_analysis_task],
                    agents=[financial_agent], 
                    result_type=str
                )
                
                logger.info("Executing risk assessment...")
                risk_result = risk_assessment_task.run(handlers=[event_handler])
                self._update_node_status('risk_assessment', 'completed', result=risk_result)
                self._update_edge_status('e3', 'completed')
                self._update_edge_status('e4', 'completed')
                self._update_edge_status('e5', 'active')
                
                # Final Synthesis
                self._update_node_status('final_synthesis', 'running')
                final_synthesis_task = cf.Task(
                    objective=f"Provide comprehensive investment recommendation for: {query}",
                    depends_on=[risk_assessment_task],
                    agents=[financial_agent], 
                    result_type=str
                )
                
                logger.info("Executing final synthesis...")
                final_result = final_synthesis_task.run(handlers=[event_handler])
                self._update_node_status('final_synthesis', 'completed', result=final_result)
                self._update_edge_status('e5', 'completed')

            execution_time = time.time() - start_time
            self._update_status({'status': 'completed', 'execution_time': execution_time})
            
            logger.info(f"Workflow completed in {execution_time:.2f} seconds")
            
            return WorkflowResult(
                success=True, 
                result=str(final_result),
                trace={
                    "market": market_result, 
                    "economic": economic_result, 
                    "risk": risk_result, 
                    "final": final_result,
                    "events": event_handler.events
                },
                agent_invocations=[],
                execution_time=execution_time, 
                workflow_name=self.name,
                workflow_status=self.workflow_status
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._update_status({'status': 'failed', 'error': str(e)})
            logger.error(f"Workflow failed: {e}", exc_info=True)
            return WorkflowResult(
                success=False, 
                result=f"Analysis failed: {str(e)}",
                agent_invocations=[],
                trace={},
                execution_time=execution_time, 
                error=str(e), 
                workflow_name=self.name,
                workflow_status=self.workflow_status
            )
    
    def _extract_tool_calls(self, events: List[Dict], agent_name: str) -> List[Dict]:
        """Extract tool calls from events for a specific agent"""
        tool_calls = []
        for event in events:
            if (event.get('event_type') == 'agent_tool_call' and 
                event.get('agent_name') == agent_name):
                tool_calls.append({
                    'toolName': event.get('tool_name', 'unknown'),
                    'toolInput': event.get('tool_input', {}),
                    'toolOutput': event.get('tool_output', {}),
                    'toolOutputSummary': event.get('tool_summary', '')
                })
        return tool_calls
    
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
                    node['data']['toolCalls'] = tool_calls
                break
        self._update_status({'nodes': self.workflow_status['nodes']})
        logger.debug(f"Node {node_id} status updated to {status}")

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
