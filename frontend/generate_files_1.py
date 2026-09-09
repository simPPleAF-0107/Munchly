import os

base_dir = r"d:\Projects\Munchly\frontend"

def write_file(path, content):
    full_path = os.path.join(base_dir, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

# 1. lib/auth.ts
write_file("src/lib/auth.ts", """
import { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) return null;
        try {
          const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/auth/login`, {
            method: 'POST',
            body: JSON.stringify({ email: credentials.email, password: credentials.password }),
            headers: { "Content-Type": "application/json" }
          });
          if (!res.ok) return null;
          const user = await res.json();
          if (user && user.access_token) {
            return {
              id: "0",
              email: credentials.email,
              accessToken: user.access_token,
              refreshToken: user.refresh_token,
            };
          }
          return null;
        } catch (e) {
          return null;
        }
      }
    })
  ],
  session: {
    strategy: "jwt"
  },
  callbacks: {
    async jwt({ token, user, account }) {
      if (user) {
        token.accessToken = (user as any).accessToken;
        token.refreshToken = (user as any).refreshToken;
      }
      return token;
    },
    async session({ session, token }) {
      (session as any).accessToken = token.accessToken;
      return session;
    }
  },
  pages: {
    signIn: '/login',
  }
};
""")

# 2. app/api/auth/[...nextauth]/route.ts
write_file("src/app/api/auth/[...nextauth]/route.ts", """
import NextAuth from "next-auth";
import { authOptions } from "@/lib/auth";

const handler = NextAuth(authOptions);

export { handler as GET, handler as POST };
""")

# 3. app/(auth)/login/page.tsx
write_file("src/app/(auth)/login/page.tsx", """
"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { signIn } from "next-auth/react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";

const loginSchema = z.object({
  email: z.string().email("Invalid email"),
  password: z.string().min(1, "Password is required"),
});

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  
  const form = useForm<z.infer<typeof loginSchema>>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  const onSubmit = async (data: z.infer<typeof loginSchema>) => {
    setError(null);
    const res = await signIn("credentials", {
      email: data.email,
      password: data.password,
      redirect: false,
    });

    if (res?.error) {
      setError("Invalid email or password");
    } else {
      router.push("/dashboard");
    }
  };

  const loginWithGoogle = async () => {
    // Implement Google login logic client-side
    // fetch /api/v1/auth/google
  };

  return (
    <div className="w-full max-w-md">
      <Card>
        <CardHeader className="space-y-1 text-center">
          <CardTitle className="text-2xl font-bold">Welcome back</CardTitle>
          <CardDescription>Login to your Munchly account</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" placeholder="m@example.com" {...form.register("email")} />
              {form.formState.errors.email && <p className="text-sm text-red-500">{form.formState.errors.email.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input id="password" type="password" {...form.register("password")} />
              {form.formState.errors.password && <p className="text-sm text-red-500">{form.formState.errors.password.message}</p>}
            </div>
            {error && <p className="text-sm text-red-500">{error}</p>}
            <Button type="submit" className="w-full" disabled={form.formState.isSubmitting}>
              {form.formState.isSubmitting ? "Signing in..." : "Sign in"}
            </Button>
          </form>
          
          <div className="relative my-4">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-background px-2 text-muted-foreground">Or continue with</span>
            </div>
          </div>
          
          <Button variant="outline" type="button" className="w-full" onClick={loginWithGoogle}>
            Google
          </Button>
        </CardContent>
        <CardFooter className="flex justify-center">
          <p className="text-sm text-muted-foreground">
            Don't have an account?{" "}
            <Link href="/register" className="text-primary hover:underline">
              Sign up
            </Link>
          </p>
        </CardFooter>
      </Card>
    </div>
  );
}
""")

# 4. app/(auth)/register/page.tsx
write_file("src/app/(auth)/register/page.tsx", """
"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { apiClient } from "@/lib/api-client";

const registerSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Invalid email"),
  password: z.string().min(8, "Password must be at least 8 characters"),
  confirmPassword: z.string()
}).refine(data => data.password === data.confirmPassword, {
  message: "Passwords do not match",
  path: ["confirmPassword"]
});

export default function RegisterPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  
  const form = useForm<z.infer<typeof registerSchema>>({
    resolver: zodResolver(registerSchema),
    defaultValues: { name: "", email: "", password: "", confirmPassword: "" },
  });

  const onSubmit = async (data: z.infer<typeof registerSchema>) => {
    setError(null);
    try {
      await apiClient.post("/auth/register", {
        name: data.name,
        email: data.email,
        password: data.password
      });
      // You might want to automatically log them in here
      router.push("/onboarding/welcome");
    } catch (err: any) {
      if (err.message?.includes("409")) {
        setError("Email already in use");
      } else {
        setError(err.message || "Something went wrong");
      }
    }
  };

  return (
    <div className="w-full max-w-md">
      <Card>
        <CardHeader className="space-y-1 text-center">
          <CardTitle className="text-2xl font-bold">Create an account</CardTitle>
          <CardDescription>Enter your details below to create your account</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input id="name" placeholder="John Doe" {...form.register("name")} />
              {form.formState.errors.name && <p className="text-sm text-red-500">{form.formState.errors.name.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" placeholder="m@example.com" {...form.register("email")} />
              {form.formState.errors.email && <p className="text-sm text-red-500">{form.formState.errors.email.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input id="password" type="password" {...form.register("password")} />
              {form.formState.errors.password && <p className="text-sm text-red-500">{form.formState.errors.password.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm Password</Label>
              <Input id="confirmPassword" type="password" {...form.register("confirmPassword")} />
              {form.formState.errors.confirmPassword && <p className="text-sm text-red-500">{form.formState.errors.confirmPassword.message}</p>}
            </div>
            {error && <p className="text-sm text-red-500">{error}</p>}
            <Button type="submit" className="w-full" disabled={form.formState.isSubmitting}>
              {form.formState.isSubmitting ? "Creating account..." : "Sign Up"}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex justify-center">
          <p className="text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link href="/login" className="text-primary hover:underline">
              Sign in
            </Link>
          </p>
        </CardFooter>
      </Card>
    </div>
  );
}
""")

# 5. app/(auth)/layout.tsx
write_file("src/app/(auth)/layout.tsx", """
import Link from "next/link";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-muted/30 p-4">
      <div className="mb-8">
        <Link href="/" className="flex items-center gap-2">
          <span className="text-3xl font-bold text-primary">Munchly</span>
        </Link>
      </div>
      {children}
    </div>
  );
}
""")

# 6. features/onboarding/store.ts
write_file("src/features/onboarding/store.ts", """
import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

export interface OnboardingState {
  currentStep: number;
  basicInfo: { name: string; age: number | null; gender: string; country_code: string; state_code: string; city: string };
  bodyInfo: { height_cm: number | null; weight_kg: number | null; activity_level: string };
  goal: { health_goal: string };
  dietaryPreference: { diet_type: string; eats_chicken: boolean; eats_mutton: boolean; eats_fish: boolean; eats_seafood: boolean };
  allergies: { allergen: string; custom_allergen?: string }[];
  restrictions: string[];
  medicalConditions: string[];
  foodPreferences: { food_id: string; preference: string }[];
  cuisinePreferences: { cuisine: string; preference_strength: number }[];
  cooking: { cooking_ability: string; max_prep_time_min: number };
  budget: { weekly_grocery_limit: number | null; weekly_grocery_limit_currency: string; budget_type: string };
  pantryItems: { food_id: string; quantity_g: number; unit: string; food_name: string }[];
  
  setCurrentStep: (step: number) => void;
  setBasicInfo: (data: Partial<OnboardingState['basicInfo']>) => void;
  setBodyInfo: (data: Partial<OnboardingState['bodyInfo']>) => void;
  setGoal: (data: Partial<OnboardingState['goal']>) => void;
  setDietaryPreference: (data: Partial<OnboardingState['dietaryPreference']>) => void;
  setAllergies: (data: OnboardingState['allergies']) => void;
  setRestrictions: (data: string[]) => void;
  setMedicalConditions: (data: string[]) => void;
  setFoodPreferences: (data: OnboardingState['foodPreferences']) => void;
  setCuisinePreferences: (data: OnboardingState['cuisinePreferences']) => void;
  setCooking: (data: Partial<OnboardingState['cooking']>) => void;
  setBudget: (data: Partial<OnboardingState['budget']>) => void;
  setPantryItems: (data: OnboardingState['pantryItems']) => void;
  reset: () => void;
}

const initialState = {
  currentStep: 0,
  basicInfo: { name: "", age: null, gender: "", country_code: "IN", state_code: "", city: "" },
  bodyInfo: { height_cm: null, weight_kg: null, activity_level: "" },
  goal: { health_goal: "" },
  dietaryPreference: { diet_type: "", eats_chicken: false, eats_mutton: false, eats_fish: false, eats_seafood: false },
  allergies: [],
  restrictions: [],
  medicalConditions: [],
  foodPreferences: [],
  cuisinePreferences: [],
  cooking: { cooking_ability: "Beginner", max_prep_time_min: 30 },
  budget: { weekly_grocery_limit: null, weekly_grocery_limit_currency: "INR", budget_type: "Economy" },
  pantryItems: [],
};

export const useOnboardingStore = create<OnboardingState>()(
  persist(
    (set) => ({
      ...initialState,
      setCurrentStep: (step) => set({ currentStep: step }),
      setBasicInfo: (data) => set((state) => ({ basicInfo: { ...state.basicInfo, ...data } })),
      setBodyInfo: (data) => set((state) => ({ bodyInfo: { ...state.bodyInfo, ...data } })),
      setGoal: (data) => set((state) => ({ goal: { ...state.goal, ...data } })),
      setDietaryPreference: (data) => set((state) => ({ dietaryPreference: { ...state.dietaryPreference, ...data } })),
      setAllergies: (data) => set({ allergies: data }),
      setRestrictions: (data) => set({ restrictions: data }),
      setMedicalConditions: (data) => set({ medicalConditions: data }),
      setFoodPreferences: (data) => set({ foodPreferences: data }),
      setCuisinePreferences: (data) => set({ cuisinePreferences: data }),
      setCooking: (data) => set((state) => ({ cooking: { ...state.cooking, ...data } })),
      setBudget: (data) => set((state) => ({ budget: { ...state.budget, ...data } })),
      setPantryItems: (data) => set({ pantryItems: data }),
      reset: () => set(initialState),
    }),
    {
      name: 'munchly-onboarding-storage',
      storage: createJSONStorage(() => typeof window !== 'undefined' ? sessionStorage : ({} as any)),
    }
  )
);
""")

# 7. features/onboarding/schemas.ts
write_file("src/features/onboarding/schemas.ts", """
import * as z from "zod";

export const basicInfoSchema = z.object({
  name: z.string().min(1, "Name is required"),
  age: z.coerce.number().min(13, "Must be at least 13").max(120, "Invalid age"),
  gender: z.string().min(1, "Gender is required"),
  country_code: z.string().default("IN"),
  state_code: z.string().optional(),
  city: z.string().optional(),
});

export const bodyInfoSchema = z.object({
  height_cm: z.coerce.number().min(50).max(300),
  weight_kg: z.coerce.number().min(10).max(500),
  activity_level: z.string().min(1, "Activity level is required"),
});

export const healthGoalSchema = z.object({
  health_goal: z.string().min(1, "Goal is required"),
});

export const dietaryPreferenceSchema = z.object({
  diet_type: z.string().min(1, "Diet type is required"),
  eats_chicken: z.boolean().optional(),
  eats_mutton: z.boolean().optional(),
  eats_fish: z.boolean().optional(),
  eats_seafood: z.boolean().optional(),
});

export const cookingSchema = z.object({
  cooking_ability: z.string().min(1),
  max_prep_time_min: z.coerce.number().min(5).max(120),
});

export const budgetSchema = z.object({
  weekly_grocery_limit: z.coerce.number().min(1),
  weekly_grocery_limit_currency: z.string().min(1),
  budget_type: z.string().min(1),
});
""")

# 8. app/onboarding/layout.tsx
write_file("src/app/onboarding/layout.tsx", """
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
""")

# 9. app/onboarding/welcome/page.tsx
write_file("src/app/onboarding/welcome/page.tsx", """
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
""")

# 10. app/onboarding/basic-info/page.tsx
write_file("src/app/onboarding/basic-info/page.tsx", """
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
""")

# 11. app/onboarding/body-info/page.tsx
write_file("src/app/onboarding/body-info/page.tsx", """
"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useRouter } from "next/navigation";
import { useOnboardingStore } from "@/features/onboarding/store";
import { bodyInfoSchema } from "@/features/onboarding/schemas";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { ACTIVITY_LEVELS } from "@/lib/constants";

export default function BodyInfoPage() {
  const router = useRouter();
  const { bodyInfo, setBodyInfo } = useOnboardingStore();

  const form = useForm<z.infer<typeof bodyInfoSchema>>({
    resolver: zodResolver(bodyInfoSchema),
    defaultValues: {
      height_cm: bodyInfo.height_cm || undefined,
      weight_kg: bodyInfo.weight_kg || undefined,
      activity_level: bodyInfo.activity_level,
    },
  });

  const onSubmit = (data: z.infer<typeof bodyInfoSchema>) => {
    setBodyInfo(data);
    router.push("/onboarding/health-goal");
  };

  return (
    <div className="space-y-8 animate-in slide-in-from-right-8 fade-in duration-500">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">Your Body Profile</h1>
        <p className="text-muted-foreground">We need this to calculate your nutritional requirements.</p>
      </div>

      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="height_cm">Height (cm)</Label>
            <Input id="height_cm" type="number" placeholder="e.g. 175" {...form.register("height_cm")} className="text-lg py-6" />
            {form.formState.errors.height_cm && <p className="text-sm text-red-500">{form.formState.errors.height_cm.message}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="weight_kg">Weight (kg)</Label>
            <Input id="weight_kg" type="number" step="0.1" placeholder="e.g. 70.5" {...form.register("weight_kg")} className="text-lg py-6" />
            {form.formState.errors.weight_kg && <p className="text-sm text-red-500">{form.formState.errors.weight_kg.message}</p>}
          </div>
        </div>

        <div className="space-y-3">
          <Label>Activity Level</Label>
          <RadioGroup 
            defaultValue={form.getValues("activity_level")} 
            onValueChange={(val) => form.setValue("activity_level", val, { shouldValidate: true })}
            className="flex flex-col gap-3"
          >
            {ACTIVITY_LEVELS.map((level) => (
              <div key={level} className="flex items-center space-x-3 border rounded-lg p-4 cursor-pointer hover:bg-muted/50 transition-colors has-[:checked]:border-primary has-[:checked]:bg-primary/5">
                <RadioGroupItem value={level} id={`activity-${level}`} />
                <Label htmlFor={`activity-${level}`} className="flex-1 cursor-pointer text-base font-medium">
                  {level}
                </Label>
              </div>
            ))}
          </RadioGroup>
          {form.formState.errors.activity_level && <p className="text-sm text-red-500">{form.formState.errors.activity_level.message}</p>}
        </div>

        <div className="pt-6">
          <Button type="submit" size="lg" className="w-full text-lg">Continue</Button>
        </div>
      </form>
    </div>
  );
}
""")

# 12. app/onboarding/health-goal/page.tsx
write_file("src/app/onboarding/health-goal/page.tsx", """
"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useRouter } from "next/navigation";
import { useOnboardingStore } from "@/features/onboarding/store";
import { healthGoalSchema } from "@/features/onboarding/schemas";
import { Button } from "@/components/ui/button";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { HEALTH_GOALS } from "@/lib/constants";

export default function HealthGoalPage() {
  const router = useRouter();
  const { goal, setGoal } = useOnboardingStore();

  const form = useForm<z.infer<typeof healthGoalSchema>>({
    resolver: zodResolver(healthGoalSchema),
    defaultValues: {
      health_goal: goal.health_goal,
    },
  });

  const onSubmit = (data: z.infer<typeof healthGoalSchema>) => {
    setGoal(data);
    router.push("/onboarding/preview");
  };

  return (
    <div className="space-y-8 animate-in slide-in-from-right-8 fade-in duration-500">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">What is your primary goal?</h1>
        <p className="text-muted-foreground">We'll optimize your meal plan based on this goal.</p>
      </div>

      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <RadioGroup 
          defaultValue={form.getValues("health_goal")} 
          onValueChange={(val) => form.setValue("health_goal", val, { shouldValidate: true })}
          className="grid gap-4 md:grid-cols-2"
        >
          {HEALTH_GOALS.map((g) => (
            <div key={g} className="flex flex-col items-center justify-center space-y-2 border-2 rounded-xl p-6 cursor-pointer hover:border-primary/50 transition-colors has-[:checked]:border-primary has-[:checked]:bg-primary/5 relative text-center">
              <RadioGroupItem value={g} id={`goal-${g}`} className="absolute top-4 right-4" />
              <Label htmlFor={`goal-${g}`} className="w-full cursor-pointer text-lg font-semibold h-full flex items-center justify-center">
                {g}
              </Label>
            </div>
          ))}
        </RadioGroup>
        {form.formState.errors.health_goal && <p className="text-sm text-red-500 text-center">{form.formState.errors.health_goal.message}</p>}

        <div className="pt-6">
          <Button type="submit" size="lg" className="w-full text-lg">Generate Nutrition Profile</Button>
        </div>
      </form>
    </div>
  );
}
""")

# Remaining pages logic will be written in the next tool call.
# Let's execute this first part.
