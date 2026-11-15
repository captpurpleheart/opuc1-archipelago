"""Logic helpers. Region names match regions in __init__.py."""
from typing import Callable, Dict, List, Tuple

from BaseClasses import CollectionState

from .data import (CHARACTERS, CHAR_INDEX, CRAFTS, CREATURES, EXTRA_POOLS, FISH, FRANKY_TRADES, GABRI_COLOUR_ITEMS,
                   MATERIALS, ROOM_ITEM, ROOM_OPTIONS, gabri_start_bars, gabri_bars_per_item, line_items_needed, rod_items_needed)
from .tables import SHRINE_COSTS

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
POST_MORIA = "Post-Gecko Moria"
CENTRAL = "Central Isle"
# Iceberg Isle (Island 3), user's region map 2026-10-28
I1, I2, I3, I4, I5, I6 = (f"Iceberg Isle Part {n}" for n in range(1, 7))
ILADDER, IBOSS, POST_AOKIJI = "Iceberg Isle Optional Ladder Route", "Iceberg Isle Island Boss", "Post-Aokiji"
# Cave Isle (Island 4), user's notes 2026-11-06
C1, C2, CPOISON, CWATER = "Cave Isle Part 1", "Cave Isle Part 2", "Cave Isle Poison Route", "Cave Isle Water Route"
CMID, CBOSS, CSECRET = "Cave Isle Mid Boss Room", "Cave Isle Island Boss", "Cave Isle Secret Boss Room"
POST_BLACKBEARD = "Post-Blackbeard"
# Obstructed Paths (Mole + 50 Bombs build sites; 0.27.0)
WHIDDEN = "Wooded Isle Hidden Beach"
GHIDDEN, GSECRET = "Gorge Isle Hidden Area", "Gorge Isle Secret Boss Area"
IOBST1, IOBST2 = "Iceberg Isle Obstructed Path", "Iceberg Isle Obstructed Path (2)"
# Every island is in every seed (0.21.0); the region after the goal boss is left out (goal option -> region)
POST_GOAL = {0: POST_ENERU, 1: POST_MORIA, 3: POST_AOKIJI, 4: POST_BLACKBEARD}
GORGE_LOG_POSE = "Gorge Isle, The Cliff Ruins"
ICEBERG_LOG_POSE = "Iceberg Isle, Unexplored Ice Region"
CAVE_LOG_POSE = "Cave Isle, The Underwater Passage"
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
    o = s.multiworld.worlds[p].options
    mode = getattr(o, unlock_opt).value
    if room == "franky":   # Franky's Supplies (0.30.0): 0 start_with, 1 item, 2 Franky, 3 both
        return bool(o.franky_supplies.value) and (mode == 0 or (
            (mode == 2 or s.has(ROOM_ITEM[room], p)) and (mode == 1 or s.has(CHARACTERS[ci], p))))
    if mode == 4:     # start_with (Kitchen / Pharmacy; the Workshop's start_with is 0)
        return True
    if mode == 0:     # Workshop: start_with; Kitchen / Pharmacy: vanilla, from chapter 3 (after Eneru)
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


def gunpowder_drop(s: CollectionState, p: int) -> bool:
    """Gunpowder from the gunners (and Bombs from the Cave Isle soldiers, 0.27.0) counts (Enemy Gunpowder Drop Logic:
    none / included / whirlwind = Nami + Whirlwind)."""
    o = s.multiworld.worlds[p].options
    mode = o.enemy_gunpowder_drop_logic.value
    return mode == 1 or (mode == 2 and s.has_all(("Nami", "Nami - Whirlwind"), p))


def gunpowder_logic(s: CollectionState, p: int) -> bool:
    return bool(s.multiworld.worlds[p].options.include_gunpowder_logic.value)


def explosive(s: CollectionState, p: int) -> bool:
    """Gunpowder or Bombs (same function in game; user, 0.27.0), dropped or crafted."""
    return has_material("Gunpowder")(s, p) or has_material("Bombs")(s, p)


def blast_path(s: CollectionState, p: int) -> bool:
    """Gunpowder / Bombs (dropped or crafted) on rock paths: they power up moves, and every Straw Hat can do it (Usopp
    with his starting Death Blow Lead Star; user, 2026-11-02)."""
    return gunpowder_logic(s, p) and explosive(s, p)


def blast_x(s: CollectionState, p: int) -> bool:
    """Gunpowder on X dig spots: any Straw Hat but Usopp, whose shots fly over them unless he has Usopp Pound."""
    from .data import CHARACTERS as _C
    users = [c for c in _C if c != "Usopp"]
    return (gunpowder_logic(s, p) and explosive(s, p)
            and (s.has_any(users, p) or s.has_all(("Usopp", "Usopp - Usopp Pound"), p)))


def rock_path(s: CollectionState, p: int) -> bool:
    """Rock / ice rock paths: the Pickaxe or Gunpowder."""
    return pickaxe(s, p) or blast_path(s, p)


def fire_attack(s: CollectionState, p: int) -> bool:
    """Fire attacks melt Ice Rocks (but give no Ice Shards): Sanji's Diable Jambe or Zoro's Single Sword Flying Dragon
    Blaze (user, 2026-11-03), or Flame Powder / Flamethrowers (Fire Hercules on the Cave Isle; user, 0.27.0)."""
    return (s.has_all(("Sanji", "Sanji - Diable Jambe"), p)
            or s.has_all(("Zoro", "Zoro - Single Sword Flying Dragon Blaze"), p)
            or has_material("Flame Powder")(s, p) or craftable("workshop", 25)(s, p))


def fire_craft(s: CollectionState, p: int) -> bool:
    """A fire attack that doesn't rely on dropped Flame Powder: the fire moves, or Flame Powder / Flamethrowers that
    can be crafted (Chopper's Pharmacy / Usopp's Workshop)."""
    return (s.has_all(("Sanji", "Sanji - Diable Jambe"), p)
            or s.has_all(("Zoro", "Zoro - Single Sword Flying Dragon Blaze"), p)
            or craftable("pharmacy", 31)(s, p) or craftable("workshop", 25)(s, p))


def ice_path(s: CollectionState, p: int) -> bool:
    """Iceberg Isle Ice Rock paths (to Parts 2, 4 and 5): the Pickaxe, Gunpowder or a fire attack."""
    return rock_path(s, p) or fire_attack(s, p)


def dig_or_blast(s: CollectionState, p: int) -> bool:
    """X dig spots (Clay, Marble, Pure Iron Ore): the Pickaxe, or Gunpowder (not the random plain-ground digs or the
    treasure map chests, which stay Pickaxe only)."""
    return pickaxe(s, p) or blast_x(s, p)
def always(s, p): return True


# Gabri: max Energy bars per level (Red, Green, Blue, White, Black, Gold; opuc-shrines.md). A shrine's level is the
# first level whose bars cover its whole cost.
GABRI_BARS = [(0, 0, 3, 0, 0, 0), (0, 3, 4, 0, 0, 0), (0, 4, 5, 0, 0, 1), (5, 5, 6, 0, 0, 1), (6, 6, 7, 0, 0, 2),
              (7, 7, 8, 5, 0, 3), (8, 8, 9, 6, 0, 4), (9, 9, 10, 8, 5, 5), (10, 10, 10, 9, 10, 6),
              (10, 10, 10, 9, 10, 7), (10, 10, 10, 9, 10, 8), (10, 10, 10, 9, 10, 9), (10, 10, 10, 9, 10, 10),
              (10, 10, 10, 10, 10, 10)]


def gabri_level(red=0, green=0, blue=0, white=0, black=0, gold=0) -> int:
    """Lowest Gabri level for a cost given in bars (100 Energy = 1 bar)."""
    need = (red, green, blue, white, black, gold)
    return next(lv for lv, bars in enumerate(GABRI_BARS) if all(n <= b for n, b in zip(need, bars)))


def shrine_bars(sid: int) -> Tuple[int, ...]:
    """A shrine's Energy cost in bars (Red, Green, Blue, White, Black, Gold), from event/epoint (tables.SHRINE_COSTS)."""
    return tuple(-(-c // 100) for c in SHRINE_COSTS[sid][:6])


def energy(sid: int) -> Rule:
    """Enough Gabri Energy for shrine / build site sid: Progressive Gabri Level items (the level whose bars cover the
    cost), or with gabri_energy_items: per_colour, enough of each colour's Progressive Energy Level item (0.28.0)."""
    bars = shrine_bars(sid)
    level = gabri_level(*bars)

    def r(s: CollectionState, p: int) -> bool:
        if opt(s, p, "gabri_energy_items"):
            step = gabri_bars_per_item(opt(s, p, "gabri_level_items"))
            start_bars = gabri_start_bars(opt(s, p, "starting_gabri_energy"))
            return all(need <= start or s.has(item, p, -(-(need - start) // step))
                       for need, start, item in zip(bars, start_bars, GABRI_COLOUR_ITEMS))
        return gabri(level)(s, p)
    return r


def obstructed(site: Rule, sid: int) -> Rule:
    """An Obstructed Path build site: its access item (+ Franky), its Energy, 1 Mole and 50 Bombs (0.27.0). The 50 Bombs
    only count when they can be crafted (Usopp's Workshop); 35-50 Bombs from Knuckle Soldier drops is too much
    farming (user, 0.33.2)."""
    return lambda s, p: (site(s, p) and energy(sid)(s, p) and has_material("Mole")(s, p)
                         and ingredient("Bombs")(s, p))




# Where each natural ingredient can be found: list of (region, extra rule). Player's notes, 2026-10-17.
SOURCES: Dict[str, List[Tuple[str, Rule]]] = {
    # Wooded Isle: player's notes 2026-10-17. Gorge Isle: user's sheet 2026-10-22 (enemy drops need no tool;
    # creature drops need the net).
    # Iceberg Isle: user's sheet 2026-10-28
    # Cave Isle: user's sheet 2026-11-06 (Part 1 / Part 2 tables)
    "Bitter Grass": [(P1, always), (P2, always), (P2R, always), (G1, always), (I1, always), (C1, always)],
    "Medicinal Herbs": [(P1, always), (P2, always), (P2R, always), (G1, always), (I1, always), (C1, always)],
    "Nectar": [(P1, always), (P2, always), (P2R, always), (G1, always), (I1, always), (C1, always)],
    # burning the plants above with a fire attack (user, 0.27.0). As an ingredient (random recipes) only the fire moves
    # and craftable Flame Powder / Flamethrowers count; Flame Powder dropped by Fire Hercules only counts for the
    # "Got Ashes" location (FIRST_PICKUP; user, 0.33.2).
    "Ashes": [(P1, fire_craft), (P2, fire_craft), (G1, fire_craft), (I1, fire_craft), (C1, fire_craft)],
    "Hardtack Ration": [(P1, always), (C1, always)],           # Cave Isle: Nishiki Agent drop
    "Mysterious Seaweed": [(C1, always), (C2, net)],          # Lantern Trilobite drop (net)
    "Volcanic Rock": [(C2, dig_or_blast)],                     # X dig spots
    "Bombs": [(C2, gunpowder_drop)],                           # Knuckle Soldier drop (drop logic option; also crafted)
    "Mole": [(C2, net)],
    "Lantern Trilobite": [(C2, net)],
    "Fire Hercules": [(C2, net), (C1, lambda s, p: has_material("Traps")(s, p))],   # Part 1 with Traps (user)
    "Light Bulb Firefly": [(C1, net)],
    "Flame Powder": [(C2, net)],                               # Fire Hercules drop (also compounded)
    "Bamboo": [(P1, sharp), (P2, sharp), (G1, sharp)],
    "Bamboo Sprout": [(P1, sharp), (P2, sharp), (G1, sharp)],
    "Coconut": [(P1, always)],
    "Flour": [(P1, always), (GPOISON, always)],          # barrels (fishing junk is unused content, user 0.30.0)
    "Mystery Egg": [(P1, always), (P2, always), (G1, always)],
    "Long Vine": [(P2, sharp), (I2, sharp)],
    "Rubber Fruit": [(P2, always), (G1, always), (I4, always)],
    "Toxin": [(P2, vacuum), (P2R, vacuum), (G2, vacuum), (C2, vacuum)],
    "Dial Fragment": [(P1, pickaxe), (P2, always), (ILADDER, always), (WHIDDEN, always)],   # Enforcer drops
    "Handy Rock": [(P1, pickaxe), (P2, pickaxe), (G1, pickaxe), (C2, always)],   # Cave: Mass Soldiers drop
    "Pure Iron Ore": [(IRON_SPOT, dig_or_blast), (C2, net)],   # Mole drop (40%, net)
    "Gourmet Mushroom": [(P1, pickaxe), (P2, pickaxe), (C1, always)],    # Cave Isle Part 1: no tool (user)
    # Gorge: Doctor Hornet drop; the hornets only drop it when caught with the net (user, 2026-10-23)
    "Royal Jelly": [(P2, net), (G1, net)],      # not Wooded Isle Part 1 (user, 2026-10-28: Honey Bees are Part 2)
    "Blue Fruit": [(P2R, always)],         # rock path right of Part 2 (user, 0.28.0)
    # X dig spots: Pickaxe or Gunpowder (0.24.0, user)
    "Marble": [(P1, dig_or_blast), (P2, dig_or_blast), (G3, dig_or_blast)],
    "Clay": [(P1, dig_or_blast), (P2, dig_or_blast), (G1, dig_or_blast)],
    "Iron Scrap": [(P1, always), (I4, always), (C2, always)],          # Marine / Sword Soldier drops
    # Gunpowder: Marine Gunners aren't on Island 1 (user, 2026-10-19); they are in Gorge Isle Part 3.
    # Chopper can also compound it (CRAFTED).
    # Gunpowder Drop Gating decides whether these count (0.24.0)
    "Gunpowder": [(G3, gunpowder_drop), (I1, gunpowder_drop), (C1, gunpowder_drop)],   # Pirate / Agent Gunners
    "Magnetic Stone": [(P2R, always), (WHIDDEN, always)],     # enemy drops (Hidden Beach: Robots)
    "Spider Web": [(SUNNY, always)],
    "Lens": [(P2, always)],                # eyeball plant drop
    "Mystery Mushroom": [(G1, always), (C1, always)],    # Zombie drop; Cave Isle Part 1 (user)
    "Mysterious Bone": [(G1, always)],     # Skull Idol drop
    "Sticky Sap": [(G1, net)],             # Hercules Beetle drop (net needed, user 2026-10-23)
    "Red Fruit": [(G1, always)],
    "Wilted Carrot": [(G1, always)],       # Zombie Squirrel drop
    # Gorge Isle Part 1's dead trees are a one-time group (Shrine 1 patch, docs/gorge_layout.md): the first trees
    # that come back are in Part 3, by the build site to Part 4 (user, 1.0.2). "Got Wood" still counts Part 1.
    "Wood": [(G3, always), (C2, always)],
    "Golden Egg": [(G2, pickaxe), (I1, net)],      # Iceberg: Flying Penguin drop (net)
    "Explosive Rock Fragment": [(G4, always), (C2, always)],
    "Brown Fruit": [(GPOISON, always), (GHIDDEN, always)],
    "Healing Capsule": [(I1, always), (C1, always)],     # Blue Pirate drop (also compounded)
    "Stamina Capsule": [(I1, always), (C1, always)],     # Red Pirate drop (also compounded)
    "Golden Fruit": [(I1, always)],
    "Ice Shard": [(I1, pickaxe)],
    "Snow Radish": [(I1, pickaxe)],
    "Ice Powder": [(I1, net)],             # Icicle Lizard drop (also compounded)
    "Scrap from a Cloak": [(I3, always)],  # Marine Commander drop
    "Frozen Meat": [(ILADDER, pickaxe)],
    # creatures (repaired net)
    "Swallowtail Butterfly": [(P1, net), (P2, net), (SUNNY, net)],
    "Invisible Swallowtail": [(P1, net), (P2, net)],
    "Honey Bee": [(P2, net)],              # not in Part 1 (user, 2026-10-27)
    "Tree Frog": [(P2, net)],
    "Seagull": [(SUNNY, net)],             # user: on the Sunny at any time with the net
    # Wooded Isle Part 2 outside the boss room after Eneru (net), or with Traps in Part 2 before him (user, 2026-11-03)
    "Lightning Beetle": [(POST_ENERU, net), (P2, lambda s, p: has_material("Traps")(s, p))],
    "Rock Lizard": [(G1, net)],
    "Hercules Beetle": [(G1, net)],
    "Doctor Hornet": [(G1, net)],
    "Golden Hercules": [(G1, net)],
    "Icicle Lizard": [(I1, net)],
    "Flying Penguin": [(I1, net)],
    "Sleep Butterfly": [(I1, net)],
    "Ice Beetle": [(I5, net)],
    "Mammoth Toad": [(ILADDER, net)],
    "Tempest Mouse": [(SUNNY, lambda s, p: has_material("Traps")(s, p)),    # Traps on the Sunny (user)
                      (IOBST2, net)],                                         # Iceberg Obstructed Path 2
    # fish (line = how far the lure must land; opuc-fishing.md)
    # Part 1 spot next to the Sunny: no Brook needed (user correction, 2026-10-19)
    "Striped Clam": [(P1, rod), (GPOISON, rod), (WHIDDEN, rod)],
    "Smiley Jellyfish": [(P1, rod), (I1, rod)],
    "Shining Saury": [(P1, _all(rod, cast(1))), (SUNNY, _all(rod, cast(1))), (WHIDDEN, _all(rod, cast(1)))],
    "Forked-Tail Killifish": [(P2, rod), (GLADDER, rod)],
    "Fist Crayfish": [(P2, rod), (GLADDER, rod)],
    "Balloon Catfish": [(P2, _all(rod, rod_level(5)))],   # not landable at rod level 1 (user)
    "Salamandrake": [(GLADDER, _all(rod, cast(5)))],      # bites at 30-45 m
    "Oriental Butterflyfish": [(GPOISON, rod), (CPOISON, rod)],
    "Clawed Shrimp": [(GPOISON, rod), (CPOISON, rod)],
    # Cave Isle spot 14995 (Poison Route): Starfish from 15 m (line level 0 reaches 19 m)
    "Superstar Starfish": [(CPOISON, rod)],
    # Panda Shark: treated like the Shark, Whopper Fishing Rod (user, 0.27.0)
    "Panda Shark": [(CPOISON, _all(rod, rod_level(11)))],
    # Hidden Beach spot 11997 (Wooded Isle west), 30 m+
    "Treasure Shell": [(WHIDDEN, _all(rod, cast(5)))],
    "Adventure Fish": [(GPOISON, rod), (I1, rod)],
    "Ice Sunfish": [(I1, _all(rod, cast(5)))],            # 30 m+ (Iceberg spot 13995, Part 1)
    # 40 m+; user (0.24.0): rod level 5 and line 11 to land it
    "Elephant Tuna": [(I1, _all(rod, rod_level(5), line(11)))],
    "Skull Knight": [(GPOISON, _all(rod, cast(5)))],      # 30 m+
    # Sharks break free from the standard rod: Whopper Fishing Rod (rod level 11) needed (user, 0.24.0)
    "Shark": [(SUNNY, _all(rod, line(5), rod_level(11))), (WHIDDEN, _all(rod, line(5), rod_level(11)))],
    # Sea Kings (Sunny-side spot only). Rod grade: Sea King rod assumed for landing them (to confirm).
    "Large Sea King": [(SUNNY, _all(rod, line(8), rod_level(22)))],
    "Extra-Large Sea King": [(SUNNY, _all(rod, line(16), rod_level(22)))],
    "Giant Turtle Sea King": [(SUNNY, _all(rod, line(19), rod_level(22)))],
    # Landing a Sea King also gives its bonus item (item/fish_prm.bin +0x04; user 2026-10-28: in logic)
    "Sea King Fin": [(SUNNY, _all(rod, line(8), rod_level(22)))],          # Large Sea King
    "Sea King Head Crest": [(SUNNY, _all(rod, line(16), rod_level(22)))],  # Extra-Large Sea King
    "Sea King Shell": [(SUNNY, _all(rod, line(19), rod_level(22)))],       # Giant Turtle Sea King
    # Old Gold Coins (only with franky_supplies, 0.30.0): from the Flour / Hardtack Ration barrels (Wooded Isle Part 1,
    # Gorge Isle Poison Path) and the Golden Hercules (1-5, net). Filler coins aren't counted.
    "Old Gold Coin": [(P1, always), (GPOISON, always), (G1, net)],
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
    "Thunder Powder": ("pharmacy", 15), "Anti-Cold Cream": ("pharmacy", 17), "Ice Powder": ("pharmacy", 23), "Flame Powder": ("pharmacy", 31),
    "Traps": ("workshop", 5), "Batteries": ("workshop", 17), "Bombs": ("workshop", 21),
    "Special Pirate Soda": ("kitchen", 18),
    # Cave Isle Shrine 2 offerings (0.27.0)
    "Mock Cherry Pie": ("kitchen", 10), "Dual-Action Tonic": ("pharmacy", 13),
}
# 0.30.0: every other crafted item a random recipe can ask for (Extra Crafting Recipes / Franky's Supplies pools)
_POOL_NAMES = {n for pool in EXTRA_POOLS.values() for n, _r, _a in pool}
for _room, _row, _res, _dummy in CRAFTS:
    if not _dummy and _res in _POOL_NAMES and _res not in CRAFTED:
        CRAFTED[_res] = (_room, _row)


# Sources whose extra rule needs a crafted item (so scope checks can follow it)
SOURCE_NEEDS: Dict[str, Tuple[str, ...]] = {"Tempest Mouse": ("Traps",)}
MATERIALS_IN_SCOPE: List[str] = [n for n in MATERIALS.values() if n in SOURCES]


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


def franky_trade(row: int) -> Rule:
    """A fixed Franky's Supplies trade (0.30.0) can be made: the option on, the menu open, Art of Supplying and the
    ingredients (Old Gold Coins, Special Pirate Soda)."""
    mats = tuple(n for n, _c in FRANKY_TRADES[row][1])
    return lambda s, p: bool(opt(s, p, "franky_supplies")) and recipe("franky", row, mats)(s, p)


def craftable(room: str, row: int) -> Rule:
    """The recipe can be made: room open, its Art level (and the Art's owner if that option is on), AP key items,
    and every ingredient found or crafted."""
    mats, keys = RECIPE_NEEDS[(room, row)]
    return recipe(room, row, mats, keys)


def recipe(room: str, row: int, mats, keys=()) -> Rule:
    """A recipe with these ingredients (natural or crafted) and AP key items: room open, its Art level (row // 8) and
    the Art's owner if that option is on. Also used for the random recipes (0.30.0)."""
    from .data import ROOM_ART
    mats, keys = tuple(mats), tuple(keys)
    art = row // 8
    _u, art_opt, ci = ROOM_OPTIONS[room]

    def r(s: CollectionState, p: int) -> bool:
        if not room_open(s, p, room) or not s.has_all(keys, p):
            return False
        if art and (not s.has(ROOM_ART[room], p, art) or (opt(s, p, art_opt) and not s.has(CHARACTERS[ci], p))):
            return False
        return all(ingredient(m)(s, p) for m in mats)
    return r


# Ingredients that only count when they can be crafted when a lot of them is asked for (Bombs: 10-50; dropped ones
# are too much farming; user, 0.33.2 / 0.33.3)
CRAFT_ONLY = {"Bombs"}


def ingredient(name: str) -> Rule:
    """An ingredient asked for in bulk (recipes, Obstructed Paths, Cave Isle Shrine 1)."""
    if name in CRAFT_ONLY:
        return craftable(*CRAFTED[name])
    return has_material(name)


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


# Franky's fixed trades are another source of their result (0.30.0; the Mole trade too since 0.30.1: user-tested, a
# crafted Mole works and doesn't count as caught)
for _row, (_res, _ing) in FRANKY_TRADES.items():
    SOURCES[_res].append((SUNNY, franky_trade(_row)))


# Materialsanity only (0.30.3, user): one-time pickups that don't count as a repeatable source for recipes. Pure Iron Ore
# dig spots (shiny, Pickaxe) in Wooded Isle Parts 1 and 2 (user's AP info sheet).
FIRST_PICKUP: Dict[str, List[Tuple[str, Rule]]] = {
    "Pure Iron Ore": [(P1, pickaxe), (P2, pickaxe)],
    # any fire attack, including Flame Powder dropped by Fire Hercules (0.33.2)
    "Ashes": [(P1, fire_attack), (P2, fire_attack), (G1, fire_attack), (I1, fire_attack), (C1, fire_attack)],
    "Wood": [(G1, always)],     # Gorge Isle Part 1's one-time dead trees (1.0.2)
}


def got_material(name: str) -> Rule:
    """A "Got <material>" location: any source, one-time pickups included."""
    once = FIRST_PICKUP.get(name, [])
    more = has_material(name)
    return lambda s, p: any(s.can_reach_region(reg, p) and extra(s, p) for reg, extra in once) or more(s, p)
