import React, { useState } from 'react';
import ReevaChat from '../../pages/ReevaChat';
import { XMarkIcon, ChatBubbleLeftRightIcon } from '@heroicons/react/24/outline'; // Assuming basic heroicons are available or replace with SVG

export default function ReevaSidebar() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {/* Floating Trigger Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 p-4 bg-emerald-600 text-white rounded-full shadow-lg hover:bg-emerald-700 transition-all z-50 flex items-center justify-center"
          title="Ask REEVA"
        >
          <ChatBubbleLeftRightIcon className="h-6 w-6" />
        </button>
      )}

      {/* Sidebar Panel */}
      <div 
        className={`fixed top-0 right-0 h-full w-96 bg-white shadow-2xl transform transition-transform duration-300 z-50 border-l border-gray-200 ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-100 bg-emerald-50">
          <h2 className="font-bold text-emerald-900 flex items-center gap-2">
            <span>🌱</span> REEVA Assistant
          </h2>
          <button 
            onClick={() => setIsOpen(false)}
            className="p-1 hover:bg-emerald-100 rounded-full text-emerald-700"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        {/* Content - The Chat Component */}
        <div className="h-[calc(100%-60px)] overflow-hidden">
             {/* We wrap the chat in a container to fit the sidebar height */}
             <div className="h-full overflow-y-auto p-2">
                <ReevaChat />
             </div>
        </div>
      </div>
    </>
  );
}
