import time
from typing import Dict, Any, Optional
from .base import WorkflowResult
from .templates import get_workflow_templates
from .coordinator import MultiAgentCoordinator

class WorkflowOrchestrator:
    """Main orchestrator for workflow execution"""
    
    def __init__(self):
        self.templates = get_workflow_templates()
        self.default_workflow = MultiAgentCoordinator()
    
    def execute_workflow(
        self,
        query: str,
        provider: str = "openai",
        workflow_name: str = "comprehensive",
        timeout: int = 45,
        **kwargs
    ) -> WorkflowResult:
        """Execute a workflow with timeout handling"""
        
        # Get workflow
        workflow = self.templates.get_workflow(workflow_name)
        if not workflow:
            workflow = self.default_workflow
        
        # Execute with timeout
        import threading
        result_container = {}
        
        def run_workflow():
            try:
                result = workflow.execute(query, provider, **kwargs)
                result_container['result'] = result
            except Exception as e:
                result_container['result'] = WorkflowResult(
                    success=False,
                    result=f"Workflow execution failed: {str(e)}",
                    trace=f"Orchestrator error: {str(e)}",
                    agent_invocations=[],
                    execution_time=0,
                    error=str(e)
                )
        
        # Run in thread with timeout
        thread = threading.Thread(target=run_workflow)
        thread.daemon = True
        thread.start()
        thread.join(timeout=timeout)
        
        if thread.is_alive():
            # Timeout occurred
            return WorkflowResult(
                success=False,
                result=f"Analysis of '{query}' timed out after {timeout} seconds. This might be due to API rate limits or high demand. Please try again.",
                trace=f"Workflow timed out after {timeout} seconds",
                agent_invocations=[],
                execution_time=timeout,
                error="Timeout"
            )
        
        return result_container.get('result', WorkflowResult(
            success=False,
            result="Unknown error occurred",
            trace="No result generated",
            agent_invocations=[],
            execution_time=0,
            error="Unknown error"
        ))
    
    def get_available_workflows(self) -> Dict[str, Any]:
        """Get information about available workflows"""
        workflows = {}
        for name in self.templates.get_available_workflows():
            workflows[name] = self.templates.get_workflow_info(name)
        return workflows
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        return {
            "available_workflows": self.get_available_workflows(),
            "default_workflow": self.default_workflow.name,
            "status": "ready"
        }

# Global orchestrator instance
_orchestrator = None

def get_orchestrator() -> WorkflowOrchestrator:
    """Get global orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = WorkflowOrchestrator()
    return _orchestrator