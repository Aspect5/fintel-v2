// Deprecated legacy component. Kept temporarily for reference; not used.
import React from 'react';
import { Report } from '../types';

interface ReportDisplayProps {
  report: Report | null;
  isLoading?: boolean;
  query?: string;
}

const ReportDisplay: React.FC<ReportDisplayProps> = () => null;

export default ReportDisplay; 