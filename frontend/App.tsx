// App.tsx - Updated handleNodeDoubleClick
import React, { useState, useEffect } from 'react';
import { useNodesState, useEdgesState } from 'reactflow';
import { AgentNodeData, ChatMessage, CustomNode, WorkflowStatus, Report } from './src/types';
import { useStore } from '../store';
import SidePanel from './src/components/SidePanel';
import WorkflowCanvas from './src/components/WorkflowCanvas';
import { ApiKeyModal } from './src/components/ApiKeyModal';
import AgentTraceModal from './src/components/AgentTraceModal';
import ReportModal from './src/components/ReportModal';
import Notification from './src/components/Notification';
import { useWorkflowStatus } from './src/hooks/useWorkflowStatus';
import WorkflowHistory from './src/components/WorkflowHistory';

// Helper functions for report generation
const generateCrossAgentInsights = (agentFindings: any[], provider: string): string => {
    if (agentFindings.length === 0) {
        return `Analysis completed successfully using ${provider}.`;
    }
    
    const insights = [];
    const agentNames = agentFindings.map(f => f.agentName);
    
    if (agentFindings.length > 1) {
        insights.push(`Analysis completed using ${agentNames.join(' and ')} with ${provider}.`);
        
        // Check for consensus
        const hasConsensus = agentFindings.every(f => 
            f.summary.toLowerCase().includes('positive') || 
            f.summary.toLowerCase().includes('favorable') ||
            f.summary.toLowerCase().includes('good')
        );
        
        if (hasConsensus) {
            insights.push("All agents identified positive trends, indicating strong consensus.");
        } else {
            insights.push("Agents provided mixed perspectives, suggesting balanced analysis.");
        }
    }
    
    return insights.join(' ');
};

const extractActionableRecommendations = (content: string): string[] => {
    const recommendations = [];
    const lines = content.split('\n');
    
    for (const line of lines) {
        if (line.includes('Action Items') || line.includes('📋 Action Items')) {
            // Extract bullet points after this section
            const startIndex = lines.indexOf(line);
            for (let i = startIndex + 1; i < lines.length; i++) {
                const currentLine = lines[i].trim();
                if (currentLine.startsWith('-') || currentLine.startsWith('•')) {
                    // Clean up the recommendation text
                    let rec = currentLine.substring(1).trim();
                    // Remove any markdown formatting
                    rec = rec.replace(/\*\*(.*?)\*\*/g, '$1'); // Remove bold
                    rec = rec.replace(/\*(.*?)\*/g, '$1'); // Remove italic
                    recommendations.push(rec);
                } else if (currentLine.startsWith('###') || currentLine.startsWith('##')) {
                    break; // New section
                }
            }
            break;
        }
    }
    
    return recommendations.length > 0 ? recommendations : ['Review analysis details'];
};

const extractRiskAssessment = (content: string): string => {
    const lines = content.split('\n');
    for (const line of lines) {
        if (line.includes('Risk Assessment') || line.includes('⚠️')) {
            const startIndex = lines.indexOf(line);
            const riskLines = [];
            for (let i = startIndex + 1; i < lines.length; i++) {
                const currentLine = lines[i].trim();
                if (currentLine.startsWith('#')) {
                    break; // New section
                }
                if (currentLine) {
                    riskLines.push(currentLine);
                }
            }
            return riskLines.join(' ').substring(0, 200) + (riskLines.join(' ').length > 200 ? '...' : '');
        }
    }
    return "Standard market risks apply";
};

const extractConfidenceLevel = (content: string): number => {
    const confidenceMatch = content.match(/confidence.*?(\d+)/i);
    if (confidenceMatch) {
        const level = parseInt(confidenceMatch[1]);
        return Math.min(Math.max(level / 10, 0), 1); // Convert to 0-1 scale
    }
    return 0.85; // Default confidence
};

const generateDataQualityNotes = (agentFindings: any[]): string => {
    const toolCount = agentFindings.reduce((count, finding) => 
        count + (finding.toolCalls?.length || 0), 0
    );
    
    const dataSources = agentFindings.reduce((sources, finding) => {
        if (finding.toolCalls) {
            finding.toolCalls.forEach((tc: any) => {
                if (tc.toolName) {
                    sources.add(tc.toolName);
                }
            });
        }
        return sources;
    }, new Set<string>());
    
    return `Analysis based on ${toolCount} data points from ${dataSources.size} sources (${Array.from(dataSources).join(', ')}).`;
};

// Type guard to check if a node is an AgentNode
const isAgentNode = (node: CustomNode): node is CustomNode & { data: AgentNodeData } => {
  return 'result' in node.data || 'error' in node.data;
};


const App: React.FC = () => {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [currentWorkflowId, setCurrentWorkflowId] = useState<string | null>(null);
    const [selectedNode, setSelectedNode] = useState<CustomNode | null>(null);
    const [initialStateSet, setInitialStateSet] = useState(false);
    const [currentReport, setCurrentReport] = useState<Report | null>(null);
    const [isReportModalVisible, setIsReportModalVisible] = useState(false);
    const [reportGenerated, setReportGenerated] = useState(false); // Track if report was already generated

    // State for the react-flow canvas
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);

    // Get workflow status
    const { workflowStatus, setWorkflowStatus } = useWorkflowStatus(currentWorkflowId, initialStateSet);

    // Get global state from the Zustand store
    const { setIsApiKeyModalOpen, chatMessages, addChatMessage } = useStore();

    // Effect to show the API key modal on first visit
    useEffect(() => {
        const hasVisited = localStorage.getItem('hasVisited');
        if (!hasVisited) {
            setIsApiKeyModalOpen(true);
            localStorage.setItem('hasVisited', 'true');
        }
    }, [setIsApiKeyModalOpen]);

    // Update nodes and edges when workflow status changes
    useEffect(() => {
        if (workflowStatus?.nodes && workflowStatus?.edges) {
            const typedNodes = workflowStatus.nodes.map((node: any) => ({
                ...node,
                type: node.type || 'default',
                data: {
                    ...node.data,
                    status: node.data?.status || 'pending'
                }
            }));
            
            setNodes(typedNodes as CustomNode[]);
            setEdges(workflowStatus.edges);
        }
    }, [workflowStatus, setNodes, setEdges]);

    // Handle workflow completion and show report modal
    useEffect(() => {
        if (workflowStatus?.status === 'completed' && workflowStatus?.result && !reportGenerated) {
            // Parse the comprehensive report from backend
            const reportContent = workflowStatus.result;
            
            // Extract agent findings from the trace if available
            const agentFindings: AgentFinding[] = [];
            const agentInvocations: any[] = [];
            
            if (workflowStatus.trace?.agent_results) {
                for (const [agentKey, agentData] of Object.entries(workflowStatus.trace.agent_results)) {
                    const data = agentData as any;
                    agentFindings.push({
                        agentName: data.name || agentKey,
                        specialization: data.specialization || 'Analysis',
                        summary: data.result || 'Analysis completed',
                        details: data.tool_calls ? data.tool_calls.map((tc: any) => 
                            `${tc.toolName}: ${tc.toolOutputSummary || 'Executed successfully'}`
                        ) : [],
                        toolCalls: data.tool_calls || []
                    });
                    
                    // Create agent invocation for step counting
                    agentInvocations.push({
                        agentName: data.name || agentKey,
                        naturalLanguageTask: `Analysis for ${agentKey}`,
                        toolCalls: data.tool_calls || [],
                        synthesizedResponse: data.result || 'Analysis completed',
                        status: 'success'
                    });
                }
            }
            
            // Generate dynamic cross-agent insights
            const crossAgentInsights = generateCrossAgentInsights(agentFindings, workflowStatus.provider || 'unknown');
            
            const report: Report = {
                executiveSummary: reportContent,
                agentFindings: agentFindings,
                failedAgents: [],
                crossAgentInsights: crossAgentInsights,
                actionableRecommendations: extractActionableRecommendations(reportContent),
                riskAssessment: extractRiskAssessment(reportContent),
                confidenceLevel: extractConfidenceLevel(reportContent),
                dataQualityNotes: generateDataQualityNotes(agentFindings),
                executionTrace: {
                    fintelQueryAnalysis: workflowStatus.query || "",
                    agentInvocations: agentInvocations
                }
            };
            
            setCurrentReport(report);
            setReportGenerated(true); // Mark report as generated
            setIsReportModalVisible(true);
        }
    }, [workflowStatus, reportGenerated]);

    const handleWorkflowStart = (initialStatus: WorkflowStatus) => {
        setIsLoading(true);
        setError(null);
        setInitialStateSet(false); // Reset for the new workflow
        setCurrentReport(null); // Reset report
        setReportGenerated(false); // Reset report generation flag
        setIsReportModalVisible(false); // Hide report modal
        
        // Use the initial status from the API response
        if (initialStatus?.nodes && initialStatus?.edges) {
            setWorkflowStatus(initialStatus);
            const typedNodes = initialStatus.nodes.map((node: any) => ({
                ...node,
                type: node.type || 'default',
                data: {
                    ...node.data,
                    status: node.data?.status || 'pending'
                }
            }));
            setNodes(typedNodes as CustomNode[]);
            setEdges(initialStatus.edges);
        }
        
        setCurrentWorkflowId(initialStatus.workflow_id || null);
        setInitialStateSet(true); // Signal that the initial state is now set
    };

    const handleSelectHistoricalWorkflow = (workflowId: string) => {
        setCurrentWorkflowId(workflowId);
        setInitialStateSet(true); // Assume historical data is complete
    };

    const handleNodeDoubleClick = (_event: React.MouseEvent, node: CustomNode) => {
        console.log('Node double-clicked:', node);
        console.log('Node data:', node.data);
        console.log('Node type:', node.type);
        
        // Check if it's the final report node
        if (node.id === 'final_synthesis' && currentReport) {
            console.log('Opening report modal for final synthesis');
            setIsReportModalVisible(true);
            return;
        }
        
        const isAgent = node.id !== 'query_input' && node.id !== 'final_synthesis';
        
        if (isAgent && isAgentNode(node)) {
            console.log('Opening modal for node:', node.id);
            setSelectedNode(node);
        } else {
            console.log('Node not eligible for modal:', {
                id: node.id,
                isAgent,
                hasResult: 'result' in node.data,
                hasError: 'error' in node.data,
                status: node.data.status,
                nodeType: node.type
            });
        }
    };

    // Update loading state based on workflow status
    useEffect(() => {
        if (workflowStatus?.status === 'completed' || workflowStatus?.status === 'failed') {
            setIsLoading(false);
        }
    }, [workflowStatus]);

    const handleAddMessage = (message: ChatMessage) => {
        addChatMessage(message);
    };

    const handleCloseReportModal = () => {
        setIsReportModalVisible(false);
        // Don't reset the report or workflow state - keep the graph visible
    };

    return (
        <div className="flex h-screen bg-brand-bg text-white font-sans">
            <SidePanel
                chatMessages={chatMessages}
                onAddMessage={handleAddMessage}
                isLoading={isLoading}
                onWorkflowStart={handleWorkflowStart}
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
                        currentWorkflowId={currentWorkflowId}
                        onSelectWorkflow={handleSelectHistoricalWorkflow}
                    />
                    
                    {workflowStatus && (
                        <div className="absolute top-4 left-4 bg-brand-surface p-4 rounded-lg shadow-lg max-w-md z-10">
                            <h3 className="text-lg font-semibold text-brand-text-primary mb-2">
                                Workflow Analysis
                            </h3>
                            <p className="text-sm text-brand-text-secondary mb-2 break-words">
                                Query: {workflowStatus.query}
                            </p>
                            <div className="flex items-center space-x-2">
                                <span className="text-sm text-brand-text-secondary">Status:</span>
                                <span className={`text-sm font-semibold ${
                                    workflowStatus.status === 'completed' ? 'text-green-400' :
                                    workflowStatus.status === 'failed' ? 'text-red-400' :
                                    workflowStatus.status === 'running' ? 'text-yellow-400' :
                                    'text-blue-400'
                                }`}>
                                    {workflowStatus.status}
                                </span>
                            </div>
                            {workflowStatus.execution_time && (
                                <div className="text-sm text-brand-text-secondary mt-1">
                                    Execution time: {workflowStatus.execution_time.toFixed(2)}s
                                </div>
                            )}
                            <div className="text-xs text-brand-text-secondary mt-3">
                                💡 Double-click on agent nodes to see details
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
                />
            )}
            <ReportModal 
                report={currentReport}
                isVisible={isReportModalVisible}
                onClose={handleCloseReportModal}
                query={workflowStatus?.query || ''}
            />
            {error && <Notification type="error" message={error} onClose={() => setError(null)} />}
        </div>
    );
};

export default App;
