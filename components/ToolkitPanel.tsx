import React, { useEffect, useState } from 'react';
import CodeBracketIcon from './icons/CodeBracketIcon';

interface Tool {
  name: string;
  description: string;
}

const ToolCard: React.FC<{ tool: Tool }> = ({ tool }) => (
    <div className="bg-brand-bg p-4 rounded-lg border border-brand-border mb-4 transition-shadow hover:shadow-lg hover:border-brand-primary/50">
        <div className="flex items-center mb-2">
            <CodeBracketIcon className="w-5 h-5 text-brand-primary mr-3 flex-shrink-0" />
            <h4 className="font-bold text-brand-text-primary">{tool.name}</h4>
        </div>
        <p className="text-sm text-brand-text-secondary mb-3 pl-8">{tool.description}</p>
    </div>
);

const ToolkitPanel: React.FC = () => {
    const [tools, setTools] = useState<Tool[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchTools = async () => {
            try {
                const response = await fetch('/api/tools');
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                const data = await response.json();
                
                if (Array.isArray(data)) {
                    setTools(data);
                } else {
                    console.error("Expected array but got:", data);
                    setError("Invalid data format received from server");
                }
            } catch (error) {
                console.error("Failed to fetch tools:", error);
                setError(error instanceof Error ? error.message : "Unknown error occurred");
            } finally {
                setLoading(false);
            }
        };

        fetchTools();
    }, []);

    if (error) {
        return (
            <div className="p-4 text-red-400">
                <h3 className="text-lg font-semibold mb-2">Error Loading Tools</h3>
                <p className="text-sm">{error}</p>
                <button 
                    onClick={() => window.location.reload()} 
                    className="mt-2 px-3 py-1 bg-red-600 text-white rounded text-sm"
                >
                    Retry
                </button>
            </div>
        );
    }

    return (
        <div className="p-4 h-full overflow-y-auto">
             <style>{`
                .animate-slide-in {
                    animation: slide-in 0.5s ease-out forwards;
                }
                @keyframes slide-in {
                    from {
                        opacity: 0;
                        transform: translateX(-10px);
                    }
                    to {
                        opacity: 1;
                        transform: translateX(0);
                    }
                }
             `}</style>
            <div className="animate-slide-in">
                <h3 className="text-lg font-semibold text-brand-text-primary mb-4 px-2">Available Tools</h3>
                {loading ? (
                    <p className="text-brand-text-secondary">Loading tools...</p>
                ) : (
                    tools.map(tool => (
                        <ToolCard key={tool.name} tool={tool} />
                    ))
                )}
            </div>
        </div>
    );
};

export default ToolkitPanel;