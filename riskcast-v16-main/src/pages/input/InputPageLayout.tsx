/**
 * Input Page Layout - 12-column grid with 2-column split
 * 
 * Layout Structure:
 * - Sidebar (240px fixed)
 * - Form Panel (8 columns)
 * - Preview Panel (4 columns, sticky)
 * - CTA Bar (sticky bottom)
 */

import React from 'react';
import { designTokens } from '@/ui/design-tokens';

interface InputPageLayoutProps {
  sidebar: React.ReactNode;
  formPanel: React.ReactNode;
  previewPanel: React.ReactNode;
  ctaBar: React.ReactNode;
}

export const InputPageLayout: React.FC<InputPageLayoutProps> = ({
  sidebar,
  formPanel,
  previewPanel,
  ctaBar,
}) => {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '240px 1fr',
        minHeight: '100vh',
        backgroundColor: designTokens.colors.bg0,
        color: designTokens.colors.textStrong,
      }}
    >
      {/* Sidebar */}
      <aside
        style={{
          position: 'fixed',
          left: 0,
          top: 64, // Header height
          width: '240px',
          height: 'calc(100vh - 64px)',
          backgroundColor: designTokens.colors.bg1,
          backdropFilter: designTokens.blur.md,
          borderRight: `1px solid rgba(255, 255, 255, 0.08)`,
          padding: designTokens.spacing['2xl'],
          overflowY: 'auto',
        }}
      >
        {sidebar}
      </aside>
      
      {/* Main Content Area */}
      <main
        style={{
          marginLeft: '240px',
          paddingTop: '64px', // Header height
          paddingBottom: '80px', // CTA bar height
        }}
      >
        <div
          style={{
            maxWidth: '1400px',
            margin: '0 auto',
            padding: `${designTokens.spacing['2xl']} ${designTokens.spacing['3xl']}`,
          }}
        >
          {/* 12-column grid */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(12, 1fr)',
              gap: designTokens.spacing['2xl'],
            }}
          >
            {/* Form Panel - 8 columns */}
            <div
              style={{
                gridColumn: 'span 8',
              }}
            >
              {formPanel}
            </div>
            
            {/* Preview Panel - 4 columns, sticky */}
            <div
              style={{
                gridColumn: 'span 4',
                position: 'sticky',
                top: '80px', // Header + padding
                alignSelf: 'start',
                maxHeight: 'calc(100vh - 160px)',
                overflowY: 'auto',
              }}
            >
              {previewPanel}
            </div>
          </div>
        </div>
      </main>
      
      {/* Sticky CTA Bar */}
      <div
        style={{
          position: 'fixed',
          bottom: 0,
          left: '240px',
          right: 0,
          height: '80px',
          zIndex: 1000,
        }}
      >
        {ctaBar}
      </div>
    </div>
  );
};
