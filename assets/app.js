const state = {
  data: null,
  mineralLocations: { materials: {}, metadata: null },
  records: [],
  filtered: [],
  selectedId: null,
  category: "all",
  grade: "all",
  componentClass: "all",
  manufacturer: "all",
  material: "all",
  missionType: "all",
  query: "",
  sourceOnly: false,
  sort: "relevance",
};

const DATA_VERSION = "20260623-2";

const els = {
  versionBadge: document.querySelector("#versionBadge"),
  searchForm: document.querySelector("#searchForm"),
  searchInput: document.querySelector("#searchInput"),
  clearSearch: document.querySelector("#clearSearch"),
  openFilters: document.querySelector("#openFilters"),
  closeFilters: document.querySelector("#closeFilters"),
  applyFiltersButton: document.querySelector("#applyFiltersButton"),
  filterModal: document.querySelector("#filterModal"),
  filterCount: document.querySelector("#filterCount"),
  modalResultCount: document.querySelector("#modalResultCount"),
  categoryFilters: document.querySelector("#categoryFilters"),
  gradeFilters: document.querySelector("#gradeFilters"),
  componentClassFilters: document.querySelector("#componentClassFilters"),
  manufacturerFilters: document.querySelector("#manufacturerFilters"),
  materialFilters: document.querySelector("#materialFilters"),
  missionTypeFilters: document.querySelector("#missionTypeFilters"),
  sourceOnly: document.querySelector("#sourceOnly"),
  resetFilters: document.querySelector("#resetFilters"),
  statsGrid: document.querySelector("#statsGrid"),
  resultTitle: document.querySelector("#resultTitle"),
  resultList: document.querySelector("#resultList"),
  detailPanel: document.querySelector("#detailPanel"),
};

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
  return getFirstTier(record).slots.flatMap((slot) =>
    slot.options.map((option) => ({ ...option, slot: slot.name, slotZh: slot.nameZh })),
  );
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
        <span>UEX 当前没有公开地点数据，未做推断。</span>
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
  const updatedAt = state.mineralLocations?.metadata?.retrievedAt
    ? new Date(state.mineralLocations.metadata.retrievedAt).toLocaleString("zh-CN", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "未知";

  return `
    <div class="mineral-overlay" role="presentation">
      <section class="mineral-card" role="dialog" aria-modal="true" aria-label="${escapeHtml(displayName)}矿点详情">
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
          来源：UEX API 2.0 · 更新时间 ${escapeHtml(updatedAt)}
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
  const missionTypes = recordMissionTypes(record).flatMap((type) => [type.name, type.label]);
  const missionFields = (record.sources || []).flatMap((source) =>
    (source.missions || []).flatMap((mission) => [
      mission.title,
      mission.titleZh,
      mission.faction,
      mission.factionZh,
      mission.category,
      mission.categoryZh,
      ...(mission.systems || []),
    ]),
  );
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
    ...missionTypes,
    ...missionFields,
  ];
  return normalizeSearchText(fields.filter(Boolean).join(" "));
}

function relevanceScore(record) {
  let score = 0;
  if (record.category.id === "ship_component") score += 16;
  if (record.category.id === "ship_weapon") score += 14;
  if (record.category.id === "personal_weapon") score += 12;
  if (record.category.id === "weapon_attachment") score += 10;
  score += Math.min(record.sourceCount || 0, 10);
  if (recordName(record).toLowerCase().includes(state.query.toLowerCase())) score += 20;
  return score;
}

function optionTag(value, label, count, activeValue, triggerLabel = label) {
  const suffix = count === undefined ? "" : `（${formatNumber(count)}）`;
  const display = `${label}${suffix}`;
  return `<button type="button" class="filter-option${value === activeValue ? " active" : ""}" data-value="${escapeHtml(value)}" data-trigger-label="${escapeHtml(triggerLabel)}" title="${escapeHtml(display)}">${escapeHtml(display)}</button>`;
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
    option.classList.toggle("active", option.dataset.value === value);
  });
  const label = selectedOptionLabel(container, value);
  const triggerLabel = container.querySelector(".filter-trigger span");
  if (triggerLabel) triggerLabel.textContent = label;
  const trigger = container.querySelector(".filter-trigger");
  if (trigger) trigger.title = label;
}

function syncComponentClassFilter() {
  const group = els.componentClassFilters.closest(".filter-group");
  const body = group.closest(".filter-body");
  const visible = state.category === "ship_component";
  group.hidden = false;
  body.classList.toggle("no-component", !visible);
  els.componentClassFilters.classList.toggle("disabled", !visible);
  if (!visible) {
    state.componentClass = "none";
    setSelectValue(els.componentClassFilters, state.componentClass);
    els.componentClassFilters.classList.remove("open");
  } else if (state.componentClass === "none") {
    state.componentClass = "all";
    setSelectValue(els.componentClassFilters, state.componentClass);
  }
}

function getPopularMaterials() {
  const labelByName = new Map();
  for (const record of state.records) {
    for (const material of getAllMaterials(record)) {
      if (!labelByName.has(material.name)) labelByName.set(material.name, materialZhName(material));
    }
  }
  const counts = state.data.counts.materials || {};
  const ordered = flowcldMaterialOrder
    .filter((name) => counts[name])
    .map((name) => [name, labelByName.get(name) || flowcldMaterialLabels[name] || name, counts[name]]);
  const remaining = Object.entries(counts)
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
  renderDropdown(els.categoryFilters, categoryOrder
    .filter(([id]) => id === "all" || state.data.counts.categories[id])
    .map(([id, label]) => {
      const count = id === "all" ? state.records.length : state.data.counts.categories[id] || 0;
      return optionTag(id, label, count, state.category);
    })
    .join(""), state.category);

  renderDropdown(els.gradeFilters, gradeOrder
    .filter(([id]) => id === "all" || state.records.some((record) => String(record.stats.grade || "") === id))
    .map(([id, label]) => {
      const count = id === "all" ? state.records.length : state.records.filter((record) => String(record.stats.grade || "") === id).length;
      return optionTag(id, label, count, state.grade);
    })
    .join(""), state.grade);

  const componentRecords = state.records.filter((record) => record.category.id === "ship_component");
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
  for (const record of state.records) {
    if (!manufacturerLabel.has(record.manufacturer)) {
      const zh = recordManufacturer(record);
      const en = record.manufacturer;
      manufacturerLabel.set(en, zh && zh !== en ? `${zh} (${en})` : en);
      manufacturerTriggerLabel.set(en, zh || en);
    }
  }
  renderDropdown(els.manufacturerFilters, [
    optionTag("all", "全部", state.records.length, state.manufacturer),
    ...Object.entries(state.data.counts.manufacturers || {})
      .sort((a, b) => b[1] - a[1])
      .map(([name, count]) => optionTag(name, manufacturerLabel.get(name) || name, count, state.manufacturer, manufacturerTriggerLabel.get(name) || name)),
  ].join(""), state.manufacturer);

  renderDropdown(els.materialFilters, [
    optionTag("all", "全部", state.records.length, state.material),
    ...getPopularMaterials().map(([name, label, count]) => {
      const display = materialDisplayLabel(name, label);
      return optionTag(name, display, count, state.material, display);
    }),
  ].join(""), state.material);

  const missionTypeCounts = countMissionTypes(state.records);
  renderDropdown(els.missionTypeFilters, missionTypeOrder
    .filter(([id]) => id === "all" || missionTypeCounts.has(id))
    .map(([id, label]) => {
      const count = id === "all" ? state.records.filter((record) => recordMissionTypes(record).length).length : missionTypeCounts.get(id) || 0;
      return optionTag(id, label, count, state.missionType);
    })
    .join(""), state.missionType);

  syncComponentClassFilter();

  els.statsGrid.innerHTML = [
    ["蓝图总数", state.data.counts.blueprints],
    ["任务来源", state.data.counts.rewardPools],
    ["中文条目", state.data.localization?.flowcldMetadataCount || state.data.localization?.flowcldCalibrationCount || 0],
    ["舰船组件", state.data.counts.categories.ship_component || 0],
  ]
    .map(([label, value]) => `<div class="stat"><strong>${formatNumber(value)}</strong><span>${label}</span></div>`)
    .join("");
}

function openFilterModal() {
  els.filterModal.scrollIntoView({ block: "nearest" });
}

function closeFilterModal() {
  els.filterModal.scrollIntoView({ block: "nearest" });
}

function resetFilters() {
  state.category = "all";
  state.grade = "all";
  state.componentClass = "none";
  state.manufacturer = "all";
  state.material = "all";
  state.missionType = "all";
  state.sourceOnly = false;
  els.sourceOnly.checked = false;
  setSelectValue(els.categoryFilters, state.category);
  setSelectValue(els.gradeFilters, state.grade);
  setSelectValue(els.componentClassFilters, state.componentClass);
  setSelectValue(els.manufacturerFilters, state.manufacturer);
  setSelectValue(els.materialFilters, state.material);
  setSelectValue(els.missionTypeFilters, state.missionType);
  syncComponentClassFilter();
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
    if (key === "category") syncComponentClassFilter();
    applyFilters();
  });
}

function bindEvents() {
  els.searchForm.addEventListener("submit", (event) => event.preventDefault());

  els.searchInput.addEventListener("input", (event) => {
    state.query = event.target.value.trim();
    applyFilters();
  });

  els.clearSearch.addEventListener("click", () => {
    els.searchInput.value = "";
    state.query = "";
    applyFilters();
  });

  bindFilterSelect(els.categoryFilters, "category");
  bindFilterSelect(els.gradeFilters, "grade");
  bindFilterSelect(els.componentClassFilters, "componentClass");
  bindFilterSelect(els.manufacturerFilters, "manufacturer");
  bindFilterSelect(els.materialFilters, "material");
  bindFilterSelect(els.missionTypeFilters, "missionType");

  els.sourceOnly.addEventListener("change", (event) => {
    state.sourceOnly = event.target.checked;
    applyFilters();
  });

  els.openFilters.addEventListener("click", openFilterModal);
  els.closeFilters.addEventListener("click", closeFilterModal);
  els.applyFiltersButton.addEventListener("click", closeFilterModal);
  els.resetFilters.addEventListener("click", resetFilters);

  els.filterModal.addEventListener("click", (event) => {
    if (event.target === els.filterModal) return;
  });

  document.addEventListener("click", (event) => {
    if (event.target.closest(".filter-select")) return;
    closeDropdowns();
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeDropdowns();
      closeFilterModal();
    }
  });

  document.querySelectorAll(".sort").forEach((button) => {
    button.addEventListener("click", () => {
      state.sort = button.dataset.sort;
      document.querySelectorAll(".sort").forEach((item) => item.classList.toggle("active", item.dataset.sort === state.sort));
      applyFilters();
    });
  });

  els.resultList.addEventListener("click", (event) => {
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

    const mineral = event.target.closest("[data-mineral]");
    if (!mineral) return;
    openMineralInfo(mineral.dataset.mineral);
  });
}

function materialMatches(record) {
  if (state.material === "all") return true;
  return getAllMaterials(record).some((item) => item.name === state.material || item.nameZh === state.material);
}

function componentClassMatches(record) {
  if (state.category !== "ship_component") return true;
  return state.componentClass === "all" || state.componentClass === "none" || recordFlowcld(record).itemClass === state.componentClass;
}

function missionTypeMatches(record) {
  return state.missionType === "all" || recordMissionTypes(record).some((type) => type.name === state.missionType);
}

function applyFilters() {
  const query = normalizeSearchText(state.query);
  syncComponentClassFilter();

  state.filtered = state.records.filter((record) => {
    if (state.category !== "all" && record.category.id !== state.category) return false;
    if (state.grade !== "all" && String(record.stats.grade || "") !== state.grade) return false;
    if (!componentClassMatches(record)) return false;
    if (state.manufacturer !== "all" && record.manufacturer !== state.manufacturer) return false;
    if (!materialMatches(record)) return false;
    if (!missionTypeMatches(record)) return false;
    if (state.sourceOnly && !(record.sourceCount > 0)) return false;
    if (query && !recordSearchText(record).includes(query)) return false;
    return true;
  });

  state.filtered.sort((a, b) => {
    if (state.sort === "name") return recordName(a).localeCompare(recordName(b), "zh-CN");
    if (state.sort === "sources") return (b.sourceCount || 0) - (a.sourceCount || 0) || recordName(a).localeCompare(recordName(b), "zh-CN");
    return relevanceScore(b) - relevanceScore(a) || recordName(a).localeCompare(recordName(b), "zh-CN");
  });

  if (!state.filtered.some((record) => record.id === state.selectedId)) {
    state.selectedId = state.filtered[0]?.id || null;
  }

  renderResults();
  renderDetail();
  renderCounts();
}

function activeFilterCount() {
  const values = [state.category, state.grade, state.manufacturer, state.material, state.missionType];
  if (state.category === "ship_component") values.push(state.componentClass);
  return values.filter((value) => value !== "all").length + (state.sourceOnly ? 1 : 0);
}

function renderCounts() {
  const count = state.filtered.length;
  els.resultTitle.textContent = `${formatNumber(count)} 个`;
  els.modalResultCount.textContent = formatNumber(count);
  els.filterCount.textContent = activeFilterCount();
}

function renderResults() {
  if (!state.filtered.length) {
    els.resultList.innerHTML = document.querySelector("#emptyTemplate").innerHTML;
    return;
  }

  els.resultList.innerHTML = state.filtered
    .slice(0, 140)
    .map((record) => {
      const sourceLabel = record.sourceCount > 0 ? "任务奖励" : "无任务来源";
      const size = sizeLabel(record.stats.size);
      const grade = record.stats.grade ? gradeLabel(record.stats.grade) : "未知等级";
      const componentClass = recordComponentClass(record);
      const metaParts = record.category.id === "ship_component"
        ? [record.category.label, recordComponentType(record), recordManufacturer(record), componentClass, size, grade]
        : [record.category.label, recordManufacturer(record), recordSubtype(record), size, grade];
      return `
        <button class="result-card ${escapeHtml(record.category.id)}${record.id === state.selectedId ? " active" : ""}" type="button" data-id="${escapeHtml(record.id)}">
          <span class="row-dot"></span>
          <span class="row-main">
            <strong>${escapeHtml(recordName(record))}</strong>
            <small>${metaParts.filter(Boolean).map((part) => escapeHtml(part)).join(" · ")}</small>
          </span>
          <span class="source-badge ${record.sourceCount > 0 ? "" : "muted"}">${sourceLabel}</span>
        </button>
      `;
    })
    .join("");
}

function selectRecord(id) {
  state.selectedId = id;
  renderResults();
  renderDetail();
}

function renderDetail() {
  const record = state.records.find((item) => item.id === state.selectedId);
  if (!record) {
    els.detailPanel.innerHTML = `
      <div class="detail-scroll">
        <div class="empty-state">
          <h3>选择一个蓝图</h3>
          <p>左侧点击任意结果，查看制作材料和任务来源。</p>
        </div>
      </div>
    `;
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
        <strong>${record.sourceCount > 0 ? "任务奖励" : "暂无任务来源"}</strong>
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
                      return `
                    <button class="material-item material-item-button" type="button" data-mineral="${escapeHtml(item.name)}">
                      <span>
                        <strong>${escapeHtml(materialName(item))}</strong>
                        <small>${escapeHtml(materialSlot(item))} · ${escapeHtml(materialKind(item))}${item.minQuality ? ` · 最低品质 ${formatNumber(item.minQuality)}` : ""}</small>
                      </span>
                      <span class="material-side">
                        <span class="material-location-badge">${locationLabel}</span>
                        <strong>x${formatNumber(item.quantity)}</strong>
                      </span>
                    </button>
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

async function boot() {
  els.resultList.innerHTML = `<div class="loading-state"><div><h3>正在加载蓝图</h3><p>请稍候...</p></div></div>`;
  try {
    const [response, mineralResponse] = await Promise.all([
      fetch(`./data/blueprint-index.json?v=${DATA_VERSION}`),
      fetch(`./data/mineral-locations.json?v=${DATA_VERSION}`).catch(() => null),
    ]);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    state.data = await response.json();
    if (mineralResponse?.ok) {
      state.mineralLocations = await mineralResponse.json();
    }
    state.records = state.data.records;
    els.versionBadge.textContent = state.data.version;
    initFilters();
    bindEvents();
    applyFilters();
  } catch (error) {
    els.resultList.innerHTML = `
      <div class="empty-state">
        <h3>加载失败</h3>
        <p>暂无数据</p>
      </div>
    `;
  }
}

boot();
