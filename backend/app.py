#!/usr/bin/env python3

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure environment before imports
os.environ["PREFECT_API_URL"] = ""
os.environ["CONTROLFLOW_ENABLE_EXPERIMENTAL_TUI"] = "false"
os.environ["CONTROLFLOW_ENABLE_PRINT_HANDLER"] = "false"
os.environ["PREFECT_LOGGING_LEVEL"] = "CRITICAL"

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import time

# Import our modules
from backend.config.settings import get_settings
from backend.providers.factory import ProviderFactory
from backend.agents.registry import get_agent_registry
from backend.tools.registry import get_tool_registry
from backend.workflows.orchestrator import get_orchestrator
from backend.utils.logging import setup_logging
from backend.utils.errors import FintelError

# Setup logging
logger = setup_logging()

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize global components
logger.info("Initializing global components...")
settings = get_settings()
logger.info("Settings loaded")

provider_factory = ProviderFactory()
logger.info("Provider factory initialized")

agent_registry = get_agent_registry()
logger.info(f"Agent registry initialized with agents: {agent_registry.get_available_agents()}")

tool_registry = get_tool_registry()
logger.info(f"Tool registry initialized: {type(tool_registry)}")

orchestrator = get_orchestrator()
logger.info("Orchestrator initialized")

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "version": "2.0.0",
        "providers": provider_factory.get_provider_status(),
        "agents": agent_registry.get_available_agents(),
        "tools": tool_registry.get_tool_status()
    })

@app.route('/api/status/keys', methods=['GET'])
def get_key_status():
    """Get individual API key status"""
    settings = get_settings()
    return jsonify({
        'openai': bool(settings.openai_api_key),
        'google': bool(settings.google_api_key),
        'alpha_vantage': bool(settings.alpha_vantage_api_key),
        'fred': bool(settings.fred_api_key)
    })

@app.route('/api/providers', methods=['GET'])
def get_providers():
    """Get available providers and their status"""
    return jsonify(provider_factory.get_provider_status())

@app.route('/api/agents', methods=['GET'])
def get_agents():
    """Get available agents"""
    agents = {}
    for agent_name in agent_registry.get_available_agents():
        agents[agent_name] = agent_registry.get_agent_info(agent_name)
    return jsonify(agents)

@app.route('/api/tools', methods=['GET'])
def get_tools():
    """Get available tools"""
    tools = tool_registry.get_available_tools()
    tool_list = []
    for name, tool in tools.items():
        tool_list.append({
            "name": name,
            "description": tool.__doc__ or 'No description available'
        })
    return jsonify(tool_list)

@app.route('/api/workflows', methods=['GET'])
def get_workflows():
    """Get available workflows"""
    return jsonify(orchestrator.get_available_workflows())

@app.route('/api/run-workflow', methods=['POST'])
def run_workflow_endpoint():
    """Execute financial analysis workflow"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        provider = data.get('provider', 'openai')
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        logger.info(f"Processing query: '{query}' with provider: {provider}")
        
        from backend.workflows.dependency_workflow import DependencyDrivenWorkflow
        workflow_instance = DependencyDrivenWorkflow()
        
        result = workflow_instance.execute(
            query=query,
            provider=provider,
            max_execution_time=240  # 4 minutes max
        )
        
        response_data = {
            "result": result.result,
            "trace": result.trace,
            "success": result.success,
            "execution_time": result.execution_time
        }
        
        if result.agent_invocations:
            response_data["agent_invocations"] = result.agent_invocations
        
        if result.error:
            response_data["error"] = result.error
        
        logger.info(f"Analysis completed in {result.execution_time:.2f}s")
        return jsonify(response_data)
        
    except TimeoutError:
        logger.error("Request timed out after 4 minutes")
        return jsonify({
            "result": "Analysis timed out. Please try a simpler query or try again later.",
            "trace": "Request exceeded maximum execution time",
            "success": False,
            "error": "Request timeout"
        }), 503
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}", exc_info=True)
        return jsonify({
            "result": "An internal error occurred during workflow execution.",
            "trace": f"Error: {str(e)}",
            "success": False,
            "error": str(e)
        }), 500

@app.errorhandler(FintelError)
def handle_fintel_error(error):
    """Handle custom Fintel errors"""
    return jsonify({
        "error": str(error),
        "type": error.__class__.__name__
    }), 400

@app.errorhandler(500)
def handle_internal_error(error):
    """Handle internal server errors"""
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred"
    }), 500

if __name__ == '__main__':
    port = int(os.getenv('BACKEND_PORT', os.getenv('PORT', 5001)))
    logger.info(f"Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False, threaded=True)