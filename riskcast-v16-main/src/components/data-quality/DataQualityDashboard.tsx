/**
 * Data Quality Dashboard
 * 
 * Shows users the quality and freshness of data being used
 * so they can make informed decisions.
 */

import React, { useState, useEffect } from 'react';
import {
  CheckCircle,
  AlertTriangle,
  XCircle,
  RefreshCw,
  Clock,
  Database,
  Cloud,
  Ship,
  Truck,
  Thermometer,
  Info
} from 'lucide-react';

import { dataQualityApi, DataQualityOverview, DataSourceStatus } from '@/api/dataQuality';
import { formatRelativeTime } from '@/utils/format';
import { GlassCard } from '@/components/GlassCard';
import { Skeleton, SkeletonCard } from '@/components/ui/Skeleton';
import { Tooltip } from '@/components/ui/Tooltip';

export function DataQualityDashboard() {
  const [overview, setOverview] = useState<DataQualityOverview | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const fetchOverview = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await dataQualityApi.getOverview();
      setOverview(data);
      setLastRefresh(new Date());
    } catch (err: any) {
      setError(err.message || 'Failed to load data quality overview');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
    // Auto-refresh every minute
    const interval = setInterval(fetchOverview, 60000);
    return () => clearInterval(interval);
  }, []);

  if (isLoading && !overview) {
    return <LoadingSkeleton />;
  }

  if (error && !overview) {
    return (
      <div className="space-y-6">
        <div className="backdrop-blur-xl bg-red-500/10 border border-red-500/20 rounded-2xl p-6">
          <div className="flex items-center gap-3">
            <XCircle className="h-5 w-5 text-red-400" />
            <div>
              <h3 className="text-lg font-semibold text-white mb-1">Error Loading Data Quality</h3>
              <p className="text-sm text-white/60">{error}</p>
            </div>
            <button
              onClick={fetchOverview}
              className="ml-auto px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-white/80 hover:text-white transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!overview) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-white">Data Quality Status</h2>
          <p className="text-white/60 text-sm mt-1">
            Real-time status of external data sources
          </p>
        </div>
        <button
          onClick={fetchOverview}
          disabled={isLoading}
          className="inline-flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-white/80 hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Warnings */}
      {overview.warnings.length > 0 && (
        <div className="backdrop-blur-xl bg-yellow-500/10 border border-yellow-500/20 rounded-2xl p-6">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-yellow-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-white mb-2">Data Quality Warnings</h3>
              <ul className="list-disc list-inside space-y-1 text-sm text-white/80">
                {overview.warnings.map((warning, i) => (
                  <li key={i}>{warning}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Overall Status */}
      <GlassCard>
        <div className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <StatusIcon status={overview.overall_status} size="large" />
              <div>
                <h3 className="text-lg font-medium text-white">
                  Overall Status: {overview.overall_status}
                </h3>
                <p className="text-sm text-white/60">
                  Last checked: {formatRelativeTime(overview.last_check)}
                </p>
              </div>
            </div>
            
            <div className="text-right">
              <div className="text-3xl font-bold text-white">
                {(overview.overall_confidence * 100).toFixed(0)}%
              </div>
              <div className="text-sm text-white/60">
                Overall Confidence
              </div>
            </div>
          </div>
          
          <div className="mt-4">
            <div className="h-2 bg-white/5 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-500"
                style={{ width: `${overview.overall_confidence * 100}%` }}
              />
            </div>
          </div>
        </div>
      </GlassCard>

      {/* Data Sources */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {overview.sources.map((source) => (
          <DataSourceCard key={source.source_name} source={source} />
        ))}
      </div>

      {/* Quality Legend */}
      <GlassCard>
        <div className="p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Data Quality Levels</h3>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 text-sm">
            <QualityLevelInfo 
              level="REAL_TIME" 
              description="Fresh data from API (< 15 min)"
              confidence="90-100%"
            />
            <QualityLevelInfo 
              level="CACHED" 
              description="Cached data (15 min - 1 hr)"
              confidence="80-90%"
            />
            <QualityLevelInfo 
              level="STALE" 
              description="Stale data (1-6 hrs)"
              confidence="60-80%"
            />
            <QualityLevelInfo 
              level="HISTORICAL" 
              description="Historical average"
              confidence="40-60%"
            />
            <QualityLevelInfo 
              level="FALLBACK" 
              description="Default values (API unavailable)"
              confidence="< 40%"
            />
          </div>
        </div>
      </GlassCard>
    </div>
  );
}


function DataSourceCard({ source }: { source: DataSourceStatus }) {
  const Icon = getSourceIcon(source.source_type);
  
  return (
    <GlassCard>
      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${getSourceBg(source.status)}`}>
              <Icon className="h-5 w-5 text-white/80" />
            </div>
            <div>
              <h4 className="font-medium text-white capitalize">
                {source.source_name.replace('_', ' ')}
              </h4>
              <p className="text-xs text-white/60">
                {source.source_type}
              </p>
            </div>
          </div>
          <StatusIcon status={source.status} />
        </div>
        
        <div className="space-y-2 mb-4">
          <div className="flex justify-between text-sm">
            <span className="text-white/60">Quality</span>
            <QualityBadge quality={source.data_quality} />
          </div>
          
          <div className="flex justify-between text-sm">
            <span className="text-white/60">Confidence</span>
            <span className="font-medium text-white">
              {(source.confidence * 100).toFixed(0)}%
            </span>
          </div>
          
          <div className="flex justify-between text-sm">
            <span className="text-white/60">Last Updated</span>
            <span className="text-white/80">
              {source.last_updated 
                ? formatRelativeTime(source.last_updated)
                : 'Never'}
            </span>
          </div>
        </div>
        
        {source.error_message && (
          <div className="mb-4 p-2 bg-red-500/10 border border-red-500/20 rounded text-xs text-red-300">
            {source.error_message}
          </div>
        )}
        
        <div className="h-1 bg-white/5 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${getProgressColor(source.status)}`}
            style={{ width: `${source.confidence * 100}%` }}
          />
        </div>
      </div>
    </GlassCard>
  );
}


function StatusIcon({ 
  status, 
  size = 'small' 
}: { 
  status: string; 
  size?: 'small' | 'large';
}) {
  const className = size === 'large' ? 'h-8 w-8' : 'h-5 w-5';
  
  switch (status) {
    case 'HEALTHY':
      return <CheckCircle className={`${className} text-green-400`} />;
    case 'DEGRADED':
      return <AlertTriangle className={`${className} text-yellow-400`} />;
    case 'OFFLINE':
      return <XCircle className={`${className} text-red-400`} />;
    default:
      return <Info className={`${className} text-white/40`} />;
  }
}


function QualityBadge({ quality }: { quality: string }) {
  const variants: Record<string, string> = {
    REAL_TIME: 'bg-green-500/20 text-green-300 border-green-500/30',
    CACHED: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    STALE: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
    HISTORICAL: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
    FALLBACK: 'bg-red-500/20 text-red-300 border-red-500/30',
  };
  
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium border ${variants[quality] || 'bg-white/5 text-white/60 border-white/10'}`}>
      {quality}
    </span>
  );
}


function QualityLevelInfo({ 
  level, 
  description, 
  confidence 
}: { 
  level: string; 
  description: string; 
  confidence: string;
}) {
  return (
    <Tooltip content={description}>
      <div className="text-center p-3 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 transition-colors cursor-help">
        <QualityBadge quality={level} />
        <p className="text-xs text-white/60 mt-2">
          {confidence}
        </p>
      </div>
    </Tooltip>
  );
}


function getSourceIcon(type: string) {
  switch (type) {
    case 'weather':
      return Cloud;
    case 'port':
      return Ship;
    case 'carrier':
      return Truck;
    case 'climate':
      return Thermometer;
    default:
      return Database;
  }
}


function getSourceBg(status: string): string {
  switch (status) {
    case 'HEALTHY':
      return 'bg-green-500/10';
    case 'DEGRADED':
      return 'bg-yellow-500/10';
    case 'OFFLINE':
      return 'bg-red-500/10';
    default:
      return 'bg-white/5';
  }
}


function getProgressColor(status: string): string {
  switch (status) {
    case 'HEALTHY':
      return 'bg-gradient-to-r from-green-500 to-emerald-500';
    case 'DEGRADED':
      return 'bg-gradient-to-r from-yellow-500 to-orange-500';
    case 'OFFLINE':
      return 'bg-gradient-to-r from-red-500 to-rose-500';
    default:
      return 'bg-white/20';
  }
}


function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      <div className="h-8 w-64 bg-white/5 rounded-lg animate-pulse" />
      <SkeletonCard showHeader contentLines={2} />
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <SkeletonCard key={i} showHeader contentLines={3} />
        ))}
      </div>
    </div>
  );
}
