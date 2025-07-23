#!/usr/bin/env python3

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
backend_dir = Path(__file__).parent
load_dotenv(backend_dir / '.env')

# Minimal imports for Firebase Studio
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

@app.route('/api/key-status', methods=['GET'])
def key_status():
    """Check API key status"""
    status = {
        "openai": bool(os.getenv("OPENAI_API_KEY")),
        "google": bool(os.getenv("GOOGLE_API_KEY")),
        "alpha_vantage": bool(os.getenv("ALPHA_VANTAGE_API_KEY")),
    }
    return jsonify(status)

@app.route('/api/run-workflow', methods=['POST'])
def run_workflow():
    """Simple workflow for Firebase Studio"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        provider = data.get('provider', 'openai')
        
        logger.info(f"Processing query: '{query}'")
        
        # Simple OpenAI API call for Firebase Studio
        try:
            import openai
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a financial analyst. Provide comprehensive financial analysis including market insights, economic context, and actionable recommendations."
                    },
                    {"role": "user", "content": query}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            result = response.choices[0].message.content
            return jsonify({
                "result": result,
                "trace": "Analysis completed via OpenAI API (Firebase Studio mode)"
            })
            
        except Exception as e:
            logger.error(f"OpenAI API failed: {e}")
            return jsonify({
                "result": f"I received your query about '{query}' but I'm currently experiencing technical difficulties. Please check your API configuration.",
                "trace": f"Error: {str(e)}"
            })
        
    except Exception as e:
        logger.error(f"Workflow error: {e}")
        return jsonify({
            "error": "Analysis failed. Please try again."
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check for Firebase Studio"""
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.getenv('BACKEND_PORT', 5001))
    logger.info(f"Starting simple Flask server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
