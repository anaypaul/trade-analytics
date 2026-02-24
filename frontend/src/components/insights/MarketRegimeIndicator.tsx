'use client'

import { MarketRegime } from '@/lib/api'

interface MarketRegimeIndicatorProps {
  regime: MarketRegime | null
}

const regimeConfig: Record<string, { color: string; bg: string; icon: string }> = {
  low_vol: { color: 'text-green-700 dark:text-green-400', bg: 'bg-green-100 dark:bg-green-900/30', icon: '~' },
  normal: { color: 'text-blue-700 dark:text-blue-400', bg: 'bg-blue-100 dark:bg-blue-900/30', icon: '~' },
  elevated: { color: 'text-yellow-700 dark:text-yellow-400', bg: 'bg-yellow-100 dark:bg-yellow-900/30', icon: '!' },
  high: { color: 'text-orange-700 dark:text-orange-400', bg: 'bg-orange-100 dark:bg-orange-900/30', icon: '!!' },
  extreme: { color: 'text-red-700 dark:text-red-400', bg: 'bg-red-100 dark:bg-red-900/30', icon: '!!!' },
  unknown: { color: 'text-gray-700 dark:text-gray-400', bg: 'bg-gray-100 dark:bg-gray-900/30', icon: '?' },
}

export function MarketRegimeIndicator({ regime }: MarketRegimeIndicatorProps) {
  if (!regime) {
    return (
      <div className="bg-muted/50 rounded-lg p-4">
        <p className="text-sm text-muted-foreground">Market regime data unavailable</p>
      </div>
    )
  }

  const config = regimeConfig[regime.regime] || regimeConfig.unknown

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {/* Regime Card */}
      <div className={`rounded-lg p-4 ${config.bg}`}>
        <div className="flex items-center justify-between mb-1">
          <h3 className="text-sm font-medium text-muted-foreground">Market Regime</h3>
          <span className={`text-lg font-bold ${config.color}`}>{config.icon}</span>
        </div>
        <p className={`text-lg font-semibold ${config.color}`}>
          {regime.regime_label}
        </p>
      </div>

      {/* VIX Card */}
      <div className="bg-muted/50 rounded-lg p-4">
        <h3 className="text-sm font-medium text-muted-foreground mb-1">VIX Level</h3>
        <p className="text-2xl font-bold">
          {regime.vix != null ? regime.vix.toFixed(2) : 'N/A'}
        </p>
        <p className="text-sm text-muted-foreground">
          Position size: {regime.position_size_pct}%
        </p>
      </div>

      {/* SPY Card */}
      <div className="bg-muted/50 rounded-lg p-4">
        <h3 className="text-sm font-medium text-muted-foreground mb-1">SPY Price</h3>
        <p className="text-2xl font-bold">
          {regime.spy_price != null ? `$${regime.spy_price.toFixed(2)}` : 'N/A'}
        </p>
        <p className="text-sm text-muted-foreground">
          {regime.gex_regime ? `GEX: ${regime.gex_regime}` : 'GEX: coming soon'}
        </p>
      </div>
    </div>
  )
}
