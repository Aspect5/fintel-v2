import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import CheckCircleIcon from '../icons/CheckCircleIcon';
import XCircleIcon from '../icons-solid/XCircleIcon';

interface OutputNodeData {
  label: string;
  status: 'pending' | 'completed' | 'failed';
  result?: any;
  error?: string;
  ticker?: string;
  confidence?: number;
  sentiment?: string;
}

const OutputNode: React.FC<NodeProps<OutputNodeData>> = ({ data }) => {
  const { label, status, result, error, ticker, confidence, sentiment } = data;
  
  const getStatusIcon = () => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="w-6 h-6 text-brand-success" />;
      case 'failed':
        return <XCircleIcon className="w-6 h-6 text-brand-danger" />;
      default:
        return null;
    }
  };

  const getBorderColor = () => {
    switch (status) {
      case 'failed':
        return 'border-brand-danger';
      case 'completed':
        return 'border-brand-success';
      default:
        return 'border-brand-border';
    }
  };

  const getBackgroundColor = () => {
    switch (status) {
      case 'failed':
        return 'bg-red-900/20';
      case 'completed':
        return 'bg-green-900/20';
      default:
        return 'bg-brand-surface';
    }
  };

  const getSentimentColor = (sentiment?: string) => {
    switch (sentiment?.toLowerCase()) {
      case 'positive':
        return 'text-green-400';
      case 'negative':
        return 'text-red-400';
      case 'neutral':
        return 'text-yellow-400';
      default:
        return 'text-brand-text-secondary';
    }
  };

  const getConfidenceColor = (confidence?: number) => {
    if (!confidence) return 'text-brand-text-secondary';
    if (confidence >= 0.8) return 'text-green-400';
    if (confidence >= 0.6) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <div className={`relative p-6 border-2 rounded-lg shadow-lg min-w-[250px] max-w-[350px] ${getBorderColor()} ${getBackgroundColor()} transition-all duration-300 cursor-pointer hover:shadow-xl hover:scale-105 group`}>
      <Handle 
        type="target" 
        position={Position.Left} 
        className="!bg-brand-secondary !w-3 !h-3 !border-2 !border-brand-bg" 
        style={{ left: '-8px' }}
      />
      
      <div className="flex items-center justify-between mb-4">
        <div className="font-bold text-xl text-white">{label}</div>
        {getStatusIcon()}
      </div>
      
      {/* Status indicator */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm text-brand-text-secondary">
          {status === 'completed' ? 'Analysis Complete' : 
           status === 'failed' ? 'Analysis Failed' : 'Processing...'}
        </span>
      </div>
      
      {/* Ticker and key metrics if completed */}
      {status === 'completed' && result && (
        <div className="space-y-3">
          {ticker && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-brand-text-secondary">Ticker</span>
              <span className="text-lg font-bold text-white">{ticker}</span>
            </div>
          )}
          
          {sentiment && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-brand-text-secondary">Sentiment</span>
              <span className={`text-sm font-medium ${getSentimentColor(sentiment)}`}>
                {sentiment.charAt(0).toUpperCase() + sentiment.slice(1)}
              </span>
            </div>
          )}
          
          {confidence !== undefined && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-brand-text-secondary">Confidence</span>
              <span className={`text-sm font-medium ${getConfidenceColor(confidence)}`}>
                {Math.round(confidence * 100)}%
              </span>
            </div>
          )}
          
          {/* Result preview */}
          <div className="mt-3 p-3 bg-green-900/30 rounded border border-green-700/50">
            <div className="text-xs text-green-300 mb-2">Analysis Result</div>
            <div className="text-sm text-green-200 line-clamp-3">
              {typeof result === 'string' ? result : 
               result.recommendation || result.market_analysis || 'Analysis completed successfully'}
            </div>
          </div>
        </div>
      )}
      
      {/* Error message if failed */}
      {status === 'failed' && error && (
        <div className="mt-3 p-3 bg-red-900/30 rounded border border-red-700/50">
          <div className="text-xs text-red-300 mb-2">Error</div>
          <div className="text-sm text-red-200 line-clamp-3">{error}</div>
        </div>
      )}
      
      {/* Pending state */}
      {status === 'pending' && (
        <div className="mt-3 p-3 bg-brand-surface/50 rounded border border-brand-border">
          <div className="text-sm text-brand-text-secondary">
            Waiting for analysis to complete...
          </div>
        </div>
      )}
    </div>
  );
};

export default OutputNode; 