from flask import Flask, request, jsonify
import controlflow as cf
import logging

# Import the centralized config. This ensures all keys are loaded before use.
from backend import config 
from backend.agents import get_agents_from_config

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

@app.route('/api/run-workflow', methods=['POST'])
def run_workflow():
    logging.info("Received request for /api/run-workflow")
    data = request.get_json()
    # ... (rest of the workflow logic remains the same)
    
@app.route('/api/key-status', methods=['GET'])
def key_status():
    """Endpoint to check which backend API keys are set."""
    status = {
        "openai": bool(config.OPENAI_API_KEY),
        "google": bool(config.GOOGLE_API_KEY),
        "alpha_vantage": bool(config.ALPHA_VANTAGE_API_KEY),
        "fred": bool(config.FRED_API_KEY),
    }
    return jsonify(status)

# ... (rest of the file remains the same)
