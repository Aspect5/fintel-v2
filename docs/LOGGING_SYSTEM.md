# Fintel Logging System

This document describes the comprehensive logging system implemented in the Fintel application for both frontend and backend components.

## Overview

The logging system provides structured logging with multiple output destinations, log levels, and filtering capabilities to help with debugging and monitoring the application.

## Frontend Logging

### Features

- **Structured Logging**: All logs include timestamp, component name, log level, and message
- **Multiple Log Levels**: DEBUG, INFO, WARN, ERROR, CRITICAL
- **Component-Specific Loggers**: Each component can have its own logger instance
- **File Output**: Logs can be exported to files for analysis
- **Real-time Log Viewer**: Built-in log viewer component for development
- **Log Buffering**: In-memory log buffer with configurable size

### Usage

#### Basic Logging

```typescript
import { createLogger } from '../utils/logger';

// Create a component-specific logger
const logger = createLogger('MyComponent');

// Log at different levels
logger.debug('Debug message', { data: 'debug info' });
logger.info('Info message', { data: 'info' });
logger.warn('Warning message', { data: 'warning' });
logger.error('Error message', { data: 'error' }, error);
logger.critical('Critical error', { data: 'critical' }, error);
```

#### Direct Logging Functions

```typescript
import { debug, info, warn, error, critical } from '../utils/logger';

debug('MyComponent', 'Debug message', { data: 'debug info' });
info('MyComponent', 'Info message', { data: 'info' });
warn('MyComponent', 'Warning message', { data: 'warning' });
error('MyComponent', 'Error message', { data: 'error' }, error);
critical('MyComponent', 'Critical error', { data: 'critical' }, error);
```

#### Log Viewer Component

The LogViewer component provides a real-time interface for viewing and filtering logs:

```typescript
import LogViewer from './src/components/LogViewer';

// In your component
const [isLogViewerVisible, setIsLogViewerVisible] = useState(false);

// In your JSX
<LogViewer 
  isVisible={isLogViewerVisible}
  onClose={() => setIsLogViewerVisible(false)}
/>
```

### Features of Log Viewer

- **Real-time Updates**: Logs update automatically every second
- **Level Filtering**: Filter logs by log level (DEBUG, INFO, WARN, ERROR, CRITICAL)
- **Component Filtering**: Filter logs by component name
- **Auto-scroll**: Automatically scroll to latest logs
- **Export**: Download logs as text file
- **Clear**: Clear the log buffer

### Configuration

```typescript
import { logger, LogLevel } from '../utils/logger';

// Set log level (only logs at or above this level will be shown)
logger.setLogLevel(LogLevel.DEBUG);

// Get current log level
const currentLevel = logger.getLogLevel();

// Get log buffer
const logs = logger.getLogBuffer();

// Clear log buffer
logger.clearLogBuffer();

// Export logs as text
const logText = logger.exportLogs();
```

## Backend Logging

### Features

- **Dual Output**: Logs to both console and file
- **Timestamped Files**: Each run creates a new log file with timestamp
- **Structured Format**: Includes function name and line number in file logs
- **Configurable Levels**: Set via settings
- **Noise Suppression**: Automatically suppresses noisy third-party loggers

### Log File Location

Backend logs are stored in the `logs/` directory with the format:
```
logs/fintel-backend_YYYYMMDD_HHMMSS.log
```

### Usage

```python
import logging

logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical error")
```

### Configuration

The logging level is configured in the settings:

```python
# In backend/config/settings.py
log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

## Log Levels

### DEBUG (0)
- Detailed information for debugging
- Used for tracing execution flow
- Includes data structures and state information

### INFO (1)
- General information about application state
- Used for tracking normal operations
- Includes workflow progress, data updates

### WARN (2)
- Warning messages for potential issues
- Used for recoverable problems
- Includes deprecated features, performance warnings

### ERROR (3)
- Error messages for failed operations
- Used for non-fatal errors
- Includes API failures, data processing errors

### CRITICAL (4)
- Critical error messages
- Used for fatal errors that may crash the application
- Includes system failures, security issues

## Best Practices

### Frontend Logging

1. **Use Component-Specific Loggers**: Create a logger for each component
2. **Include Relevant Data**: Pass objects and data for context
3. **Use Appropriate Levels**: Don't log everything as INFO
4. **Handle Errors Properly**: Always include error objects in error logs
5. **Avoid Sensitive Data**: Don't log API keys, passwords, or personal information

### Backend Logging

1. **Use Descriptive Messages**: Make logs meaningful and searchable
2. **Include Context**: Log relevant data for debugging
3. **Handle Exceptions**: Always log exceptions with full stack traces
4. **Use Structured Data**: Consider using JSON format for complex data
5. **Monitor Log Size**: Rotate logs to prevent disk space issues

## Debugging Workflow Issues

### Common Log Patterns

1. **Workflow Start**: Look for "Starting workflow" logs
2. **Node/Edge Processing**: Check for layout and edge processing logs
3. **API Responses**: Monitor backend data structure logs
4. **Polling Issues**: Check for 404 errors and polling cleanup
5. **State Updates**: Track workflow status updates

### Troubleshooting Steps

1. **Enable DEBUG Logging**: Set log level to DEBUG for maximum detail
2. **Filter by Component**: Use the log viewer to filter by specific components
3. **Check File Logs**: Review backend log files for server-side issues
4. **Export Logs**: Download logs for offline analysis
5. **Monitor Real-time**: Use the log viewer during development

## Integration with Development Workflow

### Development Mode

- Log level defaults to INFO
- Log viewer accessible via "View Logs" button
- Real-time log updates enabled

### Production Mode

- Log level should be set to WARN or ERROR
- File logging enabled for backend
- Log viewer can be disabled

### Testing

- Logs can be captured and analyzed during tests
- Use log buffer for assertions
- Export logs for test reports

## Future Enhancements

1. **Remote Logging**: Send logs to external services (Sentry, LogRocket)
2. **Log Analytics**: Add log analysis and metrics
3. **Performance Monitoring**: Track performance metrics in logs
4. **Alerting**: Set up alerts for critical errors
5. **Log Rotation**: Implement automatic log rotation and cleanup 