/**
 * Sidebar Navigation - Figma Design Implementation
 */

'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  Zap, 
  TrendingUp, 
  AlertTriangle, 
  FlaskConical,
  Database
} from 'lucide-react';
import { cn } from '@/lib/utils';

const navItems = [
  {
    name: 'Intelligence',
    href: '/',
    icon: Zap,
  },
  {
    name: 'Forecast',
    href: '/forecasting',
    icon: TrendingUp,
  },
  {
    name: 'Anomalies',
    href: '/anomalies',
    icon: AlertTriangle,
    badge: 3,
  },
  {
    name: 'Models',
    href: '/models',
    icon: FlaskConical,
  },
  {
    name: 'Data trust',
    href: '/data-health',
    icon: Database,
  },
];

export function Sidebar() {
  const pathname = usePathname();
  
  return (
    <aside className="bg-[#10181b] border-r border-[#29383d] flex flex-col gap-8 min-h-screen pb-6 pt-8 px-4 w-[210px] shrink-0">
      {/* Logo and Identity */}
      <div className="flex flex-col gap-2 pl-2">
        <div className="flex gap-2 items-center">
          <div className="flex items-center justify-center w-6 h-6">
            <Zap className="w-5 h-5 text-[#bcf58a]" fill="#bcf58a" />
          </div>
          <span className="text-[#e8f0ec] font-semibold text-base">GridPulse</span>
        </div>
        <p className="text-[#93a7ab] text-xs">Energy, Decoded.</p>
      </div>
      
      {/* Workspace Selector */}
      <div className="bg-[#121d21] border border-[#29383d] rounded-lg px-3 py-2.5 flex items-center gap-2">
        <div className="bg-[#2a3d44] rounded-full w-6 h-6 flex items-center justify-center text-[#bcf58a] text-xs font-semibold">
          N
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-[#e8f0ec] text-xs font-medium truncate">Northbank campus</p>
          <p className="text-[#6b7f84] text-[10px]">Main meter · NB-01</p>
        </div>
        <svg className="w-4 h-4 text-[#6b7f84] shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l4-4 4 4m0 6l-4 4-4-4" />
        </svg>
      </div>
      
      {/* Navigation Section */}
      <nav className="flex flex-col">
        <p className="text-[#6b7f84] text-[10px] font-medium uppercase tracking-wider mb-3 px-2">WORKSPACE</p>
        <div className="flex flex-col gap-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-2.5 px-2.5 py-2 rounded-md text-sm transition-colors relative',
                  isActive
                    ? 'bg-[#1a2b30] text-[#bcf58a]'
                    : 'text-[#93a7ab] hover:bg-[#1a2b30]/50 hover:text-[#e8f0ec]'
                )}
              >
                <Icon className="w-4 h-4" />
                <span className="font-medium">{item.name}</span>
                {item.badge && (
                  <span className="ml-auto bg-[#f3bd75] text-[#0c1215] text-[10px] font-semibold px-1.5 py-0.5 rounded">
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </div>
      </nav>
      
      {/* Demo Environment Badge */}
      <div className="mt-auto">
        <div className="bg-[#1a2b30] border border-[#29383d] rounded-lg px-3 py-2.5">
          <div className="flex items-start gap-2 mb-1">
            <span className="bg-[#bcf58a] text-[#0c1215] text-[9px] font-bold px-1.5 py-0.5 rounded uppercase">
              DEMO ENVIRONMENT
            </span>
          </div>
          <p className="text-[#93a7ab] text-[10px] leading-relaxed">
            Illustrative energy data. No live meter connection.
          </p>
        </div>
      </div>
      
      {/* User Profile */}
      <div className="border-t border-[#29383d] pt-4">
        <div className="flex items-center gap-2 px-2">
          <div className="bg-[#2a3d44] rounded-full w-6 h-6 flex items-center justify-center text-[#bcf58a] text-xs font-semibold">
            AL
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[#e8f0ec] text-xs font-medium">Alex Lin</p>
            <p className="text-[#6b7f84] text-[10px]">Energy analyst</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
