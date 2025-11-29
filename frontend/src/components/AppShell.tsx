import { ReactNode } from 'react';
import BottomNav from './BottomNav';

interface AppShellProps {
  children: ReactNode;
}

export default function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center md:p-8">
      <div className="w-full max-w-[480px] min-h-[100vh] md:min-h-[90vh] bg-white md:rounded-3xl md:shadow-2xl overflow-hidden relative">
        <div className="h-full overflow-y-auto">
          {children}
        </div>
        <BottomNav />
      </div>
    </div>
  );
}
