"use client";

import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

interface DaySelectorProps {
  selectedDay: number; // 1-7
  onSelect: (day: number) => void;
}

export function DaySelector({ selectedDay, onSelect }: DaySelectorProps) {
  return (
    <ScrollArea className="w-full whitespace-nowrap">
      <div className="flex w-max space-x-2 p-1">
        {DAYS.map((day, idx) => {
          const dayNum = idx + 1;
          const isSelected = selectedDay === dayNum;
          return (
            <button
              key={day}
              onClick={() => onSelect(dayNum)}
              className={cn(
                "px-4 py-2 rounded-full text-sm font-medium transition-colors",
                isSelected 
                  ? "bg-orange-600 text-white shadow-sm" 
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              )}
            >
              {day}
            </button>
          );
        })}
      </div>
      <ScrollBar orientation="horizontal" className="invisible" />
    </ScrollArea>
  );
}
