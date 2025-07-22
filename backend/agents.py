import os
import yaml
from pathlib import Path
import controlflow as cf
from controlflow.agents import Agent

# Import all available tools from the tools module
import tools

def get_agents_from_config(provider: str, base_url: str = None) -> tuple[Agent, Agent, list[Agent]]:
    """
    Dynamically provisions and returns a suite of agents based on a YAML configuration
    file and the selected LLM provider. This uses the correct `model` string API.

    Args:
        provider: The name of the LLM provider ('openai', 'gemini', or 'local').
        base_url: The base URL for a local, OpenAI-compatible model.

    Returns:
        A tuple containing: (coordinator_agent, synthesizer_agent, list_of_service_agents)
    """
    if provider not in ["openai", "gemini", "local"]:
        raise ValueError("Unsupported provider. Must be 'openai', 'gemini', or 'local'.")

    # --- Load Agent Configurations ---
    config_path = Path(__file__).parent / "agents.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # --- Configure LLM Models based on Provider ---
    # For a 'local' provider, we set environment variables that the OpenAI client,
    # used by ControlFlow, will automatically pick up.
    if provider == "local":
        if not base_url:
            raise ValueError("The 'local' provider requires a 'base_url'.")
        os.environ["OPENAI_API_BASE"] = base_url
        os.environ["OPENAI_API_KEY"] = "local"  # Dummy key for local models
        # Treat local as a flavor of openai for model naming
        effective_provider = "openai"
        # You would typically use model names your local server provides
        coordinator_model_name = "local-coordinator-model"
        service_model_name = "local-service-model"
    else:
        effective_provider = provider
        coordinator_model_name, service_model_name = \
            ("gemini-1.5-pro-latest", "gemini-1.0-pro") if provider == "gemini" \
            else ("gpt-4o", "gpt-4o-mini")

    # --- Instantiate Agents from Config ---
    service_agents = []
    agent_instances = {}
    available_tools = {name: getattr(tools, name) for name in dir(tools) if isinstance(getattr(tools, name), cf.Tool)}

    # Create service agents
    for agent_config in config.get("agents", []):
        agent_tools = [available_tools[tool_name] for tool_name in agent_config.get("tools", []) if tool_name in available_tools]
        agent = Agent(
            name=agent_config["name"],
            instructions=agent_config["instructions"],
            tools=agent_tools,
            model=f"{effective_provider}/{service_model_name}"
        )
        service_agents.append(agent)
        agent_instances[agent.name] = agent

    # Create system agents
    for agent_config in config.get("system_agents", []):
        agent = Agent(
            name=agent_config["name"],
            instructions=agent_config["instructions"],
            model=f"{effective_provider}/{coordinator_model_name}"
        )
        agent_instances[agent.name] = agent

    coordinator = agent_instances.get("Coordinator")
    synthesizer = agent_instances.get("Synthesizer")

    if not coordinator or not synthesizer:
        raise ValueError("The 'Coordinator' and 'Synthesizer' must be defined in agents.yaml.")

    return coordinator, synthesizer, service_agents
