
import React from 'react';

const SpinnerIcon: React.FC<{ className?: string }> = ({ className = 'w-5 h-5' }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    className={className}
    fill="none"
    viewBox="0 0 24 24"
    stroke="currentColor"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M12 6v6m0 0v6m0-6h6m-6 0H6"
      className="opacity-0 animate-spin"
      style={{ animation: 'spin 1s linear infinite' }}
    />
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M12 3a9 9 0 100 18 9 9 0 000-18z"
      className="opacity-25"
    />
    <style>{`
      @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
      }
    `}</style>
  </svg>
);

export default SpinnerIcon;
