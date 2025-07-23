import pytest
import json
from unittest.mock import Mock, patch

class TestAPIEndpoints:
    @pytest.mark.api
    def test_health_check(self, mock_flask_app):
        """Test health check endpoint"""
        response = mock_flask_app.get('/health')
        assert response.status_code == 200

    @pytest.mark.api
    def test_workflow_execution_endpoint(self, mock_flask_app, sample_workflow_query):
        """Test workflow execution endpoint"""
        with patch('app.WorkflowOrchestrator') as mock_orchestrator:
            # Mock successful workflow execution
            mock_instance = Mock()
            mock_result = Mock()
            mock_result.success = True
            mock_result.result = "Analysis complete"
            mock_result.execution_time = 10.5
            mock_result.workflow_name = "comprehensive"
            mock_instance.execute_workflow.return_value = mock_result
            mock_orchestrator.return_value = mock_instance
            
            response = mock_flask_app.post('/api/workflow/execute', 
                json={
                    'query': sample_workflow_query,
                    'provider': 'openai',
                    'workflow_name': 'comprehensive'
                })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True

    @pytest.mark.api
    def test_workflow_execution_error(self, mock_flask_app):
        """Test workflow execution error handling"""
        with patch('app.WorkflowOrchestrator') as mock_orchestrator:
            # Mock failed workflow execution
            mock_instance = Mock()
            mock_result = Mock()
            mock_result.success = False
            mock_result.error = "API timeout"
            mock_instance.execute_workflow.return_value = mock_result
            mock_orchestrator.return_value = mock_instance
            
            response = mock_flask_app.post('/api/workflow/execute', 
                json={
                    'query': 'test query',
                    'provider': 'openai'
                })
            
            assert response.status_code == 200  # Still 200 but with error in response
            data = json.loads(response.data)
            assert data['success'] is False

    @pytest.mark.api
    def test_agents_list_endpoint(self, mock_flask_app):
        """Test agents list endpoint"""
        with patch('app.AgentRegistry') as mock_registry:
            mock_instance = Mock()
            mock_instance.list_agents.return_value = [
                {'name': 'FinancialAnalyst', 'description': 'Financial analysis'},
                {'name': 'MarketAnalyst', 'description': 'Market analysis'}
            ]
            mock_registry.return_value = mock_instance
            
            response = mock_flask_app.get('/api/agents')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data) == 2

    @pytest.mark.api
    def test_tools_list_endpoint(self, mock_flask_app):
        """Test tools list endpoint"""
        with patch('app.ToolRegistry') as mock_registry:
            mock_instance = Mock()
            mock_instance.list_tools.return_value = [
                {'name': 'market_data', 'description': 'Market data tool'},
                {'name': 'economic_data', 'description': 'Economic data tool'}
            ]
            mock_registry.return_value = mock_instance
            
            response = mock_flask_app.get('/api/tools')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data) == 2
