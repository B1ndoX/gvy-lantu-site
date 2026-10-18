import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { runInNewContext } from "node:vm";
import test from "node:test";

function app(document = { querySelector: () => ({}), querySelectorAll: () => [] }) {
  const source = readFileSync(new URL("../assets/app.js", import.meta.url), "utf8").replace(/\nboot\(\);\s*$/, "");
  const context = { document };
  runInNewContext(`${source}\n globalThis.api = { state, initMissionRewards, missionSystemLabels, renderSources, renderMissionItems, renderMissionPools, openMissionInfo, recordSearchText, recordMissions };`, context);
  context.api.state.data = { missionRewards: { systems: [{ name: "Nyx", nameZh: "尼克斯" }, { name: "Pyro", nameZh: "派罗" }], missions: {} } };
  return context.api;
}

test("mission systems retain all values and explicitly mark missing data", () => {
  const api = app();
  assert.equal(api.missionSystemLabels({ systems: ["Nyx", "Pyro", "Nyx"] }), "尼克斯 (Nyx) / 派罗 (Pyro)");
  assert.equal(api.missionSystemLabels({}), "星系未注明");
  assert.equal(api.missionSystemLabels({ systems: ["Unknown"] }), "Unknown");
});

test("same names do not merge separate contract IDs, pool items are deduplicated", () => {
  const api = app();
  const mission = { id: "one", title: "Same", debugName: "same", systems: ["Nyx"] };
  api.state.records = [{ id: "bp", sources: [{ poolId: "pool", missions: [mission, { ...mission, id: "two" }] }] }];
  api.initMissionRewards();
  assert.equal(api.state.missions.size, 2);
  assert.equal(api.state.rewardPools.get("pool").size, 1);
});

test("each mission renders only its explicit pools as one draw per pool, not all items awarded", () => {
  const api = app();
  const nyx = { id: "nyx", title: "Same title", systems: ["Nyx"] };
  const pyro = { id: "pyro", title: "Same title", systems: ["Pyro"] };
  const records = (count, poolId, mission) => Array.from({ length: count }, (_, index) => ({
    id: `${poolId}-${index}`, name: `${poolId}-${index}`, category: { id: "test", label: "Test" },
    stats: {}, sources: [{ poolId, missions: [mission] }],
  }));
  api.state.records = [...records(17, "easy", nyx), ...records(7, "hard", nyx), ...records(3, "unrelated", pyro)];
  api.initMissionRewards();
  const html = api.renderMissionPools([{ id: "easy", chance: 1, trigger: "complete" },
    { id: "hard", chance: 0.5, trigger: "complete" }]);
  assert.match(html, /蓝图奖励池 1/);
  assert.match(html, /蓝图奖励池 2/);
  assert.match(html, /<strong>17 选 1<\/strong>/);
  assert.match(html, /<strong>7 选 1<\/strong>/);
  assert.match(html, /完成任务 · 池触发概率 100%/);
  assert.match(html, /池触发概率 50%/);
  assert.equal((html.match(/data-mission-blueprint=/g) || []).length, 24);
  assert.doesNotMatch(html, /unrelated|范围未确认|单张掉率|1\/17/);
  assert.match(api.renderMissionPools([{ id: "easy" }]), /池触发概率未注明/);
  assert.doesNotMatch(api.renderMissionPools([{ id: "missing" }]), /0 选 1/);
});

test("source rows show systems and task IDs without implying item drop certainty", () => {
  const api = app();
  api.state.data.missionRewards.missions.one = { pools: [] };
  const html = api.renderSources({ sources: [{ missionCount: 1, missions: [{ id: "one", title: "<script>[LOCATION]</script>", systems: ["Nyx"], chance: 1, rewardUEC: 0 }] }] });
  assert.match(html, /data-mission-id="one"/);
  assert.match(html, /aria-haspopup="dialog" title="查看任务奖励"/);
  assert.match(html, /尼克斯 \(Nyx\)/);
  assert.doesNotMatch(html, /100%|奖励池触发/);
  assert.match(html, /&lt;script&gt;\[地点\]&lt;\/script&gt;/);
  assert.doesNotMatch(html, /<script>/);
});

test("source pools share one compact task list, deduplicated by ID with eight initial rows", () => {
  const api = app();
  const missions = Array.from({ length: 10 }, (_, i) => ({ id: `task-${i}`, title: "Same title", systems: ["Nyx"] }));
  for (const mission of missions) api.state.data.missionRewards.missions[mission.id] = { pools: [] };
  const record = { sources: [{ missions: missions.slice(0, 6) }, { missions: missions.slice(5) }] };
  assert.equal(api.recordMissions(record).length, 10);
  const html = api.renderSources(record);
  const [initial, rest] = html.split('<details class="source-more">');
  assert.equal((html.match(/class="source-item"/g) || []).length, 1);
  assert.equal((initial.match(/data-mission-id=/g) || []).length, 8);
  assert.equal((rest.match(/data-mission-id=/g) || []).length, 2);
  assert.match(rest, /展开全部 10 条任务/);
  assert.match(rest, /收起更多任务/);
  assert.doesNotMatch(html, /<details[^>]* open/);
});

test("search includes localized systems and the displayed task title", () => {
  const api = app();
  const text = api.recordSearchText({ name: "Radar", category: { id: "ship_component", label: "舰船组件" },
    stats: {}, sources: [{ missions: [{ title: "Defend [LOCATION]", systems: ["Nyx"] }] }] });
  assert.match(text, /尼克斯/);
  assert.match(text, /nyx/);
  assert.match(text, /defend\[地点\]/);
});

test("direct and grouped item rewards preserve quantities and ownership conditions", () => {
  const api = app();
  const html = api.renderMissionItems([{ name: "Rifle", amount: 2, awardOnlyToMissionOwner: true },
    { type: "weighted_choice", groups: [{ probability: 0.5, items: [{ name: "Magazine", amount: 20 }] }] }]);
  assert.match(html, /×2/);
  assert.match(html, /×20/);
  assert.match(html, /仅任务拥有者/);
  assert.match(html, /备选物品组合 1/);
  assert.doesNotMatch(html, /50%|100%/);
  assert.match(api.renderMissionItems([]), /暂无已记录/);
});

test("mission dialog explains independent draws without hiding verified pools as unconfirmed", () => {
  let html = "";
  let shown = false;
  const dialog = { addEventListener() {}, showModal() { shown = true; } };
  const api = app({
    querySelector: (selector) => selector === ".mission-dialog" ? (html ? dialog : null) : {},
    querySelectorAll: () => [],
    body: { style: {}, insertAdjacentHTML: (_, value) => { html = value; } },
  });
  api.state.missions.set("mission", { title: "Same", systems: ["Nyx"] });
  api.state.data.missionRewards.missions.mission = { pools: [{ id: "first" }, { id: "second" }], items: [] };
  api.openMissionInfo("mission");
  assert.equal(shown, true);
  assert.match(html, /本任务含 2 个蓝图奖励池/);
  assert.match(html, /各池独立按对应条件及触发概率发放 1 张蓝图/);
  assert.match(html, /已集齐的池不再发放/);
  assert.match(html, /并非一次全部获得/);
  assert.match(html, /池触发概率不等于单张蓝图的掉率/);
  assert.doesNotMatch(html, /范围未确认|非已确认掉落清单|<details/);
});
