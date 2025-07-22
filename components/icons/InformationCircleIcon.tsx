import React from 'react';

const InformationCircleIcon: React.FC<React.SVGProps<SVGSVGElement>> = (props) => (
  <svg 
    xmlns="http://www.w3.org/2000/svg" 
    fill="none" 
    viewBox="0 0 24 24" 
    strokeWidth={1.5} 
    stroke="currentColor" 
    {...props}
  >
    <path 
      strokeLinecap="round" 
      strokeLinejoin="round" 
      d="M11.25 11.25l.25 5.25m.25-5.25v-2.5m0 0l-2.5-2.5M12 21a9 9 0 110-18 9 9 0 010 18zm0 0a9 9 0 000-18 9 9 0 000 18z" 
    />
  </svg>
);

export default InformationCircleIcon;
