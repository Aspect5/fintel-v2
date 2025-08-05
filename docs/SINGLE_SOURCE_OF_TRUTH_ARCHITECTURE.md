# Single Source of Truth Architecture

## Overview

The Fintel v2 system has been redesigned with a **Single Source of Truth (SSOT)** architecture to eliminate configuration conflicts, improve maintainability, and provide comprehensive validation. This document outlines the new architecture and how to use it.

## Architecture Components

### 1. Unified Registry Manager (`backend/registry/manager.py`)

The **Registry Manager** is the central coordinator that manages both tools and agents, ensuring consistency and validation across the entire system.

**Key Features:**
- Validates tool-agent relationships
- Provides comprehensive health checks
- Manages API key validation
- Offers detailed system summaries

**Usage:**
```python
from backend.registry.manager import get_registry_manager

registry_manager = get_registry_manager()
health_check = registry_manager.get_health_check()
system_summary = registry_manager.get_system_summary()
```

### 2. Tool Registry (`backend/tools/registry.py`)

The **Tool Registry** manages all tools using YAML configuration as the single source of truth.

**Key Features:**
- Loads tools from `backend/config/tools.yaml`
- Validates API key requirements
- Tracks tool usage and performance
- Provides tool availability status

**Configuration Source:** `backend/config/tools.yaml`

### 3. Agent Registry (`backend/agents/registry.py`)

The **Agent Registry** manages all agents using YAML configuration as the single source of truth.

**Key Features:**
- Loads agents from `backend/config/agents.yaml`
- Validates agent-tool dependencies
- Tracks agent capabilities
- Provides agent availability status

**Configuration Source:** `backend/config/agents.yaml`

## Configuration Files

### Tools Configuration (`backend/config/tools.yaml`)

```yaml
tools:
  get_market_data:
    name: "get_market_data"
    description: "Get real-time market data for a stock ticker"
    category: "market_data"
    function: "get_market_data"
    class: "MarketDataTool"
    api_key_required: "alpha_vantage"
    enabled: true
    examples:
      - "get_market_data(ticker='AAPL')"
    dependencies: []
    retry_config:
      max_retries: 3
      backoff_factor: 2
```

### Agents Configuration (`backend/config/agents.yaml`)

```yaml
agents:
  FinancialAnalyst:
    name: "FinancialAnalyst"
    instructions: |
      You are a Financial Analyst Coordinator...
    tools: 
      - "detect_stock_ticker"
      - "get_market_data"
      - "get_company_overview"
    capabilities:
      - "market_analysis"
      - "economic_analysis"
      - "risk_assessment"
    required: true
    enabled: true
```

## API Endpoints

### Registry Health and Status

- `GET /api/registry/health` - Comprehensive health check
- `GET /api/registry/status` - Detailed registry status
- `GET /api/registry/validation` - Validation results
- `GET /api/registry/summary` - System summary

### Agent Management

- `GET /api/agents` - All available agents
- `GET /api/registry/agents/<agent_name>` - Specific agent details
- `GET /api/registry/capabilities` - All capabilities

### Tool Management

- `GET /api/registry/tools` - All available tools
- `GET /api/registry/tools/<tool_name>` - Specific tool details

## Validation System

### Tool Validation

The system validates:
- Tool function availability
- API key requirements
- Tool dependencies
- Tool callability

### Agent Validation

The system validates:
- Agent configuration
- Tool dependencies
- Required agents availability
- Agent capabilities

### Cross-Validation

The system validates:
- Agent-tool relationships
- API key availability for tools
- Required agent availability
- Configuration consistency

## Usage Examples

### Getting System Health

```python
from backend.registry.manager import get_registry_manager

registry_manager = get_registry_manager()
health = registry_manager.get_health_check()

if health["status"] == "healthy":
    print("System is healthy")
else:
    print(f"System issues: {health['validation']['errors']}")
```

### Validating Agent Tools

```python
agent_name = "FinancialAnalyst"
tool_validation = registry_manager.validate_agent_tools(agent_name)

for tool, status in tool_validation.items():
    if status != "available":
        print(f"Tool {tool} has status: {status}")
```

### Getting Agent Information

```python
agent_info = registry_manager.get_agent_info("FinancialAnalyst")
print(f"Agent tools: {agent_info['tools']}")
print(f"Agent capabilities: {agent_info['capabilities']}")
print(f"Validation status: {agent_info['validation_status']}")
```

## Error Handling

### Validation Errors

The system provides detailed error messages for:
- Missing tools
- Missing API keys
- Invalid configurations
- Disabled required agents

### Fallback Mechanisms

- Tools with missing API keys are marked as unavailable
- Agents with missing tools are marked as invalid
- Required agents that are disabled cause system errors
- Optional agents can be disabled without affecting the system

## Monitoring and Analytics

### Tool Usage Tracking

```python
# Track tool usage with execution time
tool_registry.track_usage("get_market_data", success=True, execution_time=1.5)

# Get usage statistics
stats = tool_registry.get_usage_stats()
print(f"Tool invocations: {stats['get_market_data']['invocations']}")
```

### Agent Usage Tracking

```python
# Track agent usage
workflow_status['agent_usage'].append({
    'agent': 'FinancialAnalyst',
    'task': 'market_analysis',
    'status': 'completed',
    'timestamp': datetime.now().isoformat()
})
```

## Best Practices

### Configuration Management

1. **Single Source of Truth**: Always use YAML files for configuration
2. **Validation**: Validate configurations before deployment
3. **Documentation**: Document all tools and agents in configuration files
4. **Version Control**: Keep configuration files in version control

### Error Handling

1. **Graceful Degradation**: Handle missing tools/agents gracefully
2. **Validation**: Always validate before using tools/agents
3. **Logging**: Log validation errors and warnings
4. **Monitoring**: Monitor system health regularly

### Development Workflow

1. **Add Tools**: Add tool definitions to `tools.yaml`
2. **Add Agents**: Add agent definitions to `agents.yaml`
3. **Validate**: Run validation to check configuration
4. **Test**: Test tools and agents individually
5. **Deploy**: Deploy with confidence in configuration

## Troubleshooting

### Common Issues

1. **Missing API Keys**
   - Check API key configuration in settings
   - Verify API key environment variables
   - Check tool API key requirements

2. **Missing Tools**
   - Verify tool function exists in `builtin_tools.py`
   - Check tool configuration in `tools.yaml`
   - Validate tool dependencies

3. **Agent Validation Failures**
   - Check agent configuration in `agents.yaml`
   - Verify agent tools are available
   - Check agent capabilities

4. **Configuration Errors**
   - Validate YAML syntax
   - Check required fields in configuration
   - Verify file paths and permissions

### Debugging Commands

```python
# Get comprehensive system status
registry_manager = get_registry_manager()
status = registry_manager.get_validation_status()
print(f"Valid: {status.valid}")
print(f"Errors: {status.errors}")
print(f"Warnings: {status.warnings}")

# Check specific agent
agent_info = registry_manager.get_agent_info("FinancialAnalyst")
print(f"Agent validation: {agent_info['validation_status']}")

# Check specific tool
tool_info = registry_manager.get_tool_info("get_market_data")
print(f"Tool status: {tool_info}")
```

## Migration Guide

### From Old System

1. **Update Imports**: Use registry manager instead of direct imports
2. **Configuration**: Move configurations to YAML files
3. **Validation**: Add validation checks in code
4. **Error Handling**: Implement graceful error handling
5. **Testing**: Test with new validation system

### Configuration Migration

1. **Tools**: Move tool definitions to `tools.yaml`
2. **Agents**: Move agent definitions to `agents.yaml`
3. **Settings**: Update settings to use new validation
4. **Workflows**: Update workflows to use registry manager

## Future Enhancements

### Planned Features

1. **Dynamic Configuration**: Hot-reload configuration changes
2. **Advanced Validation**: More sophisticated validation rules
3. **Performance Monitoring**: Enhanced performance tracking
4. **Configuration UI**: Web-based configuration management
5. **Plugin System**: Support for external tool/agent plugins

### Extension Points

1. **Custom Validators**: Add custom validation rules
2. **Custom Trackers**: Add custom usage tracking
3. **Custom Providers**: Add custom tool/agent providers
4. **Custom Formats**: Support additional configuration formats

## Conclusion

The Single Source of Truth architecture provides a robust, maintainable, and extensible foundation for the Fintel v2 system. By centralizing configuration management and providing comprehensive validation, the system is more reliable and easier to maintain.

For questions or issues, refer to the validation endpoints or check the system logs for detailed error information. 