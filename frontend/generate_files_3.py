import os

base_dir = r"d:\Projects\Munchly\frontend"

def write_file(path, content):
    full_path = os.path.join(base_dir, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

# 16. app/onboarding/allergies/page.tsx
write_file("src/app/onboarding/allergies/page.tsx", """
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useOnboardingStore } from "@/features/onboarding/store";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { ALLERGENS } from "@/lib/constants";
import { Plus, X } from "lucide-react";

export default function AllergiesPage() {
  const router = useRouter();
  const { allergies, setAllergies } = useOnboardingStore();
  
  const [selected, setSelected] = useState<string[]>(allergies.filter(a => !a.custom_allergen).map(a => a.allergen));
  const [customs, setCustoms] = useState<string[]>(allergies.filter(a => a.custom_allergen).map(a => a.allergen));
  const [newCustom, setNewCustom] = useState("");

  const toggle = (allergen: string) => {
    if (allergen === "None") {
      setSelected(["None"]);
      setCustoms([]);
      return;
    }
    const filtered = selected.filter(a => a !== "None");
    if (filtered.includes(allergen)) {
      setSelected(filtered.filter(a => a !== allergen));
    } else {
      setSelected([...filtered, allergen]);
    }
  };

  const addCustom = () => {
    if (newCustom.trim() && !customs.includes(newCustom.trim())) {
      setCustoms([...customs, newCustom.trim()]);
      setSelected(selected.filter(a => a !== "None"));
      setNewCustom("");
    }
  };

  const removeCustom = (c: string) => {
    setCustoms(customs.filter(x => x !== c));
  };

  const onSubmit = () => {
    const combined = [
      ...selected.filter(a => a !== "None").map(a => ({ allergen: a })),
      ...customs.map(c => ({ allergen: c, custom_allergen: "true" }))
    ];
    setAllergies(combined);
    router.push("/onboarding/restrictions");
  };

  return (
    <div className="space-y-8 animate-in slide-in-from-right-8 fade-in duration-500">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">Do you have any allergies?</h1>
        <p className="text-muted-foreground">Select common allergens or add your own.</p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <div className="flex items-center space-x-3 border rounded-lg p-4 cursor-pointer hover:bg-muted/50">
          <Checkbox id="alg-none" checked={selected.includes("None")} onCheckedChange={() => toggle("None")} />
          <Label htmlFor="alg-none" className="flex-1 cursor-pointer font-medium">None</Label>
        </div>
        {ALLERGENS.map((a) => (
          <div key={a} className="flex items-center space-x-3 border rounded-lg p-4 cursor-pointer hover:bg-muted/50">
            <Checkbox id={`alg-${a}`} checked={selected.includes(a)} onCheckedChange={() => toggle(a)} />
            <Label htmlFor={`alg-${a}`} className="flex-1 cursor-pointer font-medium">{a}</Label>
          </div>
        ))}
      </div>

      <div className="space-y-4 pt-4">
        <Label>Other Allergies</Label>
        <div className="flex gap-2">
          <Input 
            placeholder="Type an allergy..." 
            value={newCustom} 
            onChange={(e) => setNewCustom(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addCustom())}
          />
          <Button type="button" onClick={addCustom} variant="secondary">
            <Plus className="w-4 h-4 mr-2" /> Add
          </Button>
        </div>
        
        {customs.length > 0 && (
          <div className="flex flex-wrap gap-2 pt-2">
            {customs.map(c => (
              <div key={c} className="flex items-center bg-secondary text-secondary-foreground px-3 py-1.5 rounded-full text-sm">
                <span>{c}</span>
                <button onClick={() => removeCustom(c)} className="ml-2 text-muted-foreground hover:text-foreground">
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="pt-6">
        <Button onClick={onSubmit} size="lg" className="w-full text-lg">Continue</Button>
      </div>
    </div>
  );
}
""")

# 17. app/onboarding/restrictions/page.tsx
write_file("src/app/onboarding/restrictions/page.tsx", """
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useOnboardingStore } from "@/features/onboarding/store";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { DIETARY_RESTRICTIONS } from "@/lib/constants";

export default function RestrictionsPage() {
  const router = useRouter();
  const { restrictions, setRestrictions } = useOnboardingStore();
  const [selected, setSelected] = useState<string[]>(restrictions);

  const toggle = (res: string) => {
    if (res === "None") {
      setSelected(["None"]);
      return;
    }
    const filtered = selected.filter(a => a !== "None");
    if (filtered.includes(res)) {
      setSelected(filtered.filter(a => a !== res));
    } else {
      setSelected([...filtered, res]);
    }
  };

  const onSubmit = () => {
    setRestrictions(selected.filter(a => a !== "None"));
    router.push("/onboarding/food-preferences");
  };

  return (
    <div className="space-y-8 animate-in slide-in-from-right-8 fade-in duration-500">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">Dietary Restrictions</h1>
        <p className="text-muted-foreground">Any specific restrictions we should know about?</p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="flex items-center space-x-3 border rounded-lg p-4 cursor-pointer hover:bg-muted/50">
          <Checkbox id="res-none" checked={selected.includes("None")} onCheckedChange={() => toggle("None")} />
          <Label htmlFor="res-none" className="flex-1 cursor-pointer font-medium">None</Label>
        </div>
        {DIETARY_RESTRICTIONS.map((res) => (
          <div key={res} className="flex items-center space-x-3 border rounded-lg p-4 cursor-pointer hover:bg-muted/50">
            <Checkbox id={`res-${res}`} checked={selected.includes(res)} onCheckedChange={() => toggle(res)} />
            <Label htmlFor={`res-${res}`} className="flex-1 cursor-pointer font-medium">{res}</Label>
          </div>
        ))}
      </div>

      <div className="pt-6">
        <Button onClick={onSubmit} size="lg" className="w-full text-lg">Continue</Button>
      </div>
    </div>
  );
}
""")

# 18. app/onboarding/food-preferences/page.tsx
write_file("src/app/onboarding/food-preferences/page.tsx", """
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
""")

# 19. app/onboarding/cuisine/page.tsx
write_file("src/app/onboarding/cuisine/page.tsx", """
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useOnboardingStore } from "@/features/onboarding/store";
import { Button } from "@/components/ui/button";
import { CUISINES } from "@/lib/constants";

export default function CuisinePage() {
  const router = useRouter();
  const { cuisinePreferences, setCuisinePreferences } = useOnboardingStore();
  
  // Maps cuisine name -> tier (1: Love, 2: Like, 3: Neutral)
  const [prefs, setPrefs] = useState<Record<string, number>>(() => {
    const map: Record<string, number> = {};
    CUISINES.forEach(c => { map[c.name] = 3; });
    cuisinePreferences.forEach(cp => {
      if (cp.preference_strength > 0.8) map[cp.cuisine] = 1;
      else if (cp.preference_strength > 0.5) map[cp.cuisine] = 2;
    });
    return map;
  });

  const toggleTier = (cuisine: string, tier: number) => {
    setPrefs(prev => ({ ...prev, [cuisine]: tier }));
  };

  const onSubmit = () => {
    const arr = Object.entries(prefs).map(([cuisine, tier]) => {
      let strength = 0.3; // Default neutral
      if (tier === 1) strength = 1.0;
      if (tier === 2) strength = 0.7;
      return { cuisine, preference_strength: strength };
    });
    // Ensure they have at least one like or love
    if (!arr.some(a => a.preference_strength > 0.5)) {
      alert("Please select at least one cuisine you Like or Love.");
      return;
    }
    setCuisinePreferences(arr);
    router.push("/onboarding/cooking");
  };

  const renderTier = (tier: number, title: string, icon: string, bgClass: string) => {
    const items = CUISINES.filter(c => prefs[c.name] === tier);
    return (
      <div className={`p-4 rounded-xl border ${bgClass}`}>
        <h3 className="font-semibold text-lg mb-3 flex items-center gap-2">
          <span>{icon}</span> {title}
        </h3>
        <div className="flex flex-wrap gap-2">
          {items.map(c => (
            <div key={c.name} className="bg-background px-3 py-2 rounded-full border shadow-sm text-sm flex items-center gap-2 cursor-pointer"
                 onClick={() => toggleTier(c.name, tier === 1 ? 3 : tier - 1)}>
              <span>{c.emoji}</span>
              <span className="font-medium">{c.name}</span>
            </div>
          ))}
          {items.length === 0 && <span className="text-sm text-muted-foreground italic p-2">Empty</span>}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-8 animate-in slide-in-from-right-8 fade-in duration-500">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">Cuisine Preferences</h1>
        <p className="text-muted-foreground">Tap a cuisine to move it up the tiers.</p>
      </div>

      <div className="space-y-4">
        {renderTier(1, "Love It!", "❤️", "bg-rose-50/50 border-rose-100 dark:bg-rose-950/20")}
        {renderTier(2, "Like It", "👍", "bg-blue-50/50 border-blue-100 dark:bg-blue-950/20")}
        {renderTier(3, "Neutral / Don't Care", "🤷", "bg-muted/30")}
      </div>

      <div className="pt-6">
        <Button onClick={onSubmit} size="lg" className="w-full text-lg">Continue</Button>
      </div>
    </div>
  );
}
""")
