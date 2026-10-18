const state = {
  mode: "craft",
  data: null,
  mineralLocations: { materials: {}, metadata: null },
  records: [],
  filtered: [],
  selectedId: null,
  category: "all",
  componentType: "none",
  grade: "all",
  componentClass: "none",
  manufacturer: "all",
  material: "all",
  missionType: "all",
  query: "",
  sourceOnly: false,
  favoritesOnly: false,
  favorites: new Set(),
  qualityValues: {},
  qualityConfirmed: {},
  sort: "relevance",
  visibleResults: 0,
  missions: new Map(),
  rewardPools: new Map(),
  craftPlan: [],
  planSaved: true,
};

const DATA_VERSION = "__BUILD_DATA_VERSION__";
const SEARCH_INPUT_DELAY_MS = 120;
const RESULT_BATCH_SIZE = 140;
const SOURCE_TASK_PREVIEW_LIMIT = 12;
const SOURCE_TASK_MIN_HIDDEN = 4;
const FAVORITES_STORAGE_KEY = "gvy-lantu-favorite-blueprints-v1";
const PLAN_STORAGE_KEY = "gvy-lantu-craft-plan-v1";
let searchInputTimer = 0;
let summaryResizeFrame = 0;

const els = {
  dataStatus: document.querySelector("#dataStatus"),
  versionBadge: document.querySelector("#versionBadge"),
  dataUpdatedBadge: document.querySelector("#dataUpdatedBadge"),
  searchForm: document.querySelector("#searchForm"),
  searchInput: document.querySelector("#searchInput"),
  clearSearch: document.querySelector("#clearSearch"),
  filterCount: document.querySelector("#filterCount"),
  summaryLabel: document.querySelector("#summaryLabel"),
  favoritesToggle: document.querySelector("#favoritesToggle"),
  favoritesCount: document.querySelector("#favoritesCount"),
  modalResultCount: document.querySelector("#modalResultCount"),
  filterTitle: document.querySelector("#filterTitle"),
  filterResultLabel: document.querySelector("#filterResultLabel"),
  categoryFilterLabel: document.querySelector("#categoryFilterLabel"),
  materialFilterLabel: document.querySelector("#materialFilterLabel"),
  missionTypeGroup: document.querySelector('[data-filter-group="mission-type"]'),
  modeTabs: [...document.querySelectorAll("[data-mode]")],
  categoryFilters: document.querySelector("#categoryFilters"),
  componentTypeFilters: document.querySelector("#componentTypeFilters"),
  gradeFilters: document.querySelector("#gradeFilters"),
  componentClassFilters: document.querySelector("#componentClassFilters"),
  manufacturerFilters: document.querySelector("#manufacturerFilters"),
  materialFilters: document.querySelector("#materialFilters"),
  missionTypeFilters: document.querySelector("#missionTypeFilters"),
  sourceOnly: document.querySelector("#sourceOnly"),
  sourceToggle: document.querySelector("#sourceToggle"),
  sourceSort: document.querySelector("#sourceSort"),
  resultMetaLabel: document.querySelector("#resultMetaLabel"),
  resetFilters: document.querySelector("#resetFilters"),
  resultTitle: document.querySelector("#resultTitle"),
  resultList: document.querySelector("#resultList"),
  detailPanel: document.querySelector("#detailPanel"),
};

function loadFavorites() {
  try {
    const stored = JSON.parse(window.localStorage.getItem(FAVORITES_STORAGE_KEY) || "[]");
    return new Set(Array.isArray(stored) ? stored.filter((value) => typeof value === "string") : []);
  } catch {
    return new Set();
  }
}

function persistFavorites() {
  try {
    window.localStorage.setItem(FAVORITES_STORAGE_KEY, JSON.stringify([...state.favorites].sort()));
  } catch {
    // Favorites remain usable during this visit when browser storage is unavailable.
  }
}

function isFavorite(record) {
  return state.favorites.has(record.id);
}

function updateFavoriteControl() {
  const count = state.favorites.size;
  els.favoritesCount.textContent = formatNumber(count);
  els.favoritesToggle.classList.toggle("active", state.favoritesOnly);
  els.favoritesToggle.setAttribute("aria-pressed", String(state.favoritesOnly));
  els.favoritesToggle.title = state.favoritesOnly ? "显示全部蓝图" : "仅显示我的蓝图";
}

function toggleFavorite(recordId) {
  if (state.favorites.has(recordId)) state.favorites.delete(recordId);
  else state.favorites.add(recordId);
  persistFavorites();
  updateFavoriteControl();
  applyFilters();
}

function setSlotQuality(record, slotIndex, value) {
  const slot = getFirstTier(record).slots?.[slotIndex];
  if (!slot?.modifiers?.length) return;
  const quality = Math.round(Math.max(qualitySlotMinimum(slot), Math.min(1000, Number.isFinite(value) ? value : qualitySlotBaseline(slot))));
  state.qualityValues[qualitySlotKey(record, slotIndex)] = quality;
  state.qualityConfirmed[qualitySlotKey(record, slotIndex)] = true;
  const container = [...els.detailPanel.querySelectorAll("[data-quality-slot]")].find(el => el.dataset.qualitySlot === qualitySlotKey(record, slotIndex));
  if (!container) return;
  container.querySelectorAll("[data-quality-input], [data-quality-number]").forEach(input => { input.value = quality; });
  container.querySelector(".quality-number").dataset.confirmed = "true";
  container.querySelector(".quality-number").style.setProperty("--quality-digits", String(quality).length);
  container.querySelector("[data-quality-number]").placeholder = quality;
  const existing = container.querySelector(".quality-modifier-list");
  if (existing) existing.outerHTML = renderQualityModifiers(slot, quality);
  const summary = els.detailPanel.querySelector("[data-quality-summary-content]");
  if (summary) summary.outerHTML = renderQualitySummaryContent(record);
}

function validPlan(value) {
  if (!Array.isArray(value)) return [];
  const seen = new Set();
  return value.filter(row => {
    if (!row || typeof row.recordId !== "string" || !row.recordId || row.recordId.length > 200 || seen.has(row.recordId)
      || !Number.isInteger(row.quantity) || row.quantity < 1 || row.quantity > 9999) return false;
    seen.add(row.recordId);
    return true;
  }).slice(0, 100).map(row => ({recordId: row.recordId, quantity: row.quantity,
    choices: row.choices && typeof row.choices === "object" && !Array.isArray(row.choices) ? row.choices : {}}));
}

function savePlan() {
  try {
    window.localStorage.setItem(PLAN_STORAGE_KEY, JSON.stringify(state.craftPlan));
    state.planSaved = true;
  } catch { state.planSaved = false; }
  updatePlanCount();
}

function updatePlanCount() {
  const badge = document.querySelector("#planCount");
  if (badge) badge.textContent = formatNumber(state.craftPlan.reduce((sum, row) => sum + row.quantity, 0));
}

function planTotals(plan, records) {
  const materials = new Map();
  let seconds = 0;
  const warnings = [];
  for (const row of validPlan(plan)) {
    const record = records.find(item => item.id === row.recordId);
    if (!record) { warnings.push(`当前版本未收录：${row.recordId}`); continue; }
    const tier = getFirstTier(record);
    const time = tier.craftTimeSeconds;
    if (typeof time === "number" && Number.isFinite(time) && time >= 0) seconds += time * row.quantity;
    else warnings.push(`${recordName(record)}：制作耗时未提供`);
    for (const [index, slot] of (tier.slots || []).entries()) {
      const choice = row.choices[index] ?? 0;
      const option = Number.isInteger(choice) ? slot.options?.[choice] : null;
      if (!option || typeof option.quantity !== "number" || !Number.isFinite(option.quantity) || option.quantity < 0) {
        warnings.push(`${recordName(record)}：${preferZh(slot.nameZh, slot.name)}配方选项待确认`);
        continue;
      }
      const key = JSON.stringify([option.kind, option.name, option.minQuality || 0]);
      if (!materials.has(key)) materials.set(key, {...option, quantity: 0});
      materials.get(key).quantity += option.quantity * row.quantity;
    }
  }
  return {materials: [...materials.values()], seconds, warnings};
}

function openUtilityDialog(title, content, opener, className = "") {
  if (document.querySelector("dialog[open]")) return null;
  const previousOverflow = document.body.style.overflow;
  document.body.insertAdjacentHTML("beforeend", `<dialog class="mission-dialog utility-dialog ${className}" aria-labelledby="utilityDialogTitle">
    <header class="mission-dialog-head"><h2 id="utilityDialogTitle">${escapeHtml(title)}</h2><button type="button" class="mission-close" data-close-utility aria-label="关闭${escapeHtml(title)}" autofocus>×</button></header>
    <div class="mission-dialog-body">${content}</div>
    <footer class="mission-dialog-footer"><span>${escapeHtml(formatDataUpdatedAt(state.data.dataUpdatedAt).replace(/^更新/, "数据更新"))}</span><span>制作：Ayuan</span></footer></dialog>`);
  const dialog = document.querySelector(".utility-dialog");
  document.body.style.overflow = "hidden";
  dialog.addEventListener("close", () => { dialog.remove(); document.body.style.overflow = previousOverflow; if (opener?.isConnected) opener.focus({preventScroll: true}); }, {once: true});
  dialog.addEventListener("click", event => {
    const rect = dialog.getBoundingClientRect();
    if (event.target.closest("[data-close-utility]") || (event.target === dialog && (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom))) dialog.close();
  });
  dialog.showModal();
  return dialog;
}

function renderPlanBody() {
  const totals = planTotals(state.craftPlan, state.records);
  return `<div class="plan-toolbar"><span class="detail-note">${state.planSaved ? "本机已保存" : "浏览器存储不可用，仅本次会话保留"}</span><button type="button" class="favorite-detail-button" data-clear-plan ${!state.craftPlan.length ? "disabled" : ""}>清空清单</button></div>
    <div class="plan-list">${state.craftPlan.map(row => {
      const record = state.records.find(item => item.id === row.recordId);
      return `<div class="plan-row" data-plan-row="${escapeHtml(row.recordId)}"><strong>${escapeHtml(record ? recordName(record) : `当前版本未收录：${row.recordId}`)}</strong>
        <label>数量 <input type="number" inputmode="numeric" min="1" max="9999" step="1" value="${row.quantity}" data-plan-quantity aria-label="${escapeHtml(record ? recordName(record) : row.recordId)}制作数量" /></label>
        <button type="button" class="plan-remove" data-remove-plan aria-label="移除${escapeHtml(record ? recordName(record) : row.recordId)}" title="移出清单">×</button>
        ${record ? getFirstTier(record).slots.map((slot, index) => slot.options.length > 1 ? `<label class="plan-choice">${escapeHtml(preferZh(slot.nameZh, slot.name))}<select data-plan-choice="${index}" aria-label="${escapeHtml(preferZh(slot.nameZh, slot.name))}材料选项">${slot.options.map((option, i) => `<option value="${i}" ${i === (row.choices[index] ?? 0) ? "selected" : ""}>${escapeHtml(materialName(option))}</option>`).join("")}</select></label>` : "").join("") : ""}</div>`;
    }).join("") || '<p class="mission-empty">清单为空</p>'}</div>
    <section class="detail-section"><h3>材料合计</h3><div class="dismantle-output-list">${totals.materials.map(item => `<div><strong>${escapeHtml(materialName(item))}</strong><span>${escapeHtml(materialKind(item))}${item.minQuality ? ` · 最低品质 ${formatNumber(item.minQuality)}` : ""} · ${formatNumber(Number(item.quantity.toFixed(6)))}${item.kind === "resource" ? " SCU" : " 件"}</span></div>`).join("") || '<p class="mission-empty">暂无材料</p>'}</div>
    <p class="detail-note plan-time">累计制作耗时 ${escapeHtml(formatTime(totals.seconds))}（串行估算，不含排队）</p>
    ${totals.warnings.map(warning => `<p class="detail-note">${escapeHtml(warning)}</p>`).join("")}</section>`;
}

function openCraftPlan(opener) {
  const dialog = openUtilityDialog("制作清单", renderPlanBody(), opener, "planner-dialog");
  if (!dialog) return;
  const update = () => { savePlan(); dialog.querySelector(".mission-dialog-body").innerHTML = renderPlanBody(); };
  dialog.addEventListener("change", event => {
    const row = state.craftPlan.find(item => item.recordId === event.target.closest("[data-plan-row]")?.dataset.planRow);
    if (!row) return;
    if (event.target.matches("[data-plan-quantity]")) {
      const n = Number(event.target.value);
      row.quantity = Number.isFinite(n) && event.target.value.trim() ? Math.min(9999, Math.max(1, Math.round(n))) : row.quantity;
    } else if (event.target.matches("[data-plan-choice]")) row.choices[event.target.dataset.planChoice] = Number(event.target.value);
    else return;
    update();
  });
  dialog.addEventListener("click", event => {
    if (event.target.closest("[data-remove-plan]")) {
      state.craftPlan = state.craftPlan.filter(row => row.recordId !== event.target.closest("[data-plan-row]").dataset.planRow);
      update();
    } else if (event.target.closest("[data-clear-plan]")) {
      if (window.confirm("清空当前制作清单？")) { state.craftPlan = []; update(); }
    }
  });
}

function addToPlan(recordId, opener) {
  const existing = state.craftPlan.find(row => row.recordId === recordId);
  if (existing) existing.quantity = Math.min(9999, existing.quantity + 1);
  else if (state.craftPlan.length < 100) state.craftPlan.push({recordId, quantity: 1, choices: {}});
  savePlan();
  openCraftPlan(opener);
}

function blueprintShareUrl(id, mode = state.mode) {
  const url = new URL(window.location.href);
  url.search = "";
  url.hash = new URLSearchParams({blueprint: id, mode: mode === "dismantle" ? mode : "craft"}).toString();
  return url.href;
}

async function shareBlueprint(id, opener) {
  const link = blueprintShareUrl(id);
  try {
    await navigator.clipboard.writeText(link);
    if (opener?.isConnected) { opener.textContent = "已复制"; opener.setAttribute("aria-label", "蓝图链接已复制"); }
  } catch {
    const dialog = openUtilityDialog("蓝图链接", `<label class="share-link-label">${escapeHtml(recordName(state.records.find(r => r.id === id)))}<input class="share-link-input" value="${escapeHtml(link)}" readonly aria-label="蓝图链接" /></label>`, opener);
    dialog?.querySelector("input")?.select();
  }
}

function restoreSharedBlueprint() {
  const params = new URLSearchParams(window.location.hash.slice(1));
  const id = params.get("blueprint");
  if (!id) return;
  const record = state.records.find(item => item.id === id);
  if (!record) {
    openUtilityDialog("蓝图未收录", '<p class="mission-empty">该链接对应的蓝图在当前版本中未收录。</p>');
    return;
  }
  state.query = ""; els.searchInput.value = ""; state.favoritesOnly = false;
  setMode(params.get("mode") === "dismantle" && hasDismantleOutputs(record) ? "dismantle" : "craft");
  resetFilters(); updateFavoriteControl(); selectRecord(id);
}

function formatDataUpdatedAt(value) {
  if (!value) return "更新时间暂无";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "更新时间暂无";
  const formatted = new Intl.DateTimeFormat("zh-CN", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  })
    .format(date)
    .replace(/\//g, "/");
  return `更新 ${formatted}`;
}

const categoryOrder = [
  ["all", "全部"],
  ["ship_component", "舰船组件"],
  ["ship_weapon", "舰船武器"],
  ["personal_weapon", "单兵武器"],
  ["weapon_attachment", "武器配件"],
  ["armor", "护甲装备"],
  ["tool_module", "工具模块"],
  ["other", "其他"],
];

const gradeOrder = [
  ["all", "全部"],
  ["1", "A 级"],
  ["2", "B 级"],
  ["3", "C 级"],
  ["4", "D 级"],
];

const componentClassOrder = [
  ["all", "全部"],
  ["Military", "军用"],
  ["Civilian", "民用"],
  ["Stealth", "隐形"],
  ["Competition", "竞赛"],
  ["Industrial", "工业"],
];

const componentTypeOrder = [
  ["all", "全部"],
  ["cooler", "冷却器"],
  ["powerplant", "电源"],
  ["shield", "护盾"],
  ["quantumdrive", "量子驱动"],
  ["radar", "雷达"],
  ["mininglaser", "采矿激光"],
  ["tractorbeam", "牵引光束"],
  ["refuelling", "加油模块"],
  ["salvage", "打捞模块"],
];

const flowcldMaterialOrder = [
  "Agricium",
  "Beradom",
  "Beryl",
  "Bexalite",
  "Borase",
  "Copper",
  "Corundum",
  "Dolivine",
  "Feynmaline",
  "Glacosite",
  "Gold",
  "Hephaestanite",
  "Iron",
  "Laranite",
  "Lindinium",
  "Ouratite",
  "Pressurized Ice",
  "Quartz",
  "Riccite",
  "Sadaryx",
  "Savrilium",
  "Silicon",
  "Stileron",
  "Taranite",
  "Tin",
  "Titanium",
  "Torite",
  "Tungsten",
];

const flowcldMaterialLabels = {
  Agricium: "艾瑞格金属",
  Aluminum: "铝",
  Aphorite: "紫钠水晶",
  Aslarite: "阿斯莱晶体",
  Beradom: "冰蓝珀",
  Beryl: "绿柱石",
  Bexalite: "贝沙电气石",
  Borase: "波射矿石",
  Carinite: "肯瑞特矿石",
  Copper: "铜",
  Corundum: "刚玉",
  Dolivine: "暗橄榄石",
  Feynmaline: "费恩麻林",
  Glacosite: "格拉科石",
  Gold: "金",
  Hadanite: "哈丹水晶",
  Hephaestanite: "火神石",
  Iron: "铁",
  Janalite: "加纳石",
  Laranite: "砬兰石",
  Lindinium: "林登金",
  Ouratite: "欧特拉烃",
  "Pressurized Ice": "压缩冰",
  Quartz: "石英",
  Quantainium: "量子矿",
  Quantanium: "量子矿",
  Riccite: "愈金",
  Sadaryx: "萨达瑞晶",
  "Saldynium (Ore)": "烁迪银",
  "Saldynium Ore": "烁迪银",
  Saldynium: "烁迪银",
  Savrilium: "萨维里金属",
  Silicon: "硅",
  Stileron: "稀钛铁",
  Taranite: "塔兰导电石",
  Tin: "锡",
  Titanium: "钛",
  Torite: "托瑞特金属",
  Tungsten: "钨",
};

const missionTypeOrder = [
  ["all", "全部"],
  ["Mercenary", "雇佣兵"],
  ["Ship Mining", "舰船采矿"],
  ["Hauling - Interstellar", "星际货运"],
  ["Hauling - Stellar", "星际货运"],
  ["Refueling", "加油"],
  ["Hand Mining", "手持采矿"],
  ["Priority", "优先任务"],
  ["Battaglia", "巴塔利亚任务"],
  ["Wikelo - Other Items", "维科洛物品兑换"],
  ["Wikelo - Vehicles", "维科洛载具兑换"],
  ["Hauling", "货运"],
  ["Delivery", "快递"],
  ["Courier", "快递"],
  ["Salvage", "打捞"],
  ["Bounty Hunter", "赏金猎人"],
  ["Investigation", "调查"],
  ["Collection", "采集"],
  ["Other", "其他"],
];

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatNumber(value) {
  if (value === null || value === undefined || value === "") return "未知";
  return new Intl.NumberFormat("zh-CN").format(value);
}

function formatChance(value) {
  if (value === null || value === undefined || value === "") return "";
  const number = Number(value);
  if (!Number.isFinite(number)) return "";
  if (number <= 1) return `${Math.round(number * 100)}%`;
  return `${number}%`;
}

function formatTime(seconds) {
  if (seconds == null || typeof seconds !== "number" || !Number.isFinite(seconds) || seconds < 0) return "未知";
  if (seconds < 60) return `${seconds} 秒`;
  const minutes = Math.floor(seconds / 60);
  const remain = seconds % 60;
  return remain ? `${minutes} 分 ${remain} 秒` : `${minutes} 分钟`;
}

function preferZh(value, fallback = "") {
  const text = String(value ?? "").trim();
  return text || fallback;
}

function compactSizeTokens(value) {
  return String(value ?? "")
    .replace(/[（(]\s*S0*(\d+)\s*尺寸\s*[）)]/gi, "(S$1)")
    .replace(/\bS0+(\d+)\s*尺寸\b/gi, "S$1")
    .replace(/\bS0+(\d+)\b/g, "S$1");
}

function normalizeSearchText(value) {
  return compactSizeTokens(value)
    .toLowerCase()
    .replace(/[()（）"'“”‘’/\\.,;:·，。；：、\-\s_]+/g, "");
}

function getFirstTier(record) {
  return record.tiers?.[0] || { slots: [], craftTimeSeconds: null };
}

function getAllMaterials(record) {
  return getFirstTier(record).slots.flatMap((slot, slotIndex) =>
    slot.options.map((option) => ({
      ...option,
      slot: slot.name,
      slotZh: slot.nameZh,
      slotIndex,
      slotData: slot,
    })),
  );
}

function getDismantleOutputs(record) {
  return record.dismantle?.outputs || [];
}

function hasDismantleOutputs(record) {
  return getDismantleOutputs(record).length > 0;
}

function recordName(record) {
  return compactSizeTokens(preferZh(record.zh?.name, record.name));
}

function recordManufacturer(record) {
  return preferZh(record.zh?.manufacturer, record.manufacturer);
}

function recordType(record) {
  if (record.category.id === "ship_weapon") return recordWeaponType(record);
  return preferZh(record.zh?.type, record.type);
}

function recordSubtype(record) {
  return preferZh(record.zh?.subtype, record.subtype);
}

function recordGear(record) {
  const mapped = { fpsgear: "单兵装备", vehiclegear: "载具装备", missionitems: "任务物品" };
  return mapped[record.gear] || preferZh(record.zh?.gear, record.gear);
}

function statZh(record, key) {
  return preferZh(record.stats?.zh?.[key], record.stats?.[key]);
}

function gradeLabel(value) {
  return { 1: "A 级", 2: "B 级", 3: "C 级", 4: "D 级" }[value] || "未知";
}

function sizeLabel(value) {
  if (value === null || value === undefined || value === "") return "未知尺寸";
  return `S${value}`;
}

function materialZhName(item) {
  return item.nameZh || flowcldMaterialLabels[item.name] || item.name;
}

function materialDisplayLabel(name, zh) {
  const english = String(name ?? "").trim();
  const chinese = String(zh ?? "").trim();
  if (english && chinese && english !== chinese) return `${chinese} (${english})`;
  return chinese || english || "未知材料";
}

function materialName(item) {
  return materialDisplayLabel(item.name, materialZhName(item));
}

function materialKind(item) {
  const mapped = { resource: "资源", item: "物品", material: "材料" };
  return mapped[item.kind] || preferZh(item.kindZh, item.kind);
}

function materialSlot(item) {
  return preferZh(item.slotZh, item.slot);
}

function modifierName(modifier) {
  return preferZh(modifier.propertyNameZh, modifier.propertyName);
}

function qualitySlotKey(record, slotIndex) {
  return `${record.id}:${slotIndex}`;
}

function qualitySlotMinimum(slot) {
  return Math.max(0, ...(slot?.options || []).map((option) => Number(option.minQuality) || 0));
}

function qualitySlotBaseline(slot) {
  return Math.max(qualitySlotMinimum(slot), 500);
}

function qualitySlotValue(record, slot, slotIndex) {
  const key = qualitySlotKey(record, slotIndex);
  const minimum = qualitySlotMinimum(slot);
  const stored = Number(state.qualityValues[key]);
  if (Number.isFinite(stored)) return Math.max(minimum, Math.min(1000, stored));
  return qualitySlotBaseline(slot);
}

function modifierFactor(modifier, quality) {
  const start = Number(modifier.startQuality) || 0;
  const end = Number(modifier.endQuality) || 1000;
  const startValue = Number(modifier.modifierAtStart) || 0;
  const endValue = Number(modifier.modifierAtEnd) || 0;
  if (end <= start) return endValue;
  const progress = Math.max(0, Math.min(1, (quality - start) / (end - start)));
  return startValue + (endValue - startValue) * progress;
}

function modifierGroups(slot) {
  const groups = new Map();
  (slot?.modifiers || []).forEach((modifier) => {
    const propertyKey = modifier.propertyKey || modifier.propertyName;
    if (!propertyKey) return;
    const key = `${propertyKey}:${modifier.additive ? "add" : "multiply"}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(modifier);
  });
  return [...groups.values()];
}

function modifierGroupValue(modifiers, quality) {
  const segments = [...modifiers].sort((a, b) => (Number(a.startQuality) || 0) - (Number(b.startQuality) || 0));
  if (!segments.length) return 0;
  const exact = segments.find((segment) => quality >= Number(segment.startQuality) && quality <= Number(segment.endQuality));
  if (exact) return modifierFactor(exact, quality);
  if (quality < Number(segments[0].startQuality)) return modifierFactor(segments[0], quality);
  return modifierFactor(segments[segments.length - 1], quality);
}

function renderQualityModifiers(slot, quality) {
  const groups = modifierGroups(slot);
  if (!groups.length) return "";
  return `
    <div class="quality-modifier-list">
      ${groups
        .map((group) => {
          const modifier = group[0];
          const value = modifierGroupValue(group, quality);
          const valueLabel = modifier.additive ? `修正 ${value > 0 ? "+" : ""}${formatNumber(value)}` : `系数 ${value.toFixed(3).replace(/0+$/, "").replace(/\.$/, "")}×`;
          return `<span><strong>${escapeHtml(modifierName(modifier))}</strong><small>${escapeHtml(valueLabel)}</small></span>`;
        })
        .join("")}
    </div>
  `;
}

function renderMaterialQuality(record, slot, slotIndex) {
  if (!(slot?.modifiers || []).length) return "";
  const quality = qualitySlotValue(record, slot, slotIndex);
  const minimum = qualitySlotMinimum(slot);
  const confirmed = state.qualityConfirmed[qualitySlotKey(record, slotIndex)] === true;
  return `
    <div class="material-quality" data-quality-slot="${escapeHtml(qualitySlotKey(record, slotIndex))}">
      <div class="material-quality-control">
        <input type="range" min="${minimum}" max="1000" step="1" value="${quality}" data-quality-input data-record-id="${escapeHtml(record.id)}" data-slot-index="${slotIndex}" aria-label="${escapeHtml(preferZh(slot.nameZh, slot.name))}品质" />
        <div class="quality-number" data-confirmed="${confirmed}" style="--quality-digits: ${String(quality).length}"><span>品质</span><input type="number" inputmode="numeric" min="${minimum}" max="1000" step="1" value="${confirmed ? quality : ""}" placeholder="${quality}" data-quality-number data-record-id="${escapeHtml(record.id)}" data-slot-index="${slotIndex}" aria-label="${escapeHtml(preferZh(slot.nameZh, slot.name))}品质数值" aria-describedby="qualityHint-${escapeHtml(qualitySlotKey(record, slotIndex))}" /><span class="quality-input-hint" id="qualityHint-${escapeHtml(qualitySlotKey(record, slotIndex))}" role="tooltip">点击输入品质 · ${minimum}–1000</span></div>
      </div>
      ${renderQualityModifiers(slot, quality)}
    </div>
  `;
}

function aggregateQualityEffects(record) {
  const effects = new Map();
  getFirstTier(record).slots.forEach((slot, slotIndex) => {
    const quality = qualitySlotValue(record, slot, slotIndex);
    const baseline = qualitySlotBaseline(slot);
    modifierGroups(slot).forEach((group) => {
      const modifier = group[0];
      const propertyKey = modifier.propertyKey || modifier.propertyName;
      if (!propertyKey) return;
      if (!effects.has(propertyKey)) {
        effects.set(propertyKey, {
          propertyKey,
          label: modifierName(modifier),
          currentMultiplier: 1,
          baselineMultiplier: 1,
          currentAdditive: 0,
          baselineAdditive: 0,
          hasMultiplier: false,
          hasAdditive: false,
        });
      }
      const effect = effects.get(propertyKey);
      const currentValue = modifierGroupValue(group, quality);
      const baselineValue = modifierGroupValue(group, baseline);
      if (modifier.additive) {
        effect.currentAdditive += currentValue;
        effect.baselineAdditive += baselineValue;
        effect.hasAdditive = true;
      } else {
        effect.currentMultiplier *= currentValue;
        effect.baselineMultiplier *= baselineValue;
        effect.hasMultiplier = true;
      }
    });
  });

  effects.forEach((effect) => {
    effect.ratio = effect.baselineMultiplier === 0 ? 1 : effect.currentMultiplier / effect.baselineMultiplier;
    effect.additiveDelta = effect.currentAdditive - effect.baselineAdditive;
  });
  return effects;
}

function formatQualityValue(value, digits = 2, unit = "") {
  const maximumFractionDigits = Math.max(0, Number(digits) || 0);
  const text = new Intl.NumberFormat("zh-CN", {
    maximumFractionDigits,
    minimumFractionDigits: 0,
  }).format(value);
  return `${text}${unit ? ` ${unit}` : ""}`;
}

function signedQualityChange(value, suffix = "%") {
  const rounded = Math.abs(value) < 0.005 ? 0 : value;
  return `${rounded > 0 ? "+" : ""}${rounded.toFixed(2).replace(/\.00$/, "")}${suffix}`;
}

function qualityMetricValue(metric, effects) {
  let value = Number(metric.value);
  (metric.properties || []).forEach((propertyKey) => {
    const effect = effects.get(propertyKey);
    if (!effect) return;
    if (effect.hasMultiplier) value *= effect.ratio;
    if (effect.hasAdditive) value += effect.additiveDelta;
  });
  return value;
}

function renderQualitySummaryContent(record) {
  const effects = aggregateQualityEffects(record);
  const metrics = record.qualityStats || [];
  const coveredProperties = new Set(metrics.flatMap((metric) => metric.properties || []));
  const metricCards = metrics.map((metric) => {
    const baseValue = Number(metric.value);
    const finalValue = qualityMetricValue(metric, effects);
    const percent = baseValue === 0 ? 0 : ((finalValue - baseValue) / Math.abs(baseValue)) * 100;
    const changed = Math.abs(finalValue - baseValue) > 0.0005;
    return `
      <div class="quality-result-item${changed ? " changed" : ""}">
        <strong>${escapeHtml(metric.label)}</strong>
        <span class="quality-result-values">
          <small>${escapeHtml(formatQualityValue(baseValue, metric.digits, metric.unit))}</small>
          <i aria-hidden="true">→</i>
          <b>${escapeHtml(formatQualityValue(finalValue, metric.digits, metric.unit))}</b>
          <em>${escapeHtml(changed ? signedQualityChange(percent) : "无变化")}</em>
        </span>
      </div>
    `;
  });
  const relativeCards = [...effects.values()]
    .filter((effect) => !coveredProperties.has(effect.propertyKey))
    .map((effect) => {
      const change = effect.hasMultiplier ? (effect.ratio - 1) * 100 : effect.additiveDelta;
      const changed = Math.abs(change) > 0.005;
      const start = effect.hasMultiplier ? "100%" : "0";
      const end = effect.hasMultiplier ? `${(effect.ratio * 100).toFixed(2).replace(/\.00$/, "")}%` : signedQualityChange(effect.additiveDelta, "");
      return `
        <div class="quality-result-item relative${changed ? " changed" : ""}">
          <strong>${escapeHtml(effect.label)}</strong>
          <span class="quality-result-values">
            <small>${start}</small>
            <i aria-hidden="true">→</i>
            <b>${escapeHtml(end)}</b>
            <em>${escapeHtml(changed ? signedQualityChange(change, effect.hasMultiplier ? "%" : "") : "无变化")}</em>
          </span>
        </div>
      `;
    });

  return `<div class="quality-result-grid" data-quality-summary-content>${[...metricCards, ...relativeCards].join("")}</div>`;
}

function renderQualitySummary(record) {
  if (!aggregateQualityEffects(record).size) return "";
  return `
    <section class="detail-section quality-result-section" data-quality-summary>
      <div class="quality-result-heading">
        <h3>成品品质效果</h3>
        <span>Q500 标准</span>
      </div>
      ${renderQualitySummaryContent(record)}
    </section>
  `;
}

function renderBaseStats(record) {
  const metrics = record.baseStats || [];
  if (!metrics.length) return "";
  return `<details class="detail-section base-stats">
    <summary>基础属性 <small>Q500 基准</small></summary>
    <div class="spec-grid">${metrics.map((metric) => `<div class="spec-item"><strong>${escapeHtml(metric.label)}</strong><span>${escapeHtml(formatQualityValue(metric.value, metric.digits, metric.unit))}</span></div>`).join("")}</div>
    ${(record.baseStatNotes || []).map((note) => `<p class="detail-note">${escapeHtml(note)}</p>`).join("")}
  </details>`;
}

function renderDismantle(record, standalone = false) {
  const dismantle = record.dismantle || {};
  const outputs = dismantle.outputs || [];
  if (!outputs.length) return "";
  return `
    <section class="detail-section dismantle-section">
      <h3>${standalone ? "拆解所得" : "拆解回收"}</h3>
      <p class="detail-note">按当前 LIVE 拆解规则计算，显示可回收的资源与物品；实际结果以游戏版本为准。</p>
      <div class="dismantle-summary">
        <span>效率 ${Math.round((Number(dismantle.efficiency) || 0) * 100)}%</span>
        <span>耗时 ${formatTime(dismantle.timeSeconds)}</span>
      </div>
      <div class="dismantle-output-list">
        ${outputs
          .map((output) => {
            const amount = output.kind === "resource"
              ? `${formatNumber(output.quantity)} SCU`
              : `x${formatNumber(output.quantity)}`;
            return `<div><strong>${escapeHtml(materialDisplayLabel(output.name, output.nameZh))}</strong><span>${escapeHtml(materialKind(output))} · 回收 ${escapeHtml(amount)}</span></div>`;
          })
          .join("")}
      </div>
    </section>
  `;
}

const mineralLocationGroups = [
  ["starSystems", "星系"],
  ["planets", "行星"],
  ["moons", "卫星"],
  ["lagrangePoints", "拉格朗日点"],
  ["pointsOfInterest", "兴趣点"],
];

function mineralLocationInfo(name) {
  return state.mineralLocations?.materials?.[name] || null;
}

function mineralLocationLabel(location) {
  const zh = location.zh || location.en || "未知";
  const en = location.en || location.zh || "Unknown";
  return zh === en ? zh : `${zh} (${en})`;
}

function mineralLocationSubline(location) {
  const parts = [];
  if (location.systemEn && location.systemZh) parts.push(`${location.systemZh} (${location.systemEn})`);
  if (location.parentEn && location.parentZh && location.parentEn !== location.en) {
    parts.push(`${location.parentZh} (${location.parentEn})`);
  }
  return parts.join(" · ");
}

function renderLocationSignalTooltip(location) {
  const signals = location.signals || (location.signal?.values?.length ? [location.signal] : []);
  if (!signals.length) return "";
  const unique = [...new Map(signals.map(s => [JSON.stringify([s.mode, s.base, s.primaryMaterial, s.clusterCounts, s.values]), s])).values()];
  return `<button type="button" class="mineral-signal-badge" data-signal-trigger aria-expanded="false" aria-label="查看${escapeHtml(location.zh || location.en)}信号">信号</button>
    <template data-signal-content><strong>${escapeHtml(mineralLocationLabel(location))}</strong>
    ${unique.map(signal => `<div class="mineral-signal-entry">
      <strong>${escapeHtml({ship: "舰采矿体", roc: "ROC 单矿", fps: "手采单矿"}[signal.mode] || "矿体")} · ${escapeHtml(signal.primaryMaterialZh || signal.primaryMaterial || "信号参考")}</strong>
      ${signal.shared ? '<small>同类共通信号，不代表某一种材料独有；不按矿簇数量叠加。</small>' : '<small>混合矿体以主矿信号为准，不代表只含该材料。</small>'}
      <span class="mineral-signal-values">${signal.values.map(value => `<b>${escapeHtml(formatNumber(value))}</b>`).join("")}</span>
      <small>${signal.clusterKnown ? `矿簇配置：${escapeHtml(signal.clusterCounts.join(" / "))} 块` : "矿簇配置未提供，仅作单矿参考"}</small>
    </div>`).join("")}</template>`;
}

function closeSignalTooltip() {
  document.querySelector(".mineral-location-tooltip")?.remove();
  document.querySelectorAll("[data-signal-trigger][aria-expanded=true]").forEach(button => {
    button.setAttribute("aria-expanded", "false"); button.removeAttribute("aria-describedby");
  });
}

function showSignalTooltip(button) {
  closeSignalTooltip();
  const overlay = button.closest(".mineral-overlay");
  const template = button.parentElement.querySelector("[data-signal-content]");
  if (!overlay || !template) return;
  overlay.insertAdjacentHTML("beforeend", `<div class="mineral-location-tooltip is-visible" role="tooltip">${template.innerHTML}</div>`);
  const tooltip = overlay.querySelector(".mineral-location-tooltip");
  const rect = button.getBoundingClientRect();
  const card = overlay.querySelector(".mineral-card").getBoundingClientRect();
  const width = Math.min(380, window.innerWidth - 32, card.width - 24);
  tooltip.style.width = `${width}px`;
  tooltip.style.left = `${Math.max(16, card.left + 12, Math.min(rect.right - width, card.right - width - 12, window.innerWidth - width - 16))}px`;
  const height = tooltip.getBoundingClientRect().height;
  tooltip.style.top = `${Math.max(16, Math.min(rect.bottom + 8, window.innerHeight - height - 16))}px`;
  tooltip.id = "mineralSignalTooltip";
  button.setAttribute("aria-expanded", "true");
  button.setAttribute("aria-describedby", tooltip.id);
}

function renderMineralLocationGroups(info) {
  if (!info?.hasReliableLocations) {
    return `
      <div class="mineral-empty">
        <strong>暂无可靠矿点</strong>
        <span>暂无地点数据</span>
      </div>
    `;
  }

  return mineralLocationGroups
    .map(([key, label]) => {
      const locations = info.locations?.[key] || [];
      if (!locations.length) return "";
      return `
        <section class="mineral-location-group">
          <h4>${label}</h4>
          <div class="mineral-location-list">
            ${locations
              .map((location) => {
                const subline = mineralLocationSubline(location);
                const signalTooltip = renderLocationSignalTooltip(location);
                return `
                  <div class="mineral-location-item${signalTooltip ? " has-signal" : ""}">
                    <strong title="${escapeHtml(mineralLocationLabel(location))}">${escapeHtml(mineralLocationLabel(location))}</strong>
                    ${subline ? `<small>${escapeHtml(subline)}</small>` : ""}
                    ${location.precision ? `<small>${location.precision === "template" ? "区域配置模板" : "区域分布"} · ${escapeHtml((location.modes || []).map(mode => ({ship: "舰采", roc: "ROC", fps: "手采"}[mode] || mode)).join(" / "))}${!signalTooltip ? " · 信号未提供" : ""}</small>` : ""}
                    ${signalTooltip}
                  </div>
                `;
              })
              .join("")}
          </div>
        </section>
      `;
    })
    .join("");
}

function renderMineralInfo(name) {
  const info = mineralLocationInfo(name);
  const displayName = materialDisplayLabel(name, info?.nameZh || flowcldMaterialLabels[name]);
  const commodity = info?.commodityName && info.commodityName !== name ? info.commodityName : "";
  const hasLocationSignals = mineralLocationGroups.some(([key]) =>
    (info?.locations?.[key] || []).some((location) => location.signals?.length || location.signal?.values?.length),
  );
  const mineralMetadata = state.mineralLocations?.metadata || {};
  const latestMineralTimestamp = [mineralMetadata.retrievedAt, mineralMetadata.signalSyncedAt]
    .map((value) => (value ? new Date(value) : null))
    .filter((value) => value && !Number.isNaN(value.getTime()))
    .sort((left, right) => right.getTime() - left.getTime())[0];
  const updatedAt = latestMineralTimestamp
    ? latestMineralTimestamp.toLocaleString("zh-CN", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        timeZone: "Asia/Shanghai",
      })
    : "未知";

  return `
    <div class="mineral-overlay" role="presentation">
      <section class="mineral-card${hasLocationSignals ? " has-location-signals" : ""}" role="dialog" aria-modal="true" aria-label="${escapeHtml(displayName)}矿点详情">
        <header class="mineral-card-head">
          <div>
            <span>矿物分布</span>
            <h3>${escapeHtml(displayName)}</h3>
            ${commodity ? `<small>匹配资源：${escapeHtml(commodity)}</small>` : ""}
          </div>
          <button type="button" class="mineral-close" data-close-mineral aria-label="关闭矿点详情">×</button>
        </header>
        <div class="mineral-card-body">
          ${info?.hasReliableLocations && mineralMetadata.schemaVersion === 2 ? '<p class="detail-note">以下为当前版本的产出区域，不保证固定刷新。未提供可验证的地表坐标；区域模板不对应某个指定空间站。</p>' : ""}
          ${renderMineralLocationGroups(info)}
        </div>
        <footer class="mineral-source">
          <span>数据更新 ${escapeHtml(updatedAt)}</span>
          <span class="mineral-author">制作：Ayuan</span>
        </footer>
      </section>
    </div>
  `;
}

function openMineralInfo(name) {
  closeMineralInfo();
  els.detailPanel.insertAdjacentHTML("beforeend", renderMineralInfo(name));
}

function closeMineralInfo() {
  closeSignalTooltip();
  els.detailPanel.querySelector(".mineral-overlay")?.remove();
}

function missionTitle(mission) {
  return preferZh(mission.titleZh, mission.title).replace(/\[LOCATION\]/gi, "[地点]");
}

function renderBlueprintText(text) {
  return escapeHtml(text).replaceAll("[蓝图]", '<span class="mission-blueprint-tag">[蓝图]</span>');
}

function initMissionRewards() {
  state.missions = new Map();
  state.rewardPools = new Map();
  for (const record of state.records) {
    for (const source of record.sources || []) {
      if (!state.rewardPools.has(source.poolId)) state.rewardPools.set(source.poolId, new Map());
      state.rewardPools.get(source.poolId).set(record.id, record);
      for (const mission of source.missions || []) {
        if (mission.id) state.missions.set(mission.id, mission);
      }
    }
  }
}

function missionSystemLabels(mission) {
  const systems = [...new Set((mission.systems || []).filter((name) => typeof name === "string" && name.trim()))];
  return systems.map((name) => {
    const localized = state.data.missionRewards?.systems?.find((system) => system.name === name)?.nameZh;
    const location = Object.values(state.mineralLocations.materials || {})
      .flatMap((material) => material.locations?.starSystems || [])
      .find((system) => system.en === name);
    const zh = localized || location?.zh;
    return zh && zh !== name ? `${zh} (${name})` : name;
  }).join(" / ") || "星系未注明";
}

function renderMissionItems(rewards) {
  if (!rewards.length) return '<p class="mission-empty">暂无已记录的物品奖励</p>';
  return rewards.map((reward) => {
    const groups = reward.type === "weighted_choice" ? reward.groups || [] : [{ items: [reward] }];
    const conditions = [reward.awardOnlyToMissionOwner ? "仅任务拥有者" : "",
      reward.sendToPlayerHomeLocation ? "送至家乡仓库" : ""].filter(Boolean);
    const choiceNote = reward.type === "weighted_choice"
      ? `<p class="mission-reward-meta">${groups.length === 1 ? "触发该物品奖励时，以下物品作为一组一起发放。" : "按权重选择以下一个组合；选中组合内的物品一起发放，不是所有组合都获得。"}</p>` : "";
    return choiceNote + groups.map((group, index) => `
      <div class="mission-item-group">
        ${reward.type === "weighted_choice" ? `<p class="mission-reward-meta">${groups.length > 1 ? "备选物品组合" : "物品组合"} ${index + 1}${group.probability != null ? ` · 组合选择概率 ${escapeHtml(formatChance(group.probability))}` : ""}</p>` : ""}
        ${(group.items || []).map((item) => `<div class="mission-item-row">
          <strong>${escapeHtml(preferZh(item.nameZh, item.name))}</strong>
          <span>${item.amount != null ? `×${escapeHtml(formatNumber(item.amount))}` : "数量未注明"}</span>
        </div>`).join("")}
        ${conditions.length ? `<p class="mission-reward-meta">${escapeHtml(conditions.join(" · "))}</p>` : ""}
      </div>`).join("");
  }).join("");
}

function renderMissionRequirements(requirements) {
  if (!requirements) return '<p class="mission-reward-meta">接取条件未记录；请以游戏内任务为准。</p>';
  const rows = [];
  const add = (label, value) => rows.push(`<div><dt>${escapeHtml(label)}</dt><dd>${renderBlueprintText(value)}</dd></div>`);
  for (const [field, label] of [["minStanding", "最低声望"], ["maxStanding", "最高声望"]]) {
    const standing = requirements[field];
    if (standing) add(label, `${preferZh(standing.nameZh, standing.name)}${standing.minReputation != null ? ` · 该级起始 ${formatNumber(standing.minReputation)} XP` : ""}${requirements.canBeShared !== true ? "" : standing.includeWhenSharing === true ? " · 共享时同样要求" : standing.includeWhenSharing === false ? " · 不限制共享接收者" : ""}`);
  }
  const crime = requirements.crimeStat;
  if (crime) add("犯罪等级", `${crime.min}–${crime.max}${crime.includeWhenSharing === true ? " · 共享时同样要求" : ""}`);
  for (const [field, label, yes, no] of [
    ["canBeShared", "任务共享", "可以共享", "不可共享"],
    ["illegal", "任务性质", "非法任务", "合法任务"],
    ["onceOnly", "次数限制", "仅一次", "非一次性任务"],
    ["canReacceptAfterAbandoning", "放弃后重接", "允许", "不允许"],
    ["canReacceptAfterFailing", "失败后重接", "允许", "不允许"],
  ]) if (typeof requirements[field] === "boolean") add(label, requirements[field] ? yes : no);
  if (requirements.hasPersonalCooldown === true && requirements.personalCooldownTime != null) add("个人冷却", `${formatNumber(requirements.personalCooldownTime)} 分钟`);
  if (requirements.abandonedCooldownTime > 0) add("放弃后冷却", `${formatNumber(requirements.abandonedCooldownTime)} 分钟`);
  const titles = (intros) => [...new Set((intros || []).map(missionTitle))].join(" / ");
  if (requirements.requiredIntros?.length) add("必需入门任务", titles(requirements.requiredIntros));
  if (requirements.linkedIntros?.length) add("派系入门（非硬前置）", titles(requirements.linkedIntros));
  const completed = requirements.completedContracts;
  if (completed) add("前置完成标记", `${completed.requiredCount != null ? `要求 ${formatNumber(completed.requiredCount)} 项` : "要求数量未注明"}${completed.candidates?.length ? `；对应任务：${titles(completed.candidates)}` : "；具体任务未明确"}（候选任务并非全部必做）`);
  const excluded = requirements.excludedContracts;
  if (excluded) add("已完成标记排除", `${excluded.candidates?.length ? titles(excluded.candidates) : `${formatNumber(excluded.tagCount)} 项标记，具体任务未明确`}；满足这些完成标记时可能无法接取，不是必做前置。`);
  const location = (id) => {
    const item = state.data.missionRewards?.locations?.[id];
    if (!item) return "";
    const name = !item.nameZh && item.name?.startsWith("@") ? "地点名称未解析" : preferZh(item.nameZh, item.name);
    return [name, item.system ? preferZh(item.systemZh, item.system) : ""].filter(Boolean).join(" · ");
  };
  const locationList = (label, ids) => ids?.length ? `<details class="mission-places"><summary>${escapeHtml(label)} · ${formatNumber(ids.length)} 处</summary><ul>${ids.map((id) => `<li>${escapeHtml(location(id))}</li>`).join("")}</ul></details>` : "";
  const regions = (requirements.regions || []).map((region) => {
    const label = region.system === "Pyro" && /^Region[A-D]$/.test(region.name) ? `派罗区域 ${region.name.slice(-1)}` : preferZh(region.nameZh, region.name);
    return `<div class="mission-region"><p class="mission-reward-meta">接取区域：${escapeHtml(label)}</p>${locationList("区域覆盖地点", region.locations)}</div>`;
  }).join("");
  const extraLabels = { reputationLockout: "其他派系声望限制", requiredScenarios: "活动状态限制", subLocationVariants: "子地点变体限制" };
  const extra = (requirements.additionalRestrictions || []).map((key) => extraLabels[key] || "额外接取限制");
  return `<details class="mission-requirements"><summary>接取条件与地点</summary>
    <dl class="mission-condition-grid">${rows.join("")}</dl>${regions}
    ${locationList("接取位置条件", requirements.acceptLocations)}${locationList("任务候选地点（非接取保证）", requirements.missionLocations)}
    ${requirements.unresolvedLocations ? `<p class="mission-reward-meta">另有 ${formatNumber(requirements.unresolvedLocations)} 个地点未解析。</p>` : ""}
    ${extra.length ? `<p class="mission-reward-meta">另含${escapeHtml(extra.join("、"))}，详情需在游戏内确认。</p>` : ""}
    <p class="mission-reward-meta">区域和条件来自当前任务配置，不表示服务器当前一定可接；未列出的限制不代表不存在。</p>
  </details>`;
}

function renderMissionPools(rewardPools) {
  return rewardPools.map((pool, index) => {
    const records = [...(state.rewardPools.get(pool.id)?.values() || [])]
      .sort((left, right) => recordName(left).localeCompare(recordName(right), "zh-CN"));
    const chance = formatChance(pool.chance);
    const trigger = { complete: "完成任务", fail: "任务失败", abandon: "放弃任务" }[pool.trigger] || pool.trigger;
    const types = [...new Set(records.map((record) => record.category.id === "ship_component"
      ? recordComponentType(record) : record.category.label))];
    return `<section class="mission-pool">
      <header class="mission-pool-head">
        <div><h4>蓝图奖励池 ${index + 1}</h4><small>${escapeHtml(types.join(" / "))}</small></div>
        <div class="mission-pool-draw"><strong>${records.length ? `${formatNumber(records.length)} 选 1` : "候选蓝图待补齐"}</strong><small>${escapeHtml([trigger, chance ? `池触发概率 ${chance}` : "池触发概率未注明"].filter(Boolean).join(" · "))}</small></div>
      </header>
      <div class="mission-blueprint-list">${records.map((record) => `
        <button type="button" class="mission-blueprint-row" data-mission-blueprint="${escapeHtml(record.id)}" title="查看${escapeHtml(recordName(record))}蓝图">
          <span><strong>${escapeHtml(recordName(record))}</strong>${renderRecordSummary(record)}</span>
          <span class="mission-reward-marker">${record.id === state.selectedId ? "当前蓝图" : "查看蓝图"}<i aria-hidden="true">›</i></span>
        </button>`).join("") || '<p class="mission-empty">暂无已收录的蓝图</p>'}</div>
    </section>`;
  }).join("");
}

function openMissionInfo(id, opener) {
  const mission = state.missions.get(id);
  const rewards = state.data.missionRewards?.missions?.[id];
  if (!mission || !rewards) return;
  if (document.querySelector(".mission-dialog")) return;
  const previousOverflow = document.body.style.overflow;
  document.body.insertAdjacentHTML("beforeend", `
    <dialog class="mission-dialog" aria-labelledby="missionDialogTitle">
      <header class="mission-dialog-head">
        <div><span class="mission-eyebrow">任务奖励</span><h2 id="missionDialogTitle">${renderBlueprintText(missionTitle(mission))}</h2>
          <p>${escapeHtml(missionSystemLabels(mission))}</p>
          <small>${escapeHtml([missionFaction(mission), mission.rewardUEC != null ? `${formatNumber(mission.rewardUEC)} aUEC` : ""].filter(Boolean).join(" · "))}</small>
        </div>
        <button type="button" class="mission-close" data-close-mission aria-label="关闭任务奖励" autofocus>×</button>
      </header>
      <div class="mission-dialog-body">
        ${renderMissionRequirements(rewards.requirements)}
        <section class="mission-reward-section">
          <h3>蓝图奖励</h3>
          <p class="mission-draw-note">本任务含 ${formatNumber(rewards.pools.length)} 个蓝图奖励池。各池独立按对应条件及触发概率发放 1 张蓝图，已集齐的池不再发放。以下为候选蓝图，并非一次全部获得。</p>
          ${renderMissionPools(rewards.pools || [])}
          <p class="mission-reward-meta">池触发概率不等于单张蓝图的掉率。N 选 1 不代表必得未拥有的蓝图，也不保证 N 次集齐；重复和保底规则未完整确认。实际发放以游戏任务和完成条件为准。</p>
        </section>
        <section class="mission-reward-section"><h3>物品奖励</h3><p class="mission-reward-note">以下是实物，不是蓝图；数量与蓝图奖励分别计算。领取对象和发放条件以任务配置及游戏内结果为准。</p>${renderMissionItems(rewards.items || [])}</section>
      </div>
      <footer class="mission-dialog-footer"><span>${escapeHtml(formatDataUpdatedAt(state.data.dataUpdatedAt).replace(/^更新/, "数据更新"))}</span><span>制作：Ayuan</span></footer>
    </dialog>`);
  const dialog = document.querySelector(".mission-dialog");
  document.body.style.overflow = "hidden";
  dialog.addEventListener("close", () => {
    document.body.style.overflow = previousOverflow;
    dialog.remove();
    if (opener?.isConnected) opener.focus({ preventScroll: true });
  }, { once: true });
  dialog.addEventListener("click", (event) => {
    const target = event.target.closest("[data-mission-blueprint]");
    if (target) {
      const record = state.records.find((record) => record.id === target.dataset.missionBlueprint);
      if (!record) return;
      dialog.close();
      window.clearTimeout(searchInputTimer);
      state.query = recordName(record);
      els.searchInput.value = state.query;
      state.favoritesOnly = false;
      resetFilters();
      selectRecord(target.dataset.missionBlueprint);
      const heading = els.detailPanel.querySelector("h2");
      heading?.setAttribute("tabindex", "-1");
      heading?.focus({ preventScroll: true });
      if (window.innerWidth <= 1100) els.detailPanel.scrollIntoView({ block: "start" });
      return;
    }
    const rect = dialog.getBoundingClientRect();
    const outside = event.target === dialog && (event.clientX < rect.left || event.clientX > rect.right
      || event.clientY < rect.top || event.clientY > rect.bottom);
    if (event.target.closest("[data-close-mission]") || outside) dialog.close();
  });
  dialog.showModal();
  fitRecordSummaries(dialog);
}

function missionFaction(mission) {
  return preferZh(mission.factionZh, mission.faction);
}

function recordFlowcld(record) {
  return record.flowcld || {};
}

function recordClass(record) {
  return Object.hasOwn(record.stats || {}, "componentClass") ? record.stats.componentClass : recordFlowcld(record).itemClass;
}

function recordComponentClass(record) {
  const value = recordClass(record);
  return componentClassOrder.find(([id]) => id !== "all" && id === value)?.[1] || "";
}

function recordComponentType(record) {
  return componentTypeOrder.find(([id]) => id === record.type)?.[1] || recordType(record);
}

function recordWeaponType(record) {
  const subtype = recordSubtype(record);
  if (record.category.id !== "ship_weapon") return subtype;
  const tags = new Set(String(record.stats?.tags || "").split(/\s+/));
  const families = [
    [["MassDriver"], /\bMass Driver Cannon(?:\s*\(S\d+\))?$/i, "质量驱动炮"],
    [["ScatterGun"], /\bScattergun(?:\s*\(S\d+\))?$/i, "霰弹炮"],
    [["BallisticGatling", "LaserGatling"], /\bGatling(?:\s*\(S\d+\))?$/i, "加特林"],
    [["LaserRepeater", "BallisticRepeater", "DistortionRepeater"], /\bRepeater(?:\s*\(S\d+\))?$/i, "速射炮"],
    [["LaserCannon", "BallisticCannon", "DistortionCannon", "NeutronCannon", "BANU_TachyonCannon"], /\bCannon(?:\s*\(S\d+\))?$/i, "加农炮"],
  ];
  const family = families.find(([tokens, pattern]) => tokens.some(token => tags.has(token)) || pattern.test(record.name || ""))?.[2];
  if (!family || !["laser", "ballistic", "distortion", "neutron", "tachyon", "plasma", "electron"].includes(record.subtype)) return subtype;
  return family === "质量驱动炮" ? family : `${subtype}${family}`;
}

function recordClassGrade(record) {
  const abbreviation = { Military: "军", Stealth: "隐", Industrial: "工", Civilian: "民", Competition: "竞" }[recordClass(record)] || "";
  const grade = { 1: "A", 2: "B", 3: "C", 4: "D" }[record.stats?.grade] || "";
  return `${abbreviation}${grade}`;
}

function recordSummary(record, fullType = false, manufacturer = false) {
  const type = record.category.id === "ship_component" ? recordComponentType(record)
    : fullType ? recordWeaponType(record) : recordSubtype(record);
  const parts = [record.category.label, type, recordClassGrade(record), sizeLabel(record.stats?.size)];
  if (manufacturer) parts.push(recordManufacturer(record));
  return parts.filter(Boolean).join(" · ");
}

function renderRecordSummary(record, manufacturer = false) {
  const short = recordSummary(record, false, manufacturer);
  const full = recordSummary(record, true, manufacturer);
  const description = [full, recordComponentClass(record), record.stats?.grade ? gradeLabel(record.stats.grade) : ""].filter(Boolean).join(" · ");
  const adaptive = full !== short ? ` data-summary-full="${escapeHtml(full)}" data-summary-short="${escapeHtml(short)}"` : "";
  return `<small${adaptive} title="${escapeHtml(description)}">${escapeHtml(full)}</small>`;
}

function fitRecordSummaries(root) {
  const candidates = [...root.querySelectorAll("[data-summary-full]")].filter(el => el.clientWidth);
  candidates.forEach(el => { el.textContent = el.dataset.summaryFull; });
  // Measure every full label before writes, so narrow rows fall back in one pass.
  const compact = candidates.filter(el => el.scrollWidth > el.clientWidth + 1
    || el.getBoundingClientRect().height > parseFloat(window.getComputedStyle(el).lineHeight) + 1);
  compact.forEach(el => { el.textContent = el.dataset.summaryShort; });
}

function recordMissionTypes(record) {
  const primary = recordMissions(record).filter(m => Object.hasOwn(m, "missionType"));
  if (primary.length || state.data?.sourcePolicy?.schemaVersion === 1) {
    return [...new Set(primary.map(m => m.missionType).filter(Boolean))].map(name => ({name, label: missionTypeOrder.find(([id]) => id === name)?.[1] || name}));
  }
  const meta = recordFlowcld(record);
  const names = Array.isArray(meta.rewardMissionTypes) ? meta.rewardMissionTypes : [];
  const namesCn = Array.isArray(meta.rewardMissionTypesCn) ? meta.rewardMissionTypesCn : [];
  return names.map((name, index) => ({
    name,
    label: namesCn[index] || missionTypeOrder.find(([id]) => id === name)?.[1] || name,
  }));
}

function recordSearchText(record) {
  const materials = getAllMaterials(record).flatMap((item) => [item.name, item.nameZh, materialZhName(item), materialName(item)]);
  const dismantleOutputs = getDismantleOutputs(record).flatMap((item) => [item.name, item.nameZh, materialZhName(item), materialName(item)]);
  const missionTypes = recordMissionTypes(record).flatMap((type) => [type.name, type.label]);
  const sourceFields = (record.sources || []).flatMap((source) => [
    source.poolName,
    source.poolNameZh,
    source.poolSource,
    source.poolSourceZh,
    ...(source.missions || []).flatMap((mission) => [
      mission.title,
      mission.titleZh,
      mission.faction,
      mission.factionZh,
      mission.category,
      mission.categoryZh,
      missionTitle(mission),
      missionSystemLabels(mission),
      ...(mission.systems || []),
    ]),
  ]);
  const fields = [
    record.name,
    recordName(record),
    record.category.id,
    record.category.label,
    record.type,
    recordType(record),
    recordComponentType(record),
    record.subtype,
    recordSubtype(record),
    recordWeaponType(record),
    record.manufacturer,
    recordManufacturer(record),
    recordGear(record),
    record.stats?.attachType,
    statZh(record, "attachType"),
    record.stats?.attachSubType,
    statZh(record, "attachSubType"),
    sizeLabel(record.stats?.size),
    record.stats?.grade ? gradeLabel(record.stats.grade) : "",
    recordComponentClass(record),
    recordClassGrade(record),
    ...materials,
    ...dismantleOutputs,
    ...missionTypes,
    ...sourceFields,
  ];
  return normalizeSearchText(fields.filter(Boolean).join(" "));
}

function prepareRecord(record) {
  return {
    ...record,
    _searchText: recordSearchText(record),
  };
}

function scheduleSearchApply() {
  window.clearTimeout(searchInputTimer);
  searchInputTimer = window.setTimeout(applyFilters, SEARCH_INPUT_DELAY_MS);
}

function relevanceScore(record) {
  let score = 0;
  if (record.category.id === "ship_component") score += 16;
  if (record.category.id === "ship_weapon") score += 14;
  if (record.category.id === "personal_weapon") score += 12;
  if (record.category.id === "weapon_attachment") score += 10;
  score += Math.min(state.mode === "dismantle" ? getDismantleOutputs(record).length : (record.sourceCount || 0), 10);
  if (recordName(record).toLowerCase().includes(state.query.toLowerCase())) score += 20;
  return score;
}

function optionTag(value, label, count, activeValue, triggerLabel = label) {
  const suffix = count === undefined ? "" : `（${formatNumber(count)}）`;
  const display = `${label}${suffix}`;
  const selected = value === activeValue;
  return `<button type="button" role="option" aria-selected="${selected}" class="filter-option${selected ? " active" : ""}" data-value="${escapeHtml(value)}" data-trigger-label="${escapeHtml(triggerLabel)}" title="${escapeHtml(display)}">${escapeHtml(display)}</button>`;
}

function selectedOptionLabel(container, value) {
  const option = Array.from(container.querySelectorAll(".filter-option")).find((item) => item.dataset.value === value);
  return option?.dataset.triggerLabel || option?.textContent || "全部";
}

function renderDropdown(container, optionsHtml, activeValue) {
  container.innerHTML = `
    <button type="button" class="filter-trigger" aria-haspopup="listbox" aria-expanded="false">
      <span>${escapeHtml("全部")}</span>
      <span class="filter-arrow">⌄</span>
    </button>
    <div class="filter-menu" role="listbox">${optionsHtml}</div>
  `;
  setSelectValue(container, activeValue);
}

function closeDropdowns(except = null) {
  document.querySelectorAll(".filter-select.open").forEach((item) => {
    if (item === except) return;
    item.classList.remove("open");
    item.querySelector(".filter-trigger")?.setAttribute("aria-expanded", "false");
  });
}

function setSelectValue(container, value) {
  container.dataset.value = value;
  container.querySelectorAll(".filter-option").forEach((option) => {
    const selected = option.dataset.value === value;
    option.classList.toggle("active", selected);
    option.setAttribute("aria-selected", String(selected));
  });
  const label = selectedOptionLabel(container, value);
  const triggerLabel = container.querySelector(".filter-trigger span");
  if (triggerLabel) triggerLabel.textContent = label;
  const trigger = container.querySelector(".filter-trigger");
  if (trigger) trigger.title = label;
}

function syncShipComponentFilters() {
  const visible = state.category === "ship_component";
  for (const [select, key] of [
    [els.componentTypeFilters, "componentType"],
    [els.componentClassFilters, "componentClass"],
  ]) {
    select.classList.toggle("disabled", !visible);
    if (!visible) {
      state[key] = "none";
      setSelectValue(select, state[key]);
      select.classList.remove("open");
    } else if (state[key] === "none") {
      state[key] = "all";
      setSelectValue(select, state[key]);
    }
  }
}

function modeRecords() {
  return state.mode === "dismantle" ? state.records.filter(hasDismantleOutputs) : state.records;
}

function getPopularMaterials(records = modeRecords()) {
  const labelByName = new Map();
  const counts = new Map();
  for (const record of records) {
    const materials = state.mode === "dismantle" ? getDismantleOutputs(record) : getAllMaterials(record);
    for (const material of materials) {
      if (!labelByName.has(material.name)) labelByName.set(material.name, materialZhName(material));
      counts.set(material.name, (counts.get(material.name) || 0) + 1);
    }
  }
  const ordered = flowcldMaterialOrder
    .filter((name) => counts.has(name))
    .map((name) => [name, labelByName.get(name) || flowcldMaterialLabels[name] || name, counts.get(name)]);
  const remaining = [...counts.entries()]
    .filter(([name]) => !flowcldMaterialOrder.includes(name))
    .sort((a, b) => b[1] - a[1])
    .map(([name, count]) => [name, labelByName.get(name) || flowcldMaterialLabels[name] || name, count]);
  return [...ordered, ...remaining];
}

function countBy(records, getter) {
  const counts = new Map();
  for (const record of records) {
    const value = getter(record);
    if (!value) continue;
    counts.set(value, (counts.get(value) || 0) + 1);
  }
  return counts;
}

function countMissionTypes(records) {
  const counts = new Map();
  for (const record of records) {
    for (const type of recordMissionTypes(record)) {
      counts.set(type.name, (counts.get(type.name) || 0) + 1);
    }
  }
  return counts;
}

function initFilters() {
  const records = modeRecords();
  const categoryCounts = countBy(records, (record) => record.category.id);
  renderDropdown(els.categoryFilters, categoryOrder
    .filter(([id]) => id === "all" || categoryCounts.has(id))
    .map(([id, label]) => {
      const count = id === "all" ? records.length : categoryCounts.get(id) || 0;
      return optionTag(id, label, count, state.category);
    })
    .join(""), state.category);

  renderDropdown(els.gradeFilters, gradeOrder
    .filter(([id]) => id === "all" || records.some((record) => String(record.stats.grade || "") === id))
    .map(([id, label]) => {
      const count = id === "all" ? records.length : records.filter((record) => String(record.stats.grade || "") === id).length;
      return optionTag(id, label, count, state.grade);
    })
    .join(""), state.grade);

  const componentRecords = records.filter((record) => record.category.id === "ship_component");
  const componentTypeCounts = countBy(componentRecords, (record) => record.type);
  const componentTypeActive = state.category === "ship_component" ? state.componentType : "none";
  renderDropdown(els.componentTypeFilters, [
    optionTag("none", "无", undefined, componentTypeActive),
    ...componentTypeOrder
      .filter(([id]) => id === "all" || componentTypeCounts.has(id))
      .map(([id, label]) => {
        const count = id === "all" ? componentRecords.length : componentTypeCounts.get(id) || 0;
        return optionTag(id, label, count, componentTypeActive);
      }),
  ].join(""), componentTypeActive);

  const componentClassCounts = countBy(componentRecords, recordClass);
  const componentClassActive = state.category === "ship_component" ? state.componentClass : "none";
  renderDropdown(els.componentClassFilters, [
    optionTag("none", "无", undefined, componentClassActive),
    ...componentClassOrder
      .filter(([id]) => id === "all" || componentClassCounts.has(id))
      .map(([id, label]) => {
        const count = id === "all" ? componentRecords.length : componentClassCounts.get(id) || 0;
        return optionTag(id, label, count, componentClassActive);
      }),
  ].join(""), componentClassActive);

  const manufacturerLabel = new Map();
  const manufacturerTriggerLabel = new Map();
  for (const record of records) {
    if (!manufacturerLabel.has(record.manufacturer)) {
      const zh = recordManufacturer(record);
      const en = record.manufacturer;
      manufacturerLabel.set(en, zh && zh !== en ? `${zh} (${en})` : en);
      manufacturerTriggerLabel.set(en, zh || en);
    }
  }
  renderDropdown(els.manufacturerFilters, [
    optionTag("all", "全部", records.length, state.manufacturer),
    ...[...countBy(records, (record) => record.manufacturer).entries()]
      .sort((a, b) => b[1] - a[1])
      .map(([name, count]) => optionTag(name, manufacturerLabel.get(name) || name, count, state.manufacturer, manufacturerTriggerLabel.get(name) || name)),
  ].join(""), state.manufacturer);

  renderDropdown(els.materialFilters, [
    optionTag("all", "全部", records.length, state.material),
    ...getPopularMaterials(records).map(([name, label, count]) => {
      const display = materialDisplayLabel(name, label);
      return optionTag(name, display, count, state.material, display);
    }),
  ].join(""), state.material);

  const missionTypeCounts = countMissionTypes(records);
  renderDropdown(els.missionTypeFilters, missionTypeOrder
    .filter(([id]) => id === "all" || missionTypeCounts.has(id))
    .map(([id, label]) => {
      const count = id === "all" ? records.filter((record) => recordMissionTypes(record).length).length : missionTypeCounts.get(id) || 0;
      return optionTag(id, label, count, state.missionType);
    })
    .join(""), state.missionType);

  syncShipComponentFilters();
}

function updateModeUI() {
  const dismantle = state.mode === "dismantle";
  document.documentElement.dataset.queryMode = state.mode;
  els.modeTabs.forEach((button) => {
    const active = button.dataset.mode === state.mode;
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", String(active));
  });
  els.filterTitle.textContent = dismantle ? "拆解物品" : "制造蓝图";
  els.filterResultLabel.textContent = dismantle ? "可拆解物品" : "相关蓝图";
  els.summaryLabel.textContent = dismantle ? "可拆解物品" : "蓝图索引";
  els.categoryFilterLabel.textContent = dismantle ? "物品类型" : "类型";
  els.materialFilterLabel.textContent = dismantle ? "回收物" : "材料";
  els.resultMetaLabel.textContent = dismantle ? "回收" : "来源";
  els.sourceSort.textContent = dismantle ? "回收种类" : "来源";
  els.missionTypeGroup.hidden = dismantle;
  els.sourceToggle.hidden = dismantle;
  els.searchInput.placeholder = dismantle
    ? "输入可拆解物品、类型、制造商或回收物"
    : "输入蓝图、武器、组件、制造商或材料";
}

function setMode(mode) {
  if (!['craft', 'dismantle'].includes(mode) || mode === state.mode) return;
  state.mode = mode;
  state.category = "all";
  state.componentType = "none";
  state.grade = "all";
  state.componentClass = "none";
  state.manufacturer = "all";
  state.material = "all";
  state.missionType = "all";
  state.sourceOnly = false;
  state.selectedId = null;
  els.sourceOnly.checked = false;
  updateModeUI();
  initFilters();
  applyFilters();
}

function resetFilters() {
  state.category = "all";
  state.componentType = "none";
  state.grade = "all";
  state.componentClass = "none";
  state.manufacturer = "all";
  state.material = "all";
  state.missionType = "all";
  state.sourceOnly = false;
  els.sourceOnly.checked = false;
  setSelectValue(els.categoryFilters, state.category);
  setSelectValue(els.componentTypeFilters, state.componentType);
  setSelectValue(els.gradeFilters, state.grade);
  setSelectValue(els.componentClassFilters, state.componentClass);
  setSelectValue(els.manufacturerFilters, state.manufacturer);
  setSelectValue(els.materialFilters, state.material);
  setSelectValue(els.missionTypeFilters, state.missionType);
  syncShipComponentFilters();
  applyFilters();
}

function bindFilterSelect(select, key) {
  select.addEventListener("click", (event) => {
    if (select.classList.contains("disabled")) return;
    const trigger = event.target.closest(".filter-trigger");
    const option = event.target.closest(".filter-option");
    if (trigger) {
      const willOpen = !select.classList.contains("open");
      closeDropdowns(select);
      select.classList.toggle("open", willOpen);
      trigger.setAttribute("aria-expanded", String(willOpen));
      return;
    }
    if (!option) return;
    state[key] = option.dataset.value;
    setSelectValue(select, state[key]);
    closeDropdowns();
    if (key === "category") syncShipComponentFilters();
    applyFilters();
  });

  select.addEventListener("keydown", (event) => {
    const options = [...select.querySelectorAll(".filter-option")];
    const currentIndex = options.indexOf(document.activeElement);

    if (event.key === "Escape") {
      closeDropdowns();
      select.querySelector(".filter-trigger")?.focus();
      return;
    }

    if (event.target.closest(".filter-trigger") && (event.key === "ArrowDown" || event.key === "ArrowUp")) {
      event.preventDefault();
      closeDropdowns(select);
      select.classList.add("open");
      select.querySelector(".filter-trigger")?.setAttribute("aria-expanded", "true");
      const selectedIndex = options.findIndex((option) => option.getAttribute("aria-selected") === "true");
      options[Math.max(0, selectedIndex)]?.focus();
      return;
    }

    if (currentIndex < 0 || !["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) return;
    event.preventDefault();
    const nextIndex = event.key === "Home"
      ? 0
      : event.key === "End"
        ? options.length - 1
        : (currentIndex + (event.key === "ArrowDown" ? 1 : -1) + options.length) % options.length;
    options[nextIndex]?.focus();
  });
}

function bindEvents() {
  document.querySelector("#openPlan")?.addEventListener("click", event => openCraftPlan(event.currentTarget));
  window.addEventListener("hashchange", restoreSharedBlueprint);
  window.addEventListener("resize", () => {
    window.cancelAnimationFrame(summaryResizeFrame);
    summaryResizeFrame = window.requestAnimationFrame(() => fitRecordSummaries(document));
  });
  els.searchForm.addEventListener("submit", (event) => event.preventDefault());

  els.searchInput.addEventListener("input", (event) => {
    state.query = event.target.value.trim();
    scheduleSearchApply();
  });

  els.clearSearch.addEventListener("click", () => {
    window.clearTimeout(searchInputTimer);
    els.searchInput.value = "";
    state.query = "";
    applyFilters();
  });

  bindFilterSelect(els.categoryFilters, "category");
  bindFilterSelect(els.componentTypeFilters, "componentType");
  bindFilterSelect(els.gradeFilters, "grade");
  bindFilterSelect(els.componentClassFilters, "componentClass");
  bindFilterSelect(els.manufacturerFilters, "manufacturer");
  bindFilterSelect(els.materialFilters, "material");
  bindFilterSelect(els.missionTypeFilters, "missionType");

  els.modeTabs.forEach((button) => {
    button.addEventListener("click", () => setMode(button.dataset.mode));
  });

  els.sourceOnly.addEventListener("change", (event) => {
    state.sourceOnly = event.target.checked;
    applyFilters();
  });

  els.favoritesToggle.addEventListener("click", () => {
    state.favoritesOnly = !state.favoritesOnly;
    updateFavoriteControl();
    applyFilters();
  });

  els.resetFilters.addEventListener("click", resetFilters);

  document.addEventListener("click", (event) => {
    if (event.target.closest(".filter-select")) return;
    closeDropdowns();
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeDropdowns();
      closeSignalTooltip();
    }
  });

  document.querySelectorAll(".sort").forEach((button) => {
    button.addEventListener("click", () => {
      state.sort = button.dataset.sort;
      document.querySelectorAll(".sort").forEach((item) => {
        const active = item.dataset.sort === state.sort;
        item.classList.toggle("active", active);
        item.setAttribute("aria-pressed", String(active));
      });
      applyFilters();
    });
  });

  els.resultList.addEventListener("click", (event) => {
    const loadMore = event.target.closest("[data-load-more]");
    if (loadMore) {
      state.visibleResults = Math.min(state.filtered.length, state.visibleResults + RESULT_BATCH_SIZE);
      renderResults();
      return;
    }

    const card = event.target.closest(".result-card");
    if (!card) return;
    selectRecord(card.dataset.id);
  });

  els.detailPanel.addEventListener("click", (event) => {
    const qualityCapsule = event.target.closest(".quality-number");
    if (qualityCapsule) {
      const bounds = qualityCapsule.getBoundingClientRect();
      if (event.clientX >= bounds.left && event.clientX <= bounds.right && event.clientY >= bounds.top && event.clientY <= bounds.bottom) {
        qualityCapsule.querySelector("[data-quality-number]").focus();
      }
      return;
    }
    const signalButton = event.target.closest("[data-signal-trigger]");
    if (signalButton) {
      showSignalTooltip(signalButton);
      return;
    }
    if (!event.target.closest(".mineral-location-tooltip")) closeSignalTooltip();
    const plan = event.target.closest("[data-add-plan]");
    if (plan) { addToPlan(plan.dataset.addPlan, plan); return; }
    const share = event.target.closest("[data-share-blueprint]");
    if (share) { shareBlueprint(share.dataset.shareBlueprint, share); return; }
    const mission = event.target.closest("[data-mission-id]");
    if (mission) {
      openMissionInfo(mission.dataset.missionId, mission);
      return;
    }
    const close = event.target.closest("[data-close-mineral]");
    if (close || event.target.classList.contains("mineral-overlay")) {
      closeMineralInfo();
      return;
    }

    const favoriteButton = event.target.closest("[data-toggle-favorite]");
    if (favoriteButton) {
      toggleFavorite(favoriteButton.dataset.toggleFavorite);
      return;
    }

    const mineral = event.target.closest("[data-mineral]");
    if (!mineral) return;
    openMineralInfo(mineral.dataset.mineral);
  });

  els.detailPanel.addEventListener("input", (event) => {
    const input = event.target.closest("[data-quality-input], [data-quality-number]");
    if (!input) return;
    const record = state.records.find((item) => item.id === input.dataset.recordId);
    if (!record) return;
    const slotIndex = Number(input.dataset.slotIndex);
    const slot = getFirstTier(record).slots?.[slotIndex];
    if (!slot) return;
    if (input.matches("[data-quality-number]")) input.closest(".quality-number").style.setProperty("--quality-digits", (input.value || input.placeholder).length);
    const quality = Number(input.value);
    if (!input.value.trim()) {
      if (input.validity?.badInput) { input.value = qualitySlotValue(record, slot, slotIndex); return; }
      input.closest(".quality-number")?.setAttribute("data-confirmed", "false");
      return;
    }
    if (!Number.isFinite(quality)) return;
    if (quality < 0 || quality > 1000 || !Number.isInteger(quality)) {
      setSlotQuality(record, slotIndex, quality);
      return;
    }
    if (quality < qualitySlotMinimum(slot)) { input.closest(".quality-number").dataset.confirmed = "false"; return; }
    setSlotQuality(record, slotIndex, quality);
  });
  els.detailPanel.addEventListener("focusin", event => {
    const input = event.target.closest("[data-quality-number]");
    if (!input) return;
    const record = state.records.find(item => item.id === input.dataset.recordId);
    const slotIndex = Number(input.dataset.slotIndex);
    const slot = record && getFirstTier(record).slots?.[slotIndex];
    if (!slot) return;
    input.placeholder = qualitySlotValue(record, slot, slotIndex);
    input.value = "";
    input.closest(".quality-number").dataset.confirmed = "false";
  });
  els.detailPanel.addEventListener("focusout", event => {
    const input = event.target.closest("[data-quality-number]");
    if (!input) return;
    const record = state.records.find(item => item.id === input.dataset.recordId);
    const slotIndex = Number(input.dataset.slotIndex);
    const slot = record && getFirstTier(record).slots?.[slotIndex];
    if (!slot) return;
    if (input.value.trim()) { setSlotQuality(record, slotIndex, Number(input.value)); return; }
    const confirmed = state.qualityConfirmed[qualitySlotKey(record, slotIndex)] === true;
    input.placeholder = qualitySlotValue(record, slot, slotIndex);
    input.value = confirmed ? input.placeholder : "";
    input.closest(".quality-number").dataset.confirmed = String(confirmed);
  });
  els.detailPanel.addEventListener("beforeinput", event => {
    if (event.target.matches("[data-quality-number]") && event.data && !/^\d+$/.test(event.data)) event.preventDefault();
  });
  els.detailPanel.addEventListener("pointerover", event => {
    const button = event.target.closest("[data-signal-trigger]");
    if (button && button.getAttribute("aria-expanded") !== "true") showSignalTooltip(button);
  });
  els.detailPanel.addEventListener("focusin", event => {
    if (event.target.matches("[data-signal-trigger]")) showSignalTooltip(event.target);
  });
  els.detailPanel.addEventListener("focusout", event => {
    if (event.target.matches("[data-signal-trigger]")) closeSignalTooltip();
  });
  document.addEventListener("scroll", event => {
    if (!event.target.closest?.(".mineral-location-tooltip")) closeSignalTooltip();
  }, true);
  window.addEventListener("resize", closeSignalTooltip);
}

function materialMatches(record) {
  if (state.material === "all") return true;
  const materials = state.mode === "dismantle" ? getDismantleOutputs(record) : getAllMaterials(record);
  return materials.some((item) => item.name === state.material || item.nameZh === state.material);
}

function componentClassMatches(record) {
  if (state.category !== "ship_component") return true;
  return state.componentClass === "all" || state.componentClass === "none" || recordClass(record) === state.componentClass;
}

function componentTypeMatches(record) {
  if (state.category !== "ship_component") return true;
  return state.componentType === "all" || state.componentType === "none" || record.type === state.componentType;
}

function missionTypeMatches(record) {
  if (state.mode === "dismantle") return true;
  return state.missionType === "all" || recordMissionTypes(record).some((type) => type.name === state.missionType);
}

function applyFilters() {
  const query = normalizeSearchText(state.query);
  syncShipComponentFilters();

  state.filtered = state.records.filter((record) => {
    if (state.mode === "dismantle" && !hasDismantleOutputs(record)) return false;
    if (state.category !== "all" && record.category.id !== state.category) return false;
    if (!componentTypeMatches(record)) return false;
    if (state.grade !== "all" && String(record.stats.grade || "") !== state.grade) return false;
    if (!componentClassMatches(record)) return false;
    if (state.manufacturer !== "all" && record.manufacturer !== state.manufacturer) return false;
    if (!materialMatches(record)) return false;
    if (!missionTypeMatches(record)) return false;
    if (state.mode === "craft" && state.sourceOnly && !(record.sourceCount > 0)) return false;
    if (state.favoritesOnly && !isFavorite(record)) return false;
    if (query && !(record._searchText || recordSearchText(record)).includes(query)) return false;
    return true;
  });

  state.filtered.sort((a, b) => {
    if (state.sort === "name") return recordName(a).localeCompare(recordName(b), "zh-CN");
    if (state.sort === "sources") {
      const aCount = state.mode === "dismantle" ? getDismantleOutputs(a).length : (a.sourceCount || 0);
      const bCount = state.mode === "dismantle" ? getDismantleOutputs(b).length : (b.sourceCount || 0);
      return bCount - aCount || recordName(a).localeCompare(recordName(b), "zh-CN");
    }
    return relevanceScore(b) - relevanceScore(a) || recordName(a).localeCompare(recordName(b), "zh-CN");
  });

  if (!state.filtered.some((record) => record.id === state.selectedId)) {
    state.selectedId = state.filtered[0]?.id || null;
  }
  state.visibleResults = Math.min(RESULT_BATCH_SIZE, state.filtered.length);

  renderResults();
  renderDetail();
  renderCounts();
}

function activeFilterCount() {
  const values = [state.category, state.grade, state.manufacturer, state.material];
  if (state.mode === "craft") values.push(state.missionType);
  if (state.category === "ship_component") values.push(state.componentType, state.componentClass);
  return values.filter((value) => value !== "all").length + (state.mode === "craft" && state.sourceOnly ? 1 : 0) + (state.favoritesOnly ? 1 : 0);
}

function renderCounts() {
  const count = state.filtered.length;
  els.resultTitle.textContent = `${formatNumber(count)} 个`;
  els.modalResultCount.textContent = formatNumber(count);
  els.filterCount.textContent = activeFilterCount();
  updateFavoriteControl();
}

function renderResults() {
  if (!state.filtered.length) {
    els.resultList.innerHTML = `
      <div class="empty-state">
        <h3>${state.mode === "dismantle" ? "暂无可拆解物品" : "暂无蓝图"}</h3>
        <p>无</p>
      </div>
    `;
    return;
  }

  const visibleRecords = state.filtered.slice(0, state.visibleResults);
  const cards = visibleRecords
    .map((record) => {
      const outputCount = getDismantleOutputs(record).length;
      const sourceLabel = state.mode === "dismantle"
        ? `${formatNumber(outputCount)} 种回收物`
        : record.sourceCount > 0 ? "任务奖励" : "无任务来源";
      return `
        <button class="result-card ${escapeHtml(record.category.id)}${record.id === state.selectedId ? " active" : ""}" type="button" data-id="${escapeHtml(record.id)}" aria-current="${record.id === state.selectedId ? "true" : "false"}">
          <span class="row-dot"></span>
          <span class="row-main">
            <strong>${escapeHtml(recordName(record))}</strong>
            ${renderRecordSummary(record, true)}
          </span>
          <span class="source-badge ${state.mode === "craft" && !(record.sourceCount > 0) ? "muted" : ""}">${sourceLabel}</span>
        </button>
      `;
    })
    .join("");

  const loadMore = state.visibleResults < state.filtered.length
    ? `<button class="load-more-results" type="button" data-load-more>继续加载 <strong>${formatNumber(state.visibleResults)}</strong> / ${formatNumber(state.filtered.length)}</button>`
    : "";
  els.resultList.innerHTML = cards + loadMore;
  fitRecordSummaries(els.resultList);
}

function selectRecord(id) {
  state.selectedId = id;
  if (window.history?.replaceState) window.history.replaceState(null, "", blueprintShareUrl(id));
  els.resultList.querySelectorAll(".result-card").forEach((card) => {
    const active = card.dataset.id === id;
    card.classList.toggle("active", active);
    card.setAttribute("aria-current", String(active));
  });
  renderDetail();
}

function renderDismantleDetail(record) {
  const componentClass = recordComponentClass(record);
  const componentType = record.category.id === "ship_component" ? recordComponentType(record) : recordType(record);
  const outputs = getDismantleOutputs(record);
  const specs = [
    ["物品", record.category.label],
    ["类型", componentType],
    ["子类", recordSubtype(record) || "无"],
    ["类别", componentClass || "无"],
    ["厂商", recordManufacturer(record)],
    ["尺寸", sizeLabel(record.stats.size)],
    ["等级", record.stats.grade ? gradeLabel(record.stats.grade) : "未知"],
  ];

  els.detailPanel.innerHTML = `
    <div class="detail-scroll dismantle-detail">
      <div class="detail-head">
        <span>拆解详情</span>
        <span class="detail-head-actions">
          <button type="button" class="favorite-detail-button" data-share-blueprint="${escapeHtml(record.id)}">分享</button>
          <button type="button" class="favorite-detail-button${isFavorite(record) ? " active" : ""}" data-toggle-favorite="${escapeHtml(record.id)}" aria-pressed="${isFavorite(record)}">${isFavorite(record) ? "已收藏" : "收藏物品"}</button>
          <strong>${formatNumber(outputs.length)} 种回收物</strong>
        </span>
      </div>
      <h2>${escapeHtml(recordName(record))}</h2>

      <section class="detail-section">
        <h3>物品信息</h3>
        <div class="dismantle-info-line">
          ${specs.map(([label, value]) => `<span><small>${escapeHtml(label)}</small><strong>${escapeHtml(value)}</strong></span>`).join("")}
        </div>
      </section>

      ${renderDismantle(record, true)}
    </div>
  `;
}

function renderDetail() {
  const record = state.records.find((item) => item.id === state.selectedId);
  if (!record) {
    els.detailPanel.innerHTML = `
      <div class="detail-scroll">
        <div class="empty-state">
          <h3>${state.mode === "dismantle" ? "选择一个可拆解物品" : "选择一个蓝图"}</h3>
          <p>${state.mode === "dismantle" ? "左侧点击任意物品，查看拆解后的回收材料。" : "左侧点击任意结果，查看制作材料和任务来源。"}</p>
        </div>
      </div>
    `;
    return;
  }

  if (state.mode === "dismantle") {
    renderDismantleDetail(record);
    return;
  }

  const tier = getFirstTier(record);
  const materials = getAllMaterials(record);
  const componentClass = recordComponentClass(record);
  const componentType = record.category.id === "ship_component" ? recordComponentType(record) : recordType(record);
  const missionTypes = recordMissionTypes(record);
  const specs = [
    ["分类", record.category.label],
    ["类型", componentType],
    ["子类", recordSubtype(record)],
    ["组件类别", componentClass || "无"],
    ["装备域", recordGear(record)],
    ["挂点", statZh(record, "attachType") || "未知"],
    ["尺寸", sizeLabel(record.stats.size)],
    ["等级", record.stats.grade ? gradeLabel(record.stats.grade) : "未知"],
    ["任务类型", missionTypes.length ? missionTypes.map((type) => type.label).join(" / ") : "无"],
  ];

  els.detailPanel.innerHTML = `
    <div class="detail-scroll">
      <div class="detail-head">
        <span>蓝图详情</span>
        <span class="detail-head-actions">
          <button type="button" class="favorite-detail-button${isFavorite(record) ? " active" : ""}" data-toggle-favorite="${escapeHtml(record.id)}" aria-pressed="${isFavorite(record)}">${isFavorite(record) ? "已收藏" : "收藏蓝图"}</button>
          <strong>${record.sourceCount > 0 ? "任务奖励" : "暂无任务来源"}</strong>
        </span>
      </div>
      <h2>${escapeHtml(recordName(record))}</h2>
      <div class="detail-tags">
        <span>${escapeHtml(record.category.label)}</span>
        ${record.category.id === "ship_component" ? `<span>${escapeHtml(componentType)}</span>` : ""}
        <span>${escapeHtml(recordManufacturer(record))}</span>
        ${componentClass ? `<span>${escapeHtml(componentClass)}</span>` : ""}
        <span>制作 ${formatTime(tier.craftTimeSeconds)}</span>
      </div>

      <div class="detail-tools">
        <button type="button" class="favorite-detail-button" data-add-plan="${escapeHtml(record.id)}">加入制作清单</button>
        <button type="button" class="favorite-detail-button" data-share-blueprint="${escapeHtml(record.id)}">分享蓝图</button>
      </div>

      ${renderQualitySummary(record)}
      ${renderBaseStats(record)}

      <section class="detail-section">
        <h3>制作材料</h3>
        <div class="material-list">
          ${
            materials.length
              ? materials
                  .map(
                    (item) => {
                      const locationInfo = mineralLocationInfo(item.name);
                      const locationLabel = locationInfo?.hasReliableLocations ? "矿点" : "暂无矿点";
                      const hasQuality = Boolean(item.slotData?.modifiers?.length);
                      return `
                    <div class="material-item${hasQuality ? " has-quality" : ""}">
                      <button class="material-summary material-item-button" type="button" data-mineral="${escapeHtml(item.name)}">
                        <span>
                          <strong>${escapeHtml(materialName(item))}</strong>
                          <small>${escapeHtml(materialSlot(item))} · ${escapeHtml(materialKind(item))}${item.minQuality ? ` · 最低品质 ${formatNumber(item.minQuality)}` : ""}</small>
                        </span>
                      </button>
                      ${renderMaterialQuality(record, item.slotData, item.slotIndex)}
                      <span class="material-side">
                        <button class="material-location-badge" type="button" data-mineral="${escapeHtml(item.name)}">${locationLabel}</button>
                        <strong>x${formatNumber(item.quantity)}</strong>
                      </span>
                    </div>
                  `;
                    },
                  )
                  .join("")
              : `<div class="material-item"><span><strong>暂无材料</strong><small>无</small></span></div>`
          }
        </div>
      </section>

      <section class="detail-section">
        <h3>获取方法</h3>
        <div class="source-list">${renderSources(record)}</div>
      </section>

      <section class="detail-section">
        <h3>规格</h3>
        <div class="spec-grid">
          ${specs.map(([label, value]) => `<div class="spec-item"><strong>${escapeHtml(label)}</strong><span>${escapeHtml(value)}</span></div>`).join("")}
        </div>
      </section>
    </div>
  `;
}

function recordMissions(record) {
  const missions = new Map();
  for (const source of record.sources || []) {
    for (const mission of source.missions || []) {
      const key = mission.id || JSON.stringify([mission.debugName, mission.title, mission.faction, mission.rewardUEC, mission.systems]);
      if (!missions.has(key)) missions.set(key, mission);
    }
  }
  return [...missions.values()];
}

function renderSources(record) {
  const missions = recordMissions(record);
  if (!missions.length) {
    return `
      <div class="source-item">
        <strong>暂无任务来源</strong>
        <small>无</small>
      </div>
    `;
  }

  const rows = missions.map((mission) => {
    const reward = mission.rewardUEC != null ? ` · ${formatNumber(mission.rewardUEC)} aUEC` : "";
    const faction = missionFaction(mission) ? ` · ${escapeHtml(missionFaction(mission))}` : "";
    const clickable = Boolean(mission.id && state.data.missionRewards?.missions?.[mission.id]);
    const content = `<strong>${renderBlueprintText(missionTitle(mission))}</strong> <small>· <b>${escapeHtml(missionSystemLabels(mission))}</b>${faction}${reward}</small>`;
    return `<li>${clickable ? `<button type="button" class="source-mission-button" data-mission-id="${escapeHtml(mission.id)}" aria-haspopup="dialog" title="查看任务奖励">${content}<span aria-hidden="true">›</span></button>` : `<div class="source-mission-button">${content}</div>`}</li>`;
  });
  const previewCount = rows.length - SOURCE_TASK_PREVIEW_LIMIT < SOURCE_TASK_MIN_HIDDEN
    ? rows.length : SOURCE_TASK_PREVIEW_LIMIT;
  return `
    <div class="source-item">
      <strong>任务来源</strong>
      <span class="source-line"><span>任务 ${formatNumber(missions.length)}</span></span>
      <ul class="source-missions">${rows.slice(0, previewCount).join("")}</ul>
      ${rows.length > previewCount ? `<details class="source-more">
        <summary><span class="source-expand-label">展开全部 ${formatNumber(missions.length)} 条任务</span><span class="source-collapse-label">收起更多任务</span></summary>
        <ul class="source-missions">${rows.slice(previewCount).join("")}</ul>
      </details>` : ""}
    </div>`;
}

async function fetchJson(path) {
  if (typeof DecompressionStream === "function") {
    try {
      const compressedResponse = await fetch(`${path}.gz?v=${DATA_VERSION}`);
      if (compressedResponse.ok && compressedResponse.body) {
        const decompressedStream = compressedResponse.body.pipeThrough(new DecompressionStream("gzip"));
        return JSON.parse(await new Response(decompressedStream).text());
      }
    } catch (error) {
      console.info("压缩数据不可用，改用兼容数据源。", error);
    }
  }

  const response = await fetch(`${path}?v=${DATA_VERSION}`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

async function boot() {
  state.favorites = loadFavorites();
  try { state.craftPlan = validPlan(JSON.parse(window.localStorage.getItem(PLAN_STORAGE_KEY) || "[]")); }
  catch { state.craftPlan = []; state.planSaved = false; }
  els.resultList.innerHTML = `<div class="loading-state"><div><h3>正在加载蓝图</h3><p>请稍候...</p></div></div>`;
  try {
    const [blueprintData, mineralData] = await Promise.all([
      fetchJson("./data/blueprint-index.json"),
      fetchJson("./data/mineral-locations.json").catch(() => null),
    ]);
    state.data = blueprintData;
    if (!Array.isArray(state.data.records)) throw new Error("blueprint-index.json 缺少 records 数组");
    if (mineralData) {
      state.mineralLocations = mineralData;
      if (mineralData.metadata?.schemaVersion === 2 && mineralData.metadata.sourceVersion !== state.data.version) {
        state.mineralLocations = {materials: {}, metadata: null};
      }
    }
    state.records = state.data.records.map(prepareRecord);
    initMissionRewards();
    els.versionBadge.textContent = state.data.version;
    els.dataUpdatedBadge.textContent = formatDataUpdatedAt(state.data.dataUpdatedAt);
    els.dataStatus.setAttribute(
      "aria-label",
      `${state.data.version}，${formatDataUpdatedAt(state.data.dataUpdatedAt)}，北京时间`,
    );
    updateModeUI();
    initFilters();
    bindEvents();
    applyFilters();
    updatePlanCount();
    restoreSharedBlueprint();
  } catch (error) {
    console.error("蓝图数据加载失败。", error);
    els.resultList.innerHTML = `
      <div class="empty-state">
        <h3>加载失败</h3>
        <p>请检查网络后重试。</p>
        <button class="retry-load" type="button" data-retry-load>重新加载</button>
      </div>
    `;
    els.resultList.querySelector("[data-retry-load]")?.addEventListener("click", boot, { once: true });
  }
}

boot();
