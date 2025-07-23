# backend/agents.py

import yaml
from pathlib import Path
import inspect
import os

import controlflow as cf
from controlflow.agents import Agent

import tools
import config

def get_agents_from_config(provider: str, base_url: str = None) -> dict[str, Agent]:
    """
    Dynamically provisions and returns a suite of agents based on a YAML configuration
    file and the selected LLM provider.
    """
    if provider not in ["openai", "google", "local"]:
        raise ValueError("Unsupported provider. Must be 'openai', 'google', or 'local'.")

    config_path = Path(__file__).parent / "agents.yaml"
    with open(config_path, 'r') as f:
        agent_configs = yaml.safe_load(f)

    if provider == "openai":
        model_name = "openai/gpt-4o"
        service_model_name = "openai/gpt-4o-mini"
    elif provider == "google":
        model_name = "google/gemini-1.5-pro"
        service_model_name = "google/gemini-1.5-pro"
    else: # local provider
        if not base_url:
            raise ValueError("The 'local' provider requires a 'base_url'.")
        model_name = f"openai/{base_url}"
        service_model_name = f"openai/{base_url}"

    agent_instances = {}
    
    # (FIX) Correctly discover tools as functions instead of looking for a Tool class.
    available_tools = {name: func for name, func in inspect.getmembers(tools, inspect.isfunction)}

    for agent_config in agent_configs.get("agents", []):
        agent_tools = [
            available_tools[tool_name] 
            for tool_name in agent_config.get("tools", []) 
            if tool_name in available_tools
        ]
        
        agent = Agent(
            name=agent_config["name"],
            instructions=agent_config["instructions"],
            tools=agent_tools,
            model=service_model_name
        )
        agent_instances[agent.name] = agent
    
    financial_analyst = Agent(
        name="financial_analyst",
        instructions="You are a financial analyst. Your job is to answer the user's query by delegating to your team of specialized agents.",
        tools=list(available_tools.values()),
        model=model_name
    )
    agent_instances[financial_analyst.name] = financial_analyst

    return agent_instances