import time
from typing import Dict, Any, List
import controlflow as cf
from .base import BaseWorkflow, WorkflowResult
from agents.registry import get_agent_registry

class MultiAgentCoordinator(BaseWorkflow):
    """Coordinates multiple agents for comprehensive analysis"""
    
    def __init__(self):
        super().__init__(
            name="multi_agent_analysis",
            description="Comprehensive financial analysis using multiple specialized agents"
        )
    
    def execute(self, query: str, provider: str = "openai", **kwargs) -> WorkflowResult:
        """Execute multi-agent workflow"""
        start_time = time.time()
        agent_registry = get_agent_registry()
        agent_invocations = []
        
        try:
            # Determine which agents to use based on query
            agents_to_use = self._determine_agents(query)
            
            # Create agents
            agents = {}
            for agent_name in agents_to_use:
                agent = agent_registry.get_agent(agent_name, provider)
                if agent:
                    agents[agent_name] = agent
            
            if not agents:
                raise Exception("No agents available for analysis")
            
            # Execute workflow using ControlFlow
            with cf.Flow(name="financial_analysis") as flow:
                # Create analysis tasks for each agent
                analysis_tasks = []
                
                for agent_name, agent in agents.items():
                    task = cf.Task(
                        f"analyze_with_{agent_name.lower()}",
                        instructions=f"Analyze the following query using your specialized knowledge: {query}",
                        agents=[agent],
                        result_type=str
                    )
                    analysis_tasks.append(task)
                
                # Create synthesis task
                if len(analysis_tasks) > 1:
                    synthesis_task = cf.Task(
                        "synthesize_analysis",
                        instructions=f"""
                        Synthesize the following analyses into a comprehensive financial report:
                        
                        Original Query: {query}
                        
                        Provide a well-structured analysis that:
                        1. Summarizes key findings from each analysis
                        2. Identifies important patterns and insights
                        3. Provides actionable recommendations
                        4. Highlights any risks or considerations
                        
                        Make the response comprehensive yet accessible.
                        """,
                        depends_on=analysis_tasks,
                        agents=[agents[list(agents.keys())[0]]],  # Use first agent for synthesis
                        result_type=str
                    )
                    
                    # Run the workflow
                    result = cf.run(synthesis_task)
                else:
                    # Single agent analysis
                    result = cf.run(analysis_tasks[0])
                
                # Collect agent invocations
                for task in analysis_tasks:
                    if hasattr(task, 'result') and task.result:
                        agent_invocations.append({
                            "agent": task.name,
                            "result": str(task.result),
                            "status": "completed"
                        })
            
            execution_time = time.time() - start_time
            
            return WorkflowResult(
                success=True,
                result=str(result),
                trace=f"Multi-agent analysis completed using {', '.join(agents.keys())}",
                agent_invocations=agent_invocations,
                execution_time=execution_time,
                workflow_name=self.name
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return WorkflowResult(
                success=False,
                result=f"Analysis failed: {str(e)}",
                trace=f"Multi-agent workflow error: {str(e)}",
                agent_invocations=agent_invocations,
                execution_time=execution_time,
                error=str(e),
                workflow_name=self.name
            )
    
    def _determine_agents(self, query: str) -> List[str]:
        """Determine which agents to use based on query content"""
        query_lower = query.lower()
        agents = []
        
        # Check for stock/company analysis
        if any(keyword in query_lower for keyword in ['stock', 'company', 'ticker', 'share', 'equity']):
            agents.append("MarketAnalyst")
        
        # Check for economic analysis
        if any(keyword in query_lower for keyword in ['economy', 'economic', 'gdp', 'inflation', 'unemployment', 'fed', 'interest rate']):
            agents.append("EconomicAnalyst")
        
        # Always include financial analyst for comprehensive analysis
        agents.append("FinancialAnalyst")
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(agents))