"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { formatCurrency } from "@/lib/utils";
import { MealPlanMealResponse, MealOptionResponse } from "@/types/api";

interface DailyMealsProps {
  meals: MealPlanMealResponse[];
  currency: string;
  onReplaceClick: (meal: MealPlanMealResponse) => void;
}

export function DailyMeals({ meals, currency, onReplaceClick }: DailyMealsProps) {
  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">Today's Meals</h2>
      {meals.length === 0 ? (
        <Card className="p-6 text-center text-gray-500 bg-gray-50 border-dashed">
          No meals planned for today.
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-3">
          {meals.map((meal) => {
            const selectedOption = meal.options.find((o) => o.recipe_id === meal.selected_recipe_id) || meal.options[0];
            if (!selectedOption) return null;

            return (
              <Card key={meal.id} className="overflow-hidden flex flex-col">
                {selectedOption.recipe.image_url && (
                  <div className="h-32 bg-gray-200 w-full overflow-hidden">
                    <img 
                      src={selectedOption.recipe.image_url} 
                      alt={selectedOption.recipe.title} 
                      className="w-full h-full object-cover"
                    />
                  </div>
                )}
                <CardContent className="p-4 flex-1 flex flex-col">
                  <div className="text-xs font-semibold text-orange-600 mb-1">{meal.meal_type}</div>
                  <h3 className="font-medium text-gray-900 line-clamp-2 mb-2 flex-1">
                    {selectedOption.recipe.title}
                  </h3>
                  
                  <div className="text-sm text-gray-500 flex items-center justify-between mt-auto pt-2 border-t">
                    <span>{selectedOption.recipe.calories_per_serving} kcal</span>
                    <span>{selectedOption.recipe.protein_g}g pro</span>
                    <span className="font-medium text-gray-900">
                      {formatCurrency(selectedOption.recipe.estimated_cost || 0, currency)}
                    </span>
                  </div>
                  
                  <div className="flex gap-2 mt-4">
                    <Button 
                      variant="outline" 
                      className="w-full text-xs" 
                      onClick={() => onReplaceClick(meal)}
                    >
                      Replace
                    </Button>
                    <Button className="w-full text-xs bg-orange-600 hover:bg-orange-700">
                      Eat
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
