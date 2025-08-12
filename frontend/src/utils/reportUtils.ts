// Shared helpers for report generation/rendering

export function normalizeName(input: string | undefined | null): string {
  if (!input) return '';
  return String(input)
    .toLowerCase()
    .trim()
    .replace(/[\s\-]+/g, '_')
    .replace(/__+/g, '_');
}

export function toTitleCase(value?: string): string {
  if (!value) return '';
  return value.charAt(0).toUpperCase() + value.slice(1);
}

export function normalizeRecommendation(rec?: string): string {
  if (!rec) return '';
  const r = rec.toLowerCase();
  if (/(strong\s+)?buy|accumulate|overweight/.test(r)) return 'Buy';
  if (/hold|neutral/.test(r)) return 'Hold';
  if (/sell|underperform|reduce/.test(r)) return 'Sell';
  return toTitleCase(rec);
}

// Extract a consistent enhanced result shape regardless of backend variations
export function parseEnhancedResult(result: any):
  | {
      ticker?: string;
      sentiment?: string;
      confidence?: number;
      keyInsights?: string[];
      marketAnalysis?: string;
      recommendation?: string;
      riskAssessment?: string;
      daily_series?: Array<{ date: string; value: number }>;
    }
  | null {
  try {
    if (!result) return null;
    const enhanced = result.enhanced_result || result;
    const candidate = typeof enhanced === 'object' ? enhanced : {};
    if (!candidate) return null;
    const ticker = candidate.ticker || candidate.symbol || candidate.stock;
    if (!ticker && !candidate.market_analysis && !candidate.recommendation && !candidate.sentiment) {
      return null;
    }
    return {
      ticker,
      sentiment: candidate.sentiment || 'neutral',
      confidence: typeof candidate.confidence === 'number' ? candidate.confidence : 0.5,
      keyInsights: candidate.key_insights || candidate.insights || [],
      marketAnalysis: candidate.market_analysis || candidate.analysis,
      recommendation: candidate.recommendation,
      riskAssessment: candidate.risk_assessment || candidate.risk,
      daily_series: candidate.daily_series,
    };
  } catch {
    return null;
  }
}


