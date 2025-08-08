# backend/tools/market_data.py
import requests
from typing import Dict, Any
from .base import BaseTool
from .mock_data import MOCK_MARKET_DATA, MOCK_COMPANY_OVERVIEW

class MarketDataTool(BaseTool):
    """Tool for fetching market data from Alpha Vantage"""
    
    def __init__(self, api_key: str = None):
        super().__init__("market_data", "Fetch real-time market data for stocks")
        self.api_key = api_key
        self.use_mock = not bool(api_key)
    
    def execute(self, ticker: str) -> Dict[str, Any]:
        """Execute market data fetch"""
        ticker = ticker.upper()
        
        # Use mock data if no API key
        if self.use_mock:
            mock_data = MOCK_MARKET_DATA.get(ticker, MOCK_MARKET_DATA["DEFAULT"]).copy()
            mock_data["symbol"] = ticker
            mock_data["note"] = "Using mock data - no API key configured"
            mock_data["_mock"] = True
            return mock_data
        
        if not self.can_execute():
            return {
                "symbol": ticker,
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
                # API limit reached, return mock data
                mock_data = MOCK_MARKET_DATA.get(ticker, MOCK_MARKET_DATA["DEFAULT"]).copy()
                mock_data["symbol"] = ticker
                mock_data["note"] = "API limit reached - using mock data"
                mock_data["_mock"] = True
                return mock_data
            
            if "Global Quote" in data and data["Global Quote"]:
                quote = data["Global Quote"]
                return {
                    "symbol": quote.get("01. symbol", ticker),
                    "price": quote.get("05. price", "N/A"),
                    "change": quote.get("09. change", "N/A"),
                    "change_percent": quote.get("10. change percent", "N/A"),
                    "volume": quote.get("06. volume", "N/A"),
                    "status": "success",
                    "source": "alpha_vantage"
                }
            else:
                # No data available, return mock
                mock_data = MOCK_MARKET_DATA.get(ticker, MOCK_MARKET_DATA["DEFAULT"]).copy()
                mock_data["symbol"] = ticker
                mock_data["note"] = "No live data available - using mock data"
                mock_data["_mock"] = True
                return mock_data
                
        except Exception as e:
            # On any error, return mock data
            mock_data = MOCK_MARKET_DATA.get(ticker, MOCK_MARKET_DATA["DEFAULT"]).copy()
            mock_data["symbol"] = ticker
            mock_data["note"] = f"Error occurred - using mock data: {str(e)}"
            mock_data["_mock"] = True
            return mock_data

class CompanyOverviewTool(BaseTool):
    """Tool for fetching company overview from Alpha Vantage"""
    
    def __init__(self, api_key: str = None):
        super().__init__("company_overview", "Fetch company fundamentals and overview")
        self.api_key = api_key
        self.use_mock = not bool(api_key)
    
    def execute(self, ticker: str) -> Dict[str, Any]:
        """Execute company overview fetch"""
        ticker = ticker.upper()
        
        # Use mock data if no API key
        if self.use_mock:
            mock_data = MOCK_COMPANY_OVERVIEW.get(ticker, MOCK_COMPANY_OVERVIEW["DEFAULT"]).copy()
            mock_data["symbol"] = ticker
            mock_data["note"] = "Using mock data - no API key configured"
            mock_data["_mock"] = True
            return mock_data
        
        if not self.can_execute():
            return {
                "symbol": ticker,
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
                # API limit reached, return mock data
                mock_data = MOCK_COMPANY_OVERVIEW.get(ticker, MOCK_COMPANY_OVERVIEW["DEFAULT"]).copy()
                mock_data["symbol"] = ticker
                mock_data["note"] = "API limit reached - using mock data"
                mock_data["_mock"] = True
                return mock_data
            
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
                    "status": "success",
                    "source": "alpha_vantage"
                }
            else:
                # No data available, return mock
                mock_data = MOCK_COMPANY_OVERVIEW.get(ticker, MOCK_COMPANY_OVERVIEW["DEFAULT"]).copy()
                mock_data["symbol"] = ticker
                mock_data["note"] = "No live data available - using mock data"
                mock_data["_mock"] = True
                return mock_data
                
        except Exception as e:
            # On any error, return mock data
            mock_data = MOCK_COMPANY_OVERVIEW.get(ticker, MOCK_COMPANY_OVERVIEW["DEFAULT"]).copy()
            mock_data["symbol"] = ticker
            mock_data["note"] = f"Error occurred - using mock data: {str(e)}"
            mock_data["_mock"] = True
            return mock_data