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
    Powered by Alpha Vantage.

    :param ticker: The stock ticker symbol (e.g., 'AAPL').
    """
    if not ALPHA_VANTAGE_API_KEY:
        cf.log(f"ALPHA_VANTAGE_API_KEY not found. Returning mock data for {ticker}.")
        return { "ticker": ticker, "price": 150.0, "change": "+1.5" }

    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json().get('Global Quote', {})
        if not data:
            raise ValueError(f"No data for {ticker}. It may be an invalid symbol.")
        return {
            "ticker": data.get("01. symbol"),
            "price": float(data.get("05. price")),
            "change": float(data.get("09. change"))
        }
    except (requests.RequestException, ValueError) as e:
        # Let the agent handle the error
        raise e

@cf.tool
def get_economic_data_from_fred(series_id: str, limit: int = 10) -> dict:
    """
    Retrieves a time series of a specific economic data series from FRED.

    :param series_id: The FRED series ID to fetch (e.g., 'GNPCA', 'UNRATE').
    :param limit: The number of recent data points to retrieve.
    """
    if not FRED_API_KEY:
        cf.log(f"FRED_API_KEY not found. Returning mock data for {series_id}.")
        return { "series_id": series_id, "data": [
            {"date": "2024-01-01", "value": "3.5"},
            {"date": "2024-02-01", "value": "3.6"},
        ]}

    url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={FRED_API_KEY}&file_type=json&limit={limit}&sort_order=desc"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json().get('observations', [])
        if not data:
            raise ValueError(f"No data for FRED series {series_id}.")
        return {"series_id": series_id, "data": data}
    except (requests.RequestException, ValueError) as e:
        raise e

@cf.tool
def get_company_overview(ticker: str) -> dict:
    """
    Fetches fundamental company data like market cap, P/E ratio, and description.

    :param ticker: The stock ticker symbol (e.g., 'AAPL').
    """
    if not ALPHA_VANTAGE_API_KEY:
        cf.log(f"ALPHA_VANTAGE_API_KEY not found. Returning mock data for {ticker}.")
        return { "ticker": ticker, "name": "Mock Apple Inc.", "market_cap": "3T", "pe_ratio": "30" }

    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if not data or 'Symbol' not in data:
            raise ValueError(f"No overview data for {ticker}.")
        return {
            "ticker": data.get("Symbol"),
            "name": data.get("Name"),
            "description": data.get("Description"),
            "market_cap": data.get("MarketCapitalization"),
            "pe_ratio": data.get("PERatio")
        }
    except (requests.RequestException, ValueError) as e:
        raise e
