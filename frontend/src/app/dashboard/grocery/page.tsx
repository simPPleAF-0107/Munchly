"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api-client";
import { ShoppingListResponse, MealPlanResponse } from "@/types/api";
import { GroceryList } from "@/features/grocery/components/grocery-list";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";

export default function GroceryPage() {
  const router = useRouter();
  const [list, setList] = useState<ShoppingListResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchList = async () => {
    try {
      setIsLoading(true);
      const plan = await apiClient.get<MealPlanResponse>("/meal-plans/active");
      if (plan) {
        const groceryData = await apiClient.get<ShoppingListResponse>(`/grocery/${plan.id}`);
        setList(groceryData);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchList();
  }, []);

  if (isLoading && !list) {
    return <div className="flex h-64 items-center justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600" /></div>;
  }

  if (!list) {
    return (
      <div className="flex flex-col items-center justify-center h-full space-y-4 max-w-md mx-auto text-center py-20">
        <h2 className="text-xl font-semibold">No Grocery List</h2>
        <p className="text-gray-500">You need an active meal plan to generate a grocery list.</p>
        <Button onClick={() => router.push("/dashboard/meal-plan")} className="bg-orange-600 hover:bg-orange-700">
          Go to Meal Plan
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-8 animate-in fade-in">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Grocery List</h1>
        <Button variant="outline" size="sm" onClick={fetchList}>Regenerate</Button>
      </div>
      
      <GroceryList list={list} />
    </div>
  );
}
