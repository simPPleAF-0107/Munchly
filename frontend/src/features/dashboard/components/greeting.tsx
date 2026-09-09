"use client";

import { useEffect, useState } from "react";

export function Greeting({ name }: { name: string }) {
  const [greeting, setGreeting] = useState("Good day");

  useEffect(() => {
    const hour = new Date().getHours();
    if (hour < 12) setGreeting("Good morning");
    else if (hour < 18) setGreeting("Good afternoon");
    else setGreeting("Good evening");
  }, []);

  return (
    <h1 className="text-2xl font-bold text-gray-900">
      {greeting}, {name}!
    </h1>
  );
}
