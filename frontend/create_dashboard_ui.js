const fs = require('fs');
const path = require('path');

const files = {
  'd:/Projects/Munchly/frontend/src/app/dashboard/layout.tsx': `"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Calendar, ShoppingCart, User } from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { name: "Home", href: "/dashboard", icon: Home },
  { name: "Meal Plan", href: "/dashboard/meal-plan", icon: Calendar },
  { name: "Grocery", href: "/dashboard/grocery", icon: ShoppingCart },
  { name: "Profile", href: "/dashboard/profile", icon: User },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex h-screen bg-stone-50 overflow-hidden">
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex flex-col w-64 border-r bg-white p-4 shrink-0">
        <div className="text-2xl font-bold text-orange-600 mb-8 px-2">Munchly</div>
        <nav className="flex flex-col gap-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link key={item.name} href={item.href}>
                <div
                  className={cn(
                    "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors",
                    isActive ? "bg-orange-100 text-orange-700 font-medium" : "text-gray-600 hover:bg-orange-50 hover:text-orange-600"
                  )}
                >
                  <Icon className="w-5 h-5" />
                  {item.name}
                </div>
              </Link>
            );
          })}
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto pb-20 md:pb-0 relative">
        <div className="md:hidden flex items-center h-14 border-b bg-white px-4 sticky top-0 z-10">
          <div className="text-xl font-bold text-orange-600">Munchly</div>
        </div>
        <div className="p-4 md:p-8 max-w-5xl mx-auto h-full">
          {children}
        </div>
      </main>

      {/* Mobile Bottom Nav */}
      <nav className="md:hidden fixed bottom-0 w-full bg-white border-t flex justify-around p-2 pb-safe z-20">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          return (
            <Link key={item.name} href={item.href} className="w-full">
              <div
                className={cn(
                  "flex flex-col items-center gap-1 p-2 rounded-lg transition-colors",
                  isActive ? "text-orange-600" : "text-gray-500"
                )}
              >
                <Icon className={cn("w-6 h-6", isActive && "fill-orange-50 text-orange-600")} />
                <span className="text-[10px] font-medium">{item.name}</span>
              </div>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
`,

  'd:/Projects/Munchly/frontend/src/features/dashboard/components/greeting.tsx': `"use client";

import { useEffect, useState } from "react";

export function Greeting({ name }: { name: string }) {
  const [greeting, setGreeting] = useState("Good day");

  useEffect(() => {
    const hour = new Date().getHours();
    if (hour < 12) setGreeting("Good morning");
    else if (hour < 18) setGreeting("Good afternoon");
    else setGreeting("Good evening");
  }, []);

  return (
    <h1 className="text-2xl font-bold text-gray-900">
      {greeting}, {name}!
    </h1>
  );
}
`,

  'd:/Projects/Munchly/frontend/src/features/dashboard/components/nutrition-summary.tsx': `"use client";

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
`,

  'd:/Projects/Munchly/frontend/src/features/dashboard/components/daily-meals.tsx': `"use client";

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
`,

  'd:/Projects/Munchly/frontend/src/app/dashboard/page.tsx': `"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { format } from "date-fns";
import { apiClient } from "@/lib/api-client";
import { MealPlanResponse, UserResponse } from "@/types/api";
import { formatCurrency } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Greeting } from "@/features/dashboard/components/greeting";
import { NutritionSummary } from "@/features/dashboard/components/nutrition-summary";
import { DailyMeals } from "@/features/dashboard/components/daily-meals";

export default function DashboardHome() {
  const router = useRouter();
  const [user, setUser] = useState<UserResponse | null>(null);
  const [plan, setPlan] = useState<MealPlanResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [userData, planData] = await Promise.all([
          apiClient.get<UserResponse>("/auth/me").catch(() => null),
          apiClient.get<MealPlanResponse>("/meal-plans/active").catch(() => null),
        ]);
        if (userData) setUser(userData);
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
  const todayDayOfWeek = new Date().getDay() || 7; // 1-7 where 1 is Monday

  // Filter today's meals
  const todaysMeals = plan?.meals.filter(m => m.day_of_week === todayDayOfWeek) || [];

  // Calculate today's nutrition
  let todayCals = 0;
  let todayProtein = 0;
  
  todaysMeals.forEach(meal => {
    // For now assume all are consumed for demonstration, or we'd check status
    const selected = meal.options.find(o => o.recipe_id === meal.selected_recipe_id);
    if (selected) {
      todayCals += selected.recipe.calories_per_serving;
      todayProtein += selected.recipe.protein_g;
    }
  });

  const currency = user?.currency || plan?.cost_currency || "INR";

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <header>
        <Greeting name={user?.name || "User"} />
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
              calories={{ current: todayCals, target: user?.daily_calories_target || 2000 }} 
              protein={{ current: todayProtein, target: user?.daily_protein_target || 150 }} 
            />
            
            <Card>
              <CardContent className="p-6 flex flex-col justify-center h-full space-y-2">
                <div className="text-sm font-medium text-gray-500">Weekly Cost</div>
                <div className="text-3xl font-bold text-gray-900">
                  {formatCurrency(plan.total_consumed_cost || 0, currency)}
                  <span className="text-base font-normal text-gray-500 ml-2">
                    / {formatCurrency(user?.weekly_budget || 0, currency)} budget
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
`,

  'd:/Projects/Munchly/frontend/src/features/meal-plan/components/day-selector.tsx': `"use client";

import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

interface DaySelectorProps {
  selectedDay: number; // 1-7
  onSelect: (day: number) => void;
}

export function DaySelector({ selectedDay, onSelect }: DaySelectorProps) {
  return (
    <ScrollArea className="w-full whitespace-nowrap">
      <div className="flex w-max space-x-2 p-1">
        {DAYS.map((day, idx) => {
          const dayNum = idx + 1;
          const isSelected = selectedDay === dayNum;
          return (
            <button
              key={day}
              onClick={() => onSelect(dayNum)}
              className={cn(
                "px-4 py-2 rounded-full text-sm font-medium transition-colors",
                isSelected 
                  ? "bg-orange-600 text-white" 
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              )}
            >
              {day}
            </button>
          );
        })}
      </div>
      <ScrollBar orientation="horizontal" className="invisible" />
    </ScrollArea>
  );
}
`,

  'd:/Projects/Munchly/frontend/src/features/meal-plan/components/meal-card.tsx': `"use client";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { cn, formatCurrency } from "@/lib/utils";
import { RecipeResponse } from "@/types/api";
import { Clock, CheckCircle2 } from "lucide-react";

interface MealCardProps {
  recipe: RecipeResponse;
  optionType: string;
  currency: string;
  isSelected: boolean;
  onSelect: () => void;
}

const optionTypeConfig: Record<string, { label: string; color: string; icon: string }> = {
  BEST: { label: "Best Match", color: "bg-green-100 text-green-800", icon: "⭐" },
  BUDGET: { label: "Budget Friendly", color: "bg-blue-100 text-blue-800", icon: "💰" },
  VARIETY: { label: "Try Something New", color: "bg-purple-100 text-purple-800", icon: "🌟" },
};

export function MealCard({ recipe, optionType, currency, isSelected, onSelect }: MealCardProps) {
  const config = optionTypeConfig[optionType] || { label: optionType, color: "bg-gray-100 text-gray-800", icon: "✨" };

  return (
    <Card 
      onClick={onSelect}
      className={cn(
        "relative overflow-hidden cursor-pointer transition-all hover:shadow-md h-full flex flex-col",
        isSelected ? "ring-2 ring-orange-500 shadow-sm border-orange-200" : "border-gray-200"
      )}
    >
      {isSelected && (
        <div className="absolute top-2 right-2 z-10 bg-white rounded-full">
          <CheckCircle2 className="w-6 h-6 text-orange-500" />
        </div>
      )}
      
      {recipe.image_url && (
        <div className="h-32 w-full bg-gray-100 overflow-hidden shrink-0">
          <img src={recipe.image_url} alt={recipe.title} className="w-full h-full object-cover" />
        </div>
      )}
      
      <div className="p-4 flex-1 flex flex-col">
        <div className="mb-2">
          <Badge variant="secondary" className={cn("text-xs font-medium border-0", config.color)}>
            {config.icon} {config.label}
          </Badge>
        </div>
        
        <h4 className="font-semibold text-gray-900 leading-tight mb-2 line-clamp-2">{recipe.title}</h4>
        
        <div className="mt-auto space-y-3">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {recipe.prep_time_mins + recipe.cook_time_mins}m</span>
            <span>•</span>
            <span className="capitalize">{recipe.cuisine_type}</span>
          </div>
          
          <div className="flex items-center justify-between text-sm pt-3 border-t">
            <div className="text-gray-500">
              {recipe.calories_per_serving} kcal <span className="mx-1 text-gray-300">|</span> {recipe.protein_g}g pro
            </div>
            <div className="font-medium text-gray-900">
              {formatCurrency(recipe.estimated_cost || 0, currency)}
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}
`,

  'd:/Projects/Munchly/frontend/src/features/meal-plan/components/meal-options.tsx': `"use client";

import { Button } from "@/components/ui/button";
import { MealOptionResponse, MealPlanMealResponse } from "@/types/api";
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
`,

  'd:/Projects/Munchly/frontend/src/features/meal-plan/components/replace-modal.tsx': `"use client";

import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";

const REASONS = [
  "Don't like this recipe",
  "Too expensive",
  "Takes too long to cook",
  "Had this recently",
  "Want something healthier",
  "Want something different",
  "Use ingredients I already have"
];

interface ReplaceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onReplace: (reason: string) => Promise<void>;
  isLoading: boolean;
}

export function ReplaceModal({ isOpen, onClose, onReplace, isLoading }: ReplaceModalProps) {
  const [reason, setReason] = useState(REASONS[0]);

  const handleSubmit = async () => {
    await onReplace(reason);
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Replace Meal</DialogTitle>
          <DialogDescription>
            Help us understand why you want to replace this meal so we can suggest better options.
          </DialogDescription>
        </DialogHeader>
        
        <div className="py-4">
          <RadioGroup value={reason} onValueChange={setReason} className="gap-3">
            {REASONS.map((r) => (
              <div key={r} className="flex items-center space-x-2">
                <RadioGroupItem value={r} id={r} />
                <Label htmlFor={r} className="font-normal">{r}</Label>
              </div>
            ))}
          </RadioGroup>
        </div>
        
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isLoading}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={isLoading} className="bg-orange-600 hover:bg-orange-700">
            {isLoading ? "Replacing..." : "Get New Options"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
`,

  'd:/Projects/Munchly/frontend/src/app/dashboard/meal-plan/page.tsx': `"use client";

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
      // optimistic update
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
      fetchPlan(); // revert on fail
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
`,

  'd:/Projects/Munchly/frontend/src/features/grocery/components/cost-summary.tsx': `"use client";

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
`,

  'd:/Projects/Munchly/frontend/src/features/grocery/components/category-group.tsx': `"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { ShoppingListItemResponse } from "@/types/api";
import { formatCurrency, cn } from "@/lib/utils";

interface CategoryGroupProps {
  category: string;
  items: ShoppingListItemResponse[];
  currency: string;
}

export function CategoryGroup({ category, items, currency }: CategoryGroupProps) {
  const [isOpen, setIsOpen] = useState(true);
  const [checkedItems, setCheckedItems] = useState<Record<string, boolean>>(
    items.reduce((acc, item) => ({ ...acc, [item.id]: item.is_purchased }), {})
  );

  const toggleItem = (id: string) => {
    setCheckedItems(prev => ({ ...prev, [id]: !prev[id] }));
    // In a real app, this would call an API to sync the state
  };

  const allChecked = items.every(item => checkedItems[item.id]);

  return (
    <div className="border rounded-lg overflow-hidden bg-white">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 bg-gray-50/50 hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className="font-semibold text-gray-900">{category}</span>
          <span className="text-xs px-2 py-0.5 bg-gray-200 rounded-full text-gray-600">
            {items.filter(i => checkedItems[i.id]).length} / {items.length}
          </span>
        </div>
        {isOpen ? <ChevronUp className="w-5 h-5 text-gray-500" /> : <ChevronDown className="w-5 h-5 text-gray-500" />}
      </button>
      
      {isOpen && (
        <div className="divide-y">
          {items.map((item) => (
            <label 
              key={item.id} 
              className={cn(
                "flex items-center gap-3 p-4 cursor-pointer transition-colors hover:bg-orange-50/50",
                checkedItems[item.id] ? "opacity-60 bg-gray-50" : ""
              )}
            >
              <Checkbox 
                checked={checkedItems[item.id]} 
                onCheckedChange={() => toggleItem(item.id)}
                className="data-[state=checked]:bg-orange-500 data-[state=checked]:border-orange-500"
              />
              <div className="flex-1">
                <div className={cn("font-medium", checkedItems[item.id] && "line-through text-gray-500")}>
                  {item.food_name}
                </div>
                <div className="text-xs text-gray-500 flex gap-2">
                  <span>Need: {item.needed_quantity} {item.needed_unit}</span>
                  <span>•</span>
                  <span>Buy: {item.purchase_quantity} {item.purchase_unit}</span>
                </div>
              </div>
              <div className="font-medium text-sm text-gray-700">
                {formatCurrency(item.estimated_cost, currency)}
              </div>
            </label>
          ))}
        </div>
      )}
    </div>
  );
}
`,

  'd:/Projects/Munchly/frontend/src/features/grocery/components/grocery-list.tsx': `"use client";

import { ShoppingListResponse } from "@/types/api";
import { CostSummary } from "./cost-summary";
import { CategoryGroup } from "./category-group";
import { Button } from "@/components/ui/button";
import { Share2 } from "lucide-react";

interface GroceryListProps {
  list: ShoppingListResponse;
}

export function GroceryList({ list }: GroceryListProps) {
  const handleShare = () => {
    let text = \`Grocery List (Budget: \${list.cost_currency} \${list.weekly_grocery_limit})\\n\\n\`;
    Object.entries(list.items_by_category).forEach(([category, items]) => {
      text += \`== \${category} ==\\n\`;
      items.forEach(item => {
        text += \`- \${item.food_name}: \${item.purchase_quantity} \${item.purchase_unit}\\n\`;
      });
      text += \`\\n\`;
    });
    navigator.clipboard.writeText(text);
    alert("Copied to clipboard!");
  };

  const categories = Object.keys(list.items_by_category).sort();

  return (
    <div className="space-y-6">
      <CostSummary
        consumed={list.consumed_cost}
        shopping={list.actual_shopping_cost}
        remaining={list.remaining_inventory_value}
        budget={list.weekly_grocery_limit}
        withinBudget={list.within_budget}
        currency={list.cost_currency}
      />

      <div className="flex justify-end">
        <Button variant="outline" size="sm" onClick={handleShare}>
          <Share2 className="w-4 h-4 mr-2" /> Share List
        </Button>
      </div>

      <div className="space-y-4">
        {categories.map((category) => (
          <CategoryGroup
            key={category}
            category={category}
            items={list.items_by_category[category]}
            currency={list.cost_currency}
          />
        ))}
      </div>
    </div>
  );
}
`,

  'd:/Projects/Munchly/frontend/src/app/dashboard/grocery/page.tsx': `"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api-client";
import { ShoppingListResponse, MealPlanResponse } from "@/types/api";
import { GroceryList } from "@/features/grocery/components/grocery-list";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";

export default function GroceryPage() {
  const router = useRouter();
  const [list, setList] = useState<ShoppingListResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchList = async () => {
    try {
      setIsLoading(true);
      // First get active plan
      const plan = await apiClient.get<MealPlanResponse>("/meal-plans/active");
      if (plan) {
        const groceryData = await apiClient.get<ShoppingListResponse>(\`/grocery/\${plan.id}\`);
        setList(groceryData);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchList();
  }, []);

  if (isLoading && !list) {
    return <div className="flex h-64 items-center justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600" /></div>;
  }

  if (!list) {
    return (
      <div className="flex flex-col items-center justify-center h-full space-y-4 max-w-md mx-auto text-center py-20">
        <h2 className="text-xl font-semibold">No Grocery List</h2>
        <p className="text-gray-500">You need an active meal plan to generate a grocery list.</p>
        <Button onClick={() => router.push("/dashboard/meal-plan")} className="bg-orange-600 hover:bg-orange-700">
          Go to Meal Plan
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-8 animate-in fade-in">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Grocery List</h1>
        <Button variant="outline" size="sm" onClick={fetchList}>Regenerate</Button>
      </div>
      
      <GroceryList list={list} />
    </div>
  );
}
`,

  'd:/Projects/Munchly/frontend/src/app/dashboard/profile/page.tsx': `"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api-client";
import { UserResponse } from "@/types/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { User, Settings, CreditCard, LogOut } from "lucide-react";
import { useRouter } from "next/navigation";
import { formatCurrency } from "@/lib/utils";

export default function ProfilePage() {
  const router = useRouter();
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const userData = await apiClient.get<UserResponse>("/auth/me");
        setUser(userData);
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, []);

  const handleSignOut = () => {
    // In real app, call signOut() from NextAuth
    localStorage.removeItem("token");
    router.push("/");
  };

  if (isLoading) {
    return <div className="flex h-64 items-center justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600" /></div>;
  }

  if (!user) return null;

  return (
    <div className="space-y-6 max-w-2xl mx-auto pb-8 animate-in fade-in">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Profile Settings</h1>
      
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center text-orange-600">
              <User className="w-8 h-8" />
            </div>
            <div className="flex-1">
              <h2 className="text-xl font-bold">{user.name || "User"}</h2>
              <p className="text-gray-500">{user.email}</p>
            </div>
            <Badge variant="secondary" className="bg-gradient-to-r from-orange-400 to-orange-600 text-white border-0">
              {user.subscription_tier || "Free Plan"}
            </Badge>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Settings className="w-5 h-5 text-gray-500" />
              Preferences
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="text-sm text-gray-500">Diet Type</div>
              <div className="font-medium capitalize">{user.diet_type || "No restriction"}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Cuisines</div>
              <div className="font-medium flex flex-wrap gap-1 mt-1">
                {(user.cuisines?.length ? user.cuisines : ["Any"]).map(c => (
                  <Badge key={c} variant="outline" className="capitalize">{c}</Badge>
                ))}
              </div>
            </div>
            <Button variant="outline" className="w-full mt-2" onClick={() => router.push("/onboarding")}>
              Update Preferences
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <CreditCard className="w-5 h-5 text-gray-500" />
              Budget & Goals
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="text-sm text-gray-500">Weekly Budget</div>
              <div className="font-medium">{formatCurrency(user.weekly_budget || 0, user.currency || "INR")}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Daily Targets</div>
              <div className="font-medium">
                {user.daily_calories_target || 2000} kcal • {user.daily_protein_target || 150}g protein
              </div>
            </div>
            <Button variant="outline" className="w-full mt-2">
              Edit Budget
            </Button>
          </CardContent>
        </Card>
      </div>

      <div className="pt-6 border-t flex justify-center">
        <Button variant="ghost" className="text-red-600 hover:text-red-700 hover:bg-red-50" onClick={handleSignOut}>
          <LogOut className="w-4 h-4 mr-2" />
          Sign Out
        </Button>
      </div>
    </div>
  );
}
`
};

for (const [filepath, content] of Object.entries(files)) {
  fs.mkdirSync(path.dirname(filepath), { recursive: true });
  fs.writeFileSync(filepath, content);
  console.log('Created:', filepath);
}
