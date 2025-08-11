import React from 'react';
import { Report, AgentFinding } from '../types';
import MarkdownRenderer from './MarkdownRenderer';
import KeyMetricsGrid from './KeyMetricsGrid';
import ExpandableText from './ExpandableText';
import RetryAnalysisCard from './report/RetryAnalysisCard';
import { parseEnhancedResult, normalizeRecommendation, toTitleCase } from '@/utils/reportUtils';

interface ReportDisplayProps {
  report: Report | null;
  isLoading?: boolean;
}

const InvestmentReport: React.FC<ReportDisplayProps> = ({ report, isLoading = false }) => {
  const DEBUG = import.meta.env.MODE === 'development' && (window as any).__DEBUG__;
  if (DEBUG) console.log('[InvestmentReport] Render', { hasReport: !!report });

  // use shared parseEnhancedResult from utils

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-brand-text-secondary">Generating report...</div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="p-4 text-brand-text-secondary">No report available. Run a query to generate a report.</div>
    );
  }

  // helper removed

  return (
    <div className="w-full max-w-[1400px] mx-auto space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="space-y-6 lg:col-span-2">
          <div className="bg-brand-surface p-6 rounded-xl border border-brand-border">
            {(() => {
              const enhanced = parseEnhancedResult(report.result);
              const toTC = toTitleCase;
              const recLabel = normalizeRecommendation(enhanced?.recommendation);
              const recColor =
                recLabel === 'Buy'
                  ? 'bg-green-500/15 text-green-300 ring-green-500/30'
                  : recLabel === 'Sell'
                  ? 'bg-red-500/15 text-red-300 ring-red-500/30'
                  : 'bg-yellow-500/15 text-yellow-300 ring-yellow-500/30';

              if (enhanced) {
                return (
                  <section className="mb-1">
                    <h2 className="text-lg font-semibold text-brand-text-primary mb-3">🎯 Executive Summary</h2>
                    <div className="flex flex-wrap items-center gap-2 mb-4">
                      {recLabel && (
                        <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ring-1 ring-inset ${recColor}`}>
                          {recLabel}
                        </span>
                      )}
                      {enhanced.ticker && (
                        <span className="inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ring-1 ring-inset ring-brand-border text-brand-text-secondary">
                          Ticker: <span className="ml-1 text-white">{enhanced.ticker}</span>
                        </span>
                      )}
                      {typeof enhanced.sentiment === 'string' && typeof enhanced.confidence === 'number' && (
                        <span className="inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ring-1 ring-inset ring-brand-border text-brand-text-secondary">
                          {toTC(enhanced.sentiment)}, {Math.round((enhanced.confidence || 0) * 100)}%
                        </span>
                      )}
                    </div>

                    {Array.isArray(enhanced.keyInsights) && enhanced.keyInsights.length > 0 && (
                      <ul className="list-disc list-inside space-y-1 text-brand-text-secondary">
                        {enhanced.keyInsights.slice(0, 3).map((insight: string, idx: number) => (
                          <li key={idx}>{insight}</li>
                        ))}
                      </ul>
                    )}
                  </section>
                );
              }

              const textSummary = (report as any).executiveSummary as string | undefined;
              if (textSummary && textSummary.trim().length > 0) {
                return (
                  <section className="mb-1">
                    <h2 className="text-lg font-semibold text-brand-text-primary mb-2">🎯 Executive Summary</h2>
                    <div className="text-brand-text-secondary">
                      <MarkdownRenderer content={textSummary.replace(/\s—\s/g, '. ')} />
                    </div>
                  </section>
                );
              }
              return null;
            })()}
          </div>

          {(report.result && (() => {
            const enhanced = parseEnhancedResult(report.result);
            return enhanced && enhanced.ticker;
          })()) && (
            <section className="bg-brand-surface p-6 rounded-xl border border-brand-border">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-brand-text-primary">🚀 Enhanced Analysis Results</h3>
              </div>
              {(() => {
                const enhanced = parseEnhancedResult(report.result) || (report.result as any);
                if (!enhanced || !enhanced.ticker) return null;
                return (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      <div className="flex items-center justify-between p-3 bg-brand-bg rounded-lg">
                        <span className="text-brand-text-secondary">Ticker</span>
                        <span className="font-bold text-white">{enhanced.ticker}</span>
                      </div>
                      <div className="flex items-center justify-between p-3 bg-brand-bg rounded-lg">
                        <span className="text-brand-text-secondary">Sentiment</span>
                        <span className={`font-medium ${enhanced.sentiment === 'positive' ? 'text-green-400' : enhanced.sentiment === 'negative' ? 'text-red-400' : 'text-yellow-400'}`}>
                          {enhanced.sentiment?.charAt(0).toUpperCase() + enhanced.sentiment?.slice(1)}
                        </span>
                      </div>
                    </div>
                    <div className="space-y-4">
                      {enhanced.recommendation && (
                        <div>
                          <h4 className="text-lg font-semibold text-brand-text-primary mb-2">💡 Recommendation</h4>
                          {(() => {
                            const rec = enhanced.recommendation as string | undefined;
                            const r = rec ? rec.toLowerCase() : '';
                            const label = r.match(/(strong\s+)?buy|accumulate|overweight/)
                              ? 'Buy'
                              : r.match(/hold|neutral/)
                              ? 'Hold'
                              : r.match(/sell|underperform|reduce/)
                              ? 'Sell'
                              : rec
                              ? rec.charAt(0).toUpperCase() + rec.slice(1)
                              : '';
                            const color =
                              label === 'Buy'
                                ? 'bg-green-500/15 text-green-300 ring-green-500/30'
                                : label === 'Sell'
                                ? 'bg-red-500/15 text-red-300 ring-red-500/30'
                                : 'bg-yellow-500/15 text-yellow-300 ring-yellow-500/30';
                            return (
                              <span className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-semibold ring-1 ring-inset ${color}`}>
                                {label}
                              </span>
                            );
                          })()}
                        </div>
                      )}
                      {enhanced.keyInsights && enhanced.keyInsights.length > 0 && (
                        <div>
                          <h4 className="text-lg font-semibold text-brand-text-primary mb-2">🔍 Key Insights</h4>
                          <ul className="space-y-2 list-disc list-inside">
                            {enhanced.keyInsights.map((insight: string, index: number) => (
                              <li key={index} className="text-brand-text-secondary bg-brand-bg p-2 rounded-lg text-sm list-item">
                                {insight}
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

          {report.retryAnalysis && (
            <section className="bg-brand-surface p-6 rounded-xl border border-brand-border">
              <h3 className="text-xl font-bold text-brand-text-primary mb-4">🔄 Retry Analysis</h3>
              <RetryAnalysisCard retryAnalysis={report.retryAnalysis} />
            </section>
          )}

          {report.agentFindings && report.agentFindings.length > 0 && (
            <section className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold text-brand-text-primary">🔍 Agent Analysis</h3>
                <span className="text-xs text-brand-text-tertiary">{report.agentFindings.length} agents</span>
              </div>
              <div className="report-agent-grid">
                {report.agentFindings.map((finding: AgentFinding, index: number) => (
                  <AgentCard key={index} finding={finding} />
                ))}
              </div>
            </section>
          )}

          {report.crossAgentInsights && (
            <section className="bg-brand-surface p-6 rounded-xl border border-brand-border">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-purple-500/20 rounded-full flex items-center justify-center mr-3">
                    <span className="text-purple-400 text-sm">🧠</span>
                  </div>
                  <h4 className="text-lg font-semibold text-brand-text-primary">Cross-Agent Insights</h4>
                </div>
              </div>
              <ExpandableText
                content={(report.crossAgentInsights || '').replace(/\s—\s/g, '. ')}
                maxLength={200}
                className="text-brand-text-secondary"
                collapsedClassName="line-clamp-2"
              />
            </section>
          )}
        </div>

        <aside className="hidden lg:block lg:col-span-1 sticky top-6 self-start">
          <KeyMetricsGrid
            confidenceLevel={report.confidenceLevel}
            actionableRecommendations={report.actionableRecommendations}
            dataQualityNotes={report.dataQualityNotes}
          />
        </aside>
      </div>

      <div className="lg:hidden">
        <KeyMetricsGrid
          confidenceLevel={report.confidenceLevel}
          actionableRecommendations={report.actionableRecommendations}
          dataQualityNotes={report.dataQualityNotes}
        />
      </div>
    </div>
  );
};

const AgentCard: React.FC<{ finding: AgentFinding }> = ({ finding }) => {
  const [expanded, setExpanded] = React.useState(false);
  const getAgentIcon = (agentName: string) => {
    const iconMap: { [key: string]: string } = {
      'Market Analyst': '📈',
      'Economic Analyst': '🏛️',
      'Risk Assessment': '⚠️',
    };
    return iconMap[agentName] || '🤖';
  };
  return (
    <div className="bg-brand-surface p-4 rounded-xl border border-brand-border">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center">
          <div className="w-8 h-8 bg-brand-primary/20 rounded-full flex items-center justify-center mr-2">
            <span className="text-brand-primary text-sm">{getAgentIcon(finding.agentName)}</span>
          </div>
          <div>
            <div className="text-sm font-semibold text-white leading-tight line-clamp-1">{finding.agentName}</div>
            <div className="text-[11px] text-brand-text-tertiary line-clamp-1">{finding.specialization}</div>
          </div>
        </div>
        <button className="text-[11px] text-brand-text-tertiary hover:text-brand-text-secondary" onClick={() => setExpanded(!expanded)}>
          {expanded ? 'Hide' : 'More'}
        </button>
      </div>
      <div className="text-xs text-brand-text-secondary">
        {(() => {
          const text = String(finding.summary || '').trim();
          if (!text) return 'Analysis completed';
          if (/^buy|sell|hold$/i.test(text)) return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
          return expanded ? text : (text.length > 180 ? text.slice(0, 180) + '…' : text);
        })()}
      </div>
      {expanded && (
        <div className="mt-2 border-t border-brand-border pt-2">
          {Array.isArray(finding.toolCalls) && finding.toolCalls.length > 0 ? (
            <div>
              <div className="text-[11px] text-brand-text-tertiary mb-1">Tools</div>
              <div className="flex flex-wrap gap-1">
                {finding.toolCalls
                  .filter((tc) => tc.toolName && !String(tc.toolName).startsWith('mark_task_'))
                  .slice(0, 6)
                  .map((tc, i) => (
                    <span key={i} className="text-[10px] px-2 py-0.5 rounded-full bg-brand-bg text-brand-text-secondary border border-brand-border max-w-[160px] truncate">
                      {tc.toolName}
                    </span>
                  ))}
              </div>
            </div>
          ) : (
            <div className="text-[11px] text-brand-text-tertiary">No external tools recorded</div>
          )}
        </div>
      )}
    </div>
  );
};

export default InvestmentReport;


