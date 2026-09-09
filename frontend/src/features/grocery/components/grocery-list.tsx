"use client";

import { ShoppingListResponse } from "@/types/api";
import { CostSummary } from "./cost-summary";
import { CategoryGroup } from "./category-group";
import { Button } from "@/components/ui/button";
import { Share2 } from "lucide-react";

interface GroceryListProps {
  list: ShoppingListResponse;
}

export function GroceryList({ list }: GroceryListProps) {
  const handleShare = () => {
    let text = \`Grocery List (Budget: \${list.cost_currency} \${list.weekly_grocery_limit})\\n\\n\`;
    Object.entries(list.items_by_category).forEach(([category, items]) => {
      text += \`== \${category} ==\\n\`;
      items.forEach(item => {
        text += \`- \${item.food_name}: \${item.purchase_quantity} \${item.purchase_unit}\\n\`;
      });
      text += \`\\n\`;
    });
    navigator.clipboard.writeText(text);
    alert("Copied to clipboard!");
  };

  const categories = Object.keys(list.items_by_category).sort();

  return (
    <div className="space-y-6">
      <CostSummary
        consumed={list.consumed_cost}
        shopping={list.actual_shopping_cost}
        remaining={list.remaining_inventory_value}
        budget={list.weekly_grocery_limit}
        withinBudget={list.within_budget}
        currency={list.cost_currency}
      />

      <div className="flex justify-end">
        <Button variant="outline" size="sm" onClick={handleShare}>
          <Share2 className="w-4 h-4 mr-2" /> Share List
        </Button>
      </div>

      <div className="space-y-4">
        {categories.map((category) => (
          <CategoryGroup
            key={category}
            category={category}
            items={list.items_by_category[category]}
            currency={list.cost_currency}
          />
        ))}
      </div>
    </div>
  );
}
