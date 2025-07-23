import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add backend to path FIRST
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

# Also add the venv site-packages to path
venv_site_packages = backend_dir / "venv" / "lib" / "python3.11" / "site-packages"
if venv_site_packages.exists():
    sys.path.insert(0, str(venv_site_packages))

# Mock environment variables BEFORE any imports
os.environ["PREFECT_API_URL"] = ""
os.environ["CONTROLFLOW_ENABLE_EXPERIMENTAL_TUI"] = "false"
os.environ["CONTROLFLOW_ENABLE_PRINT_HANDLER"] = "false"
os.environ["PREFECT_LOGGING_LEVEL"] = "CRITICAL"

@pytest.fixture
def mock_controlflow():
    """Mock controlflow to avoid actual LLM calls during testing"""
    with patch('controlflow.Agent') as mock_agent:
        mock_agent_instance = Mock()
        mock_agent.return_value = mock_agent_instance
        yield mock_agent_instance

@pytest.fixture
def mock_api_keys():
    """Mock API keys for testing"""
    with patch.dict(os.environ, {
        'OPENAI_API_KEY': 'test-openai-key',
        'GEMINI_API_KEY': 'test-gemini-key',
        'ALPHA_VANTAGE_API_KEY': 'test-alpha-key'
    }):
        yield

@pytest.fixture
def sample_market_data():
    """Sample market data for testing"""
    return {
        'symbol': 'AAPL',
        'price': 150.25,
        'change': 2.50,
        'change_percent': 1.69,
        'volume': 50000000,
        'market_cap': 2500000000000
    }

@pytest.fixture
def sample_workflow_query():
    """Sample query for workflow testing"""
    return "Analyze Apple Inc (AAPL) stock performance and provide investment recommendation"

@pytest.fixture
def mock_flask_app():
    """Mock Flask app for API testing"""
    mock_app = MagicMock()
    mock_app.config = {'TESTING': True}
    
    # Mock test client
    mock_client = MagicMock()
    mock_app.test_client.return_value.__enter__ = MagicMock(return_value=mock_client)
    mock_app.test_client.return_value.__exit__ = MagicMock(return_value=None)
    
    yield mock_client
