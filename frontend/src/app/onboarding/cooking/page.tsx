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
