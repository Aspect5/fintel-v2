import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import SpinnerIcon from '../icons/SpinnerIcon';
import CheckCircleIcon from '../icons/CheckCircleIcon';
import XCircleIcon from '../icons-solid/XCircleIcon';

interface TaskNodeData {
  label: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  agent?: string;
  description?: string;
  result?: string;
  error?: string;
}

const TaskNode: React.FC<NodeProps<TaskNodeData>> = ({ data }) => {
  const { label, status, agent, description, result, error } = data;
  
  const getStatusIcon = () => {
    switch (status) {
      case 'running':
        return <SpinnerIcon className="w-5 h-5 text-brand-primary animate-spin" />;
      case 'completed':
        return <CheckCircleIcon className="w-5 h-5 text-brand-success" />;
      case 'failed':
        return <XCircleIcon className="w-5 h-5 text-brand-danger" />;
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
      case 'running':
        return 'border-brand-primary';
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
      case 'running':
        return 'bg-blue-900/20';
      default:
        return 'bg-brand-surface';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'running':
        return 'Running...';
      case 'completed':
        return 'Completed';
      case 'failed':
        return 'Failed';
      case 'pending':
        return 'Pending';
      default:
        return 'Ready';
    }
  };

  return (
    <div className={`relative p-4 border-2 rounded-lg shadow-lg min-w-[200px] max-w-[280px] ${getBorderColor()} ${getBackgroundColor()} transition-all duration-300 cursor-pointer hover:shadow-xl hover:scale-105 group`}>
      <Handle 
        type="target" 
        position={Position.Left} 
        className="!bg-brand-secondary !w-3 !h-3 !border-2 !border-brand-bg" 
        style={{ left: '-8px' }}
      />
      
      <div className="flex items-center justify-between mb-3">
        <div className="font-bold text-lg text-white">{label}</div>
        {getStatusIcon()}
      </div>
      
      {/* Status indicator */}
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-brand-text-secondary">{getStatusText()}</span>
      </div>
      
      {/* Agent name if available */}
      {agent && (
        <div className="mb-2">
          <div className="text-xs text-brand-text-secondary opacity-75">Agent</div>
          <div className="text-sm text-white font-medium">{agent}</div>
        </div>
      )}
      
      {/* Description if available */}
      {description && (
        <div className="mb-2">
          <div className="text-xs text-brand-text-secondary opacity-75">Description</div>
          <div className="text-sm text-white">{description}</div>
        </div>
      )}
      
      {/* Result preview if completed */}
      {status === 'completed' && result && (
        <div className="mt-2 p-2 bg-green-900/30 rounded border border-green-700/50">
          <div className="text-xs text-green-300 mb-1">Result</div>
          <div className="text-xs text-green-200 line-clamp-2">{result}</div>
        </div>
      )}
      
      {/* Error message if failed */}
      {status === 'failed' && error && (
        <div className="mt-2 p-2 bg-red-900/30 rounded border border-red-700/50">
          <div className="text-xs text-red-300 mb-1">Error</div>
          <div className="text-xs text-red-200 line-clamp-2">{error}</div>
        </div>
      )}
      
      <Handle 
        type="source" 
        position={Position.Right} 
        className="!bg-brand-secondary !w-3 !h-3 !border-2 !border-brand-bg" 
        style={{ right: '-8px' }}
      />
    </div>
  );
};

export default TaskNode; 