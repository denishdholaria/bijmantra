import { ReactNode } from 'react';
import { useLocation, Link } from 'react-router-dom';
import { Bell, Home, QrCode, RefreshCw, Wifi, WifiOff } from 'lucide-react';
import { OfflineIndicator } from '@/components/OfflineIndicator';
import { useSyncStore } from '@/store/sync'; // We might need to create this store or use SyncService directly

interface FieldLayoutProps {
  children: ReactNode;
  title?: string;
  showBack?: boolean;
}

export function FieldLayout({ children, title = 'FieldScout', showBack = false }: FieldLayoutProps) {
  const location = useLocation();
  const isOnline = navigator.onLine; // This should be reactive ideally

  return (
    <div className="flex flex-col h-screen bg-gray-50 text-gray-900">
      {/* Mobile Header */}
      <header className="sticky top-0 z-50 bg-green-600 text-white shadow-md">
        <div className="flex items-center justify-between px-4 h-14">
          <div className="flex items-center gap-2">
            <span className="font-bold text-lg tracking-tight">{title}</span>
            <OfflineIndicator className="text-white" />
          </div>
          <div className="flex items-center gap-2">
            <button className="p-2 hover:bg-green-700 rounded-full">
              <Bell className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content (Scrollable) */}
      <main className="flex-1 overflow-y-auto p-4 pb-20">
        <div className="max-w-md mx-auto">
          {children}
        </div>
      </main>

      {/* Bottom Navigation */}
      <nav className="fixed bottom-0 w-full bg-white border-t border-gray-200 pb-safe">
        <div className="flex justify-around items-center h-16">
          <Link 
            to="/field/dashboard" 
            className={`flex flex-col items-center p-2 rounded-lg ${location.pathname.includes('/dashboard') ? 'text-green-600' : 'text-gray-500'}`}
          >
            <Home className="w-6 h-6" />
            <span className="text-xs mt-1">Home</span>
          </Link>
          
          <Link 
            to="/field/scan" 
            className={`flex flex-col items-center p-2 rounded-lg ${location.pathname.includes('/scan') ? 'text-green-600' : 'text-gray-500'}`}
          >
            <div className="bg-green-100 p-2 rounded-full -mt-6 border-4 border-white shadow-sm">
              <QrCode className="w-6 h-6 text-green-700" />
            </div>
            <span className="text-xs mt-1 font-medium">Scan</span>
          </Link>

          <Link 
            to="/field/sync" 
            className={`flex flex-col items-center p-2 rounded-lg ${location.pathname.includes('/sync') ? 'text-green-600' : 'text-gray-500'}`}
          >
            <RefreshCw className="w-6 h-6" />
            <span className="text-xs mt-1">Sync</span>
          </Link>
        </div>
      </nav>
    </div>
  );
}

export default FieldLayout;
