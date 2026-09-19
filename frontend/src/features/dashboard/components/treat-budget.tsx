"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

interface TreatBudgetProps {
  caloriesConsumed: number;
  caloriesTarget: number;
  treatAllowance: number; // Extra calories available for treats
}

export function TreatBudget({ caloriesConsumed, caloriesTarget, treatAllowance }: TreatBudgetProps) {
  const basePercent = Math.min((caloriesConsumed / caloriesTarget) * 100, 100);
  const remaining = Math.max(caloriesTarget - caloriesConsumed, 0);

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">🍰 Weekly Nutrition Budget</span>
          <span className="text-xs text-gray-500">
            {remaining > 0
              ? `${remaining} kcal remaining`
              : "Target reached"}
          </span>
        </div>
        <Progress value={basePercent} className="h-2 bg-gray-100" />
        {treatAllowance > 0 && (
          <p className="text-xs text-gray-400 mt-1">
            🌟 Treat allowance: +{treatAllowance} kcal available
          </p>
        )}
      </CardContent>
    </Card>
  );
}
