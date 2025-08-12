import { Report, AgentFinding, EnhancedResult, ToolCallResult } from '../types';
import { parseReportContent } from './reportParser';
import { normalizeName, normalizeRecommendation, toTitleCase } from './reportUtils';

function generateCrossAgentInsights(agentFindings: AgentFinding[], provider: string | undefined): string {
  if (agentFindings.length === 0) return provider ? `Analysis completed using ${provider}.` : 'Analysis completed.';
  const agentNames = agentFindings.map((f) => f.agentName);
  const base = provider
    ? `Analysis completed using ${agentNames.join(' and ')} with ${provider}.`
    : `Analysis completed using ${agentNames.join(' and ')}.`;
  const insights: string[] = [base];
  const hasConsensus = agentFindings.every((f) => String(f.summary).toLowerCase().includes('positive'));
  if (hasConsensus) {
    insights.push('All agents identified positive trends, indicating strong consensus.');
  } else {
    insights.push('Agents provided mixed perspectives, suggesting balanced analysis.');
  }
  return insights.join(' ');
}

function stringifyBrief(value: any): string {
  try {
    if (value === null || value === undefined) return 'No output';
    if (typeof value === 'string') return value.slice(0, 140);
    return JSON.stringify(value).slice(0, 140);
  } catch {
    return 'Output unavailable';
  }
}

export function buildReportFromWorkflowState(workflowData: any): Report {
  // Prefer enhanced_result if available; otherwise allow object result
  const enhanced: EnhancedResult | null = (workflowData?.enhanced_result as EnhancedResult)
    || (typeof workflowData?.result === 'object' && workflowData?.result !== null
      ? (workflowData.result as EnhancedResult)
      : null);

  const { result, agent_invocations, provider } = enhanced || {} as any;

  // Helpers for clean sentences
  const stripTrailingPunct = (s: string) => s.replace(/[\s]*[\.;:,!?]+$/g, '');
  const ensurePeriod = (s: string) => (/[\.!?]$/.test(s.trim()) ? s.trim() : `${s.trim()}.`);

  // Choose executive summary content (prefer rich synthesis-style sentence)
  let reportContent = 'Analysis completed successfully.';
  if (typeof result === 'string') {
    reportContent = result;
  } else if (typeof result === 'object' && result !== null) {
    const r: any = result;
    const recLabel = r.recommendation ? normalizeRecommendation(String(r.recommendation)) : '';
    const sentiment = typeof r.sentiment === 'string' ? toTitleCase(String(r.sentiment).toLowerCase()) : '';
    const confidencePct = typeof r.confidence === 'number' ? Math.round((r.confidence || 0) * 100) : undefined;
    const keyInsightsArr = Array.isArray(r.key_insights) ? r.key_insights : [];
    const keyInsights = keyInsightsArr
      .slice(0, 2)
      .map((s: string) => stripTrailingPunct(String(s)))
      .filter((s: string) => s.length > 0)
      .join(', ');
    const risk = r.risk_assessment ? stripTrailingPunct(String(r.risk_assessment)) : '';

    const parts: string[] = [];
    if (recLabel) parts.push(ensurePeriod(`Recommendation: ${recLabel}`));
    if (sentiment) parts.push(ensurePeriod(`Sentiment: ${sentiment}${confidencePct !== undefined ? ` (${confidencePct}%)` : ''}`));
    if (keyInsights) parts.push(ensurePeriod(`Key insights: ${keyInsights}`));
    if (risk) parts.push(ensurePeriod(`Top risks: ${risk}`));

    if (parts.length > 0) {
      reportContent = parts.join(' ');
    } else if (r.market_analysis) {
      reportContent = String(r.market_analysis);
    } else if (r.content) {
      reportContent = String(r.content);
    } else {
      try {
        reportContent = JSON.stringify(result, null, 2);
      } catch {
        reportContent = String(result);
      }
    }
  }

  // Build helper maps: role -> taskId, role -> configuredAgentName
  const roleToTaskId: Record<string, string> = {};
  const roleToAgentName: Record<string, string> = {};
  try {
    const currentNodes = (workflowData?.nodes || []) as any[];
    currentNodes.forEach((n: any) => {
      if (n?.id?.startsWith?.('task_')) {
        const role = String(n.id).replace('task_', '');
        const tid = n?.data?.taskId;
        const configuredAgentName = n?.data?.agentName;
        if (role && tid) roleToTaskId[role] = tid;
        if (role && configuredAgentName) roleToAgentName[role] = String(configuredAgentName);
      }
    });
  } catch {}

  const allEvents = (workflowData?.event_history || []) as any[];
  const isAgentToolCall = (e: any) =>
    e?.event_type === 'agent_tool_call' &&
    !e?.is_internal_controlflow_tool &&
    !(typeof e?.tool_name === 'string' && e.tool_name.startsWith('mark_task_'));
  const isToolResult = (e: any) => e?.event_type === 'tool_result';
  const normalizeLoose = (s: any) => String(s ?? '').toLowerCase().replace(/[^a-z0-9]+/g, '');

  // Build agent findings from trace if available
  let agentFindings: AgentFinding[] = [];
  if (workflowData?.trace?.task_results) {
    const taskResults = workflowData.trace.task_results;
    agentFindings = Object.entries(taskResults).map(([taskName, taskResult]: [string, any]) => {
      const agentNameMap: Record<string, string> = {
        market_analysis: 'Market Analyst',
        risk_assessment: 'Risk Assessor',
        final_synthesis: 'Investment Advisor',
        recommendation: 'Investment Advisor',
      };
      const agentName = agentNameMap[taskName] || taskName.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());

      let summary = 'Analysis completed';
      let details: string[] = [];
        if (typeof taskResult === 'object' && taskResult !== null) {
        const isSynthesisRole = taskName === 'final_synthesis' || taskName === 'recommendation' || agentName === 'Investment Advisor';
        if (isSynthesisRole) {
            const recLabel = taskResult.recommendation ? normalizeRecommendation(String(taskResult.recommendation)) : '';
            const sent = typeof taskResult.sentiment === 'string' ? toTitleCase(String(taskResult.sentiment).toLowerCase()) : '';
            const confidencePct = typeof taskResult.confidence === 'number' ? Math.round((taskResult.confidence || 0) * 100) : undefined;
            const insightsJoined = Array.isArray(taskResult.key_insights)
              ? taskResult.key_insights
                  .slice(0, 2)
                  .map((s: string) => stripTrailingPunct(String(s)))
                  .filter((s: string) => s.length > 0)
                  .join(', ')
              : '';
            const risk = taskResult.risk_assessment ? stripTrailingPunct(String(taskResult.risk_assessment)) : '';
            const parts: string[] = [];
            if (recLabel) parts.push(ensurePeriod(`Recommendation: ${recLabel}`));
            if (sent) parts.push(ensurePeriod(`Sentiment: ${sent}${confidencePct !== undefined ? ` (${confidencePct}%)` : ''}`));
            if (insightsJoined) parts.push(ensurePeriod(`Key insights: ${insightsJoined}`));
            if (risk) parts.push(ensurePeriod(`Top risks: ${risk}`));
            summary = parts.join(' ').trim() || taskResult.analysis_summary || taskResult.market_analysis || recLabel || 'Analysis completed';
        } else {
          if (taskResult.analysis_summary) summary = taskResult.analysis_summary;
          else if (taskResult.risk_summary) summary = taskResult.risk_summary;
          else if (taskResult.recommendation) summary = taskResult.recommendation;
          else if (taskResult.market_analysis) summary = taskResult.market_analysis;
        }
        if (Array.isArray(taskResult.key_insights)) details = taskResult.key_insights;
        else if (Array.isArray(taskResult.risk_factors)) details = taskResult.risk_factors;
      }

      // Derive tool calls for this task/agent from event history using robust correlation
      let toolCalls: ToolCallResult[] = [];
      try {
        const expectedTaskId = roleToTaskId[taskName];
        const normalizedRole = normalizeName(taskName);
        // const normalizedAgentName = normalizeName(agentName);

        // Primary: agent_tool_call events
        let calls = allEvents.filter((e: any) => {
          if (!isAgentToolCall(e)) return false;
          const byTaskId = Boolean(expectedTaskId && e?.task_id && e.task_id === expectedTaskId);
          const byAgentRole = Boolean(e?.agent_role && normalizeName(e.agent_role) === normalizedRole);
          const byTaskName = Boolean(e?.task_name && normalizeName(String(e.task_name).replace(/^task_/, '')) === normalizedRole);
          // Loose name match to handle 'MarketAnalyst' vs display 'Market Analyst'; prefer configured agent name if available
          const configuredNameForRole = roleToAgentName[taskName];
          const displayNameLoose = Boolean(e?.agent_name && normalizeLoose(e.agent_name) === normalizeLoose(agentName));
          const configuredNameLoose = Boolean(
            e?.agent_name && configuredNameForRole && normalizeLoose(e.agent_name) === normalizeLoose(configuredNameForRole)
          );
          const byAgentNameLoose = displayNameLoose || configuredNameLoose;
          return byTaskId || byAgentRole || byTaskName || byAgentNameLoose;
        });

        toolCalls = calls.map((e: any) => ({
          toolName: e.tool_name,
          toolInput: e.tool_input,
          toolOutput: e.tool_output,
          toolOutputSummary: stringifyBrief(e.tool_output),
        }));

        // Fallback: if no agent_tool_call captured, infer from tool_result events correlated by task/role/name
        if (toolCalls.length === 0) {
          const resultEvents = allEvents.filter((e: any) => {
            if (!isToolResult(e)) return false;
            const byTaskId = Boolean(expectedTaskId && e?.task_id && e.task_id === expectedTaskId);
            const byAgentRole = Boolean(e?.agent_role && normalizeName(e.agent_role) === normalizedRole);
            const byTaskName = Boolean(e?.task_name && normalizeName(String(e.task_name).replace(/^task_/, '')) === normalizedRole);
            const configuredNameForRole = roleToAgentName[taskName];
            const displayNameLoose = Boolean(e?.agent_name && normalizeLoose(e.agent_name) === normalizeLoose(agentName));
            const configuredNameLoose = Boolean(
              e?.agent_name && configuredNameForRole && normalizeLoose(e.agent_name) === normalizeLoose(configuredNameForRole)
            );
            const byAgentNameLoose = displayNameLoose || configuredNameLoose;
            return byTaskId || byAgentRole || byTaskName || byAgentNameLoose;
          });
          toolCalls = resultEvents.map((e: any) => ({
            toolName: e.tool_name,
            toolInput: undefined,
            toolOutput: e.result,
            toolOutputSummary: stringifyBrief(e.result),
          }));
        }
      } catch {}

      return {
        agentName,
        specialization: taskName.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase()),
        summary,
        details,
        toolCalls,
      } as AgentFinding;
    });
  } else if (Array.isArray(agent_invocations)) {
    agentFindings = agent_invocations.map((inv: any) => ({
      agentName: inv.agent || inv.agentName || 'Unknown Agent',
      specialization: inv.specialization || 'Financial Analysis',
      summary: inv.task || inv.naturalLanguageTask || 'Analysis completed',
      details: inv.details || [],
      toolCalls: inv.tool_calls || inv.toolCalls || [],
    }));
  }

  const crossAgentInsights = generateCrossAgentInsights(agentFindings, provider || '');

  // Data quality notes derived strictly from event_history agent_tool_call
  const toolEvents = allEvents.filter(isAgentToolCall);
  const uniqueTools = Array.from(new Set(toolEvents.map((e: any) => e.tool_name).filter(Boolean)));
  const dataQualityNotes = uniqueTools.length > 0
    ? `Tools used: ${toolEvents.length} calls across ${uniqueTools.length} unique tools (${uniqueTools.join(', ')}).`
    : 'No external tools were invoked.';

  // Parse structured report sections from content for consistency
  const parsed = parseReportContent(reportContent);

  const report: Report = {
    executiveSummary: reportContent,
    agentFindings,
    failedAgents: [],
    crossAgentInsights,
    actionableRecommendations: parsed.actionItems,
    riskAssessment: parsed.riskAssessment || 'Standard market risks apply',
    confidenceLevel: parsed.confidenceLevel,
    dataQualityNotes,
    executionTrace: {
      fintelQueryAnalysis: (enhanced as any)?.query || workflowData?.query || '',
      agentInvocations: agent_invocations || workflowData?.agent_invocations || [],
    },
    result: result || workflowData?.result,
  };

  return report;
}


