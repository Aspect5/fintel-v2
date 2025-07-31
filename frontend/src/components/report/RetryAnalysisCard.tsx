import React from 'react';
import { RetryAnalysisData } from '../../types';

interface RetryAnalysisCardProps {
  retryAnalysis: RetryAnalysisData;
}

const RetryAnalysisCard: React.FC<RetryAnalysisCardProps> = ({ retryAnalysis }) => {
  const {
    agentsEncounteringErrors,
    specificErrors,
    retryAttempts,
    adaptationStrategies,
    adaptationSuccess,
    impactOnAnalysis,
    retryDetails
  } = retryAnalysis;

  return (
    <div className="bg-brand-surface p-6 rounded-lg border border-brand-border">
      <div className="flex items-center mb-4">
        <h4 className="text-xl font-bold text-brand-primary">🔄 Agent Adaptation & Retry Analysis</h4>
        <div className={`ml-3 px-2 py-1 rounded-full text-xs font-semibold ${
          adaptationSuccess 
            ? 'bg-green-500/20 text-green-400 border border-green-500/30' 
            : 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
        }`}>
          {adaptationSuccess ? 'Adaptation Successful' : 'Adaptation Required'}
        </div>
      </div>

      {/* Summary Section */}
      <div className="mb-6 p-4 bg-brand-bg/50 rounded-lg">
        <h5 className="text-lg font-semibold text-brand-text-primary mb-3">Summary</h5>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-brand-text-secondary">Agents with Errors:</span>
            <span className="ml-2 text-brand-text-primary font-medium">
              {agentsEncounteringErrors.join(', ')}
            </span>
          </div>
          <div>
            <span className="text-brand-text-secondary">Total Retry Attempts:</span>
            <span className="ml-2 text-brand-text-primary font-medium">{retryAttempts}</span>
          </div>
          <div>
            <span className="text-brand-text-secondary">Error Types:</span>
            <span className="ml-2 text-brand-text-primary font-medium">
              {specificErrors.join(', ')}
            </span>
          </div>
          <div>
            <span className="text-brand-text-secondary">Impact:</span>
            <span className="ml-2 text-brand-text-primary font-medium">{impactOnAnalysis}</span>
          </div>
        </div>
      </div>

      {/* Adaptation Strategies */}
      {adaptationStrategies.length > 0 && (
        <div className="mb-6">
          <h5 className="text-lg font-semibold text-brand-text-primary mb-3">Adaptation Strategies</h5>
          <div className="space-y-2">
            {adaptationStrategies.map((strategy, index) => (
              <div key={index} className="flex items-start">
                <span className="text-blue-400 mr-2">•</span>
                <span className="text-brand-text-primary">{strategy}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Detailed Retry Information */}
      <div>
        <h5 className="text-lg font-semibold text-brand-text-primary mb-3">Detailed Retry Information</h5>
        <div className="space-y-4">
          {retryDetails.map((detail, index) => (
            <div key={index} className="border border-brand-border rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h6 className="font-semibold text-brand-text-primary">{detail.agent}</h6>
                  <p className="text-sm text-brand-text-secondary">{detail.specialization}</p>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-brand-text-secondary">Tool:</span>
                  <code className="text-xs bg-brand-bg px-2 py-1 rounded text-brand-text-primary">
                    {detail.tool}
                  </code>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3 text-sm">
                <div>
                  <span className="text-brand-text-secondary">Total Attempts:</span>
                  <span className="ml-1 text-brand-text-primary font-medium">{detail.totalAttempts}</span>
                </div>
                <div>
                  <span className="text-brand-text-secondary">Final Status:</span>
                  <span className={`ml-1 font-medium ${
                    detail.finalStatus === 'success' ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {detail.finalStatus === 'success' ? '✅ Success' : '❌ Failed'}
                  </span>
                </div>
                {detail.adaptationStrategy && (
                  <div>
                    <span className="text-brand-text-secondary">Strategy:</span>
                    <span className="ml-1 text-brand-text-primary">{detail.adaptationStrategy}</span>
                  </div>
                )}
              </div>

              {/* Retry Sequence */}
              <div>
                <h7 className="text-sm font-semibold text-brand-text-primary block mb-2">Retry Sequence:</h7>
                <div className="space-y-2">
                  {detail.retrySequence.map((attempt, attemptIndex) => (
                    <div key={attemptIndex} className="bg-brand-bg/30 rounded p-3">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-brand-text-primary">
                          Attempt {attempt.attemptNumber}
                        </span>
                        <span className={`text-xs px-2 py-1 rounded ${
                          attempt.status === 'success' 
                            ? 'bg-green-500/20 text-green-400' 
                            : 'bg-red-500/20 text-red-400'
                        }`}>
                          {attempt.status === 'success' ? '✅ Success' : '❌ Error'}
                        </span>
                      </div>
                      
                      <div className="text-xs space-y-1">
                        <div>
                          <span className="text-brand-text-secondary">Input:</span>
                          <code className="ml-1 bg-brand-bg px-1 rounded text-brand-text-primary">
                            {typeof attempt.input === 'string' ? attempt.input : JSON.stringify(attempt.input)}
                          </code>
                        </div>
                        
                        {attempt.status === 'error' && (
                          <>
                            {attempt.errorType && (
                              <div>
                                <span className="text-brand-text-secondary">Error Type:</span>
                                <span className="ml-1 text-red-400">{attempt.errorType}</span>
                              </div>
                            )}
                            {attempt.errorMessage && (
                              <div>
                                <span className="text-brand-text-secondary">Error Message:</span>
                                <span className="ml-1 text-red-400">{attempt.errorMessage}</span>
                              </div>
                            )}
                            {attempt.receivedData && (
                              <div>
                                <span className="text-brand-text-secondary">Received Data:</span>
                                <code className="ml-1 bg-brand-bg px-1 rounded text-brand-text-primary">
                                  {attempt.receivedData}
                                </code>
                              </div>
                            )}
                            {attempt.expectedFormat && (
                              <div>
                                <span className="text-brand-text-secondary">Expected Format:</span>
                                <span className="ml-1 text-brand-text-primary">{attempt.expectedFormat}</span>
                              </div>
                            )}
                          </>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default RetryAnalysisCard; 