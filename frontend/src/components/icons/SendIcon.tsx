
import React from 'react';

const SendIcon: React.FC<{ className?: string }> = ({ className = 'w-5 h-5' }) => (
  <svg 
    xmlns="http://www.w3.org/2000/svg" 
    viewBox="0 0 20 20" 
    fill="currentColor" 
    className={className}
  >
    <path d="M3.105 2.289a.75.75 0 00-.826.95l1.414 4.949a.75.75 0 00.95.54l3.85-1.418a.75.75 0 010 1.396l-3.85 1.418a.75.75 0 00-.95.54l-1.414 4.95a.75.75 0 00.826.95l14.25-6.333a.75.75 0 000-1.417L3.105 2.289z" />
  </svg>
);

export default SendIcon;
