import React from 'react';
import { AgentFinding, AgentFailure } from '../../frontend/src/types';

// Import components from the same directory
import AgentFindingCard from './AgentFindingCard';
import AgentFailureCard from './AgentFailureCard';

// FIX: Update the props to accept the 'trace' object from ChatPanel
interface ReportDisplayProps {
  trace: any;
}

const ReportDisplay: React.FC<ReportDisplayProps> = ({ trace }) => {
  // If there's no trace data, don't render the report.
  if (!trace) {
    return <p className="text-yellow-400">Report data is not available.</p>;
  }

  // Destructure the data you need from the trace object
  const { fintelQueryAnalysis, agentInvocations, executiveSummary, failedAgents } = trace;

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
      {fintelQueryAnalysis && (
        <section>
          <h3 className="text-xl font-semibold mb-3 text-white border-b border-gray-600 pb-2">Query Analysis</h3>
          <p className="text-gray-300">{fintelQueryAnalysis}</p>
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