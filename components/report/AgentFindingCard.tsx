import React from 'react';
import { AgentFinding } from '../../frontend/src/types';

const AgentFindingCard: React.FC<{ finding: AgentFinding }> = ({ finding }) => (
    <div className="bg-brand-surface p-6 rounded-lg border border-brand-border transform transition-transform duration-300 hover:scale-[1.02] hover:border-brand-primary">
        <h4 className="text-xl font-bold text-brand-primary">{finding.agentName}</h4>
        <p className="text-sm text-brand-text-secondary mb-3">{finding.specialization}</p>
        <p className="mb-4 text-brand-text-primary">{finding.summary}</p>
        <ul className="space-y-2 list-disc list-inside">
            {finding.details.map((detail, i) => (
                <li key={i} className="text-brand-text-secondary">{detail}</li>
            ))}
        </ul>
    </div>
);

export default AgentFindingCard;