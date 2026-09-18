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
    CUISINES.forEach(c => { map[c.value] = 3; });
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
    const items = CUISINES.filter(c => prefs[c.value] === tier);
    return (
      <div className={`p-4 rounded-xl border ${bgClass}`}>
        <h3 className="font-semibold text-lg mb-3 flex items-center gap-2">
          <span>{icon}</span> {title}
        </h3>
        <div className="flex flex-wrap gap-2">
          {items.map(c => (
            <div key={c.value} className="bg-background px-3 py-2 rounded-full border shadow-sm text-sm flex items-center gap-2 cursor-pointer"
                 onClick={() => toggleTier(c.value, tier === 1 ? 3 : tier - 1)}>
              <span>{c.emoji}</span>
              <span className="font-medium">{c.label}</span>
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
