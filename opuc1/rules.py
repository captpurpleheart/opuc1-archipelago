"""Logic helpers. Region names match regions in __init__.py."""
from typing import Callable, Dict, List, Tuple

from BaseClasses import CollectionState

from .data import (CHARACTERS, CHAR_INDEX, CREATURES, FISH, ROOM_ITEM, ROOM_OPTIONS, line_items_needed,
                   rod_items_needed)

P1, P2, P2R, SUNNY = "Wooded Isle Part 1", "Wooded Isle Part 2", "Wooded Isle Part 2 (Right)", "Thousand Sunny"
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
    if mode == 0:
        return room == "workshop"
    return ((mode == 2 or s.has(ROOM_ITEM[room], p))
            and (mode == 1 or s.has(CHARACTERS[ci], p)))


def net(s: CollectionState, p: int) -> bool:
    """Catching bugs needs the repaired net: the Broken net repaired at the Workshop with a Spider Web."""
    return s.has("Broken Bug-Catcher Net", p) and room_open(s, p, "workshop") and s.can_reach_region(SUNNY, p)


def pickaxe(s, p): return s.has("Pickaxe", p)
def vacuum(s, p): return s.has("Progressive Vacuum Cleaner", p)
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
def gabri(n): return lambda s, p: s.has("Progressive Gabri Level", p, n)
def always(s, p): return True


def _all(*rules: Rule) -> Rule:
    return lambda s, p: all(r(s, p) for r in rules)


# Where each natural ingredient can be found: list of (region, extra rule). Player's notes, 2026-10-17.
SOURCES: Dict[str, List[Tuple[str, Rule]]] = {
    "Bitter Grass": [(P1, always), (P2, always), (P2R, always)],
    "Medicinal Herbs": [(P1, always), (P2, always), (P2R, always)],
    "Nectar": [(P1, always), (P2, always), (P2R, always)],
    "Bamboo": [(P1, sharp), (P2, sharp)],
    "Bamboo Sprout": [(P1, sharp), (P2, sharp)],
    "Coconut": [(P1, always)],
    "Flour": [(P1, always)],
    "Mystery Egg": [(P1, always), (P2, always)],
    "Long Vine": [(P2, sharp)],
    "Rubber Fruit": [(P2, always)],
    "Toxin": [(P2, vacuum), (P2R, vacuum)],
    "Dial Fragment": [(P1, pickaxe), (P2, always)],
    "Handy Rock": [(P1, pickaxe), (P2, pickaxe)],
    "Pure Iron Ore": [(P1, pickaxe), (P2, pickaxe)],
    "Gourmet Mushroom": [(P1, pickaxe), (P2, pickaxe)],
    "Royal Jelly": [(P1, net), (P2, net)],
    "Blue Fruit": [(P2, always)],
    "Marble": [(P1, pickaxe), (P2, pickaxe)],
    "Clay": [(P1, pickaxe), (P2, pickaxe)],
    "Iron Scrap": [(P1, always)],          # Marine drops
    # Gunpowder: Marine Gunners don't appear on Island 1 (user, 2026-10-19), so recipes needing it
    # have no locations for now (see craft_in_scope)
    "Magnetic Stone": [(P2R, always)],     # enemy drops
    "Spider Web": [(SUNNY, always)],
    "Lens": [(P2, always)],                # eyeball plant drop
    # creatures (repaired net)
    "Swallowtail Butterfly": [(P1, net), (P2, net), (SUNNY, net)],
    "Invisible Swallowtail": [(P1, net), (P2, net)],
    "Honey Bee": [(P1, net), (P2, net)],
    "Tree Frog": [(P2, net)],
    # fish (line = how far the lure must land; opuc-fishing.md)
    # Part 1 spot next to the Sunny: no Brook needed (user correction, 2026-10-19)
    "Striped Clam": [(P1, rod)],
    "Smiley Jellyfish": [(P1, rod)],
    "Shining Saury": [(P1, _all(rod, line(1))), (SUNNY, _all(rod, line(1)))],
    "Forked-Tail Killifish": [(P2, rod)],
    "Fist Crayfish": [(P2, rod)],
    "Balloon Catfish": [(P2, rod)],
    "Shark": [(SUNNY, _all(rod, line(5)))],
    # Sea Kings (Sunny-side spot only). Rod grade: Sea King rod assumed for landing them (to confirm).
    "Large Sea King": [(SUNNY, _all(rod, line(8), rod_level(22)))],
    "Extra-Large Sea King": [(SUNNY, _all(rod, line(16), rod_level(22)))],
    "Giant Turtle Sea King": [(SUNNY, _all(rod, line(19), rod_level(22)))],
    "Seagull": [(SUNNY, net)],             # user: on the Sunny at any time with the net
    # Tempest Mouse: on the Sunny with Traps, but needs Island 2 (user) - out of scope
}


# Fish / creatures that can be caught in this world's scope (the others have no locations yet)
FISH_IN_SCOPE: List[str] = [n for n in FISH.values() if n in SOURCES]
CREATURES_IN_SCOPE: List[str] = [n for n in CREATURES.values() if n in SOURCES]


def opt(s: CollectionState, p: int, name: str) -> int:
    return getattr(s.multiworld.worlds[p].options, name).value


def build_site(n: int) -> Rule:
    """Build Site n's Access item, plus Franky with franky_required_for_build_sites."""
    item = f"Wooded Isle Building Site {n} Access"
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


def craft_in_scope(room: str, row: int) -> bool:
    """Every natural ingredient of the recipe can be found in this world's scope."""
    return all(m in SOURCES for m in RECIPE_NEEDS[(room, row)][0])


def has_material(name: str) -> Rule:
    sources = SOURCES[name]
    return lambda s, p: any(s.can_reach_region(r, p) and extra(s, p) for r, extra in sources)


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
    ("workshop", 23): (("Shark", "Magnetic Stone"), ()),
    ("workshop", 27): (("Pure Iron Ore",), ()),
    ("kitchen", 7): (("Forked-Tail Killifish", "Bamboo"), ()),
    ("kitchen", 12): (("Fist Crayfish", "Bitter Grass"), ()),
    ("pharmacy", 0): (("Medicinal Herbs", "Bitter Grass"), ()),
    ("pharmacy", 8): (("Medicinal Herbs", "Bitter Grass", "Royal Jelly"), ()),   # Healing Capsule + Royal Jelly
    ("pharmacy", 26): (("Toxin", "Handy Rock"), ()),
}
