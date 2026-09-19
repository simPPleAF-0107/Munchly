"use client";

import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { apiClient } from "@/lib/api-client";
import type { DailyContextResponse, CheckInPayload } from "@/types/dashboard";

const FOOD_MOODS = [
  { value: "LIGHT", emoji: "🥗", label: "Light" },
  { value: "COMFORT", emoji: "🍲", label: "Comfort" },
  { value: "ADVENTUROUS", emoji: "🌍", label: "Adventurous" },
  { value: "QUICK", emoji: "⚡", label: "Quick" },
  { value: "HEALTHY", emoji: "🥦", label: "Healthy" },
  { value: "INDULGENT", emoji: "🍰", label: "Treat" },
  { value: "NO_PREFERENCE", emoji: "🤷", label: "Whatever" },
];

const ENERGY_LEVELS = [
  { value: "LOW", emoji: "😴", label: "Low" },
  { value: "NORMAL", emoji: "😊", label: "Normal" },
  { value: "HIGH", emoji: "💪", label: "High" },
];

interface CheckInModalProps {
  open: boolean;
  onClose: () => void;
  onComplete: (ctx: DailyContextResponse) => void;
}

export function CheckInModal({ open, onClose, onComplete }: CheckInModalProps) {
  const [step, setStep] = useState(0);
  const [payload, setPayload] = useState<CheckInPayload>({
    workout_today: false,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSkip = async () => {
    try {
      const ctx = await apiClient.post<DailyContextResponse>("/daily/skip", {});
      onComplete(ctx);
    } catch {
      onClose();
    }
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      const ctx = await apiClient.post<DailyContextResponse>("/daily/check-in", payload);
      onComplete(ctx);
    } catch {
      onClose();
    } finally {
      setIsSubmitting(false);
    }
  };

  const steps = [
    // Step 0: Workout today?
    <div key="workout" className="space-y-4">
      <p className="text-sm text-gray-500">Working out today?</p>
      <div className="flex gap-3">
        <Button
          variant={payload.workout_today ? "default" : "outline"}
          className={payload.workout_today ? "bg-orange-600 hover:bg-orange-700 flex-1" : "flex-1"}
          onClick={() => { setPayload(p => ({ ...p, workout_today: true })); setStep(1); }}
        >
          🏋️ Yes
        </Button>
        <Button
          variant={!payload.workout_today ? "default" : "outline"}
          className={!payload.workout_today ? "bg-gray-600 hover:bg-gray-700 flex-1" : "flex-1"}
          onClick={() => { setPayload(p => ({ ...p, workout_today: false })); setStep(1); }}
        >
          Not today
        </Button>
      </div>
    </div>,
    // Step 1: Energy level
    <div key="energy" className="space-y-4">
      <p className="text-sm text-gray-500">How's your energy?</p>
      <div className="flex gap-3">
        {ENERGY_LEVELS.map(e => (
          <Button
            key={e.value}
            variant={payload.energy_level === e.value ? "default" : "outline"}
            className={payload.energy_level === e.value ? "bg-orange-600 hover:bg-orange-700 flex-1" : "flex-1"}
            onClick={() => { setPayload(p => ({ ...p, energy_level: e.value })); setStep(2); }}
          >
            {e.emoji} {e.label}
          </Button>
        ))}
      </div>
    </div>,
    // Step 2: Food mood
    <div key="mood" className="space-y-4">
      <p className="text-sm text-gray-500">What are you in the mood for?</p>
      <div className="grid grid-cols-4 gap-2">
        {FOOD_MOODS.map(m => (
          <Button
            key={m.value}
            variant={payload.food_mood === m.value ? "default" : "outline"}
            className={`text-xs flex flex-col h-auto py-3 ${payload.food_mood === m.value ? "bg-orange-600 hover:bg-orange-700" : ""}`}
            onClick={() => { setPayload(p => ({ ...p, food_mood: m.value })); setStep(3); }}
          >
            <span className="text-lg">{m.emoji}</span>
            {m.label}
          </Button>
        ))}
      </div>
    </div>,
    // Step 3: Confirm
    <div key="confirm" className="space-y-4 text-center">
      <p className="text-lg font-medium">All set! 🌟</p>
      <p className="text-sm text-gray-500">Munchly will adjust today's recommendations.</p>
      <Button
        className="w-full bg-orange-600 hover:bg-orange-700"
        onClick={handleSubmit}
        disabled={isSubmitting}
      >
        {isSubmitting ? "Saving..." : "Done"}
      </Button>
    </div>,
  ];

  return (
    <Dialog open={open} onOpenChange={() => onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>🌞 Good morning check-in</DialogTitle>
        </DialogHeader>
        <div className="py-4">
          {steps[step]}
        </div>
        {step < 3 && (
          <div className="flex justify-between items-center pt-2 border-t">
            <Button variant="ghost" size="sm" onClick={handleSkip}>
              Skip check-in
            </Button>
            <div className="flex gap-1">
              {[0, 1, 2, 3].map(i => (
                <div key={i} className={`w-2 h-2 rounded-full ${i <= step ? "bg-orange-500" : "bg-gray-200"}`} />
              ))}
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
