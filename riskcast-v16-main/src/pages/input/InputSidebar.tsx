/**
 * Input Sidebar - Navigation + Mode Toggle + Draft Info
 */

import React from 'react';
import { 
  Ship, Package, Calendar, DollarSign, Users, Layers, UploadCloud,
  CheckCircle2, Circle, XCircle, Clock
} from 'lucide-react';
import { designTokens } from '@/ui/design-tokens';

interface InputSidebarProps {
  mode: 'basic' | 'advanced';
  onModeChange: (mode: 'basic' | 'advanced') => void;
  activeSection: string;
  onSectionChange: (section: string) => void;
  lastSaved: Date | null;
  onDiscard: () => void;
}

const SECTIONS = [
  { id: 'route', label: 'Route', icon: Ship },
  { id: 'schedule', label: 'Schedule', icon: Calendar },
  { id: 'cargo', label: 'Cargo', icon: Package },
  { id: 'value', label: 'Value', icon: DollarSign },
  { id: 'parties', label: 'Parties', icon: Users },
  { id: 'modules', label: 'Modules', icon: Layers },
  { id: 'upload', label: 'Upload', icon: UploadCloud },
];

export const InputSidebar: React.FC<InputSidebarProps> = ({
  mode,
  onModeChange,
  activeSection,
  onSectionChange,
  lastSaved,
  onDiscard,
}) => {
  const formatLastSaved = (date: Date | null) => {
    if (!date) return 'Not saved';
    
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    return date.toLocaleDateString();
  };
  
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
      }}
    >
      {/* Mode Toggle */}
      <div
        style={{
          marginBottom: designTokens.spacing['2xl'],
        }}
      >
        <div
          style={{
            padding: designTokens.spacing.md,
            backgroundColor: 'rgba(255, 255, 255, 0.03)',
            border: `1px solid rgba(255, 255, 255, 0.08)`,
            borderRadius: designTokens.radii.lg,
            display: 'flex',
            gap: designTokens.spacing.xs,
          }}
        >
          <button
            onClick={() => onModeChange('basic')}
            style={{
              flex: 1,
              padding: `${designTokens.spacing.sm} ${designTokens.spacing.md}`,
              borderRadius: designTokens.radii.md,
              backgroundColor: mode === 'basic' ? 'rgba(110, 243, 255, 0.15)' : 'transparent',
              color: mode === 'basic' ? designTokens.colors.primaryNeon : designTokens.colors.textMuted,
              border: 'none',
              fontSize: '13px',
              fontFamily: designTokens.typography.fontFamily,
              fontWeight: 600,
              cursor: 'pointer',
              transition: designTokens.transitions.normal,
            }}
          >
            Basic
          </button>
          <button
            onClick={() => onModeChange('advanced')}
            style={{
              flex: 1,
              padding: `${designTokens.spacing.sm} ${designTokens.spacing.md}`,
              borderRadius: designTokens.radii.md,
              backgroundColor: mode === 'advanced' ? 'rgba(110, 243, 255, 0.15)' : 'transparent',
              color: mode === 'advanced' ? designTokens.colors.primaryNeon : designTokens.colors.textMuted,
              border: 'none',
              fontSize: '13px',
              fontFamily: designTokens.typography.fontFamily,
              fontWeight: 600,
              cursor: 'pointer',
              transition: designTokens.transitions.normal,
            }}
          >
            Advanced
          </button>
        </div>
      </div>
      
      {/* Navigation */}
      <nav
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: designTokens.spacing.sm,
          flex: 1,
        }}
      >
        {SECTIONS.map((section) => {
          const Icon = section.icon;
          const isActive = activeSection === section.id;
          
          return (
            <button
              key={section.id}
              onClick={() => {
                onSectionChange(section.id);
                // Scroll to section
                const element = document.getElementById(`section-${section.id}`);
                element?.scrollIntoView({ behavior: 'smooth', block: 'start' });
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: designTokens.spacing.md,
                padding: `${designTokens.spacing.md} ${designTokens.spacing.lg}`,
                backgroundColor: isActive ? 'rgba(110, 243, 255, 0.08)' : 'transparent',
                border: 'none',
                borderLeft: isActive ? `3px solid ${designTokens.colors.primaryNeon}` : '3px solid transparent',
                borderRadius: designTokens.radii.md,
                color: isActive ? designTokens.colors.primaryNeon : designTokens.colors.textMuted,
                fontSize: '14px',
                fontFamily: designTokens.typography.fontFamily,
                fontWeight: isActive ? 600 : 500,
                cursor: 'pointer',
                textAlign: 'left',
                transition: designTokens.transitions.normal,
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
                  e.currentTarget.style.color = designTokens.colors.textDefault;
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.currentTarget.style.backgroundColor = 'transparent';
                  e.currentTarget.style.color = designTokens.colors.textMuted;
                }
              }}
            >
              <Icon size={18} />
              <span>{section.label}</span>
            </button>
          );
        })}
      </nav>
      
      {/* Draft Info */}
      <div
        style={{
          marginTop: 'auto',
          paddingTop: designTokens.spacing['2xl'],
          borderTop: `1px solid rgba(255, 255, 255, 0.08)`,
        }}
      >
        <div
          style={{
            marginBottom: designTokens.spacing.lg,
            fontSize: '12px',
            color: designTokens.colors.textMuted,
            fontFamily: designTokens.typography.fontFamily,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: designTokens.spacing.sm,
              marginBottom: designTokens.spacing.xs,
            }}
          >
            <Clock size={14} />
            <span>Draft saved {formatLastSaved(lastSaved)}</span>
          </div>
        </div>
        
        <button
          onClick={onDiscard}
          style={{
            width: '100%',
            padding: `${designTokens.spacing.sm} ${designTokens.spacing.md}`,
            backgroundColor: 'transparent',
            border: `1px solid rgba(255, 255, 255, 0.08)`,
            borderRadius: designTokens.radii.md,
            color: designTokens.colors.textMuted,
            fontSize: '13px',
            fontFamily: designTokens.typography.fontFamily,
            fontWeight: 500,
            cursor: 'pointer',
            transition: designTokens.transitions.normal,
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = designTokens.colors.danger;
            e.currentTarget.style.color = designTokens.colors.danger;
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)';
            e.currentTarget.style.color = designTokens.colors.textMuted;
          }}
        >
          Discard Draft
        </button>
      </div>
    </div>
  );
};

export default InputSidebar;
