import { buildReportFromWorkflowState } from './reportBuilder';

const sampleEventHistory = [
  {
    event_type: 'agent_tool_call',
    timestamp: '2025-01-01T00:00:00Z',
    agent_name: 'Risk Assessment',
    agent_role: 'risk_assessment',
    task_id: 'T123',
    tool_name: 'fetch_market_data',
    tool_input: { ticker: 'AAPL' },
    tool_output: '{"price": 190}',
    is_internal_controlflow_tool: false,
  },
  {
    event_type: 'agent_tool_call',
    timestamp: '2025-01-01T00:00:01Z',
    agent_name: 'RiskAssessment',
    agent_role: 'risk_assessment',
    task_id: 'T123',
    tool_name: 'process_financial_data',
    tool_input: { data: [1,2,3] },
    tool_output: '{"ok": true}',
    is_internal_controlflow_tool: false,
  },
  {
    event_type: 'agent_tool_call',
    timestamp: '2025-01-01T00:00:02Z',
    agent_name: 'Risk Assessor',
    agent_role: 'risk_assessment',
    task_id: 'T123',
    tool_name: 'news_search',
    tool_input: { q: 'AAPL risk' },
    tool_output: 'Some news...',
    is_internal_controlflow_tool: false,
  },
];

describe('reportBuilder tool-call mapping and synthesis summary', () => {
  test('maps tool calls to Risk Assessor with 3 events', () => {
    const workflowData = {
      nodes: [
        { id: 'task_risk_assessment', data: { taskId: 'T123' } },
      ],
      trace: {
        task_results: {
          risk_assessment: { analysis_summary: 'Risk looks moderate', key_insights: ['Volatility increasing'] },
        },
      },
      event_history: sampleEventHistory,
      result: { recommendation: 'Hold', sentiment: 'neutral', confidence: 0.72, key_insights: ['Stable revenue'], risk_assessment: 'Market risk due to rate cuts' },
    };

    const report = buildReportFromWorkflowState(workflowData);
    const risk = report.agentFindings.find((f) => f.agentName === 'Risk Assessor');
    expect(risk).toBeTruthy();
    expect(risk?.toolCalls?.length).toBe(3);
    const toolNames = (risk?.toolCalls || []).map((t) => t.toolName);
    expect(toolNames).toEqual(expect.arrayContaining(['fetch_market_data', 'process_financial_data', 'news_search']));
  });

  test('synthesis summary is rich', () => {
    const workflowData = {
      nodes: [
        { id: 'task_final_synthesis', data: { taskId: 'T999' } },
      ],
      trace: {
        task_results: {
          final_synthesis: { recommendation: 'Buy', sentiment: 'positive', confidence: 0.84, key_insights: ['Strong earnings', 'User growth'], risk_assessment: 'Regulatory risk' },
        },
      },
      event_history: [],
    };

    const report = buildReportFromWorkflowState(workflowData);
    const synth = report.agentFindings.find((f) => f.agentName === 'Investment Advisor');
    expect(synth).toBeTruthy();
    const text = synth?.summary || '';
    expect(text).toMatch(/Recommendation: Buy\./);
    expect(text).toMatch(/Sentiment: positive \(84%\)\./);
    expect(text).toMatch(/Key insights: .+/);
    expect(text).toMatch(/Top risks: Regulatory risk/);
  });
});


