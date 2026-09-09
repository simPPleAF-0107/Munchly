"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useOnboardingStore } from "@/features/onboarding/store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Search } from "lucide-react";
import { apiClient } from "@/lib/api-client";

// Mock data to use if API fails or for offline dev
const MOCK_FOODS = [
  { id: "1", name: "Broccoli", category: "Vegetables" },
  { id: "2", name: "Chicken Breast", category: "Meats" },
  { id: "3", name: "Tofu", category: "Proteins" },
  { id: "4", name: "Quinoa", category: "Grains" },
  { id: "5", name: "Avocado", category: "Fats" },
  { id: "6", name: "Mushrooms", category: "Vegetables" },
  { id: "7", name: "Salmon", category: "Seafood" },
  { id: "8", name: "Coriander", category: "Herbs" },
];

export default function FoodPreferencesPage() {
  const router = useRouter();
  const { foodPreferences, setFoodPreferences } = useOnboardingStore();
  const [prefs, setPrefs] = useState<Record<string, string>>({});
  const [query, setQuery] = useState("");
  const [foods, setFoods] = useState<any[]>(MOCK_FOODS);

  useEffect(() => {
    const map: Record<string, string> = {};
    foodPreferences.forEach(fp => { map[fp.food_id] = fp.preference; });
    setPrefs(map);
  }, [foodPreferences]);

  useEffect(() => {
    const fetchFoods = async () => {
      try {
        const res = await apiClient.get<{foods: any[]}>(`/onboarding/foods?q=${query}&limit=20`);
        if (res?.foods) setFoods(res.foods);
      } catch (err) {
        // Fallback to mock filtering
        setFoods(MOCK_FOODS.filter(f => f.name.toLowerCase().includes(query.toLowerCase())));
      }
    };
    const timer = setTimeout(fetchFoods, 300);
    return () => clearTimeout(timer);
  }, [query]);

  const setPref = (foodId: string, pref: string) => {
    setPrefs(prev => ({ ...prev, [foodId]: pref }));
  };

  const onSubmit = () => {
    const arr = Object.entries(prefs).map(([food_id, preference]) => ({ food_id, preference }));
    setFoodPreferences(arr);
    router.push("/onboarding/cuisine");
  };

  return (
    <div className="space-y-8 animate-in slide-in-from-right-8 fade-in duration-500">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">Food Preferences</h1>
        <p className="text-muted-foreground">Tell us what you love and what you absolutely hate.</p>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground w-5 h-5" />
        <Input 
          placeholder="Search foods (e.g. mushrooms, cilantro)..." 
          className="pl-10 text-lg py-6"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      <div className="space-y-4 max-h-[50vh] overflow-y-auto pr-2">
        {foods.map(food => (
          <Card key={food.id}>
            <CardContent className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <div className="font-semibold">{food.name}</div>
                <div className="text-xs text-muted-foreground">{food.category}</div>
              </div>
              <div className="flex bg-muted/50 rounded-lg p-1">
                <button 
                  onClick={() => setPref(food.id, "like")}
                  className={`px-4 py-2 rounded-md text-sm transition-colors ${prefs[food.id] === "like" ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 font-medium shadow-sm" : "hover:bg-muted"}`}
                >
                  ❤️ Love
                </button>
                <button 
                  onClick={() => setPref(food.id, "neutral")}
                  className={`px-4 py-2 rounded-md text-sm transition-colors ${prefs[food.id] === "neutral" ? "bg-background font-medium shadow-sm" : "hover:bg-muted"}`}
                >
                  😐 Neutral
                </button>
                <button 
                  onClick={() => setPref(food.id, "dislike")}
                  className={`px-4 py-2 rounded-md text-sm transition-colors ${prefs[food.id] === "dislike" ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 font-medium shadow-sm" : "hover:bg-muted"}`}
                >
                  🚫 Never
                </button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="pt-6">
        <Button onClick={onSubmit} size="lg" className="w-full text-lg">Continue</Button>
      </div>
    </div>
  );
}
