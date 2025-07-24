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
    if workflow_id in active_workflows:
        return jsonify(active_workflows[workflow_id])
    else:
        return jsonify({"error": "Workflow not found"}), 404

@app.route('/api/workflow-stream/<workflow_id>')
def workflow_stream(workflow_id):
    """Server-sent events for real-time workflow updates"""
    def generate():
        while workflow_id in active_workflows:
            try:
                # Send current status
                status = active_workflows.get(workflow_id, {})
                yield f"data: {json.dumps(status)}\n\n"
                time.sleep(1)  # Update every second
                
                # Stop if workflow is completed or failed
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
        
        # Generate unique workflow ID
        workflow_id = str(uuid.uuid4())
        
        logger.info(f"Starting workflow {workflow_id} for query: '{query}'")
        
        # Initialize workflow
        from backend.workflows.dependency_workflow import DependencyDrivenWorkflow
        workflow_instance = DependencyDrivenWorkflow()
        
        # Add status callback to update global status
        def status_callback(status):
            active_workflows[workflow_id] = {
                **status,
                'workflow_id': workflow_id,
                'query': query
            }
        
        workflow_instance.add_status_callback(status_callback)
        
        # Initialize workflow status
        active_workflows[workflow_id] = {
            'workflow_id': workflow_id,
            'query': query,
            'status': 'initializing',
            'nodes': [],
            'edges': []
        }
        
        # Execute workflow in background thread for real-time updates
        def execute_workflow():
            try:
                result = workflow_instance.execute(query=query, provider=provider)
                active_workflows[workflow_id].update({
                    'result': result.result,
                    'success': result.success,
                    'execution_time': result.execution_time,
                    'status': 'completed' if result.success else 'failed',
                    'trace': result.trace
                })
            except Exception as e:
                active_workflows[workflow_id].update({
                    'status': 'failed',
                    'error': str(e)
                })
                logger.error(f"Workflow {workflow_id} failed: {e}", exc_info=True)
        
        # Start workflow in background
        thread = threading.Thread(target=execute_workflow)
        thread.daemon = True
        thread.start()
        
        # Return workflow ID for status tracking
        return jsonify({
            "workflow_id": workflow_id,
            "status": "started",
            "message": "Workflow started. Use /api/workflow-status/{workflow_id} to track progress."
        })
        
    except Exception as e:
        logger.error(f"Workflow startup failed: {e}", exc_info=True)
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

def cleanup_old_workflows():
    """Clean up workflows older than 1 hour"""
    while True:
        try:
            current_time = datetime.now()
            workflows_to_remove = []
            
            for workflow_id, workflow_data in active_workflows.items():
                if 'start_time' in workflow_data:
                    start_time = datetime.fromisoformat(workflow_data['start_time'])
                    if current_time - start_time > timedelta(hours=1):
                        workflows_to_remove.append(workflow_id)
            
            for workflow_id in workflows_to_remove:
                del active_workflows[workflow_id]
                logger.info(f"Cleaned up old workflow: {workflow_id}")
            
            time.sleep(300)  # Check every 5 minutes
        except Exception as e:
            logger.error(f"Error in workflow cleanup: {e}")
            time.sleep(300)

# Start cleanup thread when app starts
cleanup_thread = threading.Thread(target=cleanup_old_workflows)
cleanup_thread.daemon = True
cleanup_thread.start()

if __name__ == '__main__':
    port = int(os.getenv('BACKEND_PORT', os.getenv('PORT', 5001)))
    logger.info(f"Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False, threaded=True)