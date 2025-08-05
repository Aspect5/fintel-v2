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
        """Update workflow status and notify callbacks"""
        self.execution_context.update(update)
        
        # Add timestamp
        update['timestamp'] = datetime.now().isoformat()
        
        # Notify all callbacks
        for callback in self.status_callbacks:
            try:
                callback(update)
            except Exception as e:
                logger.error(f"Status callback error: {e}")
    
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
                return "AAPL"  # Fallback for demo
                
        except Exception as e:
            logger.error(f"Ticker detection error: {e}")
            return "AAPL"  # Fallback for demo
    
    def _should_include_agent_for_query(self, agent_config: Dict[str, Any], query: str) -> bool:
        """Determine if agent should be included based on query analysis"""
        
        # Always include required agents
        if agent_config.get('required', False):
            return True
        
        # Use keyword-based selection from config
        role = agent_config.get('role')
        return self.config_loader.should_include_agent(self.workflow_type, role, query)
    
    @cf.flow
    def execute(self, query: str, provider: str = "openai", **kwargs) -> BaseWorkflowResult:
        """
        Main workflow execution using ControlFlow patterns
        
        This method orchestrates the entire workflow using ControlFlow's
        task dependency system and structured result handling.
        """
        start_time = datetime.now()
        workflow_id = kwargs.get('workflow_id', 'unknown')
        
        try:
            logger.info(f"Starting config-driven workflow {workflow_id}: {self.workflow_type}")
            
            # Update initial status
            self._update_status({
                'status': 'initializing',
                'workflow_id': workflow_id,
                'workflow_type': self.workflow_type,
                'query': query,
                'provider': provider
            })
            
            # Extract ticker from query
            ticker = self._extract_ticker_from_query(query)
            self.execution_context['ticker'] = ticker
            
            self._update_status({
                'status': 'creating_agents',
                'ticker': ticker
            })
            
            # Create agents for this workflow execution (isolated per execution)
            agents = self.agent_factory.create_agents_for_workflow(self.workflow_type, provider)
            
            self._update_status({
                'status': 'executing_tasks',
                'agents_created': len(agents),
                'available_agents': list(agents.keys())
            })
            
            # Execute workflow using ControlFlow task orchestration
            result = self._execute_workflow_tasks(query, ticker, agents)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self._update_status({
                'status': 'completed',
                'execution_time': execution_time,
                'result_summary': f"Analysis completed for {ticker}"
            })
            
            # Build workflow result
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
            
            logger.error(f"Workflow {workflow_id} failed: {e}")
            
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
        
        This follows ControlFlow patterns for dependent tasks and structured results.
        """
        
        # Create main workflow context
        workflow_context = {
            "query": query,
            "ticker": ticker,
            "workflow_type": self.workflow_type
        }
        
        # Task 1: Market Analysis (if agent available)
        market_analysis_result = None
        if 'market_analysis' in agents:
            self._update_status({'current_task': 'market_analysis'})
            
            market_analysis_result = cf.run(
                f"Analyze market data for {ticker}",
                instructions=f"""
                Use your available tools to gather and analyze market data for {ticker}.
                
                Steps:
                1. Get current market data using get_market_data(ticker='{ticker}')
                2. Get company overview using get_company_overview(ticker='{ticker}')
                3. Analyze the data and provide insights
                
                Provide a comprehensive market analysis summary.
                """,
                agents=[agents['market_analysis']],
                result_type=MarketAnalysisResult,
                context=workflow_context,
                max_agent_turns=3
            )
            
            self.task_results['market_analysis'] = market_analysis_result
        
        # Task 2: Risk Assessment (if agent available, depends on market analysis)
        risk_assessment_result = None
        if 'risk_assessment' in agents:
            self._update_status({'current_task': 'risk_assessment'})
            
            # Build context including previous results
            risk_context = workflow_context.copy()
            if market_analysis_result:
                risk_context['market_analysis'] = market_analysis_result
            
            risk_assessment_result = cf.run(
                f"Assess investment risk for {ticker}",
                instructions=f"""
                Assess the investment risk for {ticker} based on available data.
                
                Consider:
                - Market volatility and trends
                - Company fundamentals
                - Sector-specific risks
                - Overall market conditions
                
                Provide a comprehensive risk assessment with clear risk level and factors.
                """,
                agents=[agents['risk_assessment']],
                result_type=RiskAssessmentResult,
                context=risk_context,
                max_agent_turns=2
            )
            
            self.task_results['risk_assessment'] = risk_assessment_result
        
        # Task 3: Final Synthesis (uses results from previous tasks)
        self._update_status({'current_task': 'final_synthesis'})
        
        # Find best agent for synthesis (prefer FinancialAnalyst, fallback to any available)
        synthesis_agent = self._select_synthesis_agent(agents)
        
        # Build comprehensive context for synthesis
        synthesis_context = workflow_context.copy()
        if market_analysis_result:
            synthesis_context['market_analysis'] = market_analysis_result
        if risk_assessment_result:
            synthesis_context['risk_assessment'] = risk_assessment_result
        
        final_analysis = cf.run(
            f"Create comprehensive investment analysis for {ticker}",
            instructions=f"""
            Create a comprehensive investment analysis for {ticker} based on all available information.
            
            Available data:
            - Market Analysis: {market_analysis_result.analysis_summary if market_analysis_result else 'Not available'}
            - Risk Assessment: {risk_assessment_result.risk_summary if risk_assessment_result else 'Not available'}
            
            Provide:
            1. Clear investment recommendation (Buy/Hold/Sell)
            2. Confidence level (0.0 to 1.0)
            3. Key insights (3-5 bullet points)
            4. Overall sentiment (positive/negative/neutral)
            5. Risk assessment summary
            
            Base your analysis on the available data and provide actionable insights.
            """,
            agents=[synthesis_agent],
            result_type=InvestmentAnalysis,
            context=synthesis_context,
            max_agent_turns=3
        )
        
        self.task_results['final_synthesis'] = final_analysis
        return final_analysis
    
    def _select_synthesis_agent(self, agents: Dict[str, cf.Agent]) -> cf.Agent:
        """Select the best available agent for final synthesis"""
        
        # Preferred order for synthesis
        preferred_roles = ['sentiment_classification', 'recommendation', 'market_analysis']
        
        for role in preferred_roles:
            if role in agents:
                return agents[role]
        
        # Fallback to any available agent
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
        # This would be enhanced to track actual agent calls
        # For now, return basic information
        return [
            {
                'task': task_name,
                'status': 'completed' if task_name in self.task_results else 'skipped',
                'timestamp': datetime.now().isoformat()
            }
            for task_name in ['market_analysis', 'risk_assessment', 'final_synthesis']
        ]

def create_config_driven_workflow(workflow_type: str = "quick_stock_analysis") -> ConfigDrivenWorkflow:
    """
    Factory function to create config-driven workflow instances
    
    Args:
        workflow_type: Type of workflow from workflow_config.yaml
        
    Returns:
        ConfigDrivenWorkflow instance
    """
    return ConfigDrivenWorkflow(workflow_type)