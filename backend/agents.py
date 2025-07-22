import os
import yaml
from pathlib import Path
import controlflow as cf
from controlflow.agents import Agent
from controlflow.llms.providers import OpenAI as OpenAIProvider, Google as GoogleProvider

# Import all available tools from the tools module
from backend import tools

# A mapping of our internal provider names to the ControlFlow provider classes
PROVIDER_MAP = {
    "openai": OpenAIProvider,
    "gemini": GoogleProvider,
    "local": OpenAIProvider,  # The local model uses the OpenAI client interface
}

def get_agents_from_config(provider: str, base_url: str = None) -> tuple[Agent, Agent, list[Agent]]:
    """
    Dynamically provisions and returns a suite of agents based on a YAML configuration
    file and the selected LLM provider.

    Args:
        provider: The name of the LLM provider ('openai', 'gemini', or 'local').
        base_url: The base URL for a local, OpenAI-compatible model.

    Returns:
        A tuple containing: (coordinator_agent, synthesizer_agent, list_of_service_agents)
    """
    if provider not in PROVIDER_MAP:
        raise ValueError(f"Unsupported provider '{provider}'. Must be one of {list(PROVIDER_MAP.keys())}")

    # --- Load Agent Configurations ---
    config_path = Path(__file__).parent / "agents.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # --- Configure LLM Provider ---
    coordinator_model_name, service_model_name = ("gemini-1.5-pro-latest", "gemini-1.0-pro") if provider == "gemini" else ("gpt-4o", "gpt-4o-mini")
    
    llm_provider_kwargs = {}
    if provider == "local":
        if not base_url:
            raise ValueError("The 'local' provider requires a 'base_url'.")
        llm_provider_kwargs.update(base_url=base_url, api_key="local-model")
        # In a real scenario, you might pass model names from the client
        coordinator_model_name, service_model_name = "local-coordinator", "local-service"
    
    # --- Instantiate Agents from Config ---
    service_agents = []
    agent_instances = {}

    # Get all tool functions from the tools module
    available_tools = {name: getattr(tools, name) for name in dir(tools) if isinstance(getattr(tools, name), cf.Tool)}

    # Create service agents
    for agent_config in config.get("agents", []):
        agent_tools = [available_tools[tool_name] for tool_name in agent_config.get("tools", []) if tool_name in available_tools]
        agent = Agent(
            name=agent_config["name"],
            instructions=agent_config["instructions"],
            tools=agent_tools,
            llm=PROVIDER_MAP[provider](model_name=service_model_name, **llm_provider_kwargs)
        )
        service_agents.append(agent)
        agent_instances[agent.name] = agent

    # Create system agents (Coordinator, Synthesizer)
    for agent_config in config.get("system_agents", []):
        agent = Agent(
            name=agent_config["name"],
            instructions=agent_config["instructions"],
            llm=PROVIDER_MAP[provider](model_name=coordinator_model_name, **llm_provider_kwargs)
        )
        agent_instances[agent.name] = agent

    coordinator = agent_instances.get("Coordinator")
    synthesizer = agent_instances.get("Synthesizer")

    if not coordinator or not synthesizer:
        raise ValueError("The 'Coordinator' and 'Synthesizer' must be defined in the system_agents section of agents.yaml.")

    return coordinator, synthesizer, service_agents
