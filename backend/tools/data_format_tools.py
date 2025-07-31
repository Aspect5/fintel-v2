# backend/tools/data_format_tools.py
import json
from typing import Dict, Any, Optional
from .base import BaseTool

class JsonOnlyDataTool(BaseTool):
    """Tool for processing and validating financial data in structured format"""
    
    def __init__(self):
        super().__init__(
            name="process_financial_data",
            description="Validate and ensure data quality for financial analysis. Use this tool to check data consistency, validate metrics, and ensure proper formatting before analysis. Essential for data quality assurance in financial reporting."
        )
        self._retry_attempts = {}
    
    def execute(self, data: Any, retry_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process financial data with validation
        
        Args:
            data: The financial data to process and validate
            retry_id: Optional identifier to track retry attempts
            
        Returns:
            Dict containing processing results or error details
        """
        # Track retry attempts
        if retry_id:
            if retry_id not in self._retry_attempts:
                self._retry_attempts[retry_id] = {
                    'attempts': 0,
                    'failed_formats': [],
                    'errors': []
                }
            self._retry_attempts[retry_id]['attempts'] += 1
        
        # Check if data is already a dict (valid JSON object)
        if isinstance(data, dict):
            return self._process_valid_json(data, retry_id)
        
        # Check if data is a JSON string
        if isinstance(data, str):
            try:
                parsed_data = json.loads(data)
                return self._process_valid_json(parsed_data, retry_id)
            except json.JSONDecodeError as e:
                return self._handle_json_error(data, str(e), retry_id)
        
        # Handle other data types
        return self._handle_invalid_format(data, retry_id)
    
    def _process_valid_json(self, data: Dict[str, Any], retry_id: Optional[str] = None) -> Dict[str, Any]:
        """Process valid JSON data"""
        result = {
            "status": "success",
            "message": "Financial data processed and validated successfully",
            "data_type": "valid_json",
            "data_keys": list(data.keys()) if isinstance(data, dict) else [],
            "data_size": len(str(data)),
            "validation_summary": self._generate_validation_summary(data),
            "processed_at": self._get_timestamp()
        }
        
        # Add retry information if this was a retry
        if retry_id and retry_id in self._retry_attempts:
            retry_info = self._retry_attempts[retry_id]
            result["retry_info"] = {
                "attempt_number": retry_info['attempts'],
                "previous_failures": retry_info['failed_formats'],
                "previous_errors": retry_info['errors']
            }
        
        return result
    
    def _generate_validation_summary(self, data: Dict[str, Any]) -> str:
        """Generate a summary of the financial data validation"""
        if not isinstance(data, dict):
            return "Data structure validated"
        
        # Check for common financial data fields
        financial_fields = ['price', 'volume', 'market_cap', 'pe_ratio', 'ticker', 'symbol', 'revenue', 'earnings']
        found_fields = [field for field in financial_fields if field in data]
        
        if found_fields:
            return f"Validated financial data with {len(found_fields)} key metrics: {', '.join(found_fields)}"
        else:
            return "Data structure validated - no standard financial fields detected"
    
    def _handle_json_error(self, data: str, error_msg: str, retry_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle JSON parsing errors"""
        if retry_id and retry_id in self._retry_attempts:
            self._retry_attempts[retry_id]['failed_formats'].append('invalid_json_string')
            self._retry_attempts[retry_id]['errors'].append(error_msg)
        
        return {
            "status": "error",
            "error_type": "data_format_error",
            "error_message": f"Unable to process data format: {error_msg}",
            "received_data": data[:100] + "..." if len(data) > 100 else data,
            "data_type": "string",
            "expected_format": "structured data in JSON format (e.g., {'price': 150.25, 'volume': 1234567})",
            "suggestion": "Please provide the financial data in a structured format with key-value pairs",
            "retry_id": retry_id,
            "timestamp": self._get_timestamp()
        }
    
    def _handle_invalid_format(self, data: Any, retry_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle non-JSON data types"""
        data_type = type(data).__name__
        
        if retry_id and retry_id in self._retry_attempts:
            self._retry_attempts[retry_id]['failed_formats'].append(data_type)
            self._retry_attempts[retry_id]['errors'].append(f"Expected structured data, got {data_type}")
        
        return {
            "status": "error",
            "error_type": "data_format_error",
            "error_message": f"This tool requires structured data for processing, but received {data_type}",
            "received_data": str(data)[:100] + "..." if len(str(data)) > 100 else str(data),
            "data_type": data_type,
            "expected_format": "structured data with financial metrics",
            "suggestion": f"Please convert {data_type} to a structured format. For example: {self._get_conversion_example(data)}",
            "retry_id": retry_id,
            "timestamp": self._get_timestamp()
        }
    
    def _get_conversion_example(self, data: Any) -> str:
        """Provide conversion examples based on data type"""
        if isinstance(data, (list, tuple)):
            return f"Convert to dict: {{'data': {data}}}"
        elif isinstance(data, (int, float, bool)):
            return f"Convert to dict: {{'value': {data}}}"
        elif isinstance(data, str):
            return f"Convert to dict: {{'text': \"{data}\"}}"
        else:
            return f"Convert to dict: {{'data': {data}}}"
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_retry_stats(self) -> Dict[str, Any]:
        """Get statistics about retry attempts"""
        total_retries = sum(info['attempts'] for info in self._retry_attempts.values())
        total_failures = sum(len(info['failed_formats']) for info in self._retry_attempts.values())
        
        return {
            "total_retry_sessions": len(self._retry_attempts),
            "total_retry_attempts": total_retries,
            "total_failures": total_failures,
            "retry_sessions": self._retry_attempts
        }

class MisleadingDataValidator(BaseTool):
    """Tool that deliberately provides misleading format guidance to test agent retry capabilities"""
    
    def __init__(self):
        super().__init__(
            name="misleading_data_validator",
            description="Validate financial data with advanced format checking. IMPORTANT: This tool requires data in CSV format with comma-separated values. Example: 'AAPL,185.50,2345678,28.3'"
        )
        self._retry_attempts = {}
    
    def execute(self, data: Any, retry_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate financial data with misleading format requirements
        
        Args:
            data: The financial data to validate
            retry_id: Optional identifier to track retry attempts
            
        Returns:
            Dict containing validation results or error details
        """
        # Track retry attempts
        if retry_id:
            if retry_id not in self._retry_attempts:
                self._retry_attempts[retry_id] = {
                    'attempts': 0,
                    'failed_formats': [],
                    'errors': []
                }
            self._retry_attempts[retry_id]['attempts'] += 1
        
        # MISLEADING: We claim to want CSV but actually want JSON/dict
        # Check if data is a dict (what we actually want, but we'll reject it first)
        if isinstance(data, dict):
            # After 2 failed attempts, accept dict format
            if retry_id and retry_id in self._retry_attempts and self._retry_attempts[retry_id]['attempts'] >= 2:
                return self._process_dict_data(data, retry_id)
            else:
                return self._handle_dict_error(data, retry_id)
        
        # Check if data is a CSV string (what we claim to want, but we'll reject it too)
        if isinstance(data, str) and ',' in data and not data.startswith('{'):
            # After 3 failed attempts, accept CSV format
            if retry_id and retry_id in self._retry_attempts and self._retry_attempts[retry_id]['attempts'] >= 3:
                return self._process_csv_data(data, retry_id)
            else:
                return self._handle_csv_error(data, "CSV format not supported in this version", retry_id)
        
        # Check if data is a list
        if isinstance(data, list):
            return self._handle_list_error(data, retry_id)
        
        # Handle other data types
        return self._handle_invalid_format(data, retry_id)
    
    def _process_dict_data(self, data: Dict[str, Any], retry_id: Optional[str] = None) -> Dict[str, Any]:
        """Process dict data (what we actually want)"""
        try:
            # Validate required fields
            required_fields = ['ticker', 'price', 'volume']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                return self._handle_dict_error(data, f"Missing required fields: {', '.join(missing_fields)}", retry_id)
            
            result = {
                "status": "success",
                "message": "JSON data validated and processed successfully",
                "data_type": "dict",
                "parsed_data": data,
                "validation_summary": f"Validated JSON with {len(data)} fields: {', '.join(data.keys())}",
                "processed_at": self._get_timestamp()
            }
            
            # Add retry information if this was a retry
            if retry_id and retry_id in self._retry_attempts:
                retry_info = self._retry_attempts[retry_id]
                result["retry_info"] = {
                    "attempt_number": retry_info['attempts'],
                    "previous_failures": retry_info['failed_formats'],
                    "previous_errors": retry_info['errors']
                }
            
            return result
        except Exception as e:
            return self._handle_dict_error(data, str(e), retry_id)
    
    def _process_csv_data(self, data: str, retry_id: Optional[str] = None) -> Dict[str, Any]:
        """Process CSV data (but actually convert it to dict for success)"""
        try:
            # Parse CSV and convert to dict for actual processing
            parts = data.split(',')
            if len(parts) >= 3:
                # Convert to dict format (what we actually want)
                dict_data = {
                    'ticker': parts[0].strip(),
                    'price': float(parts[1].strip()),
                    'volume': int(parts[2].strip())
                }
                if len(parts) >= 4:
                    dict_data['pe_ratio'] = float(parts[3].strip())
                
                result = {
                    "status": "success",
                    "message": "CSV data validated and processed successfully",
                    "data_type": "csv_string",
                    "parsed_data": dict_data,
                    "validation_summary": f"Validated CSV with {len(dict_data)} fields: {', '.join(dict_data.keys())}",
                    "processed_at": self._get_timestamp()
                }
                
                # Add retry information if this was a retry
                if retry_id and retry_id in self._retry_attempts:
                    retry_info = self._retry_attempts[retry_id]
                    result["retry_info"] = {
                        "attempt_number": retry_info['attempts'],
                        "previous_failures": retry_info['failed_formats'],
                        "previous_errors": retry_info['errors']
                    }
                
                return result
            else:
                return self._handle_csv_error(data, "Insufficient CSV fields", retry_id)
        except (ValueError, IndexError) as e:
            return self._handle_csv_error(data, str(e), retry_id)
    
    def _handle_csv_error(self, data: str, error_msg: str, retry_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle CSV parsing errors"""
        if retry_id and retry_id in self._retry_attempts:
            self._retry_attempts[retry_id]['failed_formats'].append('invalid_csv')
            self._retry_attempts[retry_id]['errors'].append(error_msg)
        
        return {
            "status": "error",
            "error_type": "csv_format_error",
            "error_message": f"Invalid CSV format: {error_msg}",
            "received_data": data[:100] + "..." if len(data) > 100 else data,
            "data_type": "csv_string",
            "expected_format": "CSV format with comma-separated values (e.g., 'AAPL,185.50,2345678,28.3')",
            "suggestion": "Please provide data in CSV format with ticker, price, volume, and optional P/E ratio",
            "retry_id": retry_id,
            "timestamp": self._get_timestamp()
        }
    
    def _handle_dict_error(self, data: Dict[str, Any], retry_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle dict data (reject it to force retry)"""
        if retry_id and retry_id in self._retry_attempts:
            self._retry_attempts[retry_id]['failed_formats'].append('dict')
            self._retry_attempts[retry_id]['errors'].append("This tool requires CSV format, not JSON")
        
        return {
            "status": "error",
            "error_type": "format_mismatch",
            "error_message": "This tool requires CSV format, not JSON/dict format",
            "received_data": str(data)[:100] + "..." if len(str(data)) > 100 else str(data),
            "data_type": "dict",
            "expected_format": "CSV format with comma-separated values (e.g., 'AAPL,185.50,2345678,28.3')",
            "suggestion": "Please convert your JSON data to CSV format. For example: convert {'ticker': 'AAPL', 'price': 185.50} to 'AAPL,185.50'",
            "retry_id": retry_id,
            "timestamp": self._get_timestamp()
        }
    
    def _handle_list_error(self, data: list, retry_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle list data (reject it to force retry)"""
        if retry_id and retry_id in self._retry_attempts:
            self._retry_attempts[retry_id]['failed_formats'].append('list')
            self._retry_attempts[retry_id]['errors'].append("This tool requires CSV format, not list format")
        
        return {
            "status": "error",
            "error_type": "format_mismatch",
            "error_message": "This tool requires CSV format, not list format",
            "received_data": str(data)[:100] + "..." if len(str(data)) > 100 else str(data),
            "data_type": "list",
            "expected_format": "CSV format with comma-separated values (e.g., 'AAPL,185.50,2345678,28.3')",
            "suggestion": f"Please convert your list to CSV format. For example: convert {data} to '{','.join(map(str, data))}'",
            "retry_id": retry_id,
            "timestamp": self._get_timestamp()
        }
    
    def _handle_invalid_format(self, data: Any, retry_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle other data types"""
        data_type = type(data).__name__
        
        if retry_id and retry_id in self._retry_attempts:
            self._retry_attempts[retry_id]['failed_formats'].append(data_type)
            self._retry_attempts[retry_id]['errors'].append(f"Expected CSV format, got {data_type}")
        
        return {
            "status": "error",
            "error_type": "format_mismatch",
            "error_message": f"This tool requires CSV format, but received {data_type}",
            "received_data": str(data)[:100] + "..." if len(str(data)) > 100 else str(data),
            "data_type": data_type,
            "expected_format": "CSV format with comma-separated values (e.g., 'AAPL,185.50,2345678,28.3')",
            "suggestion": f"Please convert {data_type} to CSV format. For example: convert {data} to a comma-separated string",
            "retry_id": retry_id,
            "timestamp": self._get_timestamp()
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()

# Create singleton instances for easy import
process_financial_data_tool = JsonOnlyDataTool()
misleading_data_validator_tool = MisleadingDataValidator()

def process_financial_data(data: Any, retry_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to call the financial data processing tool
    
    Args:
        data: The financial data to process and validate
        retry_id: Optional identifier to track retry attempts
        
    Returns:
        Dict containing processing results or error details
    """
    return process_financial_data_tool.execute(data, retry_id)

def misleading_data_validator(data: Any, retry_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to call the misleading data validator tool
    
    Args:
        data: The financial data to validate (misleadingly requires CSV format)
        retry_id: Optional identifier to track retry attempts
        
    Returns:
        Dict containing validation results or error details
    """
    return misleading_data_validator_tool.execute(data, retry_id) 