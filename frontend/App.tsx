// App.tsx - Updated handleNodeDoubleClick
import React, { useState, useEffect } from 'react';

// Suppress ResizeObserver loop error (known issue with React Flow)
const originalError = console.error;
console.error = (...args) => {
  if (args[0]?.includes?.('ResizeObserver loop completed with undelivered notifications')) {
    return;
  }
  originalError.apply(console, args);
};
import { useNodesState, useEdgesState } from 'reactflow';
import { AgentNodeData, ChatMessage, CustomNode, WorkflowStatus, Report } from './src/types';
import { useStore } from './src/stores/store';
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

const generateDataQualityNotes = (agentFindings: any[], toolCalls?: any[]): string => {
    let toolCount = 0;
    const dataSources = new Set<string>();
    
    // Count from agent findings
    agentFindings.forEach(finding => {
        if (finding.toolCalls) {
            toolCount += finding.toolCalls.length;
            finding.toolCalls.forEach((tc: any) => {
                if (tc.toolName) {
                    dataSources.add(tc.toolName);
                }
            });
        }
    });
    
    // Count from direct tool calls if available
    if (toolCalls && Array.isArray(toolCalls)) {
        toolCount += toolCalls.length;
        toolCalls.forEach((tc: any) => {
            if (tc.tool) {
                dataSources.add(tc.tool);
            }
        });
    }
    
    const sourcesList = Array.from(dataSources);
    if (sourcesList.length > 0) {
        return `Analysis based on ${toolCount} data points from ${dataSources.size} sources (${sourcesList.join(', ')}).`;
    } else {
        return `Analysis completed using modular agent system with ${agentFindings.length} specialist agents.`;
    }
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

    // Layout function to position nodes in a logical flow
    const layoutNodes = (nodes: any[], edges: any[]) => {
        const nodeMap = new Map();
        const levels = new Map();
        
        // Create adjacency list
        const adjacencyList = new Map();
        nodes.forEach(node => {
            adjacencyList.set(node.id, []);
            nodeMap.set(node.id, node);
        });
        
        edges.forEach(edge => {
            if (adjacencyList.has(edge.from)) {
                adjacencyList.get(edge.from).push(edge.to);
            }
        });
        
        // Find root nodes (nodes with no incoming edges)
        const rootNodes = nodes.filter(node => 
            !edges.some(edge => edge.to === node.id)
        );
        
        // Assign levels using BFS
        const queue = [...rootNodes.map(node => ({ node, level: 0 }))];
        const visited = new Set();
        
        while (queue.length > 0) {
            const { node, level } = queue.shift()!;
            if (visited.has(node.id)) continue;
            
            visited.add(node.id);
            if (!levels.has(level)) levels.set(level, []);
            levels.get(level).push(node.id);
            
            // Add children to queue
            adjacencyList.get(node.id)?.forEach(childId => {
                if (!visited.has(childId)) {
                    queue.push({ node: nodeMap.get(childId), level: level + 1 });
                }
            });
        }
        
        // Position nodes
        const nodeWidth = 250;
        const nodeHeight = 120;
        const levelSpacing = 300;
        const nodeSpacing = 200;
        
        return nodes.map(node => {
            let level = 0;
            for (const [l, levelNodes] of levels.entries()) {
                if (levelNodes.includes(node.id)) {
                    level = l;
                    break;
                }
            }
            
            const levelNodes = levels.get(level) || [];
            const nodeIndex = levelNodes.indexOf(node.id);
            const levelWidth = levelNodes.length * nodeSpacing;
            const startX = -levelWidth / 2;
            
            return {
                ...node,
                position: {
                    x: startX + nodeIndex * nodeSpacing + 400, // Center offset
                    y: level * levelSpacing + 100
                }
            };
        });
    };

    // Update nodes and edges when workflow status changes
    useEffect(() => {
        console.log('[App] Workflow status changed:', {
            hasNodes: !!workflowStatus?.nodes,
            hasEdges: !!workflowStatus?.edges,
            hasWorkflowGraph: !!workflowStatus?.workflow_graph,
            nodeCount: workflowStatus?.nodes?.length || 0,
            edgeCount: workflowStatus?.edges?.length || 0,
            workflowGraphNodes: workflowStatus?.workflow_graph?.nodes?.length || 0,
            workflowGraphEdges: workflowStatus?.workflow_graph?.edges?.length || 0
        });
        
        // Extract nodes and edges from workflow_graph if available, otherwise use direct nodes/edges
        let nodesToUse = workflowStatus?.nodes;
        let edgesToUse = workflowStatus?.edges;
        
        if (workflowStatus?.workflow_graph?.nodes && workflowStatus?.workflow_graph?.edges) {
            nodesToUse = workflowStatus.workflow_graph.nodes;
            edgesToUse = workflowStatus.workflow_graph.edges;
            console.log('[App] Using workflow_graph data:', {
                nodeCount: nodesToUse.length,
                edgeCount: edgesToUse.length
            });
        }
        
        if (nodesToUse && edgesToUse) {
            // Layout the nodes
            const positionedNodes = layoutNodes(nodesToUse, edgesToUse);
            
            const typedNodes = positionedNodes.map((node: any) => ({
                id: node.id,
                type: node.type || 'default',
                position: node.position,
                data: {
                    label: node.label,
                    status: node.status || 'pending',
                    agent: node.agent,
                    details: node.details,
                    result: node.result,
                    error: node.error
                }
            }));
            
            // Convert edges from backend format (from/to) to React Flow format (source/target)
            const reactFlowEdges = edgesToUse.map((edge: any, index: number) => ({
                id: `edge-${index}`,
                source: edge.from,
                target: edge.to,
                type: 'default'
            }));
            
            console.log('[App] Setting nodes and edges:', {
                typedNodes: typedNodes,
                reactFlowEdges: reactFlowEdges,
                nodeCount: typedNodes.length,
                edgeCount: reactFlowEdges.length
            });
            
            setNodes(typedNodes as CustomNode[]);
            setEdges(reactFlowEdges);
            
            // Debug: Check if nodes are actually set
            setTimeout(() => {
                console.log('[App] After setting nodes/edges:', {
                    nodesLength: typedNodes.length,
                    edgesLength: reactFlowEdges.length,
                    firstNode: typedNodes[0],
                    firstEdge: reactFlowEdges[0]
                });
            }, 100);
        }
    }, [workflowStatus, setNodes, setEdges]);

    // Handle workflow completion and show report modal
    useEffect(() => {
        if (workflowStatus?.status === 'completed' && !reportGenerated) {
            console.log('[App] Workflow completed, status:', workflowStatus);
            
            // Handle enhanced workflow results
            let reportContent = 'Analysis completed successfully';
            let enhancedResult = null;

            console.log('[App] Processing workflow result:', {
                result: workflowStatus.result,
                resultType: typeof workflowStatus.result,
                hasEnhancedResult: !!workflowStatus.enhanced_result
            });

            // Check if this is an enhanced workflow result
            console.log('[App] Processing workflow result:', {
                result: workflowStatus.result,
                resultType: typeof workflowStatus.result,
                hasEnhancedResult: !!workflowStatus.enhanced_result,
                enhancedResultType: typeof workflowStatus.enhanced_result,
                resultKeys: workflowStatus.result ? Object.keys(workflowStatus.result) : [],
                enhancedResultKeys: workflowStatus.enhanced_result ? Object.keys(workflowStatus.enhanced_result) : []
            });
            
            if (workflowStatus.enhanced_result && typeof workflowStatus.enhanced_result === 'object') {
                // Enhanced result in separate field (primary path)
                enhancedResult = workflowStatus.enhanced_result;
                reportContent = enhancedResult.recommendation || enhancedResult.market_analysis || enhancedResult.content || 'Analysis completed';
            } else if (workflowStatus.result && typeof workflowStatus.result === 'object') {
                if (workflowStatus.result.ticker || workflowStatus.result.recommendation || workflowStatus.result.market_analysis) {
                    // Direct enhanced workflow format
                    enhancedResult = workflowStatus.result;
                    reportContent = enhancedResult.recommendation || enhancedResult.market_analysis || enhancedResult.content || 'Analysis completed';
                } else if (workflowStatus.result.enhanced_result) {
                    // Nested enhanced workflow format
                    enhancedResult = workflowStatus.result.enhanced_result;
                    reportContent = enhancedResult.recommendation || enhancedResult.market_analysis || enhancedResult.content || 'Analysis completed';
                }
            } else if (workflowStatus.result && typeof workflowStatus.result === 'string') {
                // Legacy format
                reportContent = workflowStatus.result;
            }

            console.log('[App] Enhanced result extracted:', enhancedResult);
            
            // Extract agent findings from the trace if available
            const agentFindings: AgentFinding[] = [];
            const agentInvocations: any[] = [];
            
            // Use agent_invocations from workflow status if available
            if (workflowStatus.agent_invocations && Array.isArray(workflowStatus.agent_invocations)) {
                for (const invocation of workflowStatus.agent_invocations) {
                    agentFindings.push({
                        agentName: invocation.agent,
                        specialization: 'Financial Analysis',
                        summary: invocation.task,
                        details: [],
                        toolCalls: []
                    });
                    
                    agentInvocations.push({
                        agentName: invocation.agent,
                        naturalLanguageTask: invocation.task,
                        toolCalls: [],
                        synthesizedResponse: 'Analysis completed',
                        status: invocation.status
                    });
                }
            } else if (workflowStatus.trace?.agent_results) {
                // Fallback to old format
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
                dataQualityNotes: generateDataQualityNotes(agentFindings, workflowStatus.tool_calls),
                executionTrace: {
                    fintelQueryAnalysis: workflowStatus.query || "",
                    agentInvocations: agentInvocations
                },
                result: enhancedResult || workflowStatus.result // Include the enhanced result for the ReportDisplay component
            };
            
            setCurrentReport(report);
            setReportGenerated(true); // Mark report as generated
            setIsReportModalVisible(true);
            
            console.log('[App] Report generated and modal opened:', {
                hasEnhancedResult: !!enhancedResult,
                reportContent: reportContent.substring(0, 100) + '...',
                agentFindingsCount: agentFindings.length,
                workflowStatus: workflowStatus.status,
                hasResult: !!workflowStatus.result,
                resultType: typeof workflowStatus.result
            });
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
        
        // Check if it's the final report node or any completed node
        if (node.id === 'enhanced_result' || node.data.status === 'completed') {
            console.log('Opening report modal for completed node');
            setIsReportModalVisible(true);
            return;
        }
        
        // Check if it's an agent node with data
        const hasAgentData = 'result' in node.data || 'error' in node.data || 'toolCalls' in node.data;
        
        if (hasAgentData) {
            console.log('Opening modal for agent node:', node.id);
            setSelectedNode(node);
        } else {
            console.log('Node not eligible for modal:', {
                id: node.id,
                type: node.type,
                status: node.data.status,
                hasAgentData
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
                    eventHistory={workflowStatus?.event_history || []}
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
