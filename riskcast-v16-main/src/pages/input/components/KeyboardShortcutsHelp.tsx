/**
 * Keyboard Shortcuts Help Component
 * Shows available keyboard shortcuts
 */

import React, { useState } from 'react';
import { Keyboard, X } from 'lucide-react';
import { designTokens } from '@/ui/design-tokens';
import { GlassCard } from '@/components/GlassCard';

interface KeyboardShortcutsHelpProps {
  onClose?: () => void;
}

const SHORTCUTS = [
  { keys: ['Ctrl', 'S'], description: 'Save draft' },
  { keys: ['Enter'], description: 'Submit form (when ready)' },
  { keys: ['Escape'], description: 'Close dropdowns/modals' },
  { keys: ['Tab'], description: 'Navigate between fields' },
  { keys: ['Shift', 'Tab'], description: 'Navigate backwards' },
  { keys: ['1'], description: 'Jump to Route section' },
  { keys: ['2'], description: 'Jump to Schedule section' },
  { keys: ['3'], description: 'Jump to Cargo section' },
  { keys: ['4'], description: 'Jump to Value section' },
  { keys: ['5'], description: 'Jump to Parties section' },
  { keys: ['6'], description: 'Jump to Modules section' },
  { keys: ['7'], description: 'Jump to Upload section' },
  { keys: ['↑', '↓'], description: 'Navigate dropdown options' },
  { keys: ['←', '→'], description: 'Navigate pill groups' },
];

export const KeyboardShortcutsHelp: React.FC<KeyboardShortcutsHelpProps> = ({ onClose }) => {
  const [isOpen, setIsOpen] = useState(false);
  
  if (!isOpen) {
    return (
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        style={{
          position: 'fixed',
          bottom: '100px',
          right: '24px',
          width: '48px',
          height: '48px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: designTokens.colors.bg1,
          backdropFilter: designTokens.blur.md,
          border: `1px solid rgba(255, 255, 255, 0.08)`,
          borderRadius: '50%',
          color: designTokens.colors.textDefault,
          cursor: 'pointer',
          boxShadow: designTokens.shadows.lg,
          zIndex: 9999,
          transition: designTokens.transitions.normal,
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.backgroundColor = 'rgba(110, 243, 255, 0.1)';
          e.currentTarget.style.borderColor = designTokens.colors.primaryNeon;
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.backgroundColor = designTokens.colors.bg1;
          e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)';
        }}
        title="Keyboard shortcuts"
        aria-label="Show keyboard shortcuts"
      >
        <Keyboard size={20} />
      </button>
    );
  }
  
  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 10000,
        padding: designTokens.spacing['2xl'],
      }}
      onClick={() => {
        setIsOpen(false);
        onClose?.();
      }}
    >
      <GlassCard
        padding="lg"
        variant="default"
        onClick={(e: React.MouseEvent) => e.stopPropagation()}
        style={{ maxWidth: '600px', width: '100%', maxHeight: '80vh', overflowY: 'auto' }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: designTokens.spacing['2xl'],
          }}
        >
          <h2
            style={{
              fontSize: '24px',
              fontWeight: 700,
              color: designTokens.colors.textStrong,
              fontFamily: 'Orbitron, monospace',
            }}
          >
            Keyboard Shortcuts
          </h2>
          <button
            type="button"
            onClick={() => {
              setIsOpen(false);
              onClose?.();
            }}
            style={{
              width: '32px',
              height: '32px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: 'transparent',
              border: 'none',
              color: designTokens.colors.textMuted,
              cursor: 'pointer',
              borderRadius: designTokens.radii.md,
              transition: designTokens.transitions.fast,
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = designTokens.colors.textDefault;
              e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = designTokens.colors.textMuted;
              e.currentTarget.style.backgroundColor = 'transparent';
            }}
          >
            <X size={20} />
          </button>
        </div>
        
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: designTokens.spacing.md,
          }}
        >
          {SHORTCUTS.map((shortcut, index) => (
            <div
              key={index}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: designTokens.spacing.md,
                backgroundColor: 'rgba(255, 255, 255, 0.03)',
                borderRadius: designTokens.radii.md,
              }}
            >
              <span
                style={{
                  fontSize: '15px',
                  color: designTokens.colors.textDefault,
                  fontFamily: designTokens.typography.fontFamily,
                }}
              >
                {shortcut.description}
              </span>
              <div style={{ display: 'flex', gap: designTokens.spacing.xs, alignItems: 'center' }}>
                {shortcut.keys.map((key, keyIndex) => (
                  <React.Fragment key={keyIndex}>
                    <kbd
                      style={{
                        padding: `${designTokens.spacing.xs} ${designTokens.spacing.sm}`,
                        backgroundColor: 'rgba(255, 255, 255, 0.1)',
                        border: `1px solid rgba(255, 255, 255, 0.2)`,
                        borderRadius: designTokens.radii.sm,
                        fontSize: '12px',
                        fontFamily: 'monospace',
                        color: designTokens.colors.textStrong,
                        fontWeight: 600,
                      }}
                    >
                      {key}
                    </kbd>
                    {keyIndex < shortcut.keys.length - 1 && (
                      <span style={{ color: designTokens.colors.textMuted, fontSize: '12px' }}>+</span>
                    )}
                  </React.Fragment>
                ))}
              </div>
            </div>
          ))}
        </div>
      </GlassCard>
    </div>
  );
};
