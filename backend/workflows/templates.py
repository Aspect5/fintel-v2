from typing import Dict, Any, List
from .base import BaseWorkflow, WorkflowResult
from .coordinator import MultiAgentCoordinator

class SingleAgentWorkflow(BaseWorkflow):
    """Simple single-agent workflow"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        super().__init__(
            name=f"single_agent_{agent_name.lower()}",
            description=f"Analysis using {agent_name} agent"
        )
    
    def execute(self, query: str, provider: str = "openai", **kwargs) -> WorkflowResult:
        """Execute single agent workflow"""
        import time
        import controlflow as cf
        from agents.registry import get_agent_registry
        
        start_time = time.time()
        agent_registry = get_agent_registry()
        
        try:
            # Get agent
            agent = agent_registry.get_agent(self.agent_name, provider)
            if not agent:
                raise Exception(f"Agent {self.agent_name} not available")
            
            # Execute analysis
            with cf.Flow("single_agent_analysis") as flow:
                task = cf.Task(
                    "analyze_query",
                    instructions=f"Analyze the following query: {query}",
                    agents=[agent],
                    result_type=str
                )
                
                result = cf.run(task)
            
            execution_time = time.time() - start_time
            
            return WorkflowResult(
                success=True,
                result=str(result),
                trace=f"Single agent analysis completed using {self.agent_name}",
                agent_invocations=[{
                    "agent": self.agent_name,
                    "result": str(result),
                    "status": "completed"
                }],
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return WorkflowResult(
                success=False,
                result=f"Analysis failed: {str(e)}",
                trace=f"Single agent workflow error: {str(e)}",
                agent_invocations=[],
                execution_time=execution_time,
                error=str(e)
            )

# backend/workflows/templates.py
from typing import Dict, Any, List
from .base import BaseWorkflow, WorkflowResult
from .coordinator import MultiAgentCoordinator
from .dependency_workflow import DependencyDrivenWorkflow

class BestPracticeWorkflowTemplates:
    """Workflow templates following ControlFlow best practices"""
    
    def __init__(self):
        self._workflows: Dict[str, BaseWorkflow] = {
            # Moderated coordination strategy
            "coordinated": MultiAgentCoordinator(),
            
            # Dependency-driven DAG workflow  
            "dependency_driven": DependencyDrivenWorkflow(),
            
            # Single agent workflows for simple cases
            "market_focus": SingleAgentWorkflow("MarketAnalyst"),
            "economic_focus": SingleAgentWorkflow("EconomicAnalyst"),
        }
    
    def get_workflow(self, name: str) -> BaseWorkflow:
        """Get workflow by name with fallback to coordinated approach"""
        return self._workflows.get(name, self._workflows["coordinated"])
        
class WorkflowTemplates:
    """Collection of predefined workflow templates"""
    
    def __init__(self):
        self._workflows: Dict[str, BaseWorkflow] = {
            "comprehensive": MultiAgentCoordinator(),
            "market_analysis": SingleAgentWorkflow("MarketAnalyst"),
            "economic_analysis": SingleAgentWorkflow("EconomicAnalyst"),
            "financial_analysis": SingleAgentWorkflow("FinancialAnalyst")
        }
    
    def get_workflow(self, name: str) -> BaseWorkflow:
        """Get workflow by name"""
        return self._workflows.get(name)
    
    def get_available_workflows(self) -> List[str]:
        """Get list of available workflow names"""
        return list(self._workflows.keys())
    
    def get_workflow_info(self, name: str) -> Dict[str, Any]:
        """Get workflow information"""
        workflow = self._workflows.get(name)
        if workflow:
            return workflow.get_info()
        return {}

# Global templates instance
_templates = None

def get_workflow_templates() -> WorkflowTemplates:
    """Get global workflow templates instance"""
    global _templates
    if _templates is None:
        _templates = WorkflowTemplates()
    return _templates