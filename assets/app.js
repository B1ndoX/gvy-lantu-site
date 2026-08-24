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
  sort: "relevance",
  visibleResults: 0,
};

const DATA_VERSION = "20260818T065926Z-4-9-0-live-12344265";
const SEARCH_INPUT_DELAY_MS = 120;
const RESULT_BATCH_SIZE = 140;
const FAVORITES_STORAGE_KEY = "gvy-lantu-favorite-blueprints-v1";
let searchInputTimer = 0;

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
  ["Refueling", "Refueling"],
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
  if (!seconds) return "未知";
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
  return flowcldMaterialLabels[item.name] || preferZh(item.nameZh, item.name);
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

function qualitySlotValue(record, slot, slotIndex) {
  const key = qualitySlotKey(record, slotIndex);
  const minimum = Math.max(0, ...slot.options.map((option) => Number(option.minQuality) || 0));
  const stored = Number(state.qualityValues[key]);
  if (Number.isFinite(stored)) return Math.max(minimum, Math.min(1000, stored));
  return Math.max(minimum, 500);
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

function renderQualityModifiers(slot, quality) {
  const modifiers = slot.modifiers || [];
  if (!modifiers.length) return "";
  return `
    <div class="quality-modifier-list">
      ${modifiers
        .map((modifier) => {
          const value = modifierFactor(modifier, quality);
          const valueLabel = modifier.additive ? `修正 ${formatNumber(value)}` : `系数 ${value.toFixed(2)}×`;
          return `<span><strong>${escapeHtml(modifierName(modifier))}</strong><small>${escapeHtml(valueLabel)}</small></span>`;
        })
        .join("")}
    </div>
  `;
}

function renderMaterialQuality(record, slot, slotIndex) {
  if (!(slot?.modifiers || []).length) return "";
  const quality = qualitySlotValue(record, slot, slotIndex);
  const minimum = Math.max(0, ...slot.options.map((option) => Number(option.minQuality) || 0));
  return `
    <div class="material-quality" data-quality-slot="${escapeHtml(qualitySlotKey(record, slotIndex))}">
      <div class="material-quality-control">
        <input type="range" min="${minimum}" max="1000" step="1" value="${quality}" data-quality-input data-record-id="${escapeHtml(record.id)}" data-slot-index="${slotIndex}" aria-label="${escapeHtml(preferZh(slot.nameZh, slot.name))}品质" />
        <output>品质 ${formatNumber(quality)}</output>
      </div>
      ${renderQualityModifiers(slot, quality)}
    </div>
  `;
}

function renderDismantle(record, standalone = false) {
  const dismantle = record.dismantle || {};
  const outputs = dismantle.outputs || [];
  if (!outputs.length) return "";
  return `
    <section class="detail-section dismantle-section">
      <h3>${standalone ? "拆解所得" : "拆解回收"}</h3>
      <p class="detail-note">按当前 LIVE 拆解规则计算，仅显示可回收资源；实际结果以游戏版本为准。</p>
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
  const signal = location.signal || {};
  const values = signal.values || [];
  if (!values.length) return "";
  const meta = [];
  if (signal.probability) meta.push(`产出权重 ${signal.probability}%`);
  if (signal.maxCluster) meta.push(`最大 ${signal.maxCluster} 簇`);
  return `
    <span class="mineral-signal-badge" aria-hidden="true">信号</span>
    <div class="mineral-location-tooltip" role="tooltip">
      <strong>该地点信号值</strong>
      ${meta.length ? `<small>${escapeHtml(meta.join(" · "))}</small>` : ""}
      <span class="mineral-signal-values">
        ${values.map((value) => `<b>${escapeHtml(formatNumber(value))}</b>`).join(" ")}
      </span>
    </div>
  `;
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
                  <div class="mineral-location-item${signalTooltip ? " has-signal" : ""}" ${signalTooltip ? 'tabindex="0"' : ""}>
                    <strong>${escapeHtml(mineralLocationLabel(location))}</strong>
                    ${subline ? `<small>${escapeHtml(subline)}</small>` : ""}
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
  const displayName = materialDisplayLabel(name, flowcldMaterialLabels[name]);
  const commodity = info?.commodityName && info.commodityName !== name ? info.commodityName : "";
  const hasLocationSignals = mineralLocationGroups.some(([key]) =>
    (info?.locations?.[key] || []).some((location) => (location.signal?.values || []).length),
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
          ${renderMineralLocationGroups(info)}
        </div>
        <footer class="mineral-source">
          更新时间 ${escapeHtml(updatedAt)}
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
  els.detailPanel.querySelector(".mineral-overlay")?.remove();
}

function missionTitle(mission) {
  return preferZh(mission.titleZh, mission.title);
}

function missionFaction(mission) {
  return preferZh(mission.factionZh, mission.faction);
}

function recordFlowcld(record) {
  return record.flowcld || {};
}

function recordComponentClass(record) {
  const meta = recordFlowcld(record);
  return preferZh(meta.itemClassCn, componentClassOrder.find(([id]) => id === meta.itemClass)?.[1] || meta.itemClass);
}

function recordComponentType(record) {
  return componentTypeOrder.find(([id]) => id === record.type)?.[1] || recordType(record);
}

function recordMissionTypes(record) {
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

  const componentClassCounts = countBy(componentRecords, (record) => recordFlowcld(record).itemClass);
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
    const input = event.target.closest("[data-quality-input]");
    if (!input) return;
    const record = state.records.find((item) => item.id === input.dataset.recordId);
    if (!record) return;
    const slotIndex = Number(input.dataset.slotIndex);
    const slot = getFirstTier(record).slots?.[slotIndex];
    if (!slot) return;
    const quality = Number(input.value);
    state.qualityValues[qualitySlotKey(record, slotIndex)] = quality;
    const container = input.closest("[data-quality-slot]");
    container.querySelector("output").textContent = `品质 ${formatNumber(quality)}`;
    const existing = container.querySelector(".quality-modifier-list");
    if (existing) existing.outerHTML = renderQualityModifiers(slot, quality);
  });
}

function materialMatches(record) {
  if (state.material === "all") return true;
  const materials = state.mode === "dismantle" ? getDismantleOutputs(record) : getAllMaterials(record);
  return materials.some((item) => item.name === state.material || item.nameZh === state.material);
}

function componentClassMatches(record) {
  if (state.category !== "ship_component") return true;
  return state.componentClass === "all" || state.componentClass === "none" || recordFlowcld(record).itemClass === state.componentClass;
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
      const size = sizeLabel(record.stats.size);
      const grade = record.stats.grade ? gradeLabel(record.stats.grade) : "未知等级";
      const componentClass = recordComponentClass(record);
      const metaParts = record.category.id === "ship_component"
        ? [record.category.label, recordComponentType(record), recordManufacturer(record), componentClass, size, grade]
        : [record.category.label, recordManufacturer(record), recordSubtype(record), size, grade];
      return `
        <button class="result-card ${escapeHtml(record.category.id)}${record.id === state.selectedId ? " active" : ""}" type="button" data-id="${escapeHtml(record.id)}" aria-current="${record.id === state.selectedId ? "true" : "false"}">
          <span class="row-dot"></span>
          <span class="row-main">
            <strong>${escapeHtml(recordName(record))}</strong>
            <small>${metaParts.filter(Boolean).map((part) => escapeHtml(part)).join(" · ")}</small>
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
}

function selectRecord(id) {
  state.selectedId = id;
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

function renderSources(record) {
  const sourcesWithMissions = (record.sources || []).filter((source) => (source.missions || []).length);
  if (!sourcesWithMissions.length) {
    return `
      <div class="source-item">
        <strong>暂无任务来源</strong>
        <small>无</small>
      </div>
    `;
  }

  return sourcesWithMissions
    .map((source) => {
      const missions = source.missions || [];
      const missionHtml = `<ul class="source-missions">${missions
            .map((mission) => {
              const chance = formatChance(mission.chance);
              const reward = mission.rewardUEC ? ` · ${formatNumber(mission.rewardUEC)} aUEC` : "";
              const faction = missionFaction(mission) ? ` · ${escapeHtml(missionFaction(mission))}` : "";
              return `<li>${escapeHtml(missionTitle(mission))}${faction}${reward}${chance ? ` · ${chance}` : ""}</li>`;
            })
            .join("")}</ul>`;
      return `
        <div class="source-item">
          <strong>任务来源</strong>
          <span class="source-line">
            <span>任务 ${formatNumber(source.missionCount || 0)}</span>
          </span>
          ${missionHtml}
        </div>
      `;
    })
    .join("");
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
    }
    state.records = state.data.records.map(prepareRecord);
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
