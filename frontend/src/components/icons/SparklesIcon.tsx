
import React from 'react';

const SparklesIcon: React.FC<{ className?: string }> = ({ className = 'w-6 h-6' }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    className={className}
    fill="none"
    viewBox="0 0 24 24"
    stroke="currentColor"
    strokeWidth={2}
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M5 3v4M3 5h4M19 3v4M17 5h4M12 2v4M10 4h4M3 21v-4M5 19H1M19 21v-4M21 19h-4M12 22v-4M14 20h-4M5 12H1M12 5V1M19 12h4M12 19v4"
    />
  </svg>
);

export default SparklesIcon;
