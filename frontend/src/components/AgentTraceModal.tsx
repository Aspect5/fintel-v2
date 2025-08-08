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

const detectFormat = (data: any): string => {
    try {
        if (data === null || data === undefined) return 'None';
        if (typeof data === 'number') return 'Number';
        if (typeof data === 'boolean') return 'Boolean';
        if (Array.isArray(data)) return 'Array';
        if (typeof data === 'object') return 'Object';
        if (typeof data === 'string') {
            const trimmed = data.trim();
            if ((trimmed.startsWith('{') && trimmed.endsWith('}')) || (trimmed.startsWith('[') && trimmed.endsWith(']'))) {
                try { JSON.parse(trimmed); return 'JSON string'; } catch {}
            }
            // Naive CSV detector: lines with consistent commas
            const lines = trimmed.split(/\r?\n/).filter(l => l.length > 0);
            if (lines.length >= 1 && lines.every(l => (l.match(/,/g)?.length || 0) >= 1)) {
                return 'CSV text';
            }
            return 'Text';
        }
        return typeof data;
    } catch {
        return 'Unknown';
    }
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
    // Derive LIVE/MOCK badge from tool output
    const isMock = (() => {
        try {
            const out = toolCall.toolOutput;
            if (!out) return false;
            const obj = typeof out === 'string' ? JSON.parse(out) : out;
            if (obj && typeof obj === 'object') {
                if ((obj as any)._mock === true) return true;
                const note = (obj as any).note || (obj as any).notes || '';
                if (typeof note === 'string' && note.toLowerCase().includes('mock')) return true;
            }
        } catch {}
        return false;
    })();

    return (
                <div className={`border rounded-lg p-4 mb-4 ${content.toLowerCase().startsWith('error') ? 'bg-red-500/10 border-red-500/40' : 'bg-brand-bg border-brand-border'}`}>
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center">
                    <CodeBracketIcon className="w-5 h-5 text-brand-primary mr-2" />
                    <h5 className="font-bold text-brand-primary">{toolCall.toolName}</h5>
                </div>
                <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 text-xs font-semibold rounded-full ${isMock ? 'bg-yellow-500/20 text-yellow-400' : 'bg-green-500/20 text-green-400'}`}>
                        {isMock ? 'MOCK' : 'LIVE'}
                    </span>
                    <span className={`px-2 py-0.5 text-xs font-semibold rounded-full ${badge}`}>
                        {badgeText}
                    </span>
                </div>
            </div>

            <div className="mb-4">
                 <h6 className="font-semibold text-brand-text-secondary text-xs uppercase mb-1">Execution Summary</h6>
                  <p className={`text-sm p-2 rounded ${content.toLowerCase().startsWith('error') ? 'bg-red-500/20 text-red-300 border border-red-500/40' : 'bg-black/30 text-brand-text-primary'}`}>{content}</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <div className="flex items-center justify-between mb-1">
                        <h6 className="font-semibold text-brand-text-secondary text-xs uppercase">Parameters</h6>
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-brand-border text-brand-text-secondary">{detectFormat(toolCall.toolInput)}</span>
                    </div>
                    <pre className="bg-black/30 p-2 rounded text-xs text-brand-text-primary overflow-x-auto">
                        <code>{prettyPrintJson(toolCall.toolInput)}</code>
                    </pre>
                </div>
                <div>
                    <div className="flex items-center justify-between mb-1">
                        <h6 className="font-semibold text-brand-text-secondary text-xs uppercase">Full Output</h6>
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-brand-border text-brand-text-secondary">{detectFormat(toolCall.toolOutput)}</span>
                    </div>
                    <pre className={`${(typeof toolCall.toolOutput === 'string' && toolCall.toolOutput.toLowerCase().startsWith('error')) ? 'bg-red-500/20 text-red-300 border border-red-500/40' : 'bg-black/30 text-brand-text-primary'} p-2 rounded text-xs overflow-x-auto`}>
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

    const { label, details, error, result, toolCalls = [], taskId, status, summary, agentName } = node.data as AgentNodeData & { taskId?: string; status?: string; summary?: string; agentName?: string };

    const pretty = (data: any) => {
        try {
            if (typeof data === 'string') return data;
            return JSON.stringify(data, null, 2);
        } catch {
            return String(data);
        }
    };

    // Enhanced debugging to identify the duplication issue
    const DEBUG = import.meta.env.MODE === 'development' && (window as any).__DEBUG__;
    if (DEBUG) {
      console.log('=== AgentTraceModal Debug Info ===');
      console.log('Node ID:', node.id);
      console.log('Label:', label);
      console.log('Details (should be task description):', details);
      console.log('Result (should be analysis output):', result);
      console.log('Details length:', (details as any)?.length || 0);
      console.log('Result length:', (result as any)?.length || 0);
      console.log('Are details and result the same?', details === result);
      console.log('Full node data:', node.data);
      console.log('Event History (size only):', Array.isArray(eventHistory) ? eventHistory.length : 0);
      console.log('TaskId from node:', taskId);
      console.log('===================================');
    }

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

    // Filter event history for this node: match by taskId if present, otherwise by agentName
    const filteredEvents = Array.isArray(eventHistory)
        ? eventHistory.filter((e: any) => {
            const byTask = taskId && e.task_id === taskId;
            const byAgent = agentName && e.agent_name === agentName;
            // Allow role correlation to capture correct events when task_id missing
            const byRole = (node?.id?.startsWith?.('task_') && e?.agent_role) ? e.agent_role === (node.id as string).replace('task_', '') : false;
            return Boolean(byTask || byAgent || byRole);
          })
        : [];

    // Derive tool call list from filtered events if node doesn't provide explicit toolCalls
    const derivedToolCalls = filteredEvents
        .filter((e) => e.event_type === 'agent_tool_call' && !(e as any).is_internal_controlflow_tool)
        .map((e) => ({
            toolName: (e.tool_name as string) || 'unknown',
            toolInput: e.tool_input,
            toolOutput: e.tool_output,
            toolOutputSummary: e.tool_output ? (typeof e.tool_output === 'string' ? e.tool_output : JSON.stringify(e.tool_output)) : 'No output'
        }));
    const toolCallsToShow = (toolCalls && toolCalls.length > 0) ? toolCalls : derivedToolCalls;

    // Collect inputs received by the agent (messages and tool inputs)
    const agentInputEvents = filteredEvents.filter((e) => e.event_type === 'agent_message' || e.event_type === 'agent_tool_call');

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
                                <strong>Status:</strong> {status ? status.charAt(0).toUpperCase() + status.slice(1) : (error ? 'Failed' : result ? 'Completed' : 'Running')}
                            </div>
                            <div className="md:col-span-2">
                                <strong>Task Description:</strong> {safeDetails || getFallbackTaskDescription(label)}
                            </div>
                            {summary && (
                              <div className="md:col-span-2">
                                <strong>Summary:</strong> {(() => {
                                  const s = String(summary);
                                  return s === 'buy' ? 'Buy' : s;
                                })()}
                              </div>
                            )}
                        </div>
                    </DetailSection>

                    {/* Inputs Received */}
                    <DetailSection title="Inputs Received">
                        {agentInputEvents.length === 0 ? (
                            <div className="text-sm text-brand-text-secondary">No explicit inputs recorded.</div>
                        ) : (
                            <div className="space-y-3">
                                {agentInputEvents.map((e, idx) => (
                                    <div key={idx} className="p-3 bg-brand-bg/50 rounded border border-brand-border">
                                        <div className="flex items-center justify-between mb-2">
                                            <div className="text-sm font-medium text-white">
                                                {e.event_type === 'agent_message' ? 'Agent Message' : `Tool Input: ${e.tool_name || 'unknown'}`}
                                            </div>
                                            <span className="text-[10px] px-2 py-0.5 rounded-full bg-brand-border text-brand-text-secondary">
                                                {e.event_type === 'agent_message' ? detectFormat(e.message_content) : detectFormat(e.tool_input)}
                                            </span>
                                        </div>
                                        <pre className="bg-black/30 p-2 rounded text-xs text-brand-text-primary overflow-x-auto">
                                            <code>{(() => {
                                                const src = e.event_type === 'agent_message' ? e.message_content : e.tool_input;
                                                try {
                                                    if (typeof src === 'string') {
                                                        const trimmed = src.trim();
                                                        if ((trimmed.startsWith('{') && trimmed.endsWith('}')) || (trimmed.startsWith('[') && trimmed.endsWith(']'))) {
                                                            return JSON.stringify(JSON.parse(trimmed), null, 2);
                                                        }
                                                    }
                                                } catch {}
                                                return typeof src === 'object' ? JSON.stringify(src, null, 2) : String(src);
                                            })()}</code>
                                        </pre>
                                    </div>
                                ))}
                            </div>
                        )}
                    </DetailSection>

                    {/* Execution Timeline (merged view) */}
                    {filteredEvents.length > 0 && (
                        <DetailSection title="Execution Timeline">
                            <div className="space-y-3">
                                {filteredEvents.map((event, index) => (
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
                                            {/* Agent Message */}
                                            {event.event_type === 'agent_message' && (
                                                <div className="text-sm text-brand-text-secondary bg-black/30 p-2 rounded">
                                                    <strong>Reasoning:</strong> {event.message_content || 'No textual reasoning (tool-only step)'}
                                                </div>
                                            )}
                                            {/* Tool Call */}
                                            {event.event_type === 'agent_tool_call' && event.tool_name && (
                                                <div className="text-sm text-brand-text-secondary">
                                    <div className="flex items-center gap-2">
                                                        <strong>Tool:</strong>
                                                        <span>{event.tool_name}</span>
                                                        {Boolean((event as any).is_internal_controlflow_tool) && (
                                                            <span className="text-[10px] px-2 py-0.5 rounded-full bg-brand-border text-brand-text-secondary">Controlflow Internal Tool</span>
                                                        )}
                                        {/* Live/Mock badge based on output content */}
                                        {(() => {
                                            const out = (event as any).tool_output;
                                            const isMock = (() => {
                                                try {
                                                    if (!out) return false;
                                                    const obj = typeof out === 'string' ? JSON.parse(out) : out;
                                                    if (obj && typeof obj === 'object') {
                                                        if (obj._mock === true) return true;
                                                        const note = obj.note || obj.notes || '';
                                                        if (typeof note === 'string' && note.toLowerCase().includes('mock')) return true;
                                                    }
                                                } catch {}
                                                return false;
                                            })();
                                            return (
                                                <span className={`text-[10px] px-2 py-0.5 rounded-full ${isMock ? 'bg-yellow-500/20 text-yellow-400' : 'bg-green-500/20 text-green-400'}`}>
                                                    {isMock ? 'MOCK' : 'LIVE'}
                                                </span>
                                            );
                                        })()}
                                                    </div>
                                                    {event.tool_input && (
                                                        <div className="mt-1 bg-black/30 p-2 rounded text-xs">
                                                            <strong>Input:</strong> {JSON.stringify(event.tool_input, null, 2)}
                                                        </div>
                                                    )}
                                                    {event.tool_output !== undefined && (
                                                        <div className={`mt-1 p-2 rounded text-xs ${((event as any).is_error || (typeof event.tool_output === 'string' && event.tool_output.toLowerCase().startsWith('error'))) ? 'bg-red-500/20 text-red-300 border border-red-500/40' : 'bg-black/30'}`}>
                                                            <strong>Output:</strong> {event.tool_output === null ? 'No output' : (typeof event.tool_output === 'string' ? event.tool_output : JSON.stringify(event.tool_output, null, 2))}
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                            {/* Tool Result (if present as standalone) */}
                                            {event.event_type === 'tool_result' && (
                                                <div className="text-sm text-brand-text-secondary">
                                                    <div className="flex items-center gap-2">
                                                        <strong>Tool:</strong>
                                                        <span>{event.tool_name}</span>
                                                        {Boolean((event as any).is_internal_controlflow_tool) && (
                                                            <span className="text-[10px] px-2 py-0.5 rounded-full bg-brand-border text-brand-text-secondary">Controlflow Internal Tool</span>
                                                        )}
                                                        {(() => {
                                                            const out = (event as any).result;
                                                            const isMock = (() => {
                                                                try {
                                                                    if (!out) return false;
                                                                    const obj = typeof out === 'string' ? JSON.parse(out) : out;
                                                                    if (obj && typeof obj === 'object') {
                                                                        if (obj._mock === true) return true;
                                                                        const note = obj.note || obj.notes || '';
                                                                        if (typeof note === 'string' && note.toLowerCase().includes('mock')) return true;
                                                                    }
                                                                } catch {}
                                                                return false;
                                                            })();
                                                            return (
                                                                <span className={`text-[10px] px-2 py-0.5 rounded-full ${isMock ? 'bg-yellow-500/20 text-yellow-400' : 'bg-green-500/20 text-green-400'}`}>
                                                                    {isMock ? 'MOCK' : 'LIVE'}
                                                                </span>
                                                            );
                                                        })()}
                                                    </div>
                                                    <div className="mt-1 bg-black/30 p-2 rounded text-xs">
                                                        <strong>Output:</strong> {event.result ? event.result : 'No output'}
                                                    </div>
                                                </div>
                                            )}
                                            {/* Task Success/Failure */}
                                            {event.event_type === 'task_success' && (
                                                <div className="text-sm text-green-400 bg-green-900/20 p-2 rounded">
                                                    <strong>Result:</strong> {event.result}
                                                </div>
                                            )}
                                            {event.event_type === 'task_failure' && (
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

                    {/* Tool Calls (single source of truth: derived from event history) */}
                    {toolCallsToShow.length > 0 && (
                        <DetailSection title="Tool Executions">
                            {toolCallsToShow.map((toolCall, index) => (
                                <ToolCallDisplay key={index} toolCall={toolCall} />
                            ))}
                        </DetailSection>
                    )}

                    {/* Final Result */}
                    {result && (
                        <DetailSection title="Final Analysis">
                            <div className="bg-green-900/20 border border-green-700/50 rounded-lg p-4">
                                <div className="text-green-300 font-medium mb-2">Analysis Result</div>
                                <pre className="text-white whitespace-pre-wrap text-xs overflow-x-auto">
{pretty(result)}
                                </pre>
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
