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
        
        try:
            from backend.agents.registry import get_agent_registry
            agent_registry = get_agent_registry()
            
            # Get specialized agents
            market_agent = agent_registry.get_agent("MarketAnalyst", provider)
            economic_agent = agent_registry.get_agent("EconomicAnalyst", provider)
            financial_agent = agent_registry.get_agent("FinancialAnalyst", provider)
            
            # Initialize workflow visualization
            self._initialize_workflow_nodes(query)
            
            with cf.Flow(name="financial_analysis_flow") as flow:
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
                
                # Task C: Risk Assessment (depends on both A and B)
                risk_assessment_task = cf.Task(
                    objective="Assess investment risks based on market and economic analysis",
                    depends_on=[market_analysis_task, economic_analysis_task],
                    agents=[financial_agent],
                    result_type=str
                )
                
                # Task D: Final Synthesis (depends on all previous)
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
                
                # Execute tasks with status tracking
                logger.info("Executing market analysis...")
                market_result = market_analysis_task.run()
                self._update_node_status('market_analysis', 'success', result=market_result)
                
                logger.info("Executing economic analysis...")
                economic_result = economic_analysis_task.run()
                self._update_node_status('economic_analysis', 'success', result=economic_result)
                
                logger.info("Executing risk assessment...")
                self._update_node_status('risk_assessment', 'running')
                risk_result = risk_assessment_task.run()
                self._update_node_status('risk_assessment', 'success', result=risk_result)
                
                logger.info("Executing final synthesis...")
                self._update_node_status('final_synthesis', 'running')
                final_result = final_synthesis_task.run()
                self._update_node_status('final_synthesis', 'success', result=final_result)
            
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
                workflow_status=self.workflow_status  # Include for frontend
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
        """Initialize workflow nodes for visualization"""
        nodes = [
            {
                'id': 'coordinator',
                'type': 'coordinator',
                'position': {'x': 100, 'y': 200},
                'data': {
                    'label': 'Workflow Coordinator',
                    'details': f'Analyzing: {query}',
                    'status': 'running'
                }
            },
            {
                'id': 'market_analysis',
                'type': 'agent',
                'position': {'x': 400, 'y': 100},
                'data': {
                    'label': 'Market Analyst',
                    'details': 'Gathering market data and analyzing trends',
                    'status': 'pending',
                    'toolCalls': []
                }
            },
            {
                'id': 'economic_analysis',
                'type': 'agent',
                'position': {'x': 400, 'y': 300},
                'data': {
                    'label': 'Economic Analyst',
                    'details': 'Analyzing economic indicators and context',
                    'status': 'pending',
                    'toolCalls': []
                }
            },
            {
                'id': 'risk_assessment',
                'type': 'agent',
                'position': {'x': 700, 'y': 150},
                'data': {
                    'label': 'Risk Analyst',
                    'details': 'Assessing investment risks and opportunities',
                    'status': 'pending',
                    'toolCalls': []
                }
            },
            {
                'id': 'final_synthesis',
                'type': 'synthesizer',
                'position': {'x': 1000, 'y': 200},
                'data': {
                    'label': 'Final Synthesis',
                    'details': 'Generating comprehensive investment recommendation',
                    'status': 'pending'
                }
            }
        ]
        
        edges = [
            {'id': 'e1', 'source': 'coordinator', 'target': 'market_analysis'},
            {'id': 'e2', 'source': 'coordinator', 'target': 'economic_analysis'},
            {'id': 'e3', 'source': 'market_analysis', 'target': 'risk_assessment'},
            {'id': 'e4', 'source': 'economic_analysis', 'target': 'risk_assessment'},
            {'id': 'e5', 'source': 'risk_assessment', 'target': 'final_synthesis'},
            {'id': 'e6', 'source': 'market_analysis', 'target': 'final_synthesis'},
            {'id': 'e7', 'source': 'economic_analysis', 'target': 'final_synthesis'}
        ]
        
        self.workflow_status['nodes'] = nodes
        self.workflow_status['edges'] = edges
        self._update_status({'nodes': nodes, 'edges': edges})
    
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