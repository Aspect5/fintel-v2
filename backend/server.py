from flask import Flask, request, jsonify
from dotenv import load_dotenv
import controlflow as cf

from backend.agents import coordinator, synthesizer, SERVICE_AGENTS

# Load environment variables from .env file, which should contain OPENAI_API_KEY
load_dotenv()

app = Flask(__name__)

@app.route('/api/run-workflow', methods=['POST'])
def run_workflow():
    """
    Executes a multi-agent financial analysis workflow based on a user query.
    """
    data = request.get_json()
    if not data or 'task' not in data:
        return jsonify({"error": "No task provided"}), 400

    user_query = data['task']
    
    # Define a new flow for each request to ensure isolation
    @cf.flow
    def financial_analysis_flow():
        # --- Task 1: Planning ---
        # The coordinator agent creates a plan of which service agents to use.
        planning_task = cf.Task(
            (
                f"Based on the user's query, create a plan to answer it. "
                f"The user's query is: '{user_query}'."
                f"You must delegate the work to your team of specialist agents. "
                f"Available agents are: {', '.join(a.name for a in SERVICE_AGENTS)}. "
                f"First, identify which agents are needed. Then, for each agent, "
                f"write a clear, one-sentence task instruction. Your output should be a simple list of tasks."
            ),
            agents=[coordinator],
            result_type=list[str]
        )
        
        # --- Task 2: Delegation and Execution ---
        # The coordinator delegates the planned tasks to the service agents.
        # This uses the Moderated turn strategy, where the coordinator decides the next agent.
        analysis_tasks = cf.Task(
            (
                "Now, execute the plan you created by delegating the tasks to your team. "
                "The plan is: {plan}"
            ),
            agents=[coordinator, *SERVICE_AGENTS],
            depends_on=[planning_task],
            # The context makes the output of the planning_task available via the {plan} placeholder
            context=dict(plan=planning_task.result),
            # The turn strategy is the core of the coordinator pattern
            turn_strategy=cf.turn_strategies.Moderated(moderator=coordinator),
            result_type=list[str] # The results from the service agents
        )
        
        # --- Task 3: Synthesis ---
        # The synthesizer agent compiles the final report.
        synthesis_task = cf.Task(
            (
                "Synthesize the findings from the analysis into a final report for the user. "
                "The original query was: '{user_query}'"
                "The analysis results are: {analysis_results}"
            ),
            agents=[synthesizer],
            depends_on=[analysis_tasks],
            context=dict(
                user_query=user_query,
                analysis_results=analysis_tasks.result
            )
        )
        
        # Running the final task automatically executes its entire dependency graph
        return synthesis_task.run()

    try:
        # Execute the flow and get the final report
        final_report = financial_analysis_flow()
        return jsonify({"result": final_report})
    except Exception as e:
        # Log the error for debugging
        print(f"An error occurred during workflow execution: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Note: For production, use a proper WSGI server like Gunicorn
    app.run(port=5001, debug=True)
