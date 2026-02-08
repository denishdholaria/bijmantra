import { AlertTriangle } from 'lucide-react';

export function IntegrityBanner({ type = 'demo' }: { type?: 'demo' | 'fake-compute' }) {
  if (import.meta.env.PROD && type === 'fake-compute') return null; // Hide compute warnings in prod, only show in dev/preview

  return (
    <div className="bg-yellow-500/10 border-l-4 border-yellow-500 p-4 mb-6 rounded-r">
      <div className="flex items-center">
        <AlertTriangle className="h-5 w-5 text-yellow-600 mr-3" />
        <div>
          <h3 className="text-sm font-bold text-yellow-800 uppercase tracking-wide">
            {type === 'fake-compute' ? '⚠️ Under Construction' : '🧪 Demo Mode'}
          </h3>
          <p className="text-sm text-yellow-700 mt-1">
            {type === 'fake-compute' 
              ? 'This module is currently disconnected from real data. Values shown are placeholders.'
              : 'You are viewing demonstration data. Actions taken here will not affect production records.'}
          </p>
        </div>
      </div>
    </div>
  );
}