"use client";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { cn, formatCurrency } from "@/lib/utils";
import { RecipeResponse } from "@/types/api";
import { Clock, CheckCircle2 } from "lucide-react";

interface MealCardProps {
  recipe: RecipeResponse;
  optionType: string;
  currency: string;
  isSelected: boolean;
  onSelect: () => void;
}

const optionTypeConfig: Record<string, { label: string; color: string; icon: string }> = {
  BEST: { label: "Best Match", color: "bg-green-100 text-green-800", icon: "⭐" },
  BUDGET: { label: "Budget Friendly", color: "bg-blue-100 text-blue-800", icon: "💰" },
  VARIETY: { label: "Try Something New", color: "bg-purple-100 text-purple-800", icon: "🌟" },
};

export function MealCard({ recipe, optionType, currency, isSelected, onSelect }: MealCardProps) {
  const config = optionTypeConfig[optionType] || { label: optionType, color: "bg-gray-100 text-gray-800", icon: "✨" };

  return (
    <Card 
      onClick={onSelect}
      className={cn(
        "relative overflow-hidden cursor-pointer transition-all hover:shadow-md h-full flex flex-col",
        isSelected ? "ring-2 ring-orange-500 shadow-sm border-orange-200" : "border-gray-200"
      )}
    >
      {isSelected && (
        <div className="absolute top-2 right-2 z-10 bg-white rounded-full">
          <CheckCircle2 className="w-6 h-6 text-orange-500" />
        </div>
      )}
      
      {recipe.image_url && (
        <div className="h-32 w-full bg-gray-100 overflow-hidden shrink-0">
          <img src={recipe.image_url} alt={recipe.title} className="w-full h-full object-cover" />
        </div>
      )}
      
      <div className="p-4 flex-1 flex flex-col">
        <div className="mb-2">
          <Badge variant="secondary" className={cn("text-xs font-medium border-0", config.color)}>
            {config.icon} {config.label}
          </Badge>
        </div>
        
        <h4 className="font-semibold text-gray-900 leading-tight mb-2 line-clamp-2">{recipe.title}</h4>
        
        <div className="mt-auto space-y-3">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {recipe.prep_time_mins + recipe.cook_time_mins}m</span>
            <span>•</span>
            <span className="capitalize">{recipe.cuisine_type}</span>
          </div>
          
          <div className="flex items-center justify-between text-sm pt-3 border-t">
            <div className="text-gray-500">
              {recipe.calories_per_serving} kcal <span className="mx-1 text-gray-300">|</span> {recipe.protein_g}g pro
            </div>
            <div className="font-medium text-gray-900">
              {formatCurrency(recipe.estimated_cost || 0, currency)}
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}
