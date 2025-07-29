import React from 'react';
import { AgentFailure } from '../../frontend/src/types';
import XCircleIcon from '../icons/XCircleIcon';

const AgentFailureCard: React.FC<{ failure: AgentFailure }> = ({ failure }) => (
    <div className="bg-brand-surface p-6 rounded-lg border border-brand-danger transform transition-transform duration-300 hover:scale-[1.02]">
        <div className="flex items-center justify-between">
            <h4 className="text-xl font-bold text-brand-danger">{failure.agentName}</h4>
            <XCircleIcon className="w-6 h-6 text-brand-danger" />
        </div>
        <p className="text-sm text-brand-text-secondary mt-2 mb-3 italic">Task: {failure.task}</p>
        <div className="p-3 bg-red-900/40 rounded">
             <p className="text-sm font-semibold text-red-300 mb-1">Error Details:</p>
             <p className="text-sm text-red-300 font-mono">{failure.error}</p>
        </div>
    </div>
);

export default AgentFailureCard;