import React from 'react';
import { Report } from '../types';
import XCircleIcon from './icons/XCircleIcon';
import ReportDisplay from './ReportDisplay';

interface ReportModalProps {
  report: Report | null;
  onClose: () => void;
  isVisible: boolean;
  query?: string;
}

const ReportModal: React.FC<ReportModalProps> = ({ report, onClose, isVisible, query = '' }) => {
  if (!isVisible || !report) return null;

  return (
    <div 
      className="fixed inset-0 z-[9999] flex items-center justify-center p-4 pointer-events-none" 
    >
      {/* Semi-transparent backdrop that doesn't block the entire screen */}
      <div 
        className="absolute inset-0 bg-black/20 pointer-events-auto" 
        onClick={onClose}
      />
      
      {/* Modal content */}
      <div 
        className="relative w-full max-w-6xl h-[90vh] bg-brand-surface flex flex-col rounded-xl shadow-2xl overflow-hidden pointer-events-auto" 
        onClick={e => e.stopPropagation()}
      >
        <header className="flex items-center justify-between p-6 border-b border-brand-border bg-brand-surface flex-shrink-0">
          <div>
            <h2 className="text-2xl font-bold text-brand-text-primary">📊 Investment Analysis Report</h2>
            <p className="text-sm text-brand-text-secondary mt-1">
              Comprehensive analysis completed successfully
            </p>
          </div>
          <button 
            onClick={onClose} 
            className="text-brand-text-secondary hover:text-brand-text-primary transition-colors p-2 rounded-lg hover:bg-brand-bg"
            aria-label="Close report"
          >
            <XCircleIcon className="w-8 h-8" />
          </button>
        </header>
        
        <div className="flex-1 overflow-y-auto p-6">
          <ReportDisplay report={report} query={query} />
        </div>
      </div>
      
      <style>{`
        @keyframes fade-in {
          from { opacity: 0; transform: scale(0.95); }
          to { opacity: 1; transform: scale(1); }
        }
        .animate-fade-in { 
          animation: fade-in 0.3s ease-out forwards; 
        }
      `}</style>
    </div>
  );
};

export default ReportModal; 