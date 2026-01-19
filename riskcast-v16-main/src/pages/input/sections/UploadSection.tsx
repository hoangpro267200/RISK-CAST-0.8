/**
 * Upload Section - Section G (Optional)
 */

import React, { useRef } from 'react';
import { UploadCloud, FileText, X } from 'lucide-react';
import { designTokens } from '@/ui/design-tokens';
import { GlassCard } from '@/components/GlassCard';

interface UploadSectionProps {
  data?: {
    file?: File | null;
  };
  onChange: (field: string, value: unknown) => void;
}

export const UploadSection: React.FC<UploadSectionProps> = ({
  data,
  onChange,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onChange('file', file);
    }
  };
  
  const handleRemove = () => {
    onChange('file', null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };
  
  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };
  
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
          <UploadCloud size={28} style={{ color: designTokens.colors.primaryNeon }} />
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
            G. Upload Packing List
          </h2>
          <p
            style={{
              fontSize: '15px',
              color: designTokens.colors.textMuted,
              fontFamily: designTokens.typography.fontFamily,
            }}
          >
            Any supporting documents?
          </p>
        </div>
      </div>
      
      {!data?.file ? (
        <div
          onClick={() => fileInputRef.current?.click()}
          style={{
            minHeight: '160px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: designTokens.spacing.lg,
            padding: designTokens.spacing['3xl'],
            backgroundColor: 'rgba(255, 255, 255, 0.02)',
            border: `2px dashed rgba(255, 255, 255, 0.08)`,
            borderRadius: designTokens.radii['2xl'],
            cursor: 'pointer',
            transition: designTokens.transitions.normal,
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = designTokens.colors.primaryNeon;
            e.currentTarget.style.backgroundColor = 'rgba(110, 243, 255, 0.1)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)';
            e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.02)';
          }}
        >
          <div
            style={{
              width: '80px',
              height: '80px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: `linear-gradient(135deg, rgba(110, 243, 255, 0.1), rgba(139, 123, 255, 0.1))`,
              border: `2px solid ${designTokens.colors.primaryNeon}`,
              borderRadius: designTokens.radii['2xl'],
            }}
          >
            <UploadCloud size={40} style={{ color: designTokens.colors.primaryNeon }} />
          </div>
          
          <div style={{ textAlign: 'center' }}>
            <h3
              style={{
                fontSize: '20px',
                fontWeight: 600,
                color: designTokens.colors.textStrong,
                fontFamily: designTokens.typography.fontFamily,
                marginBottom: designTokens.spacing.sm,
              }}
            >
              Drag & Drop or Click to Upload
            </h3>
            <p
              style={{
                fontSize: '15px',
                color: designTokens.colors.textMuted,
                fontFamily: designTokens.typography.fontFamily,
              }}
            >
              Supports PDF, Excel (XLSX, XLS), CSV
            </p>
          </div>
        </div>
      ) : (
        <div
          style={{
            padding: designTokens.spacing.lg,
            backgroundColor: 'rgba(110, 243, 255, 0.1)',
            border: `1px solid ${designTokens.colors.primaryNeon}`,
            borderRadius: designTokens.radii.lg,
            display: 'flex',
            alignItems: 'center',
            gap: designTokens.spacing.md,
          }}
        >
          <FileText size={24} style={{ color: designTokens.colors.primaryNeon }} />
          
          <div style={{ flex: 1 }}>
            <div
              style={{
                fontWeight: 600,
                color: designTokens.colors.textStrong,
                fontFamily: designTokens.typography.fontFamily,
                marginBottom: designTokens.spacing.xs,
              }}
            >
              {data.file.name}
            </div>
            <div
              style={{
                fontSize: '14px',
                color: designTokens.colors.textMuted,
                fontFamily: designTokens.typography.fontFamily,
              }}
            >
              {formatFileSize(data.file.size)}
            </div>
          </div>
          
          <button
            type="button"
            onClick={handleRemove}
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
              e.currentTarget.style.color = designTokens.colors.danger;
              e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.1)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = designTokens.colors.textMuted;
              e.currentTarget.style.backgroundColor = 'transparent';
            }}
          >
            <X size={18} />
          </button>
        </div>
      )}
      
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.xlsx,.xls,.csv"
        onChange={handleFileSelect}
        style={{ display: 'none' }}
      />
    </GlassCard>
  );
};
