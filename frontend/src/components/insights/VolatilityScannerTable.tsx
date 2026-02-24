'use client'

import { useState } from 'react'
import { VolatilitySnapshot } from '@/lib/api'

interface VolatilityScannerTableProps {
  snapshots: VolatilitySnapshot[]
  formatPercent: (value: number) => string
  compact?: boolean
}

type SortField = 'symbol' | 'iv_rank' | 'iv_percentile' | 'current_iv' | 'hv_30'
type SortDir = 'asc' | 'desc'

function getIvrColor(ivr: number | null): string {
  if (ivr === null) return 'text-muted-foreground'
  if (ivr >= 70) return 'text-red-600 dark:text-red-400 font-semibold'
  if (ivr >= 50) return 'text-orange-600 dark:text-orange-400 font-medium'
  if (ivr <= 20) return 'text-green-600 dark:text-green-400'
  return ''
}

function getActionBadge(action: string): { label: string; className: string } {
  switch (action) {
    case 'sell_premium':
      return {
        label: 'SELL',
        className: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400',
      }
    case 'buy_premium':
      return {
        label: 'BUY',
        className: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
      }
    default:
      return {
        label: 'NEUTRAL',
        className: 'bg-gray-100 dark:bg-gray-900/30 text-gray-700 dark:text-gray-400',
      }
  }
}

export function VolatilityScannerTable({ snapshots, formatPercent, compact }: VolatilityScannerTableProps) {
  const [sortField, setSortField] = useState<SortField>('iv_rank')
  const [sortDir, setSortDir] = useState<SortDir>('desc')

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDir('desc')
    }
  }

  const sorted = [...snapshots].sort((a, b) => {
    const aVal = a[sortField] ?? 0
    const bVal = b[sortField] ?? 0
    if (typeof aVal === 'string' && typeof bVal === 'string') {
      return sortDir === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal)
    }
    return sortDir === 'asc' ? Number(aVal) - Number(bVal) : Number(bVal) - Number(aVal)
  })

  if (snapshots.length === 0) {
    return (
      <div className="bg-muted/50 rounded-lg p-6 text-center">
        <p className="text-muted-foreground">No volatility data available. Add symbols to your watchlist to scan.</p>
      </div>
    )
  }

  const SortHeader = ({ field, label }: { field: SortField; label: string }) => (
    <th
      onClick={() => handleSort(field)}
      className="px-3 py-2 text-left text-xs font-medium text-muted-foreground uppercase cursor-pointer hover:text-foreground transition-colors"
    >
      {label}
      {sortField === field && (
        <span className="ml-1">{sortDir === 'asc' ? '\u2191' : '\u2193'}</span>
      )}
    </th>
  )

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border">
            <SortHeader field="symbol" label="Symbol" />
            <SortHeader field="iv_rank" label="IV Rank" />
            <SortHeader field="iv_percentile" label="IV %ile" />
            <SortHeader field="current_iv" label="Current IV" />
            {!compact && <SortHeader field="hv_30" label="HV 30d" />}
            {!compact && <th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground uppercase">HV/IV</th>}
            <th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground uppercase">Action</th>
            {!compact && <th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground uppercase">Strategies</th>}
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {sorted.map((snap) => {
            const badge = getActionBadge(snap.strategy_recommendation?.action || 'neutral')
            return (
              <tr key={snap.symbol} className="hover:bg-muted/30 transition-colors">
                <td className="px-3 py-2.5 font-medium">{snap.symbol}</td>
                <td className={`px-3 py-2.5 ${getIvrColor(snap.iv_rank)}`}>
                  {snap.iv_rank != null ? `${snap.iv_rank.toFixed(1)}%` : '-'}
                </td>
                <td className="px-3 py-2.5">
                  {snap.iv_percentile != null ? `${snap.iv_percentile.toFixed(1)}%` : '-'}
                </td>
                <td className="px-3 py-2.5">
                  {snap.current_iv != null ? formatPercent(snap.current_iv * 100) : '-'}
                </td>
                {!compact && (
                  <td className="px-3 py-2.5">
                    {snap.hv_30 != null ? formatPercent(snap.hv_30 * 100) : '-'}
                  </td>
                )}
                {!compact && (
                  <td className="px-3 py-2.5">
                    {snap.hv_iv_ratio != null ? snap.hv_iv_ratio.toFixed(2) : '-'}
                  </td>
                )}
                <td className="px-3 py-2.5">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${badge.className}`}>
                    {badge.label}
                  </span>
                </td>
                {!compact && (
                  <td className="px-3 py-2.5 text-xs text-muted-foreground">
                    {snap.strategy_recommendation?.strategies?.slice(0, 2).join(', ') || '-'}
                  </td>
                )}
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
