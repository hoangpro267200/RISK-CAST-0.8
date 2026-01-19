import { Package, Building2, User, MapPin, Plane, ChevronRight, AlertCircle, AlertTriangle } from 'lucide-react';
import type { ShipmentData } from './types';
import type { ValidationIssue } from '../../lib/validation';

interface FieldTileProps {
  label: string;
  value: string | number | boolean;
  path: string;
  hasError?: boolean;
  hasWarning?: boolean;
  onClick: (path: string) => void;
}

function FieldTile({ label, value, path, hasError, hasWarning, onClick }: FieldTileProps) {
  const displayValue = typeof value === 'boolean' ? (value ? 'Yes' : 'No') : value;
  
  return (
    <div
      className={`
        group cursor-pointer rounded-xl p-4 
        bg-white/5 hover:bg-white/10 border border-white/10 
        transition-all duration-200
        ${hasError ? 'border-red-500/50 bg-red-500/10' : ''}
        ${hasWarning && !hasError ? 'border-orange-400/50 bg-orange-400/10' : ''}
      `}
      onClick={() => onClick(path)}
      data-field-path={path}
    >
      <div className="flex items-start justify-between mb-2">
        <span className="text-white/50 text-xs uppercase tracking-wide">{label}</span>
        <div className="flex items-center gap-1">
          {hasError && <AlertCircle className="w-3.5 h-3.5 text-red-400" />}
          {hasWarning && !hasError && <AlertTriangle className="w-3.5 h-3.5 text-orange-400" />}
          <ChevronRight className="w-4 h-4 text-white/30 group-hover:text-cyan-400 transition-colors" />
        </div>
      </div>
      <div className="text-white/90 font-medium truncate">{displayValue || '—'}</div>
    </div>
  );
}

interface InfoPanelProps {
  title: string;
  icon: 'trade' | 'cargo' | 'seller' | 'buyer';
  fields: Array<{
    label: string;
    value: string | number | boolean;
    path: string;
  }>;
  validationIssues: ValidationIssue[];
  onFieldClick: (path: string) => void;
}

export function InfoPanel({ title, icon, fields, validationIssues, onFieldClick }: InfoPanelProps) {
  const IconComponent = icon === 'trade' ? Plane : icon === 'cargo' ? Package : icon === 'seller' ? Building2 : User;
  
  const iconGradients = {
    trade: 'from-blue-500 to-cyan-500',
    cargo: 'from-green-500 to-emerald-500',
    seller: 'from-amber-500 to-orange-500',
    buyer: 'from-purple-500 to-pink-500',
  };

  const getFieldIssues = (path: string) => {
    return validationIssues.filter(issue => issue.affectedFields.includes(path));
  };

  return (
    <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-[20px] p-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${iconGradients[icon]} flex items-center justify-center shadow-lg`}>
          <IconComponent className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="text-white font-medium">{title}</h3>
          <p className="text-white/40 text-xs">{fields.length} fields</p>
        </div>
      </div>

      {/* Fields Grid */}
      <div className="grid grid-cols-2 gap-3">
        {fields.map((field) => {
          const issues = getFieldIssues(field.path);
          const hasError = issues.some(i => i.severity === 'critical');
          const hasWarning = issues.some(i => i.severity === 'warning');
          
          return (
            <FieldTile
              key={field.path}
              label={field.label}
              value={field.value}
              path={field.path}
              hasError={hasError}
              hasWarning={hasWarning}
              onClick={onFieldClick}
            />
          );
        })}
      </div>
    </div>
  );
}

