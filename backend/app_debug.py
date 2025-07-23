# backend/app.py

import os
# Configure ControlFlow to avoid Prefect server issues
os.environ["PREFECT_API_URL"] = ""

import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import controlflow as cf
import google.generativeai as genai

# Import project-specific modules
import config
from agents import get_agents_from_config

# Set environment variables from config
os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY or ""
os.environ["GOOGLE_API_KEY"] = config.GOOGLE_API_KEY or ""

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Flask App Initialization ---
app = Flask(__name__)

# --- CORS Configuration ---
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# --- Configure the Gemini API ---
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
        # --- Agent Setup ---
        agents = get_agents_from_config(provider=provider, base_url=base_url)
        
        financial_analyst = agents.get("financial_analyst")
        if not financial_analyst:
             logging.error("Configuration error: 'financial_analyst' agent not found.")
             return jsonify({"error": "Configuration error: 'financial_analyst' not found."}), 500

        # --- Direct Execution (bypassing Prefect orchestration) ---
        logging.info("Running financial analysis...")
        try:
            # Use ControlFlow's simple run function
            cf_result = cf.run(
                objective=query,
                agents=[financial_analyst]
            )
            
            # DEBUG: Log what we got back
            logging.info(f"DEBUG: cf_result type: {type(cf_result)}")
            logging.info(f"DEBUG: cf_result: {cf_result}")
            
            # Extract the actual result - ControlFlow might return different formats
            if hasattr(cf_result, 'result'):
                final_result = cf_result.result
            elif hasattr(cf_result, 'value'):
                final_result = cf_result.value
            elif isinstance(cf_result, str):
                final_result = cf_result
            else:
                final_result = str(cf_result)
            
            trace = "Analysis completed successfully"
            logging.info(f"Analysis completed. Final result: {final_result}")
            
        except Exception as cf_error:
            logging.warning(f"ControlFlow execution failed: {cf_error}")
            logging.info("Falling back to direct OpenAI API...")
            
            # Fallback to direct OpenAI API call
            try:
                import openai
                client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
                
                # Create a comprehensive prompt based on the query
                system_prompt = """You are a financial analyst with access to market data and economic indicators. 
                Provide a comprehensive financial analysis based on the user's query. Include relevant market insights, 
                economic context, and actionable recommendations where appropriate."""
                
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": query}
                    ],
                    max_tokens=1500,
                    temperature=0.7
                )
                
                final_result = response.choices[0].message.content
                trace = "Analysis completed via direct OpenAI API (fallback mode)"
                logging.info("Fallback analysis completed.")
                
            except Exception as api_error:
                logging.error(f"Both ControlFlow and OpenAI API failed: {api_error}")
                final_result = f"I received your financial analysis request: '{query}'. However, I'm currently experiencing technical difficulties with the analysis engine. Please try again in a few moments."
                trace = f"Error: {str(api_error)}"

        # Ensure we have a valid response
        if not final_result:
            final_result = "Analysis completed but no result was returned. Please try again."
            
        response_data = {
            "result": final_result,
            "trace": trace
        }
        
        logging.info(f"Returning response: {response_data}")
        return jsonify(response_data)

    except Exception as e:
        logging.error(f"An error occurred during workflow execution: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred on the server."}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
