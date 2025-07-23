# backend/tools.py

import os
import requests
import controlflow as cf
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- API Key Management ---
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
FRED_API_KEY = os.getenv("FRED_API_KEY")

# --- Tool Implementations ---

@cf.tool
def get_market_data(ticker: str) -> dict:
    """
    Retrieves the latest daily market data (price, volume, change) for a stock ticker.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'GOOGL')
    
    Returns:
        Dictionary containing market data or error message if API unavailable
    """
    if not ALPHA_VANTAGE_API_KEY:
        return {
            "symbol": ticker.upper(),
            "error": "Alpha Vantage API key not configured",
            "note": "Unable to fetch real-time market data"
        }
    
    try:
        url = f"https://www.alphavantage.co/query"
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": ticker,
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        # Check for API limit error
        if "Note" in data:
            return {
                "symbol": ticker.upper(),
                "error": "API limit reached",
                "note": "Alpha Vantage API calls per minute exceeded. Please try again later."
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
                "note": "Invalid ticker symbol or API issue"
            }
            
    except Exception as e:
        return {
            "symbol": ticker.upper(),
            "error": f"Request failed: {str(e)}",
            "note": "Network or API error occurred"
        }

@cf.tool
def get_company_overview(ticker: str) -> dict:
    """
    Retrieves company overview and fundamental data for a stock ticker.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'GOOGL')
    
    Returns:
        Dictionary containing company overview data or error message
    """
    if not ALPHA_VANTAGE_API_KEY:
        return {
            "symbol": ticker.upper(),
            "error": "Alpha Vantage API key not configured",
            "note": "Unable to fetch company overview data"
        }
    
    try:
        url = f"https://www.alphavantage.co/query"
        params = {
            "function": "OVERVIEW",
            "symbol": ticker,
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        # Check for API limit error
        if "Note" in data:
            return {
                "symbol": ticker.upper(),
                "error": "API limit reached",
                "note": "Alpha Vantage API calls per minute exceeded. Please try again later."
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

@cf.tool
def get_economic_data_from_fred(series_id: str = "GDP") -> dict:
    """
    Retrieves economic data from FRED (Federal Reserve Economic Data).
    
    Args:
        series_id: FRED series ID (e.g., 'GDP', 'UNRATE', 'FEDFUNDS')
    
    Returns:
        Dictionary containing economic data or error message
    """
    if not FRED_API_KEY:
        return {
            "series_id": series_id,
            "error": "FRED API key not configured",
            "note": "Unable to fetch economic data"
        }
    
    try:
        url = f"https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": series_id,
            "api_key": FRED_API_KEY,
            "file_type": "json",
            "limit": 5,
            "sort_order": "desc"
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if "observations" in data and data["observations"]:
            latest = data["observations"][0]
            return {
                "series_id": series_id,
                "latest_value": latest.get("value", "N/A"),
                "date": latest.get("date", "N/A"),
                "recent_data": data["observations"][:3],  # Last 3 data points
                "status": "success"
            }
        else:
            return {
                "series_id": series_id,
                "error": "No economic data available",
                "note": "Invalid series ID or API issue"
            }
            
    except Exception as e:
        return {
            "series_id": series_id,
            "error": f"Request failed: {str(e)}",
            "note": "Network or API error occurred"
        }
