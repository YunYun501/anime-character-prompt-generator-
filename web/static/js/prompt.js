/**
 * prompt.js — Prompt generation and clipboard utilities.
 */

import { state, getSlotStateForAPI } from "./state.js";
import * as api from "./api.js";

const PREFIX_PRESET_VALUE = "sd_quality_v1";
const PREFIX_PRESET_TEXT = "(masterpiece),(best quality),(ultra-detailed),(best illustration),(absurdres),(very aesthetic),(newest),detailed eyes, detailed face";

/** Read the constant prefix text entered by the user. */
function getPromptPrefix() {
  const el = document.getElementById("prompt-prefix");
  return (el?.value || "").trim();
}

/** Combine prefix + generated prompt in a readable way. */
export function combinePrompt(prefix, generatedPrompt) {
  const p = (prefix || "").trim();
  const g = (generatedPrompt || "").trim();

  if (!p) return g;
  if (!g) return p;
  if (p.endsWith(", ")) return p + g;
  if (p.endsWith(",")) return `${p} ${g}`;
  if (p.endsWith(" ")) return p + g;
  return `${p}, ${g}`;
}

/** Set the prompt output textarea from a generated prompt core. */
export function setPromptOutput(generatedPrompt) {
  const output = combinePrompt(getPromptPrefix(), generatedPrompt || "");
  document.getElementById("prompt-output").value = output;
}

/** Generate prompt from current state and display in the textarea. */
export async function generateAndDisplay() {
  const slotsForAPI = getSlotStateForAPI();
  const data = await api.generatePrompt(slotsForAPI, state.fullBodyMode, state.upperBodyMode);
  setPromptOutput(data.prompt || "");
}

/** Wire preset selector for the optional "Always Include" prefix text. */
export function wirePromptPrefixPreset() {
  const presetSelect = document.getElementById("prompt-prefix-preset");
  const prefixInput = document.getElementById("prompt-prefix");
  if (!presetSelect || !prefixInput) return;

  presetSelect.value = "";
  prefixInput.value = "";

  presetSelect.addEventListener("change", () => {
    if (presetSelect.value === PREFIX_PRESET_VALUE) {
      prefixInput.value = PREFIX_PRESET_TEXT;
      return;
    }
    prefixInput.value = "";
  });
}
