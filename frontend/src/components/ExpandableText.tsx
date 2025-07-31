import React, { useState } from 'react';

interface ExpandableTextProps {
  content: string;
  maxLength?: number;
  className?: string;
  expandedClassName?: string;
  collapsedClassName?: string;
}

const ExpandableText: React.FC<ExpandableTextProps> = ({
  content,
  maxLength = 200,
  className = '',
  expandedClassName = '',
  collapsedClassName = ''
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const shouldTruncate = content.length > maxLength;
  const displayText = isExpanded || !shouldTruncate ? content : content.substring(0, maxLength) + '...';
  
  if (!shouldTruncate) {
    return (
      <div className={className}>
        {content}
      </div>
    );
  }
  
  return (
    <div className={className}>
      <div className={isExpanded ? expandedClassName : collapsedClassName}>
        {displayText}
      </div>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="text-brand-primary hover:text-brand-secondary text-sm font-medium mt-2 transition-colors duration-200"
      >
        {isExpanded ? 'Show Less' : 'Show More'}
      </button>
    </div>
  );
};

export default ExpandableText; 