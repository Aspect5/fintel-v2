# backend/agents.py

import inspect
import controlflow as cf
import tools
import config

def get_agents_from_config(provider='openai', base_url=None):
    """
    Creates and returns a dictionary of agents based on the provided configuration.
    """
    # Only get functions defined in tools.py, not imported ones
    available_tools = {
        name: func for name, func in inspect.getmembers(tools, inspect.isfunction)
        if func.__module__ == tools.__name__
    }

    # --- Model Configuration ---
    if provider == 'openai':
        model = f"openai/gpt-4o-mini"
    elif provider == 'google':
        model = f"google/gemini-1.5-flash"
    else:
        model = f"openai/gpt-4o-mini"  # Default fallback

    # --- Agent Definitions ---
    
    # Market Analyst Agent
    market_analyst = cf.Agent(
        name="MarketAnalyst",
        instructions="""
        You are a market analyst specializing in stock analysis and market trends.
        Use the available tools to gather market data and provide insights on stock performance,
        technical indicators, and market sentiment.
        """,
        tools=[available_tools.get("get_market_data")],
        model=model
    )

    # Economic Forecaster Agent
    economic_forecaster = cf.Agent(
        name="EconomicForecaster",
        instructions="""
        You are an economic forecaster specializing in macroeconomic analysis.
        Use the available tools to gather economic data and provide insights on economic indicators,
        trends, and their potential impact on markets.
        """,
        tools=[available_tools.get("get_economic_data")],
        model=model
    )

    # Financial Analyst Agent (Main coordinator) - SIMPLIFIED
    financial_analyst = cf.Agent(
        name="financial_analyst",
        instructions="""
        You are a comprehensive financial analyst. Provide direct, actionable financial analysis.
        
        For investment questions:
        1. Analyze the company's fundamentals (if stock ticker provided)
        2. Consider market conditions and economic factors
        3. Provide a clear recommendation with reasoning
        4. Include risk assessment and key considerations
        
        Use the available tools to gather data, but provide your own analysis.
        Do NOT try to delegate to other agents - you are the primary analyst.
        Keep your response focused, practical, and actionable.
        """,
        tools=list(available_tools.values()),
        model=model
    )

    return {
        "MarketAnalyst": market_analyst,
        "EconomicForecaster": economic_forecaster,
        "financial_analyst": financial_analyst
    }
