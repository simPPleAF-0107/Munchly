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
