#!/usr/bin/env python3
"""
Built-in Tools Module

This module contains all the built-in tool functions that are automatically
discovered by the AutoToolDiscovery system. Each function should have a
clear docstring that describes its purpose and parameters.
"""

from typing import Dict, Any, Optional
import controlflow as cf

# Global reference to tool instances (will be set by registry)
_tool_instances = {}

def set_tool_instances(instances: Dict[str, Any]):
    """Set the tool instances for use by the tool functions"""
    global _tool_instances
    _tool_instances = instances

@cf.tool
def get_market_data(ticker: str) -> dict:
    """
    Get real-time market data for a stock ticker.
    
    This tool retrieves current stock price, volume, and market data for a given ticker symbol.
    It uses the Alpha Vantage API to fetch real-time market information.
    
    Args:
        ticker (str): Stock ticker symbol like GOOG, AAPL, MSFT
        
    Returns:
        dict: Market data with price, change, volume, and other market metrics
        
    Examples:
        get_market_data(ticker="GOOG")
        get_market_data(ticker="AAPL")
    """
    if not ticker or ticker.strip() == "":
        return {
            "error": "Missing ticker parameter",
            "hint": "Call like this: get_market_data(ticker='GOOG')"
        }
    
    ticker = ticker.upper().strip()
    if 'market_data' in _tool_instances:
        return _tool_instances['market_data'].execute(ticker=ticker)
    return {"error": "Market data tool not available", "ticker": ticker}

@cf.tool
def get_company_overview(ticker: str) -> dict:
    """
    Get comprehensive company overview including sector, industry, market cap, P/E ratio, and business description.
    
    This tool fetches detailed company information including fundamentals, business description,
    sector classification, and key financial metrics from Alpha Vantage.
    
    Args:
        ticker (str): The stock ticker symbol (e.g., 'GOOG', 'AAPL', 'MSFT')
        
    Returns:
        dict: Company overview data with fundamentals and business information
        
    Examples:
        get_company_overview(ticker="GOOG")
        get_company_overview(ticker="MSFT")
    """
    if not ticker or ticker.strip() == "":
        return {
            "error": "Missing required parameter 'ticker'",
            "message": "Please provide a stock ticker symbol like 'GOOG' or 'AAPL'",
            "example_usage": "get_company_overview(ticker='GOOG')"
        }
    
    if 'company_overview' in _tool_instances:
        return _tool_instances['company_overview'].execute(ticker=ticker.upper())
    return {"error": "Company overview tool not available", "ticker": ticker}

@cf.tool
def get_economic_data_from_fred(series_id: str, limit: int = 10) -> dict:
    """
    Get economic data from Federal Reserve (FRED) for indicators like GDP, unemployment rate, and interest rates.
    
    This tool retrieves economic indicators from the Federal Reserve Economic Data (FRED) API.
    It provides access to thousands of economic time series data points.
    
    Args:
        series_id (str): The FRED series ID (e.g., 'GDP', 'UNRATE', 'FEDFUNDS')
        limit (int): Number of recent data points to return (default: 10)
        
    Returns:
        dict: Economic data for the specified series with timestamps and values
        
    Examples:
        get_economic_data_from_fred(series_id="GDP")
        get_economic_data_from_fred(series_id="UNRATE", limit=20)
    """
    if not series_id or series_id.strip() == "":
        return {
            "error": "Missing required parameter 'series_id'",
            "message": "Please provide a FRED series ID like 'GDP', 'UNRATE', or 'FEDFUNDS'",
            "example_usage": "get_economic_data_from_fred(series_id='GDP')"
        }
    
    if 'economic_data' in _tool_instances:
        return _tool_instances['economic_data'].execute(series_id=series_id.upper(), limit=limit)
    return {"error": "Economic data tool not available", "series_id": series_id}

@cf.tool
def process_strict_json(data: dict) -> str:
    """
    Process a dictionary of financial data with strict JSON validation.
    
    This tool validates and processes financial data in JSON format. It ensures
    the input is a valid Python dictionary and performs basic data validation.
    
    Args:
        data (dict): A Python dictionary containing financial data
        
    Returns:
        str: Processing status and validation results
        
    Examples:
        process_strict_json(data={"asset": "BTC", "value": 70000})
        process_strict_json(data={"portfolio": {"stocks": ["AAPL", "GOOG"]}})
    """
    if not isinstance(data, dict):
        raise TypeError(f"Invalid input type: Expected dict, but got {type(data).__name__}. You must parse the input into a dictionary.")
    
    # Simulate some processing
    data['status'] = 'processed'
    return f"Successfully processed JSON data. Status: {data.get('status')}, Items: {len(data)}." 