import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "./App";
import { useUi } from "./stores/ui";

import "./styles/tokens.css";
import "./styles/app.css";
import "./styles/rec.css";

// Applied before first paint so a dark-mode user never sees a light flash.
useUi.getState().applyTheme();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
