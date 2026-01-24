/**
 * Schedule Section - Section B (Auto-populated, mostly readonly)
 */

import React from 'react';
import { Calendar, Clock, CalendarClock, Award } from 'lucide-react';
import { designTokens } from '@/ui/design-tokens';
import { GlassCard } from '@/components/GlassCard';
import { Input } from '../components/Input';
import { DatePicker } from '../components/DatePicker';

interface ScheduleSectionProps {
  data?: {
    etd?: string;
    transitDays?: number;
    eta?: string;
    scheduleFrequency?: string;
    reliabilityScore?: number;
  };
  routeData?: {
    serviceRoute?: string;
  };
  onChange: (field: string, value: unknown) => void;
}

export const ScheduleSection: React.FC<ScheduleSectionProps> = ({
  data,
  onChange,
}) => {
  // Calculate ETA from ETD + transit days
  const calculateETA = (etd: string, transitDays: number) => {
    if (!etd || !transitDays) return '';
    const date = new Date(etd);
    date.setDate(date.getDate() + transitDays);
    return date.toISOString().split('T')[0];
  };
  
  const eta = data?.etd && data?.transitDays
    ? calculateETA(data.etd, data.transitDays)
    : data?.eta || '';
  
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
          <Calendar size={28} style={{ color: designTokens.colors.primaryNeon }} />
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
            B. Schedule
          </h2>
          <p
            style={{
              fontSize: '15px',
              color: designTokens.colors.textMuted,
              fontFamily: designTokens.typography.fontFamily,
            }}
          >
            When does it depart and arrive?
          </p>
        </div>
      </div>
      
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: designTokens.spacing['2xl'],
        }}
      >
        <DatePicker
          label="ETD (Estimated Departure)"
          value={data?.etd}
          minDate={new Date().toISOString().split('T')[0]}
          onChange={(value) => {
            onChange('etd', value);
            // Auto-calculate ETA
            if (data?.transitDays) {
              const newETA = calculateETA(value, data.transitDays);
              onChange('eta', newETA);
            }
          }}
          helperText="Departure date"
        />
        
        <Input
          label="Transit Time (days)"
          type="number"
          value={data?.transitDays?.toString() || ''}
          icon={Clock}
          readOnly
          helperText="From service route data"
        />
        
        <DatePicker
          label="ETA (Estimated Arrival)"
          value={eta}
          onChange={(value) => onChange('eta', value)}
          helperText="Calculated from ETD + transit"
        />
        
        <Input
          label="Schedule Frequency"
          value={data?.scheduleFrequency || ''}
          icon={Clock}
          readOnly
          helperText="From service route data"
        />
        
        <Input
          label="Reliability Score"
          value={data?.reliabilityScore?.toString() || ''}
          icon={Award}
          readOnly
          helperText="From service route data"
        />
      </div>
    </GlassCard>
  );
};
