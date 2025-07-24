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
        self.workflow_status.update(update)
        for callback in self.status_callbacks:
            try:
                callback(self.workflow_status)
            except Exception as e:
                logger.error(f"Status callback error: {e}")
    
    def execute(self, query: str, provider: str = "openai", **kwargs) -> WorkflowResult:
        """Execute workflow with real-time status updates"""
        start_time = time.time()
        self.workflow_status['start_time'] = datetime.now().isoformat()
        self.workflow_status['status'] = 'running'
        
        logger.info(f"Starting workflow for query: {query}")
        
        # Initialize workflow visualization FIRST
        self._initialize_workflow_nodes(query)
        
        # Make sure the initial nodes/edges are in the status
        self._update_status({
            'nodes': self.workflow_status.get('nodes', []),
            'edges': self.workflow_status.get('edges', [])
        })
        
        try:
            from backend.agents.registry import get_agent_registry
            agent_registry = get_agent_registry()
            
            # Get specialized agents
            market_agent = agent_registry.get_agent("MarketAnalyst", provider)
            economic_agent = agent_registry.get_agent("EconomicAnalyst", provider)
            financial_agent = agent_registry.get_agent("FinancialAnalyst", provider)
            
            with cf.Flow(name="financial_analysis_flow") as flow:
                # Update visualization to show workflow start
                self._update_node_status('query_input', 'completed')
                self._update_edge_status('e1', 'active')
                self._update_edge_status('e2', 'active')
                
                # Task A: Market Analysis
                self._update_node_status('market_analysis', 'running')
                market_analysis_task = cf.Task(
                    objective=f"""Analyze market data for: {query}
                    
                    Requirements:
                    1. Get current stock price and key metrics
                    2. Analyze recent price trends
                    3. Provide 2-3 key market insights
                    
                    Be concise and focus on actionable information.""",
                    agents=[market_agent],
                    result_type=str
                )
                
                # Task B: Economic Analysis (parallel to market)
                self._update_node_status('economic_analysis', 'running')
                economic_analysis_task = cf.Task(
                    objective=f"""Provide economic context for: {query}
                    
                    Requirements:
                    1. Get key economic indicators (GDP, unemployment, interest rates)
                    2. Assess current economic conditions
                    3. Relate findings to investment implications
                    
                    Focus on current data and trends.""",
                    agents=[economic_agent],
                    result_type=str
                )
                
                # Execute parallel tasks
                logger.info("Executing market analysis...")
                market_result = market_analysis_task.run()
                self._update_node_status('market_analysis', 'completed', result=market_result)
                self._update_edge_status('e1', 'completed')
                self._update_edge_status('e3', 'active')
                
                logger.info("Executing economic analysis...")
                economic_result = economic_analysis_task.run()
                self._update_node_status('economic_analysis', 'completed', result=economic_result)
                self._update_edge_status('e2', 'completed')
                self._update_edge_status('e4', 'active')
                
                # Task C: Risk Assessment (depends on both A and B)
                self._update_node_status('risk_assessment', 'running')
                risk_assessment_task = cf.Task(
                    objective="Assess investment risks based on market and economic analysis",
                    depends_on=[market_analysis_task, economic_analysis_task],
                    agents=[financial_agent],
                    result_type=str
                )
                
                logger.info("Executing risk assessment...")
                risk_result = risk_assessment_task.run()
                self._update_node_status('risk_assessment', 'completed', result=risk_result)
                self._update_edge_status('e3', 'completed')
                self._update_edge_status('e4', 'completed')
                self._update_edge_status('e5', 'active')
                
                # Task D: Final Synthesis (depends on all previous)
                self._update_node_status('final_synthesis', 'running')
                final_synthesis_task = cf.Task(
                    objective=f"""Provide comprehensive investment recommendation for: {query}
                    
                    Include:
                    1. Executive summary
                    2. Key findings from market and economic analysis
                    3. Risk assessment summary
                    4. Clear investment recommendation
                    5. Confidence level (1-10)""",
                    depends_on=[market_analysis_task, economic_analysis_task, risk_assessment_task],
                    agents=[financial_agent],
                    result_type=str
                )
                
                logger.info("Executing final synthesis...")
                final_result = final_synthesis_task.run()
                self._update_node_status('final_synthesis', 'completed', result=final_result)
                self._update_edge_status('e5', 'completed')
                self._update_edge_status('e6', 'completed')
                self._update_edge_status('e7', 'completed')
            
            execution_time = time.time() - start_time
            self.workflow_status['status'] = 'completed'
            self.workflow_status['execution_time'] = execution_time
            
            logger.info(f"Workflow completed in {execution_time:.2f} seconds")
            
            return WorkflowResult(
                success=True,
                result=str(final_result),
                trace={
                    "market_analysis": market_result,
                    "economic_analysis": economic_result,
                    "risk_assessment": risk_result,
                    "final_synthesis": final_result
                },
                agent_invocations=[],
                execution_time=execution_time,
                workflow_name=self.name,
                workflow_status=self.workflow_status
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.workflow_status['status'] = 'failed'
            self.workflow_status['error'] = str(e)
            
            logger.error(f"Workflow failed: {e}", exc_info=True)
            return WorkflowResult(
                success=False,
                result=f"Analysis failed: {str(e)}",
                trace=f"Error: {str(e)}",
                agent_invocations=[],
                execution_time=execution_time,
                error=str(e),
                workflow_name=self.name,
                workflow_status=self.workflow_status
            )
    
    def _initialize_workflow_nodes(self, query):
        """Initialize workflow nodes showing the actual architecture"""
        nodes = [
            {
                'id': 'query_input',
                'type': 'input',
                'position': {'x': 50, 'y': 200},
                'data': {
                    'label': 'User Query',
                    'details': query[:100] + '...' if len(query) > 100 else query,
                    'status': 'running'
                }
            },
            {
                'id': 'market_analysis',
                'type': 'default',
                'position': {'x': 350, 'y': 100},
                'data': {
                    'label': 'Market Analyst',
                    'agentType': 'MarketAnalyst',
                    'details': 'Analyzing market data and trends',
                    'status': 'pending',
                    'toolCalls': []
                }
            },
            {
                'id': 'economic_analysis',
                'type': 'default',
                'position': {'x': 350, 'y': 300},
                'data': {
                    'label': 'Economic Analyst',
                    'agentType': 'EconomicAnalyst',
                    'details': 'Analyzing economic indicators',
                    'status': 'pending',
                    'toolCalls': []
                }
            },
            {
                'id': 'risk_assessment',
                'type': 'default',
                'position': {'x': 650, 'y': 200},
                'data': {
                    'label': 'Risk Assessment',
                    'agentType': 'FinancialAnalyst',
                    'details': 'Assessing investment risks',
                    'status': 'pending',
                    'toolCalls': []
                }
            },
            {
                'id': 'final_synthesis',
                'type': 'output',
                'position': {'x': 950, 'y': 200},
                'data': {
                    'label': 'Final Report',
                    'agentType': 'FinancialAnalyst',
                    'details': 'Synthesizing comprehensive recommendation',
                    'status': 'pending'
                }
            }
        ]
        
        edges = [
            {'id': 'e1', 'source': 'query_input', 'target': 'market_analysis', 'animated': False, 'style': {'stroke': '#666'}},
            {'id': 'e2', 'source': 'query_input', 'target': 'economic_analysis', 'animated': False, 'style': {'stroke': '#666'}},
            {'id': 'e3', 'source': 'market_analysis', 'target': 'risk_assessment', 'animated': False, 'style': {'stroke': '#666'}},
            {'id': 'e4', 'source': 'economic_analysis', 'target': 'risk_assessment', 'animated': False, 'style': {'stroke': '#666'}},
            {'id': 'e5', 'source': 'risk_assessment', 'target': 'final_synthesis', 'animated': False, 'style': {'stroke': '#666'}},
            {'id': 'e6', 'source': 'market_analysis', 'target': 'final_synthesis', 'animated': False, 'style': {'stroke': '#666'}},
            {'id': 'e7', 'source': 'economic_analysis', 'target': 'final_synthesis', 'animated': False, 'style': {'stroke': '#666'}}
        ]
        
        # Update the workflow_status
        self.workflow_status['nodes'] = nodes
        self.workflow_status['edges'] = edges
        
        # Trigger the update callback
        self._update_status({
            'nodes': nodes,
            'edges': edges
        })
    
    def _update_node_status(self, node_id: str, status: str, result: str = None):
        """Update specific node status"""
        for node in self.workflow_status['nodes']:
            if node['id'] == node_id:
                node['data']['status'] = status
                if result:
                    node['data']['result'] = result[:200] + "..." if len(result) > 200 else result
                break
        
        self._update_status({'nodes': self.workflow_status['nodes']})
        logger.info(f"Node {node_id} status updated to {status}")
    
    def _update_edge_status(self, edge_id: str, status: str):
        """Update edge visualization based on status"""
        for edge in self.workflow_status['edges']:
            if edge['id'] == edge_id:
                if status == 'active':
                    edge['animated'] = True
                    edge['style'] = {'stroke': '#58A6FF', 'strokeWidth': 2}
                elif status == 'completed':
                    edge['animated'] = False
                    edge['style'] = {'stroke': '#3FB950', 'strokeWidth': 2}
                break
        
        self._update_status({'edges': self.workflow_status['edges']})