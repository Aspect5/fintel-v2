import logging
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import controlflow as cf
import google.generativeai as genai

# Import project-specific modules
import config
from agents import get_agents_from_config

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Flask App Initialization ---
app = Flask(__name__)

# --- Dynamic CORS Configuration (FIX) ---
# This is a more robust way to handle CORS in a proxied cloud environment.
# Instead of a static URL, we use a function that checks the 'Origin' header
# of the incoming request and dynamically allows it.
# This adapts to the specific URL your browser is using at any given time.
@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    if origin:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response


# --- Configure the Gemini API ---
genai.configure(api_key=config.GOOGLE_API_KEY)


# --- Schemas for Gemini ---
plan_schema = {
    "type": "object",
    "properties": {
        "plan": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "agentName": {"type": "string"},
                    "task": {"type": "string"}
                },
                "required": ["agentName", "task"]
            }
        },
        "analysis": {"type": "string"}
    },
    "required": ["plan", "analysis"]
}

agent_tool_call_schema = {
    "type": "object",
    "properties": {
        "toolCalls": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "toolName": {"type": "string"},
                    "parameters": {"type": "string"}
                },
                "required": ["toolName", "parameters"]
            }
        }
    },
    "required": ["toolCalls"]
}

agent_final_response_schema = {
    "type": "object",
    "properties": {
        "finalResponse": {"type": "string"}
    },
    "required": ["finalResponse"]
}

report_synthesizer_schema = {
    "type": "object",
    "properties": {
        "executiveSummary": {"type": "string"}
    },
    "required": ["executiveSummary"]
}


purpose_to_schema_map = {
    'coordinator': plan_schema,
    'tool_planning': agent_tool_call_schema,
    'synthesis': agent_final_response_schema,
    'report': report_synthesizer_schema,
}

# --- API Endpoints ---
@app.route('/api/proxy/<path:provider>', methods=['GET'])
def proxy_request(provider):
    """
    A generic proxy endpoint to securely forward requests to external APIs.
    """
    api_key = None
    base_url = None

    if provider == 'alpha_vantage':
        api_key = config.ALPHA_VANTAGE_API_KEY
        base_url = 'https://www.alphavantage.co/query'
    elif provider == 'fred':
        api_key = config.FRED_API_KEY
        base_url = 'https://api.stlouisfed.org/fred/series/observations'
    else:
        return jsonify({"error": "Unsupported provider"}), 400

    if not api_key:
        return jsonify({"error": f"API key for {provider} is not configured on the backend."}), 500

    params = request.args.to_dict()
    params['apikey'] = api_key

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        logging.error(f"Proxy request to {provider} failed: {e}")
        try:
            error_json = e.response.json()
            return jsonify(error_json), e.response.status_code
        except:
            return jsonify({"error": "Failed to connect to the external API."}), 502

@app.route('/api/key-status', methods=['GET'])
def key_status():
    """
    Endpoint to check which backend API keys are set.
    """
    status = {
        "openai": bool(config.OPENAI_API_KEY),
        "google": bool(config.GOOGLE_API_KEY),
        "alpha_vantage": bool(config.ALPHA_VANTAGE_API_KEY),
    }
    return jsonify(status)

@app.route('/api/run-workflow', methods=['POST'])
def run_workflow():
    """Executes a financial analysis workflow."""
    logging.info("Received request for /api/run-workflow")
    data = request.get_json()

    query = data.get('query')
    if not query:
        logging.error("Request received without a query.")
        return jsonify({"error": "Query is a required field."}), 400

    provider = data.get('provider', 'openai')
    base_url = data.get('base_url')
    logging.info(f"Starting workflow for query: '{query}' with provider: {provider}")

    try:
        # --- Model Selection ---
        if provider == 'openai':
            llm = cf.OpenAI(model="gpt-4o", api_key=config.OPENAI_API_KEY)
        elif provider == 'google':
            llm = cf.Google(model="gemini-1.5-pro", api_key=config.GOOGLE_API_KEY)
        elif provider == 'local' and base_url:
            llm = cf.OpenAI(model="local-model", base_url=base_url)
        else:
            logging.error(f"Invalid or unsupported provider: {provider}")
            return jsonify({"error": f"Invalid or unsupported provider: {provider}"}), 400

        agents = get_agents_from_config(llm)
        financial_analyst = agents.get("financial_analyst")
        
        if not financial_analyst:
             logging.error("Configuration error: 'financial_analyst' agent not found.")
             return jsonify({"error": "Configuration error: 'financial_analyst' not found."}), 500

        task = cf.Task(objective=query, agent=financial_analyst)
        
        logging.info("Running ControlFlow workflow...")
        trace = cf.run(task)
        logging.info("Workflow completed.")
        
        final_result = task.result

        return jsonify({
            "result": final_result,
            "trace": trace
        })

    except Exception as e:
        logging.error(f"An error occurred during workflow execution: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred on the server."}), 500


@app.route('/api/run-agent', methods=['POST'])
def run_agent_endpoint():
    """
    This new endpoint handles the agent execution logic.
    """
    data = request.get_json()
    query = data.get('query')

    if not query:
        return jsonify({"error": "Query is required"}), 400

    try:
        result = run_agent_workflow(query)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error in agent workflow: {e}")
        return jsonify({"error": str(e)}), 500

def run_agent_workflow(query: str):
    """
    This function contains the main agent orchestration logic.
    """
    plan_result = run_coordinator_planner(query)
    agent_invocations = [run_agent_task(p) for p in plan_result['plan']]
    agent_findings = [{
        "agentName": inv['agentName'],
        "summary": inv['synthesizedResponse'],
    } for inv in agent_invocations]
    
    report = run_report_synthesizer(query, agent_findings)

    return {
        "output": report['executiveSummary'],
        "trace": {
            "fintelQueryAnalysis": plan_result['analysis'],
            "agentInvocations": agent_invocations,
        }
    }


def call_gemini_api(prompt: str, purpose: str):
    """
    A helper function to call the Gemini API with a specific purpose and schema.
    """
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        generation_config={"response_mime_type": "application/json"}
    )
    schema = purpose_to_schema_map.get(purpose)
    if not schema:
        raise ValueError(f"Invalid purpose specified: {purpose}")
    
    response = model.generate_content([prompt], generation_config=genai.types.GenerationConfig(
        response_schema=schema,
        temperature=0.1
    ))
    return response.text


def run_coordinator_planner(query: str):
    available_agents = """- Financial Analyst: Performs detailed financial data analysis.
- News Analyst: Fetches and analyzes financial news."""
    prompt = f'User Query: "{query}". Available agents:\n{available_agents}\nAnalyze the query and create a plan by selecting 2-3 agents and defining a specific task for each.'
    return call_gemini_api(prompt, 'coordinator')

def plan_tool_calls(agent_name: str, task: str):
    tool_schemas = '[{"name": "get_stock_price", "description": "Get the latest stock price for a company.", "parameters": {"symbol": "string"}}]'
    prompt = f'You are {agent_name}. Task: "{task}". Available tools:\n{tool_schemas}\nDecide which tools to call.'
    return call_gemini_api(prompt, 'tool_planning')

def synthesize_results(agent_name: str, task: str, tool_results: list):
    prompt = f'You are {agent_name}. Task: "{task}". Tool results:\n{tool_results}\nSynthesize a final answer.'
    result = call_gemini_api(prompt, 'synthesis')
    return result

def run_agent_task(plan: dict):
    tool_calls = plan_tool_calls(plan['agentName'], plan['task'])
    synthesized_response = synthesize_results(plan['agentName'], plan['task'], tool_calls['toolCalls'])
    
    return {
        "agentName": plan['agentName'],
        "naturalLanguageTask": plan['task'],
        "toolCalls": tool_calls['toolCalls'],
        "synthesizedResponse": synthesized_response['finalResponse'],
        "status": 'success'
    }

def run_report_synthesizer(query: str, agent_findings: list):
    prompt = f'Original Query: "{query}". Agent Findings:\n{agent_findings}\nSynthesize a final, user-facing report.'
    return call_gemini_api(prompt, 'report')


# --- Main Execution Block ---
if __name__ == '__main__':
    # (FIX) Bind to 0.0.0.0 to make the app accessible on your network
    app.run(host='0.0.0.0', port=5001, debug=True)