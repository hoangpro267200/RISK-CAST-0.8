/**
 * New Assessment Page
 * Create a new risk assessment and run
 */
import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { riskApi } from '../../api/client';

interface FormData {
  origin: {
    port?: string;
    country?: string;
    coordinates?: {
      lat?: number;
      lon?: number;
    };
  };
  destination: {
    port?: string;
    country?: string;
    coordinates?: {
      lat?: number;
      lon?: number;
    };
  };
  cargo: {
    type?: string;
    value?: number;
    weight?: number;
    description?: string;
  };
  [key: string]: any;
}

export function NewAssessment() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState<FormData>({
    origin: {},
    destination: {},
    cargo: {},
  });

  const createMutation = useMutation({
    mutationFn: async () => {
      // 1. Create assessment
      const assessmentResponse = await riskApi.createAssessment({
        input_data: formData
      });
      const assessment = assessmentResponse.data;

      // 2. Create run
      const runResponse = await riskApi.createRun(assessment.id, {});
      const run = runResponse.data;

      return { 
        assessment, 
        run 
      };
    },
    onSuccess: (data) => {
      navigate(`/app/risk/runs/${data.run.id}`);
    }
  });

  const updateField = (section: string, field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value
      }
    }));
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6 text-white">New Risk Assessment</h1>

      <form onSubmit={(e) => { 
        e.preventDefault(); 
        createMutation.mutate(); 
      }}>
        <div className="space-y-6">
          {/* Origin section */}
          <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4 text-white">Origin</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-white/80 mb-2">
                  Port
                </label>
                <input
                  type="text"
                  value={formData.origin.port || ''}
                  onChange={(e) => updateField('origin', 'port', e.target.value)}
                  className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter origin port"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white/80 mb-2">
                  Country
                </label>
                <input
                  type="text"
                  value={formData.origin.country || ''}
                  onChange={(e) => updateField('origin', 'country', e.target.value)}
                  className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter origin country"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-white/80 mb-2">
                    Latitude
                  </label>
                  <input
                    type="number"
                    step="any"
                    value={formData.origin.coordinates?.lat || ''}
                    onChange={(e) => updateField('origin', 'coordinates', {
                      ...formData.origin.coordinates,
                      lat: e.target.value ? parseFloat(e.target.value) : undefined
                    })}
                    className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Latitude"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-white/80 mb-2">
                    Longitude
                  </label>
                  <input
                    type="number"
                    step="any"
                    value={formData.origin.coordinates?.lon || ''}
                    onChange={(e) => updateField('origin', 'coordinates', {
                      ...formData.origin.coordinates,
                      lon: e.target.value ? parseFloat(e.target.value) : undefined
                    })}
                    className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Longitude"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Destination section */}
          <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4 text-white">Destination</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-white/80 mb-2">
                  Port
                </label>
                <input
                  type="text"
                  value={formData.destination.port || ''}
                  onChange={(e) => updateField('destination', 'port', e.target.value)}
                  className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter destination port"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white/80 mb-2">
                  Country
                </label>
                <input
                  type="text"
                  value={formData.destination.country || ''}
                  onChange={(e) => updateField('destination', 'country', e.target.value)}
                  className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter destination country"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-white/80 mb-2">
                    Latitude
                  </label>
                  <input
                    type="number"
                    step="any"
                    value={formData.destination.coordinates?.lat || ''}
                    onChange={(e) => updateField('destination', 'coordinates', {
                      ...formData.destination.coordinates,
                      lat: e.target.value ? parseFloat(e.target.value) : undefined
                    })}
                    className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Latitude"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-white/80 mb-2">
                    Longitude
                  </label>
                  <input
                    type="number"
                    step="any"
                    value={formData.destination.coordinates?.lon || ''}
                    onChange={(e) => updateField('destination', 'coordinates', {
                      ...formData.destination.coordinates,
                      lon: e.target.value ? parseFloat(e.target.value) : undefined
                    })}
                    className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Longitude"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Cargo section */}
          <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4 text-white">Cargo Details</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-white/80 mb-2">
                  Cargo Type
                </label>
                <input
                  type="text"
                  value={formData.cargo.type || ''}
                  onChange={(e) => updateField('cargo', 'type', e.target.value)}
                  className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., Electronics, Machinery, etc."
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-white/80 mb-2">
                    Value (USD)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.cargo.value || ''}
                    onChange={(e) => updateField('cargo', 'value', e.target.value ? parseFloat(e.target.value) : undefined)}
                    className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="0.00"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-white/80 mb-2">
                    Weight (kg)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.cargo.weight || ''}
                    onChange={(e) => updateField('cargo', 'weight', e.target.value ? parseFloat(e.target.value) : undefined)}
                    className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="0.00"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-white/80 mb-2">
                  Description
                </label>
                <textarea
                  value={formData.cargo.description || ''}
                  onChange={(e) => updateField('cargo', 'description', e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Additional cargo details..."
                />
              </div>
            </div>
          </div>
        </div>

        <button
          type="submit"
          disabled={createMutation.isPending}
          className="mt-6 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
        >
          {createMutation.isPending ? 'Submitting...' : 'Create Assessment & Run'}
        </button>

        {createMutation.isError && (
          <div className="mt-4 p-4 bg-red-500/20 border border-red-500/50 rounded-lg text-red-200">
            <p className="font-medium">Error creating assessment</p>
            <p className="text-sm mt-1">
              {createMutation.error instanceof Error 
                ? createMutation.error.message 
                : 'An unexpected error occurred'}
            </p>
          </div>
        )}
      </form>
    </div>
  );
}

export default NewAssessment;
