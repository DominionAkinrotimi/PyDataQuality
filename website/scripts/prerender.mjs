// Writes the finished page into dist/index.html, so the text is there without JavaScript and for
// search engines. Also adds the structured data that describes the software and its questions.
// Run by "npm run build" after the two Vite builds.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const SITE = "https://dominionakinrotimi.github.io/PyDataQuality/";

const { render, faq } = await import(pathToFileURL(path.join(root, "dist-ssr", "entry-server.js")).href);

const software = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  name: "PyDataQuality",
  description: "Checks a CSV or Excel file for duplicates, impossible values, broken dates and other problems, and says in plain sentences whether it is safe to use. Runs on your own computer.",
  url: SITE,
  applicationCategory: "BusinessApplication",
  operatingSystem: "Windows, macOS, Linux",
  softwareRequirements: "Python 3.8 or newer",
  license: "https://opensource.org/licenses/MIT",
  isAccessibleForFree: true,
  offers: { "@type": "Offer", price: "0", priceCurrency: "USD" },
  author: { "@type": "Person", name: "Dominion Akinrotimi" },
  codeRepository: "https://github.com/DominionAkinrotimi/PyDataQuality",
  downloadUrl: "https://pypi.org/project/pydataquality/",
  screenshot: SITE + "og.png",
};

const questions = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  mainEntity: faq.map(([question, answer]) => ({
    "@type": "Question",
    name: question,
    acceptedAnswer: { "@type": "Answer", text: answer },
  })),
};

const json = (data) => `<script type="application/ld+json">${JSON.stringify(data).replace(/</g, "\\u003c")}</script>`;

const file = path.join(root, "dist", "index.html");
let html = fs.readFileSync(file, "utf8");
if (!html.includes('<div id="root"></div>')) throw new Error("dist/index.html has no empty #root to fill");
// The server build writes asset addresses from the site root. The site is served from a
// sub-folder, so make them relative, as the browser build does.
const page = render().replace(/(["\s,])\/assets\//g, "$1./assets/");
html = html.replace('<div id="root"></div>', () => `<div id="root">${page}</div>`);
html = html.replace("</head>", `    ${json(software)}\n    ${json(questions)}\n  </head>`);
fs.writeFileSync(file, html);
fs.rmSync(path.join(root, "dist-ssr"), { recursive: true, force: true });
console.log(`prerendered dist/index.html (${Math.round(html.length / 1024)} kB)`);
