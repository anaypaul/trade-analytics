'use client'

import { EarningsEvent } from '@/lib/api'

interface EarningsCalendarWidgetProps {
  earnings: EarningsEvent[]
}

export function EarningsCalendarWidget({ earnings }: EarningsCalendarWidgetProps) {
  if (earnings.length === 0) return null

  return (
    <div>
      <h3 className="text-lg font-medium mb-3">Upcoming Earnings</h3>
      <p className="text-sm text-muted-foreground mb-3">
        Watch for IV crush opportunities — sell premium before earnings
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
        {earnings.map((event, idx) => (
          <div
            key={`${event.symbol}-${idx}`}
            className="flex items-center justify-between border border-border rounded-lg px-3 py-2"
          >
            <div>
              <span className="font-medium text-sm">{event.symbol}</span>
              <span className="text-xs text-muted-foreground ml-2">
                {event.time === 'pre_market' ? 'Pre-Mkt' : event.time === 'post_market' ? 'Post-Mkt' : ''}
              </span>
            </div>
            <span className="text-xs text-muted-foreground">{event.date}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
