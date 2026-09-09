"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

interface NutritionSummaryProps {
  calories: { current: number; target: number };
  protein: { current: number; target: number };
}

export function NutritionSummary({ calories, protein }: NutritionSummaryProps) {
  const calPercent = Math.min((calories.current / calories.target) * 100, 100) || 0;
  const proPercent = Math.min((protein.current / protein.target) * 100, 100) || 0;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">Daily Nutrition</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-1.5">
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Calories</span>
            <span className="font-medium">{calories.current} / {calories.target} kcal</span>
          </div>
          <Progress value={calPercent} className="h-2 bg-orange-100 [&>div]:bg-orange-500" />
        </div>
        <div className="space-y-1.5">
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Protein</span>
            <span className="font-medium">{protein.current} / {protein.target}g</span>
          </div>
          <Progress value={proPercent} className="h-2 bg-green-100 [&>div]:bg-green-500" />
        </div>
      </CardContent>
    </Card>
  );
}
