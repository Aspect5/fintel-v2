import requests
from typing import Dict, Any, List
from .base import BaseTool

class EconomicDataTool(BaseTool):
    """Tool for fetching economic data from FRED"""
    
    def __init__(self, api_key: str):
        super().__init__("economic_data", "Fetch economic data from FRED")
        self.api_key = api_key
    
    def execute(self, series_id: str, limit: int = 10) -> Dict[str, Any]:
        """Execute economic data fetch"""
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
                return {
                    "series_id": series_id,
                    "error": f"FRED API Error: {data.get('error_message', 'Unknown error')}",
                    "note": "Check series ID or API key"
                }
            
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
                return {
                    "series_id": series_id,
                    "error": "No data available",
                    "note": "Series may not exist or have no recent data"
                }
                
        except Exception as e:
            return {
                "series_id": series_id,
                "error": f"Request failed: {str(e)}",
                "note": "Network or API error occurred"
            }