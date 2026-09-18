"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useOnboardingStore } from "@/features/onboarding/store";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { DIETARY_RESTRICTIONS } from "@/lib/constants";

export default function RestrictionsPage() {
  const router = useRouter();
  const { restrictions, setRestrictions } = useOnboardingStore();
  const [selected, setSelected] = useState<string[]>(restrictions);

  const toggle = (res: string) => {
    if (res === "NONE") {
      setSelected(["NONE"]);
      return;
    }
    const filtered = selected.filter(a => a !== "NONE");
    if (filtered.includes(res)) {
      setSelected(filtered.filter(a => a !== res));
    } else {
      setSelected([...filtered, res]);
    }
  };

  const onSubmit = () => {
    setRestrictions(selected.filter(a => a !== "NONE"));
    router.push("/onboarding/food-preferences");
  };

  return (
    <div className="space-y-8 animate-in slide-in-from-right-8 fade-in duration-500">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">Dietary Restrictions</h1>
        <p className="text-muted-foreground">Any specific restrictions we should know about?</p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="flex items-center space-x-3 border rounded-lg p-4 cursor-pointer hover:bg-muted/50">
          <Checkbox id="res-none" checked={selected.includes("NONE")} onCheckedChange={() => toggle("NONE")} />
          <Label htmlFor="res-none" className="flex-1 cursor-pointer font-medium">None</Label>
        </div>
        {DIETARY_RESTRICTIONS.map((res) => (
          <div key={res.value} className="flex items-center space-x-3 border rounded-lg p-4 cursor-pointer hover:bg-muted/50">
            <Checkbox id={`res-${res.value}`} checked={selected.includes(res.value)} onCheckedChange={() => toggle(res.value)} />
            <Label htmlFor={`res-${res.value}`} className="flex-1 cursor-pointer font-medium">{res.label}</Label>
          </div>
        ))}
      </div>

      <div className="pt-6">
        <Button onClick={onSubmit} size="lg" className="w-full text-lg">Continue</Button>
      </div>
    </div>
  );
}
