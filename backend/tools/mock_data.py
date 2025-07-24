# backend/tools/mock_data.py
"""Mock data for financial tools when APIs are unavailable"""

MOCK_MARKET_DATA = {
    "GOOG": {
        "symbol": "GOOG",
        "price": "150.25",
        "change": "2.50",
        "change_percent": "1.69%",
        "volume": "1234567",
        "status": "success",
        "_mock": True
    },
    "AAPL": {
        "symbol": "AAPL",
        "price": "185.50",
        "change": "-1.25",
        "change_percent": "-0.67%",
        "volume": "2345678",
        "status": "success",
        "_mock": True
    },
    "MSFT": {
        "symbol": "MSFT",
        "price": "380.75",
        "change": "5.00",
        "change_percent": "1.33%",
        "volume": "3456789",
        "status": "success",
        "_mock": True
    },
    "DEFAULT": {
        "symbol": "UNKNOWN",
        "price": "100.00",
        "change": "0.00",
        "change_percent": "0.00%",
        "volume": "1000000",
        "status": "success",
        "_mock": True
    }
}

MOCK_COMPANY_OVERVIEW = {
    "GOOG": {
        "symbol": "GOOG",
        "name": "Alphabet Inc.",
        "sector": "Technology",
        "industry": "Internet Content & Information",
        "market_cap": "1.7T",
        "pe_ratio": "25.5",
        "dividend_yield": "0.00%",
        "description": "Alphabet Inc. is a holding company that gives ambitious projects the resources, freedom, and focus to make their ideas happen.",
        "status": "success",
        "_mock": True
    },
    "AAPL": {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "market_cap": "2.9T",
        "pe_ratio": "28.3",
        "dividend_yield": "0.50%",
        "description": "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide.",
        "status": "success",
        "_mock": True
    },
    "MSFT": {
        "symbol": "MSFT",
        "name": "Microsoft Corporation",
        "sector": "Technology",
        "industry": "Software—Infrastructure",
        "market_cap": "2.8T",
        "pe_ratio": "32.1",
        "dividend_yield": "0.88%",
        "description": "Microsoft Corporation develops, licenses, and supports software, services, devices, and solutions worldwide.",
        "status": "success",
        "_mock": True
    },
    "DEFAULT": {
        "symbol": "UNKNOWN",
        "name": "Unknown Company",
        "sector": "Unknown",
        "industry": "Unknown",
        "market_cap": "N/A",
        "pe_ratio": "N/A",
        "dividend_yield": "N/A",
        "description": "Company information not available.",
        "status": "success",
        "_mock": True
    }
}

MOCK_ECONOMIC_DATA = {
    "GDP": {
        "series_id": "GDP",
        "data": [
            {"date": "2024-Q3", "value": "27.0"},
            {"date": "2024-Q2", "value": "26.8"},
            {"date": "2024-Q1", "value": "26.5"},
            {"date": "2023-Q4", "value": "26.2"}
        ],
        "count": 4,
        "status": "success",
        "_mock": True
    },
    "UNRATE": {
        "series_id": "UNRATE",
        "data": [
            {"date": "2024-10", "value": "3.9"},
            {"date": "2024-09", "value": "3.8"},
            {"date": "2024-08", "value": "4.0"},
            {"date": "2024-07", "value": "4.1"}
        ],
        "count": 4,
        "status": "success",
        "_mock": True
    },
    "FEDFUNDS": {
        "series_id": "FEDFUNDS",
        "data": [
            {"date": "2024-10", "value": "5.25"},
            {"date": "2024-09", "value": "5.25"},
            {"date": "2024-08", "value": "5.50"},
            {"date": "2024-07", "value": "5.50"}
        ],
        "count": 4,
        "status": "success",
        "_mock": True
    },
    "DEFAULT": {
        "series_id": "UNKNOWN",
        "data": [
            {"date": "2024-01", "value": "100.0"},
            {"date": "2023-12", "value": "99.5"}
        ],
        "count": 2,
        "status": "success",
        "_mock": True
    }
}