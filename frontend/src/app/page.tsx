import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background p-4">
      <main className="max-w-3xl text-center space-y-8">
        <h1 className="text-6xl font-extrabold tracking-tight text-primary">
          Munchly
        </h1>
        <p className="text-2xl text-muted-foreground font-medium">
          Your body, health, diet, budget, location, cuisine — one personalized meal plan.
        </p>
        <div className="flex items-center justify-center gap-4 pt-8">
          <Link href="/onboarding/welcome">
            <Button size="lg" className="text-lg px-8">
              Get Started
            </Button>
          </Link>
          <Link href="/login">
            <Button size="lg" variant="outline" className="text-lg px-8">
              Sign In
            </Button>
          </Link>
        </div>
      </main>
    </div>
  );
}
