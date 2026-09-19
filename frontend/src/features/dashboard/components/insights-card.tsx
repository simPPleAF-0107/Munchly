"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api-client";
import type { BehavioralInsight } from "@/types/dashboard";

interface InsightsCardProps {
  insights: BehavioralInsight[];
  onAction: (id: string, action: "ACCEPT" | "DISMISS") => void;
}

export function InsightsCard({ insights, onAction }: InsightsCardProps) {
  if (insights.length === 0) return null;

  return (
    <Card className="border-orange-100 bg-orange-50/30">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">🧠 Munchly Learned...</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {insights.map(insight => (
          <div key={insight.id} className="bg-white rounded-lg p-3 border border-orange-100">
            <p className="text-sm text-gray-700 mb-2">{insight.message}</p>
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-400">
                Confidence: {Math.round(insight.confidence * 100)}%
              </span>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="ghost"
                  className="text-xs h-7"
                  onClick={() => onAction(insight.id, "DISMISS")}
                >
                  Dismiss
                </Button>
                <Button
                  size="sm"
                  className="text-xs h-7 bg-orange-600 hover:bg-orange-700"
                  onClick={() => onAction(insight.id, "ACCEPT")}
                >
                  ✅ Accept
                </Button>
              </div>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
