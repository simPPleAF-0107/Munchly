"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { ShoppingListItemResponse } from "@/types/api";
import { formatCurrency, cn } from "@/lib/utils";

interface CategoryGroupProps {
  category: string;
  items: ShoppingListItemResponse[];
  currency: string;
}

export function CategoryGroup({ category, items, currency }: CategoryGroupProps) {
  const [isOpen, setIsOpen] = useState(true);
  const [checkedItems, setCheckedItems] = useState<Record<string, boolean>>(
    items.reduce((acc, item) => ({ ...acc, [item.food_id]: false }), {})
  );

  const toggleItem = (id: string) => {
    setCheckedItems(prev => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="border rounded-lg overflow-hidden bg-white">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 bg-gray-50/50 hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className="font-semibold text-gray-900">{category}</span>
          <span className="text-xs px-2 py-0.5 bg-gray-200 rounded-full text-gray-600">
            {items.filter(i => checkedItems[i.food_id]).length} / {items.length}
          </span>
        </div>
        {isOpen ? <ChevronUp className="w-5 h-5 text-gray-500" /> : <ChevronDown className="w-5 h-5 text-gray-500" />}
      </button>
      
      {isOpen && (
        <div className="divide-y">
          {items.map((item) => (
            <label 
              key={item.food_id} 
              className={cn(
                "flex items-center gap-3 p-4 cursor-pointer transition-colors hover:bg-orange-50/50",
                checkedItems[item.food_id] ? "opacity-60 bg-gray-50" : ""
              )}
            >
              <Checkbox 
                checked={checkedItems[item.food_id]} 
                onCheckedChange={() => toggleItem(item.food_id)}
                className="data-[state=checked]:bg-orange-500 data-[state=checked]:border-orange-500"
              />
              <div className="flex-1">
                <div className={cn("font-medium", checkedItems[item.food_id] && "line-through text-gray-500")}>
                  {item.food_name}
                </div>
                <div className="text-xs text-gray-500 flex gap-2">
                  <span>Need: {item.consumed_quantity_g}g</span>
                  <span>•</span>
                  <span>Buy: {item.purchase_quantity_g}g {item.purchase_unit}</span>
                </div>
              </div>
              <div className="font-medium text-sm text-gray-700">
                {formatCurrency(item.estimated_item_cost, currency)}
              </div>
            </label>
          ))}
        </div>
      )}
    </div>
  );
}
