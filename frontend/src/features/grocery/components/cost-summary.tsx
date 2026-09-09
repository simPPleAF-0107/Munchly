"use client";

import { Card, CardContent } from "@/components/ui/card";
import { formatCurrency, cn } from "@/lib/utils";

interface CostSummaryProps {
  consumed: number;
  shopping: number;
  remaining: number;
  budget: number;
  withinBudget: boolean;
  currency: string;
}

export function CostSummary({ consumed, shopping, remaining, budget, withinBudget, currency }: CostSummaryProps) {
  return (
    <Card className={cn("overflow-hidden border-2", withinBudget ? "border-green-100" : "border-red-100")}>
      <CardContent className="p-0">
        <div className="p-6 bg-gray-50 border-b flex justify-between items-center">
          <div>
            <div className="text-sm font-medium text-gray-500">Estimated Grocery Bill</div>
            <div className={cn("text-3xl font-bold mt-1", withinBudget ? "text-gray-900" : "text-red-600")}>
              {formatCurrency(shopping, currency)}
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm font-medium text-gray-500">Budget Limit</div>
            <div className="text-lg font-medium text-gray-900 flex items-center justify-end gap-2">
              {formatCurrency(budget, currency)}
              <span>{withinBudget ? "✅" : "❌"}</span>
            </div>
          </div>
        </div>
        
        <div className="grid grid-cols-2 divide-x">
          <div className="p-4 text-center">
            <div className="text-xs text-gray-500 mb-1">Consumed Food Cost</div>
            <div className="font-semibold">{formatCurrency(consumed, currency)}</div>
          </div>
          <div className="p-4 text-center">
            <div className="text-xs text-gray-500 mb-1">Leftover Value</div>
            <div className="font-semibold text-green-600">+{formatCurrency(remaining, currency)}</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
