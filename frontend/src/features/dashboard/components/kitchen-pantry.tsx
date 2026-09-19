"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface KitchenPantryProps {
  pantryFoodIds: string[] | null;
  onUpdatePantry: () => void;
}

export function KitchenPantry({ pantryFoodIds, onUpdatePantry }: KitchenPantryProps) {
  const itemCount = pantryFoodIds?.length || 0;

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">🏠 Your Kitchen</CardTitle>
          <Button variant="outline" size="sm" className="text-xs" onClick={onUpdatePantry}>
            Update pantry
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {itemCount > 0 ? (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                {itemCount} items available today
              </Badge>
            </div>
            <p className="text-xs text-gray-500">
              Munchly prioritizes recipes using your available ingredients.
            </p>
          </div>
        ) : (
          <div className="text-center py-3">
            <p className="text-sm text-gray-500 mb-2">Tell Munchly what's in your kitchen</p>
            <p className="text-xs text-gray-400">
              We'll prioritize recipes that use what you already have.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
