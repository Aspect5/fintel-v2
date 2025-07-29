import React from 'react';
import { Report, AgentFinding, AgentFailure } from '../types';
import MarkdownRenderer from './MarkdownRenderer';

interface ReportDisplayProps {
  report: Report | null;
  isLoading?: boolean;
}

const ReportDisplay: React.FC<ReportDisplayProps> = ({ report, isLoading = false }) => {
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

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Main Report Content - Use the executive summary as the main content */}
      {report.executiveSummary && (
        <div className="bg-brand-surface p-6 rounded-xl border border-brand-border">
          <MarkdownRenderer content={report.executiveSummary} />
        </div>
      )}

      {/* Agent Findings - Show individual agent results */}
      {report.agentFindings && report.agentFindings.length > 0 && (
        <section className="space-y-4">
          <h3 className="text-xl font-bold text-brand-text-primary mb-4">🔍 Agent Analysis</h3>
          {report.agentFindings.map((finding: AgentFinding, index: number) => (
            <div key={index} className="bg-brand-surface p-6 rounded-xl border border-brand-border">
              <div className="flex items-center mb-3">
                <div className="w-8 h-8 bg-brand-primary/20 rounded-full flex items-center justify-center mr-3">
                  <span className="text-brand-primary text-sm">🤖</span>
                </div>
                <div>
                  <h4 className="text-lg font-semibold text-brand-text-primary">{finding.agentName}</h4>
                  <p className="text-sm text-brand-text-secondary">{finding.specialization}</p>
                </div>
              </div>
              <div className="text-brand-text-secondary mb-3">
                <MarkdownRenderer content={finding.summary} />
              </div>
              {finding.details && finding.details.length > 0 && (
                <div className="space-y-2">
                  {finding.details.map((detail, detailIndex) => (
                    <div key={detailIndex} className="flex items-start space-x-2">
                      <div className="flex-shrink-0 w-2 h-2 bg-brand-primary rounded-full mt-2"></div>
                      <p className="text-sm text-brand-text-secondary">{detail}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </section>
      )}

      {/* Key Metrics Grid - Only show if we have actionable recommendations */}
      {report.actionableRecommendations && report.actionableRecommendations.length > 0 && (
        <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Investment Recommendation */}
          <div className="bg-brand-surface p-4 rounded-xl border border-brand-border">
            <div className="flex items-center mb-2">
              <div className="w-6 h-6 bg-green-500/20 rounded-full flex items-center justify-center mr-2">
                <span className="text-green-400 text-xs">💡</span>
              </div>
              <h4 className="text-sm font-semibold text-brand-text-primary">Recommendation</h4>
            </div>
            <div className="text-brand-text-secondary text-sm">
              {report.actionableRecommendations.map((rec, index) => (
                <div key={index} className="mb-1">
                  {rec}
                </div>
              ))}
            </div>
          </div>

          {/* Confidence Level */}
          <div className="bg-brand-surface p-4 rounded-xl border border-brand-border">
            <div className="flex items-center mb-2">
              <div className="w-6 h-6 bg-blue-500/20 rounded-full flex items-center justify-center mr-2">
                <span className="text-blue-400 text-xs">🎯</span>
              </div>
              <h4 className="text-sm font-semibold text-brand-text-primary">Confidence</h4>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-brand-primary mb-1">
                {report.confidenceLevel !== undefined ? Math.round(report.confidenceLevel * 100) : 85}%
              </div>
              <div className="w-full bg-brand-bg rounded-full h-2 mb-1">
                <div 
                  className="bg-gradient-to-r from-brand-primary to-brand-secondary h-2 rounded-full transition-all duration-300"
                  style={{ width: `${(report.confidenceLevel || 0.85) * 100}%` }}
                ></div>
              </div>
              <p className="text-xs text-brand-text-secondary">High confidence</p>
            </div>
          </div>

          {/* Risk Level */}
          <div className="bg-brand-surface p-4 rounded-xl border border-brand-border">
            <div className="flex items-center mb-2">
              <div className="w-6 h-6 bg-yellow-500/20 rounded-full flex items-center justify-center mr-2">
                <span className="text-yellow-400 text-xs">⚠️</span>
              </div>
              <h4 className="text-sm font-semibold text-brand-text-primary">Risk Level</h4>
            </div>
            <div className="text-brand-text-secondary text-sm">
              <p>Moderate risk</p>
              <p className="text-xs mt-1">Standard market risks</p>
            </div>
          </div>
        </section>
      )}

      {/* Cross-Agent Insights */}
      {report.crossAgentInsights && (
        <section className="bg-brand-surface p-6 rounded-xl border border-brand-border">
          <div className="flex items-center mb-4">
            <div className="w-8 h-8 bg-purple-500/20 rounded-full flex items-center justify-center mr-3">
              <span className="text-purple-400 text-sm">🧠</span>
            </div>
            <h4 className="text-lg font-semibold text-brand-text-primary">Cross-Agent Insights</h4>
          </div>
          <div className="text-brand-text-secondary text-sm">
            <MarkdownRenderer content={report.crossAgentInsights} />
          </div>
        </section>
      )}

      {/* Data Quality Notes */}
      {report.dataQualityNotes && (
        <section className="bg-brand-surface p-4 rounded-xl border border-brand-border">
          <div className="flex items-center mb-3">
            <div className="w-6 h-6 bg-green-500/20 rounded-full flex items-center justify-center mr-2">
              <span className="text-green-400 text-xs">📊</span>
            </div>
            <h4 className="text-sm font-semibold text-brand-text-primary">Data Quality</h4>
          </div>
          <div className="text-brand-text-secondary text-sm">
            <MarkdownRenderer content={report.dataQualityNotes} />
          </div>
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