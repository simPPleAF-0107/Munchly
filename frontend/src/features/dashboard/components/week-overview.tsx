"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { formatCurrency } from "@/lib/utils";
import type { MealPlanMealResponse } from "@/types/api";

const DAY_NAMES = ["", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

interface WeekOverviewProps {
  meals: MealPlanMealResponse[];
  currency: string;
  todayDow: number;
}

export function WeekOverview({ meals, currency, todayDow }: WeekOverviewProps) {
  const [expanded, setExpanded] = useState(false);

  const dayGroups = Array.from({ length: 7 }, (_, i) => {
    const dow = i + 1;
    return {
      dow,
      name: DAY_NAMES[dow],
      isToday: dow === todayDow,
      meals: meals.filter(m => m.day_of_week === dow),
    };
  });

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">📅 Your Week</CardTitle>
          <Button variant="ghost" size="sm" onClick={() => setExpanded(!expanded)} className="text-xs">
            {expanded ? "Collapse" : "Expand"}
          </Button>
        </div>
      </CardHeader>
      {expanded && (
        <CardContent className="space-y-2">
          {dayGroups.map(day => (
            <div
              key={day.dow}
              className={`flex items-center gap-3 p-2 rounded text-sm ${
                day.isToday ? "bg-orange-50 font-medium" : "bg-gray-50"
              }`}
            >
              <span className={`w-10 text-xs font-semibold ${day.isToday ? "text-orange-600" : "text-gray-500"}`}>
                {day.isToday ? "Today" : day.name}
              </span>
              <div className="flex-1 flex gap-2">
                {day.meals.length > 0 ? day.meals.map(m => {
                  const sel = m.options.find(o => o.recipe_id === m.selected_recipe_id) || m.options[0];
                  return (
                    <span key={m.id} className="text-xs text-gray-600 truncate">
                      {sel?.recipe.name || m.meal_type}
                    </span>
                  );
                }) : (
                  <span className="text-xs text-gray-400">No meals</span>
                )}
              </div>
            </div>
          ))}
        </CardContent>
      )}
    </Card>
  );
}
