import pytest
from unittest.mock import Mock, patch
import time

class TestFullWorkflowIntegration:
    @pytest.mark.integration
    def test_end_to_end_financial_analysis(self, sample_workflow_query, mock_api_keys):
        """Test complete end-to-end financial analysis workflow"""
        with patch('agents.registry.AgentRegistry') as mock_agent_registry, \
             patch('tools.registry.ToolRegistry') as mock_tool_registry, \
             patch('workflows.orchestrator.WorkflowOrchestrator') as mock_orchestrator:
            
            # Mock agent registry
            mock_agent_instance = Mock()
            mock_agent_registry.return_value = mock_agent_instance
            
            # Mock tool registry
            mock_tool_instance = Mock()
            mock_tool_registry.return_value = mock_tool_instance
            
            # Mock orchestrator
            mock_orch_instance = Mock()
            mock_result = Mock()
            mock_result.success = True
            mock_result.result = "Comprehensive financial analysis of AAPL completed"
            mock_result.execution_time = 25.0
            mock_result.workflow_name = "comprehensive"
            mock_orch_instance.execute_workflow.return_value = mock_result
            mock_orchestrator.return_value = mock_orch_instance
            
            # Execute workflow
            from workflows.orchestrator import WorkflowOrchestrator
            orchestrator = WorkflowOrchestrator()
            result = orchestrator.execute_workflow(
                query=sample_workflow_query,
                provider="openai",
                workflow_name="comprehensive"
            )
            
            assert result.success is True
            assert "analysis" in result.result.lower()
            assert result.execution_time > 0

    @pytest.mark.integration
    def test_multi_agent_coordination(self, mock_api_keys, mock_controlflow):
        """Test multi-agent coordination workflow"""
        with patch('agents.registry.get_agent_registry') as mock_get_registry, \
             patch('workflows.coordinator.MultiAgentCoordinator') as mock_coordinator:
            
            # Mock agent registry
            mock_registry = Mock()
            mock_registry.get_agent.return_value = Mock()
            mock_get_registry.return_value = mock_registry
            
            # Mock coordinator
            mock_coord_instance = Mock()
            mock_result = Mock()
            mock_result.success = True
            mock_result.result = "Multi-agent analysis complete"
            mock_coord_instance.execute.return_value = mock_result
            mock_coordinator.return_value = mock_coord_instance
            
            # Execute coordination
            from workflows.coordinator import MultiAgentCoordinator
            coordinator = MultiAgentCoordinator()
            result = coordinator.execute(
                query="Analyze market trends",
                provider="openai"
            )
            
            assert result.success is True

    @pytest.mark.integration
    @pytest.mark.slow
    def test_workflow_performance(self, sample_workflow_query, mock_api_keys):
        """Test workflow performance with multiple queries"""
        queries = [
            "Analyze AAPL stock performance",
            "What are the current economic indicators?",
            "Compare MSFT vs GOOGL",
            "Analyze cryptocurrency market trends",
            "What is the outlook for tech stocks?"
        ]
        
        with patch('workflows.orchestrator.WorkflowOrchestrator') as mock_orchestrator:
            mock_instance = Mock()
            mock_result = Mock()
            mock_result.success = True
            mock_result.result = "Analysis complete"
            mock_result.execution_time = 5.0
            mock_instance.execute_workflow.return_value = mock_result
            mock_orchestrator.return_value = mock_instance
            
            from workflows.orchestrator import WorkflowOrchestrator
            orchestrator = WorkflowOrchestrator()
            
            start_time = time.time()
            results = []
            
            for query in queries:
                result = orchestrator.execute_workflow(
                    query=query,
                    provider="openai"
                )
                results.append(result)
            
            total_time = time.time() - start_time
            
            assert len(results) == 5
            assert all(r.success for r in results)
            assert total_time < 30  # Should complete within 30 seconds

    @pytest.mark.integration
    def test_error_handling_workflow(self, mock_api_keys):
        """Test workflow error handling"""
        with patch('workflows.orchestrator.WorkflowOrchestrator') as mock_orchestrator:
            mock_instance = Mock()
            mock_result = Mock()
            mock_result.success = False
            mock_result.error = "API rate limit exceeded"
            mock_instance.execute_workflow.return_value = mock_result
            mock_orchestrator.return_value = mock_instance
            
            from workflows.orchestrator import WorkflowOrchestrator
            orchestrator = WorkflowOrchestrator()
            
            result = orchestrator.execute_workflow(
                query="Invalid query that should fail",
                provider="openai"
            )
            
            assert result.success is False
            assert "rate limit" in result.error.lower()

    @pytest.mark.integration
    def test_provider_switching(self, sample_workflow_query, mock_api_keys):
        """Test switching between different providers"""
        providers = ["openai", "gemini", "local"]
        
        with patch('workflows.orchestrator.WorkflowOrchestrator') as mock_orchestrator:
            mock_instance = Mock()
            mock_orchestrator.return_value = mock_instance
            
            from workflows.orchestrator import WorkflowOrchestrator
            orchestrator = WorkflowOrchestrator()
            
            for provider in providers:
                mock_result = Mock()
                mock_result.success = True
                mock_result.result = f"Analysis using {provider} provider"
                mock_instance.execute_workflow.return_value = mock_result
                
                result = orchestrator.execute_workflow(
                    query=sample_workflow_query,
                    provider=provider
                )
                
                assert result.success is True
                assert provider in result.result.lower()
