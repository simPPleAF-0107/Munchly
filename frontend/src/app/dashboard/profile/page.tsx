"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api-client";
import { UserResponse } from "@/types/api";
import { UserProfile } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { User, Settings, CreditCard, LogOut } from "lucide-react";
import { useRouter } from "next/navigation";
import { formatCurrency } from "@/lib/utils";
import { getLabel, DIET_TYPES, CUISINES } from "@/lib/constants";

export default function ProfilePage() {
  const router = useRouter();
  const [user, setUser] = useState<UserResponse | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [userData, profileData] = await Promise.all([
          apiClient.get<UserResponse>("/auth/me"),
          apiClient.get<UserProfile>("/users/profile").catch(() => null),
        ]);
        setUser(userData);
        if (profileData) setProfile(profileData);
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, []);

  const handleSignOut = () => {
    localStorage.removeItem("token");
    router.push("/");
  };

  if (isLoading) {
    return <div className="flex h-64 items-center justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600" /></div>;
  }

  if (!user) return null;

  return (
    <div className="space-y-6 max-w-2xl mx-auto pb-8 animate-in fade-in">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Profile Settings</h1>
      
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center text-orange-600">
              <User className="w-8 h-8" />
            </div>
            <div className="flex-1">
              <h2 className="text-xl font-bold">{profile?.name || "User"}</h2>
              <p className="text-gray-500">{user.email}</p>
            </div>
            <Badge variant="secondary" className="bg-gradient-to-r from-orange-400 to-orange-600 text-white border-0">
              {user.subscription_tier || "Free Plan"}
            </Badge>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Settings className="w-5 h-5 text-gray-500" />
              Preferences
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="text-sm text-gray-500">Diet Type</div>
              <div className="font-medium capitalize">{profile?.health_goal ? getLabel(DIET_TYPES, profile.health_goal) : "Not set"}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Health Goal</div>
              <div className="font-medium">{profile?.health_goal || "Not set"}</div>
            </div>
            <Button variant="outline" className="w-full mt-2" onClick={() => router.push("/onboarding")}>
              Update Preferences
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <CreditCard className="w-5 h-5 text-gray-500" />
              Budget & Goals
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="text-sm text-gray-500">Weekly Budget</div>
              <div className="font-medium">{formatCurrency(profile?.weekly_grocery_limit || 0, profile?.weekly_grocery_limit_currency || "INR")}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Activity Level</div>
              <div className="font-medium">
                {profile?.activity_level || "Not set"}
              </div>
            </div>
            <Button variant="outline" className="w-full mt-2">
              Edit Budget
            </Button>
          </CardContent>
        </Card>
      </div>

      <div className="pt-6 border-t flex justify-center">
        <Button variant="ghost" className="text-red-600 hover:text-red-700 hover:bg-red-50" onClick={handleSignOut}>
          <LogOut className="w-4 h-4 mr-2" />
          Sign Out
        </Button>
      </div>
    </div>
  );
}

