import React, { useEffect, useState } from 'react';
import { getAgents, getRegistryHealth, AgentInfo, RegistryHealth } from '../../services/apiService';

const AgentStatusBadge: React.FC<{ agent: AgentInfo }> = ({ agent }) => {
  if (!agent.enabled) {
    return (
      <span className="inline-block px-2 py-1 text-xs bg-red-600 text-white rounded-full font-medium">
        Disabled
      </span>
    );
  }

  if (!agent.validation_status.valid) {
    return (
      <span className="inline-block px-2 py-1 text-xs bg-yellow-600 text-white rounded-full font-medium" 
            title="Agent has validation issues">
        Issues
      </span>
    );
  }

  if (agent.required) {
    return (
      <span className="inline-block px-2 py-1 text-xs bg-blue-600 text-white rounded-full font-medium">
        Required
      </span>
    );
  }

  return (
    <span className="inline-block px-2 py-1 text-xs bg-green-600 text-white rounded-full font-medium">
      Available
    </span>
  );
};

const AgentCard: React.FC<{ agent: AgentInfo }> = ({ agent }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const getToolStatusColor = (status: string) => {
    switch (status) {
      case 'available': return 'text-green-600';
      case 'api_key_missing': return 'text-yellow-600';
      case 'disabled': return 'text-red-600';
      case 'not_found': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className={`bg-brand-bg p-4 rounded-lg border border-brand-border mb-4 transition-shadow hover:shadow-lg hover:border-brand-primary/50 ${
      !agent.enabled ? 'opacity-60' : ''
    }`}>
      <div className="flex items-center mb-2">
        <div className="w-5 h-5 bg-purple-500 rounded-full mr-3 flex-shrink-0 flex items-center justify-center">
          <span className="text-white text-xs font-bold">A</span>
        </div>
        <div className="flex-grow">
          <h4 className="font-bold text-brand-text-primary">{agent.name}</h4>
          {agent.capabilities.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1">
              {agent.capabilities.slice(0, 3).map((capability) => (
                <span 
                  key={capability}
                  className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded-full"
                >
                  {capability}
                </span>
              ))}
              {agent.capabilities.length > 3 && (
                <span className="text-xs text-brand-text-tertiary">
                  +{agent.capabilities.length - 3} more
                </span>
              )}
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          <AgentStatusBadge agent={agent} />
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-brand-text-secondary hover:text-brand-primary text-sm px-2 py-1 rounded transition-colors"
            title={isExpanded ? "Collapse details" : "Expand details"}
          >
            {isExpanded ? '▼' : '▶'}
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="pl-8 space-y-4 border-l-2 border-brand-border ml-2">
          {/* Tools */}
          <div>
            <h5 className="font-semibold text-brand-text-primary text-sm mb-2 flex items-center">
              <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
              Tools ({agent.tools.length})
            </h5>
            <div className="space-y-2">
              {agent.tools.map((toolName) => {
                const toolStatus = agent.validation_status.tool_validation[toolName] || 'unknown';
                return (
                  <div key={toolName} className="flex items-center justify-between text-xs bg-brand-bg-secondary p-2 rounded">
                    <span className="text-brand-text-secondary">{toolName}</span>
                    <span className={`font-medium ${getToolStatusColor(toolStatus)}`}>
                      {toolStatus.replace('_', ' ')}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Capabilities */}
          {agent.capabilities.length > 0 && (
            <div>
              <h5 className="font-semibold text-brand-text-primary text-sm mb-2 flex items-center">
                <span className="w-2 h-2 bg-purple-500 rounded-full mr-2"></span>
                Capabilities ({agent.capabilities.length})
              </h5>
              <div className="flex flex-wrap gap-2">
                {agent.capabilities.map((capability) => (
                  <span 
                    key={capability}
                    className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded-full"
                  >
                    {capability}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Validation Issues */}
          {agent.validation_status.missing_tools && agent.validation_status.missing_tools.length > 0 && (
            <div>
              <h5 className="font-semibold text-brand-text-primary text-sm mb-2 flex items-center">
                <span className="w-2 h-2 bg-red-500 rounded-full mr-2"></span>
                Missing Tools
              </h5>
              <div className="space-y-1">
                {agent.validation_status.missing_tools.map((toolName) => (
                  <div key={toolName} className="text-xs text-red-600 bg-red-50 p-2 rounded border border-red-200">
                    • {toolName}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Instructions Preview */}
          <div>
            <h5 className="font-semibold text-brand-text-primary text-sm mb-2 flex items-center">
              <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
              Instructions Preview
            </h5>
            <p className="text-xs text-brand-text-secondary bg-brand-bg-secondary p-2 rounded border border-brand-border">
              {agent.instructions.length > 200 
                ? `${agent.instructions.substring(0, 200)}...` 
                : agent.instructions
              }
            </p>
          </div>
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
        <h4 className="font-semibold text-brand-text-primary">Agent System Status</h4>
        <span className={`text-sm font-medium ${getStatusColor(health.status)}`}>
          {health.status.toUpperCase()}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-4 text-xs">
        <div>
          <span className="text-brand-text-secondary">Total Agents:</span>
          <span className="ml-1 text-brand-text-primary">{health.summary.total_agents}</span>
        </div>
        <div>
          <span className="text-brand-text-secondary">Enabled:</span>
          <span className="ml-1 text-brand-text-primary">{health.summary.enabled_agents}</span>
        </div>
        <div>
          <span className="text-brand-text-secondary">Required:</span>
          <span className="ml-1 text-blue-500">{health.summary.required_agents}</span>
        </div>
        <div>
          <span className="text-brand-text-secondary">Capabilities:</span>
          <span className="ml-1 text-brand-text-primary">{health.summary.capabilities.length}</span>
        </div>
      </div>
      {health.validation.errors.length > 0 && (
        <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs">
          <div className="font-medium text-red-700 mb-1">Agent Errors:</div>
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

const AgentPanel: React.FC = () => {
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [health, setHealth] = useState<RegistryHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch both agents and health status in parallel
        const [agentsData, healthData] = await Promise.all([
          getAgents(),
          getRegistryHealth()
        ]);
        
        setAgents(agentsData);
        setHealth(healthData);
        setError(null);
      } catch (error) {
        console.error("Failed to fetch agent data:", error);
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
        <h3 className="text-lg font-semibold mb-2">Error Loading Agents</h3>
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
        <h3 className="text-lg font-semibold text-brand-text-primary mb-4 px-2">Available Agents</h3>
        
        {/* System Status */}
        <SystemStatus health={health} />
        
        {loading ? (
          <p className="text-brand-text-secondary">Loading agents...</p>
        ) : (
          agents.map(agent => (
            <AgentCard key={agent.name} agent={agent} />
          ))
        )}
      </div>
    </div>
  );
};

export default AgentPanel; 