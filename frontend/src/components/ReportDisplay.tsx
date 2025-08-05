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
  // Debug logging
  console.log('[ReportDisplay] Report received:', report);
  console.log('[ReportDisplay] Report result:', report?.result);
  
  // Helper function to parse enhanced workflow results
  const parseEnhancedResult = (result: any) => {
    console.log('[ReportDisplay] Parsing result:', result);
    
    // Handle different result formats
    if (result && result.enhanced_result) {
      // Format: { enhanced_result: { ... } }
      const enhanced = result.enhanced_result;
      return {
        ticker: enhanced.ticker,
        sentiment: enhanced.sentiment,
        confidence: enhanced.confidence,
        keyInsights: enhanced.key_insights,
        marketAnalysis: enhanced.market_analysis,
        recommendation: enhanced.recommendation,
        riskAssessment: enhanced.risk_assessment
      };
    } else if (result && result.ticker) {
      // Format: { ticker: "...", sentiment: "...", etc. }
      return {
        ticker: result.ticker,
        sentiment: result.sentiment,
        confidence: result.confidence,
        keyInsights: result.key_insights,
        marketAnalysis: result.market_analysis,
        recommendation: result.recommendation,
        riskAssessment: result.risk_assessment
      };
    } else if (result && typeof result === 'object' && Object.keys(result).length > 0) {
      // Try to extract any object with ticker-like properties
      const possibleTicker = result.ticker || result.symbol || result.stock;
      if (possibleTicker) {
        return {
          ticker: possibleTicker,
          sentiment: result.sentiment || 'neutral',
          confidence: result.confidence || 0.5,
          keyInsights: result.key_insights || result.insights || ['Analysis completed'],
          marketAnalysis: result.market_analysis || result.analysis || 'Analysis completed',
          recommendation: result.recommendation || 'Consider the analysis results',
          riskAssessment: result.risk_assessment || result.risk || 'Standard market risks apply'
        };
      }
    }
    return null;
  };

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

      {/* Enhanced Workflow Results - Display if available */}
      {(report.result && (() => {
        const enhanced = parseEnhancedResult(report.result);
        console.log('[ReportDisplay] Parsed enhanced result:', enhanced);
        return enhanced && enhanced.ticker;
      })()) && (
        <section className="bg-brand-surface p-6 rounded-xl border border-brand-border">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-bold text-brand-text-primary">🚀 Enhanced Analysis Results</h3>
            {query && (
              <DownloadButton report={report} query={query} />
            )}
          </div>
          
          {(() => {
            const enhanced = parseEnhancedResult(report.result) || report.result;
            if (!enhanced || !enhanced.ticker) return null;
            
            return (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Key Metrics */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-brand-bg rounded-lg">
                    <span className="text-brand-text-secondary">Ticker</span>
                    <span className="font-bold text-white">{enhanced.ticker}</span>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-brand-bg rounded-lg">
                    <span className="text-brand-text-secondary">Sentiment</span>
                    <span className={`font-medium ${
                      enhanced.sentiment === 'positive' ? 'text-green-400' :
                      enhanced.sentiment === 'negative' ? 'text-red-400' :
                      'text-yellow-400'
                    }`}>
                      {enhanced.sentiment?.charAt(0).toUpperCase() + enhanced.sentiment?.slice(1)}
                    </span>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-brand-bg rounded-lg">
                    <span className="text-brand-text-secondary">Confidence</span>
                    <span className={`font-medium ${
                      (enhanced.confidence || 0) >= 0.8 ? 'text-green-400' :
                      (enhanced.confidence || 0) >= 0.6 ? 'text-yellow-400' :
                      'text-red-400'
                    }`}>
                      {Math.round((enhanced.confidence || 0) * 100)}%
                    </span>
                  </div>
                </div>
                
                {/* Analysis Content */}
                <div className="space-y-4">
                  {enhanced.recommendation && (
                    <div>
                      <h4 className="text-lg font-semibold text-brand-text-primary mb-2">💡 Recommendation</h4>
                      <div className="text-brand-text-secondary bg-brand-bg p-3 rounded-lg">
                        {enhanced.recommendation}
                      </div>
                    </div>
                  )}
                  
                  {enhanced.keyInsights && enhanced.keyInsights.length > 0 && (
                    <div>
                      <h4 className="text-lg font-semibold text-brand-text-primary mb-2">🔍 Key Insights</h4>
                      <ul className="space-y-2">
                        {enhanced.keyInsights.map((insight: string, index: number) => (
                          <li key={index} className="text-brand-text-secondary bg-brand-bg p-2 rounded-lg text-sm">
                            • {insight}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            );
          })()}
        </section>
      )}

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