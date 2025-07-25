# backend/tools/registry.py - Add this to the existing file
from typing import Dict, List, Any, Optional
import controlflow as cf
from pathlib import Path
from backend.tools.plugin_loader import ToolPluginLoader
from .market_data import MarketDataTool, CompanyOverviewTool
from .economic_data import EconomicDataTool
from backend.config.settings import get_settings

class ToolRegistry:
    """Central registry for all tools"""
    
    def __init__(self):
        self._tools: Dict[str, Any] = {}
        self._tool_instances: Dict[str, Any] = {}
        self._tool_descriptions: Dict[str, str] = {}
        self._plugin_loader = ToolPluginLoader()
        self._initialize_tools()
    
    def _initialize_tools(self):
        """Initialize all available tools"""
        settings = get_settings()
        
        # Instantiate and register built-in tools
        self._tool_instances['market_data'] = MarketDataTool()
        self._tool_instances['company_overview'] = CompanyOverviewTool()
        self._tool_instances['economic_data'] = EconomicDataTool()

        # Initialize built-in tools (existing code)
        @cf.tool
        def get_market_data(ticker: str) -> dict:
            """
            Get real-time market data for a stock ticker.
            
            Examples:
                get_market_data(ticker="GOOG")
                get_market_data(ticker="AAPL")
            
            Args:
                ticker (str): Stock ticker symbol like GOOG, AAPL, MSFT
            
            Returns:
                dict: Market data with price, change, volume
            """
            if not ticker or ticker.strip() == "":
                return {
                    "error": "Missing ticker parameter",
                    "hint": "Call like this: get_market_data(ticker='GOOG')"
                }
            
            ticker = ticker.upper().strip()
            if 'market_data' in self._tool_instances:
                return self._tool_instances['market_data'].execute(ticker=ticker)
            return {"error": "Market data tool not available", "ticker": ticker}

        @cf.tool
        def get_company_overview(ticker: str) -> dict:
            """Get comprehensive company overview including sector, industry, market cap, P/E ratio, and business description
            
            Args:
                ticker: The stock ticker symbol (e.g., 'GOOG', 'AAPL', 'MSFT')
            
            Returns:
                dict: Company overview data
            """
            if not ticker or ticker.strip() == "":
                return {
                    "error": "Missing required parameter 'ticker'",
                    "message": "Please provide a stock ticker symbol like 'GOOG' or 'AAPL'",
                    "example_usage": "get_company_overview(ticker='GOOG')"
                }
            
            if 'company_overview' in self._tool_instances:
                return self._tool_instances['company_overview'].execute(ticker=ticker.upper())
            return {"error": "Company overview tool not available", "ticker": ticker}

        @cf.tool
        def get_economic_data_from_fred(series_id: str, limit: int = 10) -> dict:
            """Get economic data from Federal Reserve (FRED) for indicators like GDP, unemployment rate, and interest rates
            
            Args:
                series_id: The FRED series ID (e.g., 'GDP', 'UNRATE', 'FEDFUNDS')
                limit: Number of recent data points to return (default: 10)
            
            Returns:
                dict: Economic data for the specified series
            """
            if not series_id or series_id.strip() == "":
                return {
                    "error": "Missing required parameter 'series_id'",
                    "message": "Please provide a FRED series ID like 'GDP', 'UNRATE', or 'FEDFUNDS'",
                    "example_usage": "get_economic_data_from_fred(series_id='GDP')"
                }
            
            if 'economic_data' in self._tool_instances:
                return self._tool_instances['economic_data'].execute(series_id=series_id.upper(), limit=limit)
            return {"error": "Economic data tool not available", "series_id": series_id}
        
        self._tools = {
            'get_market_data': get_market_data,
            'get_company_overview': get_company_overview,
            'get_economic_data_from_fred': get_economic_data_from_fred
        }
        
        # Load plugin-based tools
        self._plugin_loader.load_plugins()
        
        # Merge plugin tools with built-in tools
        plugin_tools = self._plugin_loader.get_all_tool_names()
        for tool_name in plugin_tools:
            if tool_name not in self._tools:
                self._tools[tool_name] = self._plugin_loader._controlflow_tools[tool_name]
                # Extract description from docstring
                tool_func = self._plugin_loader._controlflow_tools[tool_name]
                if hasattr(tool_func, '__doc__') and tool_func.__doc__:
                    self._tool_descriptions[tool_name] = tool_func.__doc__.strip().split('\n')[0]
    
    def reload_plugins(self):
        """Reload all plugins - useful for development"""
        self._plugin_loader.load_plugins()
        self._initialize_tools()

    def get_tools(self, tool_names: List[str]) -> List[Any]:
        """Get specific tools by name"""
        tools = []
        for name in tool_names:
            if name in self._tools:
                tools.append(self._tools[name])
        return tools
        
    def get_available_tools(self) -> Dict[str, Any]:
        """Get all available tools"""
        return self._tools.copy()
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """Get tool descriptions"""
        return self._tool_descriptions.copy()

_tool_registry_instance = None

def get_tool_registry():
    """Returns a singleton instance of the ToolRegistry."""
    global _tool_registry_instance
    if _tool_registry_instance is None:
        _tool_registry_instance = ToolRegistry()
    return _tool_registry_instance