/**
 * history.js - Prompt history management with localStorage persistence.
 */

import { state } from "./state.js";

const HISTORY_KEY = "prompt_history";
const MAX_HISTORY = 50;

const historyChangeListeners = [];
let historyCache = null;

function loadHistoryFromStorage() {
  try {
    const parsed = JSON.parse(localStorage.getItem(HISTORY_KEY));
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function getHistoryCache() {
  if (!Array.isArray(historyCache)) {
    historyCache = loadHistoryFromStorage();
  }
  return historyCache;
}

/**
 * Get all history entries.
 * @returns {Array} History entries, newest first.
 */
export function getHistory() {
  return getHistoryCache().slice();
}

/**
 * Save history to localStorage.
 */
function saveHistory(history) {
  const next = Array.isArray(history) ? history : [];
  historyCache = next;
  localStorage.setItem(HISTORY_KEY, JSON.stringify(next));
  const snapshot = next.slice();
  for (const fn of historyChangeListeners) fn(snapshot);
}

/**
 * Add a new entry to history.
 * Skips if identical to the most recent entry.
 */
export function addToHistory(prompt, prefix) {
  if (!prompt || !prompt.trim()) return;

  const history = getHistoryCache().slice();

  // Skip duplicate of last entry
  if (history.length > 0 && history[0].prompt === prompt && history[0].prefix === prefix) {
    return;
  }

  // Capture current slot state
  const slotSnapshot = {};
  for (const [name, s] of Object.entries(state.slots)) {
    slotSnapshot[name] = {
      enabled: s.enabled,
      locked: s.locked,
      value_id: s.value_id,
      color: s.color,
      weight: s.weight,
    };
  }

  const entry = {
    id: Date.now().toString(),
    timestamp: new Date().toISOString(),
    prompt,
    prefix: prefix || "",
    slots: slotSnapshot,
    palette_id: state.activePaletteId,
    full_body_mode: state.fullBodyMode,
    upper_body_mode: state.upperBodyMode,
    prompt_locale: state.promptLocale,
  };

  history.unshift(entry);

  // Prune old entries
  if (history.length > MAX_HISTORY) {
    history.length = MAX_HISTORY;
  }

  saveHistory(history);
}

/**
 * Remove a single history entry by ID.
 */
export function removeFromHistory(entryId) {
  const history = getHistoryCache();
  const filtered = history.filter((e) => e.id !== entryId);
  saveHistory(filtered);
}

/**
 * Clear all history.
 */
export function clearHistory() {
  saveHistory([]);
}

/**
 * Register a listener for history changes.
 */
export function onHistoryChange(fn) {
  historyChangeListeners.push(fn);
}

/**
 * Get a single history entry by ID.
 */
export function getHistoryEntry(entryId) {
  const history = getHistoryCache();
  return history.find((e) => e.id === entryId) || null;
}

/**
 * Export all user data (history, settings) as a JSON object.
 */
export function exportUserData() {
  return {
    version: 1,
    exported_at: new Date().toISOString(),
    history: getHistory(),
    settings: {
      ui_locale: state.uiLocale,
      prompt_locale: state.promptLocale,
      palette_enabled: state.paletteEnabled,
      active_palette_id: state.activePaletteId,
    },
  };
}

/**
 * Import user data from a JSON object.
 * @returns {object} Result with success flag and message.
 */
export function importUserData(data) {
  if (!data || typeof data !== "object") {
    return { success: false, message: "invalid_data" };
  }

  if (data.version !== 1) {
    return { success: false, message: "unsupported_version" };
  }

  // Import history
  if (Array.isArray(data.history)) {
    const validHistory = data.history.filter(
      (e) => e && typeof e.id === "string" && typeof e.prompt === "string"
    );
    if (validHistory.length > MAX_HISTORY) {
      validHistory.length = MAX_HISTORY;
    }
    saveHistory(validHistory);
  }

  return { success: true, message: "import_success", count: data.history?.length || 0 };
}

/**
 * Download user data as a JSON file.
 */
export function downloadExport() {
  const data = exportUserData();
  const json = JSON.stringify(data, null, 2);
  const blob = new Blob([json], { type: "application/json" });
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = `prompt-generator-backup-${new Date().toISOString().slice(0, 10)}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Trigger file input for import.
 */
export function triggerImport(onComplete) {
  const input = document.createElement("input");
  input.type = "file";
  input.accept = ".json,application/json";

  input.addEventListener("change", async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      const data = JSON.parse(text);
      const result = importUserData(data);
      if (onComplete) onComplete(result);
    } catch (err) {
      if (onComplete) onComplete({ success: false, message: "parse_error" });
    }
  });

  input.click();
}

/**
 * Format timestamp for display.
 */
export function formatTimestamp(isoString) {
  try {
    const date = new Date(isoString);
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();

    if (isToday) {
      return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    }
    return date.toLocaleDateString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
  } catch {
    return isoString;
  }
}
