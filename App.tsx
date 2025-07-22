import React, { useState, useCallback, useEffect } from 'react';
import { Node, Edge, OnNodesChange, useNodesState, useEdgesState, Position } from 'reactflow';
import { Report, Plan, AgentFinding, AgentInvocation, ChatMessage, AgentNodeData, CustomNode, AgentFailure } from './types';
import { runCoordinatorPlanner, runAgentTask, runReportSynthesizer, AgentFailureError } from './services/geminiService';
import { getAgentDefinition } from './agents/registry';
import WorkflowCanvas from './components/WorkflowCanvas';
import SidePanel from './components/SidePanel';
import ReportDisplay from './components/ReportDisplay';
import PlayIcon from './components/icons/PlayIcon';
import DocumentTextIcon from './components/icons/DocumentTextIcon';
import AgentTraceModal from './components/AgentTraceModal';
import { useApiKeyStore } from './store';
import ApiKeyModal from './components/ApiKeyModal';
import Notification from './components/Notification';

type NotificationType = {
  message: string;
  type: 'success' | 'error';
};

const App: React.FC = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [finalReport, setFinalReport] = useState<Report | null>(null);
  const [isReportVisible, setIsReportVisible] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedNodeForTrace, setSelectedNodeForTrace] = useState<CustomNode | null>(null);
  const [notification, setNotification] = useState<NotificationType | null>(null);
  
  const areKeysSet = useApiKeyStore((state) => state.areKeysSet);
  const keysJustSet = useApiKeyStore((state) => state.keysJustSet);
  const acknowledgeKeysSet = useApiKeyStore((state) => state.acknowledgeKeysSet);

  useEffect(() => {
      if (keysJustSet) {
          setNotification({ message: "API keys accepted. Ready for analysis!", type: 'success' });
          acknowledgeKeysSet();
      }
  }, [keysJustSet, acknowledgeKeysSet]);

  useEffect(() => {
    // Welcome message.
    const welcomeMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      sender: 'ai',
      content: areKeysSet 
          ? "Welcome to FINTEL! Describe the financial analysis you need, and I'll create a workflow to get it done."
          : "Welcome to FINTEL! Please set your API keys to begin.",
      timestamp: new Date().toISOString(),
    };
    setChatMessages([welcomeMessage]);
  }, [areKeysSet]);

  const addChatMessage = (sender: 'user' | 'ai', content: string) => {
    setChatMessages(prev => [
      ...prev,
      {
        id: `msg-${Date.now()}`,
        sender,
        content,
        timestamp: new Date().toISOString(),
      },
    ]);
  };
  
  const setAndNotifyError = (errorMessage: string) => {
      setError(errorMessage);
      addChatMessage('ai', `SYSTEM ERROR: ${errorMessage}`);
      setNotification({ message: errorMessage.length > 100 ? `${errorMessage.substring(0, 97)}...` : errorMessage, type: 'error' });
  };

  const generateWorkflow = useCallback(async (query: string) => {
    if (!areKeysSet) {
        addChatMessage('ai', "Please set your API keys before starting an analysis.");
        return;
    }
    addChatMessage('user', query);
    setIsRunning(true);
    setError(null);
    setFinalReport(null);
    setIsReportVisible(false);
    setSelectedNodeForTrace(null);
    
    setNodes([]);
    setEdges([]);

    try {
      addChatMessage('ai', "Initializing FINTEL: Coordinator is analyzing the query...");
      const { plan, analysis } = await runCoordinatorPlanner(query);
      addChatMessage('ai', `Coordinator Plan: "${analysis}"`);

      const yGap = 175;
      const xGap = 350;

      const coordinatorNode: CustomNode = {
        id: 'coordinator',
        type: 'coordinator',
        position: { x: 50, y: (plan.length / 2) * yGap - yGap / 2 },
        data: { label: 'FINTEL Coordinator', details: analysis },
      };

      const agentNodes: CustomNode[] = plan.map((p, i) => ({
        id: p.agentName,
        type: 'agent',
        position: { x: xGap, y: i * yGap },
        data: {
          label: p.agentName,
          details: p.task,
          status: 'pending',
          toolCalls: [],
        },
      }));
      
      const synthesizerNode: CustomNode = {
        id: 'synthesizer',
        type: 'synthesizer',
        position: { x: xGap * 2, y: (plan.length / 2) * yGap - yGap / 2 },
        data: {
            label: 'Report Synthesizer',
            details: 'Combines agent findings into the final report.',
            status: 'pending',
        }
      };

      const newNodes = [coordinatorNode, ...agentNodes, synthesizerNode];
      
      const agentEdges = agentNodes.map(node => ({
        id: `e-coord-${node.id}`,
        source: 'coordinator',
        target: node.id,
        animated: true,
        type: 'smoothstep',
      }));

      const synthesizerEdges = agentNodes.map(node => ({
        id: `e-${node.id}-synth`,
        source: node.id,
        target: 'synthesizer',
        animated: true,
        type: 'smoothstep',
      }));

      const newEdges = [...agentEdges, ...synthesizerEdges];

      setNodes(newNodes);
      setEdges(newEdges);
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "An unknown error occurred.";
      setAndNotifyError(errorMessage);
      console.error(err);
    } finally {
        setIsRunning(false);
    }
  }, [areKeysSet]);

  const runWorkflow = useCallback(async () => {
    setIsRunning(true);
    setError(null);
    setFinalReport(null);
    setIsReportVisible(false);
    setSelectedNodeForTrace(null);
    
    setNodes(nds => nds.map(n => n.type === 'agent' ? { ...n, data: { ...n.data, status: 'running', error: undefined, result: undefined, toolCalls: [] } } : n));

    const agentPlans: Plan[] = nodes
        .filter((n): n is CustomNode => n.type === 'agent')
        .map(n => ({ agentName: n.data.label, task: n.data.details }));

    const agentPromises = agentPlans.map(p => runAgentTask(p, () => {}));
    const agentResults = await Promise.allSettled(agentPromises);
    
    const successfulInvocations: AgentInvocation[] = [];
    const failedAgents: AgentFailure[] = [];
    const nodeUpdates = new Map<string, Partial<AgentNodeData>>();

    agentResults.forEach((result, index) => {
        const agentPlan = agentPlans[index];
        if (result.status === 'fulfilled') {
            const invocation = result.value;
            successfulInvocations.push(invocation);
            nodeUpdates.set(agentPlan.agentName, {
                status: 'success',
                result: invocation.synthesizedResponse,
                toolCalls: invocation.toolCalls,
                error: undefined,
            });
        } else {
            const error = result.reason;
            const errorMsg = error instanceof Error ? error.message : "An unknown error occurred.";
            const failurePayload: AgentFailure = error instanceof AgentFailureError 
                ? error.payload 
                : { agentName: agentPlan.agentName, task: agentPlan.task, error: errorMsg };
            
            failedAgents.push(failurePayload);
            nodeUpdates.set(agentPlan.agentName, {
                status: 'failure',
                error: errorMsg,
            });
        }
    });

    setNodes(nds =>
        nds.map(n => {
            if ((n.type === 'agent' || n.type === 'synthesizer') && nodeUpdates.has(n.id)) {
                 return { ...n, data: { ...n.data, ...nodeUpdates.get(n.id) } };
            }
            return n;
        })
    );
    
    if (successfulInvocations.length === 0 && failedAgents.length > 0) {
        const errorMsg = "All agents failed to execute. Unable to generate a report.";
        setAndNotifyError(errorMsg);
        setIsRunning(false);
        setNodes(nds => nds.map(n => n.id === 'synthesizer' ? { ...n, data: { ...n.data, status: 'failure', error: 'No successful agent findings to process.' } } : n));
        return;
    }
    
    try {
        setNodes(nds => nds.map(n => n.id === 'synthesizer' ? { ...n, data: { ...n.data, status: 'running' } } : n));
        const agentFindings: AgentFinding[] = successfulInvocations.map(inv => ({
            agentName: inv.agentName,
            specialization: getAgentDefinition(inv.agentName)?.description || 'Specialized Agent',
            summary: inv.synthesizedResponse,
            details: inv.toolCalls.map(tc => `${tc.toolOutputSummary}`),
        }));

        const query = [...chatMessages].reverse().find(m => m.sender === 'user')?.content || 'No query found.';
        const synthesizedParts = await runReportSynthesizer(query, agentFindings);
        
        const finalReportData: Report = {
            ...synthesizedParts,
            agentFindings,
            failedAgents,
            executionTrace: { fintelQueryAnalysis: '', agentInvocations: successfulInvocations },
        };
        
        setFinalReport(finalReportData);
        setIsReportVisible(true);
        addChatMessage('ai', '🎉 Report generated successfully!');
        setNotification({ message: 'Report generated successfully!', type: 'success' });
        setNodes(nds => nds.map(n => n.id === 'synthesizer' ? { ...n, data: { ...n.data, status: 'success' } } : n));

    } catch(err) {
        const errorMessage = err instanceof Error ? err.message : "An unknown error occurred.";
        setAndNotifyError(`SYNTHESIS ERROR: ${errorMessage}`);
        setNodes(nds => nds.map(n => n.id === 'synthesizer' ? { ...n, data: { ...n.data, status: 'failure', error: errorMessage } } : n));
    } finally {
        setIsRunning(false);
    }

  }, [nodes, setNodes, chatMessages]);

  const handleNodeDoubleClick = useCallback((_event: React.MouseEvent, node: Node) => {
    if (node.type === 'agent' && node.data.status !== 'pending' && node.data.status !== 'running') {
      setSelectedNodeForTrace(node as CustomNode);
    }
  }, []);
  
  const mainContentStyle = {
    filter: !areKeysSet ? 'blur(5px)' : 'none',
    transition: 'filter 0.3s ease-in-out',
    pointerEvents: !areKeysSet ? 'none' : 'auto',
  } as React.CSSProperties;


  return (
    <>
      {!areKeysSet && <ApiKeyModal />}

      <div style={mainContentStyle} className="flex flex-col h-full">
          <header className="text-center py-4 border-b border-brand-border flex-shrink-0">
            <h1 className="text-2xl font-bold text-white">FINTEL</h1>
            <p className="text-sm text-brand-text-secondary">Workflow Development Environment</p>
          </header>
          
          <div className="flex-grow flex flex-row overflow-hidden">
            <SidePanel 
              chatMessages={chatMessages}
              onSendMessage={generateWorkflow}
              isLoading={isRunning || !areKeysSet}
            />

            <main className="flex-grow flex flex-col relative bg-brand-bg">
              <div className="absolute top-4 right-4 z-10 flex items-center">
                <button
                    onClick={runWorkflow}
                    disabled={isRunning || nodes.length === 0}
                    className="flex items-center justify-center px-6 py-3 bg-brand-success text-white font-semibold rounded-md hover:bg-green-500 disabled:bg-brand-text-secondary disabled:cursor-not-allowed transition-all duration-300 ease-in-out transform hover:scale-105 disabled:scale-100"
                >
                    <PlayIcon className="w-5 h-5 mr-2" />
                    {isRunning ? 'Executing...' : 'Run Workflow'}
                </button>
                {finalReport && (
                    <button
                        onClick={() => setIsReportVisible(true)}
                        className="flex items-center justify-center px-6 py-3 bg-brand-primary text-white font-semibold rounded-md hover:bg-brand-secondary transition-all duration-300 ease-in-out transform hover:scale-105 ml-4"
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

      {notification && (
          <Notification 
              message={notification.message}
              type={notification.type}
              onClose={() => setNotification(null)}
          />
      )}

      {finalReport && isReportVisible && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center animate-fade-in" onClick={() => setIsReportVisible(false)}>
          <div className="w-full max-w-4xl h-[90vh] bg-brand-surface rounded-lg shadow-2xl overflow-y-auto" onClick={e => e.stopPropagation()}>
             <ReportDisplay report={finalReport} />
          </div>
           <style>{`
            @keyframes fade-in {
              from { opacity: 0; }
              to { opacity: 1; }
            }
            .animate-fade-in {
                animation: fade-in 0.3s ease-out forwards;
            }
          `}</style>
        </div>
      )}

      {selectedNodeForTrace && (
        <AgentTraceModal 
            node={selectedNodeForTrace} 
            onClose={() => setSelectedNodeForTrace(null)} 
        />
      )}
    </>
  );
};

export default App;