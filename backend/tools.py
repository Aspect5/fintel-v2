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
        Dictionary containing market data or mock data if API unavailable
    """
    if not ALPHA_VANTAGE_API_KEY:
        # Return mock data when API key is not available
        return {
            "symbol": ticker.upper(),
            "price": "$150.25",
            "change": "+2.35 (+1.59%)",
            "volume": "1,234,567",
            "note": "Mock data - Alpha Vantage API key not configured"
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
        
        if "Global Quote" in data:
            quote = data["Global Quote"]
            return {
                "symbol": quote.get("01. symbol", ticker),
                "price": quote.get("05. price", "N/A"),
                "change": quote.get("09. change", "N/A"),
                "change_percent": quote.get("10. change percent", "N/A"),
                "volume": quote.get("06. volume", "N/A")
            }
        else:
            return {
                "symbol": ticker.upper(),
                "error": "Unable to fetch real-time data",
                "note": "API limit reached or invalid ticker"
            }
            
    except Exception as e:
        return {
            "symbol": ticker.upper(),
            "error": f"Error fetching data: {str(e)}",
            "note": "Using fallback response"
        }

@cf.tool
def get_company_overview(ticker: str) -> dict:
    """
    Retrieves company overview and fundamental data for a stock ticker.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'GOOGL')
    
    Returns:
        Dictionary containing company overview data
    """
    if not ALPHA_VANTAGE_API_KEY:
        return {
            "symbol": ticker.upper(),
            "name": f"{ticker.upper()} Corporation",
            "sector": "Technology",
            "market_cap": "$1.2T",
            "pe_ratio": "25.4",
            "note": "Mock data - Alpha Vantage API key not configured"
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
        
        if "Symbol" in data:
            return {
                "symbol": data.get("Symbol", ticker),
                "name": data.get("Name", "N/A"),
                "sector": data.get("Sector", "N/A"),
                "industry": data.get("Industry", "N/A"),
                "market_cap": data.get("MarketCapitalization", "N/A"),
                "pe_ratio": data.get("PERatio", "N/A"),
                "dividend_yield": data.get("DividendYield", "N/A"),
                "description": data.get("Description", "N/A")[:200] + "..."
            }
        else:
            return {
                "symbol": ticker.upper(),
                "error": "Company overview not available",
                "note": "API limit reached or invalid ticker"
            }
            
    except Exception as e:
        return {
            "symbol": ticker.upper(),
            "error": f"Error fetching company data: {str(e)}"
        }

@cf.tool
def get_economic_data_from_fred(series_id: str = "GDP") -> dict:
    """
    Retrieves economic data from FRED (Federal Reserve Economic Data).
    
    Args:
        series_id: FRED series ID (e.g., 'GDP', 'UNRATE', 'FEDFUNDS')
    
    Returns:
        Dictionary containing economic data
    """
    if not FRED_API_KEY:
        return {
            "series_id": series_id,
            "title": f"Economic Indicator: {series_id}",
            "latest_value": "Mock data",
            "date": "2024-01-01",
            "note": "Mock data - FRED API key not configured"
        }
    
    try:
        url = f"https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": series_id,
            "api_key": FRED_API_KEY,
            "file_type": "json",
            "limit": 1,
            "sort_order": "desc"
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if "observations" in data and data["observations"]:
            obs = data["observations"][0]
            return {
                "series_id": series_id,
                "latest_value": obs.get("value", "N/A"),
                "date": obs.get("date", "N/A"),
                "note": "Data from FRED"
            }
        else:
            return {
                "series_id": series_id,
                "error": "No data available",
                "note": "Invalid series ID or API issue"
            }
            
    except Exception as e:
        return {
            "series_id": series_id,
            "error": f"Error fetching FRED data: {str(e)}"
        }
