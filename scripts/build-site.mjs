import { cp, copyFile, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";
import { gzip } from "node:zlib";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const output = resolve(root, "dist");
const gzipAsync = promisify(gzip);

await rm(output, { recursive: true, force: true });
await mkdir(resolve(output, "data"), { recursive: true });

for (const file of ["index.html", "favicon.ico", "robots.txt", "sitemap.xml"]) {
  await copyFile(resolve(root, file), resolve(output, file));
}

for (const file of ["blueprint-index.json", "mineral-locations.json"]) {
  const source = resolve(root, "data", file);
  const destination = resolve(output, "data", file);
  const contents = await readFile(source);
  await copyFile(source, destination);
  await writeFile(`${destination}.gz`, await gzipAsync(contents, { level: 9 }));
}

await cp(resolve(root, "assets"), resolve(output, "assets"), { recursive: true });
