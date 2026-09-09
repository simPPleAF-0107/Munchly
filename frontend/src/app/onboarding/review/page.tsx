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
