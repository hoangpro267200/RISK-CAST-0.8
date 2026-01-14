/**
 * Breadcrumb Component
 * 
 * Enterprise navigation breadcrumb for Results page context.
 * Pattern: Dashboard > Shipments > SH-{id} > Risk Analysis
 */

import React from 'react';
import { ChevronRight, Home } from 'lucide-react';

export interface BreadcrumbItem {
  label: string;
  href?: string;
  icon?: React.ReactNode;
  current?: boolean;
}

export interface BreadcrumbProps {
  items: BreadcrumbItem[];
  className?: string;
}

export const Breadcrumb: React.FC<BreadcrumbProps> = ({ items, className = '' }) => {
  const handleClick = (href: string | undefined, e: React.MouseEvent) => {
    if (!href) return;
    
    // For internal navigation, use history API
    if (href.startsWith('/')) {
      e.preventDefault();
      window.history.pushState({}, '', href);
      window.dispatchEvent(new PopStateEvent('popstate'));
    }
  };

  return (
    <nav 
      aria-label="Breadcrumb" 
      className={`flex items-center ${className}`}
    >
      <ol className="flex items-center gap-1 text-sm">
        {items.map((item, index) => (
          <li key={index} className="flex items-center">
            {index > 0 && (
              <ChevronRight 
                className="w-4 h-4 mx-1.5 text-white/30 flex-shrink-0" 
                aria-hidden="true"
              />
            )}
            
            {item.current ? (
              <span 
                className="flex items-center gap-1.5 text-white/90 font-medium"
                aria-current="page"
              >
                {item.icon}
                {item.label}
              </span>
            ) : item.href ? (
              <a
                href={item.href}
                onClick={(e) => handleClick(item.href, e)}
                className="flex items-center gap-1.5 text-white/60 hover:text-white/90 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900 rounded px-1 -mx-1"
              >
                {item.icon}
                {item.label}
              </a>
            ) : (
              <span className="flex items-center gap-1.5 text-white/60">
                {item.icon}
                {item.label}
              </span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
};

/**
 * Pre-built breadcrumb for Results page
 */
export interface ResultsBreadcrumbProps {
  shipmentId?: string;
  className?: string;
}

export const ResultsBreadcrumb: React.FC<ResultsBreadcrumbProps> = ({ 
  shipmentId = 'Unknown',
  className = ''
}) => {
  const items: BreadcrumbItem[] = [
    {
      label: 'Dashboard',
      href: '/',
      icon: <Home className="w-3.5 h-3.5" />
    },
    {
      label: 'Shipments',
      href: '/shipments'
    },
    {
      label: `SH-${shipmentId}`,
      href: `/shipments/${shipmentId}`
    },
    {
      label: 'Risk Analysis',
      current: true
    }
  ];

  return <Breadcrumb items={items} className={className} />;
};
