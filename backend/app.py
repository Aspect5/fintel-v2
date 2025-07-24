# backend/app.py

import os
import sys
from pathlib import Path
import json
from flask import Flask, request, jsonify, Response
import threading
import queue
import uuid
import threading
import time
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure environment before imports
os.environ["PREFECT_API_URL"] = ""
os.environ["CONTROLFLOW_ENABLE_EXPERIMENTAL_TUI"] = "false"
os.environ["CONTROLFLOW_ENABLE_PRINT_HANDLER"] = "false"
os.environ["PREFECT_LOGGING_LEVEL"] = "CRITICAL"

# Global workflow status storage
active_workflows = {}
workflow_status_queue = queue.Queue()

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
from backend.workflows.dependency_workflow import DependencyDrivenWorkflow

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
    """Get available tools with descriptions"""
    tools = tool_registry.get_available_tools()
    descriptions = tool_registry.get_tool_descriptions()
    
    tool_list = []
    for name in tools.keys():
        tool_list.append({
            "name": name,
            "description": descriptions.get(name, 'No description available')
        })
    return jsonify(tool_list)

@app.route('/api/workflows', methods=['GET'])
def get_workflows():
    """Get available workflows"""
    return jsonify(orchestrator.get_available_workflows())

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

@app.route('/api/workflow-status/<workflow_id>', methods=['GET'])
def get_workflow_status(workflow_id):
    """Get current workflow status for visualization"""
    logger.debug(f"Status request for workflow: {workflow_id}")
    if workflow_id in active_workflows:
        status = active_workflows[workflow_id]
        logger.debug(f"Returning status: {status.get('status')}, nodes: {len(status.get('nodes', []))}")
        return jsonify(status)
    else:
        logger.warning(f"Workflow not found: {workflow_id}")
        return jsonify({"error": "Workflow not found"}), 404

@app.route('/api/workflow-stream/<workflow_id>')
def workflow_stream(workflow_id):
    """Server-sent events for real-time workflow updates"""
    def generate():
        while workflow_id in active_workflows:
            try:
                status = active_workflows.get(workflow_id, {})
                yield f"data: {json.dumps(status)}"
                
                time.sleep(1)
                if status.get('status') in ['completed', 'failed']:
                    break
            except Exception as e:
                logger.error(f"Stream error: {e}")
                break
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/run-workflow', methods=['POST'])
def run_workflow():
    """Execute workflow with real-time status tracking"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        provider = data.get('provider', 'openai')
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        workflow_id = str(uuid.uuid4())
        logger.info(f"Starting workflow {workflow_id} for query: '{query}'")
        
        workflow_instance = DependencyDrivenWorkflow()
        
        def status_callback(status_update):
            with threading.Lock():
                if workflow_id in active_workflows:
                    active_workflows[workflow_id].update(status_update)

        workflow_instance.add_status_callback(status_callback)
        
        # FIX: Initialize the workflow nodes and edges SYNCHRONOUSLY
        workflow_instance._initialize_workflow_nodes(query)
        
        initial_status = workflow_instance.workflow_status.copy()
        initial_status.update({
            'workflow_id': workflow_id,
            'query': query,
            'status': 'initializing'
        })
        active_workflows[workflow_id] = initial_status
        
        def execute_workflow_target():
            try:
                status_callback({'status': 'running', 'current_task': 'Starting analysis...'})
                result = workflow_instance.execute(query=query, provider=provider)
                final_update = {
                    'result': result.result,
                    'success': result.success,
                    'execution_time': result.execution_time,
                    'status': 'completed' if result.success else 'failed',
                    'trace': result.trace,
                    'nodes': workflow_instance.workflow_status.get('nodes', []),
                    'edges': workflow_instance.workflow_status.get('edges', [])
                }
                status_callback(final_update)

            except Exception as e:
                logger.error(f"Workflow {workflow_id} execution failed: {e}", exc_info=True)
                status_callback({'status': 'failed', 'error': str(e)})
        
        thread = threading.Thread(target=execute_workflow_target)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "workflow_id": workflow_id,
            "status": "started",
            "message": f"Workflow started. Use /api/workflow-status/{workflow_id} to track progress."
        })
        
    except Exception as e:
        logger.error(f"Workflow startup failed: {e}", exc_info=True)
        return jsonify({"error": str(e), "success": False}), 500

def cleanup_old_workflows():
    """Clean up workflows older than 1 hour"""
    while True:
        try:
            current_time = datetime.now()
            workflows_to_remove = []
            
            with threading.Lock():
                for workflow_id, workflow_data in list(active_workflows.items()):
                    if workflow_data.get('status') in ['completed', 'failed']:
                        start_time_str = workflow_data.get('start_time')
                        if start_time_str:
                            start_time = datetime.fromisoformat(start_time_str)
                            if current_time - start_time > timedelta(hours=1):
                                workflows_to_remove.append(workflow_id)
            
            for workflow_id in workflows_to_remove:
                with threading.Lock():
                    if workflow_id in active_workflows:
                        del active_workflows[workflow_id]
                        logger.info(f"Cleaned up old workflow: {workflow_id}")
            
            time.sleep(300)
        except Exception as e:
            logger.error(f"Error in workflow cleanup: {e}")
            time.sleep(300)

if __name__ == '__main__':
    cleanup_thread = threading.Thread(target=cleanup_old_workflows)
    cleanup_thread.daemon = True
    cleanup_thread.start()
    
    port = int(os.getenv('BACKEND_PORT', os.getenv('PORT', 5001)))
    logger.info(f"Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False, threaded=True)