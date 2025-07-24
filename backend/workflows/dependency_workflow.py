# backend/workflows/dependency_workflow.py
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
    
    def add_status_callback(self, callback):
        """Add callback for status updates"""
        self.status_callbacks.append(callback)
    
    def _update_status(self, update):
        """Update workflow status and notify callbacks"""
        with threading.Lock():
            # Create a new dict to avoid race conditions
            new_status = dict(self.workflow_status)
            new_status.update(update)
            self.workflow_status = new_status
            
            for callback in self.status_callbacks:
                try:
                    # Pass a copy to avoid modifications during iteration
                    callback(new_status.copy())
                except Exception as e:
                    logger.error(f"Status callback error: {e}")
    
    def execute(self, query: str, provider: str = "openai", **kwargs) -> WorkflowResult:
        """Execute workflow with real-time status updates"""
        start_time = time.time()
        
        self._update_status({'status': 'running'})
        
        logger.info(f"Executing workflow for query: {query}")
        
        try:
            from backend.agents.registry import get_agent_registry
            agent_registry = get_agent_registry()
            
            market_agent = agent_registry.get_agent("MarketAnalyst", provider)
            economic_agent = agent_registry.get_agent("EconomicAnalyst", provider)
            financial_agent = agent_registry.get_agent("FinancialAnalyst", provider)
            
            with cf.Flow(name="financial_analysis_flow") as flow:
                self._update_node_status('query_input', 'completed')
                self._update_edge_status('e1', 'active')
                self._update_edge_status('e2', 'active')
                
                self._update_node_status('market_analysis', 'running')
                market_analysis_task = cf.Task(
                    objective=f"Analyze market data for: {query}",
                    agents=[market_agent], result_type=str
                )
                
                self._update_node_status('economic_analysis', 'running')
                economic_analysis_task = cf.Task(
                    objective=f"Provide economic context for: {query}",
                    agents=[economic_agent], result_type=str
                )
                
                logger.info("Executing market and economic analysis...")
                market_result = market_analysis_task.run()
                self._update_node_status('market_analysis', 'completed', result=market_result)
                self._update_edge_status('e1', 'completed')
                self._update_edge_status('e3', 'active')
                
                economic_result = economic_analysis_task.run()
                self._update_node_status('economic_analysis', 'completed', result=economic_result)
                self._update_edge_status('e2', 'completed')
                self._update_edge_status('e4', 'active')
                
                self._update_node_status('risk_assessment', 'running')
                risk_assessment_task = cf.Task(
                    objective="Assess investment risks based on market and economic analysis",
                    depends_on=[market_analysis_task, economic_analysis_task],
                    agents=[financial_agent], result_type=str
                )
                
                logger.info("Executing risk assessment...")
                risk_result = risk_assessment_task.run()
                self._update_node_status('risk_assessment', 'completed', result=risk_result)
                self._update_edge_status('e3', 'completed')
                self._update_edge_status('e4', 'completed')
                self._update_edge_status('e5', 'active')
                
                self._update_node_status('final_synthesis', 'running')
                final_synthesis_task = cf.Task(
                    objective=f"Provide comprehensive investment recommendation for: {query}",
                    depends_on=[risk_assessment_task],
                    agents=[financial_agent], result_type=str
                )
                
                logger.info("Executing final synthesis...")
                final_result = final_synthesis_task.run()
                self._update_node_status('final_synthesis', 'completed', result=final_result)
                self._update_edge_status('e5', 'completed')

            execution_time = time.time() - start_time
            self._update_status({'status': 'completed', 'execution_time': execution_time})
            
            logger.info(f"Workflow completed in {execution_time:.2f} seconds")
            
            return WorkflowResult(
                success=True, result=str(final_result),
                trace={"market": market_result, "economic": economic_result, "risk": risk_result, "final": final_result},
                agent_invocations=[],
                execution_time=execution_time, workflow_name=self.name,
                workflow_status=self.workflow_status
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._update_status({'status': 'failed', 'error': str(e)})
            logger.error(f"Workflow failed: {e}", exc_info=True)
            return WorkflowResult(
                success=False, result=f"Analysis failed: {str(e)}",
                agent_invocations=[],
                trace={},
                execution_time=execution_time, error=str(e), workflow_name=self.name,
                workflow_status=self.workflow_status
            )
    
    def _initialize_workflow_nodes(self, query):
        """Initialize workflow nodes for frontend visualization."""
        nodes = [
            {'id': 'query_input', 'type': 'input', 'position': {'x': 50, 'y': 200}, 'data': {'label': 'User Query', 'details': query, 'status': 'running'}},
            {'id': 'market_analysis', 'type': 'default', 'position': {'x': 350, 'y': 100}, 'data': {'label': 'Market Analyst', 'status': 'pending'}},
            {'id': 'economic_analysis', 'type': 'default', 'position': {'x': 350, 'y': 300}, 'data': {'label': 'Economic Analyst', 'status': 'pending'}},
            {'id': 'risk_assessment', 'type': 'default', 'position': {'x': 650, 'y': 200}, 'data': {'label': 'Risk Assessment', 'status': 'pending'}},
            {'id': 'final_synthesis', 'type': 'output', 'position': {'x': 950, 'y': 200}, 'data': {'label': 'Final Report', 'status': 'pending'}},
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
    
    def _update_node_status(self, node_id: str, status: str, result: str = None):
        """Update a specific node's status and optionally its result."""
        for node in self.workflow_status.get('nodes', []):
            if node['id'] == node_id:
                node['data']['status'] = status
                if result:
                    node['data']['result'] = result
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