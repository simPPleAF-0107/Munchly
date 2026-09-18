"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useOnboardingStore } from "@/features/onboarding/store";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { ALLERGENS } from "@/lib/constants";
import { Plus, X } from "lucide-react";

export default function AllergiesPage() {
  const router = useRouter();
  const { allergies, setAllergies } = useOnboardingStore();
  
  const [selected, setSelected] = useState<string[]>(allergies.filter(a => !a.custom_allergen).map(a => a.allergen));
  const [customs, setCustoms] = useState<string[]>(allergies.filter(a => a.custom_allergen).map(a => a.allergen));
  const [newCustom, setNewCustom] = useState("");

  const toggle = (allergen: string) => {
    if (allergen === "NONE") {
      setSelected(["NONE"]);
      setCustoms([]);
      return;
    }
    const filtered = selected.filter(a => a !== "NONE");
    if (filtered.includes(allergen)) {
      setSelected(filtered.filter(a => a !== allergen));
    } else {
      setSelected([...filtered, allergen]);
    }
  };

  const addCustom = () => {
    if (newCustom.trim() && !customs.includes(newCustom.trim())) {
      setCustoms([...customs, newCustom.trim()]);
      setSelected(selected.filter(a => a !== "NONE"));
      setNewCustom("");
    }
  };

  const removeCustom = (c: string) => {
    setCustoms(customs.filter(x => x !== c));
  };

  const onSubmit = () => {
    const combined = [
      ...selected.filter(a => a !== "NONE").map(a => ({ allergen: a })),
      ...customs.map(c => ({ allergen: c, custom_allergen: "true" }))
    ];
    setAllergies(combined);
    router.push("/onboarding/restrictions");
  };

  return (
    <div className="space-y-8 animate-in slide-in-from-right-8 fade-in duration-500">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">Do you have any allergies?</h1>
        <p className="text-muted-foreground">Select common allergens or add your own.</p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <div className="flex items-center space-x-3 border rounded-lg p-4 cursor-pointer hover:bg-muted/50">
          <Checkbox id="alg-none" checked={selected.includes("NONE")} onCheckedChange={() => toggle("NONE")} />
          <Label htmlFor="alg-none" className="flex-1 cursor-pointer font-medium">None</Label>
        </div>
        {ALLERGENS.filter(a => a.value !== "CUSTOM").map((a) => (
          <div key={a.value} className="flex items-center space-x-3 border rounded-lg p-4 cursor-pointer hover:bg-muted/50">
            <Checkbox id={`alg-${a.value}`} checked={selected.includes(a.value)} onCheckedChange={() => toggle(a.value)} />
            <Label htmlFor={`alg-${a.value}`} className="flex-1 cursor-pointer font-medium">{a.label}</Label>
          </div>
        ))}
      </div>

      <div className="space-y-4 pt-4">
        <Label>Other Allergies</Label>
        <div className="flex gap-2">
          <Input 
            placeholder="Type an allergy..." 
            value={newCustom} 
            onChange={(e) => setNewCustom(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addCustom())}
          />
          <Button type="button" onClick={addCustom} variant="secondary">
            <Plus className="w-4 h-4 mr-2" /> Add
          </Button>
        </div>
        
        {customs.length > 0 && (
          <div className="flex flex-wrap gap-2 pt-2">
            {customs.map(c => (
              <div key={c} className="flex items-center bg-secondary text-secondary-foreground px-3 py-1.5 rounded-full text-sm">
                <span>{c}</span>
                <button onClick={() => removeCustom(c)} className="ml-2 text-muted-foreground hover:text-foreground">
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="pt-6">
        <Button onClick={onSubmit} size="lg" className="w-full text-lg">Continue</Button>
      </div>
    </div>
  );
}
