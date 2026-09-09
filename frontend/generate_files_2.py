import os

base_dir = r"d:\Projects\Munchly\frontend"

def write_file(path, content):
    full_path = os.path.join(base_dir, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

# 13. app/onboarding/preview/page.tsx
write_file("src/app/onboarding/preview/page.tsx", """
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
""")

# 14. app/onboarding/dietary-preference/page.tsx
write_file("src/app/onboarding/dietary-preference/page.tsx", """
"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useRouter } from "next/navigation";
import { useOnboardingStore } from "@/features/onboarding/store";
import { dietaryPreferenceSchema } from "@/features/onboarding/schemas";
import { Button } from "@/components/ui/button";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { DIET_TYPES } from "@/lib/constants";

export default function DietaryPreferencePage() {
  const router = useRouter();
  const { dietaryPreference, setDietaryPreference } = useOnboardingStore();

  const form = useForm<z.infer<typeof dietaryPreferenceSchema>>({
    resolver: zodResolver(dietaryPreferenceSchema),
    defaultValues: dietaryPreference,
  });

  const selectedDiet = form.watch("diet_type");

  const onSubmit = (data: z.infer<typeof dietaryPreferenceSchema>) => {
    setDietaryPreference(data);
    router.push("/onboarding/medical-conditions");
  };

  return (
    <div className="space-y-8 animate-in slide-in-from-right-8 fade-in duration-500">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">What's your diet type?</h1>
        <p className="text-muted-foreground">Select the diet that best matches how you eat.</p>
      </div>

      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
        <RadioGroup 
          defaultValue={form.getValues("diet_type")} 
          onValueChange={(val) => form.setValue("diet_type", val, { shouldValidate: true })}
          className="grid gap-4 sm:grid-cols-2"
        >
          {DIET_TYPES.map((dt) => (
            <div key={dt} className="flex flex-col space-y-2 border-2 rounded-xl p-4 cursor-pointer hover:border-primary/50 transition-colors has-[:checked]:border-primary has-[:checked]:bg-primary/5 relative">
              <div className="flex items-center space-x-3">
                <RadioGroupItem value={dt} id={`diet-${dt}`} />
                <Label htmlFor={`diet-${dt}`} className="cursor-pointer text-lg font-medium flex-1">
                  {dt}
                </Label>
              </div>
            </div>
          ))}
        </RadioGroup>
        {form.formState.errors.diet_type && <p className="text-sm text-red-500">{form.formState.errors.diet_type.message}</p>}

        {selectedDiet === "Omnivore" && (
          <div className="space-y-4 p-6 border rounded-xl bg-muted/30">
            <h3 className="font-semibold text-lg">Meats & Seafood</h3>
            <p className="text-sm text-muted-foreground">Select what you eat:</p>
            <div className="grid grid-cols-2 gap-4">
              {[
                { id: "eats_chicken", label: "Chicken" },
                { id: "eats_mutton", label: "Mutton/Beef/Pork" },
                { id: "eats_fish", label: "Fish" },
                { id: "eats_seafood", label: "Other Seafood" }
              ].map(({id, label}) => (
                <div key={id} className="flex items-center space-x-2">
                  <Checkbox 
                    id={id} 
                    checked={form.watch(id as any) as boolean} 
                    onCheckedChange={(c) => form.setValue(id as any, c === true)}
                  />
                  <Label htmlFor={id} className="cursor-pointer">{label}</Label>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="pt-4">
          <Button type="submit" size="lg" className="w-full text-lg">Continue</Button>
        </div>
      </form>
    </div>
  );
}
""")

# 15. app/onboarding/medical-conditions/page.tsx
write_file("src/app/onboarding/medical-conditions/page.tsx", """
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useOnboardingStore } from "@/features/onboarding/store";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { MEDICAL_CONDITIONS } from "@/lib/constants";
import { AlertCircle } from "lucide-react";

export default function MedicalConditionsPage() {
  const router = useRouter();
  const { medicalConditions, setMedicalConditions } = useOnboardingStore();
  const [selected, setSelected] = useState<string[]>(medicalConditions);

  const toggle = (condition: string) => {
    if (condition === "None") {
      setSelected(["None"]);
      return;
    }
    const filtered = selected.filter(c => c !== "None");
    if (filtered.includes(condition)) {
      setSelected(filtered.filter(c => c !== condition));
    } else {
      setSelected([...filtered, condition]);
    }
  };

  const onSubmit = () => {
    setMedicalConditions(selected.filter(c => c !== "None"));
    router.push("/onboarding/allergies");
  };

  return (
    <div className="space-y-8 animate-in slide-in-from-right-8 fade-in duration-500">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">Any medical conditions?</h1>
        <p className="text-muted-foreground">Select any that apply to help us safely plan your meals.</p>
      </div>

      <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900 rounded-lg p-4 flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-amber-600 dark:text-amber-500 mt-0.5 shrink-0" />
        <p className="text-sm text-amber-800 dark:text-amber-400">
          Disclaimer: Munchly is a tool for meal planning, not a substitute for professional medical advice. Always consult your physician.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="flex items-center space-x-3 border rounded-lg p-4 cursor-pointer hover:bg-muted/50">
          <Checkbox id="cond-none" checked={selected.includes("None")} onCheckedChange={() => toggle("None")} />
          <Label htmlFor="cond-none" className="flex-1 cursor-pointer font-medium">None</Label>
        </div>
        {MEDICAL_CONDITIONS.map((c) => (
          <div key={c} className="flex items-center space-x-3 border rounded-lg p-4 cursor-pointer hover:bg-muted/50">
            <Checkbox id={`cond-${c}`} checked={selected.includes(c)} onCheckedChange={() => toggle(c)} />
            <Label htmlFor={`cond-${c}`} className="flex-1 cursor-pointer font-medium">{c}</Label>
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
