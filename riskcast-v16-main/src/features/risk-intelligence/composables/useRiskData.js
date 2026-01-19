import { ref, watch } from 'vue'
import { useRiskStore } from '../stores/riskStore'
import { normalizeRiskData } from '../utils/risk/scoreNormalizer'
import axios from 'axios'

/**
 * Main data fetching and caching composable
 * Handles API calls and data normalization
 */
export function useRiskData() {
  const riskStore = useRiskStore()
  const isRefreshing = ref(false)
  const cache = new Map()
  const CACHE_TTL = 5 * 60 * 1000 // 5 minutes

  /**
   * Fetch risk data for shipment
   * @param {string} shipmentId
   * @param {boolean} forceRefresh - Bypass cache
   */
  async function fetchRiskData(shipmentId, forceRefresh = false) {
    if (!shipmentId) {
      throw new Error('Shipment ID is required')
    }

    // Check cache
    if (!forceRefresh) {
      const cached = getCachedData(shipmentId)
      if (cached) {
        riskStore.setData(cached)
        return cached
      }
    }

    // Fetch from API
    try {
      riskStore.setLoading(true)
      riskStore.setError(null)

      const response = await axios.get(`/api/v22/shipments/${shipmentId}/risk-intelligence`)
      const rawData = response.data

      // Normalize data
      const normalized = normalizeRiskData(rawData)

      // Cache data
      cacheData(shipmentId, normalized)

      // Update store
      riskStore.setData(normalized)

      return normalized
    } catch (err) {
      console.error('Failed to fetch risk data:', err)
      riskStore.setError(err)
      throw err
    } finally {
      riskStore.setLoading(false)
    }
  }

  /**
   * Refresh data manually
   * @param {string} shipmentId
   */
  async function refreshData(shipmentId) {
    isRefreshing.value = true
    try {
      await fetchRiskData(shipmentId, true)
    } finally {
      isRefreshing.value = false
    }
  }

  /**
   * Get cached data if valid
   * @param {string} shipmentId
   * @returns {Object|null}
   */
  function getCachedData(shipmentId) {
    const cached = cache.get(shipmentId)
    if (!cached) return null

    const now = Date.now()
    if (now - cached.timestamp > CACHE_TTL) {
      cache.delete(shipmentId)
      return null
    }

    return cached.data
  }

  /**
   * Cache data with timestamp
   * @param {string} shipmentId
   * @param {Object} data
   */
  function cacheData(shipmentId, data) {
    cache.set(shipmentId, {
      data,
      timestamp: Date.now()
    })
  }

  /**
   * Clear cache
   */
  function clearCache() {
    cache.clear()
  }

  /**
   * Load mock data for development
   */
  async function loadMockData() {
    const mockData = {
      shipment_id: 'MOCK-001',
      calculated_at: new Date().toISOString(),
      overall_risk_score: 72,
      
      layer_scores: [
        {
          layer_id: 'sanctions',
          layer_name: 'sanctions_risk',
          score: 85,
          weight: 0.15,
          description: 'Sanctions exposure along route',
          top_factors: [
            { factor: 'Iran transit', contribution: 0.6 },
            { factor: 'Russian airspace', contribution: 0.3 }
          ]
        },
        {
          layer_id: 'weather',
          layer_name: 'weather_risk',
          score: 65,
          weight: 0.1,
          description: 'Weather-related disruptions',
          top_factors: [
            { factor: 'Storm forecast', contribution: 0.5 },
            { factor: 'Typhoon season', contribution: 0.4 }
          ]
        },
        {
          layer_id: 'port_congestion',
          layer_name: 'port_congestion',
          score: 70,
          weight: 0.12,
          description: 'Port capacity and delays',
          top_factors: [
            { factor: 'Peak season', contribution: 0.7 }
          ]
        }
      ],
      
      esg: {
        e_score: 45,
        s_score: 60,
        g_score: 55
      },
      
      monte_carlo: {
        p50: 70,
        p95: 88,
        distribution: [
          { value: 50, probability: 0.05 },
          { value: 60, probability: 0.15 },
          { value: 70, probability: 0.30 },
          { value: 80, probability: 0.30 },
          { value: 90, probability: 0.15 },
          { value: 95, probability: 0.05 }
        ]
      },
      
      delay_prediction: {
        expected_days: 8,
        min_days: 4,
        max_days: 14,
        confidence: 0.85
      },
      
      shock_scenarios: [
        {
          scenario_id: 'port_closure',
          scenario_name: 'Port Closure',
          impact_score: 90,
          probability: 0.12,
          description: 'Unexpected port closure'
        },
        {
          scenario_id: 'storm',
          scenario_name: 'Severe Storm',
          impact_score: 75,
          probability: 0.25,
          description: 'Severe weather event'
        }
      ],
      
      risk_drivers: [
        {
          category: 'geopolitical',
          id: 'sanctions',
          name: 'Sanctions Risk',
          score: 85,
          weight: 0.4
        },
        {
          category: 'environmental',
          id: 'weather',
          name: 'Weather Risk',
          score: 65,
          weight: 0.3
        },
        {
          category: 'operational',
          id: 'port_congestion',
          name: 'Port Congestion',
          score: 70,
          weight: 0.3
        }
      ],
      
      timeline: {
        phases: [
          {
            phase_id: 'origin',
            phase_name: 'Origin Port',
            start_date: '2025-01-10',
            end_date: '2025-01-15',
            risk_level: 'low'
          },
          {
            phase_id: 'transit',
            phase_name: 'Ocean Transit',
            start_date: '2025-01-15',
            end_date: '2025-02-20',
            risk_level: 'high'
          },
          {
            phase_id: 'destination',
            phase_name: 'Destination Port',
            start_date: '2025-02-20',
            end_date: '2025-02-25',
            risk_level: 'medium'
          }
        ],
        events: [
          {
            event_id: 'storm',
            event_date: '2025-01-18',
            event_type: 'weather',
            severity: 'high',
            description: 'Storm forecast'
          },
          {
            event_id: 'sanctions',
            event_date: '2025-02-05',
            event_type: 'geopolitical',
            severity: 'critical',
            description: 'Sanctions announced'
          }
        ]
      }
    }

    const normalized = normalizeRiskData(mockData)
    riskStore.setData(normalized)
    return normalized
  }

  return {
    fetchRiskData,
    refreshData,
    clearCache,
    loadMockData,
    isRefreshing
  }
}






