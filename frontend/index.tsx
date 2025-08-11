
import React from 'react';
import ReactDOM from 'react-dom/client';
import './src/index.css';
import App from './App';
import { logger, LogLevel } from './src/utils/logger';

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error("Could not find root element to mount to");
}

const root = ReactDOM.createRoot(rootElement);

// Ensure frontend logs are captured at DEBUG by default so the Log Viewer shows activity
try {
  logger.setLogLevel(LogLevel.DEBUG);
} catch {}

// In dev, StrictMode double-invokes render; offer a one-liner switch for debugging duplicate UI
const useStrict = false;
const AppTree = useStrict ? (
  <React.StrictMode>
    <App />
  </React.StrictMode>
) : (
  <App />
);

root.render(AppTree);
