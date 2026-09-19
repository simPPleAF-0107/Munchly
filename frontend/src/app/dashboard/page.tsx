"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { format } from "date-fns";
import { apiClient } from "@/lib/api-client";
import { MealPlanResponse, UserResponse, MealPlanMealResponse } from "@/types/api";
import { UserProfile } from "@/types";
import type { DailyContextResponse, BehavioralInsight, NutrientBar } from "@/types/dashboard";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Greeting } from "@/features/dashboard/components/greeting";
import { CheckInModal } from "@/features/dashboard/components/check-in-modal";
import { MealCard } from "@/features/dashboard/components/meal-card";
import { NutrientCoverage } from "@/features/dashboard/components/nutrient-coverage";
import { InsightsCard } from "@/features/dashboard/components/insights-card";
import { KitchenPantry } from "@/features/dashboard/components/kitchen-pantry";
import { TreatBudget } from "@/features/dashboard/components/treat-budget";
import { WeekOverview } from "@/features/dashboard/components/week-overview";

export default function DashboardHome() {
  const router = useRouter();
  const [user, setUser] = useState<UserResponse | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [plan, setPlan] = useState<MealPlanResponse | null>(null);
  const [dailyCtx, setDailyCtx] = useState<DailyContextResponse | null>(null);
  const [insights, setInsights] = useState<BehavioralInsight[]>([]);
  const [showCheckIn, setShowCheckIn] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [userData, profileData, planData, dailyData, insightData] =
          await Promise.all([
            apiClient.get<UserResponse>("/auth/me").catch(() => null),
            apiClient.get<UserProfile>("/users/profile").catch(() => null),
            apiClient.get<MealPlanResponse>("/meal-plans/active").catch(() => null),
            apiClient.get<DailyContextResponse>("/daily/today").catch(() => null),
            apiClient.get<BehavioralInsight[]>("/behavioral/insights?status=PENDING").catch(() => []),
          ]);
        if (userData) setUser(userData);
        if (profileData) setProfile(profileData);
        if (planData) setPlan(planData);
        if (dailyData) setDailyCtx(dailyData);
        if (insightData) setInsights(insightData);

        // Show check-in modal if today's context is PENDING
        if (dailyData && dailyData.status === "PENDING") {
          setShowCheckIn(true);
        }
      } catch (err) {
        console.error("Failed to load dashboard data", err);
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, []);

  const handleCheckInComplete = useCallback((ctx: DailyContextResponse) => {
    setDailyCtx(ctx);
    setShowCheckIn(false);
  }, []);

  const handleEat = useCallback(async (mealId: string, recipeId: string) => {
    try {
      await apiClient.post(`/meal-plans/meals/${mealId}/action`, { action: "EAT" });
    } catch (err) {
      console.error("Failed to record eat action", err);
    }
  }, []);

  const handleChange = useCallback((meal: MealPlanMealResponse) => {
    router.push("/dashboard/meal-plan");
  }, [router]);

  const handleCraving = useCallback(async (mealType: string) => {
    // Navigate to meal plan page for craving override
    router.push("/dashboard/meal-plan");
  }, [router]);

  const handleInsightAction = useCallback(async (id: string, action: "ACCEPT" | "DISMISS") => {
    try {
      await apiClient.post(`/behavioral/insights/${id}/action`, { action });
      setInsights(prev => prev.filter(i => i.id !== id));
    } catch (err) {
      console.error("Failed to process insight", err);
    }
  }, []);

  const handleUpdatePantry = useCallback(() => {
    // Navigate to pantry management
    router.push("/dashboard/grocery");
  }, [router]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600" />
      </div>
    );
  }

  const todayStr = format(new Date(), "EEEE, MMMM d");
  const todayDayOfWeek = new Date().getDay() || 7;
  const todaysMeals = plan?.meals.filter(m => m.day_of_week === todayDayOfWeek) || [];
  const currency = plan?.cost_currency || profile?.weekly_grocery_limit_currency || "INR";

  // Compute today's nutrition from selected meals (using real recipe data)
  let todayCals = 0;
  let todayProtein = 0;
  let todayCarbs = 0;
  let todayFat = 0;
  let todayFiber = 0;

  todaysMeals.forEach(meal => {
    const selected = meal.options.find(o => o.recipe_id === meal.selected_recipe_id) || meal.options[0];
    if (selected) {
      todayCals += selected.recipe.calories;
      todayProtein += selected.recipe.protein_g;
      todayCarbs += selected.recipe.carbs_g;
      todayFat += selected.recipe.fat_g;
      todayFiber += selected.recipe.fiber_g;
    }
  });

  // Build nutrient bars from actual recipe data
  // Targets come from profile or use safe defaults until NutrientProfileService is wired
  const calTarget = dailyCtx?.adjusted_calorie_target || 2000;
  const proTarget = Math.round(calTarget * 0.25 / 4); // 25% of cals from protein
  const carbTarget = Math.round(calTarget * 0.50 / 4); // 50% of cals from carbs
  const fatTarget = Math.round(calTarget * 0.25 / 9);  // 25% of cals from fat

  const makeBar = (name: string, current: number, target: number, unit: string): NutrientBar => {
    const percent = target > 0 ? (current / target) * 100 : 0;
    const status: NutrientBar["status"] =
      percent >= 80 ? "good" : percent >= 50 ? "warning" : percent > 0 ? "low" : "limited_data";
    return { name, current: Math.round(current), target, unit, percent, status };
  };

  const nutrients: NutrientBar[] = [
    makeBar("Calories", todayCals, calTarget, "kcal"),
    makeBar("Protein", todayProtein, proTarget, "g"),
    makeBar("Carbs", todayCarbs, carbTarget, "g"),
    makeBar("Fat", todayFat, fatTarget, "g"),
    makeBar("Fiber", todayFiber, 25, "g"),
  ];

  // Nutrition suggestion based on lowest nutrient
  const lowest = [...nutrients].sort((a, b) => a.percent - b.percent)[0];
  const suggestion = lowest && lowest.percent < 60
    ? `${lowest.name} is low today \u2014 Munchly prioritized ${lowest.name.toLowerCase()}-rich options for remaining meals.`
    : undefined;

  // Treat budget: 10% above daily target as treat allowance
  const treatAllowance = Math.round(calTarget * 0.10);

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Check-in Modal */}
      <CheckInModal
        open={showCheckIn}
        onClose={() => setShowCheckIn(false)}
        onComplete={handleCheckInComplete}
      />

      {/* Header: TODAY */}
      <header className="flex items-center justify-between">
        <div>
          <Greeting name={profile?.name || "User"} />
          <p className="text-gray-500">{todayStr}</p>
          {dailyCtx && dailyCtx.status === "COMPLETED" && dailyCtx.food_mood && (
            <p className="text-xs text-orange-600 mt-1">
              Today's mood: {dailyCtx.food_mood.toLowerCase()} \u00b7 {dailyCtx.workout_today ? "Workout day \ud83d\udcaa" : "Rest day"}
            </p>
          )}
        </div>
        {dailyCtx?.status !== "COMPLETED" && (
          <Button
            variant="outline"
            size="sm"
            className="text-xs"
            onClick={() => setShowCheckIn(true)}
          >
            \ud83c\udf1e Check in
          </Button>
        )}
      </header>

      {/* Behavioral Insights */}
      <InsightsCard insights={insights} onAction={handleInsightAction} />

      {!plan ? (
        <Card className="bg-orange-50 border-orange-100">
          <CardContent className="p-6 text-center space-y-4">
            <h3 className="font-semibold text-lg text-orange-900">No active meal plan</h3>
            <p className="text-orange-700/80">Generate a personalized meal plan to get started.</p>
            <Button
              onClick={() => router.push("/dashboard/meal-plan")}
              className="bg-orange-600 hover:bg-orange-700"
            >
              Generate Plan
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* YOUR MEALS */}
          <section>
            <h2 className="text-xl font-semibold mb-4">Your Meals</h2>
            {todaysMeals.length === 0 ? (
              <Card className="p-6 text-center text-gray-500 bg-gray-50 border-dashed">
                No meals planned for today.
              </Card>
            ) : (
              <div className="grid gap-4 md:grid-cols-3">
                {todaysMeals.map(meal => (
                  <MealCard
                    key={meal.id}
                    meal={meal}
                    currency={currency}
                    onEat={handleEat}
                    onChange={handleChange}
                    onCraving={handleCraving}
                  />
                ))}
              </div>
            )}
          </section>

          {/* YOUR NUTRITION */}
          <section className="grid gap-4 md:grid-cols-2">
            <NutrientCoverage nutrients={nutrients} suggestion={suggestion} />
            <TreatBudget
              caloriesConsumed={todayCals}
              caloriesTarget={calTarget}
              treatAllowance={treatAllowance}
            />
          </section>

          {/* YOUR KITCHEN */}
          <KitchenPantry
            pantryFoodIds={dailyCtx?.pantry_food_ids || null}
            onUpdatePantry={handleUpdatePantry}
          />

          {/* YOUR WEEK (collapsed by default) */}
          <WeekOverview
            meals={plan.meals}
            currency={currency}
            todayDow={todayDayOfWeek}
          />
        </>
      )}
    </div>
  );
}
