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
