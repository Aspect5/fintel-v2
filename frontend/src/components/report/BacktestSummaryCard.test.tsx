import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import BacktestSummaryCard from './BacktestSummaryCard';

describe('BacktestSummaryCard', () => {
  test('shows metrics when backtest tool output exists', () => {
    const findings = [
      {
        agentName: 'Market Analyst',
        specialization: 'Market Analysis',
        summary: 'ok',
        details: [],
        toolCalls: [
          { toolName: 'backtest_baseline', toolInput: {}, toolOutput: JSON.stringify({ metrics: { accuracy: 0.6, auc: 0.65, brier: 0.22, mean_forward_return: 0.01, sharpe_like: 0.4, ret_when_pred_up: 0.02, ret_when_pred_down: -0.01, n_predictions: 50 } }) }
        ]
      }
    ] as any;

    render(<BacktestSummaryCard findings={findings} />);
    expect(screen.getByText('📈 Backtest Summary')).toBeInTheDocument();
    expect(screen.getByText(/Accuracy/)).toBeInTheDocument();
    expect(screen.getByText(/AUC/)).toBeInTheDocument();
    expect(screen.getByText(/Brier/)).toBeInTheDocument();
  });
});


