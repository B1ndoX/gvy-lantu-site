import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { runInNewContext } from "node:vm";
import test from "node:test";

const data = JSON.parse(readFileSync(new URL("../data/blueprint-index.json", import.meta.url)));
const source = readFileSync(new URL("../assets/app.js", import.meta.url), "utf8").replace(/\nboot\(\);\s*$/, "");
const context = { document: { querySelector: () => null, querySelectorAll: () => [] }, window: {}, URL, URLSearchParams };
runInNewContext(`${source}\nglobalThis.api = {state, prepareRecord, recordFilterValues, normalizeFilterSelection, recordMatchesFilters, buildFilterModel, optionTag, activeFilterCount};`, context);
const api = context.api;
api.state.data = data;
const records = data.records.map(api.prepareRecord);
const initial = { ...api.state };
const selection = (changes = {}, list = records) => api.normalizeFilterSelection({ ...initial, ...changes }, list);
const matches = (filters, list = records) => list.filter((record) => api.recordMatchesFilters(record, filters));

test("ship weapons disable component grades and clear stale B without losing weapons", () => {
  const filters = selection({ category: "ship_weapon", grade: "2" });
  assert.equal(filters.grade, "none");
  assert.equal(filters.componentClass, "none");
  assert.equal(filters.componentType, "none");
  assert.equal(matches(filters).length, data.records.filter((record) => record.category.id === "ship_weapon").length);
  assert.equal(api.buildFilterModel(records, filters).grade.disabled, true);
});

test("grade-only selection ignores unrelated armor and weapon internal grade fields", () => {
  const filters = selection({ grade: "2" });
  const result = matches(filters);
  assert.ok(result.length > 0);
  assert.ok(result.every((record) => record.category.id === "ship_component" && record.stats.grade === 2));
  assert.equal(result.length, records.filter((record) => record.category.id === "ship_component" && record.stats.grade === 2).length);
});

test("size-only selection crosses supported ship categories, not FPS internal sizes", () => {
  const filters = selection({ size: "3" });
  assert.equal(filters.category, "all");
  const expected = records.filter((record) => ["ship_component", "ship_weapon"].includes(record.category.id) && record.stats.size === 3);
  assert.deepEqual(matches(filters).map((record) => record.id), expected.map((record) => record.id));
  assert.ok(matches(filters).some((record) => record.category.id === "ship_weapon"));
  assert.ok(matches(filters).some((record) => record.category.id === "ship_component"));
});

test("size options contain actual sparse values, retaining true zero but not missing values", () => {
  const make = (id, size) => ({ id, name: id, category: { id: "ship_weapon" }, stats: { size }, tiers: [] });
  const list = [make("zero", 0), make("three", 3), make("five", 5), make("missing", null)];
  const filters = selection({}, list);
  assert.deepEqual(Array.from(api.buildFilterModel(list, filters).size.options, (option) => option.value), ["all", "0", "3", "5"]);
  assert.deepEqual(matches(selection({ size: "0" }, list), list).map((record) => record.id), ["zero"]);
  assert.equal(matches(filters, list).length, 4);
});

test("parent switches clear unavailable size but retain a still-applicable grade", () => {
  const filters = selection({ category: "ship_component", componentType: "quantumdrive", size: "5", grade: "2" });
  assert.equal(filters.size, "all");
  assert.equal(filters.grade, "2");
  const sizes = api.buildFilterModel(records, filters).size.options.map((option) => option.value);
  assert.ok(!sizes.includes("5"));
  assert.ok(!sizes.includes("0"));
  const armor = selection({ category: "armor", size: "3", grade: "2" });
  assert.equal(armor.size, "none");
  assert.equal(armor.grade, "none");
});

test("specialized ship tools do not expose meaningless grade or class choices", () => {
  for (const componentType of ["mininglaser", "miningmodule", "salvage", "refuelling", "tractorbeam", "orepod"]) {
    const filters = selection({ category: "ship_component", componentType, grade: "4", componentClass: "Military" });
    assert.equal(filters.grade, "none", componentType);
    assert.equal(filters.componentClass, "none", componentType);
    assert.ok(matches(filters).length > 0, componentType);
  }
});

test("material counts deduplicate repeated slot inputs and use recipe mode", () => {
  const record = { id: "one", name: "One", category: { id: "ship_weapon" }, stats: { size: 3 },
    tiers: [{ slots: [{ options: [{ name: "Iron" }] }, { options: [{ name: "Iron" }] }] }],
    dismantle: { outputs: [{ name: "Tin" }] } };
  for (const [mode, material] of [["craft", "Iron"], ["dismantle", "Tin"]]) {
    const filters = selection({ mode }, [record]);
    const options = api.buildFilterModel([record], filters).material.options;
    assert.deepEqual(Array.from(options, (option) => [option.value, option.count]), [["all", 1], [material, 1]]);
  }
});

test("facet counts equal the actual normalized click result, including parent switches", () => {
  const states = [selection(), selection({ category: "ship_weapon", size: "3" }),
    selection({ category: "ship_component", componentType: "cooler", grade: "2" }),
    selection({ category: "ship_component", componentType: "quantumdrive", sourceOnly: true }),
    selection({ query: "VK-00" }), selection({ favoritesOnly: true, favorites: new Set(records.slice(0, 5).map((record) => record.id)) })];
  for (const filters of states) {
    const model = api.buildFilterModel(records, filters);
    for (const [key, facet] of Object.entries(model)) {
      if (facet.disabled) continue;
      for (const option of facet.options) {
        const next = api.normalizeFilterSelection({ ...filters, [key]: option.value }, records);
        assert.equal(option.count, matches(next).length, `${filters.category}/${filters.componentType}: ${key}=${option.value}`);
      }
    }
  }
});

test("own facet does not lock alternatives; zero choices are disabled but remain clearable", () => {
  const filters = selection({ category: "ship_component", componentType: "cooler", grade: "2" });
  const options = api.buildFilterModel(records, filters).grade.options;
  assert.ok(options.find((option) => option.value === "1").count > 0);
  assert.match(api.optionTag("2", "B", 0, "1"), / disabled aria-disabled="true"/);
  assert.doesNotMatch(api.optionTag("2", "B", 0, "2"), / disabled/);
  assert.doesNotMatch(api.optionTag("all", "全部", 0, "2"), / disabled/);
});

test("all counts include records without a value and exclude duplicate mission types", () => {
  const filters = selection({ category: "ship_component", componentType: "cooler" });
  const model = api.buildFilterModel(records, filters);
  assert.equal(model.grade.options[0].count, matches(filters).length);
  const noResults = selection({ query: "__no_such_blueprint__", grade: "2" });
  assert.equal(api.buildFilterModel(records, noResults).grade.options[0].count, 0);
  assert.equal(noResults.grade, "2");
});

test("disabled none fields do not count as active filters", () => {
  Object.assign(api.state, selection({ category: "armor" }));
  assert.equal(api.activeFilterCount(), 1);
  Object.assign(api.state, selection({ size: "3" }));
  assert.equal(api.activeFilterCount(), 1);
});

test("raw unique blueprint membership independently verifies material and mission counts", () => {
  for (const mode of ["craft", "dismantle"]) {
    const list = mode === "craft" ? records : records.filter((record) => record.dismantle?.outputs?.length);
    for (const category of ["all", "ship_component", "ship_weapon", "armor"]) {
      const filters = selection({ mode, category }, list);
      const scope = data.records.filter((record) => (mode === "craft" || record.dismantle?.outputs?.length)
        && (category === "all" || record.category.id === category));
      const model = api.buildFilterModel(list, filters);
      for (const key of ["material", "missionType", "manufacturer", "size"]) {
        if (model[key].disabled) continue;
        for (const option of model[key].options) {
          const expected = scope.filter((record) => {
            if (option.value === "all") return true;
            if (key === "manufacturer") return record.manufacturer === option.value;
            if (key === "size") return ["ship_component", "ship_weapon"].includes(record.category.id)
              && record.stats.size !== null && record.stats.size !== undefined && String(record.stats.size) === option.value;
            if (key === "material") {
              const inputs = mode === "craft" ? (record.tiers[0]?.slots || []).flatMap((slot) => slot.options) : record.dismantle.outputs;
              return inputs.some((item) => item.name === option.value);
            }
            return record.sources.some((source) => source.missions.some((mission) => mission.missionType === option.value));
          }).length;
          assert.equal(option.count, expected, `${mode}/${category}/${key}/${option.value}`);
        }
      }
    }
  }
});

test("filter preparation preserves every raw snapshot field", () => {
  for (let index = 0; index < records.length; index++) {
    const { _filterValues, _searchText, ...raw } = records[index];
    assert.deepEqual(raw, data.records[index]);
  }
});
