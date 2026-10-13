import { StrictMode } from "react";
import { renderToString } from "react-dom/server";
import { App } from "./App";
import { FAQ } from "./sections/Closing";

/** Used by scripts/prerender.mjs at build time to write the page into dist/index.html. */
export function render(): string {
  return renderToString(
    <StrictMode>
      <App />
    </StrictMode>,
  );
}

export const faq = FAQ;
