# backend/workflows/coordinator.py
import time
from typing import Dict, Any, List
import controlflow as cf
from .base import BaseWorkflow, WorkflowResult
from agents.registry import get_agent_registry

class MultiAgentCoordinator(BaseWorkflow):
    """Coordinates multiple agents using ControlFlow's Moderated turn strategy"""
    
    def __init__(self):
        super().__init__(
            name="multi_agent_analysis",
            description="Comprehensive financial analysis using coordinated specialized agents"
        )
    
    def execute(self, query: str, provider: str = "openai", **kwargs) -> WorkflowResult:
        """Execute multi-agent workflow using ControlFlow best practices"""
        start_time = time.time()
        agent_registry = get_agent_registry()
        agent_invocations = []
        
        try:
            # Create specialized service agents
            market_agent = agent_registry.get_agent("MarketAnalyst", provider)
            economic_agent = agent_registry.get_agent("EconomicAnalyst", provider)
            financial_agent = agent_registry.get_agent("FinancialAnalyst", provider)
            
            # Create coordinator agent with more powerful model
            coordinator_config = agent_registry.get_agent("FinancialAnalyst", provider)
            if provider == "openai":
                coordinator = cf.Agent(
                    name="Coordinator",
                    instructions="""You are a senior financial coordinator. Your role is to:
                    1. Orchestrate the analysis between specialized agents
                    2. Decide which agent should act next based on the current context
                    3. Ensure comprehensive coverage of the financial query
                    4. Synthesize final recommendations""",
                    model="openai/gpt-4o"  # More powerful model for coordination
                )
            else:
                coordinator = financial_agent  # Fallback to existing agent
            
            # Use ControlFlow's declarative orchestration
            with cf.Flow(name="coordinated_financial_analysis") as flow:
                # Single task with multiple agents and Moderated turn strategy
                result = cf.run(
                    objective=f"""Provide a comprehensive financial analysis for: {query}
                    
                    Requirements:
                    1. Market analysis (price, trends, technical indicators)
                    2. Economic context (relevant economic indicators)
                    3. Investment recommendations with risk assessment
                    4. Final synthesis with actionable insights
                    
                    Each specialist should contribute their expertise, coordinated by the moderator.""",
                    agents=[market_agent, economic_agent, financial_agent, coordinator],
                    turn_strategy=cf.turn_strategies.Moderated(moderator=coordinator),
                    result_type=str
                )
            
            execution_time = time.time() - start_time
            
            return WorkflowResult(
                success=True,
                result=str(result),
                trace=f"Coordinated analysis completed using Moderated turn strategy",
                agent_invocations=[{
                    "coordination_strategy": "Moderated",
                    "agents_used": ["MarketAnalyst", "EconomicAnalyst", "FinancialAnalyst"],
                    "coordinator": "FinancialCoordinator"
                }],
                execution_time=execution_time,
                workflow_name=self.name
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return WorkflowResult(
                success=False,
                result=f"Coordinated analysis failed: {str(e)}",
                trace=f"Multi-agent coordination error: {str(e)}",
                agent_invocations=agent_invocations,
                execution_time=execution_time,
                error=str(e),
                workflow_name=self.name
            )