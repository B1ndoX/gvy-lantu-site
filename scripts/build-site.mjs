import { createHash } from "node:crypto";
import { cp, copyFile, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";
import { gzip } from "node:zlib";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const output = resolve(root, "dist");
const gzipAsync = promisify(gzip);
const dataFiles = ["blueprint-index.json", "mineral-locations.json"];
const dataVersionPlaceholder = "__BUILD_DATA_VERSION__";

const hash = (contents, length = 12) =>
  createHash("sha256").update(contents).digest("hex").slice(0, length);

const dataContents = new Map(
  await Promise.all(
    dataFiles.map(async (file) => [file, await readFile(resolve(root, "data", file))]),
  ),
);
const dataHasher = createHash("sha256");
for (const file of dataFiles) {
  dataHasher.update(`${file}\0`);
  dataHasher.update(dataContents.get(file));
  dataHasher.update("\0");
}
const dataVersion = `data-${dataHasher.digest("hex").slice(0, 16)}`;

const sourceApp = await readFile(resolve(root, "assets/app.js"), "utf8");
const placeholderCount = sourceApp.split(dataVersionPlaceholder).length - 1;
if (placeholderCount !== 1) {
  throw new Error(
    `assets/app.js must contain exactly one ${dataVersionPlaceholder} placeholder; found ${placeholderCount}`,
  );
}
const builtApp = sourceApp.replace(dataVersionPlaceholder, dataVersion);
const styles = await readFile(resolve(root, "assets/styles.css"));
const stylesVersion = hash(styles);
const appVersion = hash(builtApp);

await rm(output, { recursive: true, force: true });
await mkdir(resolve(output, "data"), { recursive: true });

for (const file of ["favicon.ico", "robots.txt", "sitemap.xml"]) {
  await copyFile(resolve(root, file), resolve(output, file));
}

const indexHtml = (await readFile(resolve(root, "index.html"), "utf8"))
  .replace(/\.\/assets\/styles\.css(?:\?v=[^"']*)?/, `./assets/styles.css?v=${stylesVersion}`)
  .replace(/\.\/assets\/app\.js(?:\?v=[^"']*)?/, `./assets/app.js?v=${appVersion}`);
await writeFile(resolve(output, "index.html"), indexHtml);

for (const file of dataFiles) {
  const contents = dataContents.get(file);
  const destination = resolve(output, "data", file);
  await writeFile(destination, contents);
  await writeFile(`${destination}.gz`, await gzipAsync(contents, { level: 9 }));
}

await cp(resolve(root, "assets"), resolve(output, "assets"), { recursive: true });
await writeFile(resolve(output, "assets/app.js"), builtApp);

console.log(`Built production assets with data revision ${dataVersion}.`);
