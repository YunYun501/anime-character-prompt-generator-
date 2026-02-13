/**
 * components.js - DOM builder functions for slot rows and sections.
 */

import { state, localizeFromI18nMap } from "./state.js";
import { t } from "./i18n.js";

const LOCKED_ICON = "\uD83D\uDD12";
const UNLOCKED_ICON = "\uD83D\uDD13";
const GROUP_DISPLAY_ORDER = [
  // Clothing theme groups.
  "uniform_service",
  "chinese_traditional",
  "japanese_traditional",
  "modern_everyday",
  "formal_fashion",
  "sports_stage",
  "armor_fantasy",
  "swimwear",
  "cute_themed",
  "props_tech",

  // Appearance groups (hair / eyes).
  "tied_ponytails",
  "braids",
  "buns_updos",
  "cuts_layers",
  "bangs_fringe",
  "anime_accents",
  "side_accents",
  "loose_back",
  "special_styles",
  "short_lengths",
  "medium_lengths",
  "long_lengths",
  "extreme_lengths",
  "spectrum_red_orange",
  "spectrum_yellow_blonde",
  "spectrum_yellow_gold",
  "spectrum_green_cyan",
  "spectrum_blue",
  "spectrum_purple_pink",
  "neutral_natural",
  "grayscale",
  "fantasy_multicolor",
  "texture_straight_smooth",
  "texture_wavy_curly",
  "texture_volume_air",
  "texture_motion_styled",
  "texture_wet_gloss",
  "texture_rough_messy",
  "style_expression_quality",
  "style_eye_shape",
  "style_intensity",
  "style_pupil_special",
  "style_eye_state",
  "style_accessories",

  // Pose and hand-action groups.
  "pose_standing",
  "pose_sitting",
  "pose_action",
  "pose_lying",
  "pose_special",
  "gesture_signs",
  "gesture_pointing_waving",
  "gesture_formal",
  "gesture_face_touch",
  "gesture_power",
  "gesture_hair_adjust",
  "gesture_affection",
  "gesture_object_interaction",
  "gesture_general",

  // Expression emotion-family groups.
  "neutral_baseline",
  "happiness_positive",
  "affection_romance",
  "playful_teasing_smug",
  "embarrassment_shyness",
  "surprise_shock",
  "anger_irritation",
  "sadness_hurt",
  "fear_anxiety_panic",
  "disgust_contempt",
  "determination_resolve",
  "confusion_skepticism",
  "tired_sleepy_bored",
  "pain_strain_sickness",
  "extreme_anime_stylized",

  // View-angle groups.
  "camera_height",
  "view_direction",
  "tilt_style",
  "framing",
  "lens_perspective",
];

function getSlotLabel(slotName) {
  return t(`slot_label_${slotName}`);
}

function createSlotOptionElement(opt) {
  const el = document.createElement("option");
  el.value = opt.id;
  el.textContent = localizeFromI18nMap(opt.name_i18n, state.uiLocale, opt.name || opt.id || "");
  return el;
}

function getOptionGroupKey(opt) {
  if (!opt || typeof opt.group !== "string") return "";
  return opt.group.trim();
}

function getOptionGroupLabel(opt) {
  const key = getOptionGroupKey(opt);
  if (!key) return "";

  // Prefer UI bundle keys so group headers always follow UI language toggle.
  const i18nKey = `group_${key}`;
  const fromUiBundle = t(i18nKey);
  if (fromUiBundle !== i18nKey) {
    return fromUiBundle;
  }

  return localizeFromI18nMap(opt.group_i18n, state.uiLocale, key);
}

function getGroupDisplayRank(groupKey) {
  const idx = GROUP_DISPLAY_ORDER.indexOf(groupKey);
  return idx >= 0 ? idx : Number.MAX_SAFE_INTEGER;
}

function populateSlotDropdown(slotName, dropdown, selectedValueId) {
  dropdown.innerHTML = "";

  const noneOpt = document.createElement("option");
  noneOpt.value = "";
  noneOpt.textContent = t("slot_none");
  dropdown.appendChild(noneOpt);

  const slotDef = state.slotDefs[slotName];
  const options = slotDef?.options || [];
  const hasGroups = options.some((opt) => getOptionGroupKey(opt));

  if (!hasGroups) {
    for (const opt of options) {
      dropdown.appendChild(createSlotOptionElement(opt));
    }
    dropdown.value = selectedValueId || "";
    return;
  }

  const grouped = new Map();
  const ungrouped = [];

  for (const opt of options) {
    const groupKey = getOptionGroupKey(opt);
    if (!groupKey) {
      ungrouped.push(opt);
      continue;
    }
    if (!grouped.has(groupKey)) {
      grouped.set(groupKey, {
        label: getOptionGroupLabel(opt),
        options: [],
      });
    }
    grouped.get(groupKey).options.push(opt);
  }

  const sortedGroups = Array.from(grouped.entries()).sort((a, b) => {
    const [aKey, aData] = a;
    const [bKey, bData] = b;
    const rankDelta = getGroupDisplayRank(aKey) - getGroupDisplayRank(bKey);
    if (rankDelta !== 0) return rankDelta;
    return aData.label.localeCompare(bData.label);
  });

  for (const [, groupData] of sortedGroups) {
    const groupEl = document.createElement("optgroup");
    groupEl.label = groupData.label;
    for (const opt of groupData.options) {
      groupEl.appendChild(createSlotOptionElement(opt));
    }
    dropdown.appendChild(groupEl);
  }

  for (const opt of ungrouped) {
    dropdown.appendChild(createSlotOptionElement(opt));
  }

  dropdown.value = selectedValueId || "";
}

function populateColorDropdown(colorSelect, selectedColor) {
  colorSelect.innerHTML = "";

  const noColorOpt = document.createElement("option");
  noColorOpt.value = "";
  noColorOpt.textContent = t("slot_no_color");
  colorSelect.appendChild(noColorOpt);

  for (const colorToken of state.individualColors) {
    const opt = document.createElement("option");
    opt.value = colorToken;
    // Use i18n map directly for better locale handling
    const i18nMap = state.individualColorsI18n[colorToken];
    opt.textContent = localizeFromI18nMap(i18nMap, state.uiLocale, colorToken);
    colorSelect.appendChild(opt);
  }

  colorSelect.value = selectedColor || "";
}

/**
 * Get all unique groups for a slot's options.
 * Returns array of [groupKey, groupLabel] sorted by display order.
 */
function getSlotGroups(slotName) {
  const slotDef = state.slotDefs[slotName];
  const options = slotDef?.options || [];
  const groups = new Map();

  for (const opt of options) {
    const groupKey = getOptionGroupKey(opt);
    if (groupKey && !groups.has(groupKey)) {
      groups.set(groupKey, getOptionGroupLabel(opt));
    }
  }

  // Sort by display order
  return Array.from(groups.entries()).sort((a, b) => {
    const rankDelta = getGroupDisplayRank(a[0]) - getGroupDisplayRank(b[0]);
    if (rankDelta !== 0) return rankDelta;
    return a[1].localeCompare(b[1]);
  });
}

/**
 * Create a custom dropdown with collapsible group toggles.
 * Returns { container, trigger, panel, updateSelection, getGroupSection }.
 */
export function createCustomDropdown(slotName, slotDef, slotState) {
  const options = slotDef?.options || [];
  const hasGroups = options.some((opt) => getOptionGroupKey(opt));

  // If no groups, just use native select
  if (!hasGroups) {
    return null;
  }

  const container = document.createElement("div");
  container.className = "custom-dropdown";
  container.dataset.slot = slotName;

  // Trigger button showing current selection
  const trigger = document.createElement("button");
  trigger.type = "button";
  trigger.className = "custom-dropdown-trigger";
  trigger.textContent = t("slot_none");

  // Dropdown panel
  const panel = document.createElement("div");
  panel.className = "custom-dropdown-panel";

  // "(None)" option at top
  const noneItem = document.createElement("div");
  noneItem.className = "dropdown-item none-option";
  noneItem.dataset.value = "";
  noneItem.textContent = t("slot_none");
  panel.appendChild(noneItem);

  // Build groups
  const groups = getSlotGroups(slotName);
  const groupSections = new Map();

  for (const [groupKey, groupLabel] of groups) {
    const groupSection = document.createElement("div");
    groupSection.className = "dropdown-group";
    groupSection.dataset.groupKey = groupKey;

    // Check if group is disabled
    const isDisabled = (slotState.disabledGroups || []).includes(groupKey);
    if (isDisabled) {
      groupSection.classList.add("disabled");
    }

    // Header with toggle and solo button
    const header = document.createElement("div");
    header.className = "dropdown-group-header";

    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "btn-group-toggle " + (isDisabled ? "off" : "on");
    toggle.textContent = isDisabled ? t("slot_off") : t("slot_on");
    toggle.dataset.groupKey = groupKey;

    const label = document.createElement("span");
    label.className = "dropdown-group-label";
    label.textContent = groupLabel;

    const soloBtn = document.createElement("button");
    soloBtn.type = "button";
    soloBtn.className = "btn-group-solo";
    soloBtn.textContent = t("group_solo") || "Solo";
    soloBtn.dataset.groupKey = groupKey;
    soloBtn.title = t("group_solo_title") || "Enable only this group";

    header.append(toggle, label, soloBtn);

    // Items container
    const items = document.createElement("div");
    items.className = "dropdown-group-items";

    // Populate with options in this group
    const groupOptions = options.filter((opt) => getOptionGroupKey(opt) === groupKey);
    for (const opt of groupOptions) {
      const item = document.createElement("div");
      item.className = "dropdown-item";
      item.dataset.value = opt.id;
      item.textContent = localizeFromI18nMap(opt.name_i18n, state.uiLocale, opt.name || opt.id || "");
      items.appendChild(item);
    }

    groupSection.append(header, items);
    panel.appendChild(groupSection);
    groupSections.set(groupKey, groupSection);
  }

  // Add ungrouped options at the end
  const ungrouped = options.filter((opt) => !getOptionGroupKey(opt));
  if (ungrouped.length > 0) {
    const ungroupedSection = document.createElement("div");
    ungroupedSection.className = "dropdown-ungrouped";
    for (const opt of ungrouped) {
      const item = document.createElement("div");
      item.className = "dropdown-item";
      item.dataset.value = opt.id;
      item.textContent = localizeFromI18nMap(opt.name_i18n, state.uiLocale, opt.name || opt.id || "");
      ungroupedSection.appendChild(item);
    }
    panel.appendChild(ungroupedSection);
  }

  container.append(trigger, panel);

  // Helper to update selection display
  function updateSelection(valueId) {
    const opt = options.find((o) => o.id === valueId);
    if (opt) {
      trigger.textContent = localizeFromI18nMap(opt.name_i18n, state.uiLocale, opt.name || opt.id || "");
      trigger.classList.remove("empty");
    } else {
      trigger.textContent = t("slot_none");
      trigger.classList.add("empty");
    }
    // Update active state on items
    for (const item of panel.querySelectorAll(".dropdown-item")) {
      item.classList.toggle("active", item.dataset.value === (valueId || ""));
    }
  }

  // Helper to get group section element
  function getGroupSection(groupKey) {
    return groupSections.get(groupKey) || null;
  }

  // Initialize selection
  updateSelection(slotState.value_id);

  return { container, trigger, panel, updateSelection, getGroupSection };
}

/**
 * Create a single slot row element.
 * Returns row refs used by handlers.
 */
export function createSlotRow(slotName, slotDef) {
  const slotState = state.slots[slotName] || { enabled: true, locked: false, disabledGroups: [] };
  const row = document.createElement("div");
  row.className = "slot-row " + (slotState.enabled ? "enabled" : "disabled") + (slotState.locked ? " locked" : "");
  row.dataset.slot = slotName;

  const onoffBtn = document.createElement("button");
  onoffBtn.className = "btn-onoff " + (slotState.enabled ? "on" : "off");
  onoffBtn.textContent = slotState.enabled ? t("slot_on") : t("slot_off");
  onoffBtn.title = t("slot_toggle_title");

  const lockBtn = document.createElement("button");
  lockBtn.className = "btn-lock" + (slotState.locked ? " locked" : "");
  lockBtn.textContent = slotState.locked ? LOCKED_ICON : UNLOCKED_ICON;
  lockBtn.title = t("slot_lock_title");

  const label = document.createElement("span");
  label.className = "slot-label";
  label.textContent = getSlotLabel(slotName);

  // Try to create custom dropdown with collapsible groups
  const customDropdownResult = createCustomDropdown(slotName, slotDef, slotState);

  // Native select (hidden when custom dropdown is used)
  const dropdown = document.createElement("select");
  dropdown.className = "slot-dropdown" + (customDropdownResult ? " hidden" : "");
  populateSlotDropdown(slotName, dropdown, slotState.value_id);

  const randomBtn = document.createElement("button");
  randomBtn.className = "btn-slot-random";
  randomBtn.textContent = "\uD83C\uDFB2";
  randomBtn.title = t("slot_randomize_title");

  const colorSelect = document.createElement("select");
  colorSelect.className = "slot-color" + (slotDef.has_color ? "" : " hidden");
  populateColorDropdown(colorSelect, slotState.color);

  const colorRandomBtn = document.createElement("button");
  colorRandomBtn.className = "btn-color-random" + (slotDef.has_color ? "" : " hidden");
  colorRandomBtn.textContent = "\uD83C\uDFA8";
  colorRandomBtn.title = t("slot_color_random_title");

  const weightInput = document.createElement("input");
  weightInput.type = "number";
  weightInput.className = "slot-weight";
  weightInput.value = String(slotState.weight ?? 1.0);
  weightInput.min = "0.1";
  weightInput.max = "2.0";
  weightInput.step = "0.1";
  weightInput.title = t("slot_weight_title");

  if (customDropdownResult) {
    row.append(onoffBtn, lockBtn, label, customDropdownResult.container, dropdown, randomBtn, colorSelect, colorRandomBtn, weightInput);
  } else {
    row.append(onoffBtn, lockBtn, label, dropdown, randomBtn, colorSelect, colorRandomBtn, weightInput);
  }

  return {
    row,
    label,
    dropdown,
    colorSelect,
    weightInput,
    onoffBtn,
    lockBtn,
    randomBtn,
    colorRandomBtn,
    customDropdown: customDropdownResult,
  };
}

/**
 * Create a section panel with header, section buttons, and slot rows.
 * Returns section refs used by handlers.
 */
export function createSection(sectionKey, sectionDef) {
  const section = document.createElement("div");
  section.className = "section";
  section.dataset.section = sectionKey;

  const header = document.createElement("div");
  header.className = "section-header";

  const title = document.createElement("span");
  title.className = "section-title";
  title.textContent = `${sectionDef.icon} ${t(sectionDef.label_key || `section_${sectionKey}`)}`;

  const buttons = document.createElement("div");
  buttons.className = "section-buttons";

  const randomBtn = document.createElement("button");
  randomBtn.className = "btn btn-sm section-random";
  randomBtn.textContent = t("section_random");

  const allOnBtn = document.createElement("button");
  allOnBtn.className = "btn btn-sm section-all-on";
  allOnBtn.textContent = t("section_all_on");

  const allOffBtn = document.createElement("button");
  allOffBtn.className = "btn btn-sm section-all-off";
  allOffBtn.textContent = t("section_all_off");

  buttons.append(randomBtn, allOnBtn, allOffBtn);
  header.append(title, buttons);
  section.appendChild(header);

  const slotComponents = {};
  const slotNames = sectionDef.slots || [];

  if (sectionDef.columns) {
    const columnsDiv = document.createElement("div");
    columnsDiv.className = "section-columns";
    const columnLabelKeys = Array.isArray(sectionDef.column_label_keys) ? sectionDef.column_label_keys : [];
    for (let colIndex = 0; colIndex < sectionDef.columns.length; colIndex += 1) {
      const colSlots = sectionDef.columns[colIndex];
      const col = document.createElement("div");
      col.className = "section-column";

      const labelKey = columnLabelKeys[colIndex];
      if (labelKey) {
        const columnLabel = document.createElement("div");
        columnLabel.className = "section-column-label";
        columnLabel.textContent = t(labelKey);
        col.appendChild(columnLabel);
      }

      for (const slotName of colSlots) {
        const def = state.slotDefs[slotName];
        if (!def) continue;
        const comps = createSlotRow(slotName, def);
        slotComponents[slotName] = comps;
        col.appendChild(comps.row);
      }
      columnsDiv.appendChild(col);
    }
    section.appendChild(columnsDiv);
  } else {
    const slotsDiv = document.createElement("div");
    slotsDiv.style.display = "flex";
    slotsDiv.style.flexDirection = "column";
    slotsDiv.style.gap = "var(--slot-gap)";
    for (const slotName of slotNames) {
      const def = state.slotDefs[slotName];
      if (!def) continue;
      const comps = createSlotRow(slotName, def);
      slotComponents[slotName] = comps;
      slotsDiv.appendChild(comps.row);
    }
    section.appendChild(slotsDiv);
  }

  return { element: section, slotComponents, randomBtn, allOnBtn, allOffBtn, slotNames };
}
