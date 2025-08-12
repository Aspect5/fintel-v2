import React from 'react';
import { AgentFinding } from '@/types';

function tryParseJSON(value: any): any | null {
  if (!value) return null;
  if (typeof value === 'object') return value;
  if (typeof value !== 'string') return null;
  try {
    return JSON.parse(value);
  } catch {
    try {
      const trimmed = value.trim();
      if (trimmed.startsWith('{') && trimmed.endsWith('}')) {
        return JSON.parse(trimmed);
      }
    } catch {}
    return null;
  }
}

function collectToolOutputs(findings: AgentFinding[], toolName: string): any[] {
  const outputs: any[] = [];
  for (const f of findings || []) {
    const calls = (f.toolCalls || []).filter(tc => (tc.toolName || '').toLowerCase() === toolName.toLowerCase());
    for (const c of calls) {
      const parsed = tryParseJSON(c.toolOutput);
      if (parsed) outputs.push(parsed);
    }
  }
  return outputs;
}

export interface AlphaIntelligenceCardProps {
  findings: AgentFinding[];
}

const AlphaIntelligenceCard: React.FC<AlphaIntelligenceCardProps> = ({ findings }) => {
  const newsArr = collectToolOutputs(findings, 'get_news_sentiment');
  const insidersArr = collectToolOutputs(findings, 'get_insider_transactions');
  const breadthArr = collectToolOutputs(findings, 'get_top_gainers_losers');

  let newsCount7 = 0;
  let newsCount30 = 0;
  let newsSent7Sum = 0;
  let newsSent30Sum = 0;
  let newsNeg7 = 0;

  for (const n of newsArr) {
    const articles = Array.isArray(n.articles) ? n.articles : [];
    if (typeof n.news_count_7 === 'number') newsCount7 += n.news_count_7;
    if (typeof n.news_count_30 === 'number') newsCount30 += n.news_count_30;
    if (typeof n.news_sent_mean_7 === 'number') newsSent7Sum += n.news_sent_mean_7;
    if (typeof n.news_sent_mean_30 === 'number') newsSent30Sum += n.news_sent_mean_30;
    if (typeof n.news_neg_count_7 === 'number') newsNeg7 += n.news_neg_count_7;
    if (!n.news_count_7 && articles.length) {
      newsCount30 += articles.length;
    }
  }
  const newsPanels = newsArr.length;
  const meanSent7 = newsPanels ? newsSent7Sum / newsPanels : 0;
  const meanSent30 = newsPanels ? newsSent30Sum / newsPanels : 0;

  let insiderBuys = 0;
  let insiderSells = 0;
  for (const ins of insidersArr) {
    const tx = Array.isArray(ins.transactions) ? ins.transactions : [];
    if (typeof ins.insider_buy_count === 'number') insiderBuys += ins.insider_buy_count;
    if (typeof ins.insider_sell_count === 'number') insiderSells += ins.insider_sell_count;
    if (!ins.insider_buy_count && !ins.insider_sell_count && tx.length) {
      for (const t of tx) {
        const ttype = String(t.type || t.transactionType || '').toLowerCase();
        if (ttype.includes('buy')) insiderBuys += 1;
        else if (ttype.includes('sell')) insiderSells += 1;
      }
    }
  }
  const insiderNet = insiderBuys - insiderSells;

  let breadth = 0;
  for (const b of breadthArr) {
    const gainers = Array.isArray(b.gainers) ? b.gainers.length : 0;
    const losers = Array.isArray(b.losers) ? b.losers.length : 0;
    if (typeof b.breadth_g_minus_l === 'number') breadth += b.breadth_g_minus_l;
    else breadth += (gainers - losers);
  }

  const hasAny = newsArr.length || insidersArr.length || breadthArr.length;
  if (!hasAny) return null;

  return (
    <section className="bg-brand-surface p-6 rounded-xl border border-brand-border">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold text-brand-text-primary">🧠 Alpha Intelligence</h3>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-brand-bg p-4 rounded-lg">
          <div className="text-sm font-semibold text-brand-text-primary mb-2">News & Sentiment</div>
          <div className="text-brand-text-secondary text-sm space-y-1">
            <div>Articles (7d/30d): {newsCount7 || 0} / {newsCount30 || 0}</div>
            <div>Mean Sentiment (7d): {meanSent7.toFixed(2)}</div>
            <div>Mean Sentiment (30d): {meanSent30.toFixed(2)}</div>
            <div>Negatives (7d): {newsNeg7 || 0}</div>
          </div>
        </div>
        <div className="bg-brand-bg p-4 rounded-lg">
          <div className="text-sm font-semibold text-brand-text-primary mb-2">Insider Activity</div>
          <div className="text-brand-text-secondary text-sm space-y-1">
            <div>Buys: {insiderBuys}</div>
            <div>Sells: {insiderSells}</div>
            <div>Net: <span className={insiderNet >= 0 ? 'text-green-400' : 'text-red-400'}>{insiderNet}</span></div>
          </div>
        </div>
        <div className="bg-brand-bg p-4 rounded-lg">
          <div className="text-sm font-semibold text-brand-text-primary mb-2">Market Breadth</div>
          <div className="text-brand-text-secondary text-sm space-y-1">
            <div>Gainers − Losers: <span className={breadth >= 0 ? 'text-green-400' : 'text-red-400'}>{breadth}</span></div>
            <div className="text-xs text-brand-text-tertiary">Based on Alpha Vantage Top Gainers/Losers</div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default AlphaIntelligenceCard;


