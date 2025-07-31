# backend/agents.py

import controlflow as cf
import config

def get_agents_from_config(provider='openai', base_url=None):
    """
    Creates and returns a dictionary of agents based on the provided configuration.
    """
            # Import tools directly - they are Tool objects, not functions
        try:
            from tools import get_market_data, get_company_overview, get_economic_data_from_fred, process_financial_data
            print("✓ Successfully imported all tools")
            
            # These are already Tool objects, not functions
            available_tools = [get_market_data, get_company_overview, get_economic_data_from_fred, process_financial_data]
            
            print(f"✓ Available tools: {[tool.name if hasattr(tool, 'name') else str(tool) for tool in available_tools]}")
            
        except ImportError as e:
            print(f"✗ Error importing tools: {e}")
            available_tools = []

    # --- Model Configuration ---
    if provider == 'openai':
        model = f"openai/gpt-4o-mini"
    elif provider == 'google':
        model = f"google/gemini-1.5-flash"
    else:
        model = f"openai/gpt-4o-mini"  # Default fallback

    # --- Agent Definitions ---
    
    # Market Analyst Agent - gets market and company tools
    market_tools = [get_market_data, get_company_overview, process_financial_data] if available_tools else []
    
    market_analyst = cf.Agent(
        name="MarketAnalyst",
        instructions="""
        You are a market analyst specializing in stock analysis and market trends.
        Use the available tools to gather market data and provide insights on stock performance.
        
        When API limits are reached, acknowledge this and provide general analysis based on 
        your knowledge of the company and market conditions.
        """,
        tools=market_tools,
        model=model
    )

    # Economic Forecaster Agent - gets economic data tool
    economic_tools = [get_economic_data_from_fred, process_financial_data] if available_tools else []
    
    economic_forecaster = cf.Agent(
        name="EconomicForecaster",
        instructions="""
        You are an economic forecaster specializing in macroeconomic analysis.
        Use the available tools to gather economic data and provide insights on economic indicators.
        
        When API limits are reached, provide analysis based on current economic knowledge.
        """,
        tools=economic_tools,
        model=model
    )

    # Financial Analyst Agent (Main coordinator) - gets all tools
    financial_analyst = cf.Agent(
        name="FinancialAnalyst",
        instructions="""
        You are a comprehensive financial analyst and coordinator. Your role is to:
        
        1. Coordinate analysis between market and economic specialists
        2. Gather data using available tools when possible
        3. Provide comprehensive financial analysis even when API limits are reached
        4. Synthesize information from multiple sources
        
        When API limits prevent data retrieval:
        - Acknowledge the limitation
        - Provide analysis based on your knowledge
        - Focus on general market trends and company fundamentals
        - Give actionable recommendations despite data limitations
        
        Always provide value to the user even with limited real-time data.
        """,
        tools=available_tools,  # All tools
        model=model
    )

    print(f"✓ Created agents successfully")
    print(f"✓ Market analyst has {len(market_tools)} tools")
    print(f"✓ Economic forecaster has {len(economic_tools)} tools") 
    print(f"✓ Financial analyst has {len(available_tools)} tools")

    return {
        "MarketAnalyst": market_analyst,
        "EconomicForecaster": economic_forecaster,
        "FinancialAnalyst": financial_analyst
    }
