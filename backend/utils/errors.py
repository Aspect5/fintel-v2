class FintelError(Exception):
    """Base exception for Fintel application"""
    pass

class ProviderError(FintelError):
    """Exception for provider-related errors"""
    pass

class WorkflowError(FintelError):
    """Exception for workflow-related errors"""
    pass

class ToolError(FintelError):
    """Exception for tool-related errors"""
    pass

class ConfigurationError(FintelError):
    """Exception for configuration-related errors"""
    pass