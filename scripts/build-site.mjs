import { cp, copyFile, mkdir, rm } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const output = resolve(root, "dist");

await rm(output, { recursive: true, force: true });
await mkdir(resolve(output, "data"), { recursive: true });

for (const file of ["index.html", "favicon.ico", "robots.txt", "sitemap.xml"]) {
  await copyFile(resolve(root, file), resolve(output, file));
}

for (const file of ["blueprint-index.json", "mineral-locations.json"]) {
  await copyFile(resolve(root, "data", file), resolve(output, "data", file));
}

await cp(resolve(root, "assets"), resolve(output, "assets"), { recursive: true });
