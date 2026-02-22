"use client"

import { Stock } from "@/types/stock"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

interface StockCardProps {
  stock: Stock
  onSelect?: (symbol: string) => void
}

export function StockCard({ stock, onSelect }: StockCardProps) {
  return (
    <Card
      className={onSelect ? "cursor-pointer hover:shadow-lg transition-shadow" : ""}
      onClick={() => onSelect?.(stock.symbol)}
    >
      <CardHeader>
        <CardTitle className="text-xl">{stock.symbol}</CardTitle>
        <CardDescription>{stock.name}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex justify-between">
            <span className="text-sm text-muted-foreground">Exchange:</span>
            <span className="text-sm font-medium">{stock.exchange}</span>
          </div>
          {stock.sector && (
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Sector:</span>
              <span className="text-sm font-medium">{stock.sector}</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
