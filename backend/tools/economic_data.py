# backend/tools/economic_data.py
import requests
from typing import Dict, Any, List
from .base import BaseTool
from .mock_data import MOCK_ECONOMIC_DATA

class EconomicDataTool(BaseTool):
    """Tool for fetching economic data from FRED"""
    
    def __init__(self, api_key: str = None):
        super().__init__("economic_data", "Fetch economic data from FRED")
        self.api_key = api_key
        self.use_mock = not bool(api_key)
    
    def execute(self, series_id: str, limit: int = 10) -> Dict[str, Any]:
        """Execute economic data fetch"""
        series_id = series_id.upper()
        
        # Use mock data if no API key
        if self.use_mock:
            mock_data = MOCK_ECONOMIC_DATA.get(series_id, MOCK_ECONOMIC_DATA["DEFAULT"]).copy()
            mock_data["series_id"] = series_id
            mock_data["note"] = "Using mock data - no API key configured"
            return mock_data
        
        if not self.can_execute():
            return {
                "series_id": series_id,
                "error": "Rate limit exceeded",
                "note": "Please wait before making another request"
            }
        
        try:
            url = "https://api.stlouisfed.org/fred/series/observations"
            params = {
                "series_id": series_id,
                "api_key": self.api_key,
                "file_type": "json",
                "limit": limit,
                "sort_order": "desc"
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            self.record_execution()
            
            if "error_code" in data:
                # API error, return mock data
                mock_data = MOCK_ECONOMIC_DATA.get(series_id, MOCK_ECONOMIC_DATA["DEFAULT"]).copy()
                mock_data["series_id"] = series_id
                mock_data["note"] = f"API error - using mock data: {data.get('error_message', 'Unknown error')}"
                return mock_data
            
            if "observations" in data:
                observations = data["observations"]
                return {
                    "series_id": series_id,
                    "data": [
                        {
                            "date": obs["date"],
                            "value": obs["value"]
                        }
                        for obs in observations if obs["value"] != "."
                    ],
                    "count": len(observations),
                    "status": "success"
                }
            else:
                # No data, return mock
                mock_data = MOCK_ECONOMIC_DATA.get(series_id, MOCK_ECONOMIC_DATA["DEFAULT"]).copy()
                mock_data["series_id"] = series_id
                mock_data["note"] = "No live data available - using mock data"
                return mock_data
                
        except Exception as e:
            # On any error, return mock data
            mock_data = MOCK_ECONOMIC_DATA.get(series_id, MOCK_ECONOMIC_DATA["DEFAULT"]).copy()
            mock_data["series_id"] = series_id
            mock_data["note"] = f"Error occurred - using mock data: {str(e)}"
            return mock_data