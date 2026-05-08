#!/usr/bin/env python3
"""
Tag Expansion Pipeline with Smart Categorization.

This script processes Cleaned_all_tags.csv and generates expanded catalog files
with proper categorization. Action verbs take priority for classification.

Usage:
    python tools/expand_catalog_pipeline.py --dry-run
    python tools/expand_catalog_pipeline.py --min-frequency 2
"""

import argparse
import csv
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


# ──────────────────────────────────────────────────────────────────────────────
# ACTION VERB PATTERNS - These take PRIORITY for classification
# ──────────────────────────────────────────────────────────────────────────────

ACTION_VERBS = {
    # Body/object touching (gesture_body_touch)
    "grab", "grabbing", "grabs",
    "press", "pressing", "pressed",
    "squeeze", "squeezing", "squeezed",
    "touch", "touching", "touches",
    "push", "pushing", "pushed",
    "fondle", "fondling", "fondled",
    "grope", "groping", "groped",
    "caress", "caressing", "caressed",
    "rub", "rubbing", "rubbed",
    "poke", "poking", "poked",

    # Clothing/item manipulation (gesture_clothing_adjust)
    "lift", "lifting", "lifted",
    "pull", "pulling", "pulled",
    "adjust", "adjusting", "adjusted",
    "tug", "tugging", "tugged",
    "remove", "removing", "removed",
    "unzip", "unzipping", "unzipped",
    "unbutton", "unbuttoning", "unbuttoned",
    "untie", "untying", "untied",
    "roll up", "rolling up",
    "tuck", "tucking", "tucked",

    # Object interaction (gesture_object_interaction)
    "hold", "holding", "holds",
    "carry", "carrying", "carried",
    "wield", "wielding", "wielded",
    "grip", "gripping", "gripped",
    "clutch", "clutching", "clutched",
    "cradle", "cradling", "cradled",
    "hug", "hugging", "hugged",
    "embrace", "embracing", "embraced",
}

# Map action verbs to gesture groups
ACTION_VERB_GROUPS = {
    # Body touch actions
    "grab": "gesture_body_touch", "grabbing": "gesture_body_touch", "grabs": "gesture_body_touch",
    "press": "gesture_body_touch", "pressing": "gesture_body_touch", "pressed": "gesture_body_touch",
    "squeeze": "gesture_body_touch", "squeezing": "gesture_body_touch", "squeezed": "gesture_body_touch",
    "touch": "gesture_body_touch", "touching": "gesture_body_touch", "touches": "gesture_body_touch",
    "push": "gesture_body_touch", "pushing": "gesture_body_touch", "pushed": "gesture_body_touch",
    "fondle": "gesture_body_touch", "fondling": "gesture_body_touch", "fondled": "gesture_body_touch",
    "grope": "gesture_body_touch", "groping": "gesture_body_touch", "groped": "gesture_body_touch",
    "caress": "gesture_body_touch", "caressing": "gesture_body_touch", "caressed": "gesture_body_touch",
    "rub": "gesture_body_touch", "rubbing": "gesture_body_touch", "rubbed": "gesture_body_touch",
    "poke": "gesture_body_touch", "poking": "gesture_body_touch", "poked": "gesture_body_touch",

    # Clothing adjustment actions
    "lift": "gesture_clothing_adjust", "lifting": "gesture_clothing_adjust", "lifted": "gesture_clothing_adjust",
    "pull": "gesture_clothing_adjust", "pulling": "gesture_clothing_adjust", "pulled": "gesture_clothing_adjust",
    "adjust": "gesture_clothing_adjust", "adjusting": "gesture_clothing_adjust", "adjusted": "gesture_clothing_adjust",
    "tug": "gesture_clothing_adjust", "tugging": "gesture_clothing_adjust", "tugged": "gesture_clothing_adjust",
    "remove": "gesture_clothing_adjust", "removing": "gesture_clothing_adjust", "removed": "gesture_clothing_adjust",
    "unzip": "gesture_clothing_adjust", "unzipping": "gesture_clothing_adjust", "unzipped": "gesture_clothing_adjust",
    "unbutton": "gesture_clothing_adjust", "unbuttoning": "gesture_clothing_adjust", "unbuttoned": "gesture_clothing_adjust",
    "untie": "gesture_clothing_adjust", "untying": "gesture_clothing_adjust", "untied": "gesture_clothing_adjust",
    "roll up": "gesture_clothing_adjust", "rolling up": "gesture_clothing_adjust",
    "tuck": "gesture_clothing_adjust", "tucking": "gesture_clothing_adjust", "tucked": "gesture_clothing_adjust",

    # Object interaction actions
    "hold": "gesture_object_interaction", "holding": "gesture_object_interaction", "holds": "gesture_object_interaction",
    "carry": "gesture_object_interaction", "carrying": "gesture_object_interaction", "carried": "gesture_object_interaction",
    "wield": "gesture_object_interaction", "wielding": "gesture_object_interaction", "wielded": "gesture_object_interaction",
    "grip": "gesture_object_interaction", "gripping": "gesture_object_interaction", "gripped": "gesture_object_interaction",
    "clutch": "gesture_object_interaction", "clutching": "gesture_object_interaction", "clutched": "gesture_object_interaction",
    "cradle": "gesture_object_interaction", "cradling": "gesture_object_interaction", "cradled": "gesture_object_interaction",
    "hug": "gesture_object_interaction", "hugging": "gesture_object_interaction", "hugged": "gesture_object_interaction",
    "embrace": "gesture_object_interaction", "embracing": "gesture_object_interaction", "embraced": "gesture_object_interaction",
}


# ──────────────────────────────────────────────────────────────────────────────
# OBJECT-BASED KEYWORD PATTERNS (Fallback when no action verb)
# ──────────────────────────────────────────────────────────────────────────────

KEYWORD_PATTERNS = {
    # Hair attributes
    "hair": {
        "keywords": ["hair", "ahoge", "bangs", "ponytail", "twintails", "pigtails",
                     "braid", "braids", "sidelocks", "forelock", "cowlick", "bun",
                     "bob cut", "hime cut", "drill", "ringlets", "curls", "straight hair",
                     "wavy hair", "long hair", "short hair", "medium hair", "very long hair"],
        "category": "hair",
        "group": "hair_style",
    },

    # Eye attributes
    "eyes": {
        "keywords": ["eyes", "eye", "pupils", "heterochromia", "iris", "eyelashes",
                     "tsurime", "tareme", "jitome", "glowing eyes", "empty eyes",
                     "half-closed eyes", "closed eyes", "one eye closed"],
        "category": "eyes",
        "group": "eye_attributes",
    },

    # Body type/features
    "body": {
        "keywords": ["breast", "breasts", "chest", "thigh", "thighs", "hip", "hips",
                     "leg", "legs", "arm", "arms", "butt", "ass", "stomach", "belly",
                     "navel", "collarbone", "shoulder", "shoulders", "back", "waist",
                     "neck", "face", "lips", "skin", "tan", "pale", "muscular",
                     "petite", "tall", "short", "slim", "curvy", "athletic",
                     "small breasts", "medium breasts", "large breasts", "huge breasts"],
        "category": "body",
        "group": "body_features",
    },

    # Expressions/emotions
    "expressions": {
        "keywords": ["smile", "smiling", "grin", "laugh", "laughing", "cry", "crying",
                     "tears", "blush", "blushing", "angry", "sad", "happy", "scared",
                     "surprised", "shocked", "embarrassed", "shy", "nervous", "excited",
                     "sleepy", "tired", "annoyed", "pout", "pouting", "frown", "frowning",
                     "expressionless", "serious", "determined", "confident", "smirk"],
        "category": "expressions",
        "group": "emotion",
    },

    # Clothing - upper body
    "clothing_upper": {
        "keywords": ["shirt", "blouse", "sweater", "jacket", "coat", "hoodie",
                     "cardigan", "vest", "tank top", "crop top", "tube top", "bra",
                     "bikini top", "sports bra", "corset", "bustier", "camisole",
                     "turtleneck", "polo", "t-shirt"],
        "category": "clothing",
        "group": "upper_body",
    },

    # Clothing - lower body
    "clothing_lower": {
        "keywords": ["skirt", "shorts", "pants", "jeans", "leggings", "tights",
                     "panties", "underwear", "bikini bottom", "miniskirt", "pleated skirt",
                     "long skirt", "pencil skirt", "hotpants", "bloomers", "hakama"],
        "category": "clothing",
        "group": "lower_body",
    },

    # Clothing - full body
    "clothing_full": {
        "keywords": ["dress", "gown", "kimono", "yukata", "hanfu", "qipao", "cheongsam",
                     "swimsuit", "bodysuit", "jumpsuit", "romper", "maid outfit",
                     "school uniform", "military uniform", "nurse uniform", "nun habit",
                     "wedding dress", "evening gown", "sundress", "sailor uniform"],
        "category": "clothing",
        "group": "full_body",
    },

    # Clothing - accessories/head
    "clothing_head": {
        "keywords": ["hat", "cap", "beret", "crown", "tiara", "headband", "hairpin",
                     "hair ribbon", "hair bow", "headphones", "earrings", "glasses",
                     "sunglasses", "mask", "veil", "hood", "helmet"],
        "category": "clothing",
        "group": "head",
    },

    # Clothing - footwear
    "clothing_feet": {
        "keywords": ["shoes", "boots", "heels", "sandals", "slippers", "sneakers",
                     "loafers", "mary janes", "thigh highs", "knee highs", "socks",
                     "stockings", "pantyhose", "barefoot", "ankle boots"],
        "category": "clothing",
        "group": "feet",
    },

    # Poses (non-gesture body positions)
    "poses": {
        "keywords": ["standing", "sitting", "lying", "kneeling", "crouching", "squatting",
                     "leaning", "bending", "stretching", "walking", "running", "jumping",
                     "floating", "flying", "falling", "sleeping", "reclining", "lounging",
                     "seiza", "wariza", "crossed legs", "spread legs", "curled up"],
        "category": "poses",
        "group": "pose_position",
    },

    # View angles
    "view_angles": {
        "keywords": ["from above", "from below", "from side", "from behind", "front view",
                     "back view", "profile", "three-quarter view", "close-up", "full body",
                     "upper body", "portrait", "cowboy shot", "dutch angle", "pov",
                     "looking at viewer", "looking away", "looking back", "looking down"],
        "category": "view_angles",
        "group": "camera_angle",
    },

    # Backgrounds
    "backgrounds": {
        "keywords": ["background", "outdoors", "indoors", "sky", "clouds", "grass",
                     "forest", "beach", "ocean", "city", "street", "room", "bedroom",
                     "bathroom", "kitchen", "school", "classroom", "office", "park",
                     "garden", "night", "sunset", "sunrise", "rain", "snow"],
        "category": "backgrounds",
        "group": "setting",
    },
}


# ──────────────────────────────────────────────────────────────────────────────
# CLASSIFICATION ENGINE
# ──────────────────────────────────────────────────────────────────────────────

class TagClassifier:
    """Classifies tags using action-verb priority, then object-based fallback."""

    def __init__(self):
        # Pre-compile regex patterns for action verbs
        self.action_verb_pattern = re.compile(
            r'\b(' + '|'.join(re.escape(v) for v in sorted(ACTION_VERBS, key=len, reverse=True)) + r')\b',
            re.IGNORECASE
        )

        # Build keyword lookup for fallback classification
        self._build_keyword_index()

    def _build_keyword_index(self) -> None:
        """Build inverted index from keywords to categories."""
        self.keyword_to_category: Dict[str, Tuple[str, str]] = {}
        for pattern_name, pattern_data in KEYWORD_PATTERNS.items():
            category = pattern_data["category"]
            group = pattern_data["group"]
            for keyword in pattern_data["keywords"]:
                self.keyword_to_category[keyword.lower()] = (category, group)

    def classify(self, tag: str) -> Dict:
        """
        Classify a tag. Returns dict with category, group, uses_hands, confidence.

        Priority:
        1. Action verb detected → gesture category
        2. Object keywords → corresponding category
        3. Unknown → returns None for category
        """
        tag_lower = tag.lower().strip()

        # Step 1: Check for action verbs (HIGHEST PRIORITY)
        action_match = self.action_verb_pattern.search(tag_lower)
        if action_match:
            verb = action_match.group(1).lower()
            gesture_group = ACTION_VERB_GROUPS.get(verb, "gesture_general")
            return {
                "category": "gesture",
                "group": gesture_group,
                "uses_hands": True,
                "confidence": 0.95,
                "classification_reason": f"action_verb:{verb}",
            }

        # Step 2: Fallback to object-based classification
        for keyword, (category, group) in self.keyword_to_category.items():
            if keyword in tag_lower:
                # Check if it's a compound tag that might still be a gesture
                # e.g., "hand on breast" has no action verb but is still a gesture
                if self._is_likely_gesture(tag_lower):
                    return {
                        "category": "gesture",
                        "group": "gesture_body_touch",
                        "uses_hands": True,
                        "confidence": 0.75,
                        "classification_reason": f"implied_gesture:{keyword}",
                    }

                return {
                    "category": category,
                    "group": group,
                    "uses_hands": False,
                    "confidence": 0.80,
                    "classification_reason": f"keyword:{keyword}",
                }

        # Step 3: Unknown category
        return {
            "category": None,
            "group": None,
            "uses_hands": False,
            "confidence": 0.0,
            "classification_reason": "unknown",
        }

    def _is_likely_gesture(self, tag: str) -> bool:
        """Check if tag implies a gesture even without explicit action verb."""
        gesture_patterns = [
            r'hand[s]?\s+on\s+',       # "hand on breast", "hands on hips"
            r'finger[s]?\s+on\s+',     # "finger on lips"
            r'arm[s]?\s+around\s+',    # "arms around waist"
            r'own\s+',                  # "own breast", "own clothes" (implies self-touching)
        ]
        for pattern in gesture_patterns:
            if re.search(pattern, tag, re.IGNORECASE):
                return True
        return False


# ──────────────────────────────────────────────────────────────────────────────
# CATALOG GENERATOR
# ──────────────────────────────────────────────────────────────────────────────

class CatalogGenerator:
    """Generates expanded catalog JSON files from classified tags."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.prompt_data_dir = project_root / "prompt data"
        self.all_tags_path = project_root / "All tags" / "Cleaned_all_tags.csv"
        self.classifier = TagClassifier()

        # Statistics
        self.stats = defaultdict(int)
        self.category_counts = defaultdict(int)
        self.group_counts = defaultdict(int)

    def load_tags(self) -> List[Tuple[str, str]]:
        """Load tags from CSV. Returns list of (english_tag, chinese_tag)."""
        tags = []
        with open(self.all_tags_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            for row in reader:
                if len(row) >= 2:
                    tags.append((row[0].strip(), row[1].strip()))
        return tags

    def generate_item(self, tag_en: str, tag_zh: str) -> Dict:
        """Generate a catalog item from a tag pair."""
        classification = self.classifier.classify(tag_en)

        # Generate ID from English tag
        item_id = re.sub(r'[^a-z0-9]+', '_', tag_en.lower()).strip('_')

        return {
            "id": item_id,
            "name": tag_en,
            "category": classification["category"],
            "group": classification["group"],
            "aliases": [],
            "uses_hands": classification["uses_hands"],
            "name_i18n": {
                "en": tag_en,
                "zh": tag_zh,
            },
            "auto_generated": True,
            "confidence": classification["confidence"],
            "classification_reason": classification["classification_reason"],
        }

    def generate_catalogs(self, dry_run: bool = False, min_frequency: int = 1) -> Dict[str, List[Dict]]:
        """Generate all expanded catalogs. Returns dict of catalog_name -> items."""
        tags = self.load_tags()
        print(f"Loaded {len(tags)} tags from {self.all_tags_path}")

        # Group items by target catalog
        catalogs: Dict[str, List[Dict]] = defaultdict(list)
        seen_ids: Dict[str, Set[str]] = defaultdict(set)

        for tag_en, tag_zh in tags:
            self.stats["total"] += 1

            item = self.generate_item(tag_en, tag_zh)
            category = item["category"]

            if category is None:
                self.stats["skipped_unknown"] += 1
                continue

            # Determine target catalog
            target_catalog = self._get_target_catalog(category)
            if target_catalog is None:
                self.stats["skipped_no_catalog"] += 1
                continue

            # Deduplicate by ID within each catalog
            if item["id"] in seen_ids[target_catalog]:
                self.stats["skipped_duplicate"] += 1
                continue

            seen_ids[target_catalog].add(item["id"])
            catalogs[target_catalog].append(item)
            self.stats["added"] += 1
            self.category_counts[category] += 1
            if item["group"]:
                self.group_counts[item["group"]] += 1

        # Sort items within each catalog
        for catalog_name in catalogs:
            catalogs[catalog_name].sort(key=lambda x: x["name"])

        return dict(catalogs)

    def _get_target_catalog(self, category: str) -> Optional[str]:
        """Map category to target catalog name."""
        mapping = {
            "gesture": "poses",
            "poses": "poses",
            "hair": "hair",
            "eyes": "eyes",
            "body": "body",
            "expressions": "expressions",
            "clothing": "clothing",
            "view_angles": "view_angles",
            "backgrounds": "backgrounds",
        }
        return mapping.get(category)

    def write_catalog(self, catalog_name: str, items: List[Dict], dry_run: bool = False) -> Path:
        """Write expanded catalog to JSON file."""
        # Determine output path
        catalog_dir = self.prompt_data_dir / catalog_name
        if catalog_name == "poses":
            output_path = catalog_dir / "poses_expanded.json"
        elif catalog_name == "clothing":
            output_path = catalog_dir / "clothing_expanded.json"
        elif catalog_name == "hair":
            output_path = catalog_dir / "hair_expanded.json"
        elif catalog_name == "eyes":
            output_path = catalog_dir / "eyes_expanded.json"
        elif catalog_name == "body":
            output_path = catalog_dir / "body_expanded.json"
        elif catalog_name == "expressions":
            output_path = catalog_dir / "expressions_expanded.json"
        elif catalog_name == "view_angles":
            output_path = catalog_dir / "view_angles_expanded.json"
        elif catalog_name == "backgrounds":
            output_path = catalog_dir / "backgrounds_expanded.json"
        else:
            output_path = catalog_dir / f"{catalog_name}_expanded.json"

        # Build index by category
        index_by_category: Dict[str, List[str]] = defaultdict(list)
        for item in items:
            cat = item.get("category") or "uncategorized"
            index_by_category[cat].append(item["id"])

        # Build index by group
        index_by_group: Dict[str, List[str]] = defaultdict(list)
        for item in items:
            group = item.get("group")
            if group:
                index_by_group[group].append(item["id"])

        # Build catalog structure
        catalog_data = {
            "schema_version": "1.0",
            "mode": "expanded",
            "source": "Cleaned_all_tags.csv",
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "total_items": len(items),
            "items": items,
            "index_by_category": dict(index_by_category),
            "index_by_group": dict(index_by_group),
            "group_i18n": self._get_group_i18n(),
            "supported_languages": ["en", "zh"],
        }

        if dry_run:
            print(f"  [DRY RUN] Would write {len(items)} items to {output_path}")
        else:
            catalog_dir.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(catalog_data, f, indent=2, ensure_ascii=False)
            print(f"  Wrote {len(items)} items to {output_path}")

        return output_path

    def _get_group_i18n(self) -> Dict:
        """Return i18n labels for gesture groups."""
        return {
            "gesture_body_touch": {"en": "Body Touch Actions", "zh": "身体触碰动作"},
            "gesture_clothing_adjust": {"en": "Clothing Adjustments", "zh": "衣物调整动作"},
            "gesture_object_interaction": {"en": "Object Interactions", "zh": "物品互动"},
            "gesture_general": {"en": "General Gestures", "zh": "通用手势"},
            "hair_style": {"en": "Hair Styles", "zh": "发型"},
            "eye_attributes": {"en": "Eye Attributes", "zh": "眼部特征"},
            "body_features": {"en": "Body Features", "zh": "身体特征"},
            "emotion": {"en": "Emotions", "zh": "情绪表情"},
            "upper_body": {"en": "Upper Body Clothing", "zh": "上身服装"},
            "lower_body": {"en": "Lower Body Clothing", "zh": "下身服装"},
            "full_body": {"en": "Full Body Outfits", "zh": "全身服装"},
            "head": {"en": "Head Accessories", "zh": "头部配饰"},
            "feet": {"en": "Footwear", "zh": "鞋袜"},
            "pose_position": {"en": "Body Positions", "zh": "身体姿态"},
            "camera_angle": {"en": "Camera Angles", "zh": "镜头角度"},
            "setting": {"en": "Settings/Backgrounds", "zh": "场景背景"},
        }

    def print_stats(self) -> None:
        """Print classification statistics."""
        print("\n" + "=" * 60)
        print("CLASSIFICATION STATISTICS")
        print("=" * 60)
        print(f"  Total tags processed: {self.stats['total']}")
        print(f"  Tags added to catalogs: {self.stats['added']}")
        print(f"  Skipped (unknown category): {self.stats['skipped_unknown']}")
        print(f"  Skipped (no target catalog): {self.stats['skipped_no_catalog']}")
        print(f"  Skipped (duplicate ID): {self.stats['skipped_duplicate']}")

        print("\nBy Category:")
        for category, count in sorted(self.category_counts.items(), key=lambda x: -x[1]):
            print(f"  {category}: {count}")

        print("\nBy Group (top 20):")
        for group, count in sorted(self.group_counts.items(), key=lambda x: -x[1])[:20]:
            print(f"  {group}: {count}")


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate expanded catalog files from Cleaned_all_tags.csv"
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Preview categorization without writing files"
    )
    parser.add_argument(
        "--min-frequency", "-f",
        type=int,
        default=1,
        help="Minimum tag frequency to include (default: 1)"
    )
    parser.add_argument(
        "--sample", "-s",
        type=int,
        default=0,
        help="Only process first N tags (for testing)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print detailed classification for each tag"
    )
    args = parser.parse_args()

    # Find project root
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    print(f"Project root: {project_root}")
    print(f"Dry run: {args.dry_run}")
    print(f"Min frequency: {args.min_frequency}")

    # Generate catalogs
    generator = CatalogGenerator(project_root)
    catalogs = generator.generate_catalogs(
        dry_run=args.dry_run,
        min_frequency=args.min_frequency,
    )

    # Write output files
    print("\n" + "=" * 60)
    print("WRITING EXPANDED CATALOGS")
    print("=" * 60)
    for catalog_name, items in catalogs.items():
        generator.write_catalog(catalog_name, items, dry_run=args.dry_run)

    # Print stats
    generator.print_stats()

    print("\nDone!")
    if args.dry_run:
        print("(This was a dry run - no files were modified)")


if __name__ == "__main__":
    main()
