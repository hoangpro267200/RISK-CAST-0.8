/**
 * Claim Filing Form
 * 
 * Form for filing First Notice of Loss (FNOL)
 */

import React, { useState } from 'react';
import { useSearchParams } from 'react-router-dom';

interface ClaimFilingFormProps {
  onSubmit: (data: any) => void;
  isLoading?: boolean;
  error?: string;
}

export function ClaimFilingForm({ onSubmit, isLoading, error }: ClaimFilingFormProps) {
  const [searchParams] = useSearchParams();
  const policyIdFromUrl = searchParams.get('policy_id');

  const [formData, setFormData] = useState({
    policy_id: policyIdFromUrl || '',
    loss_date: '',
    loss_type: '',
    loss_location: '',
    loss_description: '',
    estimated_loss_cents: 0,
    currency: 'USD',
    reported_by: '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const fnolData = {
      loss_date: formData.loss_date,
      loss_type: formData.loss_type,
      loss_location: formData.loss_location,
      loss_description: formData.loss_description,
      estimated_loss_cents: Math.round(formData.estimated_loss_cents),
      currency: formData.currency,
      reported_by: formData.reported_by,
    };

    onSubmit({ policy_id: formData.policy_id, fnol: fnolData });
  };

  const updateField = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4">
          <p className="text-red-200 text-sm">{error}</p>
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-white/80 mb-2">
          Policy ID *
        </label>
        <input
          type="text"
          value={formData.policy_id}
          onChange={(e) => updateField('policy_id', e.target.value)}
          className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Enter policy ID"
          required
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-white/80 mb-2">
            Loss Date *
          </label>
          <input
            type="date"
            value={formData.loss_date}
            onChange={(e) => updateField('loss_date', e.target.value)}
            className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-white/80 mb-2">
            Loss Type *
          </label>
          <select
            value={formData.loss_type}
            onChange={(e) => updateField('loss_type', e.target.value)}
            className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          >
            <option value="">Select loss type</option>
            <option value="DAMAGE">Damage</option>
            <option value="THEFT">Theft</option>
            <option value="TOTAL_LOSS">Total Loss</option>
            <option value="DELAY">Delay</option>
            <option value="OTHER">Other</option>
          </select>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-white/80 mb-2">
          Loss Location *
        </label>
        <input
          type="text"
          value={formData.loss_location}
          onChange={(e) => updateField('loss_location', e.target.value)}
          className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="e.g., Port of Rotterdam"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-white/80 mb-2">
          Estimated Loss (USD) *
        </label>
        <input
          type="number"
          min="0"
          step="0.01"
          value={formData.estimated_loss_cents / 100}
          onChange={(e) => updateField('estimated_loss_cents', parseFloat(e.target.value) * 100)}
          className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-white/80 mb-2">
          Loss Description *
        </label>
        <textarea
          value={formData.loss_description}
          onChange={(e) => updateField('loss_description', e.target.value)}
          rows={4}
          className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Describe the loss in detail..."
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-white/80 mb-2">
          Reported By *
        </label>
        <input
          type="text"
          value={formData.reported_by}
          onChange={(e) => updateField('reported_by', e.target.value)}
          className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Name or email"
          required
        />
      </div>

      <button
        type="submit"
        disabled={isLoading}
        className="w-full px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-blue-500/50 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors"
      >
        {isLoading ? (
          <span className="flex items-center justify-center">
            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Filing Claim...
          </span>
        ) : (
          'File Claim'
        )}
      </button>
    </form>
  );
}
