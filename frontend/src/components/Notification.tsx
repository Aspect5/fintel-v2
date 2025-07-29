import React, { useEffect } from 'react';
import CheckCircleIcon from './icons/CheckCircleIcon';
import XCircleIcon from './icons/XCircleIcon';
import InformationCircleIcon from './icons/InformationCircleIcon';

interface NotificationProps {
  message: string;
  type: 'success' | 'error' | 'info';
  onClose: () => void;
}

const icons = {
  success: <CheckCircleIcon className="w-6 h-6 text-brand-success" />,
  error: <XCircleIcon className="w-6 h-6 text-brand-danger" />,
  info: <InformationCircleIcon className="w-6 h-6 text-brand-info" />,
};

const colors = {
    success: 'border-brand-success',
    error: 'border-brand-danger',
    info: 'border-brand-info',
};

const Notification: React.FC<NotificationProps> = ({ message, type, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose();
    }, 5000); // Auto-close after 5 seconds

    return () => {
      clearTimeout(timer);
    };
  }, [onClose]);

  return (
    <div className={`fixed bottom-8 right-8 z-[100] animate-slide-in-up`}>
      <div className={`flex items-center p-4 bg-brand-surface rounded-lg shadow-2xl border-l-4 ${colors[type]}`}>
        <div className="flex-shrink-0">{icons[type]}</div>
        <div className="ml-3">
          <p className="text-sm font-medium text-brand-text-primary">{message}</p>
        </div>
        <div className="ml-4 flex-shrink-0">
          <button onClick={onClose} className="inline-flex text-brand-text-secondary hover:text-brand-text-primary transition-colors">
            <span className="sr-only">Close</span>
            <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        </div>
      </div>
      <style>{`
          @keyframes slide-in-up {
              from { transform: translateY(100%); opacity: 0; }
              to { transform: translateY(0); opacity: 1; }
          }
          .animate-slide-in-up {
              animation: slide-in-up 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
          }
      `}</style>
    </div>
  );
};

export default Notification;
