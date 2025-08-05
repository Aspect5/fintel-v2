// frontend/src/components/workflow/TaskNode.tsx
import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { CustomNodeData } from '../../types';

import SpinnerIcon from '../icons/SpinnerIcon';
import CheckCircleIcon from '../icons/CheckCircleIcon';
import XCircleIcon from '../icons-solid/XCircleIcon';
import CodeBracketIcon from '../icons/CodeBracketIcon';
import SparklesIcon from '../icons/SparklesIcon';

const TaskNode: React.FC<NodeProps<CustomNodeData>> = ({ data }) => {
  const { label, status, description, agentName, tools, liveDetails } = data;

  const getStatusIcon = () => {
    switch (status) {
      case 'running': return <SpinnerIcon className="w-5 h-5 text-blue-500 animate-spin" />;
      case 'completed': return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'failed': return <XCircleIcon className="w-5 h-5 text-red-500" />;
      default: return <div className="w-5 h-5" />;
    }
  };

  const getBorderColor = () => {
    if (status === 'failed') return 'border-red-500/80 shadow-red-500/20';
    if (status === 'completed') return 'border-green-500/80 shadow-green-500/20';
    if (status === 'running') return 'border-blue-500/80 shadow-blue-500/20';
    return 'border-gray-600/80 shadow-gray-900/20';
  };

  return (
    <div className={`relative bg-gray-800 border rounded-lg shadow-lg min-w-[280px] max-w-[320px] transition-all duration-300 ${getBorderColor()} hover:shadow-xl`}>
      <Handle type="target" position={Position.Left} className="!bg-gray-500 !w-3 !h-3 !border-2 !border-gray-800" />
      
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <div className="font-bold text-lg text-white">{label}</div>
          {getStatusIcon()}
        </div>
        <p className="text-sm text-gray-400 mt-1">{description}</p>
      </div>

      <div className="p-4 space-y-3">
        {agentName && (
          <div className="flex items-center space-x-2 text-sm">
            <SparklesIcon className="w-4 h-4 text-yellow-400" />
            <span className="text-gray-300 font-semibold">Agent:</span>
            <span className="text-gray-400">{agentName}</span>
          </div>
        )}
        
        {tools && tools.length > 0 && (
          <div className="flex items-start space-x-2 text-sm">
            <CodeBracketIcon className="w-4 h-4 text-cyan-400 mt-0.5" />
            <div>
              <span className="text-gray-300 font-semibold">Tools:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {tools.map((tool, index) => (
                  <span key={index} className="bg-gray-700 text-gray-300 text-xs px-2 py-0.5 rounded-full">{tool}</span>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {status === 'running' && liveDetails && (
        <div className="bg-gray-800/50 p-4 border-t border-gray-700">
          <h4 className="text-sm font-semibold text-white mb-2">Live Details</h4>
          <div className="space-y-3 text-xs">
            {liveDetails.agent_reasoning && (
              <div>
                <strong className="text-gray-400">Reasoning:</strong>
                <p className="text-gray-500 bg-gray-900 p-2 rounded mt-1 font-mono">{liveDetails.agent_reasoning}</p>
              </div>
            )}
            {liveDetails.tool_calls && liveDetails.tool_calls.length > 0 && (
               <div>
                 <strong className="text-gray-400">Recent Tool Calls:</strong>
                 <ul className="list-disc list-inside mt-1 space-y-1">
                   {liveDetails.tool_calls.map((call, i) => (
                     <li key={i} className="text-gray-500 font-mono text-xs truncate">
                       {call.tool_name}({JSON.stringify(call.tool_args || {})})
                     </li>
                   ))}
                 </ul>
               </div>
            )}
          </div>
        </div>
      )}

      <Handle type="source" position={Position.Right} className="!bg-gray-500 !w-3 !h-3 !border-2 !border-gray-800" />
    </div>
  );
};

export default TaskNode;
