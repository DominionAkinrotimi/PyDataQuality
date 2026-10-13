# PyDataQuality website

The public landing page. Vite, React, TypeScript, Tailwind, Motion and react-three-fiber.

```bash
npm install
npm run dev      # local preview with live reload
npm run build    # writes dist/
```

Pushing to `main` deploys it to GitHub Pages (see `.github/workflows/site.yml`).

## How it is put together

- `npm run build` does three things: builds the site, builds a server copy of it, and runs
  `scripts/prerender.mjs`, which writes the finished page into `dist/index.html` along with the
  structured data for search engines. The text is there without JavaScript.
- In the browser the page is then woken up in stages (`src/lib/wake.ts`): the first screen at once,
  the sections below it one at a time while the browser is idle.
- `src/three/HeroScene.tsx` is the 3D scene in the hero. It is only fetched after the page has
  loaded, and only on devices that can run it. `src/components/HeroPoster.tsx` is the still version,
  drawn with CSS, shown first and kept on phones, low-power devices and under reduced motion.
- `src/assets/shots/` holds screenshots of the real app (`pdq ui`), captured at 1280 x 820 at 2x.
  Check, Result and Affected rows use the built-in sample file. The others use three small example
  files (a clean survey file, and an orders file for two months) made for the pictures.
- `public/og.png` is the picture shown when the link is shared. It is a capture of the hero.
- The grid and light are CSS. There are no stock or generated pictures.
- Fonts are bundled. Nothing is loaded from another site at runtime.

## Borrowed components

- `src/components/magicui` (blur-fade, border-beam) comes from
  [Magic UI](https://magicui.design) (MIT), as listed on 21st.dev.
- `TiltCard` in `src/components/ui.tsx` was written for this site after Aceternity UI's
  "3D Card Effect".

## Rules for the copy

No customer logos, testimonials or user counts until they are real, a source link for every number,
and the product's limits stated on the page. Say "file" and "spreadsheet".
