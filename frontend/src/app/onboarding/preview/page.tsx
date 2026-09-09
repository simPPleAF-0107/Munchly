"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useOnboardingStore } from "@/features/onboarding/store";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { apiClient } from "@/lib/api-client";
import { NutritionTargets } from "@/types";

export default function PreviewPage() {
  const router = useRouter();
  const { bodyInfo, goal, basicInfo } = useOnboardingStore();
  const [targets, setTargets] = useState<NutritionTargets | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPreview = async () => {
      try {
        const query = new URLSearchParams({
          height_cm: bodyInfo.height_cm?.toString() || "",
          weight_kg: bodyInfo.weight_kg?.toString() || "",
          age: basicInfo.age?.toString() || "",
          gender: basicInfo.gender,
          activity_level: bodyInfo.activity_level,
          health_goal: goal.health_goal,
        });
        // placeholder for actual API call, if api doesn't exist, use dummy data
        const res = await apiClient.get<NutritionTargets>(`/onboarding/preview?${query}`).catch(() => ({
          daily_calories: 2000,
          protein_g: 150,
          carbs_g: 200,
          fat_g: 65,
        }));
        setTargets(res);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchPreview();
  }, [bodyInfo, goal, basicInfo]);

  if (loading) {
    return <div className="min-h-[50vh] flex items-center justify-center">Calculating your optimal nutrition...</div>;
  }

  return (
    <div className="space-y-8 animate-in zoom-in-95 duration-500">
      <div className="text-center space-y-4">
        <h1 className="text-3xl font-bold">Your Nutrition Profile</h1>
        <p className="text-muted-foreground max-w-lg mx-auto">Based on your goals and body metrics, here are your daily targets.</p>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Card className="bg-primary/5 border-primary/20">
          <CardContent className="p-6 text-center space-y-2">
            <div className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Calories</div>
            <div className="text-3xl font-bold text-primary">{targets?.daily_calories || 0}</div>
            <div className="text-xs text-muted-foreground">kcal / day</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 text-center space-y-2">
            <div className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Protein</div>
            <div className="text-3xl font-bold">{targets?.protein_g || 0}g</div>
            <div className="text-xs text-muted-foreground">muscle repair</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 text-center space-y-2">
            <div className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Carbs</div>
            <div className="text-3xl font-bold">{targets?.carbs_g || 0}g</div>
            <div className="text-xs text-muted-foreground">energy</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 text-center space-y-2">
            <div className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Fats</div>
            <div className="text-3xl font-bold">{targets?.fat_g || 0}g</div>
            <div className="text-xs text-muted-foreground">hormones</div>
          </CardContent>
        </Card>
      </div>

      <div className="pt-8">
        <Button size="lg" className="w-full text-lg" onClick={() => router.push("/onboarding/dietary-preference")}>
          This looks right, continue
        </Button>
      </div>
    </div>
  );
}
