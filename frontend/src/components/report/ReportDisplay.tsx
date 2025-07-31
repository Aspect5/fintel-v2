import React from 'react';
import { AgentFinding, AgentFailure, Report } from '../../types';
import { parseReportContent } from '../../utils/reportParser';

// Import components from the same directory
import AgentFindingCard from './AgentFindingCard';
import AgentFailureCard from './AgentFailureCard';
import RetryAnalysisCard from './RetryAnalysisCard';

interface ReportDisplayProps {
  report: Report;
  query?: string;
}

const ReportDisplay: React.FC<ReportDisplayProps> = ({ report, query }) => {
  // If there's no report data, don't render the report.
  if (!report) {
    return <p className="text-yellow-400">Report data is not available.</p>;
  }

  // Parse the executive summary to extract sections
  const parsedSections = report.parsedSections || parseReportContent(report.executiveSummary);
  
  // Use parsed sections or fall back to original data
  const executiveSummary = parsedSections.executiveSummary || report.executiveSummary;
  const queryAnalysis = parsedSections.queryAnalysis;
  const agentInvocations = report.executionTrace?.agentInvocations || [];
  const failedAgents = report.failedAgents || [];

  return (
    <div className="w-full mx-auto p-4 space-y-6 animate-fade-in">
      <style>{`
        @keyframes fade-in {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in { animation: fade-in 0.5s ease-out forwards; }
      `}</style>

      {/* Executive Summary Section */}
      {executiveSummary && (
        <section>
          <h3 className="text-xl font-semibold mb-3 text-white border-b border-gray-600 pb-2">Executive Summary</h3>
          <p className="text-gray-300 leading-relaxed">{executiveSummary}</p>
        </section>
      )}

      {/* Query Analysis Section */}
      {queryAnalysis && (
        <section>
          <h3 className="text-xl font-semibold mb-3 text-white border-b border-gray-600 pb-2">Query Analysis</h3>
          <p className="text-gray-300">{queryAnalysis}</p>
        </section>
      )}

      {/* Investment Recommendation Section */}
      {parsedSections.investmentRecommendation && (
        <section>
          <h3 className="text-xl font-semibold mb-3 text-white border-b border-gray-600 pb-2">Investment Recommendation</h3>
          <p className="text-gray-300 leading-relaxed">{parsedSections.investmentRecommendation}</p>
        </section>
      )}

      {/* Key Findings Section */}
      {parsedSections.keyFindings && parsedSections.keyFindings.length > 0 && (
        <section>
          <h3 className="text-xl font-semibold mb-3 text-white border-b border-gray-600 pb-2">Key Findings</h3>
          <ul className="list-disc list-inside space-y-2 text-gray-300">
            {parsedSections.keyFindings.map((finding, index) => (
              <li key={index}>{finding}</li>
            ))}
          </ul>
        </section>
      )}

      {/* Risk Assessment Section */}
      {parsedSections.riskAssessment && (
        <section>
          <h3 className="text-xl font-semibold mb-3 text-white border-b border-gray-600 pb-2">Risk Assessment</h3>
          <p className="text-gray-300 leading-relaxed">{parsedSections.riskAssessment}</p>
        </section>
      )}

      {/* Action Items Section */}
      {parsedSections.actionItems && parsedSections.actionItems.length > 0 && (
        <section>
          <h3 className="text-xl font-semibold mb-3 text-white border-b border-gray-600 pb-2">Action Items</h3>
          <ul className="list-disc list-inside space-y-2 text-gray-300">
            {parsedSections.actionItems.map((item, index) => (
              <li key={index}>{item}</li>
            ))}
          </ul>
        </section>
      )}

      {/* Retry Analysis Section */}
      {parsedSections.retryAnalysis && (
        <section>
          <RetryAnalysisCard retryAnalysis={parsedSections.retryAnalysis} />
        </section>
      )}

      {/* Agent Findings Section */}
      {agentInvocations && agentInvocations.length > 0 && (
        <section>
          <h3 className="text-xl font-semibold mb-3 text-white border-b border-gray-600 pb-2">Agent Findings</h3>
          <div className="grid grid-cols-1 gap-4">
            {agentInvocations.map((finding: AgentFinding, i: number) => (
              <AgentFindingCard key={`finding-${i}`} finding={finding} />
            ))}
          </div>
        </section>
      )}

      {/* Agent Failures Section */}
      {failedAgents && failedAgents.length > 0 && (
        <section>
          <h3 className="text-xl font-semibold mb-3 text-white border-b-2 border-red-500/50 pb-2">Execution Failures</h3>
          <div className="grid grid-cols-1 gap-4">
            {failedAgents.map((failure: AgentFailure, i: number) => (
              <AgentFailureCard key={`failure-${i}`} failure={failure} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
};

export default ReportDisplay;