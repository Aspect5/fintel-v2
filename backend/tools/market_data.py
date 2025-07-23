import requests
from typing import Dict, Any
from .base import BaseTool

class MarketDataTool(BaseTool):
    """Tool for fetching market data from Alpha Vantage"""
    
    def __init__(self, api_key: str):
        super().__init__("market_data", "Fetch real-time market data for stocks")
        self.api_key = api_key
    
    def execute(self, ticker: str) -> Dict[str, Any]:
        """Execute market data fetch"""
        if not self.can_execute():
            return {
                "symbol": ticker.upper(),
                "error": "Rate limit exceeded",
                "note": "Please wait before making another request"
            }
        
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": ticker,
                "apikey": self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            self.record_execution()
            
            if "Note" in data:
                return {
                    "symbol": ticker.upper(),
                    "error": "API limit reached",
                    "note": "Alpha Vantage API calls per minute exceeded"
                }
            
            if "Global Quote" in data and data["Global Quote"]:
                quote = data["Global Quote"]
                return {
                    "symbol": quote.get("01. symbol", ticker),
                    "price": quote.get("05. price", "N/A"),
                    "change": quote.get("09. change", "N/A"),
                    "change_percent": quote.get("10. change percent", "N/A"),
                    "volume": quote.get("06. volume", "N/A"),
                    "status": "success"
                }
            else:
                return {
                    "symbol": ticker.upper(),
                    "error": "No data available",
                    "note": "Invalid ticker or market closed"
                }
                
        except Exception as e:
            return {
                "symbol": ticker.upper(),
                "error": f"Request failed: {str(e)}",
                "note": "Network or API error occurred"
            }

class CompanyOverviewTool(BaseTool):
    """Tool for fetching company overview from Alpha Vantage"""
    
    def __init__(self, api_key: str):
        super().__init__("company_overview", "Fetch company fundamentals and overview")
        self.api_key = api_key
    
    def execute(self, ticker: str) -> Dict[str, Any]:
        """Execute company overview fetch"""
        if not self.can_execute():
            return {
                "symbol": ticker.upper(),
                "error": "Rate limit exceeded",
                "note": "Please wait before making another request"
            }
        
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "OVERVIEW",
                "symbol": ticker,
                "apikey": self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            self.record_execution()
            
            if "Note" in data:
                return {
                    "symbol": ticker.upper(),
                    "error": "API limit reached",
                    "note": "Alpha Vantage API calls per minute exceeded"
                }
            
            if "Symbol" in data and data["Symbol"]:
                return {
                    "symbol": data.get("Symbol", ticker),
                    "name": data.get("Name", "N/A"),
                    "sector": data.get("Sector", "N/A"),
                    "industry": data.get("Industry", "N/A"),
                    "market_cap": data.get("MarketCapitalization", "N/A"),
                    "pe_ratio": data.get("PERatio", "N/A"),
                    "dividend_yield": data.get("DividendYield", "N/A"),
                    "description": data.get("Description", "N/A")[:300] + "..." if data.get("Description") else "N/A",
                    "status": "success"
                }
            else:
                return {
                    "symbol": ticker.upper(),
                    "error": "No company data available",
                    "note": "Invalid ticker symbol or API issue"
                }
                
        except Exception as e:
            return {
                "symbol": ticker.upper(),
                "error": f"Request failed: {str(e)}",
                "note": "Network or API error occurred"
            }