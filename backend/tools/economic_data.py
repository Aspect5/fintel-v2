# backend/tools/economic_data.py
import requests
from typing import Dict, Any
from .base import BaseTool
from .mock_data import MOCK_ECONOMIC_DATA
from backend.utils.http_client import fred_request

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
            params = {
                "series_id": series_id,
                "limit": limit,
                "sort_order": "desc",
            }
            data = fred_request(params)
            self.record_execution()

            if not data:
                mock_data = MOCK_ECONOMIC_DATA.get(series_id, MOCK_ECONOMIC_DATA["DEFAULT"]).copy()
                mock_data["series_id"] = series_id
                mock_data["note"] = "API unavailable/limited - using mock data"
                return mock_data

            if "error_code" in data:
                mock_data = MOCK_ECONOMIC_DATA.get(series_id, MOCK_ECONOMIC_DATA["DEFAULT"]).copy()
                mock_data["series_id"] = series_id
                mock_data["note"] = f"API error - using mock data: {data.get('error_message', 'Unknown error')}"
                return mock_data

            if "observations" in data:
                observations = data["observations"]
                return {
                    "series_id": series_id,
                    "data": [
                        {"date": obs["date"], "value": obs["value"]}
                        for obs in observations if obs.get("value") not in (None, ".")
                    ],
                    "count": len(observations),
                    "status": "success",
                }

            mock_data = MOCK_ECONOMIC_DATA.get(series_id, MOCK_ECONOMIC_DATA["DEFAULT"]).copy()
            mock_data["series_id"] = series_id
            mock_data["note"] = "No live data available - using mock data"
            return mock_data

        except Exception as e:
            mock_data = MOCK_ECONOMIC_DATA.get(series_id, MOCK_ECONOMIC_DATA["DEFAULT"]).copy()
            mock_data["series_id"] = series_id
            mock_data["note"] = f"Error occurred - using mock data: {str(e)}"
            return mock_data