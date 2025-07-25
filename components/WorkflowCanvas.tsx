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
const CustomNode: React.FC<NodeProps> = ({ data, id }) => {
  const { label, details, status, error } = data;
  
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

  return (
    <div className={`relative p-4 bg-brand-surface border-2 rounded-lg shadow-lg min-w-[200px] ${getBorderColor()} transition-all duration-300 cursor-pointer hover:shadow-xl`}>
      <Handle 
        type="target" 
        position={Position.Left} 
        className="!bg-brand-secondary !w-3 !h-3 !border-2 !border-brand-bg" 
        style={{ left: '-8px' }}
      />
      
      <div className="flex items-center justify-between mb-2">
        <div className="font-bold text-lg text-white">{label}</div>
        {getStatusIcon()}
      </div>
      
      {details && (
        <div className="text-sm text-brand-text-secondary">{details}</div>
      )}
      
      {error && (
        <div className="text-xs text-red-400 mt-2 p-2 bg-red-900/40 rounded">
          Error: {error}
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
          background-color: #161B22;
          border-bottom: 1px solid #30363D;
          fill: #C9D1D9;
          width: 32px;
          height: 32px;
        }
        
        .react-flow__controls-brand button:last-child {
          border-bottom: none;
        }
        
        .react-flow__controls-brand button:hover {
          background-color: #0D1117;
        }
        
        .react-flow__minimap-brand {
          background-color: #161B22;
          border: 1px solid #30363D;
        }
        
        .react-flow__minimap-mask {
          fill: rgba(13, 17, 23, 0.6);
        }
        
        /* Edge styling */
        .react-flow__edge-path {
          stroke: #30363D;
          stroke-width: 2;
        }
        
        .react-flow__edge.animated .react-flow__edge-path {
          stroke: #58A6FF;
          stroke-dasharray: 5;
          animation: dashdraw 0.5s linear infinite;
        }
        
        @keyframes dashdraw {
          to {
            stroke-dashoffset: -10;
          }
        }
        
        /* Ensure proper cursor for nodes */
        .react-flow__node {
          cursor: pointer;
        }
      `}</style>
    </div>
  );
};

export default WorkflowCanvas;
