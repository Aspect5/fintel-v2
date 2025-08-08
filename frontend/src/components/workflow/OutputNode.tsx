// frontend/src/components/workflow/OutputNode.tsx
import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { CustomNodeData } from '../../types';

import CheckCircleIcon from '../icons/CheckCircleIcon';
import DocumentTextIcon from '../icons/DocumentTextIcon';

const OutputNode: React.FC<NodeProps<CustomNodeData>> = ({ data }) => {
  const { label, status, result } = data;

  const getBorderColor = () => {
    if (status === 'completed') return 'border-green-500/80 shadow-green-500/20';
    return 'border-gray-600/80 shadow-gray-900/20';
  };
  
  const isCompleted = status === 'completed' && result;

  return (
    <div className={`relative bg-gray-800 border rounded-lg shadow-lg min-w-[280px] max-w-[320px] transition-all duration-300 ${getBorderColor()} hover:shadow-xl mx-2`}>
      <Handle type="target" position={Position.Left} className="!bg-gray-500 !w-3 !h-3 !border-2 !border-gray-800" />
      
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <div className="font-bold text-lg text-white">{label}</div>
          {isCompleted ? <CheckCircleIcon className="w-5 h-5 text-green-500" /> : <DocumentTextIcon className="w-5 h-5 text-gray-400" />}
        </div>
        <p className="text-sm text-gray-400 mt-1">
          {isCompleted ? 'Workflow finished. Final report is available.' : 'Awaiting final analysis...'}
        </p>
      </div>

      {isCompleted && (
        <div className="p-4 text-xs space-y-2">
          <div className="flex justify-between">
            <span className="text-gray-400 font-semibold">Recommendation:</span>
            <span className="text-white font-bold px-2 py-0.5 rounded-full bg-blue-500/30">{result.recommendation}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400 font-semibold">Confidence:</span>
            <span className="text-white">{Math.round(result.confidence * 100)}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400 font-semibold">Sentiment:</span>
            <span className="text-white capitalize">{result.sentiment}</span>
          </div>
        </div>
      )}

    </div>
  );
};

export default OutputNode;
