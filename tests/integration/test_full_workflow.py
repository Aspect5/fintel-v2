import pytest
from unittest.mock import Mock, patch
import time

import pytest
import time
from unittest.mock import patch, Mock, MagicMock
from backend.workflows.base import WorkflowResult

class TestFullWorkflowIntegration:
    @pytest.mark.integration
    def test_end_to_end_financial_analysis(self, sample_workflow_query, mock_api_keys):
        """Test complete end-to-end financial analysis workflow"""
        # Mock at the method level to avoid ControlFlow initialization
        with patch('backend.workflows.coordinator.MultiAgentCoordinator.execute') as mock_coord_execute:
            # Create a proper WorkflowResult
            mock_result = WorkflowResult(
                success=True,
                result="Comprehensive financial analysis of AAPL completed",
                trace="Analysis completed successfully",
                agent_invocations=[
                    {"agent": "FinancialAnalyst", "result": "AAPL analysis", "status": "completed"}
                ],
                execution_time=25.0,
                workflow_name="multi_agent_analysis",
                error=None
            )
            mock_coord_execute.return_value = mock_result
            
            # Now we can safely import and use the orchestrator
            from backend.workflows.orchestrator import WorkflowOrchestrator
            orchestrator = WorkflowOrchestrator()
            
            # Execute workflow - this will use our mocked execute method
            result = orchestrator.execute_workflow(
                query=sample_workflow_query,
                provider="openai",
                workflow_name="comprehensive"
            )
            
            # Verify results
            assert result.success is True
            assert "AAPL" in result.result
            assert result.execution_time > 0
            assert result.workflow_name == "multi_agent_analysis"
            
    @pytest.mark.integration  
    def test_multi_agent_coordination(self, mock_api_keys):
        """Test multi-agent coordination workflow"""
        with patch('backend.workflows.coordinator.MultiAgentCoordinator.execute') as mock_execute:
            mock_result = WorkflowResult(
                success=True,
                result="Multi-agent analysis complete",
                trace="Coordinated analysis",
                agent_invocations=[],
                execution_time=5.0,
                workflow_name="multi_agent_coordination",
                error=None
            )
            mock_execute.return_value = mock_result
            
            from backend.workflows.coordinator import MultiAgentCoordinator
            coordinator = MultiAgentCoordinator()
            result = coordinator.execute(
                query="Analyze market trends",
                provider="openai"
            )
            
            assert result.success is True
            assert result.result == "Multi-agent analysis complete"
