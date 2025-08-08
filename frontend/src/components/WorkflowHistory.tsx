import React from 'react';

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
    const [isClearing, setIsClearing] = React.useState(false);
      const skipIdRef = React.useRef<string | null>(null);
    
    // Load history from localStorage
    React.useEffect(() => {
        const savedHistory = localStorage.getItem('workflowHistory');
        if (savedHistory) {
            setHistory(JSON.parse(savedHistory));
        }
    }, []);
    
    // Add or refresh workflow in history
    React.useEffect(() => {
        if (currentWorkflowId) {
            fetch(`/api/workflow-status/${currentWorkflowId}`)
                .then(res => res.json())
                .then(data => {
                    // If user just cleared, don't immediately re-add the same active workflow
                    if (skipIdRef.current && currentWorkflowId === skipIdRef.current) {
                        return;
                    }
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
                .catch(() => {});
        }
    }, [currentWorkflowId]);

    const handleClearHistory = () => {
        setIsClearing(true);
        try {
            localStorage.removeItem('workflowHistory');
            setHistory([]);
          // Avoid immediate re-population when a workflow is running
          skipIdRef.current = currentWorkflowId;
            // Close the panel to avoid any overlapping UI state or pending refresh timers
            setIsOpen(false);
        } finally {
            setIsClearing(false);
        }
    };
    
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
                    <div className="flex justify-between items-center mb-3">
                        <span className="text-xs text-brand-text-secondary">Stored locally</span>
                        <button
                            onClick={handleClearHistory}
                            disabled={isClearing}
                            className="text-xs text-brand-text-secondary hover:text-brand-text-primary underline disabled:opacity-50"
                        >
                            {isClearing ? 'Clearing…' : 'Clear history'}
                        </button>
                    </div>
                    {/* Refresh statuses on open */}
                    <AutoRefresher 
                        items={history} 
                        onRefresh={(updated) => setHistory(updated)} 
                        disabled={!isOpen || isClearing}
                    />
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

// Lightweight refresher component: fetches latest statuses when panel opens
const AutoRefresher: React.FC<{ items: WorkflowHistoryItem[]; onRefresh: (items: WorkflowHistoryItem[]) => void; disabled?: boolean }> = ({ items, onRefresh, disabled = false }) => {
    React.useEffect(() => {
        let mounted = true;
        if (disabled) {
            return () => { mounted = false; };
        }
        const refresh = async () => {
            try {
                const refreshed: WorkflowHistoryItem[] = await Promise.all(items.map(async (it) => {
                    try {
                        const res = await fetch(`/api/workflow-status/${it.id}`);
                        if (res.status === 404) {
                            // Prune entries that no longer exist on the backend
                            return null as any;
                        }
                        const data = await res.json();
                        return { ...it, status: data.status as any };
                    } catch {
                        return it;
                    }
                }));
                const filtered = refreshed.filter(Boolean) as WorkflowHistoryItem[];
                if (mounted) {
                    localStorage.setItem('workflowHistory', JSON.stringify(filtered));
                    onRefresh(filtered);
                }
            } catch {}
        };
        refresh();
        const t = setInterval(refresh, 15000);
        return () => { mounted = false; clearInterval(t); };
    }, [items, onRefresh, disabled]);
    return null;
};

export default WorkflowHistory;