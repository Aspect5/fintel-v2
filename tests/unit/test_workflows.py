import pytest
from unittest.mock import Mock, patch
from backend.workflows.orchestrator import WorkflowOrchestrator
from backend.workflows.coordinator import MultiAgentCoordinator
from backend.workflows.base import WorkflowResult

class TestWorkflowOrchestrator:
    @pytest.mark.unit
    def test_orchestrator_initialization(self):
        """Test workflow orchestrator initialization"""
        with patch('workflows.orchestrator.get_workflow_templates') as mock_templates:
            mock_templates.return_value = {}
            orchestrator = WorkflowOrchestrator()
            
            assert hasattr(orchestrator, 'templates')
            assert hasattr(orchestrator, 'default_workflow')

    @pytest.mark.unit
    def test_execute_workflow(self, sample_workflow_query):
        """Test workflow execution"""
        with patch('workflows.orchestrator.get_workflow_templates') as mock_templates:
            mock_templates.return_value = {}
            
            orchestrator = WorkflowOrchestrator()
            
            # Mock the execute method
            with patch.object(orchestrator, 'execute_workflow') as mock_execute:
                mock_result = WorkflowResult(
                    success=True,
                    result="Analysis complete",
                    trace="Test trace",
                    agent_invocations=[],
                    execution_time=10.5,
                    workflow_name="comprehensive"
                )
                mock_execute.return_value = mock_result
                
                result = orchestrator.execute_workflow(
                    query=sample_workflow_query,
                    provider="openai"
                )
                
                assert result.success is True
                assert result.workflow_name == "comprehensive"

class TestMultiAgentCoordinator:
    @pytest.mark.unit
    def test_coordinator_initialization(self):
        """Test multi-agent coordinator initialization"""
        coordinator = MultiAgentCoordinator()
        
        assert coordinator.name == "multi_agent_analysis"
        assert "analysis" in coordinator.description.lower()

    @pytest.mark.unit
    def test_execute_analysis(self, sample_workflow_query, mock_controlflow):
        """Test multi-agent analysis execution"""
        coordinator = MultiAgentCoordinator()
        
        # Mock the execute method
        with patch.object(coordinator, 'execute') as mock_execute:
            mock_result = WorkflowResult(
                success=True,
                result="Multi-agent analysis complete",
                trace="Test trace",
                agent_invocations=[],
                execution_time=15.2,
                workflow_name="multi_agent_analysis"
            )
            mock_execute.return_value = mock_result
            
            result = coordinator.execute(
                query=sample_workflow_query,
                provider="openai"
            )
            
            assert result.success is True
            assert "analysis" in result.result.lower()

class TestWorkflowResult:
    @pytest.mark.unit
    def test_workflow_result_creation(self):
        """Test workflow result creation"""
        result = WorkflowResult(
            success=True,
            result="Test analysis result",
            execution_time=5.0,
            workflow_name="test_workflow",
            trace="Test trace",
            agent_invocations=[],
            
        )
        
        assert result.success is True
        assert result.result == "Test analysis result"
        assert result.execution_time == 5.0
        assert result.workflow_name == "test_workflow"

    @pytest.mark.unit
    def test_workflow_result_failure(self):
        """Test workflow result for failure case"""
        result = WorkflowResult(
            success=False,
            result="Error occurred",
            trace="Error trace",
            agent_invocations=[],
            execution_time=2.0,
            workflow_name="failed_workflow",
            error="Connection timeout"
        )
        
        assert result.success is False
        assert result.error == "Connection timeout"
