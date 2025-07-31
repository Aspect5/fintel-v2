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
    print(f"Tool instances set: {list(instances.keys())}")

def get_tool_instances() -> Dict[str, Any]:
    """Get tool instances with fallback to registry"""
    global _tool_instances
    
    # If we have instances, return them
    if _tool_instances:
        return _tool_instances
    
    # Fallback: try to get from registry directly
    try:
        from backend.tools.registry import get_tool_registry
        registry = get_tool_registry()
        return registry._tool_instances
    except Exception as e:
        print(f"Warning: Could not get tool instances from registry: {e}")
        return {}

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
    
    # Get tool instances with fallback
    instances = get_tool_instances()
    
    if 'market_data' in instances:
        try:
            return instances['market_data'].execute(ticker=ticker)
        except Exception as e:
            return {"error": f"Market data tool execution failed: {e}", "ticker": ticker}
    
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
    
    ticker = ticker.upper().strip()
    
    # Get tool instances with fallback
    instances = get_tool_instances()
    
    if 'company_overview' in instances:
        try:
            return instances['company_overview'].execute(ticker=ticker)
        except Exception as e:
            return {"error": f"Company overview tool execution failed: {e}", "ticker": ticker}
    
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
    
    # Get tool instances with fallback
    instances = get_tool_instances()
    
    if 'economic_data' in instances:
        try:
            return instances['economic_data'].execute(series_id=series_id.upper(), limit=limit)
        except Exception as e:
            return {"error": f"Economic data tool execution failed: {e}", "series_id": series_id}
    
    return {"error": "Economic data tool not available", "series_id": series_id}

@cf.tool
def process_financial_data(data: Any, retry_id: Optional[str] = None) -> dict:
    """
    Validate and ensure data quality for financial analysis.
    
    Use this tool to check data consistency, validate metrics, and ensure proper formatting before analysis. 
    Essential for data quality assurance in financial reporting.
    
    Args:
        data: The financial data to process and validate
        retry_id: Optional identifier to track retry attempts
        
    Returns:
        dict: Processing results or error details with validation information
        
    Examples:
        process_financial_data(data={"price": 150.25, "volume": 1234567})
        process_financial_data(data={"ticker": "AAPL", "market_cap": "2.9T"})
    """
    # Get tool instances with fallback
    instances = get_tool_instances()
    
    if 'process_financial_data' in instances:
        try:
            return instances['process_financial_data'].execute(data=data, retry_id=retry_id)
        except Exception as e:
            return {"error": f"Financial data processing failed: {e}", "data": str(data)}
    
    return {"error": "Financial data processing tool not available", "data": str(data)}

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

@cf.tool
def misleading_data_validator(data: Any, retry_id: Optional[str] = None) -> dict:
    """
    Validate financial data with advanced format checking.
    
    IMPORTANT: This tool requires data in CSV format with comma-separated values.
    Example: 'AAPL,185.50,2345678,28.3'
    
    This tool performs advanced validation on financial data and requires
    specific CSV formatting for optimal processing.
    
    Args:
        data: The financial data to validate (must be CSV format)
        retry_id: Optional identifier to track retry attempts
        
    Returns:
        dict: Validation results or error details with CSV format guidance
        
    Examples:
        misleading_data_validator(data="AAPL,185.50,2345678,28.3")
        misleading_data_validator(data={"ticker": "AAPL", "price": 185.50}, retry_id="retry_1")
    """
    # Get tool instances with fallback
    instances = get_tool_instances()
    
    if 'misleading_data_validator' in instances:
        try:
            return instances['misleading_data_validator'].execute(data=data, retry_id=retry_id)
        except Exception as e:
            return {"error": f"Misleading data validation failed: {e}", "data": str(data)}
    
    return {"error": "Misleading data validation tool not available", "data": str(data)} 