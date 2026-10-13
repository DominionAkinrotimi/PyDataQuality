# PyDataQuality website

The public landing page. Vite, React, TypeScript, Tailwind, Motion and react-three-fiber.

```bash
npm install
npm run dev      # local preview with live reload
npm run build    # writes dist/
```

Pushing to `main` deploys it to GitHub Pages (see `.github/workflows/site.yml`).

## How it is put together

- `src/three/HeroScene.tsx` is the 3D scene in the hero. It is a separate file that is only fetched
  after the page has loaded, and only on devices that can run it. `src/components/HeroPoster.tsx` is
  the still version, drawn with CSS, that is shown first and stays in place on low-power devices and
  when the visitor prefers reduced motion. Phones also keep the still version. Both draw the sheet described in `src/lib/sheet.ts`.
- The sections below the first screen are added one at a time while the browser is idle
  (`useStagedSections` in `src/main.tsx`), and are laid out only when they come near the viewport
  (`.later` in `src/index.css`). This keeps the page responsive while it loads on a slow phone.
- `src/assets/shots/` holds screenshots of the real app (`pdq ui`) checking its built-in sample
  file, captured at 1280 x 820 at 2x. To retake them, run `pdq ui --no-browser --port 8765`, open
  the sample file, and capture the Check, Result, Affected rows and Save as normal screens.
- The grid, light and paper grain are CSS and inline SVG (`src/index.css`). There are no stock or
  generated pictures.
- Fonts are bundled. Nothing is loaded from another site at runtime.

## Borrowed components

- `src/components/magicui` (blur-fade, border-beam, number-ticker) comes from
  [Magic UI](https://magicui.design) (MIT), as listed on 21st.dev.
- `TiltCard` in `src/components/ui.tsx` was written for this site after Aceternity UI's
  "3D Card Effect".

## Rules for the copy

No customer logos, testimonials or user counts until they are real, a source link for every number,
and the product's limits stated on the page. Say "file" and "spreadsheet".
