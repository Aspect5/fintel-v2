
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

    useEffect(() => {
        const fetchTools = async () => {
            try {
                const response = await fetch('/api/tools');
                const data: Tool[] = await response.json();
                setTools(data);
            } catch (error) {
                console.error("Failed to fetch tools:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchTools();
    }, []);

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
