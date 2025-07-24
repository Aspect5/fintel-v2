from typing import Dict, List, Any, Optional
import controlflow as cf
from .market_data import MarketDataTool, CompanyOverviewTool
from .economic_data import EconomicDataTool
from config.settings import get_settings

class ToolRegistry:
    """Central registry for all tools"""
    
    def __init__(self):
        self._tools: Dict[str, Any] = {}
        self._tool_instances: Dict[str, Any] = {}
        self._initialize_tools()
    
    def _initialize_tools(self):
        """Initialize all available tools"""
        settings = get_settings()
        
        # Market data tools
        if settings.alpha_vantage_api_key:
            self._tool_instances['market_data'] = MarketDataTool(settings.alpha_vantage_api_key)
            self._tool_instances['company_overview'] = CompanyOverviewTool(settings.alpha_vantage_api_key)
        
        # Economic data tools
        if settings.fred_api_key:
            self._tool_instances['economic_data'] = EconomicDataTool(settings.fred_api_key)
        
        # Register ControlFlow tools
        self._register_controlflow_tools()
    
    def _register_controlflow_tools(self):
        """Register tools with ControlFlow decorators"""
        
        @cf.tool
        def get_market_data(ticker: str) -> dict:
            """Get market data for a stock ticker"""
            if 'market_data' in self._tool_instances:
                return self._tool_instances['market_data'].execute(ticker=ticker)
            return {"error": "Market data tool not available", "ticker": ticker}
        
        @cf.tool
        def get_company_overview(ticker: str) -> dict:
            """Get company overview for a stock ticker"""
            if 'company_overview' in self._tool_instances:
                return self._tool_instances['company_overview'].execute(ticker=ticker)
            return {"error": "Company overview tool not available", "ticker": ticker}
        
        @cf.tool
        def get_economic_data_from_fred(series_id: str, limit: int = 10) -> dict:
            """Get economic data from FRED"""
            if 'economic_data' in self._tool_instances:
                return self._tool_instances['economic_data'].execute(series_id=series_id, limit=limit)
            return {"error": "Economic data tool not available", "series_id": series_id}
        
        # Store tools for agent assignment
        self._tools = {
            'get_market_data': get_market_data,
            'get_company_overview': get_company_overview,
            'get_economic_data_from_fred': get_economic_data_from_fred
        }
    
    def get_tools(self, tool_names: List[str]) -> List[Any]:
        """Get specific tools by name"""
        tools = []
        for name in tool_names:
            if name in self._tools:
                tools.append(self._tools[name])
        return tools


    def get_tools_by_category(self, category: str) -> List[Any]:
        """Get tools by category"""
        categories = {
            'market': ['get_market_data', 'get_company_overview'],
            'economic': ['get_economic_data_from_fred'],
            'all': list(self._tools.keys())
        }
        
        tool_names = categories.get(category, [])
        return [self._tools[name] for name in tool_names if name in self._tools]
    
    def get_tool_status(self) -> Dict[str, Any]:
        """Get status of all tools"""
        status = {}
        for name, instance in self._tool_instances.items():
            status[name] = instance.get_status()
        return status
    
    def get_available_tools(self) -> Dict[str, Any]:
        """Get all available tools"""
        return self._tools.copy()

    def get_all_tools(self) -> Dict[str, Any]:
        """Get all available tools with their metadata"""
        return self._tools.copy()

# Global registry instance
_registry = None

def get_tool_registry() -> ToolRegistry:
    """Get global tool registry instance"""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry