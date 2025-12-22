/**
 * Main application layout with navigation.
 */

import { Link, useLocation } from 'react-router-dom';
import { clsx } from 'clsx';
import { 
  Settings, 
  Phone, 
  LayoutDashboard,
  Radio,
} from 'lucide-react';

interface NavItem {
  to: string;
  label: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  { to: '/', label: 'Dashboard', icon: <LayoutDashboard className="h-5 w-5" /> },
  { to: '/config', label: 'Configuration', icon: <Settings className="h-5 w-5" /> },
  { to: '/calls', label: 'Calls', icon: <Phone className="h-5 w-5" /> },
];

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-3">
              <div className="flex items-center justify-center w-9 h-9 bg-indigo-600 rounded-lg">
                <Radio className="h-5 w-5 text-white" />
              </div>
              <span className="text-lg font-semibold text-slate-900">
                Voice Agent
              </span>
            </Link>

            {/* Navigation */}
            <nav className="flex items-center gap-1">
              {navItems.map((item) => {
                const isActive = item.to === '/' 
                  ? location.pathname === '/'
                  : location.pathname.startsWith(item.to);
                
                return (
                  <Link
                    key={item.to}
                    to={item.to}
                    className={clsx(
                      'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium',
                      'transition-colors duration-150',
                      {
                        'bg-indigo-50 text-indigo-700': isActive,
                        'text-slate-600 hover:bg-slate-100 hover:text-slate-900': !isActive,
                      }
                    )}
                  >
                    {item.icon}
                    <span className="hidden sm:inline">{item.label}</span>
                  </Link>
                );
              })}
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
}

