import { defineConfig, globalIgnores } from "eslint/config";
import nextCoreWebVitals from "eslint-config-next/core-web-vitals";

/** @see https://react.dev/learn/you-might-not-need-an-effect — many valid patterns still use setState in effects; React Compiler rules are overly strict for this codebase. */
export default defineConfig([
  ...nextCoreWebVitals,
  {
    name: "stocky-react-hooks-pragmatic",
    files: ["**/*.{js,jsx,mjs,ts,tsx,mts,cts}"],
    rules: {
      "react-hooks/set-state-in-effect": "off",
      "react-hooks/immutability": "off",
    },
  },
  {
    name: "stocky-tests",
    files: ["**/__tests__/**", "**/*.{test,spec}.{ts,tsx}"],
    rules: {
      "react/display-name": "off",
    },
  },
  globalIgnores([
    ".next/**",
    "node_modules/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    "coverage/**",
  ]),
]);
