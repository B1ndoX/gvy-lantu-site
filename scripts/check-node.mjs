import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const root = new URL("../", import.meta.url);
const expected = (await readFile(new URL(".node-version", root), "utf8")).trim();
assert.match(expected, /^24\.\d+\.\d+$/);
assert.equal((await readFile(new URL(".nvmrc", root), "utf8")).trim(), expected, ".nvmrc must match .node-version");
const manifest = JSON.parse(await readFile(new URL("package.json", root), "utf8"));
const cloud = JSON.parse(await readFile(new URL("edgeone.json", root), "utf8"));
assert.equal(manifest.engines?.node, expected, "package.json must require the canonical Node version");
assert.equal(cloud.nodeVersion, expected, "edgeone.json must use the canonical Node version");
const lockText = await readFile(new URL("package-lock.json", root), "utf8").catch(error => {
  if (error.code === "ENOENT") return null;
  throw error;
});
if (lockText) {
  assert.equal(JSON.parse(lockText).packages?.[""]?.engines?.node, expected, "package-lock.json must use the canonical Node version");
} else {
  assert.equal(Object.keys({ ...manifest.dependencies, ...manifest.devDependencies }).length, 0, "Projects with npm dependencies must keep their lockfile");
}
assert.equal(process.versions.node, expected, `Use Node ${expected}; actual Node is ${process.versions.node}`);
console.log(`Verified Node ${process.versions.node} on ${process.platform}/${process.arch}`);
