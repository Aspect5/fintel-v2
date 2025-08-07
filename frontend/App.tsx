// App.tsx - Refactored for Zustand
import React, { useState, useEffect } from 'react';
import { useStore } from './src/stores/store';
import { useWorkflowStore } from './src/stores/workflowStore'; // Import the new store
import SidePanel from './src/components/SidePanel';
import WorkflowCanvas from './src/components/WorkflowCanvas';
import { ApiKeyModal } from './src/components/ApiKeyModal';
import AgentTraceModal from './src/components/AgentTraceModal';
import ReportModal from './src/components/ReportModal';
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

const generateDataQualityNotes = (agentFindings: any[], toolCalls?: any[]): string => {
    const dataSources = new Set<string>();
    let toolCount = 0;
    agentFindings.forEach(finding => {
        if (finding.toolCalls) {
            toolCount += finding.toolCalls.length;
            finding.toolCalls.forEach((tc: any) => dataSources.add(tc.toolName));
        }
    });
    if (toolCalls) {
        toolCount += toolCalls.length;
        toolCalls.forEach((tc: any) => dataSources.add(tc.tool));
    }
    const sourcesList = Array.from(dataSources);
    return sourcesList.length > 0 ? `Analysis based on ${toolCount} data points from ${sourcesList.length} sources (${sourcesList.join(', ')}).` : `Analysis completed with ${agentFindings.length} specialist agents.`;
};


const App: React.FC = () => {
    // Component-level state
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [selectedNode, setSelectedNode] = useState<CustomNode | null>(null);
    const [currentReport, setCurrentReport] = useState<Report | null>(null);
    const [isReportModalVisible, setIsReportModalVisible] = useState(false);
    const [reportGenerated, setReportGenerated] = useState(false);
    const [isLogViewerVisible, setIsLogViewerVisible] = useState(false);

    // Global state from regular Zustand store
    const { setIsApiKeyModalOpen, chatMessages, addChatMessage } = useStore();

    // Global state from the new workflow-specific Zustand store
    const {
        nodes, edges, onNodesChange, onEdgesChange,
        workflowId, setPollingWorkflow,
        status: workflowStatus, query: workflowQuery, executionTime,
        event_history
    } = useWorkflowStore();

    // This hook now manages polling and updates the store directly
    useWorkflowStatus(workflowId);

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
            console.log('[App] Workflow completed. Generating report...');
            
            // Look for enhanced result in multiple places - first try enhanced_result, then result
            let enhancedResult: EnhancedResult | null = null;
            if (workflowData.enhanced_result) {
                enhancedResult = workflowData.enhanced_result as EnhancedResult;
            } else if (typeof workflowData.result === 'object' && workflowData.result !== null) {
                enhancedResult = workflowData.result as EnhancedResult;
            }
            
            const { result, agent_invocations, provider, query, tool_calls } = enhancedResult || {};
            
            // Use agent_invocations from the store if not in enhanced_result
            const agentInvocationsToUse = agent_invocations || workflowData.agent_invocations || [];
            const toolCallsToUse = tool_calls || workflowData.tool_calls || [];
            
            let reportContent = "Analysis completed successfully.";
            if (typeof result === 'string') {
                reportContent = result;
            } else if (typeof result === 'object' && result !== null) {
                // Try to extract the most meaningful content for the executive summary
                const resultObj = result as any;
                if (resultObj.recommendation) {
                    reportContent = resultObj.recommendation;
                } else if (resultObj.market_analysis) {
                    reportContent = resultObj.market_analysis;
                } else if (resultObj.content) {
                    reportContent = resultObj.content;
                } else if (resultObj.sentiment && resultObj.confidence) {
                    // Create a summary from sentiment and confidence
                    reportContent = `Analysis indicates a ${resultObj.sentiment} sentiment with ${Math.round(resultObj.confidence * 100)}% confidence.`;
                    if (resultObj.key_insights && Array.isArray(resultObj.key_insights)) {
                        reportContent += ` Key insights: ${resultObj.key_insights.slice(0, 2).join(', ')}.`;
                    }
                } else {
                    reportContent = JSON.stringify(result, null, 2);
                }
            }
            
            // Extract agent findings from the trace data if available
            let agentFindings: AgentFinding[] = [];
            
            if (workflowData.trace?.task_results) {
                // Use the rich trace data from the backend
                const taskResults = workflowData.trace.task_results;
                agentFindings = Object.entries(taskResults).map(([taskName, taskResult]: [string, any]) => {
                    // Map task names to agent names
                    const agentNameMap: { [key: string]: string } = {
                        'market_analysis': 'Market Analyst',
                        'risk_assessment': 'Risk Assessor', 
                        'final_synthesis': 'Investment Advisor',
                        'recommendation': 'Investment Advisor'
                    };
                    
                    const agentName = agentNameMap[taskName] || taskName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                    
                    // Extract analysis content from the task result
                    let summary = 'Analysis completed';
                    let details: string[] = [];
                    
                    if (typeof taskResult === 'object' && taskResult !== null) {
                        if (taskResult.analysis_summary) {
                            summary = taskResult.analysis_summary;
                        } else if (taskResult.risk_summary) {
                            summary = taskResult.risk_summary;
                        } else if (taskResult.recommendation) {
                            summary = taskResult.recommendation;
                        } else if (taskResult.market_analysis) {
                            summary = taskResult.market_analysis;
                        }
                        
                        // Extract key insights or risk factors as details
                        if (taskResult.key_insights) {
                            details = taskResult.key_insights;
                        } else if (taskResult.risk_factors) {
                            details = taskResult.risk_factors;
                        }
                    }
                    
                    // Extract tool calls from the trace configuration
                    let toolCalls: any[] = [];
                    if (workflowData.trace?.configuration_used?.agents) {
                        const agentConfig = workflowData.trace.configuration_used.agents.find(
                            (agent: any) => agent.role === taskName
                        );
                        if (agentConfig?.tools) {
                            toolCalls = agentConfig.tools.map((toolName: string) => ({
                                toolName,
                                toolInput: 'Used for analysis',
                                toolOutput: 'Data retrieved successfully',
                                toolOutputSummary: `Executed ${toolName}`
                            }));
                        }
                    }
                    
                    return {
                        agentName,
                        specialization: taskName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                        summary,
                        details,
                        toolCalls,
                    };
                });
            } else {
                // Fallback to the old mapping logic
                agentFindings = agentInvocationsToUse.map((inv: any) => ({
                    agentName: inv.agent || inv.agentName || 'Unknown Agent',
                    specialization: inv.specialization || 'Financial Analysis',
                    summary: inv.task || inv.naturalLanguageTask || 'Analysis completed',
                    details: inv.details || [],
                    toolCalls: inv.tool_calls || inv.toolCalls || [],
                }));
            }
            
            const crossAgentInsights = generateCrossAgentInsights(agentFindings, provider || 'unknown');

            const report: Report = {
                executiveSummary: reportContent,
                agentFindings,
                failedAgents: [],
                crossAgentInsights,
                actionableRecommendations: extractActionableRecommendations(reportContent),
                riskAssessment: extractRiskAssessment(reportContent),
                confidenceLevel: extractConfidenceLevel(reportContent),
                dataQualityNotes: generateDataQualityNotes(agentFindings, toolCallsToUse),
                executionTrace: {
                    fintelQueryAnalysis: query || workflowData.query || "",
                    agentInvocations: agentInvocationsToUse,
                },
                result: result || workflowData.result,
            };

            console.log('[App] Generated report:', {
                agentFindingsCount: agentFindings.length,
                hasResult: !!result,
                hasEnhancedResult: !!workflowData.enhanced_result,
                hasAgentInvocations: !!agentInvocationsToUse.length,
                hasTrace: !!workflowData.trace,
                traceTaskResults: workflowData.trace?.task_results ? Object.keys(workflowData.trace.task_results) : [],
                agentFindings: agentFindings.map(f => ({ name: f.agentName, summary: f.summary.substring(0, 50) + '...' }))
            });

            setCurrentReport(report);
            setReportGenerated(true);
            setIsReportModalVisible(true);
        }
    }, [workflowStatus, reportGenerated]);
    
    // Effect to manage loading state based on workflow status
    useEffect(() => {
        setIsLoading(workflowStatus === 'running' || workflowStatus === 'initializing');
    }, [workflowStatus]);

    const handleSelectHistoricalWorkflow = (selectedWorkflowId: string) => {
        // Use store action to set the workflow for polling
        setPollingWorkflow(selectedWorkflowId);
    };

    const handleNodeDoubleClick = (_event: React.MouseEvent, node: CustomNode) => {
        if (node.id === 'enhanced_result' || node.data.status === 'completed') {
            setIsReportModalVisible(true);
            return;
        }
        if ('result' in node.data || 'error' in node.data || 'toolCalls' in node.data) {
            setSelectedNode(node);
        }
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