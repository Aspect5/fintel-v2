import { parseReportContent } from './reportParser';

// Test data that mimics the backend response
const testReportContent = `# 📊 Investment Analysis Report

**Query:** Should I invest in AAPL?

## Executive Summary
Based on comprehensive analysis, AAPL shows strong fundamentals with positive growth potential.

## Key Findings
- Strong revenue growth in services segment
- Robust cash flow generation
- Market leadership in premium smartphone segment

## Investment Recommendation
BUY recommendation for AAPL with a 12-month price target of $200.

## Risk Assessment
⚠️ Key risks include supply chain disruptions and regulatory challenges.

## Action Items
- Monitor quarterly earnings reports
- Track new product launches
- Watch for regulatory developments

## 🔄 Agent Adaptation & Retry Analysis

This section details how agents adapted to tool errors and retry attempts:

### Market Analyst (Market Data Analysis)

**Tool:** \`process_financial_data\`
**Total Attempts:** 3
**Final Status:** ✅ Success

**Retry Sequence:**

**Attempt 1** ❌
- **Input:** \`AAPL\` (retry_id: 1)
- **Error Type:** DataFormatError
- **Error Message:** Expected JSON format, received CSV
- **Received Data:** \`AAPL,150.25,2.5%\`
- **Expected Format:** JSON object with price and change fields

**Attempt 2** ❌
- **Input:** \`{"symbol": "AAPL"}\` (retry_id: 2)
- **Error Type:** APIError
- **Error Message:** Rate limit exceeded
- **Received Data:** \`{"error": "rate_limit"}\`
- **Expected Format:** Valid API response

**Attempt 3** ✅
- **Input:** \`{"symbol": "AAPL", "retry": true}\` (retry_id: 3)

**Adaptation Strategy:** Format adaptation: CSV, JSON; Error learning: adapted to 2 different error types

---

### Economic Analyst (Economic Indicators)

**Tool:** \`misleading_data_validator\`
**Total Attempts:** 2
**Final Status:** ✅ Success

**Retry Sequence:**

**Attempt 1** ❌
- **Input:** \`GDP data\` (retry_id: 1)
- **Error Type:** ValidationError
- **Error Message:** Insufficient data points
- **Received Data:** \`{"data": [1, 2]}\`
- **Expected Format:** At least 10 data points

**Attempt 2** ✅
- **Input:** \`{"data": [1,2,3,4,5,6,7,8,9,10,11,12], "source": "FRED"}\` (retry_id: 2)

**Adaptation Strategy:** Data enrichment: added more data points and source information

---

## Confidence Level
Confidence: 8/10 - High confidence based on successful data retrieval and analysis.`;

describe('Report Parser', () => {
  test('should extract retry analysis correctly', () => {
    const result = parseReportContent(testReportContent);
    
    expect(result.retryAnalysis).toBeDefined();
    expect(result.retryAnalysis?.agentsEncounteringErrors).toEqual(['Market Analyst', 'Economic Analyst']);
    expect(result.retryAnalysis?.retryAttempts).toBe(5);
    expect(result.retryAnalysis?.adaptationSuccess).toBe(true);
    expect(result.retryAnalysis?.retryDetails).toHaveLength(2);
    
    // Check first agent details
    const marketAnalyst = result.retryAnalysis?.retryDetails[0];
    expect(marketAnalyst?.agent).toBe('Market Analyst');
    expect(marketAnalyst?.tool).toBe('process_financial_data');
    expect(marketAnalyst?.totalAttempts).toBe(3);
    expect(marketAnalyst?.finalStatus).toBe('success');
    expect(marketAnalyst?.retrySequence).toHaveLength(3);
    
    // Check retry sequence details
    const firstAttempt = marketAnalyst?.retrySequence[0];
    expect(firstAttempt?.attemptNumber).toBe(1);
    expect(firstAttempt?.status).toBe('error');
    expect(firstAttempt?.errorType).toBe('DataFormatError');
    expect(firstAttempt?.errorMessage).toBe('Expected JSON format, received CSV');
  });

  test('should extract other sections correctly', () => {
    const result = parseReportContent(testReportContent);
    
    expect(result.executiveSummary).toContain('Based on comprehensive analysis');
    expect(result.investmentRecommendation).toContain('BUY recommendation');
    expect(result.keyFindings).toHaveLength(3);
    expect(result.riskAssessment).toContain('supply chain disruptions');
    expect(result.actionItems).toHaveLength(3);
    expect(result.confidenceLevel).toBe(0.8);
  });

  test('should handle reports without retry analysis', () => {
    const simpleReport = `## Executive Summary
Simple analysis without retries.

## Key Findings
- Finding 1
- Finding 2`;

    const result = parseReportContent(simpleReport);
    
    expect(result.retryAnalysis).toBeUndefined();
    expect(result.executiveSummary).toContain('Simple analysis');
    expect(result.keyFindings).toHaveLength(2);
  });
}); 