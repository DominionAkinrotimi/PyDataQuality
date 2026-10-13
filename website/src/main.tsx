import { StrictMode } from "react";
import { createRoot, hydrateRoot } from "react-dom/client";
import "./index.css";
import { App, STAGES } from "./App";
import { wakeInStages } from "./lib/wake";

const container = document.getElementById("root")!;
const page = (
  <StrictMode>
    <App />
  </StrictMode>
);

if (container.firstElementChild) {
  // The built site already has the page written into its HTML. Let the browser paint that first,
  // then wake it up, so the first screen never waits for the script.
  requestAnimationFrame(() => setTimeout(() => {
    wakeInStages(STAGES);
    hydrateRoot(container, page);
  }, 0));
} else {
  // In development the page is empty and is drawn from scratch.
  createRoot(container).render(page);
}
