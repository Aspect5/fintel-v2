import React from 'react';

interface DownloadButtonProps {
  report: any;
  query: string;
  className?: string;
}

const DownloadButton: React.FC<DownloadButtonProps> = ({ report, query, className = '' }) => {
  const handleDownload = async () => {
    try {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0] + '_' + 
                       new Date().toTimeString().split(' ')[0].replace(/:/g, '-');
      
      // Extract ticker from query
      const tickerMatch = query.match(/\b[A-Z]{1,5}\b/);
      const ticker = tickerMatch ? tickerMatch[0] : 'ANALYSIS';
      
      const filename = `${ticker}_analysis_${timestamp}.md`;
      
      // Create markdown content
      const markdownContent = `# Investment Analysis Report - ${ticker}

**Query:** ${query}
**Generated:** ${new Date().toLocaleString()}
**Analysis Steps:** ${report.executionTrace?.agentInvocations?.length || 0}

## Executive Summary
${report.executiveSummary || 'No executive summary available.'}

## Agent Analysis
${report.agentFindings?.map((finding: any) => `
### ${finding.agentName}
**Specialization:** ${finding.specialization}

**Analysis:**
${finding.summary}

**Tools Used:**
${finding.toolCalls?.map((tc: any) => `- ${tc.toolName}: ${tc.toolOutputSummary || 'Executed successfully'}`).join('\n') || 'No tools used'}
`).join('\n') || 'No agent analysis available.'}

## Cross-Agent Insights
${report.crossAgentInsights || 'No cross-agent insights available.'}

## Key Metrics
- **Confidence Level:** ${Math.round((report.confidenceLevel || 0.85) * 100)}%
- **Risk Assessment:** ${report.riskAssessment || 'Standard market risks'}
- **Data Quality:** ${report.dataQualityNotes || 'Analysis based on available data'}

## Action Items
${report.actionableRecommendations?.map((rec: string) => `- ${rec}`).join('\n') || '- Review analysis details'}
`;

      // Create blob and download
      const blob = new Blob([markdownContent], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      // Send to backend for storage
      try {
        await fetch('/api/save-report', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            filename,
            content: markdownContent,
            query,
            timestamp: new Date().toISOString()
          }),
        });
      } catch (error) {
        console.warn('Failed to save report to backend:', error);
      }
      
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  return (
    <button
      onClick={handleDownload}
      className={`inline-flex items-center px-4 py-2 bg-brand-primary hover:bg-brand-secondary text-white rounded-lg transition-colors duration-200 ${className}`}
    >
      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      Download Report
    </button>
  );
};

export default DownloadButton; 