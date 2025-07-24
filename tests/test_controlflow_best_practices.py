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
        
        market_agent = registry.get_agent("MarketAnalyst", "openai")
        economic_agent = registry.get_agent("EconomicAnalyst", "openai") 
        financial_agent = registry.get_agent("FinancialAnalyst", "openai")
        
        # Verify tool scoping follows principle of least privilege
        # Market agent should only have market tools
        market_tools = registry.get_agent_info("MarketAnalyst")["tools"]
        assert "get_market_data" in market_tools
        assert "get_company_overview" in market_tools
        assert "get_economic_data_from_fred" not in market_tools
        
        # Economic agent should only have economic tools
        economic_tools = registry.get_agent_info("EconomicAnalyst")["tools"] 
        assert "get_economic_data_from_fred" in economic_tools
        assert "get_market_data" not in economic_tools
    
    @pytest.mark.integration  
    def test_dependency_driven_workflow(self):
        """Test that workflows use proper task dependencies"""
        from backend.workflows.dependency_workflow import DependencyDrivenWorkflow
        
        workflow = DependencyDrivenWorkflow()
        
        # Mock the execution to test structure
        with patch('controlflow.Task') as mock_task:
            with patch('controlflow.Flow'):
                workflow.execute("Test AAPL analysis", "openai")
                
                # Verify tasks were created with proper dependencies
                assert mock_task.call_count >= 4  # market, economic, risk, synthesis
                
                # Check that synthesis task has dependencies
                synthesis_call = None
                for call in mock_task.call_args_list:
                    if 'depends_on' in call.kwargs:
                        synthesis_call = call
                        break
                
                assert synthesis_call is not None
                assert 'depends_on' in synthesis_call.kwargs