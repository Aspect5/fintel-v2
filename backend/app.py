# backend/app.py


import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import controlflow as cf
import google.generativeai as genai
import os

# Import project-specific modules
import config
from agents import get_agents_from_config

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Flask App Initialization ---
app = Flask(__name__)

# --- CORS Configuration ---
# This allows your frontend (on a different port) to talk to this backend.
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# --- Configure the Gemini API (for separate calls if needed) ---
genai.configure(api_key=config.GOOGLE_API_KEY)


@app.route('/api/key-status', methods=['GET'])
def key_status():
    """Endpoint to check which backend API keys are set."""
    status = {
        "openai": bool(config.OPENAI_API_KEY),
        "google": bool(config.GOOGLE_API_KEY),
        "alpha_vantage": bool(config.ALPHA_VANTAGE_API_KEY),
    }
    return jsonify(status)

@app.route('/api/run-workflow', methods=['POST'])
def run_workflow():
    """Executes a financial analysis workflow using ControlFlow."""
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
        # --- (FIX) Agent and Task Setup ---
        # We pass the provider and base_url directly to your agent factory function.
        # This function is now responsible for creating and configuring all agents.
        agents = get_agents_from_config(provider=provider, base_url=base_url)
        
        financial_analyst = agents.get("financial_analyst")
        if not financial_analyst:
             logging.error("Configuration error: 'financial_analyst' agent not found.")
             return jsonify({"error": "Configuration error: 'financial_analyst' not found."}), 500

        # The main task is assigned to the financial analyst.
        task = cf.Task(
            objective=query,
            agent=financial_analyst
        )

        # --- Workflow Execution ---
        logging.info("Running ControlFlow workflow...")
        trace = task.run() # Use task.run() for a cleaner flow
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
    app.run(host='0.0.0.0', port=5001, debug=True)