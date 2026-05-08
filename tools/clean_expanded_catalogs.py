"""
CatalogCleaner — filters expanded tag catalogs through 4 configurable tiers.

Tiers (default configuration):
    tier0  — Noise/garbage (ALWAYS ON): short names, usernames, numerics, brands
    tier1  — NSFW hard block (ALWAYS ON): explicit content, genitals, fluids
    tier2  — Suggestive (DEFAULTS OFF): lingerie, positions, body focus
    tier3  — Franchise/character noise (ALWAYS ON): franchise references, variants

Blocklists are loaded from JSON files in the blocklist directory:
    - nsfw_blocklist.json  (tier1 + tier2 terms/patterns)
    - franchise_blocklist.json (tier3 franchise terms + noise patterns)

Usage:
    cleaner = CatalogCleaner(blocklist_dir=Path("tools"))
    result = cleaner.clean_catalog(items, tiers={"tier0": True, ...})
    report = cleaner.generate_report()
"""

import json
import re
from pathlib import Path
from typing import Any, Optional


class CatalogCleaner:
    """Filters catalog items through 4 configurable filtering tiers.

    Loads blocklists from JSON files and applies configurable filtering
    rules to remove noise, NSFW content, suggestive items, and franchise-
    specific tags from expanded prompt tag catalogs.
    """

    def __init__(self, blocklist_dir: Optional[Path] = None):
        if blocklist_dir is None:
            blocklist_dir = Path(__file__).resolve().parent
        self.blocklist_dir = Path(blocklist_dir)
        self._nsfw_blocklist: dict = {}
        self._franchise_blocklist: dict = {}
        self._last_report: Optional[dict] = None
        self._load_blocklists_internal()

    # ------------------------------------------------------------------
    # Internal loading
    # ------------------------------------------------------------------

    def _load_blocklists_internal(self) -> None:
        """Load both blocklist JSON files from disk."""
        nsfw_path = self.blocklist_dir / "nsfw_blocklist.json"
        franchise_path = self.blocklist_dir / "franchise_blocklist.json"

        with open(nsfw_path, "r", encoding="utf-8") as f:
            self._nsfw_blocklist = json.load(f)

        with open(franchise_path, "r", encoding="utf-8") as f:
            self._franchise_blocklist = json.load(f)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_blocklists(self) -> dict:
        """Return the loaded blocklists as a dict with 'nsfw' and 'franchise' keys."""
        return {
            "nsfw": self._nsfw_blocklist,
            "franchise": self._franchise_blocklist,
        }

    def clean_catalog(self, items: list, tiers: dict = None) -> dict:
        """Filter *items* through the configured tiers and return a result dict.

        Parameters
        ----------
        items : list
            List of item dicts, each with at minimum a ``"name"`` key.
        tiers : dict, optional
            Tier enable/disable flags.  Defaults to
            ``{"tier0": True, "tier1": True, "tier2": False, "tier3": True}``.

        Returns
        -------
        dict
            {
                "kept":    list[dict],   # items that survived all enabled tiers
                "removed": list[dict],   # {item, tier, reason} entries
                "report":  {             # summary statistics
                    "total":     int,
                    "kept":      int,
                    "removed":   int,
                    "by_tier":   {"tier0": int, "tier1": int, "tier2": int, "tier3": int},
                    "by_reason": {"short_name": int, ...},
                },
            }
        """
        # --- resolve tier configuration ------------------------------------
        if tiers is None:
            tiers = {"tier0": True, "tier1": True, "tier2": False, "tier3": True}

        tier0_enabled = bool(tiers.get("tier0", True))
        tier1_enabled = bool(tiers.get("tier1", True))
        tier2_enabled = bool(tiers.get("tier2", False))
        tier3_enabled = bool(tiers.get("tier3", True))

        kept: list = []
        removed: list = []
        by_tier: dict[str, int] = {"tier0": 0, "tier1": 0, "tier2": 0, "tier3": 0}
        by_reason: dict[str, int] = {}

        # --- per-item filtering loop ---------------------------------------
        for item in items:
            name: str = item.get("name", "")
            name_lower: str = name.lower()
            remove_info: Optional[tuple[str, str]] = None

            # Tier 0 — Noise / Garbage
            if tier0_enabled and remove_info is None:
                remove_info = self._check_tier0(name)

            # Tier 1 — NSFW Hard Block
            if tier1_enabled and remove_info is None:
                remove_info = self._check_tier_nsfw(name_lower, "hard_block")

            # Tier 2 — Suggestive
            if tier2_enabled and remove_info is None:
                remove_info = self._check_tier_nsfw(name_lower, "suggestive")

            # Tier 3 — Franchise / Character Noise
            if tier3_enabled and remove_info is None:
                remove_info = self._check_tier3(name, name_lower)

            if remove_info is not None:
                tier_label, reason = remove_info
                removed.append({"item": item, "tier": tier_label, "reason": reason})
                by_tier[tier_label] += 1
                by_reason[reason] = by_reason.get(reason, 0) + 1
            else:
                kept.append(item)

        # --- build report --------------------------------------------------
        total = len(items)
        report: dict[str, Any] = {
            "total": total,
            "kept": len(kept),
            "removed": len(removed),
            "by_tier": by_tier,
            "by_reason": by_reason,
        }
        self._last_report = report

        return {"kept": kept, "removed": removed, "report": report}

    def generate_report(self) -> dict:
        """Return the report from the most recent ``clean_catalog()`` call.

        If ``clean_catalog()`` has never been called, returns an empty report
        with all counts set to zero.
        """
        if self._last_report is None:
            return {
                "total": 0,
                "kept": 0,
                "removed": 0,
                "by_tier": {"tier0": 0, "tier1": 0, "tier2": 0, "tier3": 0},
                "by_reason": {},
            }
        return self._last_report

    # ------------------------------------------------------------------
    # Tier 0 — Noise / Garbage
    # ------------------------------------------------------------------

    @staticmethod
    def _check_tier0(name: str) -> Optional[tuple[str, str]]:
        """Check *name* against Tier-0 noise rules.  Returns ``(tier, reason)`` or ``None``."""
        # 1. Short names (≤ 3 characters)
        if len(name) <= 3:
            return ("tier0", "short_name")

        # 2. Username pattern — all lowercase alphanumeric/underscore,
        #    MUST contain at least one digit or underscore (otherwise
        #    common English words like 'shirt' would be false positives).
        if re.match(r"^[a-z0-9_]+$", name) and re.search(r"[0-9_]", name):
            return ("tier0", "username_pattern")

        # 3. Purely numeric names
        if re.match(r"^[0-9]+$", name):
            return ("tier0", "numeric_only")

        # 4. Brand suffix
        if name.endswith("(brand)"):
            return ("tier0", "brand_suffix")

        # 5. Game / series suffix
        if name.endswith("(game)") or name.endswith("(series)"):
            return ("tier0", "game_series_suffix")

        return None

    # ------------------------------------------------------------------
    # Tier 1 & 2 — NSFW (shared logic)
    # ------------------------------------------------------------------

    def _check_tier_nsfw(
        self, name_lower: str, tier_name: str
    ) -> Optional[tuple[str, str]]:
        """Check *name_lower* against the ``hard_block`` or ``suggestive`` tier.

        Returns ``("tier1", reason)`` or ``("tier2", reason)`` on match,
        or ``None`` if the name is clean.
        """
        tier_label = "tier1" if tier_name == "hard_block" else "tier2"
        categories = self._nsfw_blocklist["tiers"][tier_name]["categories"]

        for cat_name, cat_data in categories.items():
            # -- term matching (word-boundary) --
            for term in cat_data.get("terms", []):
                if self._term_matches(name_lower, term):
                    return (tier_label, f"{cat_name}_term")

            # -- regex pattern matching --
            for pattern in cat_data.get("patterns", []):
                if re.search(pattern, name_lower):
                    return (tier_label, f"{cat_name}_pattern")

        return None

    @staticmethod
    def _term_matches(name_lower: str, term: str) -> bool:
        """Return ``True`` if *term* appears as a whole-word / whole-phrase
        match inside *name_lower*.

        Uses ``\\b`` word-boundary anchors so that ``"sex"`` does not match
        ``"Essex"`` and ``"anal"`` does not match ``"analysis"``.

        Multi-word terms (e.g. ``"oral sex"``) are treated as a single
        phrase that must appear on word boundaries — this correctly
        matches ``"after oral sex"`` as well as ``"oral sex act"``.
        """
        escaped = re.escape(term.lower())
        return bool(re.search(r"\b" + escaped + r"\b", name_lower))

    # ------------------------------------------------------------------
    # Tier 3 — Franchise / Character Noise
    # ------------------------------------------------------------------

    def _check_tier3(self, name: str, name_lower: str) -> Optional[tuple[str, str]]:
        """Check *name* against Tier-3 rules (franchise, double-parens, ascension)."""
        # 1. Double-parenthesized (2+ parenthesized groups)
        paren_count = len(re.findall(r"\(.*?\)", name))
        if paren_count >= 2:
            return ("tier3", "double_parenthesized")

        # 2. Franchise terms (contains match)
        for entry in self._franchise_blocklist.get("franchises", []):
            term: str = entry["term"]
            if entry.get("match", "contains") == "contains" and term.lower() in name_lower:
                reason_term = term.lower().replace(" ", "_")
                return ("tier3", f"franchise_{reason_term}")

        # 3. Ascension variant
        if "ascension" in name_lower:
            return ("tier3", "ascension_variant")

        return None
