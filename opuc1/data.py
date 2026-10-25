"""
One Piece Unlimited Cruise Part 1 (ROUPAF) - shared game data for the world and the client.
No Archipelago imports here, so the client and tests can load it directly.

Scope: Prologue, Thousand Sunny, Wooded Isle (Island 1) and Gorge Isle (Island 2).
Goal (option): the Island 1 boss (Eneru, flag 11351) or the Island 2 boss (Gecko Moria, flag 12351).
"""
from typing import Dict, List, NamedTuple, Optional, Tuple

GAME = "One Piece Unlimited Cruise 1"
BASE_ID = 8_620_000

CHARACTERS = ["Monkey D. Luffy", "Roronoa Zoro", "Usopp", "Sanji", "Nami", "Tony Tony Chopper",
              "Nico Robin", "Franky", "Brook"]
SHORT = ["Luffy", "Zoro", "Usopp", "Sanji", "Nami", "Chopper", "Robin", "Franky", "Brook"]
CHAR_INDEX = {n: i for i, n in enumerate(SHORT)}

# ----------------------------------------------------------------------------------------------
# Moves. Short move id = record target id - character * 512 (0-31). Ids come from the game's
# lvl_xxx.bin tables (see project doc opuc-moves.md); charged / barrage forms were confirmed by
# the user in game where the table names were wrong (zor 16, nam 22, nam 25).
# ----------------------------------------------------------------------------------------------
STARTING_MOVES = {  # moves each character has from the start (their level-ups are checks)
    "Luffy": ["Gum Punch", "Gum Gum Whip"], "Zoro": ["Single Sword Rain Blade", "Triple Sword Oni Giri"],
    "Usopp": ["Death Blow Lead Star (1)"], "Sanji": ["Flanchet", "Longe & Poitrine"],
    "Nami": ["Wind and Waves"], "Chopper": ["Darn You!"], "Robin": ["Dos Fleur Lock"],
    "Franky": ["Uppercut"], "Brook": ["Up Slash"],
}

# (character, base move shown in location names) -> short move id
MOVE_IDS: Dict[Tuple[str, str], int] = {
    ("Luffy", "Gum Punch"): 0, ("Luffy", "Gum Gum Whip"): 1, ("Luffy", "Gum Gum Battle Axe"): 8,
    ("Luffy", "Gum Gum Gatling"): 3, ("Luffy", "Gum Gum Balloon"): 4, ("Luffy", "Gum Gum Cannon"): 9,
    ("Luffy", "Gum Gum Storm"): 6,
    ("Zoro", "Single Sword Rain Blade"): 0, ("Zoro", "Triple Sword Oni Giri"): 1,
    ("Zoro", "Single Sword Lion's Song"): 10, ("Zoro", "Dual Sword Phoenix of 72 Desires"): 3,
    ("Zoro", "Single Sword Flying Dragon Blaze"): 12, ("Zoro", "Triple Sword Demon Bull"): 13,
    ("Zoro", "Triple Sword Succession 3000 Worlds"): 6, ("Zoro", "Deadly 9 Swords Ashura Ichibugin"): 7,
    ("Usopp", "Death Blow Lead Star (1)"): 0, ("Usopp", "Death Blow Lead Star (2)"): 1,
    ("Usopp", "Death Blow Lead Star (3)"): 2, ("Usopp", "Impact"): 11, ("Usopp", "Usopp Pound"): 4,
    ("Usopp", "Caltrop Hell"): 13, ("Usopp", "Pachinko Chaos"): 6,
    ("Sanji", "Flanchet"): 0, ("Sanji", "Longe & Poitrine"): 1, ("Sanji", "Collier Shoot"): 2,
    ("Sanji", "Party Table Kick Course"): 11, ("Sanji", "Premier Hachis"): 12, ("Sanji", "Concassé"): 5,
    ("Sanji", "Veau Shot"): 6,
    ("Nami", "Wind and Waves"): 8, ("Nami", "Wintry Blast"): 9, ("Nami", "Whirlwind"): 5,
    ("Nami", "Thunder Ball"): 11, ("Nami", "Turbulent Air"): 12, ("Nami", "Thunderbolt Tempo"): 6,
    ("Nami", "White Rocking Horse 1"): 13,
    ("Chopper", "Darn You!"): 0, ("Chopper", "Charge!"): 1, ("Chopper", "Smash!"): 10,
    ("Chopper", "Heavy Press"): 4, ("Chopper", "Kick Launch!"): 12, ("Chopper", "Experiment"): 6,
    ("Robin", "Dos Fleur Lock"): 0, ("Robin", "Quatro Fleur Tower"): 1, ("Robin", "Seis Fleur Branch"): 2,
    ("Robin", "Ocho Fleur Spike"): 11, ("Robin", "Uno Fleur Cast"): 4, ("Robin", "Quatro Fleur Splash"): 13,
    ("Robin", "Infinite Fleur Amaryllis"): 6, ("Robin", "Cien Fleur Big Tree"): 14,
    ("Franky", "Uppercut"): 8, ("Franky", "Strong Right"): 1, ("Franky", "Master Nail"): 3,
    ("Franky", "Weapons Left"): 4, ("Franky", "Franky Boxing"): 12, ("Franky", "Ultimate Hammer"): 7,
    ("Franky", "Heavy Nunchaku"): 13,
    ("Brook", "Up Slash"): 0, ("Brook", "Prelude Au Fer"): 1, ("Brook", "Polka Remise"): 2,
    ("Brook", "Gavotte Bond En Avant"): 3, ("Brook", "Fun Waltz"): 4, ("Brook", "Humming March"): 5,
    ("Brook", "Three Verse Arrow Notch Slice"): 6, ("Brook", "Lullaby Parry"): 7,
}

# Move level-up locations: (character, move, items needed besides the character).
# Levels 2-5 of each move are checks. Transformation supers (Gear Second, Diable Jambe, Sogeking,
# Rumble Ball) start maxed, so they have none.
MOVE_LOCATIONS: List[Tuple[str, str, Tuple[Tuple[str, int], ...]]] = [
    ("Luffy", "Gum Punch", ()), ("Luffy", "Gum Gum Whip", ()),
    ("Luffy", "Gum Gum Battle Axe", (("Luffy - Progressive Gum Gum Battle Axe", 1),)),
    ("Luffy", "Gum Gum Gatling", (("Luffy - Progressive Gum Gum Gatling", 1),)),
    ("Luffy", "Gum Gum Balloon", (("Luffy - Progressive Gum Gum Balloon", 1),)),
    ("Luffy", "Gum Gum Cannon", (("Luffy - Gum Gum Cannon", 1),)),
    ("Luffy", "Gum Gum Storm", (("Luffy - Gum Gum Storm", 1),)),
    ("Zoro", "Single Sword Rain Blade", ()), ("Zoro", "Triple Sword Oni Giri", ()),
    ("Zoro", "Single Sword Lion's Song", (("Zoro - Progressive Single Sword Lion's Song", 1),)),
    ("Zoro", "Dual Sword Phoenix of 72 Desires", (("Zoro - Dual Sword Phoenix of 72 Desires", 1),)),
    ("Zoro", "Single Sword Flying Dragon Blaze", (("Zoro - Single Sword Flying Dragon Blaze", 1),)),
    ("Zoro", "Triple Sword Demon Bull", (("Zoro - Triple Sword Demon Bull", 1),)),
    ("Zoro", "Triple Sword Succession 3000 Worlds", (("Zoro - Triple Sword Succession 3000 Worlds", 1),)),
    ("Zoro", "Deadly 9 Swords Ashura Ichibugin", (("Zoro - Deadly 9 Swords Ashura Ichibugin", 1),)),
    ("Usopp", "Death Blow Lead Star (1)", ()),
    ("Usopp", "Death Blow Lead Star (2)", (("Usopp - Progressive Death Blow Lead Star", 1),)),
    ("Usopp", "Death Blow Lead Star (3)", (("Usopp - Progressive Death Blow Lead Star", 2),)),
    ("Usopp", "Impact", (("Impact Dial", 1),)),
    ("Usopp", "Usopp Pound", (("Usopp - Usopp Pound", 1),)),
    ("Usopp", "Caltrop Hell", (("Usopp - Caltrop Hell", 1),)),
    ("Usopp", "Pachinko Chaos", (("Usopp - Pachinko Chaos", 1),)),
    ("Sanji", "Flanchet", ()), ("Sanji", "Longe & Poitrine", ()),
    ("Sanji", "Collier Shoot", (("Sanji - Collier Shoot", 1),)),
    ("Sanji", "Party Table Kick Course", (("Sanji - Progressive Party Table Kick Course", 1),)),
    ("Sanji", "Premier Hachis", (("Sanji - Premier Hachis", 1),)),
    ("Sanji", "Concassé", (("Sanji - Concassé", 1),)),
    ("Sanji", "Veau Shot", (("Sanji - Veau Shot", 1),)),
    ("Nami", "Wind and Waves", ()),
    ("Nami", "Wintry Blast", (("Nami - Wintry Blast", 1),)),
    ("Nami", "Whirlwind", (("Nami - Whirlwind", 1),)),
    ("Nami", "Thunder Ball", (("Progressive Clima-Tact", 1),)),
    ("Nami", "Turbulent Air", (("Nami - Turbulent Air", 1),)),
    ("Nami", "Thunderbolt Tempo", (("Nami - Thunderbolt Tempo", 1),)),
    ("Nami", "White Rocking Horse 1", (("Jet Dial", 1),)),
    ("Chopper", "Darn You!", ()),
    ("Chopper", "Charge!", (("Chopper - Progressive Charge!", 1),)),
    ("Chopper", "Smash!", (("Chopper - Smash!", 1),)),
    ("Chopper", "Heavy Press", (("Chopper - Heavy Press", 1),)),
    ("Chopper", "Kick Launch!", (("Chopper - Kick Launch!", 1),)),
    ("Chopper", "Experiment", (("Experiment Equipment", 1),)),
    ("Robin", "Dos Fleur Lock", ()),
    # a combo's third hit needs its second: Quatro then Seis come from one progressive item
    ("Robin", "Quatro Fleur Tower", (("Robin - Progressive Fleur Combo", 1),)),
    ("Robin", "Seis Fleur Branch", (("Robin - Progressive Fleur Combo", 2),)),
    ("Robin", "Ocho Fleur Spike", (("Robin - Ocho Fleur Spike", 1),)),
    ("Robin", "Uno Fleur Cast", (("Robin - Uno Fleur Cast", 1),)),
    ("Robin", "Quatro Fleur Splash", (("Robin - Quatro Fleur Splash", 1),)),
    ("Robin", "Infinite Fleur Amaryllis", (("Robin - Infinite Fleur Amaryllis", 1),)),
    ("Robin", "Cien Fleur Big Tree", (("Robin - Cien Fleur Big Tree", 1),)),
    ("Franky", "Uppercut", ()),
    ("Franky", "Strong Right", (("Franky - Progressive Strong Right", 1),)),
    ("Franky", "Master Nail", (("Franky - Master Nail", 1),)),
    ("Franky", "Weapons Left", (("Franky - Progressive Weapons Left", 1),)),
    ("Franky", "Franky Boxing", (("Franky - Franky Boxing", 1),)),
    ("Franky", "Ultimate Hammer", (("Franky - Ultimate Hammer", 1),)),
    ("Franky", "Heavy Nunchaku", (("Heavy Nunchaku", 1),)),
    ("Brook", "Up Slash", ()),
    ("Brook", "Prelude Au Fer", (("Brook - Progressive Sword Combo", 1),)),
    ("Brook", "Polka Remise", (("Brook - Progressive Sword Combo", 2),)),
    ("Brook", "Gavotte Bond En Avant", (("Brook - Gavotte Bond en Avant", 1),)),
    ("Brook", "Fun Waltz", (("Brook - Progressive Fun Waltz", 1),)),
    ("Brook", "Humming March", (("Brook - Humming March", 1),)),
    ("Brook", "Three Verse Arrow Notch Slice", (("Brook - Three Verse Arrow Notch Slice", 1),)),
    ("Brook", "Lullaby Parry", (("Steel Violin Strings", 1),)),
]
MOVE_LEVELS = (2, 3, 4, 5)

# ----------------------------------------------------------------------------------------------
# Items. kind / data tell the client what to do. count = copies in the pool.
# ----------------------------------------------------------------------------------------------
PROG, PROG_SKIP, USEFUL, FILLER = "progression", "progression_skip_balancing", "useful", "filler"


class ItemDef(NamedTuple):
    name: str
    cls: str
    count: int
    kind: str
    data: object = None


ITEMS: List[ItemDef] = []


def _add(name, cls, count, kind, data=None):
    ITEMS.append(ItemDef(name, cls, count, kind, data))


# Straw Hats (one is given at the start, chosen by option)
for _i, _n in enumerate(CHARACTERS):
    _add(_n, PROG, 1, "character", _i)

# Move unlocks: data = (character index, [short move id given by copy 1, copy 2, ...])
_MOVE_ITEMS = [
    ("Luffy - Gum Gum Kusarigama", 0, [16]), ("Luffy - Gum Gum Whip (Charged)", 0, [17]),
    ("Luffy - Progressive Gum Gum Battle Axe", 0, [8, 24]), ("Luffy - Progressive Gum Gum Gatling", 0, [3, 19]),
    ("Luffy - Progressive Gum Gum Balloon", 0, [4, 20]), ("Luffy - Gum Gum Cannon", 0, [9]),
    ("Luffy - Gum Gum Storm", 0, [6]), ("Luffy - Gear Second", 0, [7]),
    ("Zoro - Triple Sword Oni Giri (Charged)", 1, [16]), ("Zoro - Progressive Single Sword Lion's Song", 1, [10, 25]),
    ("Zoro - Dual Sword Phoenix of 72 Desires", 1, [3]), ("Zoro - Single Sword Flying Dragon Blaze", 1, [12]),
    ("Zoro - Triple Sword Demon Bull", 1, [13]), ("Zoro - Triple Sword Succession 3000 Worlds", 1, [6]),
    ("Zoro - Deadly 9 Swords Ashura Ichibugin", 1, [7]),
    ("Usopp - Progressive Death Blow Lead Star", 2, [1, 2]), ("Usopp - Usopp Pound", 2, [4]),
    ("Usopp - Caltrop Hell", 2, [13]), ("Usopp - Pachinko Chaos", 2, [6]),
    ("Sanji - Collier Shoot", 3, [2]), ("Sanji - Progressive Party Table Kick Course", 3, [11, 26]),
    ("Sanji - Premier Hachis", 3, [12]), ("Sanji - Concassé", 3, [5]), ("Sanji - Veau Shot", 3, [6]),
    ("Sanji - Diable Jambe", 3, [7]),
    ("Nami - Cool Ball & Heat Ball", 4, [22]), ("Nami - Wintry Blast", 4, [9]), ("Nami - Turbulent Air", 4, [12]),
    ("Nami - Whirlwind", 4, [5]), ("Nami - Thunderbolt Tempo", 4, [6]),
    ("Chopper - Progressive Charge!", 5, [1, 15]), ("Chopper - Smash!", 5, [10]), ("Chopper - Heavy Press", 5, [4]),
    ("Chopper - Kick Launch!", 5, [12]),
    ("Robin - Dos Fleur Lock (Charged)", 6, [15]),
    ("Robin - Progressive Fleur Combo", 6, [1, 2]), ("Robin - Ocho Fleur Spike", 6, [11]), ("Robin - Uno Fleur Cast", 6, [4]),
    ("Robin - Quatro Fleur Splash", 6, [13]), ("Robin - Infinite Fleur Amaryllis", 6, [6]),
    ("Robin - Cien Fleur Big Tree", 6, [14]),
    ("Franky - Triangle Jacker", 7, [22]), ("Franky - Progressive Strong Right", 7, [1, 15]),
    ("Franky - Master Nail", 7, [3]), ("Franky - Progressive Weapons Left", 7, [4, 18]),
    ("Franky - Franky Boxing", 7, [12]), ("Franky - Ultimate Hammer", 7, [7]),
    ("Brook - Aubade Coup Droit", 8, [15]),
    ("Brook - Progressive Sword Combo", 8, [1, 2, 17]), ("Brook - Gavotte Bond en Avant", 8, [3]),
    ("Brook - Progressive Fun Waltz", 8, [4, 19]), ("Brook - Humming March", 8, [5]),
    ("Brook - Three Verse Arrow Notch Slice", 8, [6]),
]
# Moves that make bamboo / vines cuttable ("sharp attacks") are full progression.
SHARP_MOVE_ITEMS = {"Usopp - Caltrop Hell", "Robin - Uno Fleur Cast", "Franky - Master Nail",
                    "Franky - Triangle Jacker"}
for _n, _c, _ids in _MOVE_ITEMS:
    _add(_n, PROG if _n in SHARP_MOVE_ITEMS else PROG_SKIP, len(_ids), "move", (_c, _ids))

# Abilities: data = (character index, ability slot 0/1/2). Slot 2 = Determination (5 levels).
_ABILITIES = [
    ("Luffy", "Gum Gum Body", "Gum Gum Power"), ("Zoro", "Master Swordsman", "Secrets of the Blade"),
    ("Usopp", "Battle Strategy", "Art of Development"), ("Sanji", "Black Leg", "Art of Cooking"),
    ("Nami", "Cat Burglar", "Weather Forecast"), ("Chopper", "First Aid", "Art of Compounding"),
    ("Robin", "Flower Flower Power", "Overwhelm"), ("Franky", "Iron Man", "Supply"),
    ("Brook", "Light Weight", "Speed Sword"),
]
ART_ITEMS = {"Usopp - Progressive Art of Development", "Sanji - Progressive Art of Cooking",
             "Chopper - Progressive Art of Compounding"}
for _ci, (_c, _a0, _a1) in enumerate(_ABILITIES):
    for _slot, _a in ((0, _a0), (1, _a1)):
        _n = f"{_c} - Progressive {_a}"
        _add(_n, PROG if _n in ART_ITEMS or _n == "Franky - Progressive Supply" else USEFUL, 3, "ability", (_ci, _slot))
    _add(f"{_c} - Progressive Determination", USEFUL, 5, "ability", (_ci, 2))

# Co-op moves: data = co-op requirement record index the client opens (opuc-coop-moves.md).
_add("Gum Gum 300 Pound Cannon", PROG_SKIP, 1, "coop", {"record": 2})
_add("Uso/Cho Hammer Comet", PROG_SKIP, 1, "coop", {"record": 3, "item": 177})
_add("Certificate", PROG_SKIP, 1, "coop", {"record": 1, "item": 179})

# Tools and key items. data = {"item": game item id (or per-copy list), "move": (char, id)}
_add("Pickaxe", PROG, 1, "key", {"item": 1})
_add("Broken Bug-Catcher Net", PROG, 1, "key", {"item": 3})   # repaired with the vanilla Workshop recipe
_add("Fishing Rod", PROG, 1, "key", {"item": 6})
_add("Progressive Fishing Rod Level", PROG_SKIP, 30, "rod_level")   # copies set by the rod_upgrade_items option
_add("Progressive Fishing Rod Line", PROG_SKIP, 30, "rod_line")
_add("Progressive Vacuum Cleaner", PROG, 2, "vacuum")           # 1: Vacuum (item 8), 2: Power Vacuum
for _n, _gid in [("Steel Chain", 87), ("Enhanced Reel", 89), ("Ultimate Reel", 90), ("Mystery Gadget", 91),
                 ("Garment Box", 92), ("Vision Dial", 93), ("Tone Dial", 94), ("Mask Fragment", 96)]:
    # Garment Box opens no recipe / move location (user, 2026-10-19)
    _add(_n, USEFUL if _n == "Garment Box" else PROG_SKIP, 1, "key", {"item": _gid})
_add("Jet Dial", PROG_SKIP, 1, "key", {"item": 95, "move": (4, 13)})
_add("Progressive Item Bag Upgrade", USEFUL, 2, "key", {"item": [162, 163]})
_add("Progressive Palette Upgrade", USEFUL, 2, "key", {"item": [164, 165]})
_add('Giant Slingshot "Kabuto"', PROG_SKIP, 1, "key", {"item": 170, "move": (2, 15)})
_add("Rumble Ball", PROG_SKIP, 1, "key", {"item": 171, "move": (5, 7)})
_add("Impact Dial", PROG_SKIP, 1, "key", {"item": 172, "move": (2, 11)})
_add("Experiment Equipment", PROG_SKIP, 1, "key", {"item": 173, "move": (5, 6)})
_add("Heavy Nunchaku", PROG_SKIP, 1, "key", {"item": 174, "move": (7, 13)})
_add("Steel Violin Strings", PROG_SKIP, 1, "key", {"item": 175, "move": (8, 7)})
_add("Sogeking Mask", PROG_SKIP, 1, "key", {"item": 176, "move": (2, 14)})
_add("Progressive Clima-Tact", PROG_SKIP, 2, "clima")           # 1: Clima-Tact Repair (178) + Thunder Ball, 2: Thunder Ball repeat (nam 25)
_add("Crystal", PROG_SKIP, 1, "key", {"item": 62})

# Systems
_add("Usopp's Workshop", PROG, 1, "room", "workshop")
_add("Sanji's Kitchen", PROG, 1, "room", "kitchen")
_add("Chopper's Pharmacy", PROG, 1, "room", "pharmacy")
_add("Progressive Gabri Level", PROG, 13, "gabri")

# Shrine / build site access: data = shrine id. Locked shrines get an impossible Energy cost.
SHRINE_ACCESS = {
    "Wooded Isle Shrine 1 Access": 103, "Wooded Isle Shrine 2 Access": 100, "Wooded Isle Shrine 3 Access": 101,
    "Wooded Isle Building Site 1 Access": 111, "Wooded Isle Building Site 2 Access": 112,
    "Wooded Isle Building Site 3 Access": 113, "Wooded Isle Building Site 4 Access": 114,
}
for _n, _sid in SHRINE_ACCESS.items():
    _add(_n, PROG if _sid in (103, 100, 101, 111, 112) else PROG_SKIP, 1, "shrine", _sid)

# Treasure map fragments in this test (Map 2 -> Flour chest, Map 8 -> Steel Chain chest)
for _k in range(4):
    _add(f"Map 2, Fragment {_k + 1}", PROG_SKIP, 1, "key", {"item": 194 + _k})
for _k in range(3):
    _add(f"Map 8, Fragment {_k + 1}", PROG_SKIP, 1, "key", {"item": 215 + _k})

# Filler: (name, game item id, weight). Stronger food / medicine is rarer.
FILLER_ITEMS: List[Tuple[str, int, float]] = [
    ("Hardtack Ration", 161, 10), ("Healing Capsule", 18, 10), ("Stamina Capsule", 20, 10),
    ("Angel Omelette", 140, 8), ("Broiled Killifish", 141, 8), ("Large Mushroom Salad", 142, 8),
    ("Seagull Bone Soup", 143, 8),
    ("Dual-Action Capsule", 22, 6), ("Healing Tonic", 17, 5), ("Stamina Tonic", 19, 5),
    ("Mock Cherry Pie", 144, 5), ("Simmered Ecrevisse", 145, 5), ("Pirate Shaved Ice", 146, 5),
    ("Shrimp with Tartar Sauce", 147, 5), ("Saury Full Course", 157, 5), ("Pirate's Lunch", 160, 5),
    ("Kuwagata", 28, 4),
    ("Dual-Action Tonic", 21, 3), ("Spicy Miso Shark's Fin", 149, 3), ("Octopus Dumplings", 150, 3),
    ("Sauteed Tuna Steak", 156, 3), ("Baked Stone Stew", 158, 3), ("Special Pirate Soda", 159, 3),
    ("Ancient-Recipe Soup", 151, 3), ("Stamina Stew", 148, 2), ("Sashimi Assortment", 152, 2),
    ("Restorative Drug", 24, 1), ("Revival Elixir", 23, 1), ("Meat-Lover's Delight", 153, 1),
    ("Roasted Meat Festival", 154, 1), ("Giant Shell Boat", 155, 1),
]
# Small (x3) and Large (x5) packages of every food / medicine above (and the Kuwagata), rarer than single
# ones, plus the six Gabri orbs (singles only). Appended after the singles so earlier item IDs stay put.
PACKAGES = (("Small Package of", 3, 0.5), ("Large Package of", 5, 0.25))
_singles = list(FILLER_ITEMS)
for _prefix, _count, _scale in PACKAGES:
    for _n, _gid, _w in _singles:
        FILLER_ITEMS.append((f"{_prefix} {_n}", _gid, _w * _scale))
FILLER_ITEMS += [("Red Orb", 80, 3), ("Blue Orb", 81, 3), ("White Orb", 82, 3), ("Green Orb", 83, 3),
                 ("Black Orb", 84, 3), ("Gold Orb", 85, 3)]
# Filler groups for the weighting options (game item ids)
FOOD_IDS = set(range(140, 162))
MEDICINE_IDS = set(range(17, 25))


def filler_group(gid: int) -> str:
    return "food" if gid in FOOD_IDS else "medicine" if gid in MEDICINE_IDS else "other"


# Filler that a shrine asks for (event/epoint/zone*.bin): never in the pool, so filler can't let a player
# activate a shrine before logic expects it (user, 2026-10-22). The items keep their ids.
SHRINE_OFFERING_FILLER = {"Healing Capsule", "Stamina Tonic", "Mock Cherry Pie", "Dual-Action Tonic"}
FILLER_COUNTS: Dict[str, int] = {f"{p} {n}": c for p, c, _s in PACKAGES for n, _g, _w in _singles}
for _n, _gid, _w in FILLER_ITEMS:
    _add(_n, FILLER, 0, "filler", {"item": _gid, "count": FILLER_COUNTS.get(_n, 1)})

# ---- Island 2 update (0.16.0): added after the filler so earlier item ids keep their numbers.
# ISLAND_2_ITEMS are only in the pool when Gorge Isle is in the seed (goal option).
GORGE_SHRINE_ACCESS = {
    "Gorge Isle Shrine 1 Access": 200, "Gorge Isle Shrine 2 Access": 201,
    "Gorge Isle Build Site 1 Access": 211, "Gorge Isle Build Site 2 Access": 212,
    "Gorge Isle Build Site 3 Access": 213, "Gorge Isle Build Site 4 Access": 214,
    "Gorge Isle Build Site 5 Access": 215, "Gorge Isle Build Site 6 Access": 216,
}
for _n, _sid in GORGE_SHRINE_ACCESS.items():
    _add(_n, PROG if _sid in (200, 201, 211, 212, 213) else PROG_SKIP, 1, "shrine", _sid)
SHRINE_ACCESS.update(GORGE_SHRINE_ACCESS)
# The Wherever Cannon (Sunny shrine 1010): its build site appears on Wooded Isle after reaching Gorge Isle (user)
_add("Thousand Sunny Build Site 1 Access", PROG_SKIP, 1, "shrine", 1010)
SHRINE_ACCESS["Thousand Sunny Build Site 1 Access"] = 1010
for _k in range(4):
    _add(f"Map 1, Fragment {_k + 1}", PROG_SKIP, 1, "key", {"item": 190 + _k})
for _k in range(5):
    _add(f"Map 4, Fragment {_k + 1}", PROG_SKIP, 1, "key", {"item": 201 + _k})
for _k in range(3):
    _add(f"Map 6, Fragment {_k + 1}", PROG_SKIP, 1, "key", {"item": 209 + _k})
# Log Poses open islands in the Next Island menu (the Wooded Isle is always open)
_add("Gorge Isle, the Ruined Path", PROG, 1, "island", 2)
_add("Central Isle, New Beginnings", PROG, 1, "island", 5)
# The Final Door (shrine 500): locked (impossible cost) until this item, so only with goal doom_guardian
_add("The Final Door", PROG, 1, "shrine", 500)
SHRINE_ACCESS["The Final Door"] = 500
ISLAND_5_ITEMS = {"Central Isle, New Beginnings", "The Final Door"}
ISLAND_2_ITEMS = set(GORGE_SHRINE_ACCESS) | {"Thousand Sunny Build Site 1 Access",
                                             "Gorge Isle, the Ruined Path"} | {f"Map {m}, Fragment {k + 1}" for m, n in ((1, 4), (4, 5), (6, 3))
                                               for k in range(n)}
BUILD_SITE_IDS = {sid for sid in SHRINE_ACCESS.values() if sid % 100 >= 10}

# Treasure maps in this world: map name -> its fragment item names
MAP_FRAGMENT_GROUPS: Dict[str, List[str]] = {}
for _i in ITEMS:
    if _i.name.startswith("Map ") and ", Fragment " in _i.name:
        MAP_FRAGMENT_GROUPS.setdefault(_i.name.split(",")[0], []).append(_i.name)

ITEM_TABLE: Dict[str, ItemDef] = {i.name: i for i in ITEMS}
ITEM_IDS: Dict[str, int] = {i.name: BASE_ID + n for n, i in enumerate(ITEMS)}

# ----------------------------------------------------------------------------------------------
# Locations. check = how the client detects it:
#   ("flag", n)          EventScriptEndFlag n turns on
#   ("chest", id)        treasure chest opened marker
#   ("shrine", id)       shrine / build site activated (state bit 0x02)
#   ("craft", room, row) recipe made bit (state & 0x08)
#   ("move", char, id, level)  move level reaches level
#   ("coop", co-op, level)     co-op move level reaches level
# ----------------------------------------------------------------------------------------------


class LocDef(NamedTuple):
    name: str
    region: str
    check: tuple


LOCATIONS: List[LocDef] = []


def _loc(name, region, check):
    LOCATIONS.append(LocDef(name, region, check))


for _c, _m, _req in MOVE_LOCATIONS:
    for _lv in MOVE_LEVELS:
        # Enemies don't respawn in the Prologue, so levelling moves needs Wooded Isle Part 1 in logic. (Level 2
        # of a starting move used to be Prologue logic, but a player who switches to a received character
        # can miss it; user 2026-10-19.)
        _loc(f"{_c} - {_m} Level {_lv}", "Wooded Isle Part 1", ("move", CHAR_INDEX[_c], MOVE_IDS[(_c, _m)], _lv))

_loc("Prologue Part 1 - Mud Puppet Ambush", "Prologue Part 1", ("flag", 11251))
_loc("Prologue Part 1 - Marine Ambush", "Prologue Part 1", ("flag", 11253))
_loc("Prologue Part 2 - Mud Puppet Ambush", "Prologue Part 2", ("flag", 11261))
_loc("Prologue Part 3 - Mud Puppet Ambush", "Prologue Part 3", ("flag", 11271))
_loc("Wooded Isle Shrine - An Odd Stone & A Strange Creature", "Prologue Part 3", ("shrine", 103))
_loc("First Step on the Thousand Sunny", "Wooded Isle Part 1", ("flag", 11990))
_loc("Thousand Sunny - Broken Bug-Catcher Net Chest", "Thousand Sunny", ("chest", 10851))
_loc("Thousand Sunny - Vacuum Cleaner Chest", "Thousand Sunny", ("chest", 10859))
_loc("Wooded Isle Monument - Far, Far Away", "Wooded Isle Part 1", ("flag", 11652))
_loc("Wooded Isle - Nectar Chest", "Wooded Isle Part 1", ("chest", 11700))
_loc("Wooded Isle - Restorative Drug Chest", "Wooded Isle Part 1", ("chest", 11704))
_loc("Wooded Isle - Steel Chain Chest", "Wooded Isle Part 1", ("chest", 11701))
_loc("Wooded Isle - Crystal Chest", "Wooded Isle Part 1", ("chest", 11707))
_loc("Wooded Isle Shrine - An Enormous Boulder", "Wooded Isle Part 1", ("shrine", 100))
_loc("Wooded Isle Mid-Boss - Bartholomew Kuma Defeated", "Wooded Isle Mid-Boss", ("flag", 11301))
_loc("Wooded Isle - Gabri Level Up Event 1", "Wooded Isle Mid-Boss", ("flag", 11303))
_loc("Wooded Isle - Green Orb Chest", "Wooded Isle Mid-Boss", ("chest", 11705))
_loc("Wooded Isle - Enforcer Ambush", "Wooded Isle Part 2", ("flag", 11281))
_loc("Wooded Isle Monument - Eternity", "Wooded Isle Part 2", ("flag", 11651))
_loc("Wooded Isle Build Site - An Unclimbable Area", "Wooded Isle Part 2", ("shrine", 111))
_loc("Wooded Isle - Flour Chest", "An Unclimbable Area", ("chest", 11702))
_loc("Wooded Isle Shrine - What Lies Asleep in the Amber", "Wooded Isle Part 2", ("shrine", 101))
_loc("Wooded Isle Build Site - An Incomplete Path", "Wooded Isle Part 2 (Right)", ("shrine", 112))
_loc("Wooded Isle Secret Boss - Captain Buggy Defeated", "An Incomplete Path", ("flag", 11401))
_loc("Wooded Isle - Gabri Level Up Event 3", "An Incomplete Path", ("flag", 11403))
_loc("Wooded Isle - Sea King Fin Chest", "An Incomplete Path", ("chest", 11706))

# Goal (option "goal"): the island boss of the last island in the seed (event, no location id)
ENERU = 'Wooded Isle Island Boss - "God" Eneru Defeated'          # EventScriptEndFlag 11351
MORIA = "Gorge Isle Island Boss - Gecko Moria Defeated"            # EventScriptEndFlag 12351
FINAL_BOSS = "Central Isle - Doom Guardian Defeated"                  # 15020/15030, GameClear ([0x8068A298]+6)
GOALS = {0: (ENERU, 11351, "Island Boss"), 1: (MORIA, 12351, "Gorge Isle Island Boss"),
         2: (FINAL_BOSS, 15030, "Central Isle")}
GOAL_EVENT, GOAL_FLAG = ENERU, 11351   # defaults for older slot data

# Crafting first-time checks: (room, row, original result name, art level, dummy?)
# Art level = row // 8 (rows 0-7 level 0 ... 24-31 level 3, confirmed in game).
# dummy=True: the result is a one-time key item and is replaced for good by "Archipelago Item".
CRAFTS: List[Tuple[str, int, str, bool]] = [
    ("workshop", 1, "Bug-Catcher Net", False), ("workshop", 2, "Fishing Rod", True),
    ("workshop", 3, "Clima-Tact Repair", True), ("workshop", 4, "Kuwagata", False),
    ("workshop", 6, "Fishing Rod Upgrade", True), ("workshop", 7, "Fishing Line Upgrade", True),
    ("workshop", 9, "Power Vacuum Cleaner", True), ("workshop", 10, "Whopper Fishing Rod", True),
    ("workshop", 11, "Palette Upgrade 1", True), ("workshop", 12, "Jet Dial", True),
    ("workshop", 13, "Impact Dial", True), ("workshop", 14, "Whopper Rod Upgrade", True),
    ("workshop", 19, "Palette Upgrade 2", True), ("workshop", 20, "Heavy Nunchaku", True),
    ("workshop", 21, "Bombs", False), ("workshop", 23, "Special Item Bag", True),
    ("workshop", 27, "Steel Violin Strings", True),
    ("kitchen", 7, "Broiled Killifish", False), ("kitchen", 12, "Simmered Ecrevisse", False),
    ("pharmacy", 0, "Healing Capsule", False), ("pharmacy", 8, "Healing Tonic", False),
    ("pharmacy", 26, "Poison Ball", False),
]
# Every recipe in the game whose result is a one-time key item (kept as the dummy for good,
# including ones not reachable in this test).
DUMMY_RECIPES: Dict[str, List[int]] = {
    "workshop": [2, 3, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 19, 20, 23, 24, 26, 27, 28, 30],
    "pharmacy": [14, 28],
}
ROOM_LOCATION_PREFIX = {"workshop": "Usopp's Workshop - Craft", "kitchen": "Sanji's Kitchen - Cook",
                        "pharmacy": "Chopper's Pharmacy - Compound"}
ROOM_ITEM = {"workshop": "Usopp's Workshop", "kitchen": "Sanji's Kitchen", "pharmacy": "Chopper's Pharmacy"}
# Thousand Sunny options: room -> (unlock option, "required for art" option, character index)
ROOM_OPTIONS = {"workshop": ("workshop_unlock", "usopp_required_for_art", 2),
                "kitchen": ("kitchen_unlock", "sanji_required_for_art", 3),
                "pharmacy": ("pharmacy_unlock", "chopper_required_for_art", 5)}
ROOM_ART = {"workshop": "Usopp - Progressive Art of Development", "kitchen": "Sanji - Progressive Art of Cooking",
            "pharmacy": "Chopper - Progressive Art of Compounding"}
for _room, _row, _res, _d in CRAFTS:
    _loc(f"{ROOM_LOCATION_PREFIX[_room]} {_res}", "Thousand Sunny", ("craft", _room, _row))

# Fishing / creature catching: first catch of each = a location (the item's "ever obtained" bit).
# Item ids from the game's item table; all 20 of each get location ids so seeds stay compatible when
# more islands are added. Only the ones catchable in this world's scope (rules.SOURCES) can be chosen.
CREATURES: Dict[int, str] = {
    97: "Seagull", 98: "Tempest Mouse", 99: "Invisible Swallowtail", 100: "Swallowtail Butterfly",
    101: "Honey Bee", 102: "Tree Frog", 103: "Doctor Hornet", 104: "Lightning Beetle", 105: "Flying Penguin",
    106: "Hercules Beetle", 107: "Golden Hercules", 108: "Rock Lizard", 109: "Mammoth Toad", 110: "Mole",
    111: "Icicle Lizard", 112: "Ice Beetle", 113: "Sleep Butterfly", 114: "Fire Hercules",
    115: "Light Bulb Firefly", 116: "Lantern Trilobite",
}
FISH: Dict[int, str] = {
    117: "Clawed Shrimp", 118: "Treasure Shell", 119: "Striped Clam", 120: "Superstar Starfish",
    121: "Fist Crayfish", 122: "Forked-Tail Killifish", 123: "Smiley Jellyfish", 124: "Oriental Butterflyfish",
    125: "Shining Saury", 126: "Salamandrake", 127: "Balloon Catfish", 128: "Adventure Fish", 129: "Ice Sunfish",
    130: "Skull Knight", 131: "Elephant Tuna", 132: "Shark", 133: "Panda Shark", 134: "Large Sea King",
    135: "Extra-Large Sea King", 136: "Giant Turtle Sea King",
}
for _gid, _n in FISH.items():
    _loc(f"Fishing - {_n}", "Wooded Isle Part 1", ("catch", _gid))
for _gid, _n in CREATURES.items():
    _loc(f"Creatures - {_n}", "Wooded Isle Part 1", ("catch", _gid))

# Co-op move level-up locations (levels 2-5), added after the fish / creatures so earlier IDs keep their numbers.
# (move name, co-op number, unlock item, members). Level: byte at Z + 0x568 + co-op * 2 of each member
# (Hammer Comet = co-op 3 at Z + 0x56E in both Usopp and Chopper, user 2026-10-19). Members come from the
# game's co-op definition masks (opuc-coop-moves.md). They count as supers for the importance options.
COOP_LOCATIONS: List[Tuple[str, int, str, Tuple[str, ...]]] = [
    ("Gum Gum 300 Pound Cannon", 2, "Gum Gum 300 Pound Cannon", ("Luffy", "Zoro")),
    ("Uso/Cho Hammer Comet", 3, "Uso/Cho Hammer Comet", ("Usopp", "Chopper")),
    ("Lightning Bone Sword", 1, "Certificate", ("Usopp", "Nami", "Robin", "Brook")),
]
COOP_MEMBERS: Dict[int, Tuple[int, ...]] = {cid: tuple(CHAR_INDEX[c] for c in who) for _m, cid, _i, who in COOP_LOCATIONS}
for _m, _cid, _item, _who in COOP_LOCATIONS:
    for _lv in MOVE_LEVELS:
        _loc(f"Co-op - {_m} Level {_lv}", "Wooded Isle Part 1", ("coop", _cid, _lv))

# Story progress in the Prologue (unskippable; Part 3 Completed comes after Shrine 1). Added last so earlier
# location IDs keep their numbers.
_loc("Prologue Part 1 Completed", "Prologue Part 1", ("flag", 11011))
_loc("Prologue Part 2 Completed", "Prologue Part 2", ("flag", 11021))
_loc("Meet Gabri", "Prologue Part 3", ("flag", 11032))
_loc("Prologue Part 3 Completed", "Prologue Part 3", ("flag", 11031))

# ---- Island 2 update (0.16.0). Everything here is after Eneru, so these only exist with goal Gorge Isle.
# Eneru is a location once he isn't the goal; his Gabri level-up, two Sunny chests and Lightning Beetles
# (Wooded Isle Part 2, outside the boss room) come after him (user, 2026-10-22).
_loc(ENERU, "Island Boss", ("flag", 11351))
_loc("Wooded Isle - Gabri Level Up Event 2", "Post-Eneru", ("flag", 11353))
_loc("Thousand Sunny - Pickaxe Chest", "Thousand Sunny (After an Island Boss)", ("chest", 10857))
_loc("Thousand Sunny - Red Fruit Chest", "Thousand Sunny (After an Island Boss)", ("chest", 10850))
# Gorge Isle (Island 2), user's region map 2026-10-22. Obstructed Paths / Hidden Area / Secret Boss need a Mole
# (not in logic yet): no locations there.
_loc("First Step on the Gorge Isle", "Gorge Isle Part 1", ("flag", 12200))
_loc("Gorge Isle - Zombie Ambush", "Gorge Isle Part 1", ("flag", 12251))
_loc("Gorge Isle - Golden Fruit Chest", "Gorge Isle Part 2", ("chest", 12700))
_loc("Gorge Isle - The Silent Ancient Creature", "Gorge Isle Part 2", ("shrine", 200))
_loc("Gorge Isle Mid-Boss - Captain Kuro Defeated", "Gorge Isle Part 3", ("flag", 12301))
_loc("Gorge Isle Mid-Boss - Don Krieg Defeated", "Gorge Isle Part 3", ("flag", 12302))
_loc("Gorge Isle - Gabri Level Up Event 1", "Gorge Isle Part 3", ("flag", 12303))
_loc("Gorge Isle - Marine Ambush", "Gorge Isle Part 3", ("flag", 12271))
_loc("Gorge Isle - Red Orb Chest", "Gorge Isle Part 3", ("chest", 12705))
_loc("Gorge Isle - Blue Fruit Chest", "Gorge Isle Part 3", ("chest", 12706))
_loc("Gorge Isle - An Incomplete Path", "Gorge Isle Part 3", ("shrine", 211))
_loc("Gorge Isle - Antidote Powder Chest", "Gorge Isle Part 4", ("chest", 12701))
_loc("Gorge Isle - Royal Jelly Chest", "Gorge Isle Part 4", ("chest", 12703))
_loc("Gorge Isle - Enhanced Reel Chest", "Gorge Isle Part 4", ("chest", 12704))
_loc("Gorge Isle Monument - Creation", "Gorge Isle Part 4", ("flag", 12652))
_loc("Gorge Isle - The Ruins in the Sunset", "Gorge Isle Part 4", ("shrine", 201))
_loc("Gorge Isle - An Incomplete Path (2)", "Gorge Isle Part 4", ("shrine", 212))
_loc("Gorge Isle - An Unclimbable Path", "Gorge Isle Optional Bridge Path", ("shrine", 213))
_loc("Gorge Isle - Mask Fragment Chest", "Gorge Isle Optional Ladder Path", ("chest", 12702))
_loc("Gorge Isle - An Incomplete Path (3)", "Gorge Isle Optional Ladder Path", ("shrine", 214))
_loc("Gorge Isle - Large Marine Ambush", "Gorge Isle Optional Poison Path", ("flag", 12263))
_loc("Gorge Isle Monument - Hope", "Gorge Isle Optional Poison Path", ("flag", 12651))
# ---- 0.17.0: islands open with Log Pose items; the final island (Central Isle) and after-Gecko Moria checks.
_loc("Thousand Sunny - Gold Orb Chest (1)", "Post-Eneru", ("chest", 10852))          # switched on by 11353
_loc(MORIA, "Gorge Isle Island Boss", ("flag", 12351))
_loc("Gorge Isle - Gabri Level Up Event 2", "Post-Gecko Moria", ("flag", 12353))
_loc("Thousand Sunny - Gold Orb Chest (2)", "Post-Gecko Moria", ("chest", 10853))   # switched on by 12353
_loc("Central Isle Monument - Inferno", "Central Isle", ("flag", 15800))
# Sunny shrine 1010, build site on Wooded Isle once Gorge Isle has been reached (user, 2026-10-22)
_loc("Thousand Sunny - Wherever Cannon", "Gorge Isle Part 1", ("shrine", 1010))

# Recipes that only became possible with Gorge Isle ingredients (or weren't listed before). Locations are
# only created for recipes whose ingredients are all reachable in the seed (rules.craft_in_scope).
CRAFTS_EXTRA: List[Tuple[str, int, str, bool]] = [
    ("workshop", 5, "Traps", False), ("workshop", 8, 'Giant Slingshot "Kabuto"', True),
    ("workshop", 15, "Large Item Bag", True), ("workshop", 17, "Batteries", False),
    ("workshop", 24, "Sogeking Mask", True), ("workshop", 25, "Flamethrowers", False),
    ("workshop", 26, "Sea King Fishing Rod", True), ("workshop", 28, "Uso/Cho Hammer Comet", True),
    ("workshop", 30, "Sea King Rod Upgrade", True),
    ("kitchen", 0, "Angel Omelette", False), ("kitchen", 2, "Large Mushroom Salad", False),
    ("kitchen", 6, "Seagull Bone Soup", False), ("kitchen", 8, "Shrimp with Tartar Sauce", False),
    ("kitchen", 10, "Mock Cherry Pie", False), ("kitchen", 13, "Saury Full Course", False),
    ("kitchen", 14, "Pirate Shaved Ice", False), ("kitchen", 15, "Pirate's Lunch", False),
    ("kitchen", 16, "Sauteed Tuna Steak", False), ("kitchen", 18, "Special Pirate Soda", False),
    ("kitchen", 19, "Baked Stone Stew", False), ("kitchen", 20, "Spicy Miso Shark's Fin", False),
    ("kitchen", 22, "Octopus Dumplings", False), ("kitchen", 23, "Ancient-Recipe Soup", False),
    ("kitchen", 24, "Sashimi Assortment", False), ("kitchen", 26, "Stamina Stew", False),
    ("kitchen", 28, "Giant Shell Boat", False), ("kitchen", 29, "Roasted Meat Festival", False),
    ("kitchen", 30, "Meat-Lover's Delight", False),
    ("pharmacy", 2, "Stamina Capsule", False), ("pharmacy", 5, "Dual-Action Capsule", False),
    ("pharmacy", 7, "Gunpowder", False), ("pharmacy", 10, "Stamina Tonic", False),
    ("pharmacy", 12, "Syrup", False), ("pharmacy", 13, "Dual-Action Tonic", False),
    ("pharmacy", 14, "Experiment Equipment", True), ("pharmacy", 15, "Thunder Powder", False),
    ("pharmacy", 17, "Anti-Cold Cream", False), ("pharmacy", 18, "Antidote Powder", False),
    ("pharmacy", 23, "Ice Powder", False), ("pharmacy", 25, "Restorative Drug", False),
    ("pharmacy", 28, "Rumble Ball", True), ("pharmacy", 31, "Flame Powder", False),
]
for _room, _row, _res, _d in CRAFTS_EXTRA:
    _loc(f"{ROOM_LOCATION_PREFIX[_room]} {_res}", "Thousand Sunny", ("craft", _room, _row))
CRAFTS += CRAFTS_EXTRA

LOCATION_TABLE: Dict[str, LocDef] = {l.name: l for l in LOCATIONS}
LOCATION_IDS: Dict[str, int] = {l.name: BASE_ID + n for n, l in enumerate(LOCATIONS)}


# ----------------------------------------------------------------------------------------------
# Fishing rod upgrades (option rod_upgrade_items: 30, 6 or 4 copies each of Rod Level / Rod Line)
# ----------------------------------------------------------------------------------------------
ROD_GRADE_BYTES_4 = [0x0A, 0x0B, 0x16, 0x20]     # Fishing Rod max -> Whopper -> Sea King -> MAX
LINE_LEVELS_4 = [8, 16, 23, 30]


def rod_level_from_items(mode: int, k: int) -> int:
    """Rod level (0-30, before the grade-boundary skip) after k Rod Level items."""
    if mode == 6:
        return min(30, 5 * k)
    return min(30, k)


def line_level(mode: int, k: int) -> int:
    """Line level (0-30) after k Rod Line items."""
    if k <= 0:
        return 0
    if mode == 4:
        return LINE_LEVELS_4[min(k, 4) - 1]
    if mode == 6:
        return min(30, 5 * k)
    return min(30, k)


def rod_items_needed(mode: int, level: int) -> int:
    """Rod Level items needed to reach a rod level (0-30): 4 mode = Fishing Rod max (10) -> Whopper (11)
    -> Sea King (22) -> MAX."""
    if mode == 4:
        return next(k for k, b in enumerate([0] + ROD_GRADE_BYTES_4) if b >= level)
    k = 0
    while rod_level_from_items(mode, k) < level:
        k += 1
    return k


def line_items_needed(mode: int, level: int) -> int:
    k = 0
    while line_level(mode, k) < level:
        k += 1
    return k


# Super moves (their level-up locations follow the super_move_locations_important option)
SUPER_MOVES = {
    ("Luffy", "Gum Gum Storm"), ("Zoro", "Triple Sword Succession 3000 Worlds"),
    ("Zoro", "Deadly 9 Swords Ashura Ichibugin"), ("Usopp", "Pachinko Chaos"), ("Sanji", "Veau Shot"),
    ("Nami", "Thunderbolt Tempo"), ("Nami", "White Rocking Horse 1"), ("Chopper", "Experiment"),
    ("Robin", "Infinite Fleur Amaryllis"), ("Robin", "Cien Fleur Big Tree"), ("Franky", "Ultimate Hammer"),
    ("Franky", "Heavy Nunchaku"), ("Brook", "Three Verse Arrow Notch Slice"), ("Brook", "Lullaby Parry"),
}

# Locations removed by Super Move Locations: off (super moves and co-op moves)
SUPER_LOCATION_NAMES = ({f"{_c} - {_m} Level {_lv}" for _c, _m in SUPER_MOVES for _lv in MOVE_LEVELS}
                        | {f"Co-op - {_m} Level {_lv}" for _m, _cid, _i, _w in COOP_LOCATIONS for _lv in MOVE_LEVELS})
