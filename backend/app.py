#!/usr/bin/env python3

import os
import sys
import signal
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Load environment variables first
from dotenv import load_dotenv
load_dotenv(backend_dir / '.env')

# Disable ALL ControlFlow/Prefect display and logging
os.environ["PREFECT_API_URL"] = ""
os.environ["CONTROLFLOW_ENABLE_EXPERIMENTAL_TUI"] = "false"
os.environ["CONTROLFLOW_ENABLE_PRINT_HANDLER"] = "false"
os.environ["PREFECT_LOGGING_LEVEL"] = "CRITICAL"

# Set environment variables
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "")

import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import time

# Suppress all the noisy loggers
logging.getLogger("prefect").setLevel(logging.CRITICAL)
logging.getLogger("prefect.events").setLevel(logging.CRITICAL)
logging.getLogger("prefect.task_engine").setLevel(logging.CRITICAL)
logging.getLogger("langchain_google_genai").setLevel(logging.CRITICAL)
logging.getLogger("tzlocal").setLevel(logging.CRITICAL)

# Configure our app logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Global agents cache to avoid recreating them
_agents_cache = {}

def get_cached_agents(provider='openai'):
    """Get or create agents, cached to avoid repeated initialization"""
    if provider not in _agents_cache:
        try:
            import controlflow as cf
            cf.settings.enable_experimental_tui = False
            
            # Create a simple agent
            analyst = cf.Agent(
                name="FinancialAnalyst",
                instructions="""
                You are a financial analyst. Provide comprehensive analysis including:
                1. Market insights and company fundamentals
                2. Economic context and trends  
                3. Risk assessment and recommendations
                
                If you cannot access real-time data, provide analysis based on your knowledge.
                """,
                model=f"openai/gpt-4o-mini" if provider == 'openai' else f"google/gemini-1.5-flash"
            )
            
            _agents_cache[provider] = analyst
            logger.info(f"Created and cached agent for provider: {provider}")
            
        except Exception as e:
            logger.error(f"Failed to create agent for {provider}: {e}")
            _agents_cache[provider] = None
    
    return _agents_cache[provider]

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
    """Execute financial analysis workflow with timeout handling"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        provider = data.get('provider', 'openai')
        
        logger.info(f"Processing query: '{query}' with provider: {provider}")
        
        # Use threading to implement timeout
        result_container = {}
        
        def run_analysis():
            try:
                # Try ControlFlow first, then fallback
                try:
                    result = run_controlflow_analysis(query, provider)
                    result_container['result'] = result
                    result_container['trace'] = "Analysis completed via ControlFlow multi-agent system"
                except Exception as cf_error:
                    logger.warning(f"ControlFlow failed: {cf_error}")
                    result = run_fallback_analysis(query)
                    result_container['result'] = result
                    result_container['trace'] = "Analysis completed via direct OpenAI API (fallback mode)"
            except Exception as e:
                logger.error(f"Analysis failed: {e}")
                result_container['error'] = str(e)
        
        # Run analysis in a separate thread with timeout
        analysis_thread = threading.Thread(target=run_analysis)
        analysis_thread.daemon = True
        analysis_thread.start()
        
        # Wait for up to 45 seconds
        analysis_thread.join(timeout=45)
        
        if analysis_thread.is_alive():
            logger.error("Analysis timed out after 45 seconds")
            return jsonify({
                "result": f"I received your query about '{query}' but the analysis is taking longer than expected. This might be due to API rate limits or high demand. Please try again in a moment.",
                "trace": "Analysis timed out"
            })
        
        if 'error' in result_container:
            raise Exception(result_container['error'])
        
        if 'result' not in result_container:
            raise Exception("No result generated")
        
        logger.info("Analysis completed successfully")
        return jsonify({
            "result": result_container['result'],
            "trace": result_container['trace']
        })
        
    except Exception as e:
        logger.error(f"Workflow error: {e}")
        return jsonify({
            "result": f"I encountered an error while processing your query about '{query}'. Please try again.",
            "trace": f"Error: {str(e)}"
        })

def run_controlflow_analysis(query: str, provider: str) -> str:
    """Try to run ControlFlow analysis using cached agents"""
    try:
        import controlflow as cf
        
        # Get cached agent
        analyst = get_cached_agents(provider)
        if not analyst:
            raise Exception("Agent not available")
        
        # Run the analysis with minimal logging
        result = cf.run(
            objective=f"Provide a comprehensive financial analysis for: {query}",
            agents=[analyst],
            handlers=[]  # No handlers to prevent display issues
        )
        
        return str(result)
        
    except Exception as e:
        logger.error(f"ControlFlow execution failed: {e}")
        raise

def run_fallback_analysis(query: str) -> str:
    """Fallback to direct OpenAI API"""
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
            max_tokens=2000,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"OpenAI API failed: {e}")
        raise Exception(f"OpenAI API error: {str(e)}")

if __name__ == '__main__':
    port = int(os.getenv('BACKEND_PORT', os.getenv('PORT', 5001)))
    logger.info(f"Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False, threaded=True)
