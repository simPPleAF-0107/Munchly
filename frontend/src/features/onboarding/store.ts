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
  cooking: { cooking_ability: "BASIC", max_prep_time_min: 30 },
  budget: { weekly_grocery_limit: null, weekly_grocery_limit_currency: "INR", budget_type: "GROCERIES_ONLY" },
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
