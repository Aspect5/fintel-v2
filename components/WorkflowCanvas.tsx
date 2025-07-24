import React, { useMemo } from 'react';
import ReactFlow, { Background, Controls, MiniMap, Node, Edge, OnNodesChange, OnEdgesChange, Handle, Position } from 'reactflow';
import { AgentNodeData } from '../types';

import SpinnerIcon from './icons/SpinnerIcon';
import CheckCircleIcon from './icons/CheckCircleIcon';
import XCircleIcon from './icons/XCircleIcon';
import PlayIcon from './icons/PlayIcon';
import SparklesIcon from './icons/SparklesIcon';

const StatusIcon: React.FC<{ status?: 'pending' | 'running' | 'success' | 'failure' }> = ({ status }) => {
  switch (status) {
    case 'running':
      return <SpinnerIcon className="w-5 h-5 text-brand-primary animate-spin" />;
    case 'success':
      return <CheckCircleIcon className="w-5 h-5 text-brand-success" />;
    case 'failure':
      return <XCircleIcon className="w-5 h-5 text-brand-danger" />;
    default:
      return null;
  }
};

const AgentNode: React.FC<{ data: AgentNodeData }> = ({ data }) => {
    const { label, details, status, error, toolCalls } = data;
    
    const borderColor = status === 'failure' ? 'border-brand-danger' : status === 'success' ? 'border-brand-success' : 'border-brand-border';
    const hasRun = status === 'success' || status === 'failure';

    return (
        <div className={`p-4 bg-brand-surface border-2 rounded-lg shadow-lg w-80 ${borderColor} transition-colors`}>
            <div className="flex items-center justify-between mb-2">
                <div className="font-bold text-lg text-white">{label}</div>
                <StatusIcon status={status} />
            </div>
            <div className="p-2 bg-brand-bg rounded">
                <p className="text-xs text-brand-text-secondary mb-1 font-semibold">Task:</p>
                <p className="text-sm text-brand-text-primary">{details}</p>
            </div>

            {hasRun && (
                 <div className="mt-2 text-xs text-brand-text-secondary border-t border-brand-border pt-2">
                    <div className="flex justify-between items-center">
                         <span>Tool Calls Made: <span className="font-bold text-white">{toolCalls?.length ?? 0}</span></span>
                         <span className="italic text-brand-text-secondary/70">Double-click for trace</span>
                    </div>
                </div>
            )}
            
            {error && <p className="text-xs text-red-400 mt-2 p-2 bg-red-900/40 rounded">Error: {error}</p>}
           
            <Handle type="source" position={Position.Right} className="!bg-brand-secondary" />
            <Handle type="target" position={Position.Left} className="!bg-brand-secondary" />
        </div>
    );
};

const CoordinatorNode: React.FC<{ data: { label: string; details: string } }> = ({ data }) => {
    return (
        <div className="p-4 bg-brand-primary/20 border-2 border-brand-primary rounded-lg shadow-lg w-72">
            <div className="flex items-center mb-2">
                <PlayIcon className="w-6 h-6 text-brand-primary mr-2" />
                <div className="font-bold text-lg text-white">{data.label}</div>
            </div>
            <p className="text-sm text-brand-text-secondary">{data.details}</p>
            <Handle type="source" position={Position.Right} className="!bg-brand-secondary" />
        </div>
    );
};

const SynthesizerNode: React.FC<{ data: AgentNodeData }> = ({ data }) => {
    const { label, details, status, error } = data;
    const borderColor = status === 'failure' ? 'border-brand-danger' : status === 'success' ? 'border-brand-success' : 'border-brand-border';

     return (
        <div className={`p-4 bg-brand-surface border-2 rounded-lg shadow-lg w-72 ${borderColor} transition-colors`}>
            <div className="flex items-center justify-between mb-2">
                 <div className="flex items-center">
                    <SparklesIcon className="w-5 h-5 text-brand-primary mr-2" />
                    <div className="font-bold text-lg text-white">{label}</div>
                 </div>
                <StatusIcon status={status} />
            </div>
            <p className="text-sm text-brand-text-secondary">{details}</p>
            {error && <p className="text-xs text-red-400 mt-2 p-2 bg-red-900/40 rounded">Error: {error}</p>}
            <Handle type="target" position={Position.Left} className="!bg-brand-secondary" />
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

const WorkflowCanvas: React.FC<WorkflowCanvasProps> = ({ nodes, edges, onNodesChange, onEdgesChange, onNodeDoubleClick }) => {
  // Memoize nodeTypes to prevent recreation on every render
  const nodeTypes = useMemo(() => ({
    coordinator: CoordinatorNode,
    agent: AgentNode,
    synthesizer: SynthesizerNode,
  }), []);

  return (
    <div className="w-full h-full" style={{ width: '100%', height: '100%' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeDoubleClick={onNodeDoubleClick}
        nodeTypes={nodeTypes}
        fitView
        proOptions={{ hideAttribution: true }}
        className="bg-brand-bg"
        style={{ width: '100%', height: '100%' }}
      >
        <Background gap={24} color="#30363D" />
        <Controls className="react-flow__controls-brand"/>
        <MiniMap nodeStrokeWidth={3} zoomable pannable className="react-flow__minimap-brand" />
        <style>{`
            .react-flow__controls-brand button {
                background-color: #161B22;
                border-bottom: 1px solid #30363D;
                fill: #C9D1D9;
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
             .react-flow__handle {
                background: #58A6FF;
                width: 8px;
                height: 12px;
                border-radius: 2px;
            }
        `}</style>
      </ReactFlow>
    </div>
  );
};

export default WorkflowCanvas;