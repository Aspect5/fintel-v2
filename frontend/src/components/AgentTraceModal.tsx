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
}

const AgentTraceModal: React.FC<AgentTraceModalProps> = ({ node, onClose }) => {
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
    console.log('===================================');

    return (
        <div 
            className="fixed inset-0 bg-black/80 z-[9999] flex items-center justify-center animate-fade-in" 
            onClick={onClose}
        >
            <div 
                className="w-full max-w-4xl h-[90vh] bg-brand-surface rounded-lg shadow-2xl overflow-y-auto flex flex-col m-4" 
                onClick={e => e.stopPropagation()}
            >
                <header className="flex items-center justify-between p-4 border-b border-brand-border sticky top-0 bg-brand-surface z-10">
                    <h3 className="text-xl font-bold text-white">Agent Details: {label}</h3>
                    <button onClick={onClose} className="text-brand-text-secondary hover:text-white">
                        <XCircleIcon className="w-7 h-7" />
                    </button>
                </header>
                
                <div className="p-6">
                    {error && (
                        <DetailSection title="Error">
                            <p className="text-brand-danger font-mono">{error}</p>
                        </DetailSection>
                    )}

                    {details && (
                        <DetailSection title="Agent Task">
                            <p>{details}</p>
                        </DetailSection>
                    )}

                    <DetailSection title="Tool Execution">
                        {toolCalls.length > 0 ? (
                            toolCalls.map((tc: ToolCallResult, index: number) => <ToolCallDisplay key={index} toolCall={tc} />)
                        ) : (
                            <p className="italic">No tool calls were executed for this task.</p>
                        )}
                    </DetailSection>
                    
                    <DetailSection title="Final Response">
                        {result ? (
                             <pre className="whitespace-pre-wrap font-sans">{result}</pre>
                        ) : (
                             <p className="italic">No final response was synthesized.</p>
                        )}
                    </DetailSection>
                </div>
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
    );
};

export default AgentTraceModal;
