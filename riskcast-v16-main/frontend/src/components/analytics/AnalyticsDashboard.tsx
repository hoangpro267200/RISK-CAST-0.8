/**
 * Analytics Dashboard
 * 
 * Displays loss ratios, model performance, and ROI metrics.
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Percent,
  Target,
  Activity,
  AlertTriangle,
  CheckCircle,
} from 'lucide-react';

import { analyticsApi } from '../../api/client';
import { formatCurrency, formatPercent } from '../../utils/format';
import { StatusBadge } from '../common/StatusBadge';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

export function AnalyticsDashboard() {
  const [dateRange, setDateRange] = useState('12m');
  const [selectedCorridor, setSelectedCorridor] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'loss-analysis' | 'model-performance' | 'corridors'>('overview');

  // Calculate date range
  const endDate = new Date();
  const startDate = new Date();
  const months = parseInt(dateRange.replace('m', ''));
  startDate.setMonth(startDate.getMonth() - months);

  const { data: portfolioROI, isLoading: roiLoading } = useQuery({
    queryKey: ['portfolio-roi', dateRange],
    queryFn: async () => {
      const response = await analyticsApi.getPortfolioROI({
        period: dateRange,
        start_date: startDate.toISOString().split('T')[0],
        end_date: endDate.toISOString().split('T')[0],
      });
      return response.data;
    },
  });

  const { data: lossRatios, isLoading: lossLoading } = useQuery({
    queryKey: ['loss-ratios', dateRange],
    queryFn: async () => {
      const response = await analyticsApi.getLossRatios({
        period: dateRange,
        start_date: startDate.toISOString().split('T')[0],
        end_date: endDate.toISOString().split('T')[0],
      });
      return response.data;
    },
  });

  const { data: modelPerformance, isLoading: modelLoading } = useQuery({
    queryKey: ['model-performance'],
    queryFn: async () => {
      const response = await analyticsApi.getModelPerformance();
      return response.data;
    },
  });

  const { data: trendData, isLoading: trendLoading } = useQuery({
    queryKey: ['loss-trend', dateRange],
    queryFn: async () => {
      const response = await analyticsApi.getLossTrend({ months });
      return response.data;
    },
  });

  if (roiLoading || lossLoading || trendLoading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-white/60">Loading analytics...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Analytics</h1>
          <p className="text-white/60 mt-1">
            Portfolio performance and risk analytics
          </p>
        </div>

        <select
          value={dateRange}
          onChange={(e) => setDateRange(e.target.value)}
          className="px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="3m">Last 3 Months</option>
          <option value="6m">Last 6 Months</option>
          <option value="12m">Last 12 Months</option>
          <option value="24m">Last 24 Months</option>
        </select>
      </div>

      {/* KPI Cards */}
      {portfolioROI && (
        <div className="grid gap-4 md:grid-cols-4">
          <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4">
            <div className="flex items-center mb-2 text-white/60 text-sm">
              <DollarSign className="h-4 w-4 mr-2" />
              Total Premium
            </div>
            <div className="text-2xl font-bold text-white">
              {portfolioROI.portfolio_summary?.total_premium_cents
                ? formatCurrency(portfolioROI.portfolio_summary.total_premium_cents / 100)
                : 'N/A'}
            </div>
            <p className="text-xs text-white/60 mt-1">
              {portfolioROI.portfolio_summary?.policy_count || 0} policies
            </p>
          </div>

          <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4">
            <div className="flex items-center mb-2 text-white/60 text-sm">
              <Percent className="h-4 w-4 mr-2" />
              Loss Ratio
            </div>
            <div className="flex items-center">
              <span className="text-2xl font-bold text-white">
                {portfolioROI.loss_performance?.loss_ratio
                  ? formatPercent(portfolioROI.loss_performance.loss_ratio)
                  : 'N/A'}
              </span>
              {portfolioROI.loss_performance?.loss_ratio &&
                (portfolioROI.loss_performance.loss_ratio < 0.6 ? (
                  <TrendingDown className="h-5 w-5 ml-2 text-green-400" />
                ) : (
                  <TrendingUp className="h-5 w-5 ml-2 text-red-400" />
                ))}
            </div>
            <p className="text-xs text-white/60 mt-1">Target: 60%</p>
          </div>

          <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4">
            <div className="flex items-center mb-2 text-white/60 text-sm">
              <Target className="h-4 w-4 mr-2" />
              Gross Margin
            </div>
            <div className="text-2xl font-bold text-white">
              {portfolioROI.profitability?.gross_margin_pct
                ? formatPercent(portfolioROI.profitability.gross_margin_pct / 100)
                : 'N/A'}
            </div>
            <p className="text-xs text-white/60 mt-1">
              {portfolioROI.profitability?.gross_margin_cents
                ? formatCurrency(portfolioROI.profitability.gross_margin_cents / 100)
                : 'N/A'}
            </p>
          </div>

          <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4">
            <div className="flex items-center mb-2 text-white/60 text-sm">
              <Activity className="h-4 w-4 mr-2" />
              Model Accuracy
            </div>
            <div className="flex items-center">
              <span className="text-2xl font-bold text-white">
                {portfolioROI.model_performance?.prediction_accuracy
                  ? formatPercent(portfolioROI.model_performance.prediction_accuracy)
                  : 'N/A'}
              </span>
              {portfolioROI.model_performance?.prediction_accuracy &&
                portfolioROI.model_performance.prediction_accuracy > 0.9 && (
                  <CheckCircle className="h-5 w-5 ml-2 text-green-400" />
                )}
            </div>
            <p className="text-xs text-white/60 mt-1">Expected vs Actual</p>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div>
        <div className="flex gap-2 border-b border-white/10 mb-4">
          {[
            { id: 'overview', label: 'Overview' },
            { id: 'loss-analysis', label: 'Loss Analysis' },
            { id: 'model-performance', label: 'Model Performance' },
            { id: 'corridors', label: 'By Corridor' },
          ].map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
                activeTab === tab.id
                  ? 'text-white border-blue-500'
                  : 'text-white/60 border-transparent hover:text-white'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              {/* Loss Trend Chart */}
              <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-white mb-2">
                  Loss Ratio Trend
                </h3>
                <p className="text-sm text-white/60 mb-4">
                  Monthly loss ratio over time
                </p>
                {trendData?.monthly_data ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={trendData.monthly_data}>
                      <defs>
                        <linearGradient id="colorLossRatio" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#8884d8" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#8884d8" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                      <XAxis dataKey="month" stroke="rgba(255,255,255,0.6)" />
                      <YAxis
                        tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                        stroke="rgba(255,255,255,0.6)"
                      />
                      <Tooltip
                        formatter={(value: number | undefined) => value !== undefined ? formatPercent(value) : ''}
                        contentStyle={{
                          backgroundColor: 'rgba(0,0,0,0.8)',
                          border: '1px solid rgba(255,255,255,0.2)',
                          borderRadius: '8px',
                        }}
                      />
                      <Area
                        type="monotone"
                        dataKey="loss_ratio"
                        stroke="#8884d8"
                        fill="url(#colorLossRatio)"
                      />
                      <Line
                        type="monotone"
                        dataKey={() => 0.6}
                        stroke="#ff7300"
                        strokeDasharray="5 5"
                        name="Target"
                        strokeWidth={2}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[300px] flex items-center justify-center text-white/60">
                    No trend data available
                  </div>
                )}
              </div>

              {/* Premium vs Loss Chart */}
              <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-white mb-2">
                  Premium vs Loss
                </h3>
                <p className="text-sm text-white/60 mb-4">
                  Monthly comparison
                </p>
                {trendData?.monthly_data ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={trendData.monthly_data}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                      <XAxis dataKey="month" stroke="rgba(255,255,255,0.6)" />
                      <YAxis
                        tickFormatter={(v) => `$${(v / 100000).toFixed(0)}K`}
                        stroke="rgba(255,255,255,0.6)"
                      />
                      <Tooltip
                        formatter={(value: number | undefined) => value !== undefined ? formatCurrency(value / 100) : ''}
                        contentStyle={{
                          backgroundColor: 'rgba(0,0,0,0.8)',
                          border: '1px solid rgba(255,255,255,0.2)',
                          borderRadius: '8px',
                        }}
                      />
                      <Legend />
                      <Bar dataKey="premium_cents" name="Premium" fill="#0088FE" />
                      <Bar dataKey="actual_loss_cents" name="Actual Loss" fill="#FF8042" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[300px] flex items-center justify-center text-white/60">
                    No comparison data available
                  </div>
                )}
              </div>
            </div>

            {/* Trend Indicator */}
            {trendData?.trend && (
              <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    {trendData.trend.direction === 'IMPROVING' ? (
                      <TrendingDown className="h-8 w-8 text-green-400" />
                    ) : trendData.trend.direction === 'DETERIORATING' ? (
                      <TrendingUp className="h-8 w-8 text-red-400" />
                    ) : (
                      <Activity className="h-8 w-8 text-blue-400" />
                    )}
                    <div>
                      <h3 className="font-medium text-white">
                        Loss Ratio Trend: {trendData.trend.direction}
                      </h3>
                      <p className="text-sm text-white/60">
                        First half avg:{' '}
                        {formatPercent(trendData.trend.first_half_avg_loss_ratio)} →
                        Second half avg:{' '}
                        {formatPercent(trendData.trend.second_half_avg_loss_ratio)}
                      </p>
                    </div>
                  </div>
                  <StatusBadge
                    status={
                      trendData.trend.direction === 'IMPROVING'
                        ? 'IMPROVING'
                        : trendData.trend.direction === 'DETERIORATING'
                        ? 'DETERIORATING'
                        : 'STABLE'
                    }
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {/* Loss Analysis Tab */}
        {activeTab === 'loss-analysis' && (
          <div className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              {/* Loss by Cargo Type */}
              <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-white mb-4">
                  Loss Ratio by Cargo Type
                </h3>
                {lossRatios?.by_cargo_type ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={lossRatios.by_cargo_type} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                      <XAxis
                        type="number"
                        tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                        stroke="rgba(255,255,255,0.6)"
                      />
                      <YAxis
                        type="category"
                        dataKey="cargo_type"
                        width={100}
                        stroke="rgba(255,255,255,0.6)"
                      />
                      <Tooltip
                        formatter={(v: number | undefined) => v !== undefined ? formatPercent(v) : ''}
                        contentStyle={{
                          backgroundColor: 'rgba(0,0,0,0.8)',
                          border: '1px solid rgba(255,255,255,0.2)',
                          borderRadius: '8px',
                        }}
                      />
                      <Bar dataKey="loss_ratio" fill="#8884d8">
                        {lossRatios.by_cargo_type.map((entry: any, index: number) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={entry.loss_ratio > 0.6 ? '#FF8042' : '#00C49F'}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[300px] flex items-center justify-center text-white/60">
                    No cargo type data available
                  </div>
                )}
              </div>

              {/* Loss by Corridor */}
              <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-white mb-4">
                  Loss Ratio by Corridor
                </h3>
                {lossRatios?.by_corridor ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart
                      data={lossRatios.by_corridor.slice(0, 10)}
                      layout="vertical"
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                      <XAxis
                        type="number"
                        tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                        stroke="rgba(255,255,255,0.6)"
                      />
                      <YAxis
                        type="category"
                        dataKey="corridor_code"
                        width={120}
                        stroke="rgba(255,255,255,0.6)"
                      />
                      <Tooltip
                        formatter={(v: number | undefined) => v !== undefined ? formatPercent(v) : ''}
                        contentStyle={{
                          backgroundColor: 'rgba(0,0,0,0.8)',
                          border: '1px solid rgba(255,255,255,0.2)',
                          borderRadius: '8px',
                        }}
                      />
                      <Bar dataKey="loss_ratio" fill="#0088FE">
                        {lossRatios.by_corridor.map((entry: any, index: number) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={entry.loss_ratio > 0.6 ? '#FF8042' : '#00C49F'}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[300px] flex items-center justify-center text-white/60">
                    No corridor data available
                  </div>
                )}
              </div>
            </div>

            {/* Expected vs Actual Loss */}
            {portfolioROI && (
              <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-white mb-4">
                  Expected vs Actual Loss
                </h3>
                <p className="text-sm text-white/60 mb-4">
                  Model prediction accuracy
                </p>
                <div className="grid md:grid-cols-3 gap-6">
                  <div className="text-center">
                    <p className="text-sm text-white/60">Expected Loss</p>
                    <p className="text-2xl font-bold text-white">
                      {portfolioROI.loss_performance?.expected_loss_cents
                        ? formatCurrency(
                            portfolioROI.loss_performance.expected_loss_cents / 100
                          )
                        : 'N/A'}
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-white/60">Actual Loss</p>
                    <p className="text-2xl font-bold text-white">
                      {portfolioROI.loss_performance?.actual_loss_cents
                        ? formatCurrency(
                            portfolioROI.loss_performance.actual_loss_cents / 100
                          )
                        : 'N/A'}
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-white/60">Variance</p>
                    <p
                      className={`text-2xl font-bold ${
                        portfolioROI.loss_performance?.actual_loss_cents &&
                        portfolioROI.loss_performance?.expected_loss_cents &&
                        portfolioROI.loss_performance.actual_loss_cents <
                          portfolioROI.loss_performance.expected_loss_cents
                          ? 'text-green-400'
                          : 'text-red-400'
                      }`}
                    >
                      {portfolioROI.loss_performance?.actual_loss_cents &&
                      portfolioROI.loss_performance?.expected_loss_cents
                        ? formatCurrency(
                            (portfolioROI.loss_performance.actual_loss_cents -
                              portfolioROI.loss_performance.expected_loss_cents) /
                              100
                          )
                        : 'N/A'}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Model Performance Tab */}
        {activeTab === 'model-performance' && (
          <div className="space-y-4">
            {modelPerformance ? (
              <>
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4">
                    <h4 className="text-sm font-medium text-white mb-2">
                      Mean Prediction Error
                    </h4>
                    <div className="text-2xl font-bold text-white">
                      {modelPerformance.accuracy_metrics?.mean_prediction_error
                        ? formatPercent(
                            modelPerformance.accuracy_metrics.mean_prediction_error
                          )
                        : 'N/A'}
                    </div>
                  </div>

                  <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4">
                    <h4 className="text-sm font-medium text-white mb-2">
                      Expected/Actual Ratio
                    </h4>
                    <div className="text-2xl font-bold text-white">
                      {modelPerformance.accuracy_metrics?.expected_vs_actual_ratio
                        ? modelPerformance.accuracy_metrics.expected_vs_actual_ratio.toFixed(
                            2
                          )
                        : 'N/A'}
                    </div>
                    <p className="text-xs text-white/60 mt-1">Target: 1.00 (±0.1)</p>
                  </div>

                  <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4">
                    <h4 className="text-sm font-medium text-white mb-2">
                      Calibration Status
                    </h4>
                    <StatusBadge
                      status={
                        modelPerformance.calibration_recommendation?.action || 'NO_ACTION'
                      }
                    />
                    {modelPerformance.calibration_recommendation?.suggested_adjustment && (
                      <p className="text-xs text-white/60 mt-1">
                        Suggested:{' '}
                        {formatPercent(
                          modelPerformance.calibration_recommendation.suggested_adjustment
                        )}
                      </p>
                    )}
                  </div>
                </div>

                {/* Risk Score Distribution */}
                {modelPerformance.binned_analysis && (
                  <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-white mb-2">
                      Prediction Accuracy by Risk Score Bin
                    </h3>
                    <p className="text-sm text-white/60 mb-4">
                      How well predictions match actuals across risk levels
                    </p>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={modelPerformance.binned_analysis}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                        <XAxis dataKey="bin_label" stroke="rgba(255,255,255,0.6)" />
                        <YAxis
                          tickFormatter={(v) => v.toFixed(2)}
                          stroke="rgba(255,255,255,0.6)"
                        />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: 'rgba(0,0,0,0.8)',
                            border: '1px solid rgba(255,255,255,0.2)',
                            borderRadius: '8px',
                          }}
                        />
                        <Legend />
                        <Bar dataKey="expected_loss" name="Expected" fill="#8884d8" />
                        <Bar dataKey="actual_loss" name="Actual" fill="#82ca9d" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </>
            ) : (
              <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-8 text-center text-white/60">
                Model performance data not available
              </div>
            )}
          </div>
        )}

        {/* Corridors Tab */}
        {activeTab === 'corridors' && (
          <div className="space-y-4">
            {lossRatios?.by_corridor ? (
              <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-white mb-4">
                  Corridor Performance
                </h3>
                <div className="space-y-3">
                  {lossRatios.by_corridor.map((corridor: any) => (
                    <div
                      key={corridor.corridor_id}
                      className={`flex items-center justify-between p-4 border rounded-lg hover:bg-white/5 cursor-pointer transition-colors ${
                        selectedCorridor === corridor.corridor_id
                          ? 'border-blue-500 bg-blue-500/10'
                          : 'border-white/10'
                      }`}
                      onClick={() => setSelectedCorridor(corridor.corridor_id)}
                    >
                      <div>
                        <h4 className="font-medium text-white">
                          {corridor.corridor_code || corridor.corridor_id}
                        </h4>
                        <p className="text-sm text-white/60">
                          {corridor.policy_count || 0} policies
                        </p>
                      </div>
                      <div className="flex items-center gap-6">
                        <div className="text-right">
                          <p className="text-sm text-white/60">Premium</p>
                          <p className="font-medium text-white">
                            {corridor.total_premium_cents
                              ? formatCurrency(corridor.total_premium_cents / 100)
                              : 'N/A'}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm text-white/60">Loss Ratio</p>
                          <p
                            className={`font-medium ${
                              corridor.loss_ratio > 0.6
                                ? 'text-red-400'
                                : 'text-green-400'
                            }`}
                          >
                            {corridor.loss_ratio
                              ? formatPercent(corridor.loss_ratio)
                              : 'N/A'}
                          </p>
                        </div>
                        <StatusBadge
                          status={corridor.profitable ? 'PROFITABLE' : 'LOSS'}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-8 text-center text-white/60">
                No corridor data available
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
