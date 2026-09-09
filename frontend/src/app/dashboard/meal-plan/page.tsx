"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api-client";
import { MealPlanResponse, MealPlanMealResponse } from "@/types/api";
import { DaySelector } from "@/features/meal-plan/components/day-selector";
import { MealOptions } from "@/features/meal-plan/components/meal-options";
import { ReplaceModal } from "@/features/meal-plan/components/replace-modal";
import { Button } from "@/components/ui/button";

export default function MealPlanPage() {
  const [plan, setPlan] = useState<MealPlanResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedDay, setSelectedDay] = useState(1);
  const [replaceMealId, setReplaceMealId] = useState<string | null>(null);
  const [isReplacing, setIsReplacing] = useState(false);

  const fetchPlan = async () => {
    try {
      setIsLoading(true);
      const data = await apiClient.get<MealPlanResponse>("/meal-plans/active");
      setPlan(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPlan();
  }, []);

  const handleGenerate = async () => {
    try {
      setIsLoading(true);
      const data = await apiClient.post<MealPlanResponse>("/meal-plans/generate", {});
      setPlan(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectOption = async (mealId: string, recipeId: string) => {
    try {
      setPlan((prev) => {
        if (!prev) return prev;
        const newMeals = prev.meals.map(m => 
          m.id === mealId ? { ...m, selected_recipe_id: recipeId } : m
        );
        return { ...prev, meals: newMeals };
      });
      await apiClient.post(\`/meal-plans/meals/\${mealId}/select\`, { recipe_id: recipeId });
    } catch (err) {
      console.error(err);
      fetchPlan();
    }
  };

  const handleReplaceSubmit = async (reason: string) => {
    if (!replaceMealId) return;
    try {
      setIsReplacing(true);
      const updatedMeal = await apiClient.post<MealPlanMealResponse>(\`/meal-plans/meals/\${replaceMealId}/replace\`, { reason });
      setPlan((prev) => {
        if (!prev) return prev;
        const newMeals = prev.meals.map(m => m.id === replaceMealId ? updatedMeal : m);
        return { ...prev, meals: newMeals };
      });
    } catch (err) {
      console.error(err);
    } finally {
      setIsReplacing(false);
      setReplaceMealId(null);
    }
  };

  if (isLoading && !plan) {
    return <div className="flex h-64 items-center justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600" /></div>;
  }

  if (!plan) {
    return (
      <div className="flex flex-col items-center justify-center h-full space-y-4 max-w-md mx-auto text-center py-20 animate-in fade-in">
        <h2 className="text-2xl font-bold">Plan Your Week</h2>
        <p className="text-gray-500">We'll create a custom meal plan based on your preferences, budget, and nutritional goals.</p>
        <Button onClick={handleGenerate} size="lg" className="w-full bg-orange-600 hover:bg-orange-700">
          Generate Weekly Plan
        </Button>
      </div>
    );
  }

  const dayMeals = plan.meals.filter(m => m.day_of_week === selectedDay);
  const currency = plan.cost_currency || "INR";

  return (
    <div className="space-y-6 pb-8 animate-in fade-in">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Weekly Meal Plan</h1>
        <Button variant="outline" size="sm" onClick={handleGenerate}>Regenerate</Button>
      </div>

      <DaySelector selectedDay={selectedDay} onSelect={setSelectedDay} />

      <div className="space-y-12 mt-6">
        {dayMeals.length === 0 ? (
          <div className="text-center py-12 text-gray-500">No meals planned for this day.</div>
        ) : (
          dayMeals.map((meal) => (
            <MealOptions 
              key={meal.id} 
              meal={meal} 
              currency={currency}
              onSelectOption={handleSelectOption}
              onReplaceClick={(m) => setReplaceMealId(m.id)}
            />
          ))
        )}
      </div>

      <ReplaceModal 
        isOpen={!!replaceMealId} 
        onClose={() => setReplaceMealId(null)}
        onReplace={handleReplaceSubmit}
        isLoading={isReplacing}
      />
    </div>
  );
}
