/**
 * shortcuts.js - Keyboard shortcut management with user-configurable bindings.
 */

import { t } from "./i18n.js";

const STORAGE_KEY = "prompt_generator_shortcuts";

/**
 * All available shortcut actions with metadata.
 * id: unique identifier
 * label: display name (i18n key)
 * description: what it does
 * defaultBinding: default key combination
 */
const SHORTCUT_ACTIONS = [
  {
    id: "generate",
    labelKey: "shortcut_generate",
    label: "Generate Prompt",
    defaultBinding: { key: "g", ctrl: true, shift: false, alt: false },
  },
  {
    id: "randomizeAll",
    labelKey: "shortcut_randomize",
    label: "Randomize All",
    defaultBinding: { key: "r", ctrl: true, shift: false, alt: false },
  },
  {
    id: "copy",
    labelKey: "shortcut_copy",
    label: "Copy Prompt",
    defaultBinding: { key: "c", ctrl: true, shift: true, alt: false },
  },
  {
    id: "reset",
    labelKey: "shortcut_reset",
    label: "Reset All Slots",
    defaultBinding: { key: "x", ctrl: true, shift: true, alt: false },
  },
  {
    id: "parse",
    labelKey: "shortcut_parse",
    label: "Parse to Slots",
    defaultBinding: { key: "p", ctrl: true, shift: false, alt: false },
  },
  {
    id: "clickScrollToggle",
    labelKey: "shortcut_click_scroll",
    label: "Toggle Click-to-Scroll",
    defaultBinding: { key: "j", ctrl: true, shift: false, alt: false },
  },
];

/** Build default shortcuts map from actions. */
function buildDefaultShortcuts() {
  const map = {};
  for (const action of SHORTCUT_ACTIONS) {
    map[action.id] = { ...action.defaultBinding };
  }
  return map;
}

const DEFAULT_SHORTCUTS = buildDefaultShortcuts();

/** Current shortcut bindings. */
let shortcuts = { ...DEFAULT_SHORTCUTS };

/** Currently recording shortcut for which action. */
let recordingAction = null;

/** Callback registry for shortcut triggers. */
const shortcutCallbacks = {};

/** Feature toggles. */
export const features = {
  clickScrollEnabled: true,
};

/**
 * Register a callback for a shortcut action.
 */
export function onShortcut(actionId, callback) {
  shortcutCallbacks[actionId] = callback;
}

/**
 * Load shortcuts from localStorage.
 */
export function loadShortcuts() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      const parsed = JSON.parse(saved);
      shortcuts = { ...DEFAULT_SHORTCUTS, ...parsed.shortcuts };
      if (typeof parsed.clickScrollEnabled === "boolean") {
        features.clickScrollEnabled = parsed.clickScrollEnabled;
      }
    }
  } catch (e) {
    console.warn("Failed to load shortcuts:", e);
  }
  updateShortcutDisplay();
  updateToggleState();
  renderShortcutsTable();
}

/**
 * Save shortcuts to localStorage.
 */
function saveShortcuts() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      shortcuts,
      clickScrollEnabled: features.clickScrollEnabled,
    }));
  } catch (e) {
    console.warn("Failed to save shortcuts:", e);
  }
}

/**
 * Format shortcut for display.
 */
function formatShortcut(binding) {
  if (!binding) return "—";
  const parts = [];
  if (binding.ctrl) parts.push("Ctrl");
  if (binding.alt) parts.push("Alt");
  if (binding.shift) parts.push("Shift");
  parts.push(binding.key.toUpperCase());
  return parts.join(" + ");
}

/**
 * Update shortcut display in settings bar (for click-scroll toggle).
 */
function updateShortcutDisplay() {
  const el = document.getElementById("click-scroll-shortcut");
  if (el && shortcuts.clickScrollToggle) {
    el.textContent = formatShortcut(shortcuts.clickScrollToggle);
  }
}

/**
 * Update toggle checkbox state.
 */
function updateToggleState() {
  const checkbox = document.getElementById("click-scroll-enabled");
  if (checkbox) {
    checkbox.checked = features.clickScrollEnabled;
  }
}

/**
 * Check if a keyboard event matches a shortcut binding.
 */
function matchesShortcut(e, binding) {
  if (!binding) return false;
  return (
    e.key.toLowerCase() === binding.key.toLowerCase() &&
    e.ctrlKey === binding.ctrl &&
    e.shiftKey === binding.shift &&
    e.altKey === binding.alt
  );
}

/**
 * Render the shortcuts reference table.
 */
export function renderShortcutsTable() {
  const tbody = document.getElementById("shortcuts-list");
  if (!tbody) return;

  tbody.innerHTML = "";

  for (const action of SHORTCUT_ACTIONS) {
    const tr = document.createElement("tr");

    // Action name (use i18n key, fallback to static label)
    const tdAction = document.createElement("td");
    tdAction.className = "shortcut-action";
    tdAction.textContent = t(action.labelKey) || action.label;
    tr.appendChild(tdAction);

    // Shortcut keys
    const tdKeys = document.createElement("td");
    const keysSpan = document.createElement("span");
    keysSpan.className = "shortcut-keys";
    keysSpan.id = `shortcut-display-${action.id}`;
    keysSpan.textContent = formatShortcut(shortcuts[action.id]);
    tdKeys.appendChild(keysSpan);
    tr.appendChild(tdKeys);

    // Change button
    const tdChange = document.createElement("td");
    const btn = document.createElement("button");
    btn.className = "btn-change-shortcut";
    btn.textContent = t("shortcut_change_btn") || "Change";
    btn.dataset.action = action.id;
    btn.addEventListener("click", () => startRecordingFromTable(action.id, btn));
    tdChange.appendChild(btn);
    tr.appendChild(tdChange);

    tbody.appendChild(tr);
  }
}

/**
 * Start recording a new shortcut from table button.
 */
function startRecordingFromTable(actionId, btnEl) {
  // Cancel any existing recording
  if (recordingAction) {
    cancelRecording();
  }

  recordingAction = actionId;

  // Update button state
  btnEl.classList.add("recording");
  btnEl.textContent = t("shortcut_recording") || "Press keys...";

  // Update the inline shortcut badge if it's clickScrollToggle
  if (actionId === "clickScrollToggle") {
    const el = document.getElementById("click-scroll-shortcut");
    if (el) {
      el.classList.add("recording");
      el.textContent = t("shortcut_recording") || "Press keys...";
    }
  }
}

/**
 * Start recording from the inline shortcut badge.
 */
function startRecordingInline(action) {
  if (recordingAction) {
    cancelRecording();
  }

  recordingAction = action;

  const el = document.getElementById("click-scroll-shortcut");
  if (el) {
    el.classList.add("recording");
    el.textContent = t("shortcut_recording") || "Press keys...";
  }

  // Also update table button if visible
  const tableBtn = document.querySelector(`.btn-change-shortcut[data-action="${action}"]`);
  if (tableBtn) {
    tableBtn.classList.add("recording");
    tableBtn.textContent = t("shortcut_recording") || "Press keys...";
  }
}

/**
 * Stop recording and save the new shortcut.
 */
function stopRecording(binding) {
  if (!recordingAction) return;

  const actionId = recordingAction;
  shortcuts[actionId] = binding;
  recordingAction = null;
  saveShortcuts();

  // Update displays
  updateShortcutDisplay();

  // Update table display
  const keysSpan = document.getElementById(`shortcut-display-${actionId}`);
  if (keysSpan) {
    keysSpan.textContent = formatShortcut(binding);
  }

  // Reset button states
  const tableBtn = document.querySelector(`.btn-change-shortcut[data-action="${actionId}"]`);
  if (tableBtn) {
    tableBtn.classList.remove("recording");
    tableBtn.textContent = t("shortcut_change_btn") || "Change";
  }

  const inlineEl = document.getElementById("click-scroll-shortcut");
  if (inlineEl) {
    inlineEl.classList.remove("recording");
  }
}

/**
 * Cancel recording.
 */
function cancelRecording() {
  if (!recordingAction) return;

  const actionId = recordingAction;
  recordingAction = null;

  // Reset inline badge
  const el = document.getElementById("click-scroll-shortcut");
  if (el) {
    el.classList.remove("recording");
  }
  updateShortcutDisplay();

  // Reset table button
  const tableBtn = document.querySelector(`.btn-change-shortcut[data-action="${actionId}"]`);
  if (tableBtn) {
    tableBtn.classList.remove("recording");
    tableBtn.textContent = t("shortcut_change_btn") || "Change";
  }
}

/**
 * Wire up shortcut events.
 */
export function wireShortcutEvents() {
  // Toggle checkbox
  const checkbox = document.getElementById("click-scroll-enabled");
  if (checkbox) {
    checkbox.addEventListener("change", () => {
      features.clickScrollEnabled = checkbox.checked;
      saveShortcuts();
    });
  }

  // Click on inline shortcut key to record new binding
  const shortcutEl = document.getElementById("click-scroll-shortcut");
  if (shortcutEl) {
    shortcutEl.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (recordingAction) {
        cancelRecording();
      } else {
        startRecordingInline("clickScrollToggle");
      }
    });
  }

  // Global keyboard handler
  document.addEventListener("keydown", (e) => {
    // Don't capture when typing in inputs
    const tag = e.target.tagName.toLowerCase();
    const isEditable = e.target.isContentEditable;
    if ((tag === "input" || tag === "textarea" || tag === "select" || isEditable) && !recordingAction) {
      return;
    }

    // If recording, capture the shortcut
    if (recordingAction) {
      // Ignore modifier-only presses
      if (["Control", "Shift", "Alt", "Meta"].includes(e.key)) return;

      // Escape cancels recording
      if (e.key === "Escape") {
        cancelRecording();
        return;
      }

      e.preventDefault();
      stopRecording({
        key: e.key.toLowerCase(),
        ctrl: e.ctrlKey,
        shift: e.shiftKey,
        alt: e.altKey,
      });
      return;
    }

    // Check all shortcuts
    for (const action of SHORTCUT_ACTIONS) {
      if (shortcuts[action.id] && matchesShortcut(e, shortcuts[action.id])) {
        e.preventDefault();

        // Handle click-scroll toggle specially
        if (action.id === "clickScrollToggle") {
          features.clickScrollEnabled = !features.clickScrollEnabled;
          updateToggleState();
          saveShortcuts();
          showShortcutFeedback(features.clickScrollEnabled ? "Click-to-scroll ON" : "Click-to-scroll OFF");
          return;
        }

        // Call registered callback
        if (shortcutCallbacks[action.id]) {
          shortcutCallbacks[action.id]();
          showShortcutFeedback(action.label);
        }
        return;
      }
    }
  });
}

/**
 * Show brief feedback when using a shortcut.
 */
function showShortcutFeedback(message) {
  // Remove any existing feedback
  const existing = document.querySelector(".shortcut-feedback");
  if (existing) existing.remove();

  const feedback = document.createElement("div");
  feedback.className = "shortcut-feedback";
  feedback.textContent = message;
  document.body.appendChild(feedback);

  // Trigger animation
  requestAnimationFrame(() => {
    feedback.classList.add("show");
    setTimeout(() => {
      feedback.classList.remove("show");
      setTimeout(() => feedback.remove(), 300);
    }, 1000);
  });
}
