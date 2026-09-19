"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { formatCurrency } from "@/lib/utils";
import type { MealPlanMealResponse, MealOptionResponse } from "@/types/api";

interface MealCardProps {
  meal: MealPlanMealResponse;
  currency: string;
  mealTime?: string;
  onEat: (mealId: string, recipeId: string) => void;
  onChange: (meal: MealPlanMealResponse) => void;
  onCraving: (mealType: string) => void;
}

const MEAL_EMOJIS: Record<string, string> = {
  BREAKFAST: "🍳",
  LUNCH: "🍱",
  DINNER: "🍝",
};

const MEAL_TIMES: Record<string, string> = {
  BREAKFAST: "8:00 AM",
  LUNCH: "1:00 PM",
  DINNER: "7:30 PM",
};

export function MealCard({ meal, currency, mealTime, onEat, onChange, onCraving }: MealCardProps) {
  const [showWhy, setShowWhy] = useState(false);
  const selected = meal.options.find(o => o.recipe_id === meal.selected_recipe_id) || meal.options[0];
  if (!selected) return null;

  const recipe = selected.recipe;
  // Meal Fit: use actual score from recommendation engine (0-1 -> 0-100%)
  const mealFitPercent = Math.round((selected.score || 0) * 100);
  const fitColor = mealFitPercent >= 80 ? "text-green-600" : mealFitPercent >= 60 ? "text-yellow-600" : "text-orange-600";
  const fitBg = mealFitPercent >= 80 ? "bg-green-100" : mealFitPercent >= 60 ? "bg-yellow-100" : "bg-orange-100";

  return (
    <Card className="overflow-hidden flex flex-col">
      {/* Header: Meal Type + Time */}
      <div className="px-4 pt-3 pb-1 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-lg">{MEAL_EMOJIS[meal.meal_type] || "🍽️"}</span>
          <span className="text-sm font-semibold text-gray-700">{meal.meal_type}</span>
        </div>
        <span className="text-xs text-gray-400">{mealTime || MEAL_TIMES[meal.meal_type] || ""}</span>
      </div>

      {/* Recipe Image */}
      {recipe.image_url && (
        <div className="h-32 bg-gray-200 w-full overflow-hidden">
          <img src={recipe.image_url} alt={recipe.name} className="w-full h-full object-cover" />
        </div>
      )}

      <CardContent className="p-4 flex-1 flex flex-col">
        {/* Recipe Name + Meal Fit Badge */}
        <div className="flex items-start justify-between gap-2 mb-2">
          <h3 className="font-medium text-gray-900 line-clamp-2 flex-1">{recipe.name}</h3>
          <Badge variant="outline" className={`${fitBg} ${fitColor} border-0 text-xs font-bold shrink-0`}>
            {mealFitPercent}% fit
          </Badge>
        </div>

        {/* Nutrients Row */}
        <div className="text-xs text-gray-500 flex items-center gap-3 mb-2">
          <span>{recipe.calories} kcal</span>
          <span>{recipe.protein_g}g pro</span>
          <span>{recipe.carbs_g}g carb</span>
          <span>{recipe.fat_g}g fat</span>
        </div>

        {/* Cost + Prep Time */}
        <div className="text-xs text-gray-500 flex items-center justify-between mb-3">
          <span className="font-medium text-gray-700">{formatCurrency(recipe.estimated_cost || 0, currency)}</span>
          <span>{recipe.prep_time_min} min · {recipe.difficulty}</span>
        </div>

        {/* Meal Fit Progress Bar */}
        <Progress value={mealFitPercent} className={`h-1.5 ${fitBg} mb-2`} />

        {/* "Why this meal?" toggle */}
        <button
          className="text-xs text-orange-600 hover:text-orange-700 text-left mb-3"
          onClick={() => setShowWhy(!showWhy)}
        >
          {showWhy ? "▲ Hide details" : "▼ Why this meal?"}
        </button>

        {showWhy && (
          <div className="text-xs text-gray-500 bg-gray-50 rounded p-2 mb-3 space-y-1">
            <p>⭐ Score: {selected.score?.toFixed(2) || "N/A"} ({selected.option_type})</p>
            <p>🌾 {recipe.cuisines?.join(", ") || "Mixed cuisine"}</p>
            <p>🥗 {recipe.diet_compatibility?.join(", ") || ""}</p>
            {recipe.fiber_g > 0 && <p>🌿 Fiber: {recipe.fiber_g}g</p>}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-2 mt-auto">
          <Button
            className="flex-1 text-xs bg-orange-600 hover:bg-orange-700"
            onClick={() => onEat(meal.id, selected.recipe_id)}
          >
            ✅ Eat
          </Button>
          <Button
            variant="outline"
            className="flex-1 text-xs"
            onClick={() => onChange(meal)}
          >
            🔄 Change
          </Button>
          <Button
            variant="outline"
            className="text-xs px-2"
            onClick={() => onCraving(meal.meal_type)}
            title="I have a craving"
          >
            🍕
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
