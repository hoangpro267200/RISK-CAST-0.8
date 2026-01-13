/**
 * Executive Summary Component (RC-A004)
 * 
 * CRITICAL: Optimized for 3-second decision making.
 * Users must understand risk level and top actions in 3 seconds.
 * 
 * Features:
 * - Large, color-coded risk score (immediate visual feedback)
 * - Risk level badge (LOW/MEDIUM/HIGH/CRITICAL)
 * - Top 3 risks (most impactful)
 * - Action buttons (View Details, Export)
 * - Vietnamese-first language
 */
import React from 'react';
import { Download, Eye, AlertTriangle, CheckCircle2, AlertCircle, TrendingUp } from 'lucide-react';
import { GlassCard } from './GlassCard';
import { BadgeRisk } from './BadgeRisk';
import { RiskOrbPremium } from './RiskOrbPremium';

export interface ExecutiveSummaryProps {
  /** Risk score (0-100) */
  riskScore: number;
  /** Risk level */
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | undefined;
  /** Top 3 risk drivers with impact */
  topRisks: Array<{ name: string; impact: number; contribution: number }>;
  /** Confidence score (0-1) */
  confidence: number;
  /** Executive explanation (1-2 sentences) */
  explanation?: string;
  /** Callback for View Details */
  onViewDetails?: () => void;
  /** Callback for Export */
  onExport?: () => void;
  /** Language (vi/en/zh) */
  language?: 'vi' | 'en' | 'zh';
}

const translations = {
  vi: {
    title: 'Tóm Tắt Điều Hành',
    riskScore: 'Điểm Rủi Ro',
    confidence: 'Độ Tin Cậy',
    topRisks: 'Top 3 Rủi Ro',
    viewDetails: 'Xem Chi Tiết',
    export: 'Xuất Báo Cáo',
    impact: 'Tác Động',
    contribution: 'Đóng Góp',
    percent: '%',
  },
  en: {
    title: 'Executive Summary',
    riskScore: 'Risk Score',
    confidence: 'Confidence',
    topRisks: 'Top 3 Risks',
    viewDetails: 'View Details',
    export: 'Export Report',
    impact: 'Impact',
    contribution: 'Contribution',
    percent: '%',
  },
  zh: {
    title: '执行摘要',
    riskScore: '风险评分',
    confidence: '置信度',
    topRisks: '前3大风险',
    viewDetails: '查看详情',
    export: '导出报告',
    impact: '影响',
    contribution: '贡献',
    percent: '%',
  },
};

export const ExecutiveSummary: React.FC<ExecutiveSummaryProps> = ({
  riskScore,
  riskLevel,
  topRisks = [],
  confidence,
  explanation,
  onViewDetails,
  onExport,
  language = 'vi',
}) => {
  const t = translations[language];
  
  // Get risk color based on level
  const getRiskColor = (level: string | undefined) => {
    switch (level) {
      case 'CRITICAL':
      case 'HIGH':
        return 'from-red-500 to-red-600';
      case 'MEDIUM':
        return 'from-amber-500 to-amber-600';
      case 'LOW':
        return 'from-emerald-500 to-emerald-600';
      default:
        return 'from-gray-500 to-gray-600';
    }
  };

  // Get risk icon
  const getRiskIcon = (level: string | undefined) => {
    switch (level) {
      case 'CRITICAL':
      case 'HIGH':
        return <AlertTriangle className="w-8 h-8 text-red-400" />;
      case 'MEDIUM':
        return <AlertCircle className="w-8 h-8 text-amber-400" />;
      case 'LOW':
        return <CheckCircle2 className="w-8 h-8 text-emerald-400" />;
      default:
        return <TrendingUp className="w-8 h-8 text-gray-400" />;
    }
  };

  // Format confidence
  const confidencePercent = Math.round(confidence * 100);
  const confidenceColor =
    confidence >= 0.8 ? 'text-emerald-400' :
    confidence >= 0.6 ? 'text-amber-400' :
    'text-red-400';

  return (
    <GlassCard variant="hero" className="border-2 border-blue-500/20 relative overflow-hidden">
      {/* Background gradient based on risk level */}
      <div className={`absolute inset-0 bg-gradient-to-br ${getRiskColor(riskLevel)} opacity-5 pointer-events-none`} />
      
      <div className="relative z-10">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            {getRiskIcon(riskLevel)}
            <h2 className="text-2xl font-bold text-white">{t.title}</h2>
          </div>
          
          {/* Action Buttons */}
          <div className="flex items-center gap-3">
            {onViewDetails && (
              <button
                onClick={onViewDetails}
                className="px-4 py-2 bg-white/10 hover:bg-white/20 border border-white/20 rounded-lg text-white text-sm font-medium transition-colors flex items-center gap-2"
                aria-label={t.viewDetails}
              >
                <Eye className="w-4 h-4" />
                {t.viewDetails}
              </button>
            )}
            {onExport && (
              <button
                onClick={onExport}
                className="px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white rounded-lg text-sm font-medium transition-all flex items-center gap-2 shadow-lg shadow-blue-500/25"
                aria-label={t.export}
              >
                <Download className="w-4 h-4" />
                {t.export}
              </button>
            )}
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-center">
          {/* Left: Risk Orb - Primary Focal Point */}
          <div className="flex flex-col items-center justify-center">
            <RiskOrbPremium 
              score={Math.round(riskScore)} 
              riskLevel={riskLevel}
            />
            
            {/* Risk Level Badge */}
            <div className="mt-6 text-center">
              {riskLevel ? (
                <BadgeRisk level={riskLevel} size="lg" />
              ) : (
                <span className="text-white/60 text-sm">Risk level: Unknown</span>
              )}
              
              {/* Score Display */}
              <div className="mt-3">
                <div className="text-4xl font-bold text-white">
                  {Math.round(riskScore)}
                  <span className="text-2xl text-white/60">/100</span>
                </div>
                <div className="text-sm text-white/60 mt-1">{t.riskScore}</div>
              </div>
              
              {/* Confidence */}
              <div className="mt-4 flex items-center justify-center gap-2">
                <span className="text-sm text-white/60">{t.confidence}:</span>
                <span className={`text-lg font-semibold ${confidenceColor}`}>
                  {confidencePercent}%
                </span>
              </div>
            </div>
          </div>

          {/* Right: Top 3 Risks + Explanation */}
          <div className="lg:col-span-2 space-y-4">
            {/* Executive Explanation (1-2 sentences) */}
            {explanation && (
              <div className="p-4 bg-white/5 rounded-xl border border-white/10">
                <p className="text-white/90 text-base leading-relaxed">
                  {explanation}
                </p>
              </div>
            )}

            {/* Top 3 Risks */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-blue-400" />
                {t.topRisks}
              </h3>
              
              <div className="space-y-3">
                {topRisks.slice(0, 3).map((risk, idx) => (
                  <div
                    key={idx}
                    className="flex items-center gap-4 p-4 bg-white/5 rounded-xl border border-white/10 hover:border-white/20 transition-colors"
                  >
                    {/* Rank Badge */}
                    <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center font-bold text-white ${
                      idx === 0 ? 'bg-red-500/30 border-2 border-red-500/50' :
                      idx === 1 ? 'bg-amber-500/30 border-2 border-amber-500/50' :
                      'bg-blue-500/30 border-2 border-blue-500/50'
                    }`}>
                      {idx + 1}
                    </div>
                    
                    {/* Risk Info */}
                    <div className="flex-1 min-w-0">
                      <div className="text-white font-medium truncate">
                        {risk.name}
                      </div>
                      <div className="flex items-center gap-4 mt-1 text-sm">
                        <span className="text-white/60">
                          {t.impact}: <span className="text-white font-semibold">+{risk.impact.toFixed(1)}%</span>
                        </span>
                        <span className="text-white/60">
                          {t.contribution}: <span className="text-white font-semibold">{risk.contribution.toFixed(1)}{t.percent}</span>
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
                
                {topRisks.length === 0 && (
                  <div className="p-4 bg-white/5 rounded-xl border border-white/10 text-center text-white/60">
                    No risk data available
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </GlassCard>
  );
};
