/**
 * Risk Assessment Form
 * 
 * Form for creating new risk assessments.
 */

import React, { useState } from 'react';

interface RiskAssessmentFormProps {
  onSubmit: (data: any) => void;
  isLoading?: boolean;
  error?: string;
}

export function RiskAssessmentForm({ onSubmit, isLoading, error }: RiskAssessmentFormProps) {
  const [formData, setFormData] = useState({
    shipment: {
      cargo_type: '',
      cargo_value_usd: 100000,
      container_count: 1,
      packaging_quality: 'STANDARD',
    },
    route: {
      origin_port: '',
      destination_port: '',
      carrier_code: '',
      estimated_departure: '',
      estimated_arrival: '',
    },
    coverage: {
      coverage_type: 'ALL_RISK',
      insured_value_cents: 10000000,
      currency: 'USD',
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Transform form data to API format
    const apiData = {
      shipment_data: {
        cargo: {
          type: formData.shipment.cargo_type,
          value: formData.shipment.cargo_value_usd,
          container_count: formData.shipment.container_count,
          packaging_quality: formData.shipment.packaging_quality,
        },
        route: {
          origin: { port: formData.route.origin_port },
          destination: { port: formData.route.destination_port },
          carrier: formData.route.carrier_code || undefined,
          estimated_departure: formData.route.estimated_departure || undefined,
          estimated_arrival: formData.route.estimated_arrival || undefined,
        },
      },
      schema_version: 'v1',
    };

    onSubmit(apiData);
  };

  const updateField = (section: string, field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [section]: {
        ...prev[section as keyof typeof prev],
        [field]: value,
      },
    }));
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4">
          <p className="text-red-200 text-sm">{error}</p>
        </div>
      )}

      {/* Shipment Section */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-white">Shipment Details</h3>
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-white/80 mb-2">
              Cargo Type *
            </label>
            <select
              value={formData.shipment.cargo_type}
              onChange={(e) => updateField('shipment', 'cargo_type', e.target.value)}
              className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            >
              <option value="">Select cargo type</option>
              <option value="ELECTRONICS">Electronics</option>
              <option value="MACHINERY">Machinery</option>
              <option value="TEXTILES">Textiles</option>
              <option value="FOOD_PERISHABLE">Food (Perishable)</option>
              <option value="FOOD_DRY">Food (Dry)</option>
              <option value="CHEMICALS">Chemicals</option>
              <option value="GENERAL">General Cargo</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-white/80 mb-2">
              Cargo Value (USD) *
            </label>
            <input
              type="number"
              min="1000"
              value={formData.shipment.cargo_value_usd}
              onChange={(e) => updateField('shipment', 'cargo_value_usd', parseInt(e.target.value))}
              className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-white/80 mb-2">
              Container Count
            </label>
            <input
              type="number"
              min="1"
              max="1000"
              value={formData.shipment.container_count}
              onChange={(e) => updateField('shipment', 'container_count', parseInt(e.target.value))}
              className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-white/80 mb-2">
              Packaging Quality
            </label>
            <select
              value={formData.shipment.packaging_quality}
              onChange={(e) => updateField('shipment', 'packaging_quality', e.target.value)}
              className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="POOR">Poor</option>
              <option value="STANDARD">Standard</option>
              <option value="GOOD">Good</option>
              <option value="EXCELLENT">Excellent</option>
            </select>
          </div>
        </div>
      </div>

      {/* Route Section */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-white">Route Details</h3>
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-white/80 mb-2">
              Origin Port *
            </label>
            <input
              type="text"
              placeholder="e.g., CNSHA"
              value={formData.route.origin_port}
              onChange={(e) => updateField('route', 'origin_port', e.target.value)}
              className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
            <p className="text-xs text-white/50 mt-1">UN/LOCODE format</p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-white/80 mb-2">
              Destination Port *
            </label>
            <input
              type="text"
              placeholder="e.g., NLRTM"
              value={formData.route.destination_port}
              onChange={(e) => updateField('route', 'destination_port', e.target.value)}
              className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
            <p className="text-xs text-white/50 mt-1">UN/LOCODE format</p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-white/80 mb-2">
              Carrier (Optional)
            </label>
            <input
              type="text"
              placeholder="e.g., MAEU"
              value={formData.route.carrier_code}
              onChange={(e) => updateField('route', 'carrier_code', e.target.value)}
              className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-white/80 mb-2">
              Estimated Departure
            </label>
            <input
              type="datetime-local"
              value={formData.route.estimated_departure}
              onChange={(e) => updateField('route', 'estimated_departure', e.target.value)}
              className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Coverage Section */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-white">Coverage</h3>
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-white/80 mb-2">
              Coverage Type
            </label>
            <select
              value={formData.coverage.coverage_type}
              onChange={(e) => updateField('coverage', 'coverage_type', e.target.value)}
              className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="ALL_RISK">All Risk</option>
              <option value="NAMED_PERILS">Named Perils</option>
              <option value="TOTAL_LOSS">Total Loss Only</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-white/80 mb-2">
              Insured Value (USD)
            </label>
            <input
              type="number"
              min="100000"
              value={formData.coverage.insured_value_cents / 100}
              onChange={(e) => updateField('coverage', 'insured_value_cents', parseInt(e.target.value) * 100)}
              className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
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
            Creating Assessment...
          </span>
        ) : (
          'Create Assessment'
        )}
      </button>
    </form>
  );
}
