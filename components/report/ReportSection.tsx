import React from 'react';

interface ReportSectionProps {
  title: string;
  borderColor?: string;
  children: React.ReactNode;
}

const ReportSection: React.FC<ReportSectionProps> = ({ title, borderColor = 'border-brand-border', children }) => (
  <section>
    <h3 className={`text-2xl font-semibold mb-4 text-white border-b-2 ${borderColor} pb-2`}>
      {title}
    </h3>
    {children}
  </section>
);

export default ReportSection;