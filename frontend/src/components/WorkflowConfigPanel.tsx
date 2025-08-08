import React, { useState, useEffect } from 'react';
import { useStore } from '../stores/store';
import SparklesIcon from './icons/SparklesIcon';
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
  key?: string;
  name: string;
  description: string;
  agents: AgentConfig[];
}

const WorkflowConfigPanel: React.FC = () => {
  const [workflows, setWorkflows] = useState<WorkflowConfig[]>([]);
  const { selectedWorkflow, setSelectedWorkflow } = useStore();
  const [localSelected, setLocalSelected] = useState<string>(selectedWorkflow || 'quick_stock_analysis');
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

  useEffect(() => {
    // keep local selection in sync with global store
    if (selectedWorkflow && selectedWorkflow !== localSelected) {
      setLocalSelected(selectedWorkflow);
    }
  }, [selectedWorkflow]);

  const currentWorkflow = workflows.find(w => (w.key || w.name) === localSelected);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-3">
        <SparklesIcon className="w-6 h-6 text-brand-primary" />
        <h2 className="text-xl font-semibold text-brand-text-primary">Workflow Selection</h2>
      </div>

      {/* Workflow Type Selection */}
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-brand-text-primary mb-3">
            Choose Analysis Type
          </label>
          <div className="space-y-3">
            {[...workflows, { key: 'custom', name: 'Custom', description: 'Build your own (coming soon)', agents: [] } as WorkflowConfig].map((workflow) => (
              <div
                key={(workflow.key || workflow.name)}
                className={`relative p-4 rounded-lg border-2 cursor-pointer transition-all ${
                  localSelected === (workflow.key || workflow.name)
                    ? 'border-brand-primary bg-brand-primary/10'
                    : 'border-brand-border bg-brand-bg hover:border-brand-primary/50 hover:bg-brand-bg-secondary'
                }`}
                onClick={() => {
                  const key = workflow.key || workflow.name;
                  setLocalSelected(key);
                  setSelectedWorkflow(key);
                }}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-medium text-brand-text-primary mb-1">
                      {workflow.name}
                    </h3>
                    <p className="text-sm text-brand-text-secondary">
                      {workflow.description}
                    </p>
                  </div>
                  {localSelected === (workflow.key || workflow.name) && (
                    <div className="w-5 h-5 bg-brand-primary rounded-full flex items-center justify-center ml-3">
                      <div className="w-2 h-2 bg-white rounded-full"></div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Current Workflow Details */}
      {currentWorkflow && (currentWorkflow.key || currentWorkflow.name) !== 'custom' && (
        <div className="bg-brand-bg-secondary border border-brand-border rounded-lg p-4">
          <h4 className="font-medium text-brand-text-primary mb-3">Selected Workflow Details</h4>
          
          {/* Agent Status */}
          <div className="space-y-3">
            <h5 className="text-sm font-medium text-brand-text-primary">Agent Team</h5>
            {currentWorkflow.agents.map((agent) => (
              <div key={agent.role} className="flex items-center justify-between text-sm">
                <div className="flex items-center">
                  <span className={`w-2 h-2 rounded-full mr-3 ${
                    agent.available ? 'bg-green-500' : 'bg-red-500'
                  }`}></span>
                  <span className="text-brand-text-primary">{agent.role}</span>
                  {!agent.primary && agent.fallback && (
                    <span className="text-xs text-brand-text-tertiary ml-2">
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

      {currentWorkflow && (currentWorkflow.key || currentWorkflow.name) === 'custom' && (
        <div className="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-4">
          <h4 className="font-medium text-yellow-200 mb-2">Custom Workflow</h4>
          <p className="text-sm text-yellow-300">Build-your-own is not implemented yet. Choose another workflow above or proceed via chat for suggestions.</p>
        </div>
      )}

      {/* Configuration Info */}
      <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4">
        <div className="flex items-start">
          <InformationCircleIcon className="w-5 h-5 text-blue-400 mr-3 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-blue-200">
            <p className="font-medium mb-2">Configuration Management</p>
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
  );
};

export default WorkflowConfigPanel; 