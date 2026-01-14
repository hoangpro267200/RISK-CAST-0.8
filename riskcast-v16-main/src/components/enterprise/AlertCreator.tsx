/**
 * AlertCreator Component
 * 
 * UI for creating risk alerts/notifications.
 * - Define conditions (risk score > X, lane, time window)
 * - Select notification channels
 * - Backend-agnostic (no mock triggers)
 */

import React, { useState } from 'react';
import { 
  Bell, 
  Plus, 
  X,
  AlertTriangle,
  TrendingUp,
  MapPin,
  Clock,
  Mail,
  Smartphone,
  Check
} from 'lucide-react';
import { GlassCard } from '../GlassCard';

export type AlertConditionType = 
  | 'risk_score_above'
  | 'risk_score_below'
  | 'expected_loss_above'
  | 'confidence_below'
  | 'lane_specific'
  | 'carrier_specific';

export type NotificationChannel = 'email' | 'sms' | 'push' | 'webhook';

export interface AlertCondition {
  type: AlertConditionType;
  value: number | string;
  label?: string;
}

export interface AlertConfig {
  name: string;
  description?: string;
  conditions: AlertCondition[];
  channels: NotificationChannel[];
  isActive: boolean;
  frequency?: 'realtime' | 'hourly' | 'daily';
}

export interface AlertCreatorProps {
  /** Callback when alert is created */
  onCreateAlert?: (config: AlertConfig) => Promise<void>;
  /** Callback when canceled */
  onCancel?: () => void;
  /** Initial values */
  initialConfig?: Partial<AlertConfig>;
  /** Whether form is open */
  isOpen: boolean;
  /** Additional classes */
  className?: string;
}

const CONDITION_OPTIONS: Array<{
  type: AlertConditionType;
  label: string;
  icon: React.ReactNode;
  unit?: string;
  min?: number;
  max?: number;
}> = [
  { type: 'risk_score_above', label: 'Risk Score Above', icon: <TrendingUp className="w-4 h-4" />, unit: '', min: 0, max: 100 },
  { type: 'risk_score_below', label: 'Risk Score Below', icon: <TrendingUp className="w-4 h-4" />, unit: '', min: 0, max: 100 },
  { type: 'expected_loss_above', label: 'Expected Loss Above', icon: <AlertTriangle className="w-4 h-4" />, unit: '$' },
  { type: 'confidence_below', label: 'Confidence Below', icon: <AlertTriangle className="w-4 h-4" />, unit: '%', min: 0, max: 100 },
  { type: 'lane_specific', label: 'Specific Lane', icon: <MapPin className="w-4 h-4" /> },
  { type: 'carrier_specific', label: 'Specific Carrier', icon: <MapPin className="w-4 h-4" /> }
];

const CHANNEL_OPTIONS: Array<{
  channel: NotificationChannel;
  label: string;
  icon: React.ReactNode;
  description: string;
}> = [
  { channel: 'email', label: 'Email', icon: <Mail className="w-4 h-4" />, description: 'Receive alerts via email' },
  { channel: 'push', label: 'Push', icon: <Bell className="w-4 h-4" />, description: 'Browser push notifications' },
  { channel: 'sms', label: 'SMS', icon: <Smartphone className="w-4 h-4" />, description: 'Text message alerts' }
];

export const AlertCreator: React.FC<AlertCreatorProps> = ({
  onCreateAlert,
  onCancel,
  initialConfig,
  isOpen,
  className = ''
}) => {
  const [name, setName] = useState(initialConfig?.name || '');
  const [description, setDescription] = useState(initialConfig?.description || '');
  const [conditions, setConditions] = useState<AlertCondition[]>(initialConfig?.conditions || []);
  const [channels, setChannels] = useState<NotificationChannel[]>(initialConfig?.channels || ['email']);
  const [frequency, setFrequency] = useState<'realtime' | 'hourly' | 'daily'>(initialConfig?.frequency || 'realtime');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showConditionPicker, setShowConditionPicker] = useState(false);

  if (!isOpen) return null;

  const handleAddCondition = (type: AlertConditionType) => {
    const existingCondition = conditions.find(c => c.type === type);
    if (!existingCondition) {
      const newCondition: AlertCondition = { type, value: type.includes('score') ? 70 : 10000 };
      setConditions([...conditions, newCondition]);
    }
    setShowConditionPicker(false);
  };

  const handleUpdateCondition = (index: number, value: number | string) => {
    const updated = [...conditions];
    const existing = updated[index];
    if (existing) {
      updated[index] = { ...existing, value };
      setConditions(updated);
    }
  };

  const handleRemoveCondition = (index: number) => {
    setConditions(conditions.filter((_, i) => i !== index));
  };

  const toggleChannel = (channel: NotificationChannel) => {
    if (channels.includes(channel)) {
      setChannels(channels.filter(c => c !== channel));
    } else {
      setChannels([...channels, channel]);
    }
  };

  const handleSubmit = async () => {
    if (!name.trim() || conditions.length === 0 || channels.length === 0) return;

    setIsSubmitting(true);
    try {
      await onCreateAlert?.({
        name: name.trim(),
        description: description.trim() || undefined,
        conditions,
        channels,
        isActive: true,
        frequency
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[300]" onClick={onCancel} />

      {/* Modal */}
      <div className={`fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-[301] w-full max-w-lg ${className}`}>
        <GlassCard className="max-h-[85vh] overflow-y-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-amber-500/20 flex items-center justify-center">
                <Bell className="w-5 h-5 text-amber-400" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-white">Create Alert</h2>
                <p className="text-xs text-white/50">Get notified when conditions are met</p>
              </div>
            </div>
            <button
              onClick={onCancel}
              className="p-2 text-white/50 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Form */}
          <div className="space-y-6">
            {/* Name */}
            <div>
              <label className="block text-sm font-medium text-white/80 mb-2">
                Alert Name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., High Risk Alert"
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-white/80 mb-2">
                Description (Optional)
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe when this alert should trigger..."
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500/50 resize-none"
                rows={2}
              />
            </div>

            {/* Conditions */}
            <div>
              <label className="block text-sm font-medium text-white/80 mb-2">
                Conditions
              </label>
              <div className="space-y-2">
                {conditions.map((condition, index) => {
                  const option = CONDITION_OPTIONS.find(o => o.type === condition.type);
                  return (
                    <div key={index} className="flex items-center gap-2 p-3 bg-white/5 border border-white/10 rounded-lg">
                      <div className="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center text-amber-400">
                        {option?.icon}
                      </div>
                      <span className="text-sm text-white/80 flex-shrink-0">{option?.label}</span>
                      <input
                        type={condition.type.includes('specific') ? 'text' : 'number'}
                        value={condition.value}
                        onChange={(e) => handleUpdateCondition(index, condition.type.includes('specific') ? e.target.value : Number(e.target.value))}
                        className="w-24 bg-white/10 border border-white/10 rounded px-2 py-1 text-white text-sm focus:outline-none focus:ring-1 focus:ring-blue-500/50"
                        min={option?.min}
                        max={option?.max}
                      />
                      {option?.unit && <span className="text-xs text-white/50">{option.unit}</span>}
                      <button
                        onClick={() => handleRemoveCondition(index)}
                        className="ml-auto p-1 text-white/40 hover:text-red-400 transition-colors"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  );
                })}

                {/* Add Condition Button */}
                <div className="relative">
                  <button
                    onClick={() => setShowConditionPicker(!showConditionPicker)}
                    className="w-full py-2.5 border border-dashed border-white/20 rounded-lg text-white/50 hover:text-white/80 hover:border-white/40 transition-colors flex items-center justify-center gap-2 text-sm"
                  >
                    <Plus className="w-4 h-4" />
                    Add Condition
                  </button>

                  {showConditionPicker && (
                    <div className="absolute top-full left-0 right-0 mt-2 bg-slate-800 border border-white/10 rounded-lg shadow-xl z-10 overflow-hidden">
                      {CONDITION_OPTIONS.map((option) => (
                        <button
                          key={option.type}
                          onClick={() => handleAddCondition(option.type)}
                          disabled={conditions.some(c => c.type === option.type)}
                          className="w-full flex items-center gap-3 px-4 py-3 hover:bg-white/5 transition-colors disabled:opacity-30"
                        >
                          <div className="text-amber-400">{option.icon}</div>
                          <span className="text-sm text-white/80">{option.label}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Notification Channels */}
            <div>
              <label className="block text-sm font-medium text-white/80 mb-2">
                Notification Channels
              </label>
              <div className="grid grid-cols-3 gap-2">
                {CHANNEL_OPTIONS.map((option) => (
                  <button
                    key={option.channel}
                    onClick={() => toggleChannel(option.channel)}
                    className={`flex flex-col items-center gap-2 p-3 rounded-lg border transition-colors ${
                      channels.includes(option.channel)
                        ? 'bg-blue-500/20 border-blue-500/40 text-blue-400'
                        : 'bg-white/5 border-white/10 text-white/60 hover:border-white/20'
                    }`}
                  >
                    {option.icon}
                    <span className="text-xs">{option.label}</span>
                    {channels.includes(option.channel) && (
                      <Check className="w-3 h-3 absolute top-1 right-1" />
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* Frequency */}
            <div>
              <label className="block text-sm font-medium text-white/80 mb-2">
                Check Frequency
              </label>
              <div className="flex gap-2">
                {(['realtime', 'hourly', 'daily'] as const).map((freq) => (
                  <button
                    key={freq}
                    onClick={() => setFrequency(freq)}
                    className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg border text-sm transition-colors ${
                      frequency === freq
                        ? 'bg-blue-500/20 border-blue-500/40 text-blue-400'
                        : 'bg-white/5 border-white/10 text-white/60 hover:border-white/20'
                    }`}
                  >
                    <Clock className="w-3.5 h-3.5" />
                    {freq.charAt(0).toUpperCase() + freq.slice(1)}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 mt-6 pt-6 border-t border-white/10">
            <button
              onClick={onCancel}
              className="px-4 py-2 text-white/70 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={!name.trim() || conditions.length === 0 || channels.length === 0 || isSubmitting}
              className="px-5 py-2 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-lg font-medium disabled:opacity-50 transition-opacity"
            >
              {isSubmitting ? 'Creating...' : 'Create Alert'}
            </button>
          </div>
        </GlassCard>
      </div>
    </>
  );
};

export default AlertCreator;
