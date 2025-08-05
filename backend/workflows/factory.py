# backend/workflows/factory.py
"""
Config-Driven Workflow Factory

Creates workflow instances from configuration files.
Single source of truth for workflow creation and validation.
"""

from typing import Dict, List, Any, Optional
from .config_driven_workflow import ConfigDrivenWorkflow, create_config_driven_workflow
from .config_loader import get_workflow_config_loader
from ..providers.factory import ProviderFactory
from ..utils.logging import setup_logging

logger = setup_logging()

class WorkflowValidationError(Exception):
    """Raised when workflow validation fails"""
    pass

class ConfigDrivenWorkflowFactory:
    """Factory for creating workflows from configuration"""
    
    def __init__(self):
        self.config_loader = get_workflow_config_loader()
        self.provider_factory = ProviderFactory()
        
        # Import agent factory here to avoid circular import
        from ..agents.factory import get_agent_factory
        self.agent_factory = get_agent_factory()
    
    def get_available_workflows(self) -> List[Dict[str, Any]]:
        """Get all available workflow types from configuration"""
        
        workflows = []
        
        # Get workflow configurations
        config = self.config_loader.config
        workflow_configs = config.get('workflows', {})
        
        for workflow_type, workflow_config in workflow_configs.items():
            
            # Validate workflow can be created
            validation_result = self.validate_workflow(workflow_type, 'openai')
            
            workflow_info = {
                'type': workflow_type,
                'name': workflow_config.get('name', workflow_type),
                'description': workflow_config.get('description', ''),
                'available': validation_result['valid'],
                'agents': len(workflow_config.get('agents', [])),
                'required_agents': len([a for a in workflow_config.get('agents', []) if a.get('required', False)]),
                'validation': validation_result
            }
            
            workflows.append(workflow_info)
        
        logger.info(f"Found {len(workflows)} available workflow types")
        return workflows
    
    def create_workflow(self, workflow_type: str) -> ConfigDrivenWorkflow:
        """
        Create a workflow instance of the specified type
        
        Args:
            workflow_type: Type of workflow from workflow_config.yaml
            
        Returns:
            ConfigDrivenWorkflow instance
            
        Raises:
            WorkflowValidationError: If workflow cannot be created
        """
        
        # Validate workflow before creation
        validation_result = self.validate_workflow(workflow_type, 'openai')  # Default to openai for validation
        
        if not validation_result['valid']:
            error_msg = f"Cannot create workflow '{workflow_type}': {validation_result.get('error', 'Validation failed')}"
            logger.error(error_msg)
            raise WorkflowValidationError(error_msg)
        
        if validation_result.get('warnings'):
            for warning in validation_result['warnings']:
                logger.warning(f"Workflow '{workflow_type}' warning: {warning}")
        
        # Create workflow instance
        try:
            workflow = create_config_driven_workflow(workflow_type)
            logger.info(f"Created workflow instance: {workflow_type}")
            return workflow
            
        except Exception as e:
            error_msg = f"Failed to create workflow '{workflow_type}': {str(e)}"
            logger.error(error_msg)
            raise WorkflowValidationError(error_msg)
    
    def validate_workflow(self, workflow_type: str, provider_name: str) -> Dict[str, Any]:
        """
        Validate that a workflow can be executed with the given provider
        
        Args:
            workflow_type: Type of workflow to validate
            provider_name: Provider to use for validation
            
        Returns:
            Validation result with details
        """
        
        try:
            # Check if workflow exists in config
            workflow_config = self.config_loader.get_workflow_config(workflow_type)
            if not workflow_config:
                return {
                    "valid": False,
                    "error": f"Workflow type '{workflow_type}' not found in configuration"
                }
            
            # Validate provider
            provider = self.provider_factory.get_provider(provider_name)
            if not provider or not provider.is_available():
                return {
                    "valid": False,
                    "error": f"Provider '{provider_name}' not available"
                }
            
            # Validate agents can be created
            agent_validation = self.agent_factory.validate_workflow_agents(workflow_type, provider_name)
            
            if not agent_validation.get("valid", False):
                return {
                    "valid": False,
                    "error": agent_validation.get("error", "Agent validation failed"),
                    "agent_validation": agent_validation
                }
            
            # Compile validation result
            validation_result = {
                "valid": True,
                "workflow_type": workflow_type,
                "provider": provider_name,
                "agents": agent_validation.get("agents", {}),
                "warnings": agent_validation.get("warnings", [])
            }
            
            # Add any workflow-specific warnings
            agents_config = workflow_config.get('agents', [])
            required_agents = [a for a in agents_config if a.get('required', False)]
            
            if len(required_agents) == 0:
                validation_result["warnings"].append("No required agents specified - workflow may not be stable")
            
            return validation_result
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Validation error: {str(e)}"
            }
    
    def validate_workflow_execution(self, workflow_type: str, provider_name: str, query: str) -> Dict[str, Any]:
        """
        Validate that a specific workflow execution can proceed
        
        This performs more strict validation that would prevent execution.
        """
        
        # Basic workflow validation
        base_validation = self.validate_workflow(workflow_type, provider_name)
        
        if not base_validation["valid"]:
            return base_validation
        
        # Additional execution-specific validations
        validation_result = base_validation.copy()
        execution_warnings = []
        
        # Check if query is meaningful
        if not query or len(query.strip()) < 3:
            validation_result["valid"] = False
            validation_result["error"] = "Query too short or empty"
            return validation_result
        
        # Check for potential ticker extraction
        try:
            from backend.tools.builtin_tools import _detect_ticker_with_ai
            ticker_result = _detect_ticker_with_ai(query)
            
            if ticker_result["status"] != "success" or ticker_result["ticker"] == "UNKNOWN":
                execution_warnings.append("Could not detect stock ticker from query - using fallback")
                
        except Exception:
            execution_warnings.append("Ticker detection unavailable - using fallback")
        
        # Add execution warnings
        validation_result["warnings"].extend(execution_warnings)
        validation_result["execution_ready"] = True
        
        return validation_result
    
    def get_workflow_info(self, workflow_type: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific workflow type"""
        
        workflow_config = self.config_loader.get_workflow_config(workflow_type)
        if not workflow_config:
            return None
        
        # Get validation status with default provider
        validation = self.validate_workflow(workflow_type, 'openai')
        
        return {
            'type': workflow_type,
            'name': workflow_config.get('name', workflow_type),
            'description': workflow_config.get('description', ''),
            'configuration': workflow_config,
            'validation': validation,
            'available': validation['valid'],
            'agents': [
                {
                    'name': agent.get('name'),
                    'role': agent.get('role'),
                    'required': agent.get('required', False),
                    'tools': agent.get('tools', []),
                    'fallback': agent.get('fallback')
                }
                for agent in workflow_config.get('agents', [])
            ]
        }

# Singleton instance
_workflow_factory_instance = None

def get_workflow_factory() -> ConfigDrivenWorkflowFactory:
    """Get singleton workflow factory instance"""
    global _workflow_factory_instance
    if _workflow_factory_instance is None:
        _workflow_factory_instance = ConfigDrivenWorkflowFactory()
    return _workflow_factory_instance