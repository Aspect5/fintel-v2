# Workflow modules - config-driven single source of truth
from .base import BaseWorkflow
from .config_loader import get_workflow_config_loader

__all__ = [
    'BaseWorkflow', 
    'get_workflow_config_loader',
    'get_workflow_factory',
    'create_config_driven_workflow'
]

# Import factory and workflow functions when needed to avoid circular imports
def get_workflow_factory():
    from .factory import get_workflow_factory as _get_workflow_factory
    return _get_workflow_factory()

def create_config_driven_workflow(workflow_type: str = "enhanced_simplified"):
    from .config_driven_workflow import create_config_driven_workflow as _create_config_driven_workflow
    return _create_config_driven_workflow(workflow_type)