/**
 * Parties Section - Section E (Tabbed: Seller | Buyer)
 */

import React, { useState } from 'react';
import { Users, Building, MapPin, User, Mail, Phone, FileText, Briefcase } from 'lucide-react';
import { designTokens } from '@/ui/design-tokens';
import { GlassCard } from '@/components/GlassCard';
import { Input } from '../components/Input';
import { Dropdown } from '../components/Dropdown';

interface PartiesSectionProps {
  data?: {
    seller?: {
      company?: string;
      country?: string;
      city?: string;
      address?: string;
      contact?: string;
      contactRole?: string;
      email?: string;
      phone?: string;
      businessType?: string;
      taxId?: string;
    };
    buyer?: {
      company?: string;
      country?: string;
      city?: string;
      address?: string;
      contact?: string;
      contactRole?: string;
      email?: string;
      phone?: string;
      businessType?: string;
      taxId?: string;
    };
  };
  onChange: (section: 'seller' | 'buyer', field: string, value: unknown) => void;
  mode: 'basic' | 'advanced';
}

export const PartiesSection: React.FC<PartiesSectionProps> = ({
  data,
  onChange,
  mode,
}) => {
  const [activeTab, setActiveTab] = useState<'seller' | 'buyer'>('seller');
  
  const currentData = activeTab === 'seller' ? data?.seller : data?.buyer;
  const prefix = activeTab;
  
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
          <Users size={28} style={{ color: designTokens.colors.primaryNeon }} />
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
            E. Parties
          </h2>
          <p
            style={{
              fontSize: '15px',
              color: designTokens.colors.textMuted,
              fontFamily: designTokens.typography.fontFamily,
            }}
          >
            Who's involved?
          </p>
        </div>
      </div>
      
      {/* Tabs */}
      <div
        style={{
          display: 'flex',
          gap: designTokens.spacing.sm,
          marginBottom: designTokens.spacing['2xl'],
          borderBottom: `1px solid rgba(255, 255, 255, 0.08)`,
        }}
      >
        <button
          type="button"
          onClick={() => setActiveTab('seller')}
          style={{
            padding: `${designTokens.spacing.md} ${designTokens.spacing['2xl']}`,
            backgroundColor: activeTab === 'seller' ? 'rgba(110, 243, 255, 0.1)' : 'transparent',
            border: 'none',
            borderBottom: activeTab === 'seller' ? `2px solid ${designTokens.colors.primaryNeon}` : '2px solid transparent',
            color: activeTab === 'seller' ? designTokens.colors.primaryNeon : designTokens.colors.textMuted,
            fontSize: '15px',
            fontFamily: designTokens.typography.fontFamily,
            fontWeight: activeTab === 'seller' ? 600 : 500,
            cursor: 'pointer',
            transition: designTokens.transitions.normal,
          }}
        >
          Seller
        </button>
        
        <button
          type="button"
          onClick={() => setActiveTab('buyer')}
          style={{
            padding: `${designTokens.spacing.md} ${designTokens.spacing['2xl']}`,
            backgroundColor: activeTab === 'buyer' ? 'rgba(110, 243, 255, 0.1)' : 'transparent',
            border: 'none',
            borderBottom: activeTab === 'buyer' ? `2px solid ${designTokens.colors.primaryNeon}` : '2px solid transparent',
            color: activeTab === 'buyer' ? designTokens.colors.primaryNeon : designTokens.colors.textMuted,
            fontSize: '15px',
            fontFamily: designTokens.typography.fontFamily,
            fontWeight: activeTab === 'buyer' ? 600 : 500,
            cursor: 'pointer',
            transition: designTokens.transitions.normal,
          }}
        >
          Buyer
        </button>
      </div>
      
      {/* Form Fields */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: designTokens.spacing['2xl'],
        }}
      >
        <Input
          label="Company Name"
          value={currentData?.company || ''}
          icon={Building}
          required
          onChange={(e) => onChange(prefix, 'company', e.target.value)}
        />
        
        <Dropdown
          label="Country"
          placeholder="Select country"
          value={currentData?.country}
          options={[
            { value: 'VN', label: 'Vietnam' },
            { value: 'CN', label: 'China' },
            { value: 'US', label: 'United States' },
            { value: 'DE', label: 'Germany' },
          ]}
          searchable
          required
          onChange={(value) => onChange(prefix, 'country', value)}
        />
        
        {mode === 'advanced' && (
          <>
            <Input
              label="City"
              value={currentData?.city || ''}
              icon={MapPin}
              onChange={(e) => onChange(prefix, 'city', e.target.value)}
            />
            
            <Input
              label="Address"
              value={currentData?.address || ''}
              icon={MapPin}
              onChange={(e) => onChange(prefix, 'address', e.target.value)}
            />
            
            <Input
              label="Contact Person"
              value={currentData?.contact || ''}
              icon={User}
              onChange={(e) => onChange(prefix, 'contact', e.target.value)}
            />
            
            <Input
              label="Contact Role"
              value={currentData?.contactRole || ''}
              icon={Briefcase}
              onChange={(e) => onChange(prefix, 'contactRole', e.target.value)}
            />
            
            <Input
              label="Email"
              type="email"
              value={currentData?.email || ''}
              icon={Mail}
              onChange={(e) => onChange(prefix, 'email', e.target.value)}
            />
            
            <Input
              label="Phone"
              type="tel"
              value={currentData?.phone || ''}
              icon={Phone}
              onChange={(e) => onChange(prefix, 'phone', e.target.value)}
            />
            
            <Dropdown
              label="Business Type"
              placeholder="Select business type"
              value={currentData?.businessType}
              options={[
                { value: 'manufacturer', label: 'Manufacturer' },
                { value: 'trader', label: 'Trader' },
                { value: 'retailer', label: 'Retailer' },
              ]}
              onChange={(value) => onChange(prefix, 'businessType', value)}
            />
            
            <Input
              label="Tax ID / VAT"
              value={currentData?.taxId || ''}
              icon={FileText}
              onChange={(e) => onChange(prefix, 'taxId', e.target.value)}
              helperText="Optional"
            />
          </>
        )}
      </div>
    </GlassCard>
  );
};
