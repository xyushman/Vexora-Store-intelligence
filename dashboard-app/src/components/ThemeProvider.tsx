"use client";

import * as React from "react";
import { ThemeProvider as NextThemesProvider } from "next-themes";
import { useEffect } from "react";

export function ThemeProvider({
  children,
  ...props
}: React.ComponentProps<typeof NextThemesProvider>) {
  useEffect(() => {
    // Suppress specific React Three Fiber / Recharts warnings
    const originalConsoleError = console.error;
    const originalConsoleWarn = console.warn;

    console.error = (...args: any[]) => {
      if (
        typeof args[0] === "string" &&
        (args[0].includes("The width(-1) and height(-1) of chart should be greater than 0") ||
         args[0].includes("Program Info Log"))
      ) {
        return;
      }
      originalConsoleError(...args);
    };

    console.warn = (...args: any[]) => {
      if (
        typeof args[0] === "string" &&
        (args[0].includes("THREE.Clock: This module has been deprecated") ||
         args[0].includes("Program Info Log") ||
         args[0].includes("cannot be represented accurately in double precision"))
      ) {
        return;
      }
      originalConsoleWarn(...args);
    };

    return () => {
      console.error = originalConsoleError;
      console.warn = originalConsoleWarn;
    };
  }, []);

  return <NextThemesProvider {...props}>{children}</NextThemesProvider>;
}
