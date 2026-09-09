"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useRouter } from "next/navigation";
import { useOnboardingStore } from "@/features/onboarding/store";
import { healthGoalSchema } from "@/features/onboarding/schemas";
import { Button } from "@/components/ui/button";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { HEALTH_GOALS } from "@/lib/constants";

export default function HealthGoalPage() {
  const router = useRouter();
  const { goal, setGoal } = useOnboardingStore();

  const form = useForm<z.infer<typeof healthGoalSchema>>({
    resolver: zodResolver(healthGoalSchema),
    defaultValues: {
      health_goal: goal.health_goal,
    },
  });

  const onSubmit = (data: z.infer<typeof healthGoalSchema>) => {
    setGoal(data);
    router.push("/onboarding/preview");
  };

  return (
    <div className="space-y-8 animate-in slide-in-from-right-8 fade-in duration-500">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">What is your primary goal?</h1>
        <p className="text-muted-foreground">We'll optimize your meal plan based on this goal.</p>
      </div>

      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <RadioGroup 
          defaultValue={form.getValues("health_goal")} 
          onValueChange={(val) => form.setValue("health_goal", val, { shouldValidate: true })}
          className="grid gap-4 md:grid-cols-2"
        >
          {HEALTH_GOALS.map((g) => (
            <div key={g} className="flex flex-col items-center justify-center space-y-2 border-2 rounded-xl p-6 cursor-pointer hover:border-primary/50 transition-colors has-[:checked]:border-primary has-[:checked]:bg-primary/5 relative text-center">
              <RadioGroupItem value={g} id={`goal-${g}`} className="absolute top-4 right-4" />
              <Label htmlFor={`goal-${g}`} className="w-full cursor-pointer text-lg font-semibold h-full flex items-center justify-center">
                {g}
              </Label>
            </div>
          ))}
        </RadioGroup>
        {form.formState.errors.health_goal && <p className="text-sm text-red-500 text-center">{form.formState.errors.health_goal.message}</p>}

        <div className="pt-6">
          <Button type="submit" size="lg" className="w-full text-lg">Generate Nutrition Profile</Button>
        </div>
      </form>
    </div>
  );
}
