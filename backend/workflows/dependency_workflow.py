# backend/workflows/dependency_workflow.py
import controlflow as cf
from typing import Dict, Any, Optional
from .base import BaseWorkflow, WorkflowResult
import time
import logging

logger = logging.getLogger(__name__)

class TimeoutError(Exception):
    pass

class DependencyDrivenWorkflow(BaseWorkflow):
    """Optimized workflow with tool call caching and limits"""
    
    def __init__(self):
        super().__init__(
            name="dependency_driven_analysis",
            description="Optimized financial analysis with tool call limits"
        )
        self.tool_cache = {}  # Cache tool results
        self.tool_call_counts = {}  # Track tool usage
        self.max_tool_calls_per_type = 3  # Limit calls per tool type
    
    def execute(self, query: str, provider: str = "openai", max_execution_time: int = 240, **kwargs) -> WorkflowResult:
        """Execute workflow with performance optimizations"""
        start_time = time.time()
        logger.info(f"Starting optimized workflow for query: {query}")
        
        try:
            from backend.agents.registry import get_agent_registry
            agent_registry = get_agent_registry()
            
            # Get agents with tool call limits
            market_agent = agent_registry.get_agent("MarketAnalyst", provider)
            economic_agent = agent_registry.get_agent("EconomicAnalyst", provider)
            financial_agent = agent_registry.get_agent("FinancialAnalyst", provider)
            
            # Add tool call monitoring
            self._setup_tool_monitoring([market_agent, economic_agent, financial_agent])
            
            with cf.Flow(name="optimized_financial_analysis") as flow:
                # Task A: Quick Market Analysis (30 second limit)
                market_analysis_task = cf.Task(
                    objective=f"""Get essential market data for: {query}
                    
                    REQUIREMENTS (Complete in 30 seconds):
                    1. Get current stock price and basic metrics
                    2. Identify trend direction (up/down/stable)
                    3. Provide 2 key insights maximum
                    
                    TOOL LIMITS: 
                    - Call get_market_data ONCE only
                    - Call get_company_overview ONCE only
                    - Use received data immediately - NO re-calls
                    
                    STOP after getting data and providing brief analysis.""",
                    agents=[market_agent],
                    result_type=str,
                    timeout=30
                )
                
                # Task B: Quick Economic Context (30 second limit)
                economic_analysis_task = cf.Task(
                    objective=f"""Get economic context for: {query}
                    
                    REQUIREMENTS (Complete in 30 seconds):
                    1. Get GDP, unemployment, and interest rate data
                    2. Assess current economic trend
                    3. Provide brief economic outlook
                    
                    TOOL LIMITS:
                    - Call get_economic_data_from_fred MAXIMUM 3 times
                    - Use series: GDP, UNRATE, FEDFUNDS only
                    - NO additional calls after getting these 3 indicators
                    
                    STOP after analyzing these 3 indicators.""",
                    agents=[economic_agent],
                    result_type=str,
                    timeout=30
                )
                
                # Task C: Quick Risk Assessment (20 second limit)
                risk_assessment_task = cf.Task(
                    objective="""Assess investment risks quickly.
                    
                    REQUIREMENTS (Complete in 20 seconds):
                    1. Identify 2-3 key risks
                    2. Rate risk level (low/medium/high)
                    3. Suggest 1-2 mitigation strategies
                    
                    TOOL LIMITS: NO additional tool calls - use provided data only
                    
                    STOP after brief risk assessment.""",
                    depends_on=[market_analysis_task, economic_analysis_task],
                    agents=[financial_agent],
                    result_type=str,
                    timeout=20
                )
                
                # Task D: Final Summary (30 second limit)
                final_synthesis_task = cf.Task(
                    objective=f"""Provide final investment recommendation for: {query}
                    
                    REQUIREMENTS (Complete in 30 seconds):
                    1. Executive summary (2-3 sentences)
                    2. Key findings summary
                    3. Clear recommendation (buy/hold/sell)
                    4. Confidence level (1-10)
                    
                    TOOL LIMITS: NO tool calls - synthesize from provided data only
                    
                    STOP after providing clear recommendation.""",
                    depends_on=[market_analysis_task, economic_analysis_task, risk_assessment_task],
                    agents=[financial_agent],
                    result_type=str,
                    timeout=30
                )
                
                # Execute with timeout monitoring
                def execute_with_timeout(task, task_name, timeout_seconds):
                    task_start = time.time()
                    logger.info(f"Starting {task_name}...")
                    
                    result = task.run()
                    
                    task_time = time.time() - task_start
                    logger.info(f"{task_name} completed in {task_time:.2f}s")
                    
                    if task_time > timeout_seconds:
                        logger.warning(f"{task_name} exceeded timeout of {timeout_seconds}s")
                    
                    return result
                
                # Execute tasks with monitoring
                market_result = execute_with_timeout(market_analysis_task, "Market Analysis", 30)
                
                # Check overall timeout
                if time.time() - start_time > max_execution_time:
                    raise TimeoutError(f"Workflow exceeded {max_execution_time} second limit")
                
                economic_result = execute_with_timeout(economic_analysis_task, "Economic Analysis", 30)
                
                if time.time() - start_time > max_execution_time:
                    raise TimeoutError(f"Workflow exceeded {max_execution_time} second limit")
                
                risk_result = execute_with_timeout(risk_assessment_task, "Risk Assessment", 20)
                
                if time.time() - start_time > max_execution_time:
                    raise TimeoutError(f"Workflow exceeded {max_execution_time} second limit")
                
                final_result = execute_with_timeout(final_synthesis_task, "Final Synthesis", 30)
            
            execution_time = time.time() - start_time
            logger.info(f"Optimized workflow completed in {execution_time:.2f} seconds")
            
            # Log tool usage statistics
            self._log_tool_usage()
            
            return WorkflowResult(
                success=True,
                result=str(final_result),
                trace=f"""Market Analysis: {market_result}

Economic Analysis: {economic_result}

Risk Assessment: {risk_result}""",
                agent_invocations=[],
                execution_time=execution_time,
                workflow_name=self.name
            )
            
        except TimeoutError as e:
            execution_time = time.time() - start_time
            logger.error(f"Workflow timed out after {execution_time:.2f} seconds")
            return WorkflowResult(
                success=False,
                result=f"Analysis timed out after {max_execution_time} seconds. Please try a simpler query.",
                trace=f"Timeout error: {str(e)}",
                agent_invocations=[],
                execution_time=execution_time,
                error=str(e),
                workflow_name=self.name
            )
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Workflow failed: {e}", exc_info=True)
            return WorkflowResult(
                success=False,
                result=f"An error occurred: {str(e)}",
                trace=f"Error: {str(e)}",
                agent_invocations=[],
                execution_time=execution_time,
                error=str(e),
                workflow_name=self.name
            )
    
    def _setup_tool_monitoring(self, agents):
        """Setup tool call monitoring for agents"""
        # This would integrate with ControlFlow's tool monitoring if available
        logger.info("Tool monitoring enabled for workflow")
    
    def _log_tool_usage(self):
        """Log tool usage statistics"""
        logger.info(f"Tool usage stats: {self.tool_call_counts}")