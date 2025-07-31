import React from 'react';
import ExpandableText from './ExpandableText';
import MarkdownRenderer from './MarkdownRenderer';

interface ToolCall {
  toolName: string;
  toolOutputSummary: string;
}

interface AgentAnalysisCardProps {
  agentName: string;
  specialization: string;
  analysis: string;
  toolCalls?: ToolCall[];
  icon?: string;
}

const AgentAnalysisCard: React.FC<AgentAnalysisCardProps> = ({
  agentName,
  specialization,
  analysis,
  toolCalls = [],
  icon = '🤖'
}) => {
  return (
    <div className="bg-brand-surface p-4 rounded-xl border border-brand-border hover:border-brand-primary/30 transition-all duration-200">
      {/* Header */}
      <div className="flex items-center mb-3">
        <div className="w-8 h-8 bg-brand-primary/20 rounded-full flex items-center justify-center mr-3">
          <span className="text-brand-primary text-sm">{icon}</span>
        </div>
        <div>
          <h4 className="text-lg font-semibold text-brand-text-primary">{agentName}</h4>
          <p className="text-sm text-brand-text-secondary">{specialization}</p>
        </div>
      </div>
      
      {/* Tool Calls Summary */}
      {toolCalls.length > 0 && (
        <div className="mb-3">
          <p className="text-xs font-medium text-brand-text-secondary mb-2">Tools Used:</p>
          <div className="space-y-1">
            {toolCalls.map((tool, index) => (
              <div key={index} className="flex items-center text-xs">
                <span className="text-brand-primary mr-2">•</span>
                <span className="text-brand-text-secondary font-medium">{tool.toolName}:</span>
                <span className="text-brand-text-secondary ml-1">{tool.toolOutputSummary}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Analysis */}
      <div>
        <p className="text-xs font-medium text-brand-text-secondary mb-2">Analysis:</p>
        <div className="text-sm text-brand-text-secondary">
          <MarkdownRenderer content={analysis} />
        </div>
      </div>
    </div>
  );
};

export default AgentAnalysisCard; 