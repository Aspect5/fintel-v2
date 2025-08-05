# backend/registry/__init__.py
"""
Registry Module - Unified Tool and Agent Management

This module provides a unified interface for managing tools and agents
with validation and consistency checks.
"""

from .manager import get_registry_manager, RegistryManager, ValidationResult

__all__ = [
    'get_registry_manager',
    'RegistryManager', 
    'ValidationResult'
] 