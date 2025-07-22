from controlflow import Agent
from backend.tools import get_market_data, get_economic_data_from_fred, get_company_overview

# --- Agent Definitions ---

# Use a more capable model for coordination and synthesis
COORDINATOR_MODEL = "openai/gpt-4o"
# Use a faster, cheaper model for specialized, routine tasks
SERVICE_MODEL = "openai/gpt-4o-mini"

# The Coordinator Agent: Responsible for planning and orchestrating the workflow.
# This agent will act as the "moderator" in the ControlFlow turn strategy.
coordinator = Agent(
    name="Coordinator",
    instructions=(
        "You are the central coordinator of a multi-agent financial analysis system. "
        "Your role is to understand the user's high-level goal and delegate specific tasks "
        "to a team of specialized agents. First, create a plan of action. Then, for each step, "
        "select the most appropriate agent to carry out the task. "
        "Do not perform the analysis yourself; your job is to manage the workflow."
    ),
    model=COORDINATOR_MODEL,
)

# The Market Analyst Agent: A specialized service agent for stock and company analysis.
market_analyst = Agent(
    name="MarketAnalyst",
    description="Specializes in analyzing financial markets, individual securities, and companies.",
    instructions="You are an expert market analyst. Your goal is to provide insights into market conditions and company performance using the tools available to you. Be concise and data-driven.",
    tools=[get_market_data, get_company_overview],
    model=SERVICE_MODEL,
)

# The Economic Forecaster Agent: A specialized service agent for macroeconomic trends.
economic_forecaster = Agent(
    name="EconomicForecaster",
    description="Specializes in macro-economic trends and forecasting using data from FRED.",
    instructions="You are an expert economic forecaster. Your primary goal is to provide a comprehensive outlook on economic conditions by analyzing historical data series. Use your tools to fetch the data and identify trends.",
    tools=[get_economic_data_from_fred],
    model=SERVICE_MODEL,
)

# The Synthesizer Agent: Responsible for compiling the final report from the findings of other agents.
synthesizer = Agent(
    name="Synthesizer",
    description="Synthesizes findings from other agents into a final, coherent report.",
    instructions=(
        "You are the final step in the analysis pipeline. Your job is to take the findings "
        "from the specialist agents and weave them into a single, comprehensive, and easy-to-read "
        "report for the user. Do not call any tools. Your sole focus is on summarizing and presenting the "
        "information you are given."
    ),
    model=COORDINATOR_MODEL, # Use the more powerful model for high-quality synthesis
)

# A list of all service agents available for the coordinator to delegate to.
# The coordinator itself is not a service agent.
SERVICE_AGENTS = [market_analyst, economic_forecaster]
