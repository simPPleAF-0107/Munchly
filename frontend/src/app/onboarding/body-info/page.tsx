"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useRouter } from "next/navigation";
import { useOnboardingStore } from "@/features/onboarding/store";
import { bodyInfoSchema } from "@/features/onboarding/schemas";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { ACTIVITY_LEVELS } from "@/lib/constants";

export default function BodyInfoPage() {
  const router = useRouter();
  const { bodyInfo, setBodyInfo } = useOnboardingStore();

  const form = useForm<z.infer<typeof bodyInfoSchema>>({
    resolver: zodResolver(bodyInfoSchema),
    defaultValues: {
      height_cm: bodyInfo.height_cm || undefined,
      weight_kg: bodyInfo.weight_kg || undefined,
      activity_level: bodyInfo.activity_level,
    },
  });

  const onSubmit = (data: z.infer<typeof bodyInfoSchema>) => {
    setBodyInfo(data);
    router.push("/onboarding/health-goal");
  };

  return (
    <div className="space-y-8 animate-in slide-in-from-right-8 fade-in duration-500">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">Your Body Profile</h1>
        <p className="text-muted-foreground">We need this to calculate your nutritional requirements.</p>
      </div>

      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="height_cm">Height (cm)</Label>
            <Input id="height_cm" type="number" placeholder="e.g. 175" {...form.register("height_cm")} className="text-lg py-6" />
            {form.formState.errors.height_cm && <p className="text-sm text-red-500">{form.formState.errors.height_cm.message}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="weight_kg">Weight (kg)</Label>
            <Input id="weight_kg" type="number" step="0.1" placeholder="e.g. 70.5" {...form.register("weight_kg")} className="text-lg py-6" />
            {form.formState.errors.weight_kg && <p className="text-sm text-red-500">{form.formState.errors.weight_kg.message}</p>}
          </div>
        </div>

        <div className="space-y-3">
          <Label>Activity Level</Label>
          <RadioGroup 
            defaultValue={form.getValues("activity_level")} 
            onValueChange={(val) => form.setValue("activity_level", val, { shouldValidate: true })}
            className="flex flex-col gap-3"
          >
            {ACTIVITY_LEVELS.map((level) => (
              <div key={level} className="flex items-center space-x-3 border rounded-lg p-4 cursor-pointer hover:bg-muted/50 transition-colors has-[:checked]:border-primary has-[:checked]:bg-primary/5">
                <RadioGroupItem value={level} id={`activity-${level}`} />
                <Label htmlFor={`activity-${level}`} className="flex-1 cursor-pointer text-base font-medium">
                  {level}
                </Label>
              </div>
            ))}
          </RadioGroup>
          {form.formState.errors.activity_level && <p className="text-sm text-red-500">{form.formState.errors.activity_level.message}</p>}
        </div>

        <div className="pt-6">
          <Button type="submit" size="lg" className="w-full text-lg">Continue</Button>
        </div>
      </form>
    </div>
  );
}
