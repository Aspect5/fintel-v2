import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.workflows.orchestrator import WorkflowOrchestrator
from backend.workflows.base import WorkflowResult, BaseWorkflow
from backend.workflows.dependency_workflow import DependencyDrivenWorkflow

class TestWorkflowOrchestrator:
    @pytest.mark.unit
    @patch('backend.workflows.orchestrator.get_workflow_templates')
    def test_orchestrator_initialization(self, mock_get_templates):
        """Test workflow orchestrator initialization"""
        mock_templates = Mock()
        mock_get_templates.return_value = mock_templates
        orchestrator = WorkflowOrchestrator()
        
        assert orchestrator.templates == mock_templates
        assert isinstance(orchestrator.default_workflow, DependencyDrivenWorkflow)

    @pytest.mark.unit
    @patch('backend.workflows.orchestrator.get_workflow_templates')
    def test_execute_workflow_with_timeout(self, mock_get_templates, sample_workflow_query):
        """Test workflow execution with a timeout."""
        mock_workflow = Mock(spec=BaseWorkflow)
        
        def long_running_task(*args, **kwargs):
            import time
            time.sleep(2)
            return WorkflowResult(success=True, result="Complete", execution_time=2, workflow_name="test")

        mock_workflow.execute.side_effect = long_running_task

        mock_templates = Mock()
        mock_templates.get_workflow.return_value = mock_workflow
        mock_get_templates.return_value = mock_templates
        
        orchestrator = WorkflowOrchestrator()
        
        result = orchestrator.execute_workflow(
            query=sample_workflow_query,
            provider="openai",
            timeout=1
        )
        
        assert result.success is False
        assert result.error == "Timeout"
        mock_templates.get_workflow.assert_called_once()
        mock_workflow.execute.assert_called_once()


class TestDependencyDrivenWorkflow:
    @pytest.mark.unit
    def test_workflow_initialization(self):
        """Test dependency-driven workflow initialization"""
        workflow = DependencyDrivenWorkflow()
        
        assert workflow.name == "dependency_driven_analysis"
        assert "financial analysis" in workflow.description.lower()

    @pytest.mark.unit
    @patch('backend.workflows.dependency_workflow.cf.Task')
    @patch('backend.workflows.dependency_workflow.cf.Flow')
    @patch('backend.workflows.dependency_workflow.cf.run')
    @patch('backend.agents.registry.get_agent_registry')
    def test_execute_workflow_logic(self, mock_get_agent_registry, mock_cf_run, mock_flow, mock_task, sample_workflow_query):
        """Test the core logic of the dependency-driven workflow execution."""
        mock_agent = Mock()
        mock_agent.name = "TestAgent"
        mock_agent_registry = Mock()
        mock_agent_registry.get_agent.return_value = mock_agent
        mock_get_agent_registry.return_value = mock_agent_registry
        
        mock_run = MagicMock()
        mock_run.return_value = "Final analysis from mocked ControlFlow"
        mock_task.return_value.run = mock_run
        
        workflow = DependencyDrivenWorkflow()
        result = workflow.execute(query=sample_workflow_query, provider="openai")
        
        assert result.success is True
        assert result.result == "Final analysis from mocked ControlFlow"
        assert mock_get_agent_registry.call_count > 0
        mock_run.assert_called_once()

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
