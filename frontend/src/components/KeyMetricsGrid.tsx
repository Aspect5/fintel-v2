import React from 'react';
import MarkdownRenderer from './MarkdownRenderer';

interface KeyMetricsGridProps {
  confidenceLevel?: number;
  riskAssessment?: string;
  actionableRecommendations?: string[];
  dataQualityNotes?: string;
}

const KeyMetricsGrid: React.FC<KeyMetricsGridProps> = ({
  confidenceLevel = 0.85,
  riskAssessment = "Standard market risks",
  actionableRecommendations = [],
  dataQualityNotes = "Analysis based on available market and economic data."
}) => {
  const getConfidenceColor = (level: number) => {
    if (level >= 0.8) return 'text-green-400';
    if (level >= 0.6) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getConfidenceLabel = (level: number) => {
    if (level >= 0.8) return 'High confidence';
    if (level >= 0.6) return 'Moderate confidence';
    return 'Low confidence';
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Confidence Level */}
      <div className="bg-brand-surface p-4 rounded-xl border border-brand-border">
        <div className="flex items-center mb-3">
          <div className="w-6 h-6 bg-blue-500/20 rounded-full flex items-center justify-center mr-2">
            <span className="text-blue-400 text-xs">🎯</span>
          </div>
          <h4 className="text-sm font-semibold text-brand-text-primary flex items-center gap-2">
            Confidence
            <span
              title="Derived from the synthesis agent's confidence (0–1) scaled to percent. Will be calibrated by data breadth, agent consensus, and risk. High ≥ 80, Moderate 60–79, Low < 60."
              className="cursor-help text-brand-text-tertiary"
            >
              ⓘ
            </span>
          </h4>
        </div>
        <div className="text-center">
          <div className={`text-2xl font-bold mb-1 ${getConfidenceColor(confidenceLevel)}`}>
            {Math.round(confidenceLevel * 100)}%
          </div>
          <div className="w-full bg-brand-bg rounded-full h-2 mb-2">
            <div 
              className="bg-gradient-to-r from-brand-primary to-brand-secondary h-2 rounded-full transition-all duration-300"
              style={{ width: `${confidenceLevel * 100}%` }}
            ></div>
          </div>
          <p className="text-xs text-brand-text-secondary">{getConfidenceLabel(confidenceLevel)}</p>
        </div>
      </div>

      {/* Risk Assessment */}
      <div className="bg-brand-surface p-4 rounded-xl border border-brand-border">
        <div className="flex items-center mb-3">
          <div className="w-6 h-6 bg-yellow-500/20 rounded-full flex items-center justify-center mr-2">
            <span className="text-yellow-400 text-xs">⚠️</span>
          </div>
          <h4 className="text-sm font-semibold text-brand-text-primary">Risk Level</h4>
        </div>
        <div className="text-brand-text-secondary text-sm">
          <p className="font-medium">Moderate</p>
          <p className="text-xs mt-1">{riskAssessment}</p>
        </div>
      </div>

      {/* Action Items */}
      <div className="bg-brand-surface p-4 rounded-xl border border-brand-border">
        <div className="flex items-center mb-3">
          <div className="w-6 h-6 bg-green-500/20 rounded-full flex items-center justify-center mr-2">
            <span className="text-green-400 text-xs">📋</span>
          </div>
          <h4 className="text-sm font-semibold text-brand-text-primary">Next Steps</h4>
        </div>
        <div className="text-brand-text-secondary text-sm">
          {actionableRecommendations.length > 0 ? (
            <div className="space-y-1">
              <div className="text-xs">
                <MarkdownRenderer content={actionableRecommendations.slice(0, 2).map(rec => `- ${rec}`).join('\n')} />
              </div>
              {actionableRecommendations.length > 2 && (
                <p className="text-xs text-brand-text-secondary mt-1">
                  +{actionableRecommendations.length - 2} more items
                </p>
              )}
            </div>
          ) : (
            <p className="text-xs">Review analysis details</p>
          )}
        </div>
      </div>

      {/* Data Quality */}
      <div className="bg-brand-surface p-4 rounded-xl border border-brand-border">
        <div className="flex items-center mb-3">
          <div className="w-6 h-6 bg-purple-500/20 rounded-full flex items-center justify-center mr-2">
            <span className="text-purple-400 text-xs">📊</span>
          </div>
          <h4 className="text-sm font-semibold text-brand-text-primary">Data Quality</h4>
        </div>
        <div className="text-brand-text-secondary text-xs">
          <p>{dataQualityNotes}</p>
        </div>
      </div>
    </div>
  );
};

export default KeyMetricsGrid; 