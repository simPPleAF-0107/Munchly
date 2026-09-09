"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Calendar, ShoppingCart, User } from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { name: "Home", href: "/dashboard", icon: Home },
  { name: "Meal Plan", href: "/dashboard/meal-plan", icon: Calendar },
  { name: "Grocery", href: "/dashboard/grocery", icon: ShoppingCart },
  { name: "Profile", href: "/dashboard/profile", icon: User },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex h-screen bg-stone-50 overflow-hidden">
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex flex-col w-64 border-r bg-white p-4 shrink-0">
        <div className="text-2xl font-bold text-orange-600 mb-8 px-2">Munchly</div>
        <nav className="flex flex-col gap-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link key={item.name} href={item.href}>
                <div
                  className={cn(
                    "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors",
                    isActive ? "bg-orange-100 text-orange-700 font-medium" : "text-gray-600 hover:bg-orange-50 hover:text-orange-600"
                  )}
                >
                  <Icon className="w-5 h-5" />
                  {item.name}
                </div>
              </Link>
            );
          })}
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto pb-20 md:pb-0 relative">
        <div className="md:hidden flex items-center h-14 border-b bg-white px-4 sticky top-0 z-10">
          <div className="text-xl font-bold text-orange-600">Munchly</div>
        </div>
        <div className="p-4 md:p-8 max-w-5xl mx-auto h-full">
          {children}
        </div>
      </main>

      {/* Mobile Bottom Nav */}
      <nav className="md:hidden fixed bottom-0 w-full bg-white border-t flex justify-around p-2 pb-safe z-20">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          return (
            <Link key={item.name} href={item.href} className="w-full">
              <div
                className={cn(
                  "flex flex-col items-center gap-1 p-2 rounded-lg transition-colors",
                  isActive ? "text-orange-600" : "text-gray-500"
                )}
              >
                <Icon className={cn("w-6 h-6", isActive && "fill-orange-50 text-orange-600")} />
                <span className="text-[10px] font-medium">{item.name}</span>
              </div>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
