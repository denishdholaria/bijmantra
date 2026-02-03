import React, { useState } from 'react';
import { RefreshCw } from 'lucide-react';

interface ChatResponse {
  response: string;
}

export function ReevaChat() {
  const [query, setQuery] = useState<string>('');
  const [response, setResponse] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  const handleAsk = async () => {
    if (!query) return;
    setLoading(true);
    setError('');
    setResponse('');

    try {
      const res = await fetch('http://localhost:8081/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });

      if (!res.ok) {
        throw new Error(`Error: ${res.statusText}`);
      }

      const data: ChatResponse = await res.json();
      setResponse(data.response);
    } catch (err: any) {
      setError(err.message || 'An unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 max-w-md mx-auto bg-white dark:bg-slate-800 rounded-xl shadow-md border border-gray-200 dark:border-slate-700">
      <h2 className="text-xl font-bold mb-4 text-emerald-800 dark:text-emerald-400">REEVA Assistant</h2>
      
      <div className="flex gap-2 mb-4">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask REEVA about trials..."
          className="flex-1 p-2 border border-gray-300 dark:border-slate-600 rounded bg-white dark:bg-slate-900 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          onKeyDown={(e) => e.key === 'Enter' && handleAsk()}
        />
        <button
          onClick={handleAsk}
          disabled={loading}
          className="px-4 py-2 bg-emerald-600 text-white rounded hover:bg-emerald-700 disabled:opacity-50"
        >
          {loading ? 'Thinking...' : 'Ask'}
        </button>
      </div>

      {error && (
        <div className="flex items-center justify-between p-3 mb-4 text-sm text-red-700 dark:text-red-300 bg-red-100 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded">
          <span>{error}</span>
          <button
            onClick={handleAsk}
            className="flex items-center gap-1 px-2 py-1 text-xs border border-red-300 dark:border-red-700 rounded hover:bg-red-200 dark:hover:bg-red-900/40"
          >
            <RefreshCw className="h-3 w-3" />
            Retry
          </button>
        </div>
      )}

      {response && (
        <div className="p-4 bg-gray-50 dark:bg-slate-900 rounded border border-gray-100 dark:border-slate-700">
          <p className="whitespace-pre-wrap text-gray-800 dark:text-gray-200">{response}</p>
        </div>
      )}
    </div>
  );
}

export default ReevaChat;
