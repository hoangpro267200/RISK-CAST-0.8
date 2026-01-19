/**
 * Risk Modules Section - Section F
 */

import React from 'react';
import { Layers, Leaf, CloudRain, Anchor, Truck, TrendingUp, ShieldCheck } from 'lucide-react';
import { designTokens } from '@/ui/design-tokens';
import { GlassCard } from '@/components/GlassCard';

interface RiskModulesSectionProps {
  data?: {
    esg?: boolean;
    weather?: boolean;
    portCongestion?: boolean;
    carrier?: boolean;
    market?: boolean;
    insurance?: boolean;
  };
  onChange: (field: string, value: unknown) => void;
}

const MODULES = [
  { id: 'esg', label: 'ESG Risk', icon: Leaf, desc: 'Environmental, social & governance compliance' },
  { id: 'weather', label: 'Weather & Climate Risk', icon: CloudRain, desc: 'Real-time weather disruption analysis' },
  { id: 'portCongestion', label: 'Port Congestion Risk', icon: Anchor, desc: 'Port delays & congestion monitoring' },
  { id: 'carrier', label: 'Carrier Performance', icon: Truck, desc: 'Carrier reliability & history optimization' },
  { id: 'market', label: 'Market Condition Scanner', icon: TrendingUp, desc: 'Freight rates & market volatility' },
  { id: 'insurance', label: 'Insurance Optimization', icon: ShieldCheck, desc: 'Coverage recommendations & premium estimates' },
];

export const RiskModulesSection: React.FC<RiskModulesSectionProps> = ({
  data,
  onChange,
}) => {
  return (
    <GlassCard padding="lg" variant="default">
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: designTokens.spacing.lg,
          marginBottom: designTokens.spacing['2xl'],
        }}
      >
        <div
          style={{
            width: '56px',
            height: '56px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: `linear-gradient(135deg, rgba(110, 243, 255, 0.2), rgba(139, 123, 255, 0.2))`,
            border: `2px solid ${designTokens.colors.primaryNeon}`,
            borderRadius: designTokens.radii.lg,
          }}
        >
          <Layers size={28} style={{ color: designTokens.colors.primaryNeon }} />
        </div>
        
        <div style={{ flex: 1 }}>
          <h2
            style={{
              fontSize: '24px',
              fontWeight: 700,
              color: designTokens.colors.textStrong,
              fontFamily: 'Orbitron, monospace',
              marginBottom: designTokens.spacing.xs,
            }}
          >
            F. Risk Analysis Modules
          </h2>
          <p
            style={{
              fontSize: '15px',
              color: designTokens.colors.textMuted,
              fontFamily: designTokens.typography.fontFamily,
            }}
          >
            What should we analyze?
          </p>
        </div>
      </div>
      
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: designTokens.spacing.lg,
        }}
      >
        {MODULES.map((module) => {
          const Icon = module.icon;
          const isEnabled = data?.[module.id as keyof typeof data] ?? true;
          
          return (
            <div
              key={module.id}
              onClick={() => onChange(module.id, !isEnabled)}
              style={{
                padding: designTokens.spacing['2xl'],
                backgroundColor: isEnabled ? 'rgba(110, 243, 255, 0.08)' : 'rgba(255, 255, 255, 0.03)',
                border: `2px solid ${isEnabled ? designTokens.colors.primaryNeon : 'rgba(255, 255, 255, 0.08)'}`,
                borderRadius: designTokens.radii.xl,
                cursor: 'pointer',
                transition: designTokens.transitions.normal,
                display: 'flex',
                flexDirection: 'column',
                gap: designTokens.spacing.md,
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-4px)';
                e.currentTarget.style.boxShadow = `0 8px 32px rgba(110, 243, 255, 0.2)`;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div
                  style={{
                    width: '48px',
                    height: '48px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: isEnabled
                      ? `linear-gradient(135deg, rgba(110, 243, 255, 0.3), rgba(139, 123, 255, 0.3))`
                      : 'rgba(255, 255, 255, 0.05)',
                    border: `2px solid ${isEnabled ? designTokens.colors.primaryNeon : 'rgba(255, 255, 255, 0.08)'}`,
                    borderRadius: designTokens.radii.md,
                  }}
                >
                  <Icon size={24} style={{ color: isEnabled ? designTokens.colors.primaryNeon : designTokens.colors.textMuted }} />
                </div>
                
                <input
                  type="checkbox"
                  checked={isEnabled}
                  onChange={() => {}} // Handled by parent onClick
                  style={{
                    width: '24px',
                    height: '24px',
                    cursor: 'pointer',
                  }}
                />
              </div>
              
              <h3
                style={{
                  fontSize: '18px',
                  fontWeight: 600,
                  color: designTokens.colors.textStrong,
                  fontFamily: designTokens.typography.fontFamily,
                }}
              >
                {module.label}
              </h3>
              
              <p
                style={{
                  fontSize: '14px',
                  color: designTokens.colors.textMuted,
                  fontFamily: designTokens.typography.fontFamily,
                }}
              >
                {module.desc}
              </p>
            </div>
          );
        })}
      </div>
    </GlassCard>
  );
};
