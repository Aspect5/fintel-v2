import logging
import controlflow as cf
from flask import Flask, request, jsonify
from flask_cors import CORS

# Import project-specific modules
import config
from agents import get_agents_from_config

# --- Logging Configuration ---
# Set up basic logging to see requests and errors in the console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Flask App Initialization ---
app = Flask(__name__)
# Enable CORS for frontend requests
CORS(app)

# --- API Endpoints ---

@app.route('/api/proxy/<path:provider>', methods=['GET'])
def proxy_request(provider):
    """
    A generic proxy endpoint to securely forward requests to external APIs.
    """
    # Determine which API key to use based on the provider
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

    # Prepare the request to the external API
    # Forward all query parameters from the original request
    params = request.args.to_dict()
    params['apikey'] = api_key

    try:
        response = requests.get(base_url, params=params)
        # Raise an exception for bad status codes (4xx or 5xx)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        # Return a generic error to the client
        logging.error(f"Proxy request to {provider} failed: {e}")
        # Attempt to return the provider's error message if possible
        try:
            error_json = e.response.json()
            return jsonify(error_json), e.response.status_code
        except:
            return jsonify({"error": "Failed to connect to the external API."}), 502
            
@app.route('/api/key-status', methods=['GET'])
def key_status():
    """
    Endpoint to check which backend API keys are set.
    This helps the frontend determine which LLM providers are available.
    """
    status = {
        "openai": bool(config.OPENAI_API_KEY),
        "google": bool(config.GOOGLE_API_KEY),
        "alpha_vantage": bool(config.ALPHA_VANTAGE_API_KEY),
    }
    return jsonify(status)

@app.route('/api/run-workflow', methods=['POST'])
def run_workflow():
    """
    Main endpoint to execute a financial analysis workflow using ControlFlow.
    It receives a query and provider details from the frontend, runs the
    agent-based workflow, and returns the final result along with a full
    trace of the execution.
    """
    logging.info("Received request for /api/run-workflow")
    data = request.get_json()

    # --- Input Validation ---
    query = data.get('query')
    if not query:
        logging.error("Request received without a query.")
        return jsonify({"error": "Query is a required field."}), 400

    provider = data.get('provider', 'openai') # Default to OpenAI
    base_url = data.get('base_url') # For local/custom models
    logging.info(f"Starting workflow for query: '{query}' with provider: {provider}")

    try:
        # --- Model Selection ---
        # Choose the appropriate ControlFlow model based on the provider selected in the UI
        if provider == 'openai':
            llm = cf.OpenAI(model="gpt-4o", api_key=config.OPENAI_API_KEY)
        elif provider == 'google':
            llm = cf.Google(model="gemini-1.5-pro", api_key=config.GOOGLE_API_KEY)
        elif provider == 'local' and base_url:
            llm = cf.OpenAI(model="local-model", base_url=base_url)
        else:
            logging.error(f"Invalid or unsupported provider: {provider}")
            return jsonify({"error": f"Invalid or unsupported provider: {provider}"}), 400

        # --- Agent and Task Setup ---
        # Load agents (Financial Analyst, User Proxy) from the YAML configuration
        agents = get_agents_from_config(llm)
        financial_analyst = agents.get("financial_analyst")
        
        if not financial_analyst:
             logging.error("Configuration error: 'financial_analyst' agent not found.")
             return jsonify({"error": "Configuration error: 'financial_analyst' not found."}), 500

        # The main task is assigned to the financial analyst to solve the user's query
        task = cf.Task(
            objective=query,
            agent=financial_analyst
        )

        # --- Workflow Execution ---
        # cf.run() executes the flow and returns a list of all events (tasks, tool calls, messages)
        # This trace is ideal for visualizing the agent's reasoning process on the frontend
        logging.info("Running ControlFlow workflow...")
        trace = cf.run(task)
        logging.info("Workflow completed.")
        
        # The final result of the root task is considered the answer
        final_result = task.result

        # --- Response ---
        return jsonify({
            "result": final_result,
            "trace": trace  # Send the full event trace for detailed visualization
        })

    except Exception as e:
        logging.error(f"An error occurred during workflow execution: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred on the server."}), 500

# --- Main Execution Block ---
if __name__ == '__main__':
    # Note: For production, use a WSGI server like Gunicorn instead of app.run()
    # Example: gunicorn --bind 0.0.0.0:5001 app:app
    app.run(port=5001, debug=True)
