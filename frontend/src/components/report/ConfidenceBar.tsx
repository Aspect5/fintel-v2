import React from 'react';

const ConfidenceBar: React.FC<{ level: number }> = ({ level }) => {
  const percentage = Math.round(level * 100);
  let barColor = 'bg-brand-success';
  if (percentage < 75) barColor = 'bg-brand-warning';
  if (percentage < 50) barColor = 'bg-brand-danger';

  return (
    <div className="w-full bg-brand-border rounded-full h-2.5">
      <div
        className={`${barColor} h-2.5 rounded-full`}
        style={{ width: `${percentage}%` }}
      ></div>
    </div>
  );
};

export default ConfidenceBar;