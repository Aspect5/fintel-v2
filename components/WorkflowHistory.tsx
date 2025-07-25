import React from 'react';
import { ChatMessage } from '../types';

interface WorkflowHistoryItem {
    id: string;
    query: string;
    timestamp: string;
    status: 'completed' | 'failed' | 'running';
}

interface WorkflowHistoryProps {
    currentWorkflowId: string | null;
    onSelectWorkflow: (workflowId: string) => void;
}

const WorkflowHistory: React.FC<WorkflowHistoryProps> = ({ 
    currentWorkflowId, 
    onSelectWorkflow 
}) => {
    const [history, setHistory] = React.useState<WorkflowHistoryItem[]>([]);
    const [isOpen, setIsOpen] = React.useState(false);
    
    // Load history from localStorage
    React.useEffect(() => {
        const savedHistory = localStorage.getItem('workflowHistory');
        if (savedHistory) {
            setHistory(JSON.parse(savedHistory));
        }
    }, []);
    
    // Add new workflow to history
    React.useEffect(() => {
        if (currentWorkflowId) {
            fetch(`/api/workflow-status/${currentWorkflowId}`)
                .then(res => res.json())
                .then(data => {
                    if (data.query) {
                        const newItem: WorkflowHistoryItem = {
                            id: currentWorkflowId,
                            query: data.query,
                            timestamp: new Date().toISOString(),
                            status: data.status
                        };
                        
                        setHistory(prev => {
                            const updated = [newItem, ...prev.filter(item => item.id !== currentWorkflowId)].slice(0, 10);
                            localStorage.setItem('workflowHistory', JSON.stringify(updated));
                            return updated;
                        });
                    }
                })
                .catch(console.error);
        }
    }, [currentWorkflowId]);
    
    return (
        <div className="absolute top-4 right-4 z-20">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="bg-brand-surface px-4 py-2 rounded-lg shadow-lg hover:bg-brand-border transition-colors flex items-center space-x-2"
            >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>History</span>
            </button>
            
            {isOpen && (
                <div className="absolute top-12 right-0 bg-brand-surface rounded-lg shadow-xl p-4 w-80 max-h-96 overflow-y-auto">
                    <h3 className="text-lg font-semibold mb-3">Recent Workflows</h3>
                    {history.length === 0 ? (
                        <p className="text-brand-text-secondary text-sm">No previous workflows</p>
                    ) : (
                        <div className="space-y-2">
                            {history.map(item => (
                                <button
                                    key={item.id}
                                    onClick={() => onSelectWorkflow(item.id)}
                                    className={`w-full text-left p-3 rounded-lg transition-colors ${
                                        item.id === currentWorkflowId 
                                            ? 'bg-brand-primary text-white' 
                                            : 'bg-brand-bg hover:bg-brand-border'
                                    }`}
                                >
                                    <div className="font-medium text-sm">{item.query}</div>
                                    <div className="text-xs text-brand-text-secondary mt-1">
                                        {new Date(item.timestamp).toLocaleString()}
                                        <span className={`ml-2 ${
                                            item.status === 'completed' ? 'text-green-400' :
                                            item.status === 'failed' ? 'text-red-400' :
                                            'text-yellow-400'
                                        }`}>
                                            • {item.status}
                                        </span>
                                    </div>
                                </button>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default WorkflowHistory;