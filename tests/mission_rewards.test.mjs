import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { runInNewContext } from "node:vm";
import test from "node:test";

function app(document = { querySelector: () => ({}), querySelectorAll: () => [] }) {
  const source = readFileSync(new URL("../assets/app.js", import.meta.url), "utf8").replace(/\nboot\(\);\s*$/, "");
  const context = { document, window: { getComputedStyle: () => ({ lineHeight: "14px" }) } };
  runInNewContext(`${source}\n globalThis.api = { state, initMissionRewards, missionSystemLabels, renderSources, renderMissionItems, renderMissionPools, renderMissionRequirements, renderBaseStats, renderQualitySummaryContent, renderDismantle, openMissionInfo, recordSearchText, recordMissions, recordWeaponType, recordClassGrade, recordSummary, renderRecordSummary, fitRecordSummaries, recordType };`, context);
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

test("source pools share one compact task list, deduplicated by ID with twelve initial rows", () => {
  const api = app();
  const missions = Array.from({ length: 20 }, (_, i) => ({ id: `task-${i}`, title: "Same title", systems: ["Nyx"] }));
  for (const mission of missions) api.state.data.missionRewards.missions[mission.id] = { pools: [] };
  const record = { sources: [{ missions: missions.slice(0, 6) }, { missions: missions.slice(5) }] };
  assert.equal(api.recordMissions(record).length, 20);
  const html = api.renderSources(record);
  const [initial, rest] = html.split('<details class="source-more">');
  assert.equal((html.match(/class="source-item"/g) || []).length, 1);
  assert.equal((initial.match(/data-mission-id=/g) || []).length, 12);
  assert.equal((rest.match(/data-mission-id=/g) || []).length, 8);
  assert.match(rest, /展开全部 20 条任务/);
  assert.match(rest, /收起更多任务/);
  assert.doesNotMatch(html, /<details[^>]* open/);
});

test("small task tails are shown directly, never hidden behind a two-row expansion", () => {
  const api = app();
  for (const count of [8, 10, 11, 12, 14, 15, 16, 96]) {
    const missions = Array.from({length: count}, (_, i) => ({id: `task-${i}`, title: `Task ${i}`}));
    for (const mission of missions) api.state.data.missionRewards.missions[mission.id] = {pools: []};
    const html = api.renderSources({sources: [{missions}]});
    if (count <= 15) {
      assert.doesNotMatch(html, /class="source-more"/);
      assert.equal((html.match(/data-mission-id=/g) || []).length, count);
    } else {
      assert.equal((html.split('<details class="source-more">')[0].match(/data-mission-id=/g) || []).length, 12);
      assert.match(html, /class="source-more"/);
    }
  }
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
  assert.match(html, /物品组合 1/);
  assert.match(html, /组合选择概率 50%/);
  assert.match(html, /作为一组一起发放/);
  assert.match(api.renderMissionItems([]), /暂无已记录/);
});

test("mission dialog explains independent draws without hiding verified pools as unconfirmed", () => {
  let html = "";
  let shown = false;
  const dialog = { addEventListener() {}, querySelectorAll() { return []; }, showModal() { shown = true; } };
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
  assert.match(html, /不保证 N 次集齐/);
  assert.doesNotMatch(html, /范围未确认|非已确认掉落清单|<details/);
});

test("compact class-grade labels preserve verified classes without inventing a weapon class", () => {
  const api = app();
  for (const [itemClass, grade, expected] of [["Military",1,"军A"],["Stealth",1,"隐A"],["Industrial",3,"工C"],["Civilian",2,"民B"],["Competition",4,"竞D"],
    [undefined,1,"A"],["Unknown",2,"B"],["Military",null,"军"],[undefined,null,""]]) {
    assert.equal(api.recordClassGrade({flowcld:{itemClass},stats:{grade}}),expected);
  }
});

test("specific ship weapon types use the primary subtype and a verified family, never a generic laser cannon for every weapon", () => {
  const api=app();
  const weapon=(name,subtype,label,tags="")=>({name,category:{id:"ship_weapon",label:"舰船武器"},subtype,zh:{subtype:label},stats:{tags}});
  for(const [name,subtype,label,tags,expected] of [
    ["M7A Cannon","laser","激光","LaserCannon","激光加农炮"],
    ["Singe Cannon (S1)","tachyon","快子","BANU_TachyonCannon","快子加农炮"],
    ["Attrition-1 Repeater","laser","激光","LaserRepeater","激光速射炮"],
    ["Tigerstrike T-19P","ballistic","实弹","BallisticGatling","实弹加特林"],
    ["Dominance-1 Scattergun","laser","激光","ScatterGun","激光霰弹炮"],
    ["NN-13 Cannon","neutron","中子","NeutronCannon","中子加农炮"],
    ["Sledge I Mass Driver Cannon","ballistic","实弹","MassDriver","质量驱动炮"],
    ["FL-22 Cannon","laser","激光","DistortionCannon","激光加农炮"],
    ["Unknown Model","laser","激光","","激光"],
    ["Unknown Cannon","new-subtype","新类型","LaserCannon","新类型"],
  ]) {
    const record=weapon(name,subtype,label,tags);
    assert.equal(api.recordWeaponType(record),expected,name);
    assert.equal(api.recordType(record),expected,name);
  }
  assert.equal(api.recordWeaponType({name:"Laser Rifle",category:{id:"personal_weapon"},subtype:"rifle",zh:{subtype:"步枪"}}),"步枪");
});

test("reward and result summaries show compact grades, escape text and index both full and short types", () => {
  const api=app();
  const cooler={name:"Cooler",category:{id:"ship_component",label:"舰船组件"},type:"cooler",stats:{size:1,grade:1},flowcld:{itemClass:"Stealth"}};
  assert.equal(api.recordSummary(cooler),"舰船组件 · 冷却器 · S1 · 隐A");
  const weapon={name:"M7A Cannon",category:{id:"ship_weapon",label:"舰船武器"},manufacturer:"<Maker>",subtype:"laser",zh:{subtype:"激光"},stats:{size:5,grade:1,tags:"LaserCannon"}};
  const html=api.renderRecordSummary(weapon,true);
  assert.match(html,/data-summary-full="舰船武器 · A · 激光加农炮 · S5 · &lt;Maker&gt;"/);
  assert.match(html,/data-summary-short="舰船武器 · A · 激光 · S5 · &lt;Maker&gt;"/);
  assert.doesNotMatch(html,/<Maker>|军A/);
  assert.match(api.recordSearchText(weapon),/激光加农炮/);
  assert.match(api.recordSearchText(cooler),/隐a/);
});

test("summary fitting falls back on overflow or a second line and restores full names when space returns", () => {
  const api=app();
  const small={dataset:{summaryFull:"full type",summaryShort:"short"},textContent:"short",clientWidth:120,
    get scrollWidth(){return this.textContent==="full type"?150:50;},getBoundingClientRect(){return {height:14};}};
  const root={querySelectorAll:()=>[small]};
  api.fitRecordSummaries(root);assert.equal(small.textContent,"short");
  small.clientWidth=200;
  api.fitRecordSummaries(root);assert.equal(small.textContent,"full type");
  small.getBoundingClientRect=()=>({height:28});
  api.fitRecordSummaries(root);assert.equal(small.textContent,"short");
  small.clientWidth=0;small.textContent="hidden";
  api.fitRecordSummaries(root);assert.equal(small.textContent,"hidden");
});

test("requirements keep optional entry points, distinct locations, false flags and zero XP", () => {
  const api = app();
  api.state.data.missionRewards.locations = { site: { name: "Checkmate", nameZh: "死局空间站", system: "Pyro", systemZh: "派罗" } };
  const html = api.renderMissionRequirements({ minStanding: { name: "Neutral", nameZh: "中立", minReputation: 0, includeWhenSharing: false },
    canBeShared: true, illegal: false, onceOnly: false, hasPersonalCooldown: true, personalCooldownTime: 45,
    linkedIntros: [{ title: "Establishing Security", titleZh: "建立安全保障" }],
    regions: [{ name: "RegionA", system: "Pyro", locations: ["site"] }], missionLocations: ["site"] });
  assert.match(html, /<details class="mission-requirements">/);
  assert.doesNotMatch(html, /<details[^>]* open/);
  assert.match(html, /中立 · 该级起始 0 XP · 不限制共享接收者/);
  assert.match(html, /派系入门（非硬前置）/);
  assert.doesNotMatch(html, /必需入门任务/);
  assert.match(html, /合法任务/);
  assert.match(html, /非一次性任务/);
  assert.match(html, /45 分钟/);
  assert.match(html, /派罗区域 A/);
  assert.match(html, /任务候选地点（非接取保证）/);
  assert.match(html, /死局空间站 · 派罗/);
  assert.match(api.renderMissionRequirements(null), /接取条件未记录/);
});

test("base stats preserve exact units and escape labels, while dismantling includes items", () => {
  const api = app();
  const html = api.renderBaseStats({ baseStats: [{ id: "speed", label: "<speed>", value: 1234.5, unit: "m/s", digits: 1 }], baseStatNotes: ["<note>"] });
  assert.match(html, /Q500 基准/);
  assert.match(html, /1,234.5 m\/s/);
  assert.match(html, /&lt;speed&gt;/);
  assert.doesNotMatch(html, /<note>/);
  assert.match(api.renderDismantle({ dismantle: { outputs: [{ name: "Eye", kind: "item", quantity: 2 }] } }), /资源与物品/);
});
