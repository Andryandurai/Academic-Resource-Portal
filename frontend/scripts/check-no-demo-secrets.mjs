#!/usr/bin/env node
/**
 * Security check, not a unit test — there is no JS test runner in this
 * project (see package.json), so this is a small, focused, standalone
 * script instead of new test infrastructure.
 *
 * Fails (non-zero exit) if the demo account credentials from
 * src/pages/auth/Login.tsx appear anywhere in a production build's output.
 * A clean run confirms VITE_SHOW_DEMO_ACCOUNTS was correctly left unset (or
 * false) for that build — see .env.example.
 *
 * Intentionally does NOT read VITE_SHOW_DEMO_ACCOUNTS itself: this script
 * checks the actual build artifact, not the env var's intent, so it also
 * catches a future change to Login.tsx that accidentally breaks the
 * dead-code-elimination this relies on.
 *
 * Usage: node scripts/check-no-demo-secrets.mjs   (run after `npm run build`)
 */

import { readdirSync, readFileSync, existsSync } from "node:fs";
import { join } from "node:path";

const DIST_ASSETS = join(import.meta.dirname, "..", "dist", "assets");

// Kept in sync with the literals in src/pages/auth/Login.tsx's DEMO_ACCOUNTS.
// Not a secret itself — these are the same public demo values documented
// throughout this project; the point of this script is confirming they do
// NOT end up in a default production build, not hiding what they are.
const FORBIDDEN_STRINGS = ["andyandy1234", "trial1234", "student@rec.local"];

if (!existsSync(DIST_ASSETS)) {
  console.error(`No build found at ${DIST_ASSETS} — run "npm run build" first.`);
  process.exit(1);
}

const jsFiles = readdirSync(DIST_ASSETS).filter((f) => f.endsWith(".js"));
if (jsFiles.length === 0) {
  console.error(`No .js files found under ${DIST_ASSETS} — build may have failed.`);
  process.exit(1);
}

let found = false;
for (const file of jsFiles) {
  const content = readFileSync(join(DIST_ASSETS, file), "utf-8");
  for (const needle of FORBIDDEN_STRINGS) {
    if (content.includes(needle)) {
      console.error(`FOUND "${needle}" in dist/assets/${file}`);
      found = true;
    }
  }
}

if (found) {
  console.error(
    "\nDemo credentials are present in this build. If this is a deliberate " +
      "demo/grading deployment, this is expected (VITE_SHOW_DEMO_ACCOUNTS=true) " +
      "— otherwise, rebuild without that variable set.",
  );
  process.exit(1);
}

console.log(`OK — no demo credential strings found in ${jsFiles.length} built JS file(s).`);
