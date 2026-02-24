'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  getMarketRegime,
  getVolatilityScanner,
  getDailyInsights,
  getEarningsCalendar,
  MarketRegime,
  VolatilitySnapshot,
  DailyInsight,
  EarningsEvent,
} from '@/lib/api'
import { MarketRegimeIndicator } from './MarketRegimeIndicator'
import { VolatilityScannerTable } from './VolatilityScannerTable'
import { DailyInsightsList } from './DailyInsightsList'
import { EarningsCalendarWidget } from './EarningsCalendarWidget'

interface InsightsTabProps {
  formatCurrency: (value: number) => string
  formatPercent: (value: number) => string
}

export function InsightsTab({ formatCurrency, formatPercent }: InsightsTabProps) {
  const [regime, setRegime] = useState<MarketRegime | null>(null)
  const [volSnapshots, setVolSnapshots] = useState<VolatilitySnapshot[]>([])
  const [insights, setInsights] = useState<DailyInsight[]>([])
  const [earnings, setEarnings] = useState<EarningsEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeSection, setActiveSection] = useState<'overview' | 'scanner' | 'insights'>('overview')

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const [regimeData, volData, insightsData, earningsData] = await Promise.allSettled([
        getMarketRegime(),
        getVolatilityScanner(),
        getDailyInsights(10),
        getEarningsCalendar(),
      ])

      if (regimeData.status === 'fulfilled') setRegime(regimeData.value)
      if (volData.status === 'fulfilled') setVolSnapshots(volData.value)
      if (insightsData.status === 'fulfilled') setInsights(insightsData.value)
      if (earningsData.status === 'fulfilled') setEarnings(earningsData.value)
    } catch (err: any) {
      setError(err.message || 'Failed to load insights data')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="animate-pulse">
          <div className="h-6 bg-muted rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="h-24 bg-muted rounded"></div>
            <div className="h-24 bg-muted rounded"></div>
            <div className="h-24 bg-muted rounded"></div>
          </div>
          <div className="h-64 bg-muted rounded"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Daily Options Insights</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Market regime, volatility scanner, and trade recommendations
          </p>
        </div>
        <button
          onClick={loadData}
          className="px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
        >
          Refresh
        </button>
      </div>

      {error && (
        <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* Market Regime Card */}
      <MarketRegimeIndicator regime={regime} />

      {/* Section Tabs */}
      <div className="flex space-x-1 bg-muted/50 rounded-lg p-1">
        {(['overview', 'scanner', 'insights'] as const).map((section) => (
          <button
            key={section}
            onClick={() => setActiveSection(section)}
            className={`flex-1 py-2 px-3 text-sm font-medium rounded-md transition-colors ${
              activeSection === section
                ? 'bg-background shadow-sm text-foreground'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            {section === 'overview' ? 'Overview' : section === 'scanner' ? 'Volatility Scanner' : 'Trade Setups'}
          </button>
        ))}
      </div>

      {/* Section Content */}
      {activeSection === 'overview' && (
        <div className="space-y-6">
          {/* Top Premium Selling Candidates */}
          <div>
            <h3 className="text-lg font-medium mb-3">Top Premium Selling Candidates</h3>
            <p className="text-sm text-muted-foreground mb-3">
              Stocks with IVR &gt; 50 — options are expensive, sell premium
            </p>
            <VolatilityScannerTable
              snapshots={volSnapshots.filter(s => (s.iv_rank ?? 0) >= 50).slice(0, 5)}
              formatPercent={formatPercent}
              compact
            />
          </div>

          {/* Upcoming Earnings */}
          {earnings.length > 0 && (
            <EarningsCalendarWidget earnings={earnings.slice(0, 5)} />
          )}
        </div>
      )}

      {activeSection === 'scanner' && (
        <VolatilityScannerTable
          snapshots={volSnapshots}
          formatPercent={formatPercent}
        />
      )}

      {activeSection === 'insights' && (
        <DailyInsightsList
          insights={insights}
          formatCurrency={formatCurrency}
        />
      )}
    </div>
  )
}
