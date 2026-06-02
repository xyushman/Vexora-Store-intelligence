"use client";

import { useTheme } from "next-themes";
import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";

export default function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMounted(true);
  }, []);

  if (!mounted) {
    return <div className="w-9 h-9" />; // Placeholder to avoid hydration mismatch
  }

  return (
    <button
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
      className="relative flex items-center justify-center w-10 h-10 rounded-full border border-gray-200 dark:border-gray-800 bg-white dark:bg-black/50 backdrop-blur-md shadow-sm hover:scale-105 transition-all duration-300"
      aria-label="Toggle theme"
    >
      <div className="relative flex items-center justify-center w-full h-full text-[var(--foreground)]">
        {theme === "dark" ? (
          <Sun size={16} strokeWidth={2} />
        ) : (
          <Moon size={16} strokeWidth={2} />
        )}
      </div>
    </button>
  );
}
