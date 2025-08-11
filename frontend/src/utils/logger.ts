// frontend/src/utils/logger.ts
/**
 * Frontend logging utility with file and console output
 * Provides structured logging with different levels and component-specific logging
 */

export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3,
  CRITICAL = 4
}

export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  component: string;
  message: string;
  data?: any;
  error?: Error;
}

class Logger {
  private logLevel: LogLevel = LogLevel.INFO;
  private logBuffer: LogEntry[] = [];
  private maxBufferSize = 1000;
  private isFileLoggingEnabled = false;
  private logFileName = 'fintel-frontend.log';

  constructor() {
    // File logging is disabled by default to avoid noisy downloads.
    // Enable explicitly by setting window.__ENABLE_FRONTEND_FILE_LOGGING__ = true
    this.setupFileLogging();
  }

  private setupFileLogging(): void {
    // Only enable if explicitly opted in via global flag
    if (typeof window !== 'undefined' && (window as any).__ENABLE_FRONTEND_FILE_LOGGING__ && 'showSaveFilePicker' in window) {
      this.isFileLoggingEnabled = true;
    }
  }

  private getTimestamp(): string {
    return new Date().toISOString();
  }

  private formatLogEntry(entry: LogEntry): string {
    const levelStr = LogLevel[entry.level];
    const dataStr = entry.data ? ` | Data: ${JSON.stringify(entry.data, null, 2)}` : '';
    const errorStr = entry.error ? ` | Error: ${entry.error.message}\n${entry.error.stack}` : '';
    
    return `[${entry.timestamp}] [${levelStr}] [${entry.component}] ${entry.message}${dataStr}${errorStr}`;
  }

  private addToBuffer(entry: LogEntry): void {
    this.logBuffer.push(entry);
    
    // Keep buffer size manageable
    if (this.logBuffer.length > this.maxBufferSize) {
      this.logBuffer = this.logBuffer.slice(-this.maxBufferSize);
    }
  }

  private async writeToFile(logContent: string): Promise<void> {
    if (!this.isFileLoggingEnabled) return;

    try {
      // Create a blob with the log content
      const blob = new Blob([logContent + '\n'], { type: 'text/plain' });
      
      // Try to append to existing file or create new one
      // Note: This is a simplified approach - in a real app you might want to use
      // the File System Access API or send logs to a backend endpoint
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = this.logFileName;
      a.style.display = 'none';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to write log to file:', error);
    }
  }

  private log(level: LogLevel, component: string, message: string, data?: any, error?: Error): void {
    if (level < this.logLevel) return;

    const entry: LogEntry = {
      timestamp: this.getTimestamp(),
      level,
      component,
      message,
      data,
      error
    };

    // Add to buffer
    this.addToBuffer(entry);

    // Format for output
    const formattedLog = this.formatLogEntry(entry);

    // Console output with appropriate styling
    switch (level) {
      case LogLevel.DEBUG:
        console.debug(`%c${formattedLog}`, 'color: #6c757d');
        break;
      case LogLevel.INFO:
        console.info(`%c${formattedLog}`, 'color: #0d6efd');
        break;
      case LogLevel.WARN:
        console.warn(`%c${formattedLog}`, 'color: #ffc107');
        break;
      case LogLevel.ERROR:
        console.error(`%c${formattedLog}`, 'color: #dc3545');
        break;
      case LogLevel.CRITICAL:
        console.error(`%c${formattedLog}`, 'color: #dc3545; font-weight: bold;');
        break;
    }

    // Write to file in background
    this.writeToFile(formattedLog);
  }

  // Public logging methods
  debug(component: string, message: string, data?: any): void {
    this.log(LogLevel.DEBUG, component, message, data);
  }

  info(component: string, message: string, data?: any): void {
    this.log(LogLevel.INFO, component, message, data);
  }

  warn(component: string, message: string, data?: any): void {
    this.log(LogLevel.WARN, component, message, data);
  }

  error(component: string, message: string, data?: any, error?: Error): void {
    this.log(LogLevel.ERROR, component, message, data, error);
  }

  critical(component: string, message: string, data?: any, error?: Error): void {
    this.log(LogLevel.CRITICAL, component, message, data, error);
  }

  // Configuration methods
  setLogLevel(level: LogLevel): void {
    this.logLevel = level;
  }

  getLogLevel(): LogLevel {
    return this.logLevel;
  }

  // Utility methods
  getLogBuffer(): LogEntry[] {
    return [...this.logBuffer];
  }

  clearLogBuffer(): void {
    this.logBuffer = [];
  }

  exportLogs(): string {
    return this.logBuffer.map(entry => this.formatLogEntry(entry)).join('\n');
  }

  // Component-specific logger factory
  forComponent(componentName: string) {
    return {
      debug: (message: string, data?: any) => this.debug(componentName, message, data),
      info: (message: string, data?: any) => this.info(componentName, message, data),
      warn: (message: string, data?: any) => this.warn(componentName, message, data),
      error: (message: string, data?: any, error?: Error) => this.error(componentName, message, data, error),
      critical: (message: string, data?: any, error?: Error) => this.critical(componentName, message, data, error),
    };
  }
}

// Create singleton instance
export const logger = new Logger();

// Export convenience functions
export const debug = (component: string, message: string, data?: any) => logger.debug(component, message, data);
export const info = (component: string, message: string, data?: any) => logger.info(component, message, data);
export const warn = (component: string, message: string, data?: any) => logger.warn(component, message, data);
export const error = (component: string, message: string, data?: any, error?: Error) => logger.error(component, message, data, error);
export const critical = (component: string, message: string, data?: any, error?: Error) => logger.critical(component, message, data, error);

// Export component logger factory
export const createLogger = (componentName: string) => logger.forComponent(componentName); 