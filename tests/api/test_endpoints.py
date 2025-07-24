import pytest
import json
from unittest.mock import Mock, patch

class TestAPIEndpoints:
    @pytest.fixture
    def client(self):
        """Create a test client for the Flask app"""
        from backend.app import app
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    @pytest.mark.api
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
    
    @pytest.mark.api
    def test_key_status_endpoint(self, client):
        """Test API key status endpoint"""
        response = client.get('/api/status/keys?provider=openai')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'is_configured' in data
    
    @pytest.mark.api
    def test_providers_endpoint(self, client):
        """Test providers list endpoint"""
        response = client.get('/api/providers')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict)
        assert 'openai' in data
        assert 'google' in data
    
    @pytest.mark.api
    def test_agents_list_endpoint(self, client):
        """Test agents list endpoint"""
        response = client.get('/api/agents')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict)
    
    @pytest.mark.api
    def test_workflows_endpoint(self, client):
        """Test workflows list endpoint"""
        response = client.get('/api/workflows')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict)
        assert 'dependency_driven' in data
    
    @pytest.mark.api
    @patch('backend.workflows.dependency_workflow.DependencyDrivenWorkflow.execute')
    def test_run_workflow_endpoint(self, mock_execute, client, sample_workflow_query):
        """Test workflow execution endpoint"""
        from backend.workflows.base import WorkflowResult
        mock_result = WorkflowResult(
            success=True,
            result="Analysis complete",
            trace="Execution trace",
            agent_invocations=[],
            execution_time=10.5,
            workflow_name="dependency_driven",
            error=None
        )
        mock_execute.return_value = mock_result
        
        response = client.post('/api/run-workflow',
            json={
                'query': sample_workflow_query,
                'provider': 'openai',
                'workflow': 'dependency_driven'
            })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    @pytest.mark.api
    def test_run_workflow_missing_data(self, client):
        """Test workflow execution with missing data"""
        response = client.post('/api/run-workflow', json={})
        assert response.status_code == 400
