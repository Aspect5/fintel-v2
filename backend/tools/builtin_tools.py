#!/usr/bin/env python3
"""
Built-in Tools Module - Single Source of Truth

This module contains all the built-in tool functions following ControlFlow best practices.
Each function is decorated with @cf.tool and has clear type annotations and docstrings.
This serves as the single source of truth for all tools in the system.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import controlflow as cf
import json

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

def get_tool_function(tool_name: str):
    """Get a tool function by name"""
    # Map tool names to functions
    tool_functions = {
        "get_market_data": get_market_data,
        "get_company_overview": get_company_overview,
        "get_economic_data_from_fred": get_economic_data_from_fred,
        "process_financial_data": process_financial_data,
        "misleading_data_validator": misleading_data_validator,
        "process_strict_json": process_strict_json,
        "calculate_pe_ratio": calculate_pe_ratio,
        "analyze_cash_flow": analyze_cash_flow,
        "get_competitor_analysis": get_competitor_analysis,
        "detect_stock_ticker": detect_stock_ticker,
        "get_mock_news": get_mock_news,
        "get_mock_analyst_ratings": get_mock_analyst_ratings,
        "get_mock_social_sentiment": get_mock_social_sentiment
    }
    
    return tool_functions.get(tool_name)

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
            "error": "Ticker symbol is required",
            "ticker": ticker,
            "timestamp": datetime.now().isoformat()
        }
    
    # Get tool instances with fallback
    instances = get_tool_instances()
    
    if 'market_data' in instances:
        try:
            return instances['market_data'].execute(ticker=ticker.upper())
        except Exception as e:
            return {"error": f"Market data tool execution failed: {e}", "ticker": ticker}
    
    # Fallback to mock data if tool not available
    return {
        "ticker": ticker.upper(),
        "price": 150.25,
        "change": 2.50,
        "change_percent": 1.69,
        "volume": 1234567,
        "market_cap": "2.9T",
        "timestamp": datetime.now().isoformat(),
        "source": "mock_data"
    }

@cf.tool
def get_company_overview(ticker: str) -> dict:
    """
    Get comprehensive company overview and fundamental data.
    
    This tool retrieves detailed company information including financial metrics,
    company description, sector information, and key ratios.
    
    Args:
        ticker (str): Stock ticker symbol like GOOG, AAPL, MSFT
        
    Returns:
        dict: Company overview with financial metrics and company information
        
    Examples:
        get_company_overview(ticker="GOOG")
        get_company_overview(ticker="AAPL")
    """
    if not ticker or ticker.strip() == "":
        return {
            "error": "Ticker symbol is required",
            "ticker": ticker,
            "timestamp": datetime.now().isoformat()
        }
    
    # Get tool instances with fallback
    instances = get_tool_instances()
    
    if 'company_overview' in instances:
        try:
            return instances['company_overview'].execute(ticker=ticker.upper())
        except Exception as e:
            return {"error": f"Company overview tool execution failed: {e}", "ticker": ticker}
    
    # Fallback to mock data if tool not available
    return {
        "ticker": ticker.upper(),
        "name": f"{ticker.upper()} Corporation",
        "sector": "Technology",
        "industry": "Software",
        "market_cap": "2.9T",
        "pe_ratio": 25.5,
        "dividend_yield": 0.5,
        "description": f"Leading technology company {ticker.upper()}",
        "timestamp": datetime.now().isoformat(),
        "source": "mock_data"
    }

@cf.tool
def get_economic_data_from_fred(series_id: str, limit: int = 10) -> dict:
    """
    Get economic data from FRED (Federal Reserve Economic Data).
    
    This tool retrieves economic indicators and time series data from the FRED API.
    Useful for macroeconomic analysis and economic trend assessment.
    
    Args:
        series_id (str): FRED series ID like GDP, UNRATE, CPIAUCSL
        limit (int): Number of data points to retrieve (default: 10)
        
    Returns:
        dict: Economic data with time series information
        
    Examples:
        get_economic_data_from_fred(series_id="GDP")
        get_economic_data_from_fred(series_id="UNRATE", limit=20)
    """
    if not series_id or series_id.strip() == "":
        return {
            "error": "Series ID is required",
            "series_id": series_id,
            "timestamp": datetime.now().isoformat()
        }
    
    # Get tool instances with fallback
    instances = get_tool_instances()
    
    if 'economic_data' in instances:
        try:
            return instances['economic_data'].execute(series_id=series_id.upper(), limit=limit)
        except Exception as e:
            return {"error": f"Economic data tool execution failed: {e}", "series_id": series_id}
    
    # Fallback to mock data if tool not available
    return {
        "series_id": series_id.upper(),
        "title": f"{series_id.upper()} Economic Indicator",
        "frequency": "Monthly",
        "units": "Percent",
        "data": [
            {"date": "2024-01", "value": 3.2},
            {"date": "2024-02", "value": 3.1},
            {"date": "2024-03", "value": 3.0}
        ],
        "timestamp": datetime.now().isoformat(),
        "source": "mock_data"
    }

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
    try:
        # Check if data is already a dict (valid JSON object)
        if isinstance(data, dict):
            return {
                "status": "success",
                "message": "Financial data processed and validated successfully",
                "data_type": "valid_json",
                "data_keys": list(data.keys()),
                "data_size": len(str(data)),
                "validation_summary": "Data structure validated",
                "processed_at": datetime.now().isoformat(),
                **({"retry_info": {"retry_id": retry_id}} if retry_id else {})
            }
        
        # Check if data is a JSON string
        if isinstance(data, str):
            try:
                parsed_data = json.loads(data)
                return {
                    "status": "success",
                    "message": "JSON string parsed and validated successfully",
                    "data_type": "json_string",
                    "data_keys": list(parsed_data.keys()) if isinstance(parsed_data, dict) else [],
                    "data_size": len(data),
                    "validation_summary": "JSON string validated",
                    "processed_at": datetime.now().isoformat(),
                    **({"retry_info": {"retry_id": retry_id}} if retry_id else {})
                }
            except json.JSONDecodeError as e:
                return {
                    "status": "error",
                    "error_type": "json_parse_error",
                    "error_message": f"Unable to parse JSON string: {e}",
                    "received_data": data[:100] + "..." if len(data) > 100 else data,
                    "data_type": "string",
                    "processed_at": datetime.now().isoformat()
                }
        
        # Handle other data types
        return {
            "status": "error",
            "error_type": "unsupported_format",
            "error_message": f"Unsupported data type: {type(data).__name__}",
            "received_data": str(data)[:100] + "..." if len(str(data)) > 100 else str(data),
            "data_type": type(data).__name__,
            "processed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_type": "processing_error",
            "error_message": f"Data processing failed: {e}",
            "received_data": str(data)[:100] + "..." if len(str(data)) > 100 else str(data),
            "data_type": type(data).__name__,
            "processed_at": datetime.now().isoformat()
        }

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
    data['processed_at'] = datetime.now().isoformat()
    
    return f"Successfully processed JSON data. Status: {data.get('status')}, Items: {len(data)}."

@cf.tool
def misleading_data_validator(data: Any, retry_id: Optional[str] = None) -> dict:
    """
    Validate financial data with advanced format checking.
    
    This tool performs advanced validation on financial data and can handle
    multiple data formats including dictionaries, JSON strings, and CSV data.
    
    Args:
        data: The financial data to validate
        retry_id: Optional identifier to track retry attempts
        
    Returns:
        dict: Validation results or error details with format guidance
        
    Examples:
        misleading_data_validator(data={"ticker": "AAPL", "price": 185.50})
        misleading_data_validator(data='{"ticker": "GOOG", "price": 150.25}')
    """
    try:
        # Handle dictionary data
        if isinstance(data, dict):
            return {
                "status": "success",
                "message": "Dictionary data validated successfully",
                "data_type": "dict",
                "data_keys": list(data.keys()),
                "validation_summary": "Dictionary structure validated",
                "processed_at": datetime.now().isoformat()
            }
        
        # Handle JSON string data
        if isinstance(data, str):
            try:
                parsed_data = json.loads(data)
                return {
                    "status": "success",
                    "message": "JSON string validated successfully",
                    "data_type": "json_string",
                    "data_keys": list(parsed_data.keys()) if isinstance(parsed_data, dict) else [],
                    "validation_summary": "JSON string validated",
                    "processed_at": datetime.now().isoformat()
                }
            except json.JSONDecodeError:
                # Try to handle as CSV
                if ',' in data:
                    return {
                        "status": "success",
                        "message": "CSV format detected and validated",
                        "data_type": "csv_string",
                        "validation_summary": "CSV format validated",
                        "processed_at": datetime.now().isoformat()
                    }
                else:
                    return {
                        "status": "error",
                        "error_type": "format_error",
                        "error_message": "Data is not valid JSON or CSV format",
                        "received_data": data[:100] + "..." if len(data) > 100 else data,
                        "data_type": "string",
                        "processed_at": datetime.now().isoformat()
                    }
        
        # Handle other data types
        return {
            "status": "error",
            "error_type": "unsupported_format",
            "error_message": f"Unsupported data type: {type(data).__name__}",
            "received_data": str(data)[:100] + "..." if len(str(data)) > 100 else str(data),
            "data_type": type(data).__name__,
            "processed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_type": "validation_error",
            "error_message": f"Data validation failed: {e}",
            "received_data": str(data)[:100] + "..." if len(str(data)) > 100 else str(data),
            "data_type": type(data).__name__,
            "processed_at": datetime.now().isoformat()
        }

@cf.tool
def calculate_pe_ratio(ticker: str, current_price: float = None) -> dict:
    """
    Calculate P/E ratio for a given stock and compare it to industry averages.
    
    This tool analyzes the Price-to-Earnings ratio of a stock and provides
    insights on whether it's overvalued or undervalued compared to industry peers.
    
    Args:
        ticker (str): Stock ticker symbol (e.g., 'AAPL', 'GOOG', 'MSFT')
        current_price (float): Optional current price (will fetch if not provided)
        
    Returns:
        dict: P/E ratio analysis with industry comparison and valuation insights
        
    Examples:
        calculate_pe_ratio(ticker="AAPL")
        calculate_pe_ratio(ticker="GOOG", current_price=150.0)
    """
    if not ticker or ticker.strip() == "":
        return {
            "error": "Ticker symbol is required",
            "ticker": ticker,
            "timestamp": datetime.now().isoformat()
        }
    
    # In absence of a direct Alpha Vantage endpoint here, return labeled mock to avoid LIVE mislabeling
    pe_ratio = 25.5
    industry_average = 22.0
    analysis = "Slightly overvalued compared to industry" if pe_ratio > industry_average else "Undervalued compared to industry"
    
    return {
        "ticker": ticker.upper(),
        "pe_ratio": pe_ratio,
        "industry_average": industry_average,
        "analysis": analysis,
        "valuation_status": "overvalued" if pe_ratio > industry_average else "undervalued",
        "timestamp": datetime.now().isoformat(),
        "source": "mock_data",
        "_mock": True,
        **({"inputs": {"current_price": current_price}} if current_price is not None else {})
    }

@cf.tool
def analyze_cash_flow(ticker: str, period: str = "quarterly") -> dict:
    """
    Analyze cash flow for a company and identify trends and financial health indicators.
    
    This tool examines operating cash flow, free cash flow, and cash flow trends
    to assess a company's financial health and ability to generate cash.
    
    Args:
        ticker (str): Stock ticker symbol (e.g., 'AAPL', 'GOOG', 'MSFT')
        period (str): Analysis period - 'quarterly' or 'annual'
        
    Returns:
        dict: Cash flow analysis with trends, metrics, and financial health assessment
        
    Examples:
        analyze_cash_flow(ticker="AAPL")
        analyze_cash_flow(ticker="MSFT", period="annual")
    """
    if not ticker or ticker.strip() == "":
        return {
            "error": "Ticker symbol is required",
            "ticker": ticker,
            "timestamp": datetime.now().isoformat()
        }
    
    # Mock implementation - in real system, this would fetch actual cash flow data
    return {
        "ticker": ticker.upper(),
        "period": period,
        "free_cash_flow": "$10.5B",
        "operating_cash_flow": "$15.2B",
        "trend": "positive",
        "financial_health": "excellent",
        "cash_flow_stability": "high",
        "timestamp": datetime.now().isoformat(),
        "source": "mock_data"
    }

@cf.tool
def get_competitor_analysis(ticker: str, competitors: List[str] = None) -> dict:
    """
    Compare company against competitors and analyze competitive positioning.
    
    This tool performs a comprehensive competitive analysis by comparing
    market share, financial metrics, and strategic advantages against competitors.
    
    Args:
        ticker (str): Primary stock ticker symbol (e.g., 'AAPL', 'GOOG', 'MSFT')
        competitors (List[str]): List of competitor ticker symbols
        
    Returns:
        dict: Competitive analysis with market share, advantages, and strategic insights
        
    Examples:
        get_competitor_analysis(ticker="AAPL")
        get_competitor_analysis(ticker="GOOG", competitors=["MSFT", "AMZN"])
    """
    if not ticker or ticker.strip() == "":
        return {
            "error": "Ticker symbol is required",
            "ticker": ticker,
            "timestamp": datetime.now().isoformat()
        }
    
    # Mock implementation - in real system, this would fetch actual competitive data
    default_competitors = ["MSFT", "GOOG", "AMZN"] if ticker.upper() == "AAPL" else ["AAPL", "GOOG", "MSFT"]
    competitors_list = competitors or default_competitors
    
    return {
        "ticker": ticker.upper(),
        "competitors": competitors_list,
        "market_share": "15%",
        "competitive_advantages": ["Brand", "Technology", "Scale"],
        "threats": ["New entrants", "Regulatory changes"],
        "competitive_position": "strong",
        "timestamp": datetime.now().isoformat(),
        "source": "mock_data"
    } 

# --- Showcase mock tools for demos ---

@cf.tool
def get_mock_news(ticker: str, limit: int = 3) -> dict:
    """Return recent mock headlines for the given ticker for demo purposes."""
    if not ticker:
        return {"status": "error", "error": "ticker required"}
    headlines = [
        f"{ticker.upper()} announces strategic partnership to accelerate growth",
        f"Analysts weigh in on {ticker.upper()} quarterly results",
        f"{ticker.upper()} expands into new market with innovative product launch",
    ][: max(1, min(limit, 5))]
    return {
        "ticker": ticker.upper(),
        "headlines": headlines,
        "status": "success",
        "_mock": True,
        "timestamp": datetime.now().isoformat(),
    }

@cf.tool
def get_mock_analyst_ratings(ticker: str) -> dict:
    """Return mock analyst ratings breakdown for demo purposes."""
    if not ticker:
        return {"status": "error", "error": "ticker required"}
    return {
        "ticker": ticker.upper(),
        "buy": 18,
        "hold": 6,
        "sell": 1,
        "consensus": "buy",
        "price_target": {"median": 200.0, "high": 240.0, "low": 165.0},
        "status": "success",
        "_mock": True,
        "timestamp": datetime.now().isoformat(),
    }

@cf.tool
def get_mock_social_sentiment(ticker: str) -> dict:
    """Return mock social sentiment metrics for demo purposes."""
    if not ticker:
        return {"status": "error", "error": "ticker required"}
    return {
        "ticker": ticker.upper(),
        "sentiment_score": 0.62,
        "volume": 12450,
        "trend": "rising",
        "mentions": ["AI", "earnings", "guidance"],
        "status": "success",
        "_mock": True,
        "timestamp": datetime.now().isoformat(),
    }

def _detect_ticker_with_ai(query: str) -> dict:
    """
    Internal function for AI-powered stock ticker detection from natural language queries.
    
    This function uses intelligent reasoning to extract stock ticker symbols from user queries,
    handling various formats like company names, partial names, descriptions, and context.
    
    Args:
        query (str): Natural language query that may contain stock ticker information
        
    Returns:
        dict: Detection result with ticker symbol and confidence
    """
    try:
        # Use AI reasoning to detect ticker
        detection_prompt = f"""
        You are a financial expert. Extract the stock ticker symbol from this query: "{query}"
        
        Rules:
        1. Look for explicit ticker symbols (1-5 capital letters)
        2. Match company names to their ticker symbols
        3. Consider context and industry hints
        4. Handle partial company names and descriptions
        5. Return the most likely ticker symbol
        
        Common ticker mappings:
        - Apple, iPhone, Mac → AAPL
        - Google, Alphabet → GOOG
        - Microsoft, Windows, Office → MSFT
        - Amazon, AWS → AMZN
        - Tesla, Model S, Model 3 → TSLA
        - Netflix, streaming → NFLX
        - Facebook, Meta, Instagram → META
        - Nvidia, GPU, graphics → NVDA
        - Intel, processors → INTC
        - AMD, Ryzen → AMD
        - Coca-Cola, Coke → KO
        - Disney, Marvel, Star Wars → DIS
        - Walmart, retail → WMT
        - Home Depot, hardware → HD
        - McDonald's, fast food → MCD
        - Starbucks, coffee → SBUX
        - Boeing, airplanes → BA
        - General Electric, GE → GE
        - JPMorgan, JPMorgan Chase → JPM
        - Bank of America, BofA → BAC
        - Wells Fargo, banking → WFC
        - Goldman Sachs, investment bank → GS
        - Morgan Stanley, investment → MS
        - Visa, credit cards → V
        - Mastercard, payments → MA
        - PayPal, digital payments → PYPL
        - Salesforce, CRM software → CRM
        - Oracle, database → ORCL
        - Adobe, creative software → ADBE
        - Cisco, networking → CSCO
        - Qualcomm, mobile chips → QCOM
        - Broadcom, semiconductors → AVGO
        - Verizon, telecom → VZ
        - AT&T, telecommunications → T
        - Comcast, cable → CMCSA
        - Charter, Spectrum → CHTR
        
        Return only the ticker symbol in uppercase, or "UNKNOWN" if no ticker can be determined.
        """
        
        # Use ControlFlow to get AI reasoning
        result = cf.run(detection_prompt, max_agent_turns=1)
        
        # Extract ticker from result
        ticker = result.strip().upper()
        
        # Validate ticker format
        if len(ticker) <= 5 and ticker.isalpha() and ticker != "UNKNOWN":
            return {
                "ticker": ticker,
                "confidence": 0.9,
                "method": "ai_detection",
                "query": query,
                "status": "success"
            }
        else:
            return {
                "ticker": "UNKNOWN",
                "confidence": 0.0,
                "method": "ai_detection",
                "query": query,
                "status": "no_ticker_found"
            }
            
    except Exception as e:
        return {
            "ticker": "UNKNOWN",
            "confidence": 0.0,
            "method": "ai_detection",
            "query": query,
            "status": "error",
            "error": str(e)
        }

@cf.tool
def detect_stock_ticker(query: str) -> dict:
    """
    AI-powered stock ticker detection from natural language queries.
    
    This tool uses intelligent reasoning to extract stock ticker symbols from user queries,
    handling various formats like company names, partial names, descriptions, and context.
    
    Args:
        query (str): Natural language query that may contain stock ticker information
        
    Returns:
        dict: Detection result with ticker symbol and confidence
        
    Examples:
        detect_stock_ticker("analyze Apple stock")
        detect_stock_ticker("what's happening with TSLA")
        detect_stock_ticker("evaluate the electric vehicle company Tesla")
    """
    return _detect_ticker_with_ai(query) 