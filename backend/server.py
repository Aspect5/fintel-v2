from flask import Flask, request, jsonify
from dotenv import load_dotenv
import controlflow as cf

# The agent provisioning is now entirely data-driven from agents.yaml
from backend.agents import get_agents_from_config

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

@app.route('/api/run-workflow', methods=['POST'])
def run_workflow():
    """
    Executes a multi-agent financial analysis workflow based on a user query
    and dynamically selected LLM provider.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    user_query = data.get('task')
    provider = data.get('provider')
    base_url = data.get('base_url')

    if not user_query or not provider:
        return jsonify({"error": "Missing 'task' or 'provider' in request"}), 400

    try:
        # Step 1: Dynamically provision agents from the YAML config
        coordinator, synthesizer, service_agents = get_agents_from_config(provider, base_url)

        # Step 2: Define the workflow using these dynamic agents
        @cf.flow
        def financial_analysis_flow():
            planning_task = cf.Task(
                (
                    f"Based on the user's query ('{user_query}'), create a plan. "
                    f"Delegate work to your team of specialists: {', '.join(a.name for a in service_agents)}. "
                    "For each required agent, write a clear, one-sentence task instruction."
                ),
                agents=[coordinator],
                result_type=list[str]
            )
            
            analysis_tasks = cf.Task(
                "Execute the plan: {plan}",
                agents=[coordinator, *service_agents],
                depends_on=[planning_task],
                context=dict(plan=planning_task.result),
                turn_strategy=cf.turn_strategies.Moderated(moderator=coordinator),
                result_type=list[str]
            )
            
            synthesis_task = cf.Task(
                (
                    "Synthesize the findings from the analysis into a final report for the user. "
                    "The original query was: '{user_query}'.
"
                    "The analysis results are: {analysis_results}"
                ),
                agents=[synthesizer],
                depends_on=[analysis_tasks],
                context=dict(
                    user_query=user_query,
                    analysis_results=analysis_tasks.result
                )
            )
            
            return synthesis_task.run()

        # Step 3: Execute the flow and return the result
        final_report = financial_analysis_flow()
        return jsonify({"result": final_report})

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"An unexpected error occurred during workflow execution: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500

if __name__ == '__main__':
    app.run(port=5001, debug=True)
