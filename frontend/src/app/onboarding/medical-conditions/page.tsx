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
