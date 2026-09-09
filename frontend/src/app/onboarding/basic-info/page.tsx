"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useRouter } from "next/navigation";
import { useOnboardingStore } from "@/features/onboarding/store";
import { basicInfoSchema } from "@/features/onboarding/schemas";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";

export default function BasicInfoPage() {
  const router = useRouter();
  const { basicInfo, setBasicInfo } = useOnboardingStore();

  const form = useForm<z.infer<typeof basicInfoSchema>>({
    resolver: zodResolver(basicInfoSchema),
    defaultValues: {
      name: basicInfo.name,
      age: basicInfo.age || undefined,
      gender: basicInfo.gender,
      country_code: basicInfo.country_code,
      state_code: basicInfo.state_code,
      city: basicInfo.city,
    },
  });

  const onSubmit = (data: z.infer<typeof basicInfoSchema>) => {
    setBasicInfo(data);
    router.push("/onboarding/body-info");
  };

  return (
    <div className="space-y-8 animate-in slide-in-from-right-8 fade-in duration-500">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">Tell us about yourself</h1>
        <p className="text-muted-foreground">This helps us personalize your meal plans.</p>
      </div>

      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <div className="space-y-2">
          <Label htmlFor="name">What should we call you?</Label>
          <Input id="name" placeholder="Your name" {...form.register("name")} className="text-lg py-6" />
          {form.formState.errors.name && <p className="text-sm text-red-500">{form.formState.errors.name.message}</p>}
        </div>

        <div className="space-y-2">
          <Label htmlFor="age">How old are you?</Label>
          <Input id="age" type="number" placeholder="Age" {...form.register("age")} className="text-lg py-6" />
          {form.formState.errors.age && <p className="text-sm text-red-500">{form.formState.errors.age.message}</p>}
        </div>

        <div className="space-y-3">
          <Label>Gender</Label>
          <RadioGroup 
            defaultValue={form.getValues("gender")} 
            onValueChange={(val) => form.setValue("gender", val, { shouldValidate: true })}
            className="flex flex-col sm:flex-row gap-4"
          >
            {["Male", "Female", "Other"].map((g) => (
              <div key={g} className="flex items-center space-x-2 border rounded-lg p-4 flex-1 cursor-pointer hover:bg-muted/50 transition-colors has-[:checked]:border-primary has-[:checked]:bg-primary/5">
                <RadioGroupItem value={g} id={`gender-${g}`} />
                <Label htmlFor={`gender-${g}`} className="flex-1 cursor-pointer">{g}</Label>
              </div>
            ))}
          </RadioGroup>
          {form.formState.errors.gender && <p className="text-sm text-red-500">{form.formState.errors.gender.message}</p>}
        </div>

        <div className="pt-6">
          <Button type="submit" size="lg" className="w-full text-lg">Continue</Button>
        </div>
      </form>
    </div>
  );
}
