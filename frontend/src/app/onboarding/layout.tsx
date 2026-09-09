"use client";

import { usePathname, useRouter } from "next/navigation";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { ChevronLeft } from "lucide-react";

const ONBOARDING_STEPS_ORDER = [
  "/onboarding/welcome",
  "/onboarding/basic-info",
  "/onboarding/body-info",
  "/onboarding/health-goal",
  "/onboarding/preview",
  "/onboarding/dietary-preference",
  "/onboarding/medical-conditions",
  "/onboarding/allergies",
  "/onboarding/restrictions",
  "/onboarding/food-preferences",
  "/onboarding/cuisine",
  "/onboarding/cooking",
  "/onboarding/budget",
  "/onboarding/review",
];

export default function OnboardingLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  
  const currentIdx = ONBOARDING_STEPS_ORDER.indexOf(pathname);
  const progress = currentIdx >= 0 ? ((currentIdx + 1) / ONBOARDING_STEPS_ORDER.length) * 100 : 0;

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <header className="sticky top-0 z-10 bg-background/80 backdrop-blur-md border-b">
        <div className="container max-w-3xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            {currentIdx > 0 && (
              <Button variant="ghost" size="icon" onClick={() => router.back()}>
                <ChevronLeft className="w-5 h-5" />
              </Button>
            )}
            <span className="font-bold text-xl text-primary">Munchly</span>
          </div>
          {currentIdx > 0 && (
            <div className="text-sm text-muted-foreground font-medium">
              Step {currentIdx} of {ONBOARDING_STEPS_ORDER.length - 1}
            </div>
          )}
        </div>
        {currentIdx > 0 && <Progress value={progress} className="h-1 rounded-none" />}
      </header>

      <main className="flex-1 container max-w-3xl mx-auto px-4 py-8">
        {children}
      </main>
    </div>
  );
}
