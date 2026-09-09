import os

base_dir = r"d:\Projects\Munchly\frontend"

def write_file(path, content):
    full_path = os.path.join(base_dir, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

# 20. app/onboarding/cooking/page.tsx
write_file("src/app/onboarding/cooking/page.tsx", """
"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useRouter } from "next/navigation";
import { useOnboardingStore } from "@/features/onboarding/store";
import { cookingSchema } from "@/features/onboarding/schemas";
import { Button } from "@/components/ui/button";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { COOKING_ABILITIES } from "@/lib/constants";

export default function CookingPage() {
  const router = useRouter();
  const { cooking, setCooking } = useOnboardingStore();

  const form = useForm<z.infer<typeof cookingSchema>>({
    resolver: zodResolver(cookingSchema),
    defaultValues: cooking,
  });

  const onSubmit = (data: z.infer<typeof cookingSchema>) => {
    setCooking(data);
    router.push("/onboarding/budget");
  };

  const prepTime = form.watch("max_prep_time_min");

  return (
    <div className="space-y-8 animate-in slide-in-from-right-8 fade-in duration-500">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">Cooking & Time</h1>
        <p className="text-muted-foreground">Let's find recipes that match your skills and schedule.</p>
      </div>

      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
        <div className="space-y-4">
          <Label className="text-lg">How would you rate your cooking skills?</Label>
          <RadioGroup 
            defaultValue={form.getValues("cooking_ability")} 
            onValueChange={(val) => form.setValue("cooking_ability", val, { shouldValidate: true })}
            className="grid gap-3 sm:grid-cols-2"
          >
            {COOKING_ABILITIES.map((c) => (
              <div key={c} className="flex items-center space-x-3 border rounded-lg p-4 cursor-pointer hover:bg-muted/50 transition-colors has-[:checked]:border-primary has-[:checked]:bg-primary/5">
                <RadioGroupItem value={c} id={`cook-${c}`} />
                <Label htmlFor={`cook-${c}`} className="flex-1 cursor-pointer font-medium">{c}</Label>
              </div>
            ))}
          </RadioGroup>
          {form.formState.errors.cooking_ability && <p className="text-sm text-red-500">{form.formState.errors.cooking_ability.message}</p>}
        </div>

        <div className="space-y-6 pt-4 border-t">
          <div className="flex justify-between items-center">
            <Label className="text-lg">Maximum prep & cook time per meal?</Label>
            <span className="font-bold text-xl text-primary">{prepTime} min</span>
          </div>
          
          <Slider 
            defaultValue={[form.getValues("max_prep_time_min")]} 
            max={120} min={5} step={5}
            onValueChange={(vals) => form.setValue("max_prep_time_min", vals[0], { shouldValidate: true })}
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>5 min (Quick)</span>
            <span>120 min (Elaborate)</span>
          </div>
          {form.formState.errors.max_prep_time_min && <p className="text-sm text-red-500">{form.formState.errors.max_prep_time_min.message}</p>}
        </div>

        <div className="pt-6">
          <Button type="submit" size="lg" className="w-full text-lg">Continue</Button>
        </div>
      </form>
    </div>
  );
}
""")

# 21. app/onboarding/budget/page.tsx
write_file("src/app/onboarding/budget/page.tsx", """
"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useRouter } from "next/navigation";
import { useOnboardingStore } from "@/features/onboarding/store";
import { budgetSchema } from "@/features/onboarding/schemas";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { BUDGET_TYPES } from "@/lib/constants";

export default function BudgetPage() {
  const router = useRouter();
  const { budget, setBudget } = useOnboardingStore();

  const form = useForm<z.infer<typeof budgetSchema>>({
    resolver: zodResolver(budgetSchema),
    defaultValues: {
      weekly_grocery_limit: budget.weekly_grocery_limit || undefined,
      weekly_grocery_limit_currency: budget.weekly_grocery_limit_currency,
      budget_type: budget.budget_type,
    },
  });

  const onSubmit = (data: z.infer<typeof budgetSchema>) => {
    setBudget(data);
    router.push("/onboarding/review");
  };

  return (
    <div className="space-y-8 animate-in slide-in-from-right-8 fade-in duration-500">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">Budget</h1>
        <p className="text-muted-foreground">Let's keep your meal plan affordable.</p>
      </div>

      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
        <div className="space-y-4">
          <Label className="text-lg">What kind of budget are you on?</Label>
          <RadioGroup 
            defaultValue={form.getValues("budget_type")} 
            onValueChange={(val) => form.setValue("budget_type", val, { shouldValidate: true })}
            className="grid gap-3 sm:grid-cols-2"
          >
            {BUDGET_TYPES.map((b) => (
              <div key={b} className="flex items-center space-x-3 border rounded-lg p-4 cursor-pointer hover:bg-muted/50 transition-colors has-[:checked]:border-primary has-[:checked]:bg-primary/5">
                <RadioGroupItem value={b} id={`budg-${b}`} />
                <Label htmlFor={`budg-${b}`} className="flex-1 cursor-pointer font-medium">{b}</Label>
              </div>
            ))}
          </RadioGroup>
          {form.formState.errors.budget_type && <p className="text-sm text-red-500">{form.formState.errors.budget_type.message}</p>}
        </div>

        <div className="space-y-4 pt-4 border-t">
          <Label className="text-lg">Weekly Grocery Limit</Label>
          <div className="flex gap-4">
            <div className="w-1/3">
              <Input {...form.register("weekly_grocery_limit_currency")} readOnly className="bg-muted text-center text-lg py-6" />
            </div>
            <div className="w-2/3">
              <Input type="number" placeholder="e.g. 2000" {...form.register("weekly_grocery_limit")} className="text-lg py-6" />
            </div>
          </div>
          {form.formState.errors.weekly_grocery_limit && <p className="text-sm text-red-500">{form.formState.errors.weekly_grocery_limit.message}</p>}
        </div>

        <div className="pt-6">
          <Button type="submit" size="lg" className="w-full text-lg">Review My Profile</Button>
        </div>
      </form>
    </div>
  );
}
""")

# 22. app/onboarding/review/page.tsx
write_file("src/app/onboarding/review/page.tsx", """
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useOnboardingStore } from "@/features/onboarding/store";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiClient } from "@/lib/api-client";

export default function ReviewPage() {
  const router = useRouter();
  const state = useOnboardingStore();
  const [loading, setLoading] = useState(false);

  const onSubmit = async () => {
    setLoading(true);
    try {
      // Assemble request
      const payload = {
        profile: {
          full_name: state.basicInfo.name,
          gender: state.basicInfo.gender,
          height_cm: state.bodyInfo.height_cm,
          weight_kg: state.bodyInfo.weight_kg,
          activity_level: state.bodyInfo.activity_level,
          health_goal: state.goal.health_goal,
          cooking_ability: state.cooking.cooking_ability,
          budget_type: state.budget.budget_type,
          location_country: state.basicInfo.country_code,
          location_city: state.basicInfo.city,
          currency: state.budget.weekly_grocery_limit_currency
        },
        dietary_preferences: [state.dietaryPreference.diet_type], // Simplifying for now
        allergies: state.allergies.map(a => ({ allergen: a.allergen, severity: "High" })),
        food_preferences: state.foodPreferences.map(fp => ({ food_item: fp.food_id, preference_type: fp.preference })),
        cuisines: state.cuisinePreferences.filter(c => c.preference_strength > 0.5).map(c => c.cuisine)
      };

      await apiClient.post("/onboarding/complete", payload);
      router.push("/dashboard");
    } catch (err) {
      console.error(err);
      alert("Failed to save profile. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const Section = ({ title, children, editPath }: { title: string, children: React.ReactNode, editPath: string }) => (
    <Card className="mb-4">
      <CardHeader className="py-4 flex flex-row items-center justify-between">
        <CardTitle className="text-lg">{title}</CardTitle>
        <Button variant="ghost" size="sm" onClick={() => router.push(editPath)}>Edit</Button>
      </CardHeader>
      <CardContent className="pb-4">
        {children}
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-8 animate-in zoom-in-95 duration-500">
      <div className="space-y-2 text-center">
        <h1 className="text-3xl font-bold">Review Your Profile</h1>
        <p className="text-muted-foreground">Make sure everything looks correct before we generate your meal plan.</p>
      </div>

      <div className="space-y-4">
        <Section title="Basic Info" editPath="/onboarding/basic-info">
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="text-muted-foreground">Name</div><div>{state.basicInfo.name}</div>
            <div className="text-muted-foreground">Age</div><div>{state.basicInfo.age}</div>
            <div className="text-muted-foreground">Gender</div><div>{state.basicInfo.gender}</div>
          </div>
        </Section>

        <Section title="Body & Goals" editPath="/onboarding/body-info">
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="text-muted-foreground">Height</div><div>{state.bodyInfo.height_cm} cm</div>
            <div className="text-muted-foreground">Weight</div><div>{state.bodyInfo.weight_kg} kg</div>
            <div className="text-muted-foreground">Activity</div><div>{state.bodyInfo.activity_level}</div>
            <div className="text-muted-foreground">Goal</div><div className="font-semibold text-primary">{state.goal.health_goal}</div>
          </div>
        </Section>

        <Section title="Diet & Allergies" editPath="/onboarding/dietary-preference">
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="text-muted-foreground">Diet Type</div><div>{state.dietaryPreference.diet_type}</div>
            <div className="text-muted-foreground">Allergies</div><div>{state.allergies.length > 0 ? state.allergies.map(a => a.allergen).join(', ') : 'None'}</div>
            <div className="text-muted-foreground">Restrictions</div><div>{state.restrictions.length > 0 ? state.restrictions.join(', ') : 'None'}</div>
          </div>
        </Section>

        <Section title="Cooking & Budget" editPath="/onboarding/cooking">
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="text-muted-foreground">Skill Level</div><div>{state.cooking.cooking_ability}</div>
            <div className="text-muted-foreground">Max Time</div><div>{state.cooking.max_prep_time_min} min</div>
            <div className="text-muted-foreground">Budget Type</div><div>{state.budget.budget_type}</div>
            <div className="text-muted-foreground">Weekly Limit</div><div>{state.budget.weekly_grocery_limit_currency} {state.budget.weekly_grocery_limit}</div>
          </div>
        </Section>
      </div>

      <div className="pt-4 pb-12">
        <Button onClick={onSubmit} size="lg" className="w-full text-lg h-14 rounded-full shadow-lg" disabled={loading}>
          {loading ? "Generating Plan..." : "Create My Meal Plan"}
        </Button>
      </div>
    </div>
  );
}
""")
