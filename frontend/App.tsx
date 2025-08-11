// App.tsx - Refactored for Zustand
import React, { useState, useEffect } from 'react';
import { useStore } from './src/stores/store';
import { useWorkflowStore } from './src/stores/workflowStore'; // Import the new store
import SidePanel from './src/components/SidePanel';
import WorkflowCanvas from './src/components/WorkflowCanvas';
import { ApiKeyModal } from './src/components/ApiKeyModal';
import AgentTraceModal from './src/components/AgentTraceModal';
import ReportModal from './src/components/ReportModal';
import { buildReportFromWorkflowState } from './src/utils/reportBuilder';
import Notification from './src/components/Notification';
import { useWorkflowStatus } from './src/hooks/useWorkflowStatus';
import WorkflowHistory from './src/components/WorkflowHistory';
import LogViewer from './src/components/LogViewer';
import {
  CustomNode, Report, AgentFinding, EnhancedResult,
} from './src/types';

// Suppress ResizeObserver loop error
const originalError = console.error;
console.error = (...args) => {
  if (args[0]?.includes?.('ResizeObserver loop completed with undelivered notifications')) {
    return;
  }
  originalError.apply(console, args);
};

// Debug flag to gate noisy logs
const DEBUG = import.meta.env.MODE === 'development' && (window as any).__DEBUG__;

// Helper functions (assuming they are still needed, otherwise can be removed)
const generateCrossAgentInsights = (agentFindings: any[], provider: string): string => {
    if (agentFindings.length === 0) return `Analysis completed using ${provider}.`;
    const agentNames = agentFindings.map(f => f.agentName);
    const insights = [`Analysis completed using ${agentNames.join(' and ')} with ${provider}.`];
    const hasConsensus = agentFindings.every(f => f.summary.toLowerCase().includes('positive'));
    if (hasConsensus) {
        insights.push("All agents identified positive trends, indicating strong consensus.");
    } else {
        insights.push("Agents provided mixed perspectives, suggesting balanced analysis.");
    }
    return insights.join(' ');
};
const extractActionableRecommendations = (content: string): string[] => {
    const recommendations: string[] = [];
    const lines = content.split('\n');
    const startIndex = lines.findIndex(line => line.includes('Action Items') || line.includes('📋'));
    if (startIndex === -1) return ['Review analysis details'];
    for (let i = startIndex + 1; i < lines.length; i++) {
        const line = lines[i].trim();
        if (line.startsWith('-') || line.startsWith('•')) {
            recommendations.push(line.substring(1).trim().replace(/\*\*/g, ''));
        } else if (line.startsWith('#')) {
            break;
        }
    }
    return recommendations.length > 0 ? recommendations : ['Review analysis details'];
};

const extractRiskAssessment = (content: string): string => {
    const lines = content.split('\n');
    const startIndex = lines.findIndex(line => line.includes('Risk Assessment') || line.includes('⚠️'));
    if (startIndex === -1) return "Standard market risks apply";
    const riskLines: string[] = [];
    for (let i = startIndex + 1; i < lines.length; i++) {
        if (lines[i].trim().startsWith('#')) break;
        if (lines[i].trim()) riskLines.push(lines[i].trim());
    }
    return riskLines.join(' ').substring(0, 200) + '...';
};

const extractConfidenceLevel = (content: string): number => {
    const match = content.match(/confidence.*?(\d+)/i);
    return match ? Math.min(Math.max(parseInt(match[1], 10) / 10, 0), 1) : 0.85;
};

// Deprecated: superseded by event_history-derived data quality notes
// const generateDataQualityNotes = (...) => {}


const App: React.FC = () => {
    // Component-level state
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [selectedNode, setSelectedNode] = useState<CustomNode | null>(null);
    const [currentReport, setCurrentReport] = useState<Report | null>(null);
    const [isReportModalVisible, setIsReportModalVisible] = useState(false);
    const [reportGenerated, setReportGenerated] = useState(false);
    const [isLogViewerVisible, setIsLogViewerVisible] = useState(false);
    const [bannerInfo, setBannerInfo] = useState<{ type: string; loadedAt: string } | null>(null);

    // Global state from regular Zustand store
    const { setIsApiKeyModalOpen, chatMessages, addChatMessage } = useStore();

    // Global state from the new workflow-specific Zustand store
    const {
        nodes, edges, onNodesChange, onEdgesChange,
        workflowId,
        status: workflowStatus, query: workflowQuery, executionTime,
        event_history,
        loadWorkflowSnapshot,
    } = useWorkflowStore();

    // This hook now manages polling and updates the store directly
    useWorkflowStatus(workflowId);

    // Reset local, derived state whenever the workflowId changes to prevent leakage
    useEffect(() => {
        setCurrentReport(null);
        setReportGenerated(false);
        setSelectedNode(null);
        setIsReportModalVisible(false);
        setBannerInfo(null);
    }, [workflowId]);

    // Effect to show the API key modal on first visit
    useEffect(() => {
        const hasVisited = localStorage.getItem('hasVisited');
        if (!hasVisited) {
            setIsApiKeyModalOpen(true);
            localStorage.setItem('hasVisited', 'true');
        }
    }, [setIsApiKeyModalOpen]);




    // Effect to handle workflow completion and generate a report
    useEffect(() => {
        const workflowData = useWorkflowStore.getState();
        if (workflowData.status === 'completed' && !reportGenerated) {
            if (DEBUG) console.log('[App] Workflow completed. Generating report...');
            const report = buildReportFromWorkflowState(workflowData as any);
            if (DEBUG) console.log('[App] Generated report via builder:', report);
            setCurrentReport(report);
            setReportGenerated(true);
            setIsReportModalVisible(true);
        }
    }, [workflowStatus, reportGenerated]);
    
    // Effect to manage loading state based on workflow status
    useEffect(() => {
        setIsLoading(workflowStatus === 'running' || workflowStatus === 'initializing');
    }, [workflowStatus]);

    const handleSelectHistoricalWorkflow = async (selectedWorkflowId: string) => {
        const data = await loadWorkflowSnapshot(selectedWorkflowId);
        const wfType = data?.workflow_type || 'unknown';
        const loadedAt = new Date().toLocaleTimeString();
        setBannerInfo({ type: wfType, loadedAt });
        const msg = `Loaded ${wfType} (${loadedAt}).`;
        useStore.getState().addChatMessage({ role: 'assistant', content: msg });
        // Clear any derived report/selection state to avoid leakage from previous workflow
        setCurrentReport(null);
        setReportGenerated(false);
        setSelectedNode(null);
        setIsReportModalVisible(false);
        // Auto-hide banner after a few seconds
        setTimeout(() => setBannerInfo(null), 4000);

    // Reconstruct a report from the loaded snapshot so the final report opens from history
    try {
        // Resolve enhanced result
        const enhanced = (data?.enhanced_result as EnhancedResult) || (typeof data?.result === 'object' ? (data.result as EnhancedResult) : null);
        const { result, agent_invocations, provider, query } = enhanced || {};

        // Build role->taskId map from nodes
        const roleToTaskId: Record<string, string> = {};
        try {
            const nodesList = (data?.nodes || []) as any[];
            nodesList.forEach((n: any) => {
                if (n?.id?.startsWith?.('task_')) {
                    const role = String(n.id).replace('task_', '');
                    const tid = n?.data?.taskId;
                    if (role && tid) roleToTaskId[role] = tid;
                }
            });
        } catch {}

        const allEvents = (data?.event_history || []) as any[];
        const isAgentToolCall = (e: any) => e?.event_type === 'agent_tool_call' && !e?.is_internal_controlflow_tool;

        // Executive summary/content
        let reportContent = 'Analysis completed successfully.';
        if (typeof result === 'string') {
            reportContent = result;
        } else if (typeof result === 'object' && result !== null) {
            const resultObj = result as any;
            if (resultObj.recommendation) {
                reportContent = resultObj.recommendation;
            } else if (resultObj.market_analysis) {
                reportContent = resultObj.market_analysis;
            } else if (resultObj.content) {
                reportContent = resultObj.content;
            } else if (resultObj.sentiment && resultObj.confidence) {
                reportContent = `Analysis indicates a ${resultObj.sentiment} sentiment with ${Math.round(resultObj.confidence * 100)}% confidence.`;
                if (resultObj.key_insights && Array.isArray(resultObj.key_insights)) {
                    reportContent += ` Key insights: ${resultObj.key_insights.slice(0, 2).join(', ')}.`;
                }
            } else {
                reportContent = JSON.stringify(result, null, 2);
            }
        }

        // Agent findings from snapshot trace + event history
        let agentFindings: AgentFinding[] = [];
        if (data?.trace?.task_results) {
            const taskResults = data.trace.task_results;
            agentFindings = Object.entries(taskResults).map(([taskName, taskResult]: [string, any]) => {
                const agentNameMap: { [key: string]: string } = {
                    'market_analysis': 'Market Analyst',
                    'risk_assessment': 'Risk Assessor',
                    'final_synthesis': 'Investment Advisor',
                    'recommendation': 'Investment Advisor'
                };
                const agentName = agentNameMap[taskName] || taskName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                let summary = 'Analysis completed';
                let details: string[] = [];
                if (typeof taskResult === 'object' && taskResult !== null) {
                    if (taskResult.analysis_summary) summary = taskResult.analysis_summary;
                    else if (taskResult.risk_summary) summary = taskResult.risk_summary;
                    else if (taskResult.recommendation) summary = taskResult.recommendation;
                    else if (taskResult.market_analysis) summary = taskResult.market_analysis;
                    if (taskResult.key_insights) details = taskResult.key_insights;
                    else if (taskResult.risk_factors) details = taskResult.risk_factors;
                }
                // Tool calls for this task/agent
                let toolCalls: any[] = [];
                try {
                    const expectedTaskId = roleToTaskId[taskName];
                    const calls = allEvents.filter((e: any) => {
                        if (!isAgentToolCall(e)) return false;
                        const byTaskId = expectedTaskId && e?.task_id && e.task_id === expectedTaskId;
                        const byAgentRole = e?.agent_role && e.agent_role === taskName;
                        const byAgentName = e?.agent_name && e.agent_name === agentName;
                        return Boolean(byTaskId || byAgentRole || byAgentName);
                    });
                    toolCalls = calls.map((e: any) => {
                        const output = e.tool_output;
                        let summary = '';
                        try {
                            if (output === null || output === undefined) summary = 'No output';
                            else if (typeof output === 'string') summary = output.slice(0, 140);
                            else summary = JSON.stringify(output).slice(0, 140);
                        } catch {
                            summary = `Executed ${e.tool_name}`;
                        }
                        return { toolName: e.tool_name, toolInput: e.tool_input, toolOutput: output, toolOutputSummary: summary };
                    });
                } catch {}
                return { agentName, specialization: taskName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()), summary, details, toolCalls };
            });
        } else if (Array.isArray(agent_invocations)) {
            agentFindings = agent_invocations.map((inv: any) => ({
                agentName: inv.agent || inv.agentName || 'Unknown Agent',
                specialization: inv.specialization || 'Financial Analysis',
                summary: inv.task || inv.naturalLanguageTask || 'Analysis completed',
                details: inv.details || [],
                toolCalls: inv.tool_calls || inv.toolCalls || [],
            }));
        }

        const crossAgentInsights = generateCrossAgentInsights(agentFindings, provider || '');
        const toolEvents = allEvents.filter(isAgentToolCall);
        const uniqueTools = Array.from(new Set(toolEvents.map((e: any) => e.tool_name).filter(Boolean)));
        const dataQualityNotes = uniqueTools.length > 0
            ? `Tools used: ${toolEvents.length} calls across ${uniqueTools.length} unique tools (${uniqueTools.join(', ')}).`
            : `No external tools were invoked.`;

        const report: Report = {
            executiveSummary: reportContent,
            agentFindings,
            failedAgents: [],
            crossAgentInsights,
            actionableRecommendations: extractActionableRecommendations(reportContent),
            riskAssessment: extractRiskAssessment(reportContent),
            confidenceLevel: extractConfidenceLevel(reportContent),
            dataQualityNotes,
            executionTrace: {
                fintelQueryAnalysis: query || data.query || '',
                agentInvocations: agent_invocations || [],
            },
            result: result || data.result,
        };
        setCurrentReport(report);
    } catch (e) {
        if (DEBUG) console.warn('[App] Failed to reconstruct report from history snapshot', e);
    }
    };

  const handleNodeDoubleClick = (_event: React.MouseEvent, node: CustomNode) => {
    // Output node opens report
    if (node.id === 'output') {
      setIsReportModalVisible(true);
      return;
    }
    // For agent/task nodes, open the AgentTraceModal
    setSelectedNode(node);
  };

    return (
        <div className="flex h-screen bg-brand-bg text-white font-sans">
            <SidePanel
                chatMessages={chatMessages}
                onAddMessage={addChatMessage}
                isLoading={isLoading}
                onSendMessage={() => {}}
            />

            <main className="flex-1 relative">
                <div className="absolute inset-0">
                    <WorkflowCanvas
                        nodes={nodes}
                        edges={edges}
                        onNodesChange={onNodesChange}
                        onEdgesChange={onEdgesChange}
                        onNodeDoubleClick={handleNodeDoubleClick}
                    />
                    
                    <WorkflowHistory 
                        currentWorkflowId={workflowId}
                        onSelectWorkflow={handleSelectHistoricalWorkflow}
                    />
                    {bannerInfo && (
                        <div className="absolute top-4 left-1/2 -translate-x-1/2 bg-brand-surface/90 backdrop-blur px-3 py-1.5 rounded-full shadow border border-brand-border text-xs text-brand-text-primary z-20">
                            Active: <span className="font-semibold">{bannerInfo.type}</span> • loaded at {bannerInfo.loadedAt}
                        </div>
                    )}
                    
                    {workflowStatus !== 'idle' && (
                        <div className="absolute top-4 left-4 bg-brand-surface p-4 rounded-lg shadow-lg max-w-md z-10">
                            <h3 className="text-lg font-semibold text-brand-text-primary mb-2">
                                Workflow Analysis
                            </h3>
                            <p className="text-sm text-brand-text-secondary mb-2 break-words">
                                Query: {workflowQuery}
                            </p>
                            <div className="flex items-center space-x-2">
                                <span className="text-sm text-brand-text-secondary">Status:</span>
                                <span className={`text-sm font-semibold ${
                                    workflowStatus === 'completed' ? 'text-green-400' :
                                    workflowStatus === 'failed' ? 'text-red-400' :
                                    workflowStatus === 'running' ? 'text-yellow-400' :
                                    'text-blue-400'
                                }`}>
                                    {workflowStatus}
                                </span>
                                {workflowStatus === 'running' || workflowStatus === 'initializing' ? (
                                    <span className="inline-block w-4 h-4 border-2 border-brand-primary border-t-transparent rounded-full animate-spin" aria-label="loading" />
                                ) : null}
                            </div>
                            {executionTime > 0 && (
                                <div className="text-sm text-brand-text-secondary mt-1">
                                    Execution time: {executionTime.toFixed(2)}s
                                </div>
                            )}
                            <div className="text-xs text-brand-text-secondary mt-3">
                                💡 Double-click nodes for details.
                            </div>
                            <div className="text-xs text-brand-text-secondary mt-1">
                                Nodes: {nodes.length}, Edges: {edges.length}
                            </div>
                            <div className="text-xs text-brand-text-secondary mt-1">
                                <button
                                    onClick={() => setIsLogViewerVisible(true)}
                                    className="text-brand-primary hover:text-brand-primary-light underline"
                                >
                                    View Logs
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </main>
            <ApiKeyModal />
            {selectedNode && (
                <AgentTraceModal 
                    node={selectedNode} 
                    onClose={() => setSelectedNode(null)}
                    eventHistory={event_history || []}
                />
            )}
            <ReportModal 
                report={currentReport}
                isVisible={isReportModalVisible}
                onClose={() => setIsReportModalVisible(false)}
                query={workflowQuery || ''}
            />
            <LogViewer 
                isVisible={isLogViewerVisible}
                onClose={() => setIsLogViewerVisible(false)}
            />
            {error && <Notification type="error" message={error} onClose={() => setError(null)} />}
        </div>
    );
};

export default App;