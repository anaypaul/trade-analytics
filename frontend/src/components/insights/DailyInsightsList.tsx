'use client'

import { DailyInsight, dismissInsight } from '@/lib/api'
import { useState } from 'react'

interface DailyInsightsListProps {
  insights: DailyInsight[]
  formatCurrency: (value: number) => string
}

const priorityConfig: Record<number, { label: string; className: string }> = {
  1: { label: 'CRITICAL', className: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400' },
  2: { label: 'HIGH', className: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400' },
  3: { label: 'MEDIUM', className: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400' },
  4: { label: 'LOW', className: 'bg-gray-100 dark:bg-gray-900/30 text-gray-700 dark:text-gray-400' },
}

const typeIcons: Record<string, string> = {
  trade_setup: 'T',
  position_alert: '!',
  earnings_play: 'E',
  roll_recommendation: 'R',
  risk_warning: 'W',
  morning_brief: 'M',
  regime_change: 'G',
  flow_alert: 'F',
}

export function DailyInsightsList({ insights, formatCurrency }: DailyInsightsListProps) {
  const [dismissedIds, setDismissedIds] = useState<Set<string>>(new Set())

  const handleDismiss = async (id: string) => {
    try {
      await dismissInsight(id)
      setDismissedIds(prev => new Set([...Array.from(prev), id]))
    } catch {
      // Silently handle — user can retry
    }
  }

  const visible = insights.filter(i => !dismissedIds.has(i.id))

  if (visible.length === 0) {
    return (
      <div className="bg-muted/50 rounded-lg p-8 text-center">
        <p className="text-lg font-medium mb-1">No trade setups right now</p>
        <p className="text-sm text-muted-foreground">
          Insights are generated based on market conditions and your watchlist.
          Check back during market hours for fresh setups.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {visible.map((insight) => {
        const priority = priorityConfig[insight.priority] || priorityConfig[3]
        const icon = typeIcons[insight.insight_type] || '?'

        return (
          <div
            key={insight.id}
            className="border border-border rounded-lg p-4 hover:bg-muted/30 transition-colors"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-start gap-3 min-w-0">
                {/* Signal Score */}
                <div className="flex-shrink-0 w-10 h-10 rounded-full bg-muted flex items-center justify-center">
                  <span className="text-xs font-bold">
                    {insight.signal_score ?? icon}
                  </span>
                </div>

                <div className="min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium ${priority.className}`}>
                      {priority.label}
                    </span>
                    {insight.related_symbol && (
                      <span className="text-xs font-medium bg-muted px-1.5 py-0.5 rounded">
                        {insight.related_symbol}
                      </span>
                    )}
                    {insight.strategy_type && (
                      <span className="text-xs text-muted-foreground">
                        {insight.strategy_type.replace(/_/g, ' ')}
                      </span>
                    )}
                  </div>
                  <h4 className="font-medium text-sm">{insight.title}</h4>
                  {insight.description && (
                    <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                      {insight.description}
                    </p>
                  )}

                  {/* Signal badges */}
                  {insight.signals_triggered && insight.signals_triggered.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {insight.signals_triggered.map((signal: any, idx: number) => (
                        <span
                          key={idx}
                          className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] bg-muted text-muted-foreground"
                        >
                          {signal.signal}: {signal.value}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              <button
                onClick={() => handleDismiss(insight.id)}
                className="flex-shrink-0 text-muted-foreground hover:text-foreground transition-colors p-1"
                title="Dismiss"
              >
                x
              </button>
            </div>
          </div>
        )
      })}
    </div>
  )
}
