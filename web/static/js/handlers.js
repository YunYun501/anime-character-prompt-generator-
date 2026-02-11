/**
 * handlers.js - Event handler wiring for all UI interactions.
 */

import { state, getSlotStateForAPI, getLockedMap } from "./state.js";
import * as api from "./api.js";
import { clearPromptOutput, generateAndDisplay, getPromptOutputText, setPromptOutput } from "./prompt.js";

/** Reference to all slot DOM components, keyed by slot name. */
let allSlotComponents = {};

/** Slots toggled OFF once when upper-body mode is enabled. */
const UPPER_BODY_MODE_ONE_SHOT_DISABLE_SLOTS = ["waist", "lower_body", "full_body", "legs", "feet"];

/** Cache for deterministic swatch color conversion. */
const paletteColorCache = new Map();

/** Store component refs so handlers can update the DOM. */
export function setSlotComponents(comps) {
  allSlotComponents = comps;
}

// Slot-level handlers

export function wireSlotEvents(slotName, comps) {
  const { onoffBtn, lockBtn, randomBtn, colorRandomBtn, dropdown, colorSelect, weightInput } = comps;

  onoffBtn.addEventListener("click", () => {
    const s = state.slots[slotName];
    s.enabled = !s.enabled;
    renderSlotEnabledState(slotName, comps);

    if (slotName === "lower_body") {
      maybeDisableLegsForLowerBodyCoverage();
    }
    generateAndDisplay();
  });

  lockBtn.addEventListener("click", () => {
    const s = state.slots[slotName];
    s.locked = !s.locked;
    lockBtn.textContent = s.locked ? "\uD83D\uDD12" : "\uD83D\uDD13";
    lockBtn.className = "btn-lock" + (s.locked ? " locked" : "");
    comps.row.classList.toggle("locked", s.locked);
  });

  randomBtn.addEventListener("click", async () => {
    const currentValues = {};
    for (const [n, sl] of Object.entries(state.slots)) {
      if (sl.enabled && sl.value) currentValues[n] = sl.value;
    }

    const data = await api.randomizeSlots(
      [slotName], getLockedMap(), state.paletteEnabled, state.activePaletteId,
      state.fullBodyMode, state.upperBodyMode, currentValues
    );
    applyResults(data.results);
    generateAndDisplay();
  });

  colorRandomBtn.addEventListener("click", async () => {
    const def = state.slotDefs[slotName];
    if (!def || !def.has_color) return;
    if (!state.paletteEnabled || !state.activePaletteId) return;

    const data = await api.randomizeSlots(
      [slotName], {}, state.paletteEnabled, state.activePaletteId,
      state.fullBodyMode, state.upperBodyMode, {}
    );

    if (data.results[slotName]) {
      const color = data.results[slotName].color;
      state.slots[slotName].color = color;
      colorSelect.value = color || "";
      generateAndDisplay();
    }
  });

  dropdown.addEventListener("change", () => {
    state.slots[slotName].value = dropdown.value || null;
    if (slotName === "lower_body") {
      maybeDisableLegsForLowerBodyCoverage();
    }
    generateAndDisplay();
  });

  colorSelect.addEventListener("change", () => {
    state.slots[slotName].color = colorSelect.value || null;
    generateAndDisplay();
  });

  weightInput.addEventListener("change", () => {
    state.slots[slotName].weight = parseFloat(weightInput.value) || 1.0;
    generateAndDisplay();
  });
}

// Section-level handlers

export function wireSectionEvents(sectionData) {
  const { randomBtn, allOnBtn, allOffBtn, slotNames } = sectionData;

  randomBtn.addEventListener("click", async () => {
    const currentValues = {};
    for (const [n, sl] of Object.entries(state.slots)) {
      if (sl.enabled && sl.value) currentValues[n] = sl.value;
    }

    const data = await api.randomizeSlots(
      slotNames, getLockedMap(), state.paletteEnabled, state.activePaletteId,
      state.fullBodyMode, state.upperBodyMode, currentValues
    );
    applyResults(data.results);
    generateAndDisplay();
  });

  allOnBtn.addEventListener("click", () => {
    for (const name of slotNames) {
      state.slots[name].enabled = true;
      const c = allSlotComponents[name];
      if (c) renderSlotEnabledState(name, c);
    }
    applySlotConstraints();
    generateAndDisplay();
  });

  allOffBtn.addEventListener("click", () => {
    for (const name of slotNames) {
      state.slots[name].enabled = false;
      const c = allSlotComponents[name];
      if (c) renderSlotEnabledState(name, c);
    }
    applySlotConstraints();
    generateAndDisplay();
  });
}

// Global handlers

export function wireGlobalEvents() {
  document.getElementById("full-body-mode").checked = state.fullBodyMode;
  document.getElementById("upper-body-mode").checked = state.upperBodyMode;
  document.getElementById("palette-enabled").checked = state.paletteEnabled;
  initPalettePicker();
  applySlotConstraints();

  document.getElementById("btn-randomize-all").addEventListener("click", async () => {
    maybeRandomizePaletteForRandomizeAll();
    const data = await api.randomizeAll(
      getLockedMap(), state.paletteEnabled, state.activePaletteId, state.fullBodyMode, state.upperBodyMode
    );
    applyResults(data.results);
    generateAndDisplay();
  });

  document.getElementById("btn-generate").addEventListener("click", () => {
    generateAndDisplay();
  });

  document.getElementById("btn-reset").addEventListener("click", () => {
    for (const [name, s] of Object.entries(state.slots)) {
      s.value = null;
      s.color = null;
      s.weight = 1.0;

      const c = allSlotComponents[name];
      if (!c) continue;
      c.dropdown.value = "";
      c.colorSelect.value = "";
      c.weightInput.value = "1.0";
    }
    applySlotConstraints();
    clearPromptOutput();
  });

  document.getElementById("btn-copy").addEventListener("click", () => {
    const text = getPromptOutputText();
    navigator.clipboard.writeText(text);
  });

  document.getElementById("full-body-mode").addEventListener("change", (e) => {
    state.fullBodyMode = e.target.checked;
    generateAndDisplay();
  });

  document.getElementById("upper-body-mode").addEventListener("change", (e) => {
    const wasEnabled = state.upperBodyMode;
    state.upperBodyMode = e.target.checked;
    if (!wasEnabled && state.upperBodyMode) {
      applyUpperBodyModeOneShotDisable();
    }
    applySlotConstraints();
    generateAndDisplay();
  });

  document.getElementById("palette-enabled").addEventListener("change", async (e) => {
    state.paletteEnabled = e.target.checked;
    if (state.paletteEnabled && state.activePaletteId) {
      await applyActivePaletteToCurrentSlots(state.activePaletteId);
      return;
    }
    generateAndDisplay();
  });
}

// Save / Load handlers

export function wireSaveLoadEvents() {
  document.getElementById("btn-save").addEventListener("click", async () => {
    const name = document.getElementById("config-name").value.trim();
    if (!name) {
      setStatus("Please enter a config name");
      return;
    }

    const data = { slots: {} };
    for (const [slotName, s] of Object.entries(state.slots)) {
      data.slots[slotName] = {
        enabled: s.enabled,
        locked: s.locked,
        value: s.value,
        color: s.color,
        weight: s.weight,
      };
    }
    await api.saveConfig(name, data);
    setStatus(`Saved: ${name}`);
    refreshConfigList();
  });

  document.getElementById("btn-load").addEventListener("click", async () => {
    const name = document.getElementById("config-select").value;
    if (!name) {
      setStatus("Select a config first");
      return;
    }

    const res = await api.loadConfig(name);
    const slots = res.data?.slots || {};
    for (const [slotName, saved] of Object.entries(slots)) {
      if (!state.slots[slotName]) continue;

      Object.assign(state.slots[slotName], saved);
      const c = allSlotComponents[slotName];
      if (!c) continue;

      c.dropdown.value = saved.value || "";
      c.colorSelect.value = saved.color || "";
      c.weightInput.value = saved.weight ?? 1.0;
      c.lockBtn.textContent = saved.locked ? "\uD83D\uDD12" : "\uD83D\uDD13";
      c.lockBtn.className = "btn-lock" + (saved.locked ? " locked" : "");
      renderSlotEnabledState(slotName, c);
    }

    setStatus(`Loaded: ${name}`);
    applySlotConstraints();
    generateAndDisplay();
  });

  document.getElementById("btn-refresh-configs").addEventListener("click", refreshConfigList);
}

async function refreshConfigList() {
  const data = await api.fetchConfigs();
  const select = document.getElementById("config-select");
  select.innerHTML = '<option value="">(Select config)</option>';
  for (const name of data.configs || []) {
    const opt = document.createElement("option");
    opt.value = name;
    opt.textContent = name;
    select.appendChild(opt);
  }
}

/** Called on init to populate the config dropdown. */
export { refreshConfigList };

function setStatus(msg) {
  document.getElementById("save-status").textContent = msg;
}

// Helpers

/** Apply randomization results to state + DOM. */
function applyResults(results) {
  for (const [name, res] of Object.entries(results)) {
    state.slots[name].value = res.value;
    state.slots[name].color = res.color;

    const c = allSlotComponents[name];
    if (!c) continue;
    c.dropdown.value = res.value || "";
    c.colorSelect.value = res.color || "";
  }
  if (Object.prototype.hasOwnProperty.call(results, "lower_body")) {
    maybeDisableLegsForLowerBodyCoverage();
  }
  applySlotConstraints();
}

function renderSlotEnabledState(slotName, comps) {
  const s = state.slots[slotName];
  comps.onoffBtn.textContent = s.enabled ? "On" : "Off";
  comps.onoffBtn.className = "btn-onoff " + (s.enabled ? "on" : "off");
  comps.row.className = "slot-row " + (s.enabled ? "enabled" : "disabled") + (s.locked ? " locked" : "");
}

function isLowerBodyCoveringLegs() {
  const lower = state.slots.lower_body;
  if (!lower || !lower.enabled || !lower.value) return false;
  return !!state.lowerBodyCoversLegsByName[lower.value];
}

function maybeDisableLegsForLowerBodyCoverage() {
  if (!isLowerBodyCoveringLegs()) return;

  const legsState = state.slots.legs;
  const legsComps = allSlotComponents.legs;
  if (!legsState || !legsComps) return;
  if (!legsState.enabled) return;

  legsState.enabled = false;
  renderSlotEnabledState("legs", legsComps);
}

function applyUpperBodyModeOneShotDisable() {
  for (const slotName of UPPER_BODY_MODE_ONE_SHOT_DISABLE_SLOTS) {
    const slotState = state.slots[slotName];
    const c = allSlotComponents[slotName];
    if (!slotState || !c) continue;
    slotState.enabled = false;
    renderSlotEnabledState(slotName, c);
  }
}

function applySlotConstraints() {
  // No persistent force-disable constraints currently.
}

// Palette UI and behavior

function initPalettePicker() {
  const pickerBtn = document.getElementById("palette-picker-btn");
  const pickerMenu = document.getElementById("palette-picker-menu");
  const pickerWrap = document.getElementById("palette-picker");
  const lockBtn = document.getElementById("btn-palette-lock");
  const nativeSelect = document.getElementById("palette-select");

  if (!pickerBtn || !pickerMenu || !pickerWrap || !lockBtn || !nativeSelect) return;

  renderPaletteMenu();
  setPaletteSelection(state.activePaletteId);
  renderPaletteLockButton();

  pickerBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    togglePaletteMenu(!pickerMenu.classList.contains("open"));
  });

  lockBtn.addEventListener("click", () => {
    state.paletteLocked = !state.paletteLocked;
    renderPaletteLockButton();
  });

  nativeSelect.addEventListener("change", async (e) => {
    await onPaletteSelected(e.target.value || null, true);
  });

  document.addEventListener("click", (e) => {
    if (!pickerWrap.contains(e.target)) {
      togglePaletteMenu(false);
    }
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      togglePaletteMenu(false);
    }
  });
}

function togglePaletteMenu(open) {
  const pickerBtn = document.getElementById("palette-picker-btn");
  const pickerMenu = document.getElementById("palette-picker-menu");
  if (!pickerBtn || !pickerMenu) return;
  pickerMenu.classList.toggle("open", !!open);
  pickerBtn.setAttribute("aria-expanded", open ? "true" : "false");
}

function renderPaletteMenu() {
  const pickerMenu = document.getElementById("palette-picker-menu");
  if (!pickerMenu) return;

  pickerMenu.innerHTML = "";
  pickerMenu.appendChild(createPaletteOptionButton("", "(None)", []));
  for (const p of state.palettes || []) {
    pickerMenu.appendChild(createPaletteOptionButton(p.id, p.name || p.id, p.colors || []));
  }
}

function createPaletteOptionButton(paletteId, label, colors) {
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "palette-option";
  btn.dataset.paletteId = paletteId;

  const labelSpan = document.createElement("span");
  labelSpan.textContent = label;

  const swatches = document.createElement("span");
  swatches.className = "palette-swatches";
  renderPaletteSwatches(swatches, colors, 4);

  btn.append(labelSpan, swatches);

  btn.addEventListener("click", async () => {
    await onPaletteSelected(paletteId || null, true);
    togglePaletteMenu(false);
  });

  return btn;
}

async function onPaletteSelected(paletteId, applyPaletteColors) {
  setPaletteSelection(paletteId);

  if (!paletteId || !applyPaletteColors || !state.paletteEnabled) return;
  await applyActivePaletteToCurrentSlots(paletteId);
}

async function applyActivePaletteToCurrentSlots(paletteId) {
  if (!paletteId) return;

  const slotsForAPI = getSlotStateForAPI();
  const data = await api.applyPalette(paletteId, slotsForAPI, state.fullBodyMode, state.upperBodyMode);

  for (const [name, color] of Object.entries(data.colors || {})) {
    state.slots[name].color = color;
    const c = allSlotComponents[name];
    if (c) c.colorSelect.value = color || "";
  }

  if (data.prompt) {
    setPromptOutput(data.prompt);
  } else {
    generateAndDisplay();
  }
}

function setPaletteSelection(paletteId) {
  state.activePaletteId = paletteId || null;

  const nativeSelect = document.getElementById("palette-select");
  if (nativeSelect) {
    nativeSelect.value = state.activePaletteId || "";
  }

  const palette = getPaletteById(state.activePaletteId);
  const nameEl = document.getElementById("palette-picker-name");
  const swatchesEl = document.getElementById("palette-picker-swatches");
  if (nameEl) nameEl.textContent = palette ? (palette.name || palette.id) : "(None)";
  if (swatchesEl) renderPaletteSwatches(swatchesEl, palette?.colors || [], 5);

  const pickerMenu = document.getElementById("palette-picker-menu");
  if (pickerMenu) {
    for (const btn of pickerMenu.querySelectorAll(".palette-option")) {
      btn.classList.toggle("active", btn.dataset.paletteId === (state.activePaletteId || ""));
    }
  }
}

function renderPaletteLockButton() {
  const btn = document.getElementById("btn-palette-lock");
  if (!btn) return;
  btn.textContent = state.paletteLocked ? "\uD83D\uDD12" : "\uD83D\uDD13";
  btn.className = "btn-lock" + (state.paletteLocked ? " locked" : "");
  btn.title = state.paletteLocked
    ? "Palette locked for Randomize All"
    : "Lock palette during Randomize All";
}

function maybeRandomizePaletteForRandomizeAll() {
  if (!state.paletteEnabled) return;
  if (state.paletteLocked) return;

  const paletteId = pickRandomPaletteId(state.activePaletteId);
  if (!paletteId) return;
  setPaletteSelection(paletteId);
}

function pickRandomPaletteId(currentId) {
  const palettes = state.palettes || [];
  if (!palettes.length) return null;
  if (palettes.length === 1) return palettes[0].id;

  let pool = palettes;
  if (currentId) {
    const filtered = palettes.filter((p) => p.id !== currentId);
    if (filtered.length) pool = filtered;
  }
  const idx = Math.floor(Math.random() * pool.length);
  return pool[idx].id;
}

function getPaletteById(paletteId) {
  if (!paletteId) return null;
  return (state.palettes || []).find((p) => p.id === paletteId) || null;
}

function renderPaletteSwatches(container, colors, maxCount) {
  container.innerHTML = "";
  const useColors = (colors || []).slice(0, maxCount);
  for (const colorName of useColors) {
    const sw = document.createElement("span");
    sw.className = "palette-swatch";
    sw.title = colorName;
    sw.style.backgroundColor = colorTokenToCss(colorName);
    container.appendChild(sw);
  }
}

function colorTokenToCss(token) {
  const key = (token || "").trim().toLowerCase();
  if (!key) return "#666";
  const cached = paletteColorCache.get(key);
  if (cached) return cached;

  if (typeof CSS !== "undefined" && CSS.supports("color", key)) {
    paletteColorCache.set(key, key);
    return key;
  }

  const compact = key.replace(/[\s_-]+/g, "");
  if (typeof CSS !== "undefined" && CSS.supports("color", compact)) {
    paletteColorCache.set(key, compact);
    return compact;
  }

  let hash = 0;
  for (let i = 0; i < key.length; i += 1) {
    hash = (hash * 31 + key.charCodeAt(i)) % 360;
  }
  const fallback = `hsl(${Math.abs(hash)} 55% 55%)`;
  paletteColorCache.set(key, fallback);
  return fallback;
}
