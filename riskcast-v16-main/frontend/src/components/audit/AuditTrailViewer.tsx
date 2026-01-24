/**
 * Audit Trail Viewer
 * 
 * Displays and filters audit events with hash chain verification.
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Search,
  Filter,
  CheckCircle,
  XCircle,
  Shield,
  Link2,
  Eye,
  Download,
  RefreshCw,
  X,
} from 'lucide-react';

import { auditApi } from '../../api/client';
import { formatDateTime } from '../../utils/format';
import { StatusBadge } from '../common/StatusBadge';

interface AuditEvent {
  id: string;
  tenant_id: string;
  sequence_num?: number;
  event_type: string;
  action: string;
  entity_type?: string;
  entity_id?: string;
  actor_type: string;
  actor_id?: string;
  payload_json?: Record<string, any>;
  prev_hash?: string;
  event_hash: string;
  created_at: string;
}

interface AuditFilters {
  event_type?: string;
  entity_type?: string;
  entity_id?: string;
  actor_id?: string;
  start_date?: string;
  end_date?: string;
}

interface ChainVerification {
  valid: boolean;
  event_count?: number;
  verified_events?: number;
  first_invalid_sequence?: number;
  errors?: string[];
  from_sequence?: number;
}

export function AuditTrailViewer() {
  const [filters, setFilters] = useState<AuditFilters>({});
  const [selectedEvent, setSelectedEvent] = useState<AuditEvent | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  const { data: eventsResponse, isLoading, refetch } = useQuery({
    queryKey: ['audit-events', filters],
    queryFn: async () => {
      const response = await auditApi.listEvents({
        entity_type: filters.entity_type,
        entity_id: filters.entity_id,
        from_date: filters.start_date,
        to_date: filters.end_date,
        limit: 100,
      });
      return response.data;
    },
  });

  const events: AuditEvent[] = eventsResponse?.events || eventsResponse?.items || eventsResponse || [];

  const { data: verification } = useQuery<ChainVerification>({
    queryKey: ['audit-verification'],
    queryFn: async () => {
      const response = await auditApi.verifyChain();
      return response.data;
    },
  });

  const handleExport = async () => {
    try {
      const response = await auditApi.exportChain({ format: 'json' });
      const data = response.data;
      
      // Create download
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: 'application/json',
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit-export-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export failed:', error);
      alert('Failed to export audit trail');
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Audit Trail</h1>
          <p className="text-white/60 mt-1">
            Immutable record of all system events
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-white/10 hover:bg-white/20 border border-white/20 rounded-lg text-white transition-colors flex items-center gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
          <button
            onClick={handleExport}
            className="px-4 py-2 bg-white/10 hover:bg-white/20 border border-white/20 rounded-lg text-white transition-colors flex items-center gap-2"
          >
            <Download className="h-4 w-4" />
            Export
          </button>
        </div>
      </div>

      {/* Chain Verification Status */}
      <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Shield
              className={`h-8 w-8 ${
                verification?.valid ? 'text-green-400' : 'text-red-400'
              }`}
            />
            <div>
              <h3 className="font-medium text-white">Hash Chain Verification</h3>
              <p className="text-sm text-white/60">
                {verification?.valid
                  ? 'All events verified - chain integrity confirmed'
                  : 'Chain integrity issue detected'}
              </p>
            </div>
          </div>

          {verification?.valid ? (
            <span className="px-3 py-1 rounded-full text-xs font-medium border border-green-500/60 text-green-300 inline-flex items-center">
              <CheckCircle className="h-3 w-3 mr-1" />
              Verified
            </span>
          ) : (
            <span className="px-3 py-1 rounded-full text-xs font-medium bg-red-500/20 text-red-300 border border-red-500/50 inline-flex items-center">
              <XCircle className="h-3 w-3 mr-1" />
              Verification Failed
            </span>
          )}
        </div>

        {verification && (
          <div className="mt-4 grid grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-white/60">Total Events</span>
              <p className="font-medium text-white">
                {verification.event_count || 0}
              </p>
            </div>
            <div>
              <span className="text-white/60">Verified Events</span>
              <p className="font-medium text-white">
                {verification.verified_events || 0}
              </p>
            </div>
            <div>
              <span className="text-white/60">First Invalid</span>
              <p className="font-medium text-white">
                {verification.first_invalid_sequence || '-'}
              </p>
            </div>
            <div>
              <span className="text-white/60">Errors</span>
              <p className="font-medium text-white">
                {verification.errors?.length || 0}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg">
        <div className="p-4 border-b border-white/10 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">Filters</h2>
          <button
            type="button"
            onClick={() => setShowFilters(!showFilters)}
            className="px-3 py-1.5 text-sm bg-white/10 hover:bg-white/20 border border-white/20 rounded-lg text-white transition-colors flex items-center gap-2"
          >
            <Filter className="h-4 w-4" />
            {showFilters ? 'Hide' : 'Show'} Filters
          </button>
        </div>

        {showFilters && (
          <div className="p-4">
            <div className="grid md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-white/80 mb-2">
                  Event Type
                </label>
                <select
                  value={filters.event_type || 'ALL'}
                  onChange={(e) =>
                    setFilters((f) => ({
                      ...f,
                      event_type: e.target.value === 'ALL' ? undefined : e.target.value,
                    }))
                  }
                  className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="ALL">All Types</option>
                  <option value="POLICY">Policy</option>
                  <option value="CLAIM">Claim</option>
                  <option value="RISK_ASSESSMENT">Risk Assessment</option>
                  <option value="QUOTE">Quote</option>
                  <option value="PAYOUT">Payout</option>
                  <option value="MODEL">Model</option>
                  <option value="EVIDENCE">Evidence</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-white/80 mb-2">
                  Entity Type
                </label>
                <select
                  value={filters.entity_type || 'ALL'}
                  onChange={(e) =>
                    setFilters((f) => ({
                      ...f,
                      entity_type: e.target.value === 'ALL' ? undefined : e.target.value,
                    }))
                  }
                  className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="ALL">All Entities</option>
                  <option value="policy">Policy</option>
                  <option value="claim">Claim</option>
                  <option value="risk_run">Risk Run</option>
                  <option value="quote">Quote</option>
                  <option value="evidence_bundle">Evidence Bundle</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-white/80 mb-2">
                  Entity ID
                </label>
                <input
                  type="text"
                  placeholder="Filter by entity ID..."
                  value={filters.entity_id || ''}
                  onChange={(e) =>
                    setFilters((f) => ({
                      ...f,
                      entity_id: e.target.value || undefined,
                    }))
                  }
                  className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-white/80 mb-2">
                  Actor ID
                </label>
                <input
                  type="text"
                  placeholder="Filter by actor..."
                  value={filters.actor_id || ''}
                  onChange={(e) =>
                    setFilters((f) => ({
                      ...f,
                      actor_id: e.target.value || undefined,
                    }))
                  }
                  className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="flex justify-end mt-4 gap-2">
              <button
                type="button"
                onClick={() => setFilters({})}
                className="px-4 py-2 border border-white/20 text-white rounded-lg hover:bg-white/10 transition-colors"
              >
                Clear Filters
              </button>
              <button
                type="button"
                onClick={() => refetch()}
                className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
              >
                Apply Filters
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Events Table */}
      <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg">
        <div className="p-4 border-b border-white/10">
          <h2 className="text-lg font-semibold text-white">Audit Events</h2>
          <p className="text-sm text-white/60 mt-1">
            {events.length} events found
          </p>
        </div>
        <div className="p-4 overflow-x-auto">
          {isLoading ? (
            <div className="flex justify-center py-8">
              <RefreshCw className="h-8 w-8 animate-spin text-white/40" />
            </div>
          ) : events.length === 0 ? (
            <div className="text-center py-12 text-white/60">
              No events found.
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/10 text-white/60">
                  <th className="text-left py-2 px-3 font-medium">Timestamp</th>
                  <th className="text-left py-2 px-3 font-medium">Event Type</th>
                  <th className="text-left py-2 px-3 font-medium">Action</th>
                  <th className="text-left py-2 px-3 font-medium">Entity</th>
                  <th className="text-left py-2 px-3 font-medium">Actor</th>
                  <th className="text-left py-2 px-3 font-medium">Hash</th>
                  <th className="text-left py-2 px-3 font-medium"></th>
                </tr>
              </thead>
              <tbody>
                {events.map((event: AuditEvent) => (
                  <tr
                    key={event.id}
                    className="border-b border-white/5 hover:bg-white/5 transition-colors"
                  >
                    <td className="py-2 px-3 text-white/80">
                      {formatDateTime(event.created_at)}
                    </td>
                    <td className="py-2 px-3">
                      <StatusBadge status={event.event_type} />
                    </td>
                    <td className="py-2 px-3 text-white/90">{event.action}</td>
                    <td className="py-2 px-3">
                      <div className="text-sm">
                        <span className="text-white/60">
                          {event.entity_type || 'N/A'}:
                        </span>
                        {event.entity_id && (
                          <span className="font-mono ml-1 text-white/80">
                            {event.entity_id.slice(0, 8)}...
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="py-2 px-3">
                      <div className="text-sm">
                        <StatusBadge status={event.actor_type} />
                        {event.actor_id && (
                          <span className="font-mono ml-1 text-xs text-white/60">
                            {event.actor_id.slice(0, 8)}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="py-2 px-3">
                      <div className="flex items-center gap-1">
                        <Link2 className="h-3 w-3 text-white/40" />
                        <span className="font-mono text-xs text-white/70">
                          {event.event_hash.slice(0, 12)}...
                        </span>
                      </div>
                    </td>
                    <td className="py-2 px-3">
                      <button
                        type="button"
                        onClick={() => setSelectedEvent(event)}
                        className="text-blue-400 hover:text-blue-300"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Event Detail Sidebar */}
      {selectedEvent && (
        <div className="fixed inset-y-0 right-0 w-[500px] bg-slate-900 border-l border-white/10 z-50 overflow-y-auto">
          <div className="p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold text-white">Event Details</h2>
              <button
                type="button"
                onClick={() => setSelectedEvent(null)}
                className="text-white/60 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-6">
              {/* Basic Info */}
              <div className="space-y-2">
                <h4 className="font-medium text-white">Basic Information</h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <span className="text-white/60">Event ID</span>
                  <span className="font-mono text-xs text-white break-all">
                    {selectedEvent.id}
                  </span>

                  <span className="text-white/60">Timestamp</span>
                  <span className="text-white">
                    {formatDateTime(selectedEvent.created_at)}
                  </span>

                  <span className="text-white/60">Event Type</span>
                  <span className="text-white">{selectedEvent.event_type}</span>

                  <span className="text-white/60">Action</span>
                  <span className="text-white">{selectedEvent.action}</span>

                  {selectedEvent.sequence_num !== undefined && (
                    <>
                      <span className="text-white/60">Sequence</span>
                      <span className="text-white">
                        {selectedEvent.sequence_num}
                      </span>
                    </>
                  )}
                </div>
              </div>

              <div className="h-px bg-white/10"></div>

              {/* Entity Info */}
              <div className="space-y-2">
                <h4 className="font-medium text-white">Entity</h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <span className="text-white/60">Type</span>
                  <span className="text-white">
                    {selectedEvent.entity_type || 'N/A'}
                  </span>

                  <span className="text-white/60">ID</span>
                  <span className="font-mono text-xs text-white break-all">
                    {selectedEvent.entity_id || 'N/A'}
                  </span>
                </div>
              </div>

              <div className="h-px bg-white/10"></div>

              {/* Actor Info */}
              <div className="space-y-2">
                <h4 className="font-medium text-white">Actor</h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <span className="text-white/60">Type</span>
                  <span className="text-white">{selectedEvent.actor_type}</span>

                  <span className="text-white/60">ID</span>
                  <span className="font-mono text-xs text-white break-all">
                    {selectedEvent.actor_id || 'N/A'}
                  </span>
                </div>
              </div>

              <div className="h-px bg-white/10"></div>

              {/* Hash Chain */}
              <div className="space-y-2">
                <h4 className="font-medium text-white flex items-center">
                  <Link2 className="h-4 w-4 mr-2" />
                  Hash Chain
                </h4>
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="text-white/60">Previous Hash</span>
                    <p className="font-mono text-xs break-all bg-white/5 p-2 rounded mt-1 text-white/80">
                      {selectedEvent.prev_hash || 'GENESIS (no previous)'}
                    </p>
                  </div>
                  <div>
                    <span className="text-white/60">Event Hash</span>
                    <p className="font-mono text-xs break-all bg-white/5 p-2 rounded mt-1 text-white">
                      {selectedEvent.event_hash}
                    </p>
                  </div>
                </div>
              </div>

              <div className="h-px bg-white/10"></div>

              {/* Payload */}
              {selectedEvent.payload_json && (
                <div className="space-y-2">
                  <h4 className="font-medium text-white">Payload</h4>
                  <pre className="text-xs bg-white/5 p-3 rounded overflow-auto max-h-[300px] text-white/90 border border-white/10">
                    {JSON.stringify(selectedEvent.payload_json, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
