"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { format } from "date-fns";
import { apiClient } from "@/lib/api-client";
import { MealPlanResponse, UserResponse } from "@/types/api";
import { UserProfile } from "@/types";
import { formatCurrency } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Greeting } from "@/features/dashboard/components/greeting";
import { NutritionSummary } from "@/features/dashboard/components/nutrition-summary";
import { DailyMeals } from "@/features/dashboard/components/daily-meals";

export default function DashboardHome() {
  const router = useRouter();
  const [user, setUser] = useState<UserResponse | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [plan, setPlan] = useState<MealPlanResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [userData, profileData, planData] = await Promise.all([
          apiClient.get<UserResponse>("/auth/me").catch(() => null),
          apiClient.get<UserProfile>("/users/profile").catch(() => null),
          apiClient.get<MealPlanResponse>("/meal-plans/active").catch(() => null),
        ]);
        if (userData) setUser(userData);
        if (profileData) setProfile(profileData);
        if (planData) setPlan(planData);
      } catch (err) {
        console.error("Failed to load dashboard data", err);
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, []);

  if (isLoading) {
    return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600" /></div>;
  }

  const todayStr = format(new Date(), "EEEE, MMMM d");
  const todayDayOfWeek = new Date().getDay() || 7;

  const todaysMeals = plan?.meals.filter(m => m.day_of_week === todayDayOfWeek) || [];

  let todayCals = 0;
  let todayProtein = 0;
  
  todaysMeals.forEach(meal => {
    const selected = meal.options.find(o => o.recipe_id === meal.selected_recipe_id) || meal.options[0];
    if (selected) {
      todayCals += selected.recipe.calories;
      todayProtein += selected.recipe.protein_g;
    }
  });

  const currency = plan?.cost_currency || profile?.weekly_grocery_limit_currency || "INR";

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <header>
        <Greeting name={profile?.name || "User"} />
        <p className="text-gray-500">{todayStr}</p>
      </header>

      {!plan ? (
        <Card className="bg-orange-50 border-orange-100">
          <CardContent className="p-6 text-center space-y-4">
            <h3 className="font-semibold text-lg text-orange-900">No active meal plan</h3>
            <p className="text-orange-700/80">Generate a personalized meal plan to get started.</p>
            <Button onClick={() => router.push("/dashboard/meal-plan")} className="bg-orange-600 hover:bg-orange-700">
              Generate Plan
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="grid gap-4 md:grid-cols-2">
            <NutritionSummary 
              calories={{ current: todayCals, target: 2000 }} 
              protein={{ current: todayProtein, target: 150 }} 
            />
            
            <Card>
              <CardContent className="p-6 flex flex-col justify-center h-full space-y-2">
                <div className="text-sm font-medium text-gray-500">Weekly Cost</div>
                <div className="text-3xl font-bold text-gray-900">
                  {formatCurrency(plan.total_consumed_cost || 0, currency)}
                  <span className="text-base font-normal text-gray-500 ml-2">
                    / {formatCurrency(profile?.weekly_grocery_limit || 0, currency)} budget
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>

          <DailyMeals 
            meals={todaysMeals} 
            currency={currency} 
            onReplaceClick={() => router.push("/dashboard/meal-plan")} 
          />
        </>
      )}
    </div>
  );
}

