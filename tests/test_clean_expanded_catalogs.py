"""
TDD test suite for CatalogCleaner (tools/clean_expanded_catalogs.py).

These tests are written BEFORE the implementation exists. They define the
expected behavior of the CatalogCleaner class across all four filtering tiers.

Expected Class Interface:
    CatalogCleaner(blocklist_dir: Path = None)
    CatalogCleaner.clean_catalog(items: list, tiers: dict = None) -> dict
    CatalogCleaner.load_blocklists() -> dict
    CatalogCleaner.generate_report() -> dict

CatalogCleaner.clean_catalog() return value:
    {
        "kept": list,        # items that survived filtering
        "removed": list,     # items that were removed: {item: ..., tier: str, reason: str}
        "report": {          # summary statistics
            "total": int,
            "kept": int,
            "removed": int,
            "by_tier": {"tier0": int, "tier1": int, "tier2": int, "tier3": int},
            "by_reason": {"short_name": int, "username_pattern": int, ...}
        }
    }

Tiers (default configuration):
    tier0  — Noise/garbage (ALWAYS ON): short names, usernames, numerics, brands
    tier1  — NSFW hard block (ALWAYS ON): explicit content, genitals, fluids
    tier2  — Suggestive (DEFAULTS OFF): lingerie, positions, body focus
    tier3  — Franchise/character noise (ALWAYS ON): franchise references, variants
"""

import pytest
from pathlib import Path
import copy

# -- Import (will fail until implementation exists -- expected TDD failure) --
from tools.clean_expanded_catalogs import CatalogCleaner


# ---------------------------------------------------------------------------
# FIXTURES
# ---------------------------------------------------------------------------

@pytest.fixture
def blocklist_dir():
    """Path to the blocklist directory."""
    return Path(__file__).parent.parent / "tools"


@pytest.fixture
def cleaner(blocklist_dir):
    """Create a CatalogCleaner with default settings."""
    return CatalogCleaner(blocklist_dir=blocklist_dir)


@pytest.fixture
def clean_catalog_items():
    """Items that should survive ALL filtering tiers (baseline valid items)."""
    return [
        {"id": "ponytail", "name": "ponytail", "category": "hair", "group": "style"},
        {"id": "blue_eyes", "name": "blue eyes", "category": "eyes", "group": "color"},
        {"id": "shirt", "name": "shirt", "category": "clothing", "group": "upper_body"},
        {"id": "standing", "name": "standing", "category": "poses", "group": "general"},
        {"id": "school_uniform", "name": "school uniform", "category": "clothing", "group": "uniform"},
        {"id": "arm_behind_back", "name": "arm behind back", "category": "poses", "group": "general"},
        {"id": "long_hair", "name": "long hair", "category": "hair", "group": "length"},
        {"id": "smile", "name": "smile", "category": "expressions", "group": "general"},
    ]


@pytest.fixture
def tier0_noise_items():
    """Tier 0 candidates — noise, garbage, usernames, brands."""
    return [
        {"id": "a", "name": "a", "category": "clothing", "group": "upper_body"},
        {"id": "abc", "name": "abc", "category": "clothing", "group": "upper_body"},
        {"id": "yuki_mizuki_79", "name": "yuki_mizuki_79", "category": "clothing", "group": "general"},
        {"id": "12345", "name": "12345", "category": "clothing", "group": "general"},
        {"id": "brand_item", "name": "some tag (brand)", "category": "clothing", "group": "general"},
        {"id": "caps", "name": "caps", "category": "hair", "group": "style"},
    ]


@pytest.fixture
def tier0_valid_short_items():
    """Edge-case short names that COULD be valid (but tier0 currently filters ≤3 chars)."""
    return [
        {"id": "bob", "name": "bob", "category": "hair", "group": "style"},
        {"id": "cap", "name": "cap", "category": "clothing", "group": "headwear"},
    ]


@pytest.fixture
def tier1_nsfw_items():
    """Tier 1 candidates — NSFW hard block content."""
    return [
        {"id": "thigh_sex", "name": "after thigh sex", "category": "poses", "group": "general"},
        {"id": "penis_face", "name": "penis on face", "category": "body", "group": "general"},
        {"id": "cum_breasts", "name": "cum on breasts", "category": "body", "group": "general"},
        {"id": "guro_magala", "name": "guro magala", "category": "general", "group": "general"},
    ]


@pytest.fixture
def tier1_sfw_body_items():
    """SFW body-part items that must NOT be filtered by Tier 1."""
    return [
        {"id": "arm_back", "name": "arm behind back", "category": "poses", "group": "general"},
        {"id": "hands_on_hips", "name": "hands on hips", "category": "poses", "group": "general"},
        {"id": "leg_crossed", "name": "leg crossed", "category": "poses", "group": "general"},
    ]


@pytest.fixture
def tier2_suggestive_items():
    """Tier 2 candidates — suggestive/risqué items (defaults OFF)."""
    return [
        {"id": "lace_panties", "name": "lace panties", "category": "clothing", "group": "underwear"},
        {"id": "corset_top", "name": "corset top", "category": "clothing", "group": "upper_body"},
        {"id": "thong_sandal", "name": "thong sandal", "category": "clothing", "group": "footwear"},
    ]


@pytest.fixture
def tier3_franchise_items():
    """Tier 3 candidates — franchise/character-specific items."""
    return [
        {"id": "saber_alter", "name": "saber alter (fate)", "category": "clothing", "group": "general"},
        {"id": "abigail_swimsuit", "name": "abigail williams (swimsuit) (fate)", "category": "clothing", "group": "general"},
        {"id": "genshin_outfit", "name": "genshin impact outfit", "category": "clothing", "group": "general"},
        {"id": "touhou_hat", "name": "touhou character hat", "category": "clothing", "group": "headwear"},
    ]


@pytest.fixture
def tier3_generic_items():
    """Generic items with NO franchise affiliation — must survive Tier 3."""
    return [
        {"id": "school_uniform_generic", "name": "school uniform", "category": "clothing", "group": "uniform"},
        {"id": "kimono", "name": "kimono", "category": "clothing", "group": "full_body"},
        {"id": "sailor_outfit", "name": "sailor outfit", "category": "clothing", "group": "full_body"},
    ]


@pytest.fixture
def full_mixed_catalog(
    tier0_noise_items,
    tier0_valid_short_items,
    tier1_nsfw_items,
    tier1_sfw_body_items,
    tier2_suggestive_items,
    tier3_franchise_items,
    tier3_generic_items,
    clean_catalog_items,
):
    """A complete mixed catalog containing items from ALL tiers for E2E testing."""
    all_items = (
        tier0_noise_items
        + tier0_valid_short_items
        + tier1_nsfw_items
        + tier1_sfw_body_items
        + tier2_suggestive_items
        + tier3_franchise_items
        + tier3_generic_items
        + clean_catalog_items
    )
    return all_items


@pytest.fixture
def default_tiers():
    """Default tier configuration — tier2 is OFF."""
    return {"tier0": True, "tier1": True, "tier2": False, "tier3": True}


@pytest.fixture
def tier2_enabled_tiers():
    """Tier configuration with tier2 (suggestive) ENABLED."""
    return {"tier0": True, "tier1": True, "tier2": True, "tier3": True}


# ---------------------------------------------------------------------------
# TIER 0 - NOISE / GARBAGE
# ---------------------------------------------------------------------------

class TestTier0NoiseGarbage:
    """Tier 0 filtering: short names, usernames, numerics, brands."""

    def test_removes_short_names(self, cleaner, tier0_noise_items, clean_catalog_items):
        """Items with name length ≤ 3 characters are removed."""
        test_items = tier0_noise_items[:2] + clean_catalog_items  # "a", "abc"
        tiers = {"tier0": True, "tier1": False, "tier2": False, "tier3": False}

        result = cleaner.clean_catalog(test_items, tiers=tiers)
        kept_names = [item["name"] for item in result["kept"]]

        assert "a" not in kept_names, "Single-char name 'a' should be filtered"
        assert "abc" not in kept_names, "Three-char name 'abc' should be filtered"
        assert "ponytail" in kept_names, "Valid 4+ char item should survive"

    def test_removes_username_pattern(self, cleaner, tier0_noise_items, clean_catalog_items):
        """Items matching alphanumeric-only (no caps, no spaces) are removed as usernames."""
        test_items = [tier0_noise_items[2]] + clean_catalog_items  # "yuki_mizuki_79"
        tiers = {"tier0": True, "tier1": False, "tier2": False, "tier3": False}

        result = cleaner.clean_catalog(test_items, tiers=tiers)
        kept_names = [item["name"] for item in result["kept"]]

        assert "yuki_mizuki_79" not in kept_names, "Username pattern should be filtered"

    def test_removes_numeric_only(self, cleaner, tier0_noise_items, clean_catalog_items):
        """Items with purely numeric names are removed."""
        test_items = [tier0_noise_items[3]] + clean_catalog_items  # "12345"
        tiers = {"tier0": True, "tier1": False, "tier2": False, "tier3": False}

        result = cleaner.clean_catalog(test_items, tiers=tiers)
        kept_names = [item["name"] for item in result["kept"]]

        assert "12345" not in kept_names, "Numeric-only name should be filtered"

    def test_filters_valid_looking_short_names(self, cleaner, tier0_valid_short_items, clean_catalog_items):
        """Edge case: names like 'bob', 'cap' are ≤3 chars and filtered by tier0.
        This is documented behavior — ≤3 char names are always filtered.
        If this behavior changes, update the test."""
        test_items = tier0_valid_short_items + clean_catalog_items
        tiers = {"tier0": True, "tier1": False, "tier2": False, "tier3": False}

        result = cleaner.clean_catalog(test_items, tiers=tiers)
        kept_names = [item["name"] for item in result["kept"]]

        # Current tier0 rule: all ≤3 char names are removed
        assert "bob" not in kept_names, (
            "≤3 char names are filtered by tier0. "
            "Documented behavior: short names cannot be validated without NLP."
        )
        assert "cap" not in kept_names, (
            "≤3 char names are filtered by tier0. "
            "Documented behavior: short names cannot be validated without NLP."
        )

    def test_removes_brand_items(self, cleaner, tier0_noise_items, clean_catalog_items):
        """Items with '(brand)' suffix are removed."""
        test_items = [tier0_noise_items[4]] + clean_catalog_items  # "some tag (brand)"
        tiers = {"tier0": True, "tier1": False, "tier2": False, "tier3": False}

        result = cleaner.clean_catalog(test_items, tiers=tiers)
        kept_names = [item["name"] for item in result["kept"]]

        assert "some tag (brand)" not in kept_names, "Items with '(brand)' suffix should be filtered"


# ---------------------------------------------------------------------------
# TIER 1 - NSFW HARD BLOCK
# ---------------------------------------------------------------------------

class TestTier1NSFWHardBlock:
    """Tier 1 filtering: explicit sexual content, genitals, fluids, extreme."""

    def test_removes_explicit_sex_acts(self, cleaner, tier1_nsfw_items, clean_catalog_items):
        """Items containing explicit sex act references are removed."""
        test_items = [tier1_nsfw_items[0]] + clean_catalog_items  # "after thigh sex"
        tiers = {"tier0": False, "tier1": True, "tier2": False, "tier3": False}

        result = cleaner.clean_catalog(test_items, tiers=tiers)
        kept_names = [item["name"] for item in result["kept"]]

        assert "after thigh sex" not in kept_names, "Explicit sex act reference should be filtered"

    def test_removes_genital_references(self, cleaner, tier1_nsfw_items, clean_catalog_items):
        """Items referencing genitals are removed."""
        test_items = [tier1_nsfw_items[1]] + clean_catalog_items  # "penis on face"
        tiers = {"tier0": False, "tier1": True, "tier2": False, "tier3": False}

        result = cleaner.clean_catalog(test_items, tiers=tiers)
        kept_names = [item["name"] for item in result["kept"]]

        assert "penis on face" not in kept_names, "Genital reference should be filtered"

    def test_removes_bodily_fluids(self, cleaner, tier1_nsfw_items, clean_catalog_items):
        """Items referencing bodily fluids (cum, semen, etc.) are removed."""
        test_items = [tier1_nsfw_items[2]] + clean_catalog_items  # "cum on breasts"
        tiers = {"tier0": False, "tier1": True, "tier2": False, "tier3": False}

        result = cleaner.clean_catalog(test_items, tiers=tiers)
        kept_names = [item["name"] for item in result["kept"]]

        assert "cum on breasts" not in kept_names, "Bodily fluid reference should be filtered"

    def test_removes_extreme_content(self, cleaner, tier1_nsfw_items, clean_catalog_items):
        """Items referencing extreme/guro/horror content are removed."""
        test_items = [tier1_nsfw_items[3]] + clean_catalog_items  # "guro magala"
        tiers = {"tier0": False, "tier1": True, "tier2": False, "tier3": False}

        result = cleaner.clean_catalog(test_items, tiers=tiers)
        kept_names = [item["name"] for item in result["kept"]]

        assert "guro magala" not in kept_names, "Extreme/guro content should be filtered"

    def test_keeps_sfw_body_parts(self, cleaner, tier1_sfw_body_items, clean_catalog_items):
        """SFW body-part items (arm, hands, leg) are KEPT — not flagged as NSFW."""
        test_items = tier1_sfw_body_items + clean_catalog_items
        tiers = {"tier0": False, "tier1": True, "tier2": False, "tier3": False}

        result = cleaner.clean_catalog(test_items, tiers=tiers)
        kept_names = set(item["name"] for item in result["kept"])

        assert "arm behind back" in kept_names, "SFW body reference 'arm behind back' must survive Tier 1"
        assert "hands on hips" in kept_names, "SFW body reference 'hands on hips' must survive Tier 1"
        assert "leg crossed" in kept_names, "SFW body reference 'leg crossed' must survive Tier 1"


# ---------------------------------------------------------------------------
# TIER 2 - SUGGESTIVE (CONFIGURABLE, DEFAULTS OFF)
# ---------------------------------------------------------------------------

class TestTier2Suggestive:
    """Tier 2 filtering: suggestive/risqué items — DISABLED by default."""

    def test_disabled_by_default(self, cleaner, tier2_suggestive_items, clean_catalog_items):
        """With default config, suggestive items like 'lace panties' are KEPT."""
        test_items = tier2_suggestive_items + clean_catalog_items
        # Default tiers: tier2 is False (disabled)
        tiers = {"tier0": False, "tier1": False, "tier2": False, "tier3": False}

        result = cleaner.clean_catalog(test_items, tiers=tiers)
        kept_names = set(item["name"] for item in result["kept"])

        assert "lace panties" in kept_names, (
            "Tier 2 is OFF by default — 'lace panties' should survive"
        )
        assert "corset top" in kept_names, (
            "Tier 2 is OFF by default — 'corset top' should survive"
        )

    def test_removes_when_enabled(self, cleaner, tier2_suggestive_items, clean_catalog_items):
        """When tier2 is enabled, suggestive items like 'lace panties' are removed."""
        test_items = tier2_suggestive_items + clean_catalog_items
        tiers = {"tier0": False, "tier1": False, "tier2": True, "tier3": False}

        result = cleaner.clean_catalog(test_items, tiers=tiers)
        kept_names = set(item["name"] for item in result["kept"])

        assert "lace panties" not in kept_names, (
            "Tier 2 is ON — 'lace panties' (underwear) should be filtered"
        )
        assert "corset top" not in kept_names, (
            "Tier 2 is ON — 'corset top' (intimate apparel) should be filtered"
        )
        # 'thong sandal' may or may not match — thong is ambiguous (footwear vs underwear)
        # The blocklist uses word-boundary patterns, so 'thong sandal' might survive.
        # This depends on implementation; if it gets filtered, that's also acceptable.


# ---------------------------------------------------------------------------
# TIER 3 - FRANCHISE / CHARACTER NOISE
# ---------------------------------------------------------------------------

class TestTier3FranchiseNoise:
    """Tier 3 filtering: franchise-specific and character-variant items."""

    def test_removes_franchise_items(self, cleaner, tier3_franchise_items, clean_catalog_items):
        """Items containing franchise references (e.g., '(fate)') are removed."""
        test_items = [tier3_franchise_items[0]] + clean_catalog_items  # "saber alter (fate)"
        tiers = {"tier0": False, "tier1": False, "tier2": False, "tier3": True}

        result = cleaner.clean_catalog(test_items, tiers=tiers)
        kept_names = set(item["name"] for item in result["kept"])

        assert "saber alter (fate)" not in kept_names, (
            "Franchise-tagged item should be filtered by Tier 3"
        )

    def test_removes_double_parens(self, cleaner, tier3_franchise_items, clean_catalog_items):
        """Items with multiple parenthesized qualifiers (character + franchise) are removed."""
        test_items = [tier3_franchise_items[1]] + clean_catalog_items  # double-parens
        tiers = {"tier0": False, "tier1": False, "tier2": False, "tier3": True}

        result = cleaner.clean_catalog(test_items, tiers=tiers)
        kept_names = set(item["name"] for item in result["kept"])

        assert "abigail williams (swimsuit) (fate)" not in kept_names, (
            "Double-parenthesized character+variant+franchise item should be filtered"
        )

    def test_removes_genshin_items(self, cleaner, tier3_franchise_items, clean_catalog_items):
        """Items referencing Genshin Impact are removed."""
        test_items = [tier3_franchise_items[2]] + clean_catalog_items
        tiers = {"tier0": False, "tier1": False, "tier2": False, "tier3": True}

        result = cleaner.clean_catalog(test_items, tiers=tiers)
        kept_names = set(item["name"] for item in result["kept"])

        assert "genshin impact outfit" not in kept_names, (
            "Genshin Impact reference should be filtered as franchise content"
        )

    def test_keeps_generic_items(self, cleaner, tier3_generic_items, clean_catalog_items):
        """Generic items (school uniform, kimono) with NO franchise ref are KEPT."""
        test_items = tier3_generic_items + clean_catalog_items
        tiers = {"tier0": False, "tier1": False, "tier2": False, "tier3": True}

        result = cleaner.clean_catalog(test_items, tiers=tiers)
        kept_names = set(item["name"] for item in result["kept"])

        assert "school uniform" in kept_names, "Generic 'school uniform' must survive Tier 3"
        assert "kimono" in kept_names, "Generic 'kimono' must survive Tier 3"
        assert "sailor outfit" in kept_names, "Generic 'sailor outfit' must survive Tier 3"


# ---------------------------------------------------------------------------
# END-TO-END / INTEGRATION
# ---------------------------------------------------------------------------

class TestEndToEnd:
    """Full pipeline and cross-cutting tests."""

    def test_full_clean_pipeline_default_tiers(self, cleaner, full_mixed_catalog, default_tiers):
        """E2E: feed a mixed catalog through all default tiers, verify removal counts."""
        result = cleaner.clean_catalog(full_mixed_catalog, tiers=default_tiers)

        # Result structure
        assert "kept" in result, "Result must contain 'kept' list"
        assert "removed" in result, "Result must contain 'removed' list"
        assert "report" in result, "Result must contain 'report' dict"

        kept = result["kept"]
        removed = result["removed"]
        report = result["report"]

        # Total count invariance
        total_items = len(full_mixed_catalog)
        assert len(kept) + len(removed) == total_items, (
            f"kept ({len(kept)}) + removed ({len(removed)}) != total ({total_items})"
        )

        # With default tiers (tier2 OFF), we expect:
        #   tier0 removes: "a", "abc", "yuki_mizuki_79", "12345", "some tag (brand)" + "bob", "cap" = 7
        #     (plus possibly "caps" if it matches noise patterns)
        #   tier1 removes: "after thigh sex", "penis on face", "cum on breasts", "guro magala" = 4
        #   tier2 (OFF): nothing removed
        #   tier3 removes: "saber alter (fate)", "abigail williams (swimsuit) (fate)",
        #                  "genshin impact outfit", "touhou character hat" = 4
        #
        # Clean items (8) + tier1 SFW (3) + tier3 generic (3) + tier2 suggestive (3) = should be kept
        #   = 8 + 3 + 3 + 3 = 17 kept (if "caps" survives) or 16 (if "caps" filtered)

        # Verify report contains the expected keys
        assert report["total"] == total_items
        assert "by_tier" in report
        assert "by_reason" in report

        # Tier 2 should have zero removals (disabled)
        assert report["by_tier"]["tier2"] == 0, (
            "Tier 2 is disabled — removal count should be 0"
        )

        # Verify SFW items survived
        kept_names = set(item["name"] for item in kept)
        assert "ponytail" in kept_names
        assert "school uniform" in kept_names
        assert "arm behind back" in kept_names
        assert "smile" in kept_names

        # Verify NSFW items removed
        removed_names = set(item["item"]["name"] for item in removed)
        assert "after thigh sex" in removed_names
        assert "penis on face" in removed_names
        assert "cum on breasts" in removed_names
        assert "guro magala" in removed_names

        # With tier2 OFF, suggestive items survive
        assert "lace panties" in kept_names, "Tier 2 OFF — suggestive items should survive"

        # Verify tier3 franchise items removed
        assert "saber alter (fate)" in removed_names
        assert "abigail williams (swimsuit) (fate)" in removed_names

    def test_full_clean_pipeline_tier2_enabled(self, cleaner, full_mixed_catalog, tier2_enabled_tiers):
        """E2E: with tier2 enabled, suggestive items are also removed."""
        result = cleaner.clean_catalog(full_mixed_catalog, tiers=tier2_enabled_tiers)

        kept_names = set(item["name"] for item in result["kept"])
        removed_names = set(item["item"]["name"] for item in result["removed"])

        assert "lace panties" in removed_names, (
            "Tier 2 ON — 'lace panties' should be removed"
        )
        assert result["report"]["by_tier"]["tier2"] > 0, (
            "Tier 2 is enabled — removal count should be > 0"
        )

    def test_idempotent(self, cleaner, full_mixed_catalog, default_tiers):
        """Running cleaner twice on the same data produces identical results."""
        result1 = cleaner.clean_catalog(full_mixed_catalog, tiers=default_tiers)
        result2 = cleaner.clean_catalog(full_mixed_catalog, tiers=default_tiers)

        names1 = sorted(item["name"] for item in result1["kept"])
        names2 = sorted(item["name"] for item in result2["kept"])
        assert names1 == names2, "Idempotent: kept items should be identical both runs"

        removed_names1 = sorted(item["item"]["name"] for item in result1["removed"])
        removed_names2 = sorted(item["item"]["name"] for item in result2["removed"])
        assert removed_names1 == removed_names2, (
            "Idempotent: removed items should be identical both runs"
        )

        assert result1["report"]["kept"] == result2["report"]["kept"]
        assert result1["report"]["removed"] == result2["report"]["removed"]

        # Running again on already-cleaned data should not change results further
        result3 = cleaner.clean_catalog(result1["kept"], tiers=default_tiers)
        assert len(result3["kept"]) == len(result1["kept"]), (
            "Idempotent: cleaning already-clean data should not remove more items"
        )

    def test_report_generated(self, cleaner, full_mixed_catalog, default_tiers):
        """Cleaner produces a summary report dict with expected keys and structure."""
        result = cleaner.clean_catalog(full_mixed_catalog, tiers=default_tiers)
        report = result["report"]

        # Required top-level keys
        assert "total" in report
        assert "kept" in report
        assert "removed" in report
        assert "by_tier" in report
        assert "by_reason" in report

        # Type checks
        assert isinstance(report["total"], int), "total must be int"
        assert isinstance(report["kept"], int), "kept must be int"
        assert isinstance(report["removed"], int), "removed must be int"
        assert isinstance(report["by_tier"], dict), "by_tier must be dict"
        assert isinstance(report["by_reason"], dict), "by_reason must be dict"

        # Invariants
        assert report["kept"] + report["removed"] == report["total"], (
            "kept + removed must equal total"
        )
        assert sum(report["by_tier"].values()) == report["removed"], (
            "sum(by_tier) must equal total removed"
        )
        assert sum(report["by_reason"].values()) == report["removed"], (
            "sum(by_reason) must equal total removed"
        )

    def test_load_blocklists(self, cleaner):
        """Blocklists are loaded correctly and contain expected structure."""
        blocklists = cleaner.load_blocklists()

        assert "nsfw" in blocklists, "NSFW blocklist should be loaded"
        assert "franchise" in blocklists, "Franchise blocklist should be loaded"

        nsfw = blocklists["nsfw"]
        assert "tiers" in nsfw
        assert "hard_block" in nsfw["tiers"]
        assert "suggestive" in nsfw["tiers"]

        franchise = blocklists["franchise"]
        assert "franchises" in franchise
        assert "noise_patterns" in franchise

    def test_generate_report_standalone(self, cleaner, full_mixed_catalog, default_tiers):
        """generate_report() can be called after clean_catalog to get the latest report."""
        cleaner.clean_catalog(full_mixed_catalog, tiers=default_tiers)
        report = cleaner.generate_report()

        assert "total" in report
        assert "kept" in report
        assert "removed" in report
        assert isinstance(report["total"], int)

    def test_empty_catalog(self, cleaner, default_tiers):
        """Cleaning an empty catalog returns empty results, not errors."""
        result = cleaner.clean_catalog([], tiers=default_tiers)

        assert result["kept"] == [], "Empty input → empty kept list"
        assert result["removed"] == [], "Empty input → empty removed list"
        assert result["report"]["total"] == 0
        assert result["report"]["kept"] == 0
        assert result["report"]["removed"] == 0

    def test_all_tiers_disabled(self, cleaner, full_mixed_catalog):
        """When all tiers are disabled, no items are removed."""
        all_off = {"tier0": False, "tier1": False, "tier2": False, "tier3": False}
        result = cleaner.clean_catalog(full_mixed_catalog, tiers=all_off)

        assert len(result["kept"]) == len(full_mixed_catalog), (
            "All tiers OFF — all items should be kept"
        )
        assert len(result["removed"]) == 0, (
            "All tiers OFF — nothing should be removed"
        )

    def test_preserves_item_structure(self, cleaner, clean_catalog_items, default_tiers):
        """Cleaned items preserve their full structure (id, name, category, group, etc.)."""
        result = cleaner.clean_catalog(clean_catalog_items, tiers=default_tiers)
        kept = result["kept"]

        for item in kept:
            assert "id" in item
            assert "name" in item
            assert "category" in item
            assert "group" in item

    def test_removed_items_have_reason(self, cleaner, full_mixed_catalog, default_tiers):
        """Each removed item includes the tier and reason for removal."""
        result = cleaner.clean_catalog(full_mixed_catalog, tiers=default_tiers)

        for removed_entry in result["removed"]:
            assert "item" in removed_entry, "Each removed entry must include the original item"
            assert "tier" in removed_entry, "Each removed entry must specify which tier filtered it"
            assert "reason" in removed_entry, "Each removed entry must include a reason string"

            # Tier should be a valid value
            assert removed_entry["tier"] in ["tier0", "tier1", "tier2", "tier3"], (
                f"Unexpected tier value: {removed_entry['tier']}"
            )

            # Reason should be a non-empty string
            assert isinstance(removed_entry["reason"], str)
            assert len(removed_entry["reason"]) > 0, "Removal reason should not be empty"

    def test_does_not_mutate_input(self, cleaner, full_mixed_catalog, default_tiers):
        """The cleaner should not mutate the input list (functional purity)."""
        original = copy.deepcopy(full_mixed_catalog)
        result = cleaner.clean_catalog(full_mixed_catalog, tiers=default_tiers)

        # Input list should be unchanged
        assert len(full_mixed_catalog) == len(original), (
            "Input list length should not change after cleaning"
        )
        for orig_item, cleaned_item in zip(original, full_mixed_catalog):
            assert orig_item == cleaned_item, (
                "Input items should not be mutated by cleaning"
            )

        # Result items should be references to original items (not copies)
        if result["kept"]:
            kept_id = result["kept"][0]["id"]
            for item in full_mixed_catalog:
                if item["id"] == kept_id:
                    assert result["kept"][0] is item, (
                        "Kept items should be references to original items"
                    )
                    break


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
