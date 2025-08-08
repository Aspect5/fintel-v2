# backend/app.py
# ruff: noqa: E402

import os
import sys
from pathlib import Path
import json
from flask import Flask, request, jsonify, Response
import threading
import queue
import uuid
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
os.environ["PREFECT_EVENTS_ENABLED"] = "false"
os.environ["PREFECT_LOGGING_TO_API_ENABLED"] = "false"
os.environ["PREFECT_CLIENT_ENABLE_LIFESPAN_HOOKS"] = "false"

# Third-party and internal imports
from flask_cors import CORS
from backend.config.settings import get_settings
from backend.providers.factory import ProviderFactory
from backend.registry import get_registry_manager
from backend.utils.logging import setup_logging
from backend.utils.errors import FintelError
from backend.utils.monitoring import workflow_monitor

# Global workflow status storage
active_workflows = {}
workflow_status_queue = queue.Queue()

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

# Initialize unified registry manager
registry_manager = get_registry_manager()
validation_result = registry_manager.get_validation_status()

if not validation_result.valid:
    logger.error(f"Registry validation failed with {len(validation_result.errors)} errors:")
    for error in validation_result.errors:
        logger.error(f"  - {error}")
    
    if validation_result.warnings:
        logger.warning(f"Registry validation warnings ({len(validation_result.warnings)}):")
        for warning in validation_result.warnings:
            logger.warning(f"  - {warning}")
else:
    logger.info("Registry validation passed successfully")
    if validation_result.warnings:
        logger.warning(f"Registry validation warnings ({len(validation_result.warnings)}):")
        for warning in validation_result.warnings:
            logger.warning(f"  - {warning}")

logger.info(f"Registry manager initialized with {len(registry_manager.tool_registry._tools)} tools and {len(registry_manager.agent_registry._agent_configs)} agents")

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint with resource monitoring and registry validation"""
    # Get current resource usage
    resource_usage = workflow_monitor.check_resources()
    
    # Get registry validation status
    validation_result = registry_manager.get_validation_status()
    system_summary = registry_manager.get_system_summary()
    
    return jsonify({
        "status": "healthy" if validation_result.valid else "degraded",
        "version": "2.0.0",
        "providers": provider_factory.get_provider_status(),
        "registry": {
            "validation": {
                "valid": validation_result.valid,
                "errors": validation_result.errors,
                "warnings": validation_result.warnings
            },
            "summary": system_summary
        },
        "resources": resource_usage,
        "active_workflows": len(active_workflows),
        "workflow_metrics": {
            "total_workflows": len(workflow_monitor.get_all_metrics()),
            "successful_workflows": len([m for m in workflow_monitor.get_all_metrics().values() if m.success]),
            "failed_workflows": len([m for m in workflow_monitor.get_all_metrics().values() if not m.success])
        }
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
    """Get available agents with validation"""
    try:
        available_agents = registry_manager.agent_registry.get_available_agents()
        agent_info = {}
        
        for agent_name in available_agents:
            info = registry_manager.get_agent_info(agent_name)
            if info:
                # Add tool validation to agent info
                tool_validation = registry_manager.validate_agent_tools(agent_name)
                info['tool_validation'] = tool_validation
                agent_info[agent_name] = info
        
        return jsonify({
            "agents": available_agents,
            "agent_info": agent_info,
            "capabilities": list(registry_manager._get_all_capabilities())
        })
    except Exception as e:
        logger.error(f"Error getting agents: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/registry/health', methods=['GET'])
def get_registry_health():
    """Get comprehensive registry health check"""
    try:
        health_check = registry_manager.get_health_check()
        return jsonify(health_check)
    except Exception as e:
        logger.error(f"Error getting registry health: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/registry/status', methods=['GET'])
def get_registry_status():
    """Get detailed registry status with validation information"""
    try:
        validation_result = registry_manager.get_validation_status()
        system_summary = registry_manager.get_system_summary()
        
        return jsonify({
            "validation": {
                "valid": validation_result.valid,
                "errors": validation_result.errors,
                "warnings": validation_result.warnings,
                "details": validation_result.details
            },
            "summary": system_summary,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting registry status: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/registry/validation', methods=['GET'])
def get_registry_validation():
    """Get registry validation status"""
    try:
        validation_result = registry_manager.get_validation_status()
        return jsonify({
            "valid": validation_result.valid,
            "errors": validation_result.errors,
            "warnings": validation_result.warnings,
            "details": validation_result.details
        })
    except Exception as e:
        logger.error(f"Error getting registry validation: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/registry/summary', methods=['GET'])
def get_registry_summary():
    """Get comprehensive registry summary"""
    try:
        return jsonify(registry_manager.get_system_summary())
    except Exception as e:
        logger.error(f"Error getting registry summary: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/registry/agents/<agent_name>', methods=['GET'])
def get_agent_details(agent_name):
    """Get detailed information about a specific agent"""
    try:
        agent_info = registry_manager.get_agent_info(agent_name)
        if not agent_info:
            return jsonify({"error": f"Agent '{agent_name}' not found"}), 404
        
        # Add tool validation for this agent
        tool_validation = registry_manager.validate_agent_tools(agent_name)
        agent_info['tool_validation'] = tool_validation
        
        return jsonify(agent_info)
    except Exception as e:
        logger.error(f"Error getting agent details for {agent_name}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/registry/tools/<tool_name>', methods=['GET'])
def get_tool_details(tool_name):
    """Get detailed information about a specific tool"""
    try:
        tool_info = registry_manager.get_tool_info(tool_name)
        if not tool_info:
            return jsonify({"error": f"Tool '{tool_name}' not found"}), 404
        
        # Add agent mapping for this tool
        agents_using_tool = registry_manager.get_agents_by_tool(tool_name)
        tool_info['agents_using_tool'] = agents_using_tool
        
        return jsonify(tool_info)
    except Exception as e:
        logger.error(f"Error getting tool details for {tool_name}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/registry/capabilities', methods=['GET'])
def get_capabilities():
    """Get all available capabilities and their agent mappings"""
    try:
        capability_mapping = registry_manager.get_capability_to_agents_mapping()
        all_capabilities = list(set().union(*capability_mapping.values())) if capability_mapping else []
        
        return jsonify({
            "capabilities": all_capabilities,
            "capability_mapping": capability_mapping
        })
    except Exception as e:
        logger.error(f"Error getting capabilities: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/registry/tools', methods=['GET'])
def get_tools():
    """Return a list of available tools and their schemas"""
    try:
        # Get available tools from the registry manager
        tool_to_agents = registry_manager.get_tool_to_agents_mapping()
        available_tools = registry_manager.tool_registry.get_all_tool_info()
        
        # Convert to a list format for the frontend
        tools_list = []
        for tool_name, tool_info in available_tools.items():
            if tool_info:  # Only include valid tools
                tool_data = {
                    "name": tool_name,
                    "summary": tool_info.get('description', "No description available"),
                    "details": {
                        "args": {},
                        "returns": "Unknown",
                        "examples": tool_info.get('examples', [])
                    },
                    "type": "function",
                    "capable_agents": tool_to_agents.get(tool_name, []),
                    "category": tool_info.get('category', 'unknown'),
                    "enabled": tool_info.get('enabled', True),
                    "api_key_required": tool_info.get('api_key_required'),
                    "validation_status": "available" if tool_info.get('enabled', True) else "disabled"
                }
                tools_list.append(tool_data)
        
        return jsonify(tools_list)
    except Exception as e:
        logger.error(f"Failed to load tools: {e}", exc_info=True)
        return jsonify({"error": "Failed to load tools"}), 500


@app.route('/api/suggest-workflow', methods=['POST'])
def suggest_workflow():
    """Suggest the most appropriate workflow based on the user's query using a lightweight LLM classification."""
    try:
        data = request.get_json() or {}
        query = data.get('query')
        if not query:
            return jsonify({"error": "Query is required"}), 400

        from backend.workflows.config_loader import get_workflow_config_loader
        import controlflow as cf

        config_loader = get_workflow_config_loader()
        workflows = config_loader.config.get('workflows', {})
        if not workflows:
            return jsonify({"error": "No workflows available"}), 500

        workflow_descriptions = "".join([
            f"- {name}: {cfg.get('description', cfg.get('name', name))}" for name, cfg in workflows.items()
        ])

        prompt = f"""Based on the following user query, which of these workflows is the most appropriate?

User Query: "{query}"

Available Workflows:
{workflow_descriptions}

Respond with ONLY the name of the best workflow (e.g., 'quick_stock_analysis')."""

        try:
            result = cf.run(prompt, result_type=str, max_agent_turns=1)
            # Normalize the response and strip any surrounding quotes
            recommended_workflow = (result or "").strip().strip("'").strip('"')
        except Exception as e:
            logger.warning(f"LLM classification failed, using default. Error: {e}")
            recommended_workflow = None

        if recommended_workflow in workflows:
            suggested_name = workflows[recommended_workflow].get('name', recommended_workflow)
            return jsonify({
                "recommended_workflow": recommended_workflow,
                "suggestion_text": f"It looks like you're asking for a '{suggested_name}'. Shall I proceed with this analysis?"
            })
        else:
            default_wf = config_loader.config.get('settings', {}).get('default_workflow', 'quick_stock_analysis')
            default_name = workflows.get(default_wf, {}).get('name', 'Quick Stock Analysis')
            return jsonify({
                "recommended_workflow": default_wf,
                "suggestion_text": f"I can run a '{default_name}' for you. Shall I proceed?"
            })
    except Exception as e:
        logger.error(f"suggest_workflow error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/workflows', methods=['GET'])
def get_workflows():
    """Get available workflows from configuration"""
    try:
        from backend.workflows.factory import get_workflow_factory
        workflow_factory = get_workflow_factory()
        workflows = workflow_factory.get_available_workflows()
        
        return jsonify(workflows)
        
    except Exception as e:
        logger.error(f"Error getting workflows: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/workflow-metrics', methods=['GET'])
def get_workflow_metrics():
    """Get workflow execution metrics"""
    all_metrics = workflow_monitor.get_all_metrics()
    
    # Calculate summary statistics
    total_workflows = len(all_metrics)
    successful_workflows = len([m for m in all_metrics.values() if m.success])
    failed_workflows = total_workflows - successful_workflows
    
    avg_duration = 0
    avg_memory = 0
    avg_cpu = 0
    
    if total_workflows > 0:
        completed_workflows = [m for m in all_metrics.values() if m.end_time]
        if completed_workflows:
            avg_duration = sum(m.duration for m in completed_workflows) / len(completed_workflows)
            avg_memory = sum(m.memory_usage_mb for m in completed_workflows) / len(completed_workflows)
            avg_cpu = sum(m.cpu_usage_percent for m in completed_workflows) / len(completed_workflows)
    
    return jsonify({
        "summary": {
            "total_workflows": total_workflows,
            "successful_workflows": successful_workflows,
            "failed_workflows": failed_workflows,
            "success_rate": (successful_workflows / total_workflows * 100) if total_workflows > 0 else 0,
            "average_duration_seconds": round(avg_duration, 2),
            "average_memory_mb": round(avg_memory, 1),
            "average_cpu_percent": round(avg_cpu, 1)
        },
        "recent_workflows": [
            {
                "workflow_id": workflow_id,
                "duration": metrics.duration,
                "memory_usage_mb": metrics.memory_usage_mb,
                "cpu_usage_percent": metrics.cpu_usage_percent,
                "success": metrics.success,
                "error": metrics.error
            }
            for workflow_id, metrics in sorted(
                all_metrics.items(), 
                key=lambda x: x[1].start_time, 
                reverse=True
            )[:10]  # Last 10 workflows
        ]
    })

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
    """Get current workflow status for visualization with metrics"""
    logger.debug(f"Status request for workflow: {workflow_id}")
    if workflow_id in active_workflows:
        status = active_workflows[workflow_id].copy()
        
        # Ensure completed workflows have results
        if status.get('status') == 'completed' and not status.get('result'):
            logger.warning(f"Completed workflow {workflow_id} missing results")
        
        # Add metrics if available
        metrics = workflow_monitor.get_workflow_metrics(workflow_id)
        if metrics:
            status['metrics'] = {
                'duration': metrics.duration,
                'memory_usage_mb': metrics.memory_usage_mb,
                'cpu_usage_percent': metrics.cpu_usage_percent,
                'execution_time': metrics.execution_time
            }
        
        logger.info(f"Returning status for {workflow_id}: status={status.get('status')}, hasResult={bool(status.get('result'))}, hasEnhancedResult={bool(status.get('enhanced_result'))}")
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
    """Execute config-driven workflow with real-time status tracking and strict validation"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        provider = data.get('provider', 'openai')
        workflow_type = data.get('workflow_type', 'quick_stock_analysis')
        ticker_override = data.get('ticker_override')
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        # Import workflow factory and exception class here to avoid circular imports
        from backend.workflows.factory import get_workflow_factory, WorkflowValidationError
        
        # Strict validation before execution
        workflow_factory = get_workflow_factory()
        validation_result = workflow_factory.validate_workflow_execution(workflow_type, provider, query)
        
        if not validation_result.get('valid', False):
            error_msg = validation_result.get('error', 'Workflow validation failed')
            logger.error(f"Workflow validation failed: {error_msg}")
            return jsonify({
                "error": f"Cannot execute workflow: {error_msg}",
                "validation_details": validation_result
            }), 400
        
        # Log warnings but allow execution to proceed
        if validation_result.get('warnings'):
            for warning in validation_result['warnings']:
                logger.warning(f"Workflow validation warning: {warning}")
        
        workflow_id = str(uuid.uuid4())
        logger.info(f"Starting config-driven workflow {workflow_id}: {workflow_type} for query: '{query}'")
        
        # Start monitoring
        workflow_monitor.start_workflow(workflow_id)
        
        # Create workflow instance using config-driven factory
        try:
            workflow_instance = workflow_factory.create_workflow(workflow_type)
        except WorkflowValidationError as e:
            logger.error(f"Failed to create workflow: {e}")
            return jsonify({
                "error": f"Cannot create workflow: {str(e)}",
                "workflow_type": workflow_type
            }), 400
        
        # Set up status callback
        def status_callback(status_update):
            with threading.Lock():
                # Add detailed logging
                logger.info(f"Status callback received: {status_update}")
                
                # Ensure workflow_id is always present
                status_update['workflow_id'] = workflow_id
                
                # Add event history from the event handler if available
                if hasattr(workflow_instance, 'event_handler') and workflow_instance.event_handler:
                    try:
                        status_update['event_history'] = workflow_instance.event_handler.get_events()
                    except AttributeError:
                        # Event handler doesn't have the method yet, skip it
                        status_update['event_history'] = []
                
                # Initialize or update the active workflow
                if workflow_id not in active_workflows:
                    active_workflows[workflow_id] = {}
                
                # Update while preserving nodes/edges if not in update
                current = active_workflows[workflow_id]
                if 'nodes' not in status_update and 'nodes' in current:
                    status_update['nodes'] = current['nodes']
                if 'edges' not in status_update and 'edges' in current:
                    status_update['edges'] = current['edges']
                    
                active_workflows[workflow_id].update(status_update)
                logger.info(f"Updated workflow {workflow_id}: status={status_update.get('status')}, hasResult={bool(status_update.get('result'))}, hasEnhancedResult={bool(status_update.get('enhanced_result'))}, eventCount={len(status_update.get('event_history', []))}")
        
        workflow_instance.add_status_callback(status_callback)
        
        # Get initial status and store it
        initial_status = workflow_instance.workflow_status.copy()
        initial_status.update({
            'workflow_id': workflow_id,
            'query': query,
            'status': 'initializing'
        })
        
        # Store initial status in active_workflows
        active_workflows[workflow_id] = initial_status
        logger.info(f"Stored initial workflow state for config-driven workflow: {workflow_type}")
        
        # Execute workflow in background thread
        def execute_workflow_target():
            try:
                # Update status to running
                status_callback({'status': 'running', 'current_task': 'Starting analysis...'})
                
                # Execute with workflow_id passed
                result = workflow_instance.execute(query=query, provider=provider, workflow_id=workflow_id, ticker_override=ticker_override)
                
                # Final update with complete results
                final_update = {
                    'result': result.result,  # This should now be the enhanced result object
                    'enhanced_result': result.result,  # Also include as enhanced_result for compatibility
                    'success': result.success,
                    'execution_time': result.execution_time,
                    'status': 'completed' if result.success else 'failed',
                    'trace': result.trace,
                    'agent_invocations': result.agent_invocations,
                    'hasResult': True,
                    'hasEnhancedResult': True  # Explicitly mark enhanced result as available
                }
                status_callback(final_update)
                logger.info(f"Config-driven workflow {workflow_id} ({workflow_type}) completed successfully")
                
                # End monitoring with success
                workflow_monitor.end_workflow(workflow_id, success=True)
                
            except Exception as e:
                logger.error(f"Config-driven workflow {workflow_id} ({workflow_type}) execution failed: {e}", exc_info=True)
                
                # Provide more detailed error information
                error_details = f"Analysis failed: {str(e)}"
                if "RiskAssessment agent is not available" in str(e):
                    error_details += "\n\nNote: The system has been updated to handle agent failures gracefully. Please try the analysis again - the coordinator will now adapt to unavailable agents."
                
                status_callback({
                    'status': 'failed', 
                    'error': error_details
                })
                
                # End monitoring with failure
                workflow_monitor.end_workflow(workflow_id, success=False, error=error_details)
        
        thread = threading.Thread(target=execute_workflow_target)
        thread.daemon = True
        thread.start()
        
        # Return immediate response with initial status
        return jsonify({
            "workflow_id": workflow_id,
            "status": "started",
            "message": f"Workflow started. Use /api/workflow-status/{workflow_id} to track progress.",
            "workflow_status": initial_status
        })
        
    except Exception as e:
        logger.error(f"Workflow startup failed: {e}", exc_info=True)
        return jsonify({"error": str(e), "success": False}), 500

@app.route('/api/create-agent', methods=['POST'])
def create_agent():
    """Create a new agent from a template"""
    from backend.agents.templates import AgentTemplateRegistry
    
    data = request.get_json()
    template_name = data.get('template')
    agent_name = data.get('name')
    parameters = data.get('parameters', {})
    additional_tools = data.get('additional_tools', [])
    additional_instructions = data.get('additional_instructions', '')
    
    try:
        registry = AgentTemplateRegistry()
        agent = registry.create_agent_from_template(
            template_name,
            name=agent_name,
            additional_instructions=additional_instructions,
            additional_tools=additional_tools,
            **parameters
        )
        
        # Save to the main agent registry via registry manager
        registry_manager = get_registry_manager()
        registry_manager.agent_registry._agents[agent_name] = agent
        
        return jsonify({
            "success": True,
            "agent_name": agent_name,
            "message": f"Agent '{agent_name}' created successfully"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

@app.route('/api/available-tools', methods=['GET'])
def get_available_tools():
    """Get all available tools including plugins"""
    registry_manager = get_registry_manager()
    tools = registry_manager.tool_registry.get_available_tools()
    descriptions = registry_manager.tool_registry.get_tool_descriptions()
    
    # Group tools by category
    categorized_tools = {
        "market_data": [],
        "economic_data": [],
        "analysis": [],
        "custom": []
    }
    
    for tool_name , tool in tools.items():
        tool_info = {
            "name": tool_name,
            "description": descriptions.get(tool_name, "No description available")
        }
        
        if "market" in tool_name or "company" in tool_name:
            categorized_tools["market_data"].append(tool_info)
        elif "economic" in tool_name:
            categorized_tools["economic_data"].append(tool_info)
        elif "analyze" in tool_name or "calculate" in tool_name:
            categorized_tools["analysis"].append(tool_info)
        else:
            categorized_tools["custom"].append(tool_info)
    
    return jsonify(categorized_tools)

@app.route('/api/workflow-configs', methods=['GET'])
def get_workflow_configs():
    """Get workflow configurations for frontend"""
    try:
        from backend.workflows.config_loader import get_workflow_config_loader
        
        config_loader = get_workflow_config_loader()
        workflows = []
        
        # Get all workflow configurations
        for workflow_name in ['quick_stock_analysis', 'competitor_deep_dive', 'macroeconomic_outlook']:
            workflow_config = config_loader.get_workflow_config(workflow_name)
            if workflow_config:
                # Get available agents for this workflow
                available_agents = config_loader.get_available_agents_for_workflow(workflow_name, "openai")
                
                # Format agent configurations
                agents = []
                for agent_config in workflow_config.get('agents', []):
                    role = agent_config.get('role')
                    agent_info = available_agents.get(role, {})
                    
                    agents.append({
                        'name': agent_config.get('name'),
                        'role': role,
                        'required': agent_config.get('required', False),
                        'fallback': agent_config.get('fallback'),
                        'tools': agent_config.get('tools', []),
                        'available': bool(agent_info.get('agent')),
                        'primary': agent_info.get('primary', False)
                    })
                
                workflows.append({
                    'key': workflow_name,
                    'name': workflow_config.get('name', workflow_name),
                    'description': workflow_config.get('description', ''),
                    'agents': agents
                })
        
        return jsonify({
            'workflows': workflows,
            'total_workflows': len(workflows)
        })
        
    except Exception as e:
        logger.error(f"Error getting workflow configs: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/save-report', methods=['POST'])
def save_report():
    """Save a report to the reports/ directory"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        content = data.get('content')
        # Ignore optional fields if unused
        _ = data.get('query')
        _ = data.get('timestamp')
        
        if not all([filename, content]):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Create reports directory if it doesn't exist
        reports_dir = Path(project_root) / 'reports'
        reports_dir.mkdir(exist_ok=True)
        
        # Save the report
        report_path = reports_dir / filename
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Report saved: {report_path}")
        
        return jsonify({
            "success": True,
            "message": f"Report saved as {filename}",
            "path": str(report_path)
        })
        
    except Exception as e:
        logger.error(f"Failed to save report: {e}")
        return jsonify({"error": str(e)}), 500

def cleanup_old_workflows():
    """Clean up workflows older than 24 hours (increased from 1 hour)"""
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
                            if current_time - start_time > timedelta(hours=24):  # Changed from 1 to 24
                                workflows_to_remove.append(workflow_id)
            
            for workflow_id in workflows_to_remove:
                with threading.Lock():
                    if workflow_id in active_workflows:
                        del active_workflows[workflow_id]
                        logger.info(f"Cleaned up old workflow: {workflow_id}")
            
            time.sleep(3600)  # Check every hour instead of every 5 minutes
        except Exception as e:
            logger.error(f"Error in workflow cleanup: {e}")
            time.sleep(3600)

if __name__ == '__main__':
    cleanup_thread = threading.Thread(target=cleanup_old_workflows)
    cleanup_thread.daemon = True
    cleanup_thread.start()
    
    port = int(os.getenv('BACKEND_PORT', os.getenv('PORT', 5001)))
    logger.info(f"Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False, threaded=True)
