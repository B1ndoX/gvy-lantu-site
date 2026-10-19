import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { runInNewContext } from "node:vm";
import test from "node:test";

const data = JSON.parse(readFileSync(new URL("../data/blueprint-index.json", import.meta.url)));
const source = readFileSync(new URL("../assets/app.js", import.meta.url), "utf8").replace(/\nboot\(\);\s*$/, "");
function app() {
  const context = {document: {querySelector: () => null, querySelectorAll: () => []}, URL, URLSearchParams,
    window: {location: {href: "https://example.test/?private=value#blueprint=private-id"}}};
  runInNewContext(`${source}\nglobalThis.api = {state, prepareRecord, missionVariantKey, groupSourceMissions,
    recordMissions, initMissionRewards, renderSources, filterShareUrl, parseSharedFilters, normalizeFilterSelection,
    recordMatchesFilters, blueprintShareUrl, hasDismantleOutputs, craftPlanText, planMaterialQuantity, renderPlanBody};`, context);
  context.api.state.data = data;
  context.api.state.records = data.records.map(context.api.prepareRecord);
  return context.api;
}
const clone = value => JSON.parse(JSON.stringify(value));
const ids = (api, selection) => api.state.records.filter(record => (selection.mode !== "dismantle" || api.hasDismantleOutputs(record))
  && api.recordMatchesFilters(record, selection)).map(record => record.id);

test("source trailing chevrons center within their own row rather than the first text line", () => {
  const css = readFileSync(new URL("../assets/styles.css", import.meta.url), "utf8");
  const rule = css.match(/\.source-mission-button > span\s*\{([^}]+)\}/)[1];
  assert.match(rule, /top:\s*50%/);
  assert.match(rule, /transform:\s*translateY\(-50%\)/);
  assert.match(rule, /line-height:\s*1\s*;/);
  assert.doesNotMatch(rule, /top:\s*1px/);
});

test("filter links roundtrip exact public result membership and sorting without exporting private state", () => {
  const api = app();
  for (const changes of [{}, {size: "0"}, {size: "3", sort: "sources"},
    {category: "ship_component", componentType: "quantumdrive", grade: "2", sourceOnly: true},
    {query: "VK-00", sort: "name"}, {query: "斯坦顿"},
    {mode: "dismantle", material: "Borase", sourceOnly: true}]) {
    const initial = {...api.state, ...changes, favoritesOnly: true, favorites: new Set(["private-id"])};
    const list = initial.mode === "dismantle" ? api.state.records.filter(api.hasDismantleOutputs) : api.state.records;
    const normalized = api.normalizeFilterSelection(initial, list);
    const link = new URL(api.filterShareUrl(normalized));
    const params = new URLSearchParams(link.hash.slice(1));
    const result = api.parseSharedFilters(params);
    assert.equal(link.origin, "https://example.test");
    assert.equal(link.search, "");
    assert.equal(result.error, undefined);
    assert.equal(result.selection.favoritesOnly, false);
    assert.equal(result.selection.sort, normalized.sort);
    assert.equal(params.has("blueprint"), false);
    assert.doesNotMatch(link.href, /private|favorite|quality|craftPlan/);
    assert.deepEqual(ids(api, result.selection), ids(api, {...normalized, favoritesOnly: false}));
    assert.equal(result.adjusted, false);
    if (initial.mode === "dismantle") assert.equal(params.has("source"), false);
  }
});

test("filter links keep legitimate empty combinations and report unavailable fields or changed builds", () => {
  const api = app();
  const material = api.state.records.find(record => record.type === "cooler" && record.stats.grade === 2).tiers[0].slots[0].options[0].name;
  const params = new URLSearchParams({view: "filters", v: "1", mode: "craft", query: "ignored",
    q: "this-does-not-match-any-item", category: "ship_component", componentType: "cooler", grade: "2", material});
  const result = api.parseSharedFilters(params);
  assert.equal(result.adjusted, false);
  assert.equal(result.selection.material, material);
  assert.equal(result.selection.grade, "2");
  assert.equal(ids(api, result.selection).length, 0);
  params.set("material", "removed-material");
  params.set("live", "4.0.0-live.old");
  const obsolete = api.parseSharedFilters(params);
  assert.equal(obsolete.adjusted, true);
  assert.equal(obsolete.changedVersion, true);
  assert.equal(obsolete.selection.material, "all");
});

test("shared filters reject ambiguous or oversized links and ignore unapproved private keys", () => {
  const api = app();
  for (const suffix of ["v=9", "mode=unknown", "source=true", "sort=unsafe", "view=unknown", `q=${"a".repeat(1001)}`]) {
    const params = new URLSearchParams("view=filters&v=1&mode=craft");
    const [key, value] = suffix.split("=");
    params.set(key, value);
    assert.ok(api.parseSharedFilters(params).error, suffix.slice(0, 30));
  }
  const duplicate = new URLSearchParams("view=filters&v=1&mode=craft&size=1&size=3");
  assert.ok(api.parseSharedFilters(duplicate).error);
  const privateFields = new URLSearchParams("view=filters&v=1&mode=craft&favoritesOnly=1&favorites=secret&craftPlan=secret&__proto__=secret");
  const result = api.parseSharedFilters(privateFields);
  assert.equal(result.selection.favoritesOnly, false);
  assert.equal(Object.hasOwn(result.selection, "favorites"), false);
  assert.equal(Object.hasOwn(result.selection, "craftPlan"), false);
  assert.equal(Object.hasOwn(result.selection, "secret"), false);
  assert.throws(() => api.filterShareUrl({...api.state, query: "q".repeat(1001)}));
  const blueprint = new URL(api.blueprintShareUrl("exact-id", "dismantle"));
  assert.equal(blueprint.hash, "#blueprint=exact-id&mode=dismantle");
});

test("mission folding requires complete equal records, not just matching titles", () => {
  const api = app();
  const first = {id: "first", debugName: "identity-one", title: "Same title", systems: ["Nyx"], rewardUEC: 0, missionType: "Hauling"};
  const rewards = {requirements: {canBeShared: false, minStanding: {minReputation: 0}},
    items: [], pools: [{id: "pool", trigger: "complete", chance: 1}]};
  api.state.data = {missionRewards: {missions: {first: clone(rewards), second: clone(rewards)}}};
  const second = {...first, id: "second", debugName: "identity-two"};
  assert.equal(api.groupSourceMissions([first, second]).length, 1);
  assert.equal(api.groupSourceMissions([first, second])[0].length, 2);
  for (const mutation of [
    (m, r) => {m.systems = ["Pyro"];}, (m, r) => {m.rewardUEC = 1;},
    (m, r) => {m.missionType = "Mercenary";}, (m, r) => {m.futureField = "different";},
    (m, r) => {r.requirements.canBeShared = true;}, (m, r) => {delete r.requirements.canBeShared;},
    (m, r) => {r.pools[0].id = "other-pool";}, (m, r) => {r.pools[0].chance = 0;},
    (m, r) => {r.items = [{name: "extra", amount: 1}];}, (m, r) => {r.requirements = null;},
    (m, r) => {r.requirements.additionalRestrictions = ["requiredScenarios"];},
    (m, r) => {r.requirements.futureCondition = false;},
  ]) {
    const m = clone(second), r = clone(rewards);
    mutation(m, r);
    api.state.data.missionRewards.missions.second = r;
    assert.equal(api.groupSourceMissions([first, m]).length, 2);
  }
  api.state.data.missionRewards.missions.second = {};
  assert.equal(api.groupSourceMissions([first, second]).length, 2);
});

test("every real source keeps its exact task IDs, raw data, search and reward relations after folding", () => {
  const api = app();
  api.initMissionRewards();
  const before = JSON.stringify(data);
  let folded = 0;
  for (const record of api.state.records) {
    const missions = api.recordMissions(record);
    const groups = api.groupSourceMissions(missions);
    const flattened = Array.from(groups).flatMap(group => Array.from(group, m => m.id));
    assert.deepEqual(flattened.sort(), Array.from(missions, m => m.id).sort(), record.id);
    for (const group of groups) if (group.length > 1) {
      folded++;
      assert.ok(group.every(m => api.missionVariantKey(m) === api.missionVariantKey(group[0])));
    }
    const html = api.renderSources(record);
    assert.equal((html.match(/data-mission-id=/g) || []).length, missions.length, record.id);
    assert.equal((html.match(/data-source-variants=/g) || []).length, groups.filter(group => group.length > 1).length);
  }
  assert.ok(folded > 0);
  assert.equal(JSON.stringify(data), before);
  assert.equal(api.state.missions.size, 672);
  const vk = api.state.records.find(record => record.id === "33be7f1a-3f75-4627-bb8b-88e6d6b42f4e");
  const html = api.renderSources(vk);
  assert.match(html, /任务 16/);
  assert.match(html, /aria-expanded="false"/);
  assert.match(html, /class="source-missions source-variant-members"[^>]* hidden/);
  assert.doesNotMatch(html, /个变体|source-variant-label/);
});

test("copied plan matches displayed totals, units and separate quality minima without changing storage", () => {
  const api = app();
  api.state.records = [{id: "one", name: "One", category: {id: "test", label: "Test"}, stats: {}, tiers: [{craftTimeSeconds: 15, slots: [
    {options: [{kind: "resource", name: "Iron", quantity: 0.1, minQuality: 0}]},
    {options: [{kind: "resource", name: "Iron", quantity: 0.2, minQuality: 1}]},
    {options: [{kind: "item", name: "Core", quantity: 1, minQuality: 0}]},
  ]}]}];
  api.state.craftPlan = [{recordId: "one", quantity: 3, choices: {}}];
  const before = JSON.stringify(api.state.craftPlan);
  const text = api.craftPlanText(), html = api.renderPlanBody();
  assert.match(text, /One ×3/);
  assert.match(text, /0\.3 SCU · 至少 0/);
  assert.match(text, /0\.6 SCU · 至少 1/);
  assert.match(text, /3 件 · 至少 0/);
  assert.match(text, /清单总耗时 45 秒/);
  assert.match(text, /不含排队/);
  assert.match(html, /data-copy-plan/);
  assert.match(html, /data-plan-copy-fallback hidden/);
  assert.equal(JSON.stringify(api.state.craftPlan), before);
  assert.equal(api.planMaterialQuantity(0.000001), "0.000001");
  api.state.craftPlan.push({recordId: "removed", quantity: 2, choices: {}});
  assert.match(api.craftPlanText(), /当前版本未收录：removed/);
});
