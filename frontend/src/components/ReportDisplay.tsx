import React from 'react';
import { Report, AgentFinding, AgentFailure } from '../types';
import MarkdownRenderer from './MarkdownRenderer';
import AgentAnalysisCard from './AgentAnalysisCard';
import KeyMetricsGrid from './KeyMetricsGrid';
import ExpandableText from './ExpandableText';
import DownloadButton from './DownloadButton';

interface ReportDisplayProps {
  report: Report | null;
  isLoading?: boolean;
  query?: string;
}

const ReportDisplay: React.FC<ReportDisplayProps> = ({ report, isLoading = false, query = '' }) => {
  // Helper function to extract executive summary from full report
  const extractExecutiveSummary = (fullReport: string): string => {
    const lines = fullReport.split('\n');
    let inExecutiveSummary = false;
    let executiveSummaryLines: string[] = [];
    
    for (const line of lines) {
      if (line.includes('🎯 Executive Summary') || line.includes('### 🎯 Executive Summary')) {
        inExecutiveSummary = true;
        continue;
      }
      
      if (inExecutiveSummary) {
        if (line.startsWith('### ') || line.startsWith('## ')) {
          break; // Next section
        }
        if (line.trim()) {
          executiveSummaryLines.push(line);
        }
      }
    }
    
    return executiveSummaryLines.join('\n').trim();
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-brand-text-secondary">Generating report...</div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="p-4 text-brand-text-secondary">
        No report available. Run a query to generate a report.
      </div>
    );
  }

  // Extract agent icon mapping
  const getAgentIcon = (agentName: string) => {
    const iconMap: { [key: string]: string } = {
      'Market Analyst': '📈',
      'Economic Analyst': '🏛️',
      'Risk Assessment': '⚠️'
    };
    return iconMap[agentName] || '🤖';
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header Section */}
      <div className="bg-brand-surface p-6 rounded-xl border border-brand-border">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-bold text-brand-text-primary">📊 Investment Analysis Report</h1>
          <div className="text-sm text-brand-text-secondary">
            Analysis completed in {report.executionTrace?.agentInvocations?.length || 0} steps
          </div>
        </div>
        
        {/* Executive Summary */}
        {report.executiveSummary && (
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-brand-text-primary mb-2">🎯 Executive Summary</h2>
            <div className="text-brand-text-secondary">
              <MarkdownRenderer content={extractExecutiveSummary(report.executiveSummary)} />
            </div>
          </div>
        )}
      </div>

      {/* Key Metrics Grid - Always visible for quick decision making */}
      <KeyMetricsGrid
        confidenceLevel={report.confidenceLevel}
        actionableRecommendations={report.actionableRecommendations}
        dataQualityNotes={report.dataQualityNotes}
      />

      {/* Agent Analysis - Side by side cards */}
      {report.agentFindings && report.agentFindings.length > 0 && (
        <section className="space-y-4">
          <h3 className="text-xl font-bold text-brand-text-primary">🔍 Agent Analysis</h3>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {report.agentFindings.map((finding: AgentFinding, index: number) => (
              <AgentAnalysisCard
                key={index}
                agentName={finding.agentName}
                specialization={finding.specialization}
                analysis={finding.summary}
                toolCalls={finding.toolCalls}
                icon={getAgentIcon(finding.agentName)}
              />
            ))}
          </div>
        </section>
      )}

      {/* Cross-Agent Insights - Expandable section */}
      {report.crossAgentInsights && (
        <section className="bg-brand-surface p-6 rounded-xl border border-brand-border">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-purple-500/20 rounded-full flex items-center justify-center mr-3">
                <span className="text-purple-400 text-sm">🧠</span>
              </div>
              <h4 className="text-lg font-semibold text-brand-text-primary">Cross-Agent Insights</h4>
            </div>
            {query && (
              <DownloadButton report={report} query={query} />
            )}
          </div>
          <ExpandableText
            content={report.crossAgentInsights}
            maxLength={200}
            className="text-brand-text-secondary"
            collapsedClassName="line-clamp-2"
          />
        </section>
      )}

      {/* Failed Agents - Only show if there are failures */}
      {report.failedAgents && report.failedAgents.length > 0 && (
        <section className="bg-red-500/10 p-4 rounded-xl border border-red-500/20">
          <div className="flex items-center mb-3">
            <div className="w-6 h-6 bg-red-500/20 rounded-full flex items-center justify-center mr-2">
              <span className="text-red-400 text-xs">❌</span>
            </div>
            <h4 className="text-sm font-semibold text-red-400">Failed Agents</h4>
          </div>
          <div className="space-y-2">
            {report.failedAgents.map((failure: AgentFailure, index: number) => (
              <div key={index} className="bg-brand-bg p-3 rounded-lg border border-red-500/20">
                <div className="flex items-center justify-between mb-1">
                  <h5 className="text-sm font-medium text-red-400">
                    {failure.agentName}
                  </h5>
                </div>
                <p className="text-brand-text-secondary text-xs mb-1">{failure.task}</p>
                <p className="text-red-300 text-xs">{failure.error}</p>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
};

export default ReportDisplay; 