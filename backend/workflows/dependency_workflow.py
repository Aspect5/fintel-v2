# backend/workflows/dependency_workflow.py
import controlflow as cf
from typing import Dict, Any
from .base import BaseWorkflow, WorkflowResult

class DependencyDrivenWorkflow(BaseWorkflow):
    """Workflow using proper task dependencies following ControlFlow best practices"""
    
    def __init__(self):
        super().__init__(
            name="dependency_driven_analysis",
            description="Financial analysis using explicit task dependencies"
        )
    
    def execute(self, query: str, provider: str = "openai", **kwargs) -> WorkflowResult:
        """Execute workflow using DAG-based task dependencies"""
        start_time = time.time()
        
        try:
            from agents.registry import get_agent_registry
            agent_registry = get_agent_registry()
            
            # Get specialized agents
            market_agent = agent_registry.get_agent("MarketAnalyst", provider)
            economic_agent = agent_registry.get_agent("EconomicAnalyst", provider)
            financial_agent = agent_registry.get_agent("FinancialAnalyst", provider)
            
            with cf.Flow(name="dependency_driven_financial_analysis") as flow:
                # Task A: Market Data Gathering (no dependencies)
                market_analysis = cf.Task(
                    objective=f"Gather and analyze market data for: {query}",
                    agents=[market_agent],
                    result_type=dict
                )
                
                # Task B: Economic Context (no dependencies, can run parallel to A)
                economic_analysis = cf.Task(
                    objective=f"Analyze relevant economic indicators for: {query}",
                    agents=[economic_agent],
                    result_type=dict
                )
                
                # Task C: Risk Assessment (depends on both A and B)
                risk_assessment = cf.Task(
                    objective="Assess investment risks based on market and economic analysis",
                    depends_on=[market_analysis, economic_analysis],
                    agents=[financial_agent],
                    result_type=dict
                )
                
                # Task D: Final Synthesis (depends on all previous tasks)
                final_synthesis = cf.Task(
                    objective=f"""Synthesize comprehensive investment recommendation for: {query}
                    
                    Include:
                    1. Executive summary
                    2. Key findings from market analysis
                    3. Economic context and implications
                    4. Risk assessment summary
                    5. Actionable recommendations
                    6. Confidence level and caveats""",
                    depends_on=[market_analysis, economic_analysis, risk_assessment],
                    agents=[financial_agent],
                    result_type=str
                )
                
                # Running the final task automatically executes all dependencies
                result = final_synthesis.run()
            
            execution_time = time.time() - start_time
            
            return WorkflowResult(
                success=True,
                result=str(result),
                trace="Dependency-driven analysis with automatic orchestration",
                agent_invocations=[],
                execution_time=execution_time,
                workflow_name=self.name
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return WorkflowResult(
                success=False,
                result=f"Dependency-driven analysis failed: {str(e)}",
                trace=f"DAG execution error: {str(e)}",
                agent_invocations=[],
                execution_time=execution_time,
                error=str(e),
                workflow_name=self.name
            )