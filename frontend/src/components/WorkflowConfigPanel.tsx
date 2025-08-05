import React, { useState, useEffect } from 'react';
import CodeBracketIcon from './icons/CodeBracketIcon';
import InformationCircleIcon from './icons/InformationCircleIcon';

interface AgentConfig {
  name: string;
  role: string;
  required: boolean;
  fallback?: string;
  tools: string[];
  available: boolean;
  primary: boolean;
}

interface WorkflowConfig {
  name: string;
  description: string;
  agents: AgentConfig[];
}

const WorkflowConfigPanel: React.FC = () => {
  const [workflows, setWorkflows] = useState<WorkflowConfig[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState<string>('enhanced_simplified');
  const [isExpanded, setIsExpanded] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchWorkflowConfigs();
  }, []);

  const fetchWorkflowConfigs = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/workflow-configs');
      if (response.ok) {
        const data = await response.json();
        setWorkflows(data.workflows || []);
      }
    } catch (error) {
      console.error('Failed to fetch workflow configs:', error);
    } finally {
      setLoading(false);
    }
  };

  const currentWorkflow = workflows.find(w => w.name === selectedWorkflow);

  return (
    <div className="bg-brand-surface border border-brand-border rounded-lg p-4 mb-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <CodeBracketIcon className="w-5 h-5 text-brand-primary mr-2" />
          <h3 className="text-lg font-semibold text-brand-text-primary">Workflow Configuration</h3>
        </div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-brand-text-secondary hover:text-brand-primary transition-colors"
        >
          {isExpanded ? '▼' : '▶'}
        </button>
      </div>

      {isExpanded && (
        <div className="space-y-4">
          {/* Workflow Selection */}
          <div>
            <label className="block text-sm font-medium text-brand-text-primary mb-2">
              Workflow Type
            </label>
            <select
              value={selectedWorkflow}
              onChange={(e) => setSelectedWorkflow(e.target.value)}
              className="w-full bg-brand-bg border border-brand-border rounded px-3 py-2 text-brand-text-primary focus:border-brand-primary focus:outline-none"
            >
              {workflows.map((workflow) => (
                <option key={workflow.name} value={workflow.name}>
                  {workflow.name}
                </option>
              ))}
            </select>
          </div>

          {/* Current Workflow Info */}
          {currentWorkflow && (
            <div className="bg-brand-bg-secondary rounded-lg p-3">
              <h4 className="font-medium text-brand-text-primary mb-2">{currentWorkflow.name}</h4>
              <p className="text-sm text-brand-text-secondary mb-3">{currentWorkflow.description}</p>
              
              {/* Agent Status */}
              <div className="space-y-2">
                <h5 className="text-sm font-medium text-brand-text-primary">Agent Status</h5>
                {currentWorkflow.agents.map((agent) => (
                  <div key={agent.role} className="flex items-center justify-between text-sm">
                    <div className="flex items-center">
                      <span className={`w-2 h-2 rounded-full mr-2 ${
                        agent.available ? 'bg-green-500' : 'bg-red-500'
                      }`}></span>
                      <span className="text-brand-text-primary">{agent.role}</span>
                      {!agent.primary && agent.fallback && (
                        <span className="text-xs text-brand-text-tertiary ml-1">
                          (fallback: {agent.fallback})
                        </span>
                      )}
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 rounded text-xs ${
                        agent.required 
                          ? 'bg-red-600 text-white' 
                          : 'bg-gray-600 text-white'
                      }`}>
                        {agent.required ? 'Required' : 'Optional'}
                      </span>
                      <span className="text-xs text-brand-text-tertiary">
                        {agent.tools.length} tools
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Configuration Info */}
          <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-3">
            <div className="flex items-start">
              <InformationCircleIcon className="w-5 h-5 text-blue-400 mr-2 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-blue-200">
                <p className="font-medium mb-1">Configuration Management</p>
                <p className="text-xs">
                  Agents and tools can be customized by editing{' '}
                  <code className="bg-blue-900/50 px-1 rounded">backend/config/workflow_config.yaml</code>
                </p>
                <p className="text-xs mt-1">
                  Changes take effect after restarting the backend server.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkflowConfigPanel; 