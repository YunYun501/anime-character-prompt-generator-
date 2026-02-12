"""One-time script to expand catalogs with fewer than 20 items."""
import json

# ===== 1. HAIR CATALOG =====
with open("prompt data/hair/hair_catalog.json", "r", encoding="utf-8") as f:
    hair = json.load(f)

new_hair = [
    {"id": "hip_length_hair", "name": "hip-length hair", "category": "length", "aliases": []},
    {"id": "knee_length_hair", "name": "knee-length hair", "category": "length", "aliases": []},
    {"id": "floor_length_hair", "name": "floor-length hair", "category": "length", "aliases": []},
    {"id": "chin_length_hair", "name": "chin-length hair", "category": "length", "aliases": []},
    {"id": "ear_length_hair", "name": "ear-length hair", "category": "length", "aliases": []},
    {"id": "chest_length_hair", "name": "chest-length hair", "category": "length", "aliases": []},
    {"id": "asymmetrical_length_hair", "name": "asymmetrical length hair", "category": "length", "aliases": []},
    {"id": "bob_length_hair", "name": "bob-length hair", "category": "length", "aliases": []},
    {"id": "ankle_length_hair", "name": "ankle-length hair", "category": "length", "aliases": []},
    {"id": "glossy_hair", "name": "glossy hair", "category": "texture", "aliases": []},
    {"id": "wispy_hair", "name": "wispy hair", "category": "texture", "aliases": []},
    {"id": "feathered_hair", "name": "feathered hair", "category": "texture", "aliases": []},
    {"id": "tousled_hair", "name": "tousled hair", "category": "texture", "aliases": []},
    {"id": "slicked_back_hair", "name": "slicked-back hair", "category": "texture", "aliases": []},
    {"id": "damp_hair", "name": "damp hair", "category": "texture", "aliases": []},
    {"id": "frizzy_hair", "name": "frizzy hair", "category": "texture", "aliases": []},
    {"id": "flowing_hair", "name": "flowing hair", "category": "texture", "aliases": []},
    {"id": "tangled_hair", "name": "tangled hair", "category": "texture", "aliases": []},
]

existing_ids = {item["id"] for item in hair["items"]}
added = 0
for item in new_hair:
    if item["id"] not in existing_ids:
        hair["items"].append(item)
        hair["index_by_category"][item["category"]].append(item["id"])
        added += 1

with open("prompt data/hair/hair_catalog.json", "w", encoding="utf-8") as f:
    json.dump(hair, f, indent=2, ensure_ascii=False)
print(f"Hair: added {added} items")

# ===== 2. BODY FEATURES =====
with open("prompt data/body/body_features.json", "r", encoding="utf-8") as f:
    body = json.load(f)

new_body = [
    {"id": "wide_hips", "name": "wide hips", "category": "body_type", "aliases": []},
    {"id": "thick_thighs", "name": "thick thighs", "category": "body_type", "aliases": []},
    {"id": "narrow_waist", "name": "narrow waist", "category": "body_type", "aliases": []},
    {"id": "long_legs", "name": "long legs", "category": "body_type", "aliases": []},
    {"id": "abs", "name": "abs", "category": "body_type", "aliases": ["toned abs"]},
    {"id": "skinny", "name": "skinny", "category": "body_type", "aliases": []},
    {"id": "voluptuous", "name": "voluptuous", "category": "body_type", "aliases": []},
    {"id": "flat_chest", "name": "flat chest", "category": "body_type", "aliases": []},
    {"id": "broad_shoulders", "name": "broad shoulders", "category": "body_type", "aliases": []},
    {"id": "willowy", "name": "willowy", "category": "body_type", "aliases": []},
    {"id": "stocky", "name": "stocky", "category": "body_type", "aliases": []},
    {"id": "lanky", "name": "lanky", "category": "body_type", "aliases": []},
    {"id": "soft_body", "name": "soft body", "category": "body_type", "aliases": []},
    {"id": "towering", "name": "towering", "category": "height", "aliases": []},
    {"id": "statuesque", "name": "statuesque", "category": "height", "aliases": []},
    {"id": "compact", "name": "compact", "category": "height", "aliases": []},
    {"id": "diminutive", "name": "diminutive", "category": "height", "aliases": []},
    {"id": "medium_height", "name": "medium height", "category": "height", "aliases": []},
    {"id": "model_height", "name": "model height", "category": "height", "aliases": []},
    {"id": "imposing_height", "name": "imposing height", "category": "height", "aliases": []},
    {"id": "caramel_skin", "name": "caramel skin", "category": "skin", "aliases": []},
    {"id": "ivory_skin", "name": "ivory skin", "category": "skin", "aliases": []},
    {"id": "rosy_skin", "name": "rosy skin", "category": "skin", "aliases": []},
    {"id": "mole_under_eye", "name": "mole under eye", "category": "skin", "aliases": []},
    {"id": "beauty_mark", "name": "beauty mark", "category": "skin", "aliases": []},
    {"id": "body_freckles", "name": "body freckles", "category": "skin", "aliases": []},
    {"id": "tan_lines", "name": "tan lines", "category": "skin", "aliases": []},
    {"id": "smooth_skin", "name": "smooth skin", "category": "skin", "aliases": []},
    {"id": "shiny_skin", "name": "shiny skin", "category": "skin", "aliases": []},
    {"id": "dimples", "name": "dimples", "category": "skin", "aliases": []},
    {"id": "collarbone", "name": "collarbone", "category": "skin", "aliases": []},
    {"id": "middle_aged", "name": "middle-aged", "category": "age_appearance", "aliases": []},
    {"id": "elderly", "name": "elderly", "category": "age_appearance", "aliases": []},
    {"id": "ojou_sama", "name": "ojou-sama", "category": "age_appearance", "aliases": []},
    {"id": "onee_san", "name": "onee-san", "category": "age_appearance", "aliases": []},
    {"id": "baby_face", "name": "baby face", "category": "age_appearance", "aliases": []},
    {"id": "child", "name": "child", "category": "age_appearance", "aliases": []},
]

existing_ids = {item["id"] for item in body["items"]}
added = 0
for item in new_body:
    if item["id"] not in existing_ids:
        body["items"].append(item)
        body["index_by_category"][item["category"]].append(item["id"])
        added += 1

with open("prompt data/body/body_features.json", "w", encoding="utf-8") as f:
    json.dump(body, f, indent=2, ensure_ascii=False)
print(f"Body: added {added} items")

# ===== 3. CLOTHING =====
with open("prompt data/clothing/clothing_list.json", "r", encoding="utf-8") as f:
    clothing = json.load(f)

new_clothing = [
    # head (20 new)
    {"id": "crown", "name": "crown", "body_part": "head", "aliases": []},
    {"id": "hair_ribbon", "name": "hair ribbon", "body_part": "head", "aliases": []},
    {"id": "headband", "name": "headband", "body_part": "head", "aliases": []},
    {"id": "hair_flower", "name": "hair flower", "body_part": "head", "aliases": []},
    {"id": "mini_top_hat", "name": "mini top hat", "body_part": "head", "aliases": []},
    {"id": "sun_hat", "name": "sun hat", "body_part": "head", "aliases": []},
    {"id": "mob_cap", "name": "mob cap", "body_part": "head", "aliases": []},
    {"id": "bonnet", "name": "bonnet", "body_part": "head", "aliases": []},
    {"id": "helmet", "name": "helmet", "body_part": "head", "aliases": []},
    {"id": "baseball_cap", "name": "baseball cap", "body_part": "head", "aliases": []},
    {"id": "bucket_hat", "name": "bucket hat", "body_part": "head", "aliases": []},
    {"id": "cowboy_hat", "name": "cowboy hat", "body_part": "head", "aliases": []},
    {"id": "military_hat", "name": "military hat", "body_part": "head", "aliases": []},
    {"id": "sailor_hat", "name": "sailor hat", "body_part": "head", "aliases": []},
    {"id": "rice_hat", "name": "rice hat", "body_part": "head", "aliases": ["kasa"]},
    {"id": "nightcap", "name": "nightcap", "body_part": "head", "aliases": []},
    {"id": "veil", "name": "veil", "body_part": "head", "aliases": []},
    {"id": "lace_headband", "name": "lace headband", "body_part": "head", "aliases": []},
    {"id": "flower_crown", "name": "flower crown", "body_part": "head", "aliases": []},
    {"id": "hair_pins", "name": "hair pins", "body_part": "head", "aliases": ["kanzashi"]},
    # neck (15 new)
    {"id": "necklace", "name": "necklace", "body_part": "neck", "aliases": []},
    {"id": "pendant", "name": "pendant", "body_part": "neck", "aliases": []},
    {"id": "collar", "name": "collar", "body_part": "neck", "aliases": []},
    {"id": "pearl_necklace", "name": "pearl necklace", "body_part": "neck", "aliases": []},
    {"id": "chain_necklace", "name": "chain necklace", "body_part": "neck", "aliases": []},
    {"id": "neck_bell", "name": "neck bell", "body_part": "neck", "aliases": ["bell collar"]},
    {"id": "feather_boa", "name": "feather boa", "body_part": "neck", "aliases": []},
    {"id": "ascot", "name": "ascot", "body_part": "neck", "aliases": []},
    {"id": "neckerchief", "name": "neckerchief", "body_part": "neck", "aliases": []},
    {"id": "locket", "name": "locket", "body_part": "neck", "aliases": []},
    {"id": "dog_collar", "name": "dog collar", "body_part": "neck", "aliases": []},
    {"id": "spiked_collar", "name": "spiked collar", "body_part": "neck", "aliases": []},
    {"id": "flower_necklace", "name": "flower necklace", "body_part": "neck", "aliases": ["lei"]},
    {"id": "goggles_around_neck", "name": "goggles around neck", "body_part": "neck", "aliases": []},
    {"id": "headphones_around_neck", "name": "headphones around neck", "body_part": "neck", "aliases": []},
    # waist (14 new)
    {"id": "obi", "name": "obi", "body_part": "waist", "aliases": []},
    {"id": "waist_sash", "name": "waist sash", "body_part": "waist", "aliases": []},
    {"id": "garter_belt", "name": "garter belt", "body_part": "waist", "aliases": []},
    {"id": "suspenders", "name": "suspenders", "body_part": "waist", "aliases": []},
    {"id": "fanny_pack", "name": "fanny pack", "body_part": "waist", "aliases": ["waist bag"]},
    {"id": "chain_belt", "name": "chain belt", "body_part": "waist", "aliases": []},
    {"id": "corset_belt", "name": "corset belt", "body_part": "waist", "aliases": ["waist cincher"]},
    {"id": "rope_belt", "name": "rope belt", "body_part": "waist", "aliases": []},
    {"id": "ribbon_belt", "name": "ribbon belt", "body_part": "waist", "aliases": []},
    {"id": "sash", "name": "sash", "body_part": "waist", "aliases": []},
    {"id": "hip_chain", "name": "hip chain", "body_part": "waist", "aliases": ["belly chain"]},
    {"id": "waist_pouch", "name": "waist pouch", "body_part": "waist", "aliases": []},
    {"id": "waist_cape", "name": "waist cape", "body_part": "waist", "aliases": []},
    {"id": "ammunition_belt", "name": "ammunition belt", "body_part": "waist", "aliases": ["ammo belt"]},
    # outerwear (15 new)
    {"id": "trench_coat", "name": "trench coat", "body_part": "outerwear", "aliases": []},
    {"id": "poncho", "name": "poncho", "body_part": "outerwear", "aliases": []},
    {"id": "cloak", "name": "cloak", "body_part": "outerwear", "aliases": []},
    {"id": "denim_jacket", "name": "denim jacket", "body_part": "outerwear", "aliases": []},
    {"id": "bomber_jacket", "name": "bomber jacket", "body_part": "outerwear", "aliases": []},
    {"id": "fur_coat", "name": "fur coat", "body_part": "outerwear", "aliases": []},
    {"id": "haori", "name": "haori", "body_part": "outerwear", "aliases": []},
    {"id": "bolero", "name": "bolero", "body_part": "outerwear", "aliases": []},
    {"id": "duster_coat", "name": "duster coat", "body_part": "outerwear", "aliases": []},
    {"id": "overcoat", "name": "overcoat", "body_part": "outerwear", "aliases": []},
    {"id": "shawl", "name": "shawl", "body_part": "outerwear", "aliases": []},
    {"id": "fur_trimmed_coat", "name": "fur-trimmed coat", "body_part": "outerwear", "aliases": []},
    {"id": "military_jacket", "name": "military jacket", "body_part": "outerwear", "aliases": []},
    {"id": "cropped_jacket", "name": "cropped jacket", "body_part": "outerwear", "aliases": []},
    {"id": "hoodie_jacket", "name": "hoodie jacket", "body_part": "outerwear", "aliases": []},
    # hands (15 new)
    {"id": "elbow_gloves", "name": "elbow gloves", "body_part": "hands", "aliases": []},
    {"id": "opera_gloves", "name": "opera gloves", "body_part": "hands", "aliases": []},
    {"id": "leather_gloves", "name": "leather gloves", "body_part": "hands", "aliases": []},
    {"id": "paw_gloves", "name": "paw gloves", "body_part": "hands", "aliases": []},
    {"id": "arm_warmers", "name": "arm warmers", "body_part": "hands", "aliases": []},
    {"id": "gauntlets", "name": "gauntlets", "body_part": "hands", "aliases": []},
    {"id": "half_gloves", "name": "half gloves", "body_part": "hands", "aliases": []},
    {"id": "fur_trimmed_gloves", "name": "fur-trimmed gloves", "body_part": "hands", "aliases": []},
    {"id": "frilled_gloves", "name": "frilled gloves", "body_part": "hands", "aliases": []},
    {"id": "latex_gloves", "name": "latex gloves", "body_part": "hands", "aliases": []},
    {"id": "single_glove", "name": "single glove", "body_part": "hands", "aliases": []},
    {"id": "detached_sleeves", "name": "detached sleeves", "body_part": "hands", "aliases": []},
    {"id": "bridal_gauntlets", "name": "bridal gauntlets", "body_part": "hands", "aliases": []},
    {"id": "wristband", "name": "wristband", "body_part": "hands", "aliases": []},
    {"id": "bracelet", "name": "bracelet", "body_part": "hands", "aliases": []},
    # legs (11 new)
    {"id": "pantyhose", "name": "pantyhose", "body_part": "legs", "aliases": []},
    {"id": "striped_thigh_highs", "name": "striped thigh-highs", "body_part": "legs", "aliases": []},
    {"id": "leg_warmers", "name": "leg warmers", "body_part": "legs", "aliases": []},
    {"id": "torn_stockings", "name": "torn stockings", "body_part": "legs", "aliases": []},
    {"id": "lace_stockings", "name": "lace stockings", "body_part": "legs", "aliases": []},
    {"id": "striped_stockings", "name": "striped stockings", "body_part": "legs", "aliases": []},
    {"id": "loose_socks", "name": "loose socks", "body_part": "legs", "aliases": []},
    {"id": "tabi_socks", "name": "tabi socks", "body_part": "legs", "aliases": ["tabi"]},
    {"id": "garter_straps", "name": "garter straps", "body_part": "legs", "aliases": []},
    {"id": "bandaged_leg", "name": "bandaged leg", "body_part": "legs", "aliases": []},
    {"id": "over_knee_socks", "name": "over-knee socks", "body_part": "legs", "aliases": []},
    # feet (12 new)
    {"id": "ankle_boots", "name": "ankle boots", "body_part": "feet", "aliases": []},
    {"id": "knee_high_boots", "name": "knee-high boots", "body_part": "feet", "aliases": []},
    {"id": "thigh_high_boots", "name": "thigh-high boots", "body_part": "feet", "aliases": []},
    {"id": "mary_janes", "name": "mary janes", "body_part": "feet", "aliases": []},
    {"id": "ballet_flats", "name": "ballet flats", "body_part": "feet", "aliases": []},
    {"id": "slippers", "name": "slippers", "body_part": "feet", "aliases": []},
    {"id": "pumps", "name": "pumps", "body_part": "feet", "aliases": []},
    {"id": "combat_boots", "name": "combat boots", "body_part": "feet", "aliases": []},
    {"id": "wedge_heels", "name": "wedge heels", "body_part": "feet", "aliases": ["wedges"]},
    {"id": "lace_up_boots", "name": "lace-up boots", "body_part": "feet", "aliases": []},
    {"id": "flip_flops", "name": "flip flops", "body_part": "feet", "aliases": []},
    {"id": "high_heels", "name": "high heels", "body_part": "feet", "aliases": []},
]

existing_ids = {item["id"] for item in clothing["items"]}
added = 0
for item in new_clothing:
    if item["id"] not in existing_ids:
        clothing["items"].append(item)
        bp = item["body_part"]
        if bp not in clothing["index_by_body_part"]:
            clothing["index_by_body_part"][bp] = []
        clothing["index_by_body_part"][bp].append(item["id"])
        added += 1

with open("prompt data/clothing/clothing_list.json", "w", encoding="utf-8") as f:
    json.dump(clothing, f, indent=2, ensure_ascii=False)
print(f"Clothing: added {added} items")
