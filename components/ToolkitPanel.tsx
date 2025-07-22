
import React from 'react';
import { toolRegistry } from '../tools/financialTools';
import { Tool } from '../tools/toolTypes';
import CodeBracketIcon from './icons/CodeBracketIcon';

const ToolCard: React.FC<{ tool: Tool }> = ({ tool }) => (
    <div className="bg-brand-bg p-4 rounded-lg border border-brand-border mb-4 transition-shadow hover:shadow-lg hover:border-brand-primary/50">
        <div className="flex items-center mb-2">
            <CodeBracketIcon className="w-5 h-5 text-brand-primary mr-3 flex-shrink-0" />
            <h4 className="font-bold text-brand-text-primary">{tool.name}</h4>
        </div>
        <p className="text-sm text-brand-text-secondary mb-3 pl-8">{tool.description}</p>
        <div>
            <h5 className="text-xs font-semibold text-brand-text-secondary uppercase mb-2 pl-8">Parameters</h5>
            <div className="space-y-2 text-xs p-3 bg-black/20 rounded ml-8">
                {Object.entries(tool.parameters.properties).map(([paramName, paramDef]) => (
                     <div key={paramName}>
                        <span className="font-mono text-brand-primary">{paramName}</span>
                        <span className="font-mono text-brand-text-secondary">: {paramDef.type}</span>
                        {tool.parameters.required?.includes(paramName) && <span className="text-brand-danger text-xs ml-2 font-semibold">(required)</span>}
                        <p className="text-brand-text-secondary pl-2 italic">{paramDef.description}</p>
                    </div>
                ))}
                 {Object.keys(tool.parameters.properties).length === 0 && <p className="text-brand-text-secondary italic">No parameters required.</p>}
            </div>
        </div>
    </div>
);

const ToolkitPanel: React.FC = () => {
    const tools = Array.from(toolRegistry.values());

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
                {tools.map(tool => (
                    <ToolCard key={tool.name} tool={tool} />
                ))}
            </div>
        </div>
    );
};

export default ToolkitPanel;
