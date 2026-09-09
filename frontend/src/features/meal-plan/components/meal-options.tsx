"use client";

import { Button } from "@/components/ui/button";
import { MealPlanMealResponse } from "@/types/api";
import { MealCard } from "./meal-card";
import { RefreshCw } from "lucide-react";

interface MealOptionsProps {
  meal: MealPlanMealResponse;
  currency: string;
  onSelectOption: (mealId: string, recipeId: string) => void;
  onReplaceClick: (meal: MealPlanMealResponse) => void;
}

export function MealOptions({ meal, currency, onSelectOption, onReplaceClick }: MealOptionsProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-lg text-gray-900 capitalize">{meal.meal_type.toLowerCase()}</h3>
        <Button 
          variant="ghost" 
          size="sm" 
          className="text-orange-600 hover:text-orange-700 hover:bg-orange-50"
          onClick={() => onReplaceClick(meal)}
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Replace Options
        </Button>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {meal.options.map((option) => (
          <MealCard
            key={option.recipe_id}
            recipe={option.recipe}
            optionType={option.option_type}
            currency={currency}
            isSelected={meal.selected_recipe_id === option.recipe_id}
            onSelect={() => onSelectOption(meal.id, option.recipe_id)}
          />
        ))}
      </div>
    </div>
  );
}
