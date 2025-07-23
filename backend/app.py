#!/usr/bin/env python3

import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Configure environment before imports
os.environ["PREFECT_API_URL"] = ""
os.environ["CONTROLFLOW_ENABLE_EXPERIMENTAL_TUI"] = "false"
os.environ["CONTROLFLOW_ENABLE_PRINT_HANDLER"] = "false"
os.environ["PREFECT_LOGGING_LEVEL"] = "CRITICAL"

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

# Import our modules
from config.settings import get_settings
from providers.factory import ProviderFactory
from agents.registry import get_agent_registry
from tools.registry import get_tool_registry
from workflows.orchestrator import get_orchestrator
from utils.logging import setup_logging
from utils.errors import FintelError

# Setup logging
logger = setup_logging()

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize global components
settings = get_settings()
provider_factory = ProviderFactory()
agent_registry = get_agent_registry()
tool_registry = get_tool_registry()
orchestrator = get_orchestrator()

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
    """Get the status of API keys"""
    settings = get_settings()
    return jsonify({
        'openai': bool(settings.openai_api_key),
        'google': bool(settings.google_api_key),
        'alpha_vantage': bool(settings.alpha_vantage_api_key),
        'fred': bool(settings.fred_api_key),
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

@app.route('/api/workflows', methods=['GET'])
def get_workflows():
    """Get available workflows"""
    return jsonify(orchestrator.get_available_workflows())

@app.route('/api/run-workflow', methods=['POST'])
def run_workflow():
    """Execute financial analysis workflow"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        provider = data.get('provider', 'openai')
        workflow = data.get('workflow', 'comprehensive')
        
        if not query:
            return jsonify({
                "error": "Query is required"
            }), 400
        
        logger.info(f"Processing query: '{query}' with provider: {provider}, workflow: {workflow}")
        
        # Execute workflow
        result = orchestrator.execute_workflow(
            query=query,
            provider=provider,
            workflow_name=workflow,
            timeout=45
        )
        
        # Format response
        response = {
            "result": result.result,
            "trace": result.trace,
            "success": result.success,
            "execution_time": result.execution_time
        }
        
        # Add agent invocations if available
        if result.agent_invocations:
            response["agent_invocations"] = result.agent_invocations
        
        # Add error if present
        if result.error:
            response["error"] = result.error
        
        logger.info(f"Analysis completed successfully in {result.execution_time:.2f}s")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Workflow error: {e}")
        return jsonify({
            "result": f"I encountered an error while processing your query. Please try again.",
            "trace": f"Error: {str(e)}",
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Legacy endpoint for backward compatibility"""
    return run_workflow()

# Fallback analysis function for backward compatibility
def run_fallback_analysis(query: str) -> str:
    """Fallback to direct OpenAI API"""
    try:
        import openai
        
        client = openai.OpenAI(api_key=settings.openai_api_key)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a financial analyst. Provide comprehensive financial analysis including market insights, economic context, and actionable recommendations."
                },
                {"role": "user", "content": query}
            ],
            max_tokens=2000,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"OpenAI API failed: {e}")
        raise Exception(f"OpenAI API error: {str(e)}")

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
    logger.error(f"Internal server error: {error}")
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred"
    }), 500

if __name__ == '__main__':
    port = int(os.getenv('BACKEND_PORT', os.getenv('PORT', 5001)))
    logger.info(f"Starting Flask server on port {port}")
    logger.info(f"Available providers: {list(provider_factory.get_available_providers().keys())}")
    logger.info(f"Available agents: {agent_registry.get_available_agents()}")
    
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False, threaded=True)