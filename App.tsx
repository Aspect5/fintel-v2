// App.tsx (Corrected Version)

import React, { useState, useCallback, useEffect } from 'react';
// FIX: Import the corrected types and use Edge from reactflow
import { Node, Edge, useNodesState, useEdgesState } from 'reactflow';
import { Report, Plan, ChatMessage, CustomNode, CustomNodeData, AgentNodeData, AgentInvocationStatus } from './types';
import { runCoordinatorPlanner, runAgentTask } from './services/agentService';
import { runControlFlow } from './services/controlflowService';
import WorkflowCanvas from './components/WorkflowCanvas';
import SidePanel from './components/SidePanel';
import ReportDisplay from './components/ReportDisplay';
import PlayIcon from './components/icons/PlayIcon';
import DocumentTextIcon from './components/icons/DocumentTextIcon';
import AgentTraceModal from './components/AgentTraceModal';
import { useStore } from './store';
import ApiKeyModal from './components/ApiKeyModal';
import Notification from './components/Notification';
import { GEMINI_API_KEY } from './config';

type NotificationType = {
  message: string;
  type: 'success' | 'error';
};

// FIX: A type guard to correctly identify nodes with AgentNodeData
const isAgentNode = (node: CustomNode): node is Node<AgentNodeData> =>
  node.type === 'agent' && node.data && 'toolCalls' in node.data;

const App: React.FC = () => {
  // FIX: useNodesState generic is the union of DATA types, not the full node type.
  const [nodes, setNodes, onNodesChange] = useNodesState<CustomNodeData>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]); // Explicitly type edges
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [finalReport, setFinalReport] = useState<Report | null>(null);
  const [isReportVisible, setIsReportVisible] = useState<boolean>(false);
  // FIX: State for the selected node should be the specific agent node type.
  const [selectedNodeForTrace, setSelectedNodeForTrace] = useState<Node<AgentNodeData> | null>(null);
  const [notification, setNotification] = useState<NotificationType | null>(null);

  const { areKeysSet, keysJustSet, acknowledgeKeysSet, executionEngine } = useStore();

  const [showApiKeyModal, setShowApiKeyModal] = useState(false);

  useEffect(() => {
    if (!GEMINI_API_KEY) {
      setShowApiKeyModal(true);
    }
  }, []);

  useEffect(() => {
    if (keysJustSet) {
      setNotification({ message: "API keys accepted. Ready for analysis!", type: 'success' });
      acknowledgeKeysSet();
      setShowApiKeyModal(false);
    }
  }, [keysJustSet, acknowledgeKeysSet]);

  useEffect(() => {
    const welcomeMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      sender: 'ai',
      content: areKeysSet || GEMINI_API_KEY
        ? "Welcome to FINTEL! Describe the financial analysis you need, and I'll create a workflow to get it done."
        : "Welcome to FINTEL! Please set your API keys to begin.",
      timestamp: new Date().toISOString(),
    };
    setChatMessages([welcomeMessage]);
  }, [areKeysSet]);

  const addChatMessage = (sender: 'user' | 'ai', content: string) => {
    setChatMessages(prev => [
      ...prev,
      { id: `msg-${Date.now()}`, sender, content, timestamp: new Date().toISOString() },
    ]);
  };

  const setAndNotifyError = (errorMessage: string) => {
    addChatMessage('ai', `SYSTEM ERROR: ${errorMessage}`);
    setNotification({ message: errorMessage.length > 100 ? `${errorMessage.substring(0, 97)}...` : errorMessage, type: 'error' });
  };

  const generateGeminiWorkflow = useCallback(async (query: string) => {
    try {
      addChatMessage('ai', "Initializing Gemini Engine: Coordinator is analyzing the query...");
      const { plan, analysis } = await runCoordinatorPlanner(query);
      addChatMessage('ai', `Coordinator Plan: "${analysis}"`);

      const yGap = 175;
      const xGap = 350;

      // FIX: Remove explicit CustomNode type annotation. Let TypeScript infer the types.
      // The object literals are compatible with CustomNode and setNodes will accept them.
      const coordinatorNode: CustomNode = { id: 'coordinator', type: 'coordinator', position: { x: 50, y: (plan.length / 2) * yGap - yGap / 2 }, data: { label: 'FINTEL Coordinator', details: analysis, status: 'success' } };
      const agentNodes: CustomNode[] = plan.map((p, i) => ({ id: p.agentName, type: 'agent', position: { x: xGap, y: i * yGap }, data: { label: p.agentName, details: p.task, status: 'pending', toolCalls: [] } }));
      const synthesizerNode: CustomNode = { id: 'synthesizer', type: 'synthesizer', position: { x: xGap * 2, y: (plan.length / 2) * yGap - yGap / 2 }, data: { label: 'Report Synthesizer', details: 'Combines agent findings.', status: 'pending' } };

      setNodes([coordinatorNode, ...agentNodes, synthesizerNode]);
      const agentEdges = agentNodes.map(node => ({ id: `e-coord-${node.id}`, source: 'coordinator', target: node.id, animated: true, type: 'smoothstep' }));
      const synthesizerEdges = agentNodes.map(node => ({ id: `e-${node.id}-synth`, source: node.id, target: 'synthesizer', animated: true, type: 'smoothstep' }));
      setEdges([...agentEdges, ...synthesizerEdges]);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "An unknown error occurred.";
      setAndNotifyError(errorMessage);
    }
  }, [setEdges, setNodes]);

  const runGeminiWorkflow = useCallback(async () => {
    setNodes(nds => nds.map(n => n.type === 'agent' ? { ...n, data: { ...n.data, status: 'running' as AgentInvocationStatus } } : n));
    
    // FIX: Use the type guard to correctly type the filtered nodes. This resolves the error on `.data.label`
    const agentPlans: Plan[] = nodes.filter(isAgentNode).map(n => ({ agentName: n.data.label, task: n.data.details }));
    
    await Promise.allSettled(agentPlans.map(p => runAgentTask(p, () => {})));

  }, [nodes, setNodes]);

  const runPythonWorkflow = useCallback(async (query: string) => {
    addChatMessage('ai', "Executing with ControlFlow (Python) Engine...");

    // FIX: This node needs to conform to AgentNodeData since its type is 'agent'.
    const runningNode: CustomNode = {
      id: 'controlflow_runner',
      type: 'agent',
      position: { x: 150, y: 150 },
      data: {
        label: 'ControlFlow Backend',
        details: 'Orchestrating agents in Python...',
        status: 'running',
        toolCalls: [], // Added to satisfy the AgentNodeData type
      },
    };
    setNodes([runningNode]);
    setEdges([]);

    try {
      const report = await runControlFlow(query);
      setFinalReport(report);
      setIsReportVisible(true);
      addChatMessage('ai', '🎉 Report generated by ControlFlow Engine!');
      setNotification({ message: 'Python backend finished successfully!', type: 'success' });
      setNodes(nds => nds.map(n => n.id === 'controlflow_runner' ? { ...n, data: { ...n.data, status: 'success', result: "Completed." } } : n));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "An unknown error occurred.";
      setAndNotifyError(errorMessage);
      setNodes(nds => nds.map(n => n.id === 'controlflow_runner' ? { ...n, data: { ...n.data, status: 'failure', error: errorMessage } } : n));
    }
  }, [setNodes, setEdges]);

  const handleSendMessage = useCallback(async (query: string) => {
    if ((executionEngine === "Gemini (In-Browser)") && (!areKeysSet && !GEMINI_API_KEY)) {
      addChatMessage('ai', "Please set your Gemini API key to use the in-browser engine.");
      return;
    }

    addChatMessage('user', query);
    setIsRunning(true);
    setFinalReport(null);
    setIsReportVisible(false);
    setSelectedNodeForTrace(null);

    if (executionEngine === "ControlFlow (Python)") {
      await runPythonWorkflow(query);
    } else {
      await generateGeminiWorkflow(query);
    }

    setIsRunning(false);
  }, [executionEngine, areKeysSet, generateGeminiWorkflow, runPythonWorkflow]);

  const handleRunWorkflowClick = () => {
    if (executionEngine === "Gemini (In-Browser)") {
      runGeminiWorkflow();
    } else {
      setAndNotifyError("The 'Run Workflow' button is only for the Gemini engine. ControlFlow runs automatically.");
    }
  };

  // FIX: Correctly type the `node` parameter and use the type guard.
  const handleNodeDoubleClick = useCallback((_event: React.MouseEvent, node: CustomNode) => {
    if (isAgentNode(node) && node.data.status !== 'pending' && node.data.status !== 'running') {
      setSelectedNodeForTrace(node);
    }
  }, []);

  const mainContentStyle = { filter: showApiKeyModal ? 'blur(5px)' : 'none', transition: 'filter 0.3s ease-in-out', pointerEvents: showApiKeyModal ? 'none' : 'auto' } as React.CSSProperties;

  return (
    <>
      {showApiKeyModal && <ApiKeyModal />}

      <div style={mainContentStyle} className="flex flex-col h-full">
        { /* JSX remains the same */ }
        <header className="text-center py-4 border-b border-brand-border flex-shrink-0">
          <h1 className="text-2xl font-bold text-white">FINTEL</h1>
          <p className="text-sm text-brand-text-secondary">Dual-Backend Agentic Environment</p>
        </header>

        <div className="flex-grow flex flex-row overflow-hidden">
          <SidePanel
            chatMessages={chatMessages}
            onSendMessage={handleSendMessage}
            isLoading={isRunning}
          />

          <main className="flex-grow flex flex-col relative bg-brand-bg">
            <div className="absolute top-4 right-4 z-10 flex items-center">
              {executionEngine === 'Gemini (In-Browser)' && (
                <button
                  onClick={handleRunWorkflowClick}
                  disabled={isRunning || nodes.length === 0}
                  className="flex items-center justify-center px-6 py-3 bg-brand-success text-white font-semibold rounded-md hover:bg-green-500 disabled:bg-brand-text-secondary disabled:cursor-not-allowed"
                >
                  <PlayIcon className="w-5 h-5 mr-2" />
                  {isRunning ? 'Executing...' : 'Run Gemini Workflow'}
                </button>
              )}
              {finalReport && (
                <button
                  onClick={() => setIsReportVisible(true)}
                  className="flex items-center justify-center px-6 py-3 bg-brand-primary text-white font-semibold rounded-md hover:bg-brand-secondary ml-4"
                >
                  <DocumentTextIcon className="w-5 h-5 mr-2" />
                  View Report
                </button>
              )}
            </div>
            <WorkflowCanvas
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onNodeDoubleClick={handleNodeDoubleClick}
            />
          </main>
        </div>
      </div>

      {notification && <Notification message={notification.message} type={notification.type} onClose={() => setNotification(null)} />}
      {finalReport && isReportVisible && <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center" onClick={() => setIsReportVisible(false)}><div className="w-full max-w-4xl h-[90vh] bg-brand-surface rounded-lg shadow-2xl overflow-y-auto" onClick={e => e.stopPropagation()}><ReportDisplay report={finalReport} /></div></div>}
      {selectedNodeForTrace && <AgentTraceModal node={selectedNodeForTrace} onClose={() => setSelectedNodeForTrace(null)} />}
    </>
  );
};

export default App;