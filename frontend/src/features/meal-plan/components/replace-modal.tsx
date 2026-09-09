"use client";

import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";

const REASONS = [
  "Don't like this recipe",
  "Too expensive",
  "Takes too long to cook",
  "Had this recently",
  "Want something healthier",
  "Want something different",
  "Use ingredients I already have"
];

interface ReplaceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onReplace: (reason: string) => Promise<void>;
  isLoading: boolean;
}

export function ReplaceModal({ isOpen, onClose, onReplace, isLoading }: ReplaceModalProps) {
  const [reason, setReason] = useState(REASONS[0]);

  const handleSubmit = async () => {
    await onReplace(reason);
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Replace Meal</DialogTitle>
          <DialogDescription>
            Help us understand why you want to replace this meal so we can suggest better options.
          </DialogDescription>
        </DialogHeader>
        
        <div className="py-4">
          <RadioGroup value={reason} onValueChange={setReason} className="gap-3">
            {REASONS.map((r) => (
              <div key={r} className="flex items-center space-x-2">
                <RadioGroupItem value={r} id={r} />
                <Label htmlFor={r} className="font-normal">{r}</Label>
              </div>
            ))}
          </RadioGroup>
        </div>
        
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isLoading}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={isLoading} className="bg-orange-600 hover:bg-orange-700">
            {isLoading ? "Replacing..." : "Get New Options"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
