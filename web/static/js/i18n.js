/**
 * i18n.js — Internationalization module.
 * Provides t(), tCatalog(), locale switching, and change listeners.
 */

export const SUPPORTED_LOCALES = ["en", "zh"];
const DEFAULT_LOCALE = "en";
const STORAGE_KEY = "ui_locale";

let currentLocale = DEFAULT_LOCALE;
let uiStrings = {};
let catalogStrings = {};
const changeListeners = [];

async function loadLocaleData(locale) {
  const uiRes = await fetch(`/static/i18n/${locale}.json`);
  uiStrings = await uiRes.json();

  if (locale !== "en") {
    try {
      const catRes = await fetch(`/static/i18n/catalog_${locale}.json`);
      catalogStrings = await catRes.json();
    } catch {
      catalogStrings = {};
    }
  } else {
    catalogStrings = {};
  }
}

/** Look up a UI string by key. Supports {param} replacement via params object. */
export function t(key, params) {
  let str = (key in uiStrings) ? uiStrings[key] : key;
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      str = str.replace(`{${k}}`, v);
    }
  }
  return str;
}

/** Look up a catalog item display name. Falls back to the English name. */
export function tCatalog(itemId, fallback) {
  if (currentLocale === "en" || !itemId) return fallback;
  return catalogStrings[itemId] || fallback;
}

export function getLocale() {
  return currentLocale;
}

export async function setLocale(code) {
  if (!SUPPORTED_LOCALES.includes(code)) return;
  currentLocale = code;
  localStorage.setItem(STORAGE_KEY, code);
  await loadLocaleData(code);
  for (const fn of changeListeners) {
    fn(code);
  }
}

export function onLocaleChange(fn) {
  changeListeners.push(fn);
}

/** Initialize i18n: load saved locale preference and fetch bundles. */
export async function initI18n() {
  const saved = localStorage.getItem(STORAGE_KEY);
  const locale = SUPPORTED_LOCALES.includes(saved) ? saved : DEFAULT_LOCALE;
  currentLocale = locale;
  await loadLocaleData(locale);
}
