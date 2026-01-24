/**
 * Input Page Layout - Desktop split layout with responsive breakpoints
 * 
 * Layout Structure (no external header - self-contained):
 * - Sidebar (240px fixed, collapses on mobile)
 * - Form Panel (flex: 1 1 auto, min-width: 560px, max-width: 760px)
 * - Preview Panel (flex: 0 0 420px, min-width: 360px, max-width: 520px, sticky)
 * - CTA Bar (sticky bottom)
 * 
 * Responsive:
 * - Desktop (>= 1280px): 2-column layout (form + preview)
 * - Tablet (768px - 1279px): Single column, preview below form
 * - Mobile (< 768px): Single column, sidebar collapses, no preview
 */

import React, { useState, useEffect } from 'react';
import { designTokens } from '@/ui/design-tokens';

interface InputPageLayoutProps {
  sidebar: React.ReactNode;
  formPanel: React.ReactNode;
  previewPanel: React.ReactNode;
  ctaBar: React.ReactNode;
}

// Layout constants
const SIDEBAR_WIDTH = 240;
const FORM_MIN_WIDTH = 560;
const FORM_MAX_WIDTH = 760;
const PREVIEW_WIDTH = 420;
const PREVIEW_MIN_WIDTH = 360;
const PREVIEW_MAX_WIDTH = 520;
const CTA_HEIGHT = 80;

export const InputPageLayout: React.FC<InputPageLayoutProps> = ({
  sidebar,
  formPanel,
  previewPanel,
  ctaBar,
}) => {
  const [windowWidth, setWindowWidth] = useState(() => {
    if (typeof window !== 'undefined') {
      return window.innerWidth;
    }
    return 1440; // Default desktop width
  });
  
  // Responsive breakpoints
  const isDesktop = windowWidth >= 1280;
  const isTablet = windowWidth >= 768 && windowWidth < 1280;
  const isMobile = windowWidth < 768;
  const showSidebar = windowWidth >= 768;

  useEffect(() => {
    // Set initial width on mount
    if (typeof window !== 'undefined') {
      setWindowWidth(window.innerWidth);
    }
    
    const handleResize = () => {
      setWindowWidth(window.innerWidth);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <div
      style={{
        display: 'flex',
        minHeight: '100vh',
        backgroundColor: designTokens.colors.bg0,
        color: designTokens.colors.textStrong,
        overflow: 'hidden', // Prevent any scroll on root
        position: 'relative',
      }}
    >
      {/* Sidebar - Fixed position, starts from top:0 (no header) */}
      {showSidebar && (
        <aside
          style={{
            position: 'fixed',
            left: 0,
            top: 0,
            width: `${SIDEBAR_WIDTH}px`,
            height: '100vh',
            backgroundColor: designTokens.colors.bg1,
            backdropFilter: designTokens.blur.md,
            borderRight: `1px solid rgba(255, 255, 255, 0.08)`,
            padding: designTokens.spacing['2xl'],
            paddingTop: designTokens.spacing['3xl'],
            overflowY: 'auto',
            overflowX: 'hidden',
            zIndex: 100,
            boxSizing: 'border-box',
          }}
        >
          {sidebar}
        </aside>
      )}
      
      {/* Main Content Area */}
      <main
        style={{
          marginLeft: showSidebar ? `${SIDEBAR_WIDTH}px` : 0,
          paddingBottom: `${CTA_HEIGHT}px`,
          width: showSidebar ? `calc(100% - ${SIDEBAR_WIDTH}px)` : '100%',
          minHeight: '100vh',
          overflowY: 'auto',
          overflowX: 'hidden',
          boxSizing: 'border-box',
        }}
      >
        <div
          style={{
            maxWidth: '1200px',
            margin: '0 auto',
            padding: isMobile 
              ? `${designTokens.spacing.xl} ${designTokens.spacing.lg}`
              : `${designTokens.spacing['2xl']} ${designTokens.spacing['2xl']}`,
            boxSizing: 'border-box',
          }}
        >
          {/* Desktop: 2-column flex layout */}
          {isDesktop ? (
            <div
              style={{
                display: 'flex',
                gap: designTokens.spacing['2xl'],
                alignItems: 'flex-start',
                width: '100%',
              }}
            >
              {/* Form Panel - Flex grow with constraints */}
              <div
                style={{
                  flex: '1 1 auto',
                  minWidth: `${FORM_MIN_WIDTH}px`,
                  maxWidth: `${FORM_MAX_WIDTH}px`,
                  boxSizing: 'border-box',
                }}
              >
                {formPanel}
              </div>
              
              {/* Preview Panel - Fixed width, sticky */}
              <div
                style={{
                  flex: `0 0 ${PREVIEW_WIDTH}px`,
                  minWidth: `${PREVIEW_MIN_WIDTH}px`,
                  maxWidth: `${PREVIEW_MAX_WIDTH}px`,
                  position: 'sticky',
                  top: designTokens.spacing['2xl'],
                  alignSelf: 'flex-start',
                  maxHeight: `calc(100vh - ${CTA_HEIGHT + 48}px)`,
                  overflowY: 'auto',
                  overflowX: 'hidden',
                  boxSizing: 'border-box',
                }}
              >
                {previewPanel}
              </div>
            </div>
          ) : (
            /* Tablet/Mobile: Single column */
            <div
              style={{
                width: '100%',
                maxWidth: `${FORM_MAX_WIDTH}px`,
                margin: '0 auto',
              }}
            >
              {formPanel}
              {/* Show preview on tablet only */}
              {isTablet && (
                <div style={{ 
                  marginTop: designTokens.spacing['2xl'],
                  maxWidth: `${PREVIEW_MAX_WIDTH}px`,
                }}>
                  {previewPanel}
                </div>
              )}
            </div>
          )}
        </div>
      </main>
      
      {/* Sticky CTA Bar */}
      <div
        style={{
          position: 'fixed',
          bottom: 0,
          left: showSidebar ? `${SIDEBAR_WIDTH}px` : 0,
          right: 0,
          height: `${CTA_HEIGHT}px`,
          zIndex: 1000,
          boxSizing: 'border-box',
        }}
      >
        {ctaBar}
      </div>
    </div>
  );
};
