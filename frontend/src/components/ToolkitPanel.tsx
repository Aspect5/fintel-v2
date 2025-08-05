import React, { useEffect, useState } from 'react';
import CodeBracketIcon from './icons/CodeBracketIcon';
import { getTools, getRegistryHealth, ToolInfo, RegistryHealth } from '../../services/apiService';

interface ToolDetails {
  args: Record<string, any>;
  returns: string;
  examples: string[];
}

interface Tool {
  name: string;
  summary: string;
  details: ToolDetails;
  type: string;
  capable_agents?: string[];
  category?: string;
  enabled?: boolean;
  api_key_required?: string;
  validation_status?: string;
}

const AgentCapabilities: React.FC<{ agents: string[] }> = ({ agents }) => {
  if (!agents || agents.length === 0) {
    return (
      <div className="pl-8 mb-3">
        <h5 className="font-semibold text-brand-text-secondary text-sm mb-2 flex items-center">
          <span className="w-2 h-2 bg-gray-400 rounded-full mr-2"></span>
          Capable Agents
        </h5>
        <p className="text-xs text-brand-text-tertiary italic">No agents can use this tool</p>
      </div>
    );
  }

  return (
    <div className="pl-8 mb-3">
      <h5 className="font-semibold text-brand-text-primary text-sm mb-2 flex items-center">
        <span className="w-2 h-2 bg-purple-500 rounded-full mr-2"></span>
        Capable Agents
      </h5>
      <div className="flex flex-wrap gap-2">
        {agents.map((agentName) => (
          <span 
            key={agentName}
            className="inline-block px-2 py-1 text-xs bg-purple-600 text-white rounded-full font-medium hover:bg-purple-700 transition-colors"
            title={`${agentName} can use this tool`}
          >
            {agentName}
          </span>
        ))}
      </div>
    </div>
  );
};

const ToolStatusBadge: React.FC<{ tool: Tool }> = ({ tool }) => {
  if (!tool.enabled) {
    return (
      <span className="inline-block px-2 py-1 text-xs bg-red-600 text-white rounded-full font-medium">
        Disabled
      </span>
    );
  }

  if (tool.api_key_required) {
    return (
      <span className="inline-block px-2 py-1 text-xs bg-yellow-600 text-white rounded-full font-medium" 
            title={`Requires ${tool.api_key_required} API key`}>
        API Key Required
      </span>
    );
  }

  return (
    <span className="inline-block px-2 py-1 text-xs bg-green-600 text-white rounded-full font-medium">
      Available
    </span>
  );
};

const ToolCard: React.FC<{ tool: Tool }> = ({ tool }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    
    return (
        <div className={`bg-brand-bg p-4 rounded-lg border border-brand-border mb-4 transition-shadow hover:shadow-lg hover:border-brand-primary/50 ${
            !tool.enabled ? 'opacity-60' : ''
        }`}>
            <div className="flex items-center mb-2">
                <CodeBracketIcon className="w-5 h-5 text-brand-primary mr-3 flex-shrink-0" />
                <div className="flex-grow">
                    <h4 className="font-bold text-brand-text-primary">{tool.name}</h4>
                    {tool.category && (
                        <span className="text-xs text-brand-text-tertiary bg-brand-bg-secondary px-2 py-1 rounded">
                            {tool.category}
                        </span>
                    )}
                </div>
                <div className="flex items-center gap-2">
                    <ToolStatusBadge tool={tool} />
                    <button
                        onClick={() => setIsExpanded(!isExpanded)}
                        className="text-brand-text-secondary hover:text-brand-primary text-sm px-2 py-1 rounded transition-colors"
                        title={isExpanded ? "Collapse details" : "Expand details"}
                    >
                        {isExpanded ? '▼' : '▶'}
                    </button>
                </div>
            </div>
            <p className="text-sm text-brand-text-secondary mb-3 pl-8 leading-relaxed">{tool.summary}</p>
            
            {/* Agent Capabilities - Always Visible */}
            <AgentCapabilities agents={tool.capable_agents || []} />
                        
            {isExpanded && (
                <div className="pl-8 space-y-4 border-l-2 border-brand-border ml-2">
                    {/* API Key Requirement */}
                    {tool.api_key_required && (
                        <div>
                            <h5 className="font-semibold text-brand-text-primary text-sm mb-2 flex items-center">
                                <span className="w-2 h-2 bg-yellow-500 rounded-full mr-2"></span>
                                API Key Required
                            </h5>
                            <p className="text-xs text-brand-text-secondary bg-yellow-50 p-2 rounded border border-yellow-200">
                                This tool requires a <strong>{tool.api_key_required}</strong> API key to function.
                            </p>
                        </div>
                    )}
                    
                    {Object.keys(tool.details.args).length > 0 && (
                        <div>
                            <h5 className="font-semibold text-brand-text-primary text-sm mb-2 flex items-center">
                                <span className="w-2 h-2 bg-brand-primary rounded-full mr-2"></span>
                                Arguments
                            </h5>
                            <div className="space-y-2">
                                {Object.entries(tool.details.args).map(([argName, argData]) => (
                                    <div key={argName} className="text-xs text-brand-text-secondary bg-brand-bg-secondary p-2 rounded">
                                        <div className="flex items-center mb-1">
                                            <code className="bg-brand-bg px-1 rounded font-mono text-brand-primary">{argName}</code>
                                            {typeof argData === 'object' && argData.type && (
                                                <span className="ml-2 text-brand-text-tertiary">({argData.type})</span>
                                            )}
                                            {typeof argData === 'object' && argData.required === false && (
                                                <span className="ml-2 text-xs bg-yellow-600 text-white px-1 rounded">optional</span>
                                            )}
                                        </div>
                                        {typeof argData === 'object' && argData.description && (
                                            <p className="text-brand-text-secondary">{argData.description}</p>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                    
                    {tool.details.returns && tool.details.returns !== "Unknown" && (
                        <div>
                            <h5 className="font-semibold text-brand-text-primary text-sm mb-2 flex items-center">
                                <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                                Returns
                            </h5>
                            <p className="text-xs text-brand-text-secondary bg-brand-bg-secondary p-2 rounded">{tool.details.returns}</p>
                        </div>
                    )}
                    
                    {tool.details.examples.length > 0 && (
                        <div>
                            <h5 className="font-semibold text-brand-text-primary text-sm mb-2 flex items-center">
                                <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                                Examples
                            </h5>
                            <div className="space-y-2">
                                {tool.details.examples.map((example, index) => (
                                    <code key={index} className="block text-xs bg-brand-bg-secondary p-2 rounded font-mono text-brand-text-secondary border border-brand-border">
                                        {example}
                                    </code>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

const SystemStatus: React.FC<{ health: RegistryHealth | null }> = ({ health }) => {
    if (!health) return null;

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'healthy': return 'text-green-500';
            case 'degraded': return 'text-yellow-500';
            default: return 'text-red-500';
        }
    };

    return (
        <div className="mb-4 p-3 bg-brand-bg-secondary rounded-lg border border-brand-border">
            <div className="flex items-center justify-between mb-2">
                <h4 className="font-semibold text-brand-text-primary">System Status</h4>
                <span className={`text-sm font-medium ${getStatusColor(health.status)}`}>
                    {health.status.toUpperCase()}
                </span>
            </div>
            <div className="grid grid-cols-2 gap-4 text-xs">
                <div>
                    <span className="text-brand-text-secondary">Tools:</span>
                    <span className="ml-1 text-brand-text-primary">
                        {health.summary.enabled_tools}/{health.summary.total_tools}
                    </span>
                </div>
                <div>
                    <span className="text-brand-text-secondary">Agents:</span>
                    <span className="ml-1 text-brand-text-primary">
                        {health.summary.enabled_agents}/{health.summary.total_agents}
                    </span>
                </div>
                <div>
                    <span className="text-brand-text-secondary">Errors:</span>
                    <span className="ml-1 text-red-500">{health.validation.errors.length}</span>
                </div>
                <div>
                    <span className="text-brand-text-secondary">Warnings:</span>
                    <span className="ml-1 text-yellow-500">{health.validation.warnings.length}</span>
                </div>
            </div>
            {health.validation.errors.length > 0 && (
                <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs">
                    <div className="font-medium text-red-700 mb-1">Errors:</div>
                    {health.validation.errors.slice(0, 2).map((error, index) => (
                        <div key={index} className="text-red-600">• {error}</div>
                    ))}
                    {health.validation.errors.length > 2 && (
                        <div className="text-red-500 italic">... and {health.validation.errors.length - 2} more</div>
                    )}
                </div>
            )}
        </div>
    );
};

const ToolkitPanel: React.FC = () => {
    const [tools, setTools] = useState<Tool[]>([]);
    const [health, setHealth] = useState<RegistryHealth | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                
                // Fetch both tools and health status in parallel
                const [toolsData, healthData] = await Promise.all([
                    getTools(),
                    getRegistryHealth()
                ]);
                
                setTools(toolsData);
                setHealth(healthData);
                setError(null);
            } catch (error) {
                console.error("Failed to fetch toolkit data:", error);
                setError(error instanceof Error ? error.message : "Unknown error occurred");
            } finally {
                setLoading(false);
            }
        };

        fetchData();
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
                
                {/* System Status */}
                <SystemStatus health={health} />
                
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