import pytest
from unittest.mock import patch, Mock
from backend.workflows.base import WorkflowResult
from backend.workflows.orchestrator import WorkflowOrchestrator

class TestFullWorkflowIntegration:
    @pytest.mark.integration
    @patch('backend.workflows.dependency_workflow.DependencyDrivenWorkflow.execute')
    def test_end_to_end_financial_analysis(self, mock_execute, sample_workflow_query, mock_api_keys):
        """Test complete end-to-end financial analysis workflow"""
        mock_result = WorkflowResult(
            success=True,
            result="Comprehensive financial analysis of AAPL completed",
            trace="Analysis completed successfully",
            agent_invocations=[
                {"agent": "FinancialAnalyst", "result": "AAPL analysis", "status": "completed"}
            ],
            execution_time=25.0,
            workflow_name="dependency_driven",
            error=None
        )
        mock_execute.return_value = mock_result
        
        orchestrator = WorkflowOrchestrator()
        
        result = orchestrator.execute_workflow(
            query=sample_workflow_query,
            provider="openai",
            workflow_name="dependency_driven"
        )
        
        assert result.success is True
        assert "AAPL" in result.result
        assert result.execution_time > 0
        assert result.workflow_name == "dependency_driven"
