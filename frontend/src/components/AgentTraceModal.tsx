// components/AgentTraceModal.tsx - Updated to handle missing data
import React from 'react';
import { AgentNodeData, CustomNode, ToolCallResult } from '../types';
import XCircleIcon from './icons/XCircleIcon';
import CodeBracketIcon from './icons/CodeBracketIcon';

const DetailSection: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
    <section className="mb-6">
        <h4 className="text-lg font-semibold text-brand-text-primary mb-2 border-b border-brand-border pb-1">{title}</h4>
        <div className="text-sm text-brand-text-secondary p-3 bg-brand-bg rounded-md">
            {children}
        </div>
    </section>
);

const getSummaryStyling = (summary: string): { badge: string; badgeText: string; content: string } => {
    if (summary.startsWith('[LIVE]')) return { badge: 'bg-green-500/20 text-green-400', badgeText: 'LIVE', content: summary.replace('[LIVE] ', '') };
    if (summary.startsWith('[MOCK]')) return { badge: 'bg-yellow-500/20 text-yellow-400', badgeText: 'MOCK', content: summary.replace('[MOCK] ', '') };
    if (summary.startsWith('[SYNTHETIC]')) return { badge: 'bg-blue-500/20 text-blue-400', badgeText: 'SYNTHETIC', content: summary.replace('[SYNTHETIC] ', '') };
    if (summary.startsWith('[INTERNAL MOCK]')) return { badge: 'bg-purple-500/20 text-purple-400', badgeText: 'INTERNAL MOCK', content: summary.replace('[INTERNAL MOCK] ', '') };
    return { badge: 'bg-brand-border text-brand-text-secondary', badgeText: 'INFO', content: summary };
};

const ToolCallDisplay: React.FC<{ toolCall: ToolCallResult }> = ({ toolCall }) => {
    const prettyPrintJson = (data: any) => {
        try {
            const obj = typeof data === 'string' ? JSON.parse(data) : data;
            return JSON.stringify(obj, null, 2);
        } catch (e) {
            return String(data);
        }
    };

    const { badge, badgeText, content } = getSummaryStyling(toolCall.toolOutputSummary || '');

    return (
        <div className="bg-brand-bg border border-brand-border rounded-lg p-4 mb-4">
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center">
                    <CodeBracketIcon className="w-5 h-5 text-brand-primary mr-2" />
                    <h5 className="font-bold text-brand-primary">{toolCall.toolName}</h5>
                </div>
                <span className={`px-2 py-0.5 text-xs font-semibold rounded-full ${badge}`}>
                    {badgeText}
                </span>
            </div>

            <div className="mb-4">
                 <h6 className="font-semibold text-brand-text-secondary text-xs uppercase mb-1">Execution Summary</h6>
                 <p className="text-sm text-brand-text-primary p-2 bg-black/30 rounded">{content}</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <h6 className="font-semibold text-brand-text-secondary text-xs uppercase mb-1">Parameters</h6>
                    <pre className="bg-black/30 p-2 rounded text-xs text-brand-text-primary overflow-x-auto">
                        <code>{prettyPrintJson(toolCall.toolInput)}</code>
                    </pre>
                </div>
                <div>
                    <h6 className="font-semibold text-brand-text-secondary text-xs uppercase mb-1">Full Output</h6>
                    <pre className="bg-black/30 p-2 rounded text-xs text-brand-text-primary overflow-x-auto">
                        <code>{prettyPrintJson(toolCall.toolOutput)}</code>
                    </pre>
                </div>
            </div>
        </div>
    );
};

interface AgentTraceModalProps {
    node: CustomNode | null;
    onClose: () => void;
    // Enhanced event history for audit trails
    eventHistory?: Array<{
        event_type: string;
        timestamp: string;
        agent_name?: string;
        message_content?: string;
        tool_calls?: any[];
        tool_name?: string;
        tool_input?: any;
        tool_output?: any;
        task_id?: string;
        task_objective?: string;
        result?: string;
        error?: string;
    }>;
}

const AgentTraceModal: React.FC<AgentTraceModalProps> = ({ node, onClose, eventHistory = [] }) => {
    if (!node) return null;

    const { label, details, error, result, toolCalls = [] } = node.data as AgentNodeData;

    // Enhanced debugging to identify the duplication issue
    console.log('=== AgentTraceModal Debug Info ===');
    console.log('Node ID:', node.id);
    console.log('Label:', label);
    console.log('Details (should be task description):', details);
    console.log('Result (should be analysis output):', result);
    console.log('Details length:', details?.length || 0);
    console.log('Result length:', result?.length || 0);
    console.log('Are details and result the same?', details === result);
    console.log('Full node data:', node.data);
    console.log('Event History:', eventHistory);
    console.log('===================================');

    // CRITICAL FIX: Ensure details and result are not the same
    // If they are the same, it means the details field was overwritten with the result
    const isDetailsOverwritten = details === result && details && result;
    const safeDetails = isDetailsOverwritten ? null : details;
    
    // Generate fallback task description based on agent label
    const getFallbackTaskDescription = (agentLabel: string) => {
        if (agentLabel.includes('Market')) return 'Analyze market data, financial metrics, and trading patterns';
        if (agentLabel.includes('Risk')) return 'Assess investment risks and market volatility';
        if (agentLabel.includes('Financial')) return 'Provide comprehensive financial analysis and recommendations';
        if (agentLabel.includes('Economic')) return 'Analyze economic indicators and macroeconomic trends';
        return 'Perform specialized financial analysis';
    };

    const formatTimestamp = (timestamp: string) => {
        try {
            return new Date(timestamp).toLocaleString();
        } catch {
            return timestamp;
        }
    };

    const getEventIcon = (eventType: string) => {
        switch (eventType) {
            case 'task_start':
                return '🚀';
            case 'task_success':
                return '✅';
            case 'task_failure':
                return '❌';
            case 'agent_message':
                return '💭';
            case 'agent_tool_call':
                return '🔧';
            case 'tool_result':
                return '📊';
            default:
                return '📝';
        }
    };

    const getEventColor = (eventType: string) => {
        switch (eventType) {
            case 'task_start':
                return 'text-blue-400';
            case 'task_success':
                return 'text-green-400';
            case 'task_failure':
                return 'text-red-400';
            case 'agent_message':
                return 'text-purple-400';
            case 'agent_tool_call':
                return 'text-yellow-400';
            case 'tool_result':
                return 'text-cyan-400';
            default:
                return 'text-gray-400';
        }
    };

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-brand-surface border border-brand-border rounded-lg shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
                <div className="flex items-center justify-between p-6 border-b border-brand-border">
                    <h2 className="text-xl font-bold text-white flex items-center">
                        <span className="mr-2">🔍</span>
                        Agent Trace: {label}
                    </h2>
                    <button
                        onClick={onClose}
                        className="text-brand-text-secondary hover:text-white transition-colors"
                    >
                        <XCircleIcon className="w-6 h-6" />
                    </button>
                </div>

                <div className="overflow-y-auto max-h-[calc(90vh-120px)] p-6">
                    {/* Agent Overview */}
                    <DetailSection title="Agent Overview">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <strong>Agent Name:</strong> {label}
                            </div>
                            <div>
                                <strong>Status:</strong> {error ? 'Failed' : result ? 'Completed' : 'Running'}
                            </div>
                            <div className="md:col-span-2">
                                <strong>Task Description:</strong> {safeDetails || getFallbackTaskDescription(label)}
                            </div>
                        </div>
                    </DetailSection>

                    {/* Event Timeline */}
                    {eventHistory.length > 0 && (
                        <DetailSection title="Execution Timeline">
                            <div className="space-y-3">
                                {eventHistory.map((event, index) => (
                                    <div key={index} className="flex items-start space-x-3 p-3 bg-brand-bg/50 rounded-lg border border-brand-border">
                                        <div className={`text-lg ${getEventColor(event.event_type)}`}>
                                            {getEventIcon(event.event_type)}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center justify-between mb-1">
                                                <span className="font-medium text-white capitalize">
                                                    {event.event_type.replace('_', ' ')}
                                                </span>
                                                <span className="text-xs text-brand-text-secondary">
                                                    {formatTimestamp(event.timestamp)}
                                                </span>
                                            </div>
                                            
                                            {/* Event-specific details */}
                                            {event.event_type === 'agent_message' && event.message_content && (
                                                <div className="text-sm text-brand-text-secondary bg-black/30 p-2 rounded">
                                                    <strong>Reasoning:</strong> {event.message_content}
                                                </div>
                                            )}
                                            
                                            {event.event_type === 'agent_tool_call' && event.tool_name && (
                                                <div className="text-sm text-brand-text-secondary">
                                                    <strong>Tool:</strong> {event.tool_name}
                                                    {event.tool_input && (
                                                        <div className="mt-1 bg-black/30 p-2 rounded text-xs">
                                                            <strong>Input:</strong> {JSON.stringify(event.tool_input, null, 2)}
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                            
                                            {event.event_type === 'tool_result' && event.tool_output && (
                                                <div className="text-sm text-brand-text-secondary">
                                                    <strong>Output:</strong> 
                                                    <div className="mt-1 bg-black/30 p-2 rounded text-xs overflow-x-auto">
                                                        {typeof event.tool_output === 'string' 
                                                            ? event.tool_output 
                                                            : JSON.stringify(event.tool_output, null, 2)}
                                                    </div>
                                                </div>
                                            )}
                                            
                                            {event.event_type === 'task_success' && event.result && (
                                                <div className="text-sm text-green-400 bg-green-900/20 p-2 rounded">
                                                    <strong>Result:</strong> {event.result}
                                                </div>
                                            )}
                                            
                                            {event.event_type === 'task_failure' && event.error && (
                                                <div className="text-sm text-red-400 bg-red-900/20 p-2 rounded">
                                                    <strong>Error:</strong> {event.error}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </DetailSection>
                    )}

                    {/* Tool Calls */}
                    {toolCalls.length > 0 && (
                        <DetailSection title="Tool Executions">
                            {toolCalls.map((toolCall, index) => (
                                <ToolCallDisplay key={index} toolCall={toolCall} />
                            ))}
                        </DetailSection>
                    )}

                    {/* Final Result */}
                    {result && (
                        <DetailSection title="Final Analysis">
                            <div className="bg-green-900/20 border border-green-700/50 rounded-lg p-4">
                                <div className="text-green-300 font-medium mb-2">Analysis Result</div>
                                <div className="text-white whitespace-pre-wrap">{result}</div>
                            </div>
                        </DetailSection>
                    )}

                    {/* Error Information */}
                    {error && (
                        <DetailSection title="Error Details">
                            <div className="bg-red-900/20 border border-red-700/50 rounded-lg p-4">
                                <div className="text-red-300 font-medium mb-2">Error Information</div>
                                <div className="text-red-200 whitespace-pre-wrap">{error}</div>
                            </div>
                        </DetailSection>
                    )}
                </div>
            </div>
        </div>
    );
};

export default AgentTraceModal;
