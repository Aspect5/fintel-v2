import React from 'react';
import { AgentFinding } from '@/types';

function tryParseJSON(value: any): any | null {
  if (!value) return null;
  if (typeof value === 'object') return value;
  if (typeof value !== 'string') return null;
  try { return JSON.parse(value); } catch { return null; }
}

export interface BacktestSummaryCardProps {
  findings: AgentFinding[];
}

const BacktestSummaryCard: React.FC<BacktestSummaryCardProps> = ({ findings }) => {
  let metrics: any | null = null;
  for (const f of findings || []) {
    for (const c of (f.toolCalls || [])) {
      if ((c.toolName || '').toLowerCase() === 'backtest_baseline') {
        const parsed = tryParseJSON(c.toolOutput);
        if (parsed && parsed.metrics) {
          metrics = parsed.metrics;
          break;
        }
      }
    }
    if (metrics) break;
  }

  if (!metrics) return null;

  const { accuracy, auc, brier, mean_forward_return, sharpe_like, ret_when_pred_up, ret_when_pred_down, n_predictions } = metrics;

  return (
    <section className="bg-brand-surface p-6 rounded-xl border border-brand-border">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold text-brand-text-primary">📈 Backtest Summary</h3>
        <span className="text-xs text-brand-text-tertiary">n={n_predictions}</span>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <div className="bg-brand-bg p-3 rounded-lg">
          <div className="text-xs text-brand-text-tertiary">Accuracy</div>
          <div className="text-white font-semibold">{typeof accuracy === 'number' ? (accuracy * 100).toFixed(1) + '%' : '—'}</div>
        </div>
        <div className="bg-brand-bg p-3 rounded-lg">
          <div className="text-xs text-brand-text-tertiary">AUC</div>
          <div className="text-white font-semibold">{typeof auc === 'number' ? auc.toFixed(3) : '—'}</div>
        </div>
        <div className="bg-brand-bg p-3 rounded-lg">
          <div className="text-xs text-brand-text-tertiary">Brier</div>
          <div className="text-white font-semibold">{typeof brier === 'number' ? brier.toFixed(3) : '—'}</div>
        </div>
        <div className="bg-brand-bg p-3 rounded-lg">
          <div className="text-xs text-brand-text-tertiary">Mean Fwd Return</div>
          <div className="text-white font-semibold">{typeof mean_forward_return === 'number' ? (mean_forward_return * 100).toFixed(2) + '%' : '—'}</div>
        </div>
        <div className="bg-brand-bg p-3 rounded-lg">
          <div className="text-xs text-brand-text-tertiary">Sharpe-like</div>
          <div className="text-white font-semibold">{typeof sharpe_like === 'number' ? sharpe_like.toFixed(2) : '—'}</div>
        </div>
        <div className="bg-brand-bg p-3 rounded-lg">
          <div className="text-xs text-brand-text-tertiary">Ret if Pred Up</div>
          <div className="text-white font-semibold">{typeof ret_when_pred_up === 'number' ? (ret_when_pred_up * 100).toFixed(2) + '%' : '—'}</div>
        </div>
        <div className="bg-brand-bg p-3 rounded-lg">
          <div className="text-xs text-brand-text-tertiary">Ret if Pred Down</div>
          <div className="text-white font-semibold">{typeof ret_when_pred_down === 'number' ? (ret_when_pred_down * 100).toFixed(2) + '%' : '—'}</div>
        </div>
      </div>
    </section>
  );
};

export default BacktestSummaryCard;


