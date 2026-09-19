"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import type { NutrientBar } from "@/types/dashboard";

interface NutrientCoverageProps {
  nutrients: NutrientBar[];
  suggestion?: string;
}

const STATUS_CONFIG = {
  good: { emoji: "🟢", color: "bg-green-500", trackColor: "bg-green-100" },
  warning: { emoji: "🟡", color: "bg-yellow-500", trackColor: "bg-yellow-100" },
  low: { emoji: "🔴", color: "bg-red-500", trackColor: "bg-red-100" },
  limited_data: { emoji: "⚪", color: "bg-gray-300", trackColor: "bg-gray-100" },
};

export function NutrientCoverage({ nutrients, suggestion }: NutrientCoverageProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">Your Nutrition</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {nutrients.map(n => {
          const config = STATUS_CONFIG[n.status];
          return (
            <div key={n.name} className="space-y-1">
              <div className="flex justify-between items-center text-sm">
                <span className="text-gray-600">
                  {config.emoji} {n.name}
                  {n.status === "limited_data" && (
                    <span className="text-xs text-gray-400 ml-1">— limited data</span>
                  )}
                </span>
                <span className="font-medium text-gray-800">
                  {n.status === "limited_data"
                    ? "—"
                    : `${Math.round(n.percent)}%`
                  }
                </span>
              </div>
              <Progress
                value={n.status === "limited_data" ? 0 : Math.min(n.percent, 100)}
                className={`h-1.5 ${config.trackColor}`}
              />
            </div>
          );
        })}

        {suggestion && (
          <div className="mt-3 p-2 bg-orange-50 rounded text-xs text-orange-800">
            💡 {suggestion}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
