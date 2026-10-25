"""Logic helpers. Region names match regions in __init__.py."""
from typing import Callable, Dict, List, Tuple

from BaseClasses import CollectionState

from .data import (CHARACTERS, CHAR_INDEX, CREATURES, FISH, ROOM_ITEM, ROOM_OPTIONS, line_items_needed,
                   rod_items_needed)

P1, P2, P2R, SUNNY = "Wooded Isle Part 1", "Wooded Isle Part 2", "Wooded Isle Part 2 (Right)", "Thousand Sunny"
# The story chapter is 2 + the LATEST island boss beaten (0x800FF220 checks 14351, 13355, 12351, then 11351), so
# beating Gecko Moria before Eneru also opens what Eneru opens (Kitchen / Pharmacy rooms, user 2026-10-24).
SUNNY_CH3 = "Thousand Sunny (After an Island Boss)"
# The repeatable dig spot by the Sunny (Blue Orb in vanilla; Pure Iron Ore with blue_orb_spot_gives_iron_ore),
# reached by running on the water with Brook. The other Pure Iron Ore dig spots are one-time only and too few for
# the recipes (user, 2026-10-25), so this is Pure Iron Ore's only logical source for now (Island 4 Moles later).
IRON_SPOT = "Wooded Isle Part 1 (Sunny Dig Spot)"
POST_ENERU = "Post-Eneru"                 # anything after the Island 1 boss (incl. Wooded Isle Part 2 outside his room)
G1, G2, G3, G4 = "Gorge Isle Part 1", "Gorge Isle Part 2", "Gorge Isle Part 3", "Gorge Isle Part 4"
GBRIDGE, GLADDER, GPOISON = ("Gorge Isle Optional Bridge Path", "Gorge Isle Optional Ladder Path",
                             "Gorge Isle Optional Poison Path")
GBOSS = "Gorge Isle Island Boss"
# Regions that only exist when Gorge Isle (Island 2) is in the seed
ISLAND_2_REGIONS = {POST_ENERU, SUNNY_CH3, G1, G2, G3, G4, GBRIDGE, GLADDER, GPOISON, GBOSS}
POST_MORIA = "Post-Gecko Moria"
CENTRAL = "Central Isle"
# Regions that only exist when the final island is in the seed (goal central_isle)
ISLAND_5_REGIONS = {POST_MORIA, CENTRAL}
GORGE_LOG_POSE = "Gorge Isle, the Ruined Path"
CENTRAL_LOG_POSE = "Central Isle, New Beginnings"
Rule = Callable[[CollectionState, int], bool]


def char(name: str) -> Rule:
    item = CHARACTERS[CHAR_INDEX[name]]
    return lambda s, p: s.has(item, p)


def sharp(s: CollectionState, p: int) -> bool:
    """Can cut bamboo and vines."""
    return (s.has_any(("Roronoa Zoro", "Brook", "Pickaxe"), p)
            or s.has_all(("Usopp", "Usopp - Caltrop Hell"), p)
            or s.has_all(("Nico Robin", "Robin - Uno Fleur Cast"), p)
            or (s.has("Franky", p) and s.has_any(("Franky - Master Nail", "Franky - Triangle Jacker"), p)))


def room_open(s: CollectionState, p: int, room: str) -> bool:
    """A Sunny room can be used (Thousand Sunny options; kitchen / pharmacy "vanilla" = after the goal)."""
    unlock_opt, _art_opt, ci = ROOM_OPTIONS[room]
    mode = getattr(s.multiworld.worlds[p].options, unlock_opt).value
    if mode == 0:     # vanilla: Workshop open; Kitchen / Pharmacy from chapter 3 (after Eneru)
        return room == "workshop" or s.can_reach_region(SUNNY_CH3, p)
    return ((mode == 2 or s.has(ROOM_ITEM[room], p))
            and (mode == 1 or s.has(CHARACTERS[ci], p)))


def net(s: CollectionState, p: int) -> bool:
    """Catching bugs needs the repaired net: the Broken net repaired at the Workshop with a Spider Web."""
    return s.has("Broken Bug-Catcher Net", p) and room_open(s, p, "workshop") and s.can_reach_region(SUNNY, p)


def pickaxe(s, p): return s.has("Pickaxe", p)
def vacuum(s, p): return s.has("Progressive Vacuum Cleaner", p)
def power_vacuum(s, p): return s.has("Progressive Vacuum Cleaner", p, 2)
def rod(s, p): return s.has("Fishing Rod", p)
def line(n):
    """Lure must land at least line level n away (copies needed depend on the rod_upgrade_items option)."""
    def r(s: CollectionState, p: int) -> bool:
        o = s.multiworld.worlds[p].options
        item = "Progressive Fishing Rod Level" if o.combine_rod_and_line.value else "Progressive Fishing Rod Line"
        return s.has(item, p, line_items_needed(o.rod_upgrade_items.value, n))
    return r
def rod_level(n):
    """Rod level n (22 = Sea King grade) in Rod Level items (copies needed depend on rod_upgrade_items)."""
    return lambda s, p: s.has("Progressive Fishing Rod Level", p,
                              rod_items_needed(s.multiworld.worlds[p].options.rod_upgrade_items.value, n))
def _all(*rules: Rule) -> Rule:
    return lambda s, p: all(r(s, p) for r in rules)


def cast(n):
    """Line level n to reach the fish, and (until tested more) rod level n to land it (user, 2026-10-22)."""
    return _all(line(n), rod_level(n))
def gabri(n): return lambda s, p: s.has("Progressive Gabri Level", p, n)
def always(s, p): return True




# Where each natural ingredient can be found: list of (region, extra rule). Player's notes, 2026-10-17.
SOURCES: Dict[str, List[Tuple[str, Rule]]] = {
    # Wooded Isle: player's notes 2026-10-17. Gorge Isle: user's sheet 2026-10-22 (enemy drops need no tool;
    # creature drops need the net).
    "Bitter Grass": [(P1, always), (P2, always), (P2R, always), (G1, always)],
    "Medicinal Herbs": [(P1, always), (P2, always), (P2R, always), (G1, always)],
    "Nectar": [(P1, always), (P2, always), (P2R, always), (G1, always)],
    "Bamboo": [(P1, sharp), (P2, sharp), (G1, sharp)],
    "Bamboo Sprout": [(P1, sharp), (P2, sharp), (G1, sharp)],
    "Coconut": [(P1, always)],
    "Flour": [(P1, always), (GPOISON, always)],
    "Mystery Egg": [(P1, always), (P2, always), (G1, always)],
    "Long Vine": [(P2, sharp)],
    "Rubber Fruit": [(P2, always), (G1, always)],
    "Toxin": [(P2, vacuum), (P2R, vacuum), (G2, vacuum)],
    "Dial Fragment": [(P1, pickaxe), (P2, always)],
    "Handy Rock": [(P1, pickaxe), (P2, pickaxe), (G1, pickaxe)],
    "Pure Iron Ore": [(IRON_SPOT, pickaxe)],
    "Gourmet Mushroom": [(P1, pickaxe), (P2, pickaxe)],
    # Gorge: Doctor Hornet drop; the hornets only drop it when caught with the net (user, 2026-10-23)
    "Royal Jelly": [(P1, net), (P2, net), (G1, net)],
    "Blue Fruit": [(P2, always)],
    "Marble": [(P1, pickaxe), (P2, pickaxe), (G3, pickaxe)],
    "Clay": [(P1, pickaxe), (P2, pickaxe), (G1, pickaxe)],
    "Iron Scrap": [(P1, always)],          # Marine drops
    # Gunpowder: Marine Gunners aren't on Island 1 (user, 2026-10-19); they are in Gorge Isle Part 3.
    # Chopper can also compound it (CRAFTED).
    "Gunpowder": [(G3, always)],
    "Magnetic Stone": [(P2R, always)],     # enemy drops
    "Spider Web": [(SUNNY, always)],
    "Lens": [(P2, always)],                # eyeball plant drop
    "Mystery Mushroom": [(G1, always)],    # Zombie drop
    "Mysterious Bone": [(G1, always)],     # Skull Idol drop
    "Sticky Sap": [(G1, net)],             # Hercules Beetle drop (net needed, user 2026-10-23)
    "Red Fruit": [(G1, always)],
    "Wilted Carrot": [(G1, always)],       # Zombie Squirrel drop
    "Wood": [(G1, always)],
    "Golden Egg": [(G2, pickaxe)],
    "Explosive Rock Fragment": [(G4, always)],
    "Brown Fruit": [(GPOISON, always)],
    # creatures (repaired net)
    "Swallowtail Butterfly": [(P1, net), (P2, net), (SUNNY, net)],
    "Invisible Swallowtail": [(P1, net), (P2, net)],
    "Honey Bee": [(P1, net), (P2, net)],
    "Tree Frog": [(P2, net)],
    "Seagull": [(SUNNY, net)],             # user: on the Sunny at any time with the net
    "Lightning Beetle": [(POST_ENERU, net)],   # Wooded Isle Part 2 outside the boss room, after Eneru
    "Rock Lizard": [(G1, net)],
    "Hercules Beetle": [(G1, net)],
    "Doctor Hornet": [(G1, net)],
    "Golden Hercules": [(G1, net)],
    "Tempest Mouse": [(SUNNY, lambda s, p: has_material("Traps")(s, p))],   # Traps on the Sunny (user)
    # fish (line = how far the lure must land; opuc-fishing.md)
    # Part 1 spot next to the Sunny: no Brook needed (user correction, 2026-10-19)
    "Striped Clam": [(P1, rod), (GPOISON, rod)],
    "Smiley Jellyfish": [(P1, rod)],
    "Shining Saury": [(P1, _all(rod, cast(1))), (SUNNY, _all(rod, cast(1)))],
    "Forked-Tail Killifish": [(P2, rod), (GLADDER, rod)],
    "Fist Crayfish": [(P2, rod), (GLADDER, rod)],
    "Balloon Catfish": [(P2, _all(rod, rod_level(5)))],   # not landable at rod level 1 (user)
    "Salamandrake": [(GLADDER, _all(rod, cast(5)))],      # bites at 30-45 m
    "Oriental Butterflyfish": [(GPOISON, rod)],
    "Clawed Shrimp": [(GPOISON, rod)],
    "Adventure Fish": [(GPOISON, rod)],
    "Skull Knight": [(GPOISON, _all(rod, cast(5)))],      # 30 m+
    "Shark": [(SUNNY, _all(rod, cast(5)))],
    # Sea Kings (Sunny-side spot only). Rod grade: Sea King rod assumed for landing them (to confirm).
    "Large Sea King": [(SUNNY, _all(rod, line(8), rod_level(22)))],
    "Extra-Large Sea King": [(SUNNY, _all(rod, line(16), rod_level(22)))],
    "Giant Turtle Sea King": [(SUNNY, _all(rod, line(19), rod_level(22)))],
}


# Fish / creatures that can be caught in this world's scope (the others have no locations yet)
FISH_IN_SCOPE: List[str] = [n for n in FISH.values() if n in SOURCES]
CREATURES_IN_SCOPE: List[str] = [n for n in CREATURES.values() if n in SOURCES]


def opt(s: CollectionState, p: int, name: str) -> int:
    return getattr(s.multiworld.worlds[p].options, name).value


def build_site(n, island: str = "Wooded Isle") -> Rule:
    """Build Site n's Access item, plus Franky with franky_required_for_build_sites."""
    item = f"Wooded Isle Building Site {n} Access" if island == "Wooded Isle" else f"{island} Build Site {n} Access"
    return lambda s, p: s.has(item, p) and (not opt(s, p, "franky_required_for_build_sites") or s.has("Franky", p))


def monument(s: CollectionState, p: int) -> bool:
    return not opt(s, p, "robin_required_for_monuments") or s.has("Nico Robin", p)


def map_fragment(names) -> Rule:
    """Any of these fragments (every one with treasure_maps_need_every_fragment: the client holds them until the
    map is complete), plus Nami with nami_required_for_maps (fragments wait for her)."""
    def r(s: CollectionState, p: int) -> bool:
        have = s.has_all(names, p) if opt(s, p, "treasure_maps_need_every_fragment") else s.has_any(names, p)
        return have and (not opt(s, p, "nami_required_for_maps") or s.has("Nami", p))
    return r


SEA_KINGS = ("Large Sea King", "Extra-Large Sea King", "Giant Turtle Sea King")
SEA_KING_MATERIALS = SEA_KINGS + ("Sea King Fin", "Sea King Head Crest", "Sea King Shell")


def needs_sea_king(room: str, row: int) -> bool:
    return any(m in SEA_KING_MATERIALS for m in RECIPE_NEEDS[(room, row)][0])


# Ingredients that are crafted themselves: (room, row) of their recipe
CRAFTED: Dict[str, Tuple[str, int]] = {
    "Healing Capsule": ("pharmacy", 0), "Stamina Capsule": ("pharmacy", 2), "Dual-Action Capsule": ("pharmacy", 5),
    "Gunpowder": ("pharmacy", 7), "Stamina Tonic": ("pharmacy", 10), "Syrup": ("pharmacy", 12),
    "Thunder Powder": ("pharmacy", 15), "Ice Powder": ("pharmacy", 23), "Flame Powder": ("pharmacy", 31),
    "Traps": ("workshop", 5), "Batteries": ("workshop", 17), "Bombs": ("workshop", 21),
    "Special Pirate Soda": ("kitchen", 18),
}


# Sources whose extra rule needs a crafted item (so scope checks can follow it)
SOURCE_NEEDS: Dict[str, Tuple[str, ...]] = {"Tempest Mouse": ("Traps",)}


def material_in_scope(name: str, regions, seen=()) -> bool:
    """Can this ingredient be found (or crafted from such ingredients) in these regions?"""
    if any(r in regions for r, _ in SOURCES.get(name, [])) and \
            all(material_in_scope(n, regions, seen) for n in SOURCE_NEEDS.get(name, ())):
        return True
    rec = CRAFTED.get(name)
    return bool(rec) and rec not in seen and craft_in_scope(*rec, regions=regions, seen=seen + (rec,))


def craft_in_scope(room: str, row: int, regions=None, seen=()) -> bool:
    """Every ingredient of the recipe can be found (or crafted) in the seed's regions (default: everything)."""
    if (room, row) not in RECIPE_NEEDS:
        return False
    if regions is None:
        regions = {r for srcs in SOURCES.values() for r, _ in srcs}
    return all(material_in_scope(m, regions, seen + ((room, row),)) for m in RECIPE_NEEDS[(room, row)][0])


def craftable(room: str, row: int) -> Rule:
    """The recipe can be made: room open, its Art level (and the Art's owner if that option is on), AP key items,
    and every ingredient found or crafted."""
    from .data import ROOM_ART
    mats, keys = RECIPE_NEEDS[(room, row)]
    art = row // 8
    _u, art_opt, ci = ROOM_OPTIONS[room]

    def r(s: CollectionState, p: int) -> bool:
        if not room_open(s, p, room) or not s.has_all(keys, p):
            return False
        if art and (not s.has(ROOM_ART[room], p, art) or (opt(s, p, art_opt) and not s.has(CHARACTERS[ci], p))):
            return False
        return all(has_material(m)(s, p) for m in mats)
    return r


def has_material(name: str) -> Rule:
    sources = SOURCES.get(name, [])
    rec = CRAFTED.get(name)

    def r(s: CollectionState, p: int) -> bool:
        if any(s.can_reach_region(reg, p) and extra(s, p) for reg, extra in sources):
            return True
        return bool(rec) and rec in RECIPE_NEEDS and craftable(*rec)(s, p)
    return r


# Crafting: natural ingredients and AP key items per recipe (room, row)
RECIPE_NEEDS: Dict[Tuple[str, int], Tuple[Tuple[str, ...], Tuple[str, ...]]] = {
    ("workshop", 1): (("Spider Web",), ("Broken Bug-Catcher Net",)),
    ("workshop", 2): (("Bamboo Sprout", "Bamboo", "Long Vine"), ()),
    ("workshop", 3): (("Magnetic Stone", "Lens", "Iron Scrap"), ()),
    ("workshop", 4): (("Rubber Fruit",), ()),
    ("workshop", 6): (("Bamboo Sprout",), ()),
    ("workshop", 7): (("Long Vine",), ()),
    ("workshop", 9): ((), ("Mystery Gadget",)),
    ("workshop", 10): (("Pure Iron Ore", "Iron Scrap"), ("Enhanced Reel", "Fishing Rod")),
    ("workshop", 11): (("Bamboo", "Clay"), ()),
    ("workshop", 12): (("Dial Fragment", "Balloon Catfish"), ()),
    ("workshop", 13): (("Dial Fragment", "Gunpowder"), ()),
    ("workshop", 14): (("Pure Iron Ore", "Iron Scrap"), ()),
    ("workshop", 19): (("Striped Clam", "Clay"), ()),
    ("workshop", 20): (("Marble",), ("Steel Chain",)),
    ("workshop", 21): (("Gunpowder", "Clay"), ()),
    # 0.16.0: every other recipe (user's recipe sheets / item/*_src.en.atb). Ingredients that aren't in SOURCES
    # or CRAFTED keep the recipe out of scope for now.
    ("workshop", 5): (("Syrup", "Bamboo", "Wood"), ()),
    ("workshop", 8): (("Hercules Beetle", "Bamboo", "Rubber Fruit"), ()),
    ("workshop", 15): (("Rock Lizard", "Mysterious Bone"), ()),
    ("workshop", 17): (("Thunder Powder", "Magnetic Stone", "Iron Scrap"), ()),
    ("workshop", 24): (("Clay", "Scrap from a Cloak"), ("Mask Fragment",)),
    ("workshop", 25): (("Flame Powder", "Lens"), ()),
    ("workshop", 26): (("Special Pirate Soda",), ("Ultimate Reel",)),
    ("workshop", 28): (("Rubber Fruit", "Pure Iron Ore", "Wood"), ()),
    ("workshop", 30): (("Batteries", "Dial Fragment"), ()),
    ("kitchen", 0): (("Mystery Egg", "Red Fruit"), ()),
    ("kitchen", 2): (("Gourmet Mushroom", "Mystery Mushroom", "Bitter Grass"), ()),
    ("kitchen", 6): (("Seagull", "Wilted Carrot", "Striped Clam"), ()),
    ("kitchen", 8): (("Clawed Shrimp", "Mystery Egg", "Bitter Grass"), ()),
    ("kitchen", 10): (("Red Fruit", "Syrup", "Mystery Egg", "Flour"), ()),
    ("kitchen", 13): (("Shining Saury", "Snow Radish"), ()),
    ("kitchen", 14): (("Ice Shard", "Syrup", "Red Fruit", "Blue Fruit"), ()),
    ("kitchen", 15): (("Frozen Meat", "Mammoth Toad"), ()),
    ("kitchen", 16): (("Elephant Tuna", "Wilted Carrot"), ()),
    ("kitchen", 18): (("Brown Fruit", "Ice Shard"), ()),
    ("kitchen", 19): (("Volcanic Rock", "Tempest Mouse", "Flour"), ()),
    ("kitchen", 20): (("Shark", "Golden Fruit"), ()),
    ("kitchen", 22): (("Skull Knight", "Flour", "Brown Fruit"), ()),
    ("kitchen", 23): (("Lantern Trilobite", "Mysterious Seaweed", "Superstar Starfish"), ()),
    ("kitchen", 24): (("Ice Sunfish", "Oriental Butterflyfish", "Balloon Catfish"), ()),
    ("kitchen", 26): (("Salamandrake", "Smiley Jellyfish", "Stamina Tonic"), ()),
    ("kitchen", 28): (("Sea King Shell", "Elephant Tuna", "Treasure Shell"), ()),
    ("kitchen", 29): (("Sea King Head Crest", "Mammoth Toad", "Frozen Meat"), ()),
    ("kitchen", 30): (("Sea King Fin", "Snow Radish", "Seagull"), ()),
    ("pharmacy", 2): (("Wilted Carrot", "Nectar"), ()),
    ("pharmacy", 5): (("Mystery Mushroom", "Bitter Grass", "Nectar"), ()),
    ("pharmacy", 7): (("Explosive Rock Fragment", "Wood"), ()),
    ("pharmacy", 10): (("Stamina Capsule", "Royal Jelly"), ()),
    ("pharmacy", 12): (("Nectar", "Sticky Sap"), ()),
    ("pharmacy", 13): (("Dual-Action Capsule", "Royal Jelly"), ()),
    ("pharmacy", 14): (("Wood", "Healing Capsule", "Doctor Hornet"), ()),
    ("pharmacy", 15): (("Lightning Beetle", "Iron Scrap"), ()),
    ("pharmacy", 17): (("Icicle Lizard",), ()),
    ("pharmacy", 18): (("Doctor Hornet", "Bitter Grass"), ()),
    ("pharmacy", 23): (("Ice Beetle", "Ice Shard"), ()),
    ("pharmacy", 25): (("Salamandrake", "Invisible Swallowtail"), ()),
    ("pharmacy", 28): (("Golden Egg", "Golden Fruit", "Golden Hercules"), ()),
    ("pharmacy", 31): (("Fire Hercules", "Volcanic Rock"), ()),
    ("workshop", 23): (("Shark", "Magnetic Stone"), ()),
    ("workshop", 27): (("Pure Iron Ore",), ()),
    ("kitchen", 7): (("Forked-Tail Killifish", "Bamboo"), ()),
    ("kitchen", 12): (("Fist Crayfish", "Bitter Grass"), ()),
    ("pharmacy", 0): (("Medicinal Herbs", "Bitter Grass"), ()),
    ("pharmacy", 8): (("Medicinal Herbs", "Bitter Grass", "Royal Jelly"), ()),   # Healing Capsule + Royal Jelly
    ("pharmacy", 26): (("Toxin", "Handy Rock"), ()),
}
