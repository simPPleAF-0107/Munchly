"use client";

import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";

export default function WelcomePage() {
  const router = useRouter();

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-6 animate-in fade-in zoom-in duration-500">
      <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight">
        Welcome to <span className="text-primary">Munchly</span> 🥗
      </h1>
      <p className="text-lg md:text-xl text-muted-foreground max-w-xl">
        Let's build a personalized meal plan tailored exactly to your body, goals, and tastes. It only takes a few minutes.
      </p>
      <div className="pt-8">
        <Button size="lg" className="w-full sm:w-auto text-lg px-8 py-6 rounded-full" onClick={() => router.push("/onboarding/basic-info")}>
          Let's Begin
        </Button>
      </div>
    </div>
  );
}
