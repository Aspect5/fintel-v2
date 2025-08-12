import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import AlphaIntelligenceCard from './AlphaIntelligenceCard';

describe('AlphaIntelligenceCard', () => {
  test('renders aggregates when tool outputs present', () => {
    const findings = [
      {
        agentName: 'Market Analyst',
        specialization: 'Market Analysis',
        summary: 'ok',
        details: [],
        toolCalls: [
          { toolName: 'get_news_sentiment', toolInput: {}, toolOutput: JSON.stringify({ articles: [{}, {}], news_count_7: 2, news_count_30: 5, news_sent_mean_7: 0.2, news_sent_mean_30: 0.1, news_neg_count_7: 1 }) },
          { toolName: 'get_insider_transactions', toolInput: {}, toolOutput: JSON.stringify({ insider_buy_count: 3, insider_sell_count: 1 }) },
          { toolName: 'get_top_gainers_losers', toolInput: {}, toolOutput: JSON.stringify({ gainers: [1,2,3], losers: [1] }) },
        ]
      }
    ] as any;

    render(<AlphaIntelligenceCard findings={findings} />);
    expect(screen.getByText('🧠 Alpha Intelligence')).toBeInTheDocument();
    expect(screen.getByText(/Articles \(7d\/30d\):/)).toBeInTheDocument();
    expect(screen.getByText(/Insider Activity/)).toBeInTheDocument();
    expect(screen.getByText(/Market Breadth/)).toBeInTheDocument();
  });
});


