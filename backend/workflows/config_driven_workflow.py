# backend/workflows/config_driven_workflow.py
"""
Config-Driven ControlFlow Workflow

Completely replaces hardcoded workflows with configuration-driven execution.
Uses proper ControlFlow patterns for task orchestration and dependency management.
"""

import controlflow as cf
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Literal
from pydantic import BaseModel, Field

from .base import BaseWorkflow, WorkflowResult as BaseWorkflowResult
from .config_loader import get_workflow_config_loader
from ..utils.logging import setup_logging
from ..utils.monitoring import WorkflowMonitor

logger = setup_logging()

class InvestmentAnalysis(BaseModel):
    """Structured result model for investment analysis"""
    ticker: str = Field(description="Stock ticker symbol")
    market_analysis: str = Field(description="Market analysis summary")
    sentiment: Literal["positive", "negative", "neutral"] = Field(description="Overall sentiment")
    recommendation: str = Field(description="Investment recommendation")
    confidence: float = Field(description="Confidence level (0-1)", ge=0, le=1)
    key_insights: List[str] = Field(description="Key insights", min_items=1, max_items=5)
    risk_assessment: str = Field(description="Risk assessment summary")

class MarketAnalysisResult(BaseModel):
    """Result from market analysis task"""
    ticker: str
    current_price: Optional[float] = None
    market_data: str
    company_overview: str
    analysis_summary: str

class RiskAssessmentResult(BaseModel):
    """Result from risk assessment task"""
    ticker: str
    risk_level: Literal["Low", "Medium", "High"]
    risk_factors: List[str]
    risk_summary: str

class ConfigDrivenWorkflow(BaseWorkflow):
    """
    ControlFlow-native workflow that builds itself from configuration.
    Completely replaces hardcoded workflow implementations.
    """
    
    def __init__(self, workflow_type: str = "quick_stock_analysis"):
        """Initialize workflow with configuration validation"""
        
        self.workflow_type = workflow_type
        super().__init__(
            name=f"config_driven_{workflow_type}",
            description=f"Config-driven {workflow_type} workflow using ControlFlow patterns"
        )
        
        # Initialize core components
        self.config_loader = get_workflow_config_loader()
        
        # Import registry manager and agent factory here to avoid circular imports
        from ..registry.manager import get_registry_manager
        from ..agents.factory import get_agent_factory
        
        self.registry_manager = get_registry_manager()
        self.agent_factory = get_agent_factory()
        
        # Load and validate workflow configuration
        self.workflow_config = self._load_and_validate_config()
        
        # Workflow execution state
        self.execution_context = {}
        self.task_results = {}
        self.status_callbacks = []
        
        # Initialize workflow status for tracking
        self.workflow_status = {
            'status': 'initialized',
            'nodes': [],
            'edges': [],
            'result': None,
            'enhanced_result': None,
            'execution_time': 0,
            'workflow_name': self.name,
            'workflow_type': workflow_type
        }
        
        logger.info(f"Initialized config-driven workflow: {workflow_type}")
    
    def _load_and_validate_config(self) -> Dict[str, Any]:
        """Load and strictly validate workflow configuration"""
        
        config = self.config_loader.get_workflow_config(self.workflow_type)
        if not config:
            raise ValueError(f"Workflow type '{self.workflow_type}' not found in configuration")
        
        # Validate required configuration sections
        required_sections = ['agents']
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Workflow configuration missing required section: {section}")
        
        # Validate that we have at least one required agent
        agents = config.get('agents', [])
        required_agents = [agent for agent in agents if agent.get('required', False)]
        if not required_agents:
            raise ValueError(f"Workflow '{self.workflow_type}' must have at least one required agent")
        
        logger.info(f"Configuration validated for workflow: {self.workflow_type}")
        return config
    
    def add_status_callback(self, callback):
        """Add callback for status updates"""
        self.status_callbacks.append(callback)
    
    def _update_status(self, update: Dict[str, Any]):
        """Update workflow status and notify callbacks with enhanced live inspection data"""
        self.execution_context.update(update)
        
        # Add timestamp
        update['timestamp'] = datetime.now().isoformat()
        
        # Enhanced live inspection data
        if 'current_task' in update:
            task_details = {
                'task_name': update['current_task'],
                'task_progress': self._get_task_progress(update['current_task']),
                'agent_reasoning': self._get_current_agent_reasoning(),
                'tool_calls': self._get_recent_tool_calls(),
                'execution_context': self.execution_context.copy()
            }
            update['live_details'] = task_details
        
        # Add workflow-level metrics
        update['workflow_metrics'] = self._get_workflow_metrics()
        
        # Generate workflow graph for frontend visualization
        try:
            workflow_graph = self._generate_workflow_graph()
            update['nodes'] = workflow_graph['nodes']
            update['edges'] = workflow_graph['edges']
            update['hasNodes'] = True if workflow_graph['nodes'] else False
        except Exception as e:
            logger.error(f"Error generating workflow graph: {e}", exc_info=True)
            update['nodes'] = []
            update['edges'] = []
            update['hasNodes'] = False
        
        # Notify all callbacks
        for callback in self.status_callbacks:
            try:
                callback(update)
            except Exception as e:
                logger.error(f"Status callback error: {e}")
    
    def _get_task_progress(self, task_name: str) -> Dict[str, Any]:
        """Get detailed progress information for a specific task"""
        return {
            'task_name': task_name,
            'status': 'running',
            'start_time': self.execution_context.get(f'{task_name}_start_time'),
            'current_step': self.execution_context.get(f'{task_name}_current_step', 'initializing'),
            'steps_completed': self.execution_context.get(f'{task_name}_steps_completed', 0),
            'total_steps': self.execution_context.get(f'{task_name}_total_steps', 1)
        }
    
    def _get_current_agent_reasoning(self) -> Optional[str]:
        """Get the most recent agent reasoning from the event handler"""
        try:
            if hasattr(self, 'event_handler') and self.event_handler:
                if hasattr(self.event_handler, 'get_events_by_type'):
                    events = self.event_handler.get_events_by_type('agent_message')
                    if events:
                        latest_event = events[-1]
                        return latest_event.get('message_content', 'No reasoning available')
        except Exception as e:
            logger.warning(f"Could not retrieve agent reasoning: {e}")
        return None
    
    def _get_recent_tool_calls(self) -> List[Dict[str, Any]]:
        """Get recent tool calls for live inspection"""
        try:
            if hasattr(self, 'event_handler') and self.event_handler:
                if hasattr(self.event_handler, 'get_events_by_type'):
                    tool_events = self.event_handler.get_events_by_type('agent_tool_call')
                    return tool_events[-3:] if tool_events else []
        except Exception as e:
            logger.warning(f"Could not retrieve tool calls: {e}")
        return []
    
    def _extract_ticker_from_query(self, query: str) -> str:
        """Extract ticker symbol using AI-powered detection"""
        try:
            from ..tools.builtin_tools import _detect_ticker_with_ai
            
            detection_result = _detect_ticker_with_ai(query)
            
            if detection_result["status"] == "success" and detection_result["ticker"] != "UNKNOWN":
                logger.info(f"AI detected ticker: {detection_result['ticker']}")
                return detection_result["ticker"]
            else:
                logger.warning("AI ticker detection failed, using fallback")
                return "AAPL"
                
        except Exception as e:
            logger.error(f"Ticker detection error: {e}")
            return "AAPL"
    
    def _should_include_agent_for_query(self, agent_config: Dict[str, Any], query: str) -> bool:
        """Determine if agent should be included based on query analysis"""
        if agent_config.get('required', False):
            return True
        
        role = agent_config.get('role')
        return self.config_loader.should_include_agent(self.workflow_type, role, query)
    
    @cf.flow
    def execute(self, query: str, provider: str = "openai", **kwargs) -> BaseWorkflowResult:
        """
        Main workflow execution using ControlFlow patterns
        """
        start_time = datetime.now()
        workflow_id = kwargs.get('workflow_id', 'unknown')
        
        self.execution_context['start_time'] = start_time
        
        try:
            logger.info(f"Starting config-driven workflow {workflow_id}: {self.workflow_type}")
            
            self._update_status({
                'status': 'initializing',
                'workflow_id': workflow_id,
                'workflow_type': self.workflow_type,
                'query': query,
                'provider': provider
            })
            
            ticker = self._extract_ticker_from_query(query)
            self.execution_context['ticker'] = ticker
            
            self._update_status({'status': 'creating_agents', 'ticker': ticker})
            
            agents = self.agent_factory.create_agents_for_workflow(self.workflow_type, provider)
            
            self._update_status({
                'status': 'executing_tasks',
                'agents_created': len(agents),
                'available_agents': list(agents.keys())
            })
            
            result = self._execute_workflow_tasks(query, ticker, agents)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self._update_status({
                'status': 'completed',
                'execution_time': execution_time,
                'result_summary': f"Analysis completed for {ticker}"
            })
            
            return BaseWorkflowResult(
                success=True,
                result=result.dict(),
                trace=self._build_execution_trace(),
                agent_invocations=self._build_agent_invocations(),
                execution_time=execution_time,
                workflow_name=self.name
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_message = f"Config-driven workflow failed: {str(e)}"
            logger.error(f"Workflow {workflow_id} failed: {e}", exc_info=True)
            
            self._update_status({
                'status': 'failed',
                'error': error_message,
                'execution_time': execution_time
            })
            
            return BaseWorkflowResult(
                success=False,
                result="",
                trace={'error': error_message, 'context': self.execution_context},
                agent_invocations=self._build_agent_invocations(),
                execution_time=execution_time,
                workflow_name=self.name,
                error=error_message
            )
    
    def _execute_workflow_tasks(self, query: str, ticker: str, agents: Dict[str, cf.Agent]) -> InvestmentAnalysis:
        """
        Execute workflow tasks using ControlFlow task orchestration
        """
        workflow_context = {"query": query, "ticker": ticker, "workflow_type": self.workflow_type}
        
        from ..utils.monitoring import FintelEventHandler
        self.event_handler = FintelEventHandler()
        
        market_analysis_result = None
        if 'market_analysis' in agents:
            self._update_status({
                'current_task': 'market_analysis',
                'task_details': 'Analyzing market data and company fundamentals'
            })
            self.execution_context['market_analysis_start_time'] = datetime.now().isoformat()
            market_analysis_result = cf.run(
                f"Analyze market data for {ticker}",
                instructions=f"Use get_market_data(ticker='{ticker}') and get_company_overview(ticker='{ticker}') to provide a market analysis.",
                agents=[agents['market_analysis']],
                result_type=MarketAnalysisResult,
                context=workflow_context,
                max_agent_turns=3
            )
            self.task_results['market_analysis'] = market_analysis_result
        
        risk_assessment_result = None
        if 'risk_assessment' in agents:
            self._update_status({
                'current_task': 'risk_assessment',
                'task_details': 'Assessing investment risks and market volatility'
            })
            risk_context = workflow_context.copy()
            if market_analysis_result:
                risk_context['market_analysis'] = market_analysis_result
            
            risk_assessment_result = cf.run(
                f"Assess investment risk for {ticker}",
                instructions="Assess investment risk based on available data, including market analysis.",
                agents=[agents['risk_assessment']],
                result_type=RiskAssessmentResult,
                context=risk_context,
                max_agent_turns=2
            )
            self.task_results['risk_assessment'] = risk_assessment_result
        
        self._update_status({
            'current_task': 'final_synthesis',
            'task_details': 'Synthesizing analysis into a comprehensive recommendation'
        })
        synthesis_agent = self._select_synthesis_agent(agents)
        synthesis_context = workflow_context.copy()
        if market_analysis_result:
            synthesis_context['market_analysis'] = market_analysis_result
        if risk_assessment_result:
            synthesis_context['risk_assessment'] = risk_assessment_result
            
        final_analysis = cf.run(
            f"Create comprehensive investment analysis for {ticker}",
            instructions="Create a final investment analysis based on all available data. Provide recommendation, confidence, insights, sentiment, and risk summary.",
            agents=[synthesis_agent],
            result_type=InvestmentAnalysis,
            context=synthesis_context,
            max_agent_turns=3
        )
        self.task_results['final_synthesis'] = final_analysis
        
        return final_analysis
    
    def _select_synthesis_agent(self, agents: Dict[str, cf.Agent]) -> cf.Agent:
        """Select the best available agent for final synthesis"""
        preferred_roles = ['sentiment_classification', 'recommendation', 'market_analysis']
        for role in preferred_roles:
            if role in agents:
                return agents[role]
        if agents:
            return list(agents.values())[0]
        raise ValueError("No agents available for synthesis")
    
    def _build_execution_trace(self) -> Dict[str, Any]:
        """Build execution trace for debugging and monitoring"""
        return {
            'workflow_type': self.workflow_type,
            'execution_context': self.execution_context,
            'task_results': {
                task_name: (result.dict() if hasattr(result, 'dict') else str(result))
                for task_name, result in self.task_results.items()
            },
            'configuration_used': self.workflow_config
        }
    
    def _build_agent_invocations(self) -> List[Dict[str, Any]]:
        """Build agent invocation history for monitoring"""
        return [
            {
                'task': task_name,
                'status': 'completed' if task_name in self.task_results else 'skipped',
                'timestamp': datetime.now().isoformat()
            }
            for task_name in ['market_analysis', 'risk_assessment', 'final_synthesis']
        ]
    
    def _get_task_status(self, task_role: str, workflow_status: str, current_task: Optional[str]) -> str:
        """Determine the status of a task based on workflow context."""
        if task_role in self.task_results:
            # You might want to check for failure within the result object if applicable
            return 'completed'
        if task_role == current_task:
            return 'running'
        if workflow_status == 'failed' and task_role != current_task:
            return 'pending' # Or 'cancelled' if you want to be more specific
        
        # Check if task is upstream of the current running task
        defined_tasks = [agent.get('role') for agent in self.workflow_config.get('agents', [])]
        try:
            current_task_index = defined_tasks.index(current_task)
            task_index = defined_tasks.index(task_role)
            if task_index < current_task_index:
                return 'completed' # Should have been completed if we are past it
        except (ValueError, TypeError):
             # A task isn't in the defined list, or current_task is None
            pass

        return 'pending'

    def _generate_workflow_graph(self) -> Dict[str, List[Dict[str, Any]]]:
        """Dynamically generate workflow nodes and edges for frontend visualization."""
        nodes, edges = [], []
        agent_configs = self.workflow_config.get('agents', [])
        current_task = self.execution_context.get('current_task')
        workflow_status = self.execution_context.get('status', 'initializing')

        if not agent_configs:
            return {"nodes": [], "edges": []}

        node_width, x_pos, y_pos = 280, 0, 100
        
        # Input Node
        nodes.append({
            "id": "input", "type": "input", "position": {"x": x_pos, "y": y_pos},
            "data": {"label": "User Query", "status": "completed", "description": self.execution_context.get('query', '')}
        })
        last_node_id = "input"
        x_pos += node_width

        # Agent/Task Nodes
        all_agent_roles = [ac.get('role') for ac in agent_configs if ac.get('role')]
        
        for agent_config in agent_configs:
            role = agent_config.get('role')
            if not role: continue

            status = self._get_task_status(role, workflow_status, current_task)
            
            nodes.append({
                "id": f"task_{role}", "type": "task", "position": {"x": x_pos, "y": y_pos},
                "data": {
                    "label": agent_config.get('label', role.replace('_', ' ').title()),
                    "status": status,
                    "description": agent_config.get('description', ''),
                    "agentName": agent_config.get('name', 'N/A'),
                    "tools": [t.get('name', '') for t in self.registry_manager.get_tools_for_agent(role)],
                    "liveDetails": self._get_live_details_for_agent(role) if status == 'running' else None,
                }
            })
            edges.append({"id": f"edge_{last_node_id}_to_task_{role}", "source": last_node_id, "target": f"task_{role}", "type": "depends_on"})
            last_node_id = f"task_{role}"
            x_pos += node_width

        # Synthesis Task (as a virtual node)
        synthesis_status = self._get_task_status('final_synthesis', workflow_status, current_task)
        nodes.append({
            "id": "task_final_synthesis", "type": "task", "position": {"x": x_pos, "y": y_pos},
            "data": {
                "label": "Final Synthesis", "status": synthesis_status, "description": "Synthesizing all analyses into a final report.",
                "liveDetails": self._get_live_details_for_agent('final_synthesis') if synthesis_status == 'running' else None,
            }
        })
        edges.append({"id": f"edge_{last_node_id}_to_task_final_synthesis", "source": last_node_id, "target": "task_final_synthesis", "type": "depends_on"})
        last_node_id = "task_final_synthesis"
        x_pos += node_width
        
        # Output Node
        output_status = "completed" if workflow_status == "completed" else "pending"
        result_data = self.task_results.get('final_synthesis')
        nodes.append({
            "id": "output", "type": "output", "position": {"x": x_pos, "y": y_pos},
            "data": {
                "label": "Final Report", "status": output_status, 
                "result": result_data.dict() if isinstance(result_data, BaseModel) else result_data
            }
        })
        edges.append({"id": f"edge_{last_node_id}_to_output", "source": last_node_id, "target": "output", "type": "produces"})

        return {"nodes": nodes, "edges": edges}


    def _get_live_details_for_agent(self, agent_role: str) -> Optional[Dict[str, Any]]:
        """Get live details for a specific agent if it's the current task."""
        if self.execution_context.get('current_task') == agent_role:
            return {
                'task_name': agent_role,
                'task_progress': self._get_task_progress(agent_role),
                'agent_reasoning': self._get_current_agent_reasoning(),
                'tool_calls': self._get_recent_tool_calls()
            }
        return None
    
    def _get_workflow_metrics(self) -> Dict[str, Any]:
        """Get current workflow metrics"""
        start_time = self.execution_context.get('start_time')
        execution_time = (datetime.now() - start_time).total_seconds() if start_time else 0
        
        # Count based on actual tasks executed or defined
        tasks_in_config = self.workflow_config.get('agents', [])
        total_tasks = len(tasks_in_config) + 1 # Add 1 for synthesis

        return {
            'total_tasks': total_tasks,
            'completed_tasks': len(self.task_results),
            'execution_time': execution_time
        }

def create_config_driven_workflow(workflow_type: str = "quick_stock_analysis") -> ConfigDrivenWorkflow:
    """
    Factory function to create config-driven workflow instances
    """
    return ConfigDrivenWorkflow(workflow_type)
