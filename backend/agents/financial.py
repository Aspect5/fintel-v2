# backend/agents/financial.py
from .base import BaseAgentConfig

class FinancialAnalystConfig(BaseAgentConfig):
    """Financial Analyst with comprehensive tool access"""
    
    def __init__(self):
        super().__init__(
            name="FinancialAnalyst",
            instructions="""
            You are a comprehensive financial analyst and coordinator.
            
            Your core responsibilities:
            1. Coordinate analysis between market and economic specialists
            2. Synthesize information from multiple sources
            3. Provide comprehensive financial analysis with clear recommendations
            4. Assess risks and provide confidence levels
            
            When coordinating:
            - Leverage specialized agents for their expertise
            - Focus on synthesis and high-level insights
            - Always provide actionable recommendations
            """,
            # Full tool access for coordinator role
            tools=["get_market_data", "get_company_overview", "get_economic_data_from_fred"]
        )

# backend/agents/market.py  
class MarketAnalystConfig(BaseAgentConfig):
    """Market Analyst with focused tool access"""
    
    def __init__(self):
        super().__init__(
            name="MarketAnalyst",
            instructions="""
            You are a specialized market analyst focused on stock analysis and market trends.
            
            Your expertise:
            1. Stock price analysis and technical indicators
            2. Company fundamental analysis  
            3. Market sentiment and trends
            4. Trading volume and liquidity analysis
            
            Focus on:
            - Current market data and price movements
            - Company fundamentals and valuation metrics
            - Market sentiment and momentum indicators
            """,
            # Scoped tools - only market-related tools
            tools=["get_market_data", "get_company_overview"]
        )

# backend/agents/economic.py
class EconomicAnalystConfig(BaseAgentConfig):
    """Economic Analyst with focused tool access"""
    
    def __init__(self):
        super().__init__(
            name="EconomicAnalyst", 
            instructions="""
            You are an expert economic analyst specializing in macroeconomic analysis.
            
            Your expertise:
            1. GDP growth and economic indicators
            2. Employment and unemployment trends
            3. Inflation and monetary policy
            4. Interest rates and Federal Reserve policy
            5. Economic forecasting and trend analysis
            
            Key indicators to monitor:
            - GDP, UNRATE, FEDFUNDS, CPIAUCSL, PAYEMS
            
            Always provide context for how economic conditions impact investments.
            """,
            # Scoped tools - only economic data tools
            tools=["get_economic_data_from_fred"]
        )