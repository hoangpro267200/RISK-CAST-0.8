/**
 * Input Form Panel - Main form container with sections
 */

import React from 'react';
import { designTokens } from '@/ui/design-tokens';
import type { InputFormState } from './hooks/useFormState';
import { RouteServiceSection } from './sections/RouteServiceSection';
import { ScheduleSection } from './sections/ScheduleSection';
import { CargoDetailsSection } from './sections/CargoDetailsSection';
import { ValueTermsSection } from './sections/ValueTermsSection';
import { PartiesSection } from './sections/PartiesSection';
import { RiskModulesSection } from './sections/RiskModulesSection';
import { UploadSection } from './sections/UploadSection';
import { GlassCard } from '@/components/GlassCard';
import type { InputFormState } from './hooks/useFormState';

interface InputFormPanelProps {
  formState: InputFormState;
  onFieldChange: (section: keyof InputFormState, field: string, value: unknown) => void;
  onSectionChange: (section: keyof InputFormState, data: Partial<InputFormState[keyof InputFormState]>) => void;
  mode: 'basic' | 'advanced';
  activeSection: string;
}

export const InputFormPanel: React.FC<InputFormPanelProps> = ({
  formState,
  onFieldChange,
  onSectionChange,
  mode,
  activeSection,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: designTokens.spacing['3xl'],
      }}
    >
      {/* Section A: Route & Service */}
      <section id="section-route">
        <RouteServiceSection
          data={formState.route}
          onChange={(field, value) => onFieldChange('route', field, value)}
          mode={mode}
        />
      </section>
      
      {/* Section B: Schedule */}
      <section id="section-schedule">
        <ScheduleSection
          data={formState.schedule}
          routeData={formState.route}
          onChange={(field, value) => onFieldChange('schedule', field, value)}
        />
      </section>
      
      {/* Section C: Cargo Details */}
      <section id="section-cargo">
        <CargoDetailsSection
          data={formState.cargo}
          onChange={(field, value) => onFieldChange('cargo', field, value)}
          mode={mode}
        />
      </section>
      
      {/* Section D: Value & Terms */}
      <section id="section-value">
        <ValueTermsSection
          data={formState.value}
          onChange={(field, value) => onFieldChange('value', field, value)}
          mode={mode}
        />
      </section>
      
      {/* Section E: Parties */}
      <section id="section-parties">
        <PartiesSection
          data={formState.parties}
          onChange={(section, field, value) => {
            onSectionChange('parties', {
              ...formState.parties,
              [section]: {
                ...formState.parties?.[section as 'seller' | 'buyer'],
                [field]: value,
              },
            });
          }}
          mode={mode}
        />
      </section>
      
      {/* Section F: Risk Modules */}
      <section id="section-modules">
        <RiskModulesSection
          data={formState.modules}
          onChange={(field, value) => onFieldChange('modules', field, value)}
        />
      </section>
      
      {/* Section G: Upload */}
      <section id="section-upload">
        <UploadSection
          data={formState.upload}
          onChange={(field, value) => onFieldChange('upload', field, value)}
        />
      </section>
    </div>
  );
};
