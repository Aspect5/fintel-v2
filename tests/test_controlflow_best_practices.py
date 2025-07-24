# tests/unit/test_controlflow_best_practices.py
import pytest
import controlflow as cf
from unittest.mock import Mock, patch
from backend.agents.registry import get_agent_registry

class TestControlFlowBestPractices:
    
    @pytest.mark.unit
    def test_agent_specialization(self):
        """Test that agents are properly specialized with scoped tools"""
        registry = get_agent_registry()
        
        market_agent_info = registry.get_agent_info("MarketAnalyst")
        economic_agent_info = registry.get_agent_info("EconomicAnalyst") 
        
        # Verify tool scoping follows principle of least privilege
        assert "get_market_data" in market_agent_info["tools"]
        assert "get_company_overview" in market_agent_info["tools"]
        assert "get_economic_data_from_fred" not in market_agent_info["tools"]
        
        assert "get_economic_data_from_fred" in economic_agent_info["tools"]
        assert "get_market_data" not in economic_agent_info["tools"]
    
    @pytest.mark.integration
    @patch('backend.workflows.dependency_workflow.cf.Task')
    @patch('backend.workflows.dependency_workflow.cf.Flow')
    @patch('backend.agents.registry.get_agent_registry')
    def test_dependency_driven_workflow(self, mock_get_agent_registry, mock_flow, mock_task):
        """Test that workflows use proper task dependencies"""
        from backend.workflows.dependency_workflow import DependencyDrivenWorkflow
        
        workflow = DependencyDrivenWorkflow()
        
        workflow.execute("Test AAPL analysis", "openai")
        
        # Verify tasks were created with proper dependencies
        assert mock_task.call_count >= 3  # At least market, economic, and synthesis
        
        # Check that synthesis task has dependencies
        synthesis_call = None
        for call in mock_task.call_args_list:
            if call.kwargs.get('depends_on'):
                synthesis_call = call
                break
        
        assert synthesis_call is not None
        assert 'depends_on' in synthesis_call.kwargs
