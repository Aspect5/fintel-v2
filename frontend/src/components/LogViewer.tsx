// frontend/src/components/LogViewer.tsx
import React, { useState, useEffect, useRef } from 'react';
import { logger, LogLevel, LogEntry } from '../utils/logger';

interface LogViewerProps {
  isVisible: boolean;
  onClose: () => void;
}

const LogViewer: React.FC<LogViewerProps> = ({ isVisible, onClose }) => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [filterLevel, setFilterLevel] = useState<LogLevel>(LogLevel.DEBUG);
  const [filterComponent, setFilterComponent] = useState<string>('');
  const [autoScroll, setAutoScroll] = useState(true);
  const logContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isVisible) return;

    const updateLogs = () => {
      setLogs(logger.getLogBuffer());
    };

    // Update logs immediately
    updateLogs();

    // Set up interval to update logs
    const interval = setInterval(updateLogs, 1000);

    return () => clearInterval(interval);
  }, [isVisible]);

  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  const filteredLogs = logs.filter(log => {
    const levelMatch = log.level >= filterLevel;
    const componentMatch = !filterComponent || log.component.toLowerCase().includes(filterComponent.toLowerCase());
    return levelMatch && componentMatch;
  });

  const getLevelColor = (level: LogLevel): string => {
    switch (level) {
      case LogLevel.DEBUG: return 'text-gray-500';
      case LogLevel.INFO: return 'text-blue-500';
      case LogLevel.WARN: return 'text-yellow-500';
      case LogLevel.ERROR: return 'text-red-500';
      case LogLevel.CRITICAL: return 'text-red-700 font-bold';
      default: return 'text-gray-300';
    }
  };

  const exportLogs = () => {
    const logText = logger.exportLogs();
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `fintel-logs-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.log`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const clearLogs = () => {
    logger.clearLogBuffer();
    setLogs([]);
  };

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-brand-surface border border-brand-border rounded-lg shadow-xl w-11/12 h-5/6 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-brand-border">
          <h2 className="text-xl font-semibold text-white">Log Viewer</h2>
          <div className="flex items-center space-x-2">
            <button
              onClick={exportLogs}
              className="px-3 py-1 bg-brand-primary text-white rounded hover:bg-brand-primary-dark"
            >
              Export
            </button>
            <button
              onClick={clearLogs}
              className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700"
            >
              Clear
            </button>
            <button
              onClick={onClose}
              className="px-3 py-1 bg-brand-secondary text-white rounded hover:bg-brand-secondary-dark"
            >
              Close
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center space-x-4 p-4 border-b border-brand-border bg-brand-bg">
          <div className="flex items-center space-x-2">
            <label className="text-white text-sm">Level:</label>
            <select
              value={filterLevel}
              onChange={(e) => setFilterLevel(Number(e.target.value))}
              className="bg-brand-surface border border-brand-border text-white rounded px-2 py-1 text-sm"
            >
              <option value={LogLevel.DEBUG}>DEBUG</option>
              <option value={LogLevel.INFO}>INFO</option>
              <option value={LogLevel.WARN}>WARN</option>
              <option value={LogLevel.ERROR}>ERROR</option>
              <option value={LogLevel.CRITICAL}>CRITICAL</option>
            </select>
          </div>
          
          <div className="flex items-center space-x-2">
            <label className="text-white text-sm">Component:</label>
            <input
              type="text"
              value={filterComponent}
              onChange={(e) => setFilterComponent(e.target.value)}
              placeholder="Filter by component..."
              className="bg-brand-surface border border-brand-border text-white rounded px-2 py-1 text-sm w-40"
            />
          </div>

          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="autoScroll"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
              className="rounded"
            />
            <label htmlFor="autoScroll" className="text-white text-sm">Auto-scroll</label>
          </div>

          <div className="text-white text-sm">
            Showing {filteredLogs.length} of {logs.length} logs
          </div>
        </div>

        {/* Logs */}
        <div 
          ref={logContainerRef}
          className="flex-1 overflow-y-auto p-4 bg-brand-bg font-mono text-sm"
        >
          {filteredLogs.length === 0 ? (
            <div className="text-brand-text-secondary text-center py-8">
              No logs to display
            </div>
          ) : (
            filteredLogs.map((log, index) => (
              <div key={index} className="mb-1">
                <span className="text-brand-text-tertiary">[{log.timestamp}]</span>
                <span className={`ml-2 ${getLevelColor(log.level)}`}>
                  [{LogLevel[log.level]}]
                </span>
                <span className="text-brand-text-secondary ml-2">[{log.component}]</span>
                <span className="text-white ml-2">{log.message}</span>
                {log.data && (
                  <div className="ml-8 mt-1 text-brand-text-secondary">
                    <pre className="whitespace-pre-wrap text-xs">
                      {JSON.stringify(log.data, null, 2)}
                    </pre>
                  </div>
                )}
                {log.error && (
                  <div className="ml-8 mt-1 text-red-400">
                    <pre className="whitespace-pre-wrap text-xs">
                      {log.error.stack || log.error.message}
                    </pre>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default LogViewer; 