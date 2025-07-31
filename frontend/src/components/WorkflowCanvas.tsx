// components/WorkflowCanvas.tsx
import React, { useEffect, useMemo } from 'react';
import ReactFlow, { 
  Background, 
  Controls, 
  MiniMap, 
  Node, 
  Edge, 
  OnNodesChange, 
  OnEdgesChange, 
  Handle, 
  Position,
  ConnectionMode,
  ReactFlowProvider,
  useReactFlow,
  NodeProps
} from 'reactflow';
import 'reactflow/dist/style.css';

import SpinnerIcon from './icons/SpinnerIcon';
import CheckCircleIcon from './icons/CheckCircleIcon';
import XCircleIcon from './icons-solid/XCircleIcon';

// Custom node component with proper typing
const CustomNode: React.FC<NodeProps> = ({ data }) => {
  const { label, details, status, error, result } = data;
  
  const getStatusIcon = () => {
    switch (status) {
      case 'running':
        return <SpinnerIcon className="w-5 h-5 text-brand-primary animate-spin" />;
      case 'completed':
      case 'success':
        return <CheckCircleIcon className="w-5 h-5 text-brand-success" />;
      case 'failed':
      case 'failure':
        return <XCircleIcon className="w-5 h-5 text-brand-danger" />;
      default:
        return null;
    }
  };

  const getBorderColor = () => {
    if (status === 'failed' || status === 'failure') return 'border-brand-danger';
    if (status === 'completed' || status === 'success') return 'border-brand-success';
    if (status === 'running') return 'border-brand-primary';
    return 'border-brand-border';
  };

  const getStatusText = () => {
    switch (status) {
      case 'running':
        return 'Running...';
      case 'completed':
      case 'success':
        return 'Completed';
      case 'failed':
      case 'failure':
        return 'Failed';
      case 'pending':
        return 'Pending';
      default:
        return 'Ready';
    }
  };

  // Check if this is the User Query node
  const isUserQuery = label === 'User Query';
  
  // Get provider info from localStorage or default
  const getProviderInfo = () => {
    try {
      const stored = localStorage.getItem('fintel-app-storage');
      if (stored) {
        const data = JSON.parse(stored);
        return data.state?.controlFlowProvider || 'OpenAI';
      }
    } catch (e) {
      // Ignore errors
    }
    return 'OpenAI';
  };

  return (
    <div className={`relative p-4 bg-brand-surface border-2 rounded-lg shadow-lg min-w-[200px] max-w-[280px] ${getBorderColor()} transition-all duration-300 cursor-pointer hover:shadow-xl hover:scale-105 group`}>
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
      
      {/* Status indicator - only show for non-User Query nodes and non-completed nodes */}
      {!isUserQuery && (status !== 'completed' && status !== 'success') && (
        <div className="flex items-center justify-between mb-2">
          <span className={`text-xs px-2 py-1 rounded-full ${
            status === 'failed' || status === 'failure' ? 'bg-red-500/20 text-red-400' :
            status === 'running' ? 'bg-blue-500/20 text-blue-400' :
            'bg-gray-500/20 text-gray-400'
          }`}>
            {getStatusText()}
          </span>
          <span className="text-xs text-brand-text-secondary opacity-0 group-hover:opacity-100 transition-opacity">
            Double-click for details
          </span>
        </div>
      )}
      
      {/* Provider info for User Query node */}
      {isUserQuery && (
        <div className="mb-2">
          <span className="text-xs text-brand-text-secondary bg-brand-primary/20 px-2 py-1 rounded">
            Provider: {getProviderInfo()}
          </span>
        </div>
      )}
      
      {/* Details/Summary */}
      {details && (
        <div className="text-sm text-brand-text-secondary mb-2 line-clamp-2">
          {details.length > 80 ? `${details.substring(0, 80)}...` : details}
        </div>
      )}
      
      {/* Result preview - only for completed nodes that are not User Query */}
      {result && (status === 'completed' || status === 'success') && !isUserQuery && (
        <div className="text-xs text-green-400 bg-green-500/10 p-2 rounded border border-green-500/20">
          ✓ Complete
        </div>
      )}
      
      {error && (
        <div className="text-xs text-red-400 bg-red-500/10 p-2 rounded border border-red-500/20">
          ✗ {error.length > 50 ? `${error.substring(0, 50)}...` : error}
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

interface WorkflowCanvasProps {
  nodes: Node[];
  edges: Edge[];
  onNodesChange: OnNodesChange;
  onEdgesChange: OnEdgesChange;
  onNodeDoubleClick?: (event: React.MouseEvent, node: Node) => void;
}

const WorkflowCanvasContent: React.FC<WorkflowCanvasProps> = ({ 
  nodes, 
  edges, 
  onNodesChange, 
  onEdgesChange, 
  onNodeDoubleClick 
}) => {
  const { fitView } = useReactFlow();

  // Memoize node types to prevent React Flow warnings
  const nodeTypes = useMemo(() => ({
    default: CustomNode,
    input: CustomNode,
    output: CustomNode,
  }), []);

  useEffect(() => {
    try {
      if (nodes.length > 0) {
        setTimeout(() => {
          fitView({ padding: 0.2, duration: 800 });
        }, 100);
      }
    } catch (error) {
      console.error('Error fitting view:', error);
    }
  }, [nodes, fitView]);

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onNodeDoubleClick={onNodeDoubleClick}
      nodeTypes={nodeTypes}
      connectionMode={ConnectionMode.Loose}
      fitView
      className="bg-brand-bg"
      proOptions={{ hideAttribution: true }}
    >
      <Background gap={24} color="#30363D" />
      <Controls className="react-flow__controls-brand" />
      <MiniMap 
        nodeStrokeWidth={3} 
        zoomable 
        pannable 
        className="react-flow__minimap-brand" 
      />
    </ReactFlow>
  );
};

const WorkflowCanvas: React.FC<WorkflowCanvasProps> = (props) => {
  return (
    <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}>
      <ReactFlowProvider>
        <WorkflowCanvasContent {...props} />
      </ReactFlowProvider>
      <style>{`
        /* Reset React Flow node wrapper styles */
        .react-flow__node {
          padding: 0 !important;
          border: none !important;
          background: transparent !important;
          border-radius: 0 !important;
          box-shadow: none !important;
          font-size: inherit !important;
        }
        
        .react-flow__node-default,
        .react-flow__node-input,
        .react-flow__node-output {
          padding: 0 !important;
          border: none !important;
          background: transparent !important;
        }
        
        /* Ensure handles are properly positioned */
        .react-flow__handle {
          background: #58A6FF;
          border: 2px solid #0D1117;
          width: 12px;
          height: 12px;
          border-radius: 50%;
        }
        
        .react-flow__handle-left {
          left: -6px;
        }
        
        .react-flow__handle-right {
          right: -6px;
        }
        
        /* Selection styles */
        .react-flow__node.selected > div > div:first-child {
          box-shadow: 0 0 0 2px #58A6FF !important;
        }
        
        /* Controls styling */
        .react-flow__controls-brand {
          box-shadow: 0 0 0 1px #30363D;
          border-radius: 4px;
          overflow: hidden;
        }
        
        .react-flow__controls-brand button {
          background: #21262D;
          border: 1px solid #30363D;
          color: #C9D1D9;
        }
        
        .react-flow__controls-brand button:hover {
          background: #30363D;
        }
        
        /* Line clamp utility */
        .line-clamp-2 {
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }
      `}</style>
    </div>
  );
};

export default WorkflowCanvas;
