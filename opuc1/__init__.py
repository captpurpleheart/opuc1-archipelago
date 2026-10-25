"""
One Piece Unlimited Cruise Part 1 (Wii, PAL ROUPAF) - Archipelago world.
Prologue, Thousand Sunny, Wooded Isle (Island 1) and Gorge Isle (Island 2). Goal: the last island's boss.
"""
from typing import Any, Dict, List, Tuple

from BaseClasses import Item, ItemClassification, Location, Region, Tutorial
from worlds.AutoWorld import WebWorld, World
from worlds.generic.Rules import add_item_rule
from worlds.LauncherComponents import Component, Type, components, launch as launch_component

from . import rules as R
from .data import (CHARACTERS, CHAR_INDEX, CRAFTS, DUMMY_RECIPES, FILLER_ITEMS, GAME, GOAL_EVENT, ITEM_IDS,
                   ITEM_TABLE, ITEMS, LOCATION_IDS, LOCATIONS, MOVE_LEVELS, MOVE_LOCATIONS, ROOM_ART,
                   ROOM_ITEM, ROOM_LOCATION_PREFIX, SUPER_MOVES, SUPER_LOCATION_NAMES, COOP_LOCATIONS, ROOM_OPTIONS,
                   FILLER_COUNTS, filler_group, GOALS, ENERU, ISLAND_2_ITEMS, ISLAND_5_ITEMS,
                   SHRINE_OFFERING_FILLER)
from .options import OPTION_GROUPS, OPUCOptions

def launch_client(*args: str) -> None:
    from .client import launch
    launch_component(launch, name="OPUCClient", args=args)


components.append(Component("One Piece Unlimited Cruise 1 Client", func=launch_client,
                            component_type=Type.CLIENT, game_name=GAME))

CLASS = {"progression": ItemClassification.progression,
         "progression_skip_balancing": ItemClassification.progression_skip_balancing,
         "useful": ItemClassification.useful, "filler": ItemClassification.filler}

REGIONS = ["Menu", "Prologue Part 1", "Prologue Part 2", "Prologue Part 3", R.P1, R.SUNNY, R.IRON_SPOT,
           "Wooded Isle Mid-Boss", R.P2, R.P2R, "An Unclimbable Area", "An Incomplete Path", "Island Boss",
           R.POST_ENERU, R.SUNNY_CH3, R.G1, R.G2, R.G3, R.G4, R.GBRIDGE, R.GLADDER, R.GPOISON, R.GBOSS,
           R.POST_MORIA, R.CENTRAL]


class OPUCItem(Item):
    game = GAME


class OPUCLocation(Location):
    game = GAME


class OPUCWeb(WebWorld):
    theme = "ocean"
    option_groups = OPTION_GROUPS
    tutorials = [Tutorial("Setup Guide", "Setting up One Piece Unlimited Cruise 1 for Archipelago.",
                          "English", "setup_en.md", "setup/en", ["CaptPurpleHeart"])]


class OPUCWorld(World):
    """
    One Piece Unlimited Cruise Part 1: The Treasure Beneath the Waves. Explore the islands with the
    Straw Hats, craft gear on the Thousand Sunny and power up Gabri to open new paths.
    """
    game = GAME
    web = OPUCWeb()
    options_dataclass = OPUCOptions
    options: OPUCOptions
    item_name_to_id = ITEM_IDS
    location_name_to_id = LOCATION_IDS
    item_name_groups = {
        "Straw Hats": set(CHARACTERS),
        "Shrine Access": {i.name for i in ITEMS if i.kind == "shrine"},
        "Map Fragments": {i.name for i in ITEMS if i.name.startswith("Map ")},
    }
    location_name_groups = {
        "Fishing": {l.name for l in LOCATIONS if l.name.startswith("Fishing - ")},
        "Creatures": {l.name for l in LOCATIONS if l.name.startswith("Creatures - ")},
        "Co-op Moves": {l.name for l in LOCATIONS if l.name.startswith("Co-op - ")},
    }
    origin_region_name = "Menu"

    # Universal Tracker can rebuild this world from the slot data alone (see interpret_slot_data).
    ut_can_gen_without_yaml = True

    def generate_early(self) -> None:
        o = self.options
        passthrough = getattr(self.multiworld, "re_gen_passthrough", {}).get(self.game)
        if passthrough:          # Universal Tracker: same settings as the game it is connected to
            o.starting_character.value = passthrough["starting_character"]
            o.goal.value = passthrough.get("goal", 0)
            o.rod_upgrade_items.value = passthrough.get("rod_upgrade_items", 30)
            o.combine_rod_and_line.value = passthrough.get("combine_rod_and_line", 0)
            for key in ("super_move_locations",
                        "fishsanity", "creaturesanity", "workshop_unlock", "kitchen_unlock", "pharmacy_unlock",
                        "usopp_required_for_art", "sanji_required_for_art", "chopper_required_for_art",
                        "nami_required_for_maps", "robin_required_for_monuments", "franky_required_for_build_sites",
                        "treasure_maps_need_every_fragment", "sea_kings_important",
                        "bag_palette_upgrade_item_type", "cat_burglar_item_type", "light_weight_item_type",
                        "blue_orb_spot_gives_iron_ore"):
                if key in passthrough:
                    getattr(o, key).value = passthrough[key]
            self.fish_locations = list(passthrough.get("fish_locations", []))
            self.creature_locations = list(passthrough.get("creature_locations", []))
        # Islands in the seed: the goal is the last island's boss (Gorge Isle needs Eneru beaten first)
        self.island2 = o.goal.value >= 1
        self.island5 = o.goal.value >= 2
        self.scope_regions = (set(REGIONS) - (set() if self.island2 else R.ISLAND_2_REGIONS)
                              - (set() if self.island5 else R.ISLAND_5_REGIONS)
                              - (set() if o.blue_orb_spot_gives_iron_ore.value else {R.IRON_SPOT}))
        if not passthrough:
            def pick(on: bool, pool: List[str], count: int) -> List[str]:
                pool = [n for n in pool if R.material_in_scope(n, self.scope_regions)]
                return sorted(self.random.sample(pool, min(count, len(pool)))) if on else []
            self.fish_locations = pick(o.fishsanity.value != 0, R.FISH_IN_SCOPE, o.fish_locations.value)
            self.creature_locations = pick(o.creaturesanity.value != 0, R.CREATURES_IN_SCOPE,
                                           o.creature_locations.value)
        self.catch_locations = {f"Fishing - {n}": n for n in self.fish_locations}
        self.catch_locations.update({f"Creatures - {n}": n for n in self.creature_locations})
        self.starting_character = o.starting_character.value
        self.vacuum_orbs = [self.random.randint(80, 85) for _ in range(5)]
        # The Prologue has few locations (enemies don't respawn there), so the vanilla way out of it
        # (Shrine 1) is always placed in this world's first sphere.
        for name in ("Crystal", "Wooded Isle Shrine 1 Access"):
            self.multiworld.local_early_items[self.player][name] = 1

    # ---------------------------------------------------------------------------------- items
    # items whose class follows an option (useful, or progression that skips balancing)
    CLASS_OPTIONS = {"Progressive Item Bag Upgrade": "bag_palette_upgrade_item_type",
                     "Progressive Palette Upgrade": "bag_palette_upgrade_item_type",
                     "Nami - Progressive Cat Burglar": "cat_burglar_item_type",
                     "Brook - Progressive Light Weight": "light_weight_item_type"}

    def create_item(self, name: str) -> OPUCItem:
        d = ITEM_TABLE[name]
        cls = CLASS[d.cls]
        opt = self.CLASS_OPTIONS.get(name)
        if opt and getattr(self.options, opt).value == 1:
            cls = ItemClassification.progression_skip_balancing
        return OPUCItem(name, cls, ITEM_IDS[name], self.player)

    def filler_weights(self) -> Tuple[List[str], List[float]]:
        """Filler Weighting Options: within each group (food / medicine / other) items are weighted by quality
        (or equally) and packages by size (or like singles); each group's total is its slider."""
        if getattr(self, "_filler", None):
            return self._filler
        o = self.options
        groups: Dict[str, List[Tuple[str, float]]] = {"food": [], "medicine": [], "other": []}
        singles = {gid: w for n, gid, w in FILLER_ITEMS if n not in FILLER_COUNTS}
        for n, gid, w in FILLER_ITEMS:
            count = FILLER_COUNTS.get(n, 1)
            if n.split(" of ", 1)[-1] in SHRINE_OFFERING_FILLER:
                continue                    # a shrine asks for it
            if count > 1 and not o.include_bundle_filler.value:
                continue
            base = singles[gid] if o.filler_quality_weighting.value else 1.0
            scale = (w / singles[gid]) if (count > 1 and o.bundle_size_weighting.value) else 1.0
            groups[filler_group(gid)].append((n, base * scale))
        totals = {"food": o.food_filler_weight.value, "medicine": o.medicine_filler_weight.value,
                  "other": o.other_filler_weight.value}
        if not any(totals.values()):
            totals = {"food": 64, "medicine": 27, "other": 9}     # all sliders at 0: use the defaults
        names, weights = [], []
        for g, entries in groups.items():
            s = sum(w for _, w in entries)
            for n, w in entries:
                if totals[g] and s:
                    names.append(n)
                    weights.append(totals[g] * w / s)
        self._filler = (names, weights)
        return self._filler

    def get_filler_item_name(self) -> str:
        names, weights = self.filler_weights()
        return self.random.choices(names, weights)[0]

    def create_items(self) -> None:
        start = CHARACTERS[self.starting_character]
        self.multiworld.push_precollected(self.create_item(start))
        pool: List[OPUCItem] = []
        rod_copies = self.options.rod_upgrade_items.value
        for d in ITEMS:
            count = rod_copies if d.kind in ("rod_level", "rod_line") else d.count
            if d.kind == "rod_line" and self.options.combine_rod_and_line.value:
                count = 0                   # Rod Level items raise the line as well
            if d.kind == "room" and getattr(self.options, ROOM_OPTIONS[d.data][0]).value in (0, 2):
                count = 0                   # this room isn't opened by its own item
            if d.name in ISLAND_2_ITEMS and not self.island2:
                count = 0                   # Gorge Isle isn't in this seed
            if d.name in ISLAND_5_ITEMS and not self.island5:
                count = 0                   # the final island isn't in this seed
            for _ in range(count):
                if d.name != start:
                    pool.append(self.create_item(d.name))
        open_slots = len(self.multiworld.get_unfilled_locations(self.player)) - len(pool)
        if open_slots < 0:
            # Too few locations (e.g. goal Wooded Isle with Super Move Locations off): leave out Determination
            # levels (useful only) until the items fit.
            spare = [i for i in pool if i.name.endswith("Progressive Determination")]
            self.random.shuffle(spare)
            for item in spare[:-open_slots]:
                pool.remove(item)
            open_slots = len(self.multiworld.get_unfilled_locations(self.player)) - len(pool)
        if open_slots < 0:
            raise Exception(f"{self.player_name}: {len(pool)} items but only "
                            f"{len(pool) + open_slots} locations.")
        pool += [self.create_item(self.get_filler_item_name()) for _ in range(open_slots)]
        self.multiworld.itempool += pool

    # -------------------------------------------------------------------------------- regions
    def create_regions(self) -> None:
        regions = {name: Region(name, self.player, self.multiworld) for name in REGIONS}
        self.multiworld.regions += regions.values()
        p = self.player

        def connect(a: str, b: str, rule=None) -> None:
            regions[a].connect(regions[b], f"{a} -> {b}", (lambda s: rule(s, p)) if rule else None)

        connect("Menu", "Prologue Part 1")
        connect("Prologue Part 1", "Prologue Part 2")
        connect("Prologue Part 2", "Prologue Part 3")
        # Out of the Prologue only through Shrine 1. (The Pickaxe route around it is gone: the client holds the
        # Pickaxe back until the first step on the Thousand Sunny, flag 11990; user 2026-10-19.)
        connect("Prologue Part 3", R.P1, lambda s, p: s.has_all(("Wooded Isle Shrine 1 Access", "Crystal"), p))
        connect(R.P1, R.SUNNY)
        if self.options.blue_orb_spot_gives_iron_ore.value:
            connect(R.P1, R.IRON_SPOT, lambda s, p: s.has("Brook", p))
        connect(R.P1, "Wooded Isle Mid-Boss", lambda s, p: s.has("Wooded Isle Shrine 2 Access", p))
        connect("Wooded Isle Mid-Boss", R.P2)
        connect(R.P2, "Island Boss", lambda s, p: s.has("Wooded Isle Shrine 3 Access", p)
                and R.gabri(1)(s, p) and R.net(s, p))
        connect(R.P2, "An Unclimbable Area", lambda s, p: s.has("Pickaxe", p) and R.build_site(1)(s, p)
                and R.gabri(2)(s, p))
        connect(R.P2, R.P2R, R.pickaxe)
        connect(R.P2R, "An Incomplete Path", lambda s, p: R.build_site(2)(s, p)
                and R.gabri(6)(s, p))
        if self.island2:
            # Gorge Isle (user's region map, 2026-10-22). Shrine / build site offerings are part of the way in.
            connect("Island Boss", R.POST_ENERU)
            connect(R.POST_ENERU, R.SUNNY_CH3)
            # Gorge Isle opens with its Log Pose (Next Island menu, from the Sunny); Eneru isn't needed
            # (user tested Gorge Isle before Eneru, 2026-10-22)
            connect(R.SUNNY, R.G1, lambda s, p: s.has(R.GORGE_LOG_POSE, p))
            # The rocks into Part 2 also go if nearby scenery is destroyed and the area reloaded: no Pickaxe
            # needed (user, 2026-10-23). Part 4 still needs it (Build Site 1's Marble is dug up).
            connect(R.G1, R.G2)
            connect(R.G2, R.G3, self.gorge_shrine_1)
            connect(R.G3, R.G4, self.gorge_site_1)
            connect(R.G3, R.GPOISON, R.power_vacuum)
            connect(R.G4, R.GBOSS, self.gorge_shrine_2)
            connect(R.G4, R.GBRIDGE, self.gorge_site_2)
            connect(R.GBRIDGE, R.GLADDER, self.gorge_site_3)
            # Ladder Path -> Part 3 (Build Site 4) is one-way and Part 3 is already reachable: no entrance needed
            # entrance rules that look at other regions (materials, crafting rooms)
            for e in [x for r in (R.G2, R.G3, R.G4, R.GBRIDGE) for x in regions[r].exits]:
                for reg in regions.values():
                    self.multiworld.register_indirect_condition(reg, e)
        for e in list(regions[R.P2].exits):      # the net needs the Sunny (Workshop) region
            self.multiworld.register_indirect_condition(regions[R.SUNNY], e)

        if self.island5:
            connect(R.GBOSS, R.POST_MORIA)
            connect(R.POST_MORIA, R.SUNNY_CH3)  # Gecko Moria first opens the same (chapter 4); not when he's the goal
            # The final island: its Log Pose, then the Final Door (500: 1000 of five Energy colours = Gabri 13)
            connect(R.SUNNY, R.CENTRAL, lambda s, p: s.has(R.CENTRAL_LOG_POSE, p))
        goal_name, _flag, goal_region = GOALS[self.options.goal.value]
        for loc in LOCATIONS:
            if loc.region not in self.scope_regions or loc.name == goal_name:
                continue                    # island not in this seed, or the goal (an event below)
            if loc.name in SUPER_LOCATION_NAMES and not self.options.super_move_locations.value:
                continue                    # Super Move Locations: off
            if loc.check[0] == "catch" and loc.name not in self.catch_locations:
                continue                    # fishing / creature location not picked for this seed
            if loc.check[0] == "craft" and not self.craft_has_location(loc.check[1], loc.check[2]):
                continue                    # room opens after the goal, or an ingredient isn't on Island 1
            regions[loc.region].locations.append(OPUCLocation(p, loc.name, LOCATION_IDS[loc.name], regions[loc.region]))

        goal = OPUCLocation(p, goal_name, None, regions[goal_region])
        goal.place_locked_item(OPUCItem("Victory", ItemClassification.progression, None, p))
        regions[goal_region].locations.append(goal)

    # Gorge Isle shrines / build sites: access item, Gabri level, offered items (event/epoint/zone2.bin)
    @staticmethod
    def gorge_shrine_1(s, p) -> bool:   # The Silent Ancient Creature: 3 Mysterious Bone, 1 Healing Capsule
        return (s.has("Gorge Isle Shrine 1 Access", p) and R.gabri(1)(s, p)
                and R.has_material("Mysterious Bone")(s, p) and R.has_material("Healing Capsule")(s, p))

    @staticmethod
    def gorge_shrine_2(s, p) -> bool:   # The Ruins in the Sunset: 30 Gunpowder, 3 Clay
        return (s.has("Gorge Isle Shrine 2 Access", p) and R.gabri(3)(s, p)
                and R.has_material("Gunpowder")(s, p) and R.has_material("Clay")(s, p))

    @staticmethod
    def gorge_site_1(s, p) -> bool:     # An Incomplete Path: 2 Marble
        return R.build_site(1, "Gorge Isle")(s, p) and R.gabri(3)(s, p) and R.has_material("Marble")(s, p)

    @staticmethod
    def gorge_site_2(s, p) -> bool:     # An Incomplete Path (2): 3 Marble
        return R.build_site(2, "Gorge Isle")(s, p) and R.gabri(3)(s, p) and R.has_material("Marble")(s, p)

    @staticmethod
    def gorge_site_3(s, p) -> bool:     # An Unclimbable Path: 5 Bamboo
        return R.build_site(3, "Gorge Isle")(s, p) and R.gabri(5)(s, p) and R.has_material("Bamboo")(s, p)

    @staticmethod
    def gorge_site_4(s, p) -> bool:     # An Incomplete Path (3): 5 Marble
        return R.build_site(4, "Gorge Isle")(s, p) and R.gabri(2)(s, p) and R.has_material("Marble")(s, p)

    def room_has_locations(self, room: str) -> bool:
        """Vanilla Kitchen / Pharmacy open after Eneru: only with Gorge Isle in the seed."""
        return room == "workshop" or getattr(self.options, ROOM_OPTIONS[room][0]).value != 0 or self.island2

    def craft_has_location(self, room: str, row: int) -> bool:
        """Room usable before the goal and every ingredient reachable in the seed's islands."""
        return self.room_has_locations(room) and R.craft_in_scope(room, row, self.scope_regions)

    # ---------------------------------------------------------------------------------- rules
    def set_rules(self) -> None:
        p = self.player
        mw = self.multiworld

        def rule(name: str, r) -> None:
            mw.get_location(name, p).access_rule = lambda s: r(s, p)

        o = self.options
        for c, m, req in MOVE_LOCATIONS:
            who = CHARACTERS[CHAR_INDEX[c]]
            for lv in MOVE_LEVELS:
                name = f"{c} - {m} Level {lv}"
                if (c, m) in SUPER_MOVES and o.super_move_locations.value == 0:
                    continue                # no super move locations in this seed
                rule(name, lambda s, p, who=who, req=req: s.has(who, p) and all(s.has(n, p, k) for n, k in req))
                if (c, m) in SUPER_MOVES and o.super_move_locations.value == 2:
                    add_item_rule(mw.get_location(name, p), lambda item: not item.advancement)

        for m, _cid, item, members in (COOP_LOCATIONS if o.super_move_locations.value else []):
            need = (item,) + tuple(CHARACTERS[CHAR_INDEX[c]] for c in members)
            for lv in MOVE_LEVELS:
                name = f"Co-op - {m} Level {lv}"
                rule(name, lambda s, p, need=need: s.has_all(need, p))
                if o.super_move_locations.value == 2:      # co-op moves count as supers
                    add_item_rule(mw.get_location(name, p), lambda item: not item.advancement)

        rule("Wooded Isle Shrine - An Odd Stone & A Strange Creature",
             lambda s, p: s.has_all(("Wooded Isle Shrine 1 Access", "Crystal"), p))
        rule("Prologue Part 3 Completed", lambda s, p: s.has_all(("Wooded Isle Shrine 1 Access", "Crystal"), p))
        rule("Wooded Isle Monument - Far, Far Away", lambda s, p: R.pickaxe(s, p) and R.monument(s, p))
        rule("Wooded Isle Monument - Eternity", R.monument)
        rule("Wooded Isle - Nectar Chest", R.pickaxe)
        rule("Wooded Isle - Restorative Drug Chest", R.pickaxe)
        rule("Wooded Isle - Steel Chain Chest", lambda s, p: s.has("Pickaxe", p) and
             R.map_fragment(("Map 8, Fragment 1", "Map 8, Fragment 2", "Map 8, Fragment 3"))(s, p))
        rule("Wooded Isle - Flour Chest", lambda s, p: s.has("Pickaxe", p) and
             R.map_fragment(("Map 2, Fragment 1", "Map 2, Fragment 2", "Map 2, Fragment 3", "Map 2, Fragment 4"))(s, p))
        rule("Wooded Isle Shrine - An Enormous Boulder", lambda s, p: s.has("Wooded Isle Shrine 2 Access", p))
        rule("Wooded Isle Shrine - What Lies Asleep in the Amber",
             lambda s, p: s.has("Wooded Isle Shrine 3 Access", p) and R.gabri(1)(s, p) and R.net(s, p))
        rule("Wooded Isle Build Site - An Unclimbable Area",
             lambda s, p: s.has("Pickaxe", p) and R.build_site(1)(s, p) and R.gabri(2)(s, p))
        rule("Wooded Isle Build Site - An Incomplete Path",
             lambda s, p: R.build_site(2)(s, p) and R.gabri(6)(s, p))

        if self.island2:
            rule("Gorge Isle - The Silent Ancient Creature", self.gorge_shrine_1)
            rule("Gorge Isle - The Ruins in the Sunset", self.gorge_shrine_2)
            rule("Gorge Isle - An Incomplete Path", self.gorge_site_1)
            rule("Gorge Isle - An Incomplete Path (2)", self.gorge_site_2)
            rule("Gorge Isle - An Unclimbable Path", self.gorge_site_3)
            rule("Gorge Isle - An Incomplete Path (3)", self.gorge_site_4)
            rule("Gorge Isle Monument - Creation", R.monument)
            # The Wherever Cannon: 300 Red (Gabri 3), 7 Iron Scrap, 10 Gunpowder
            rule("Thousand Sunny - Wherever Cannon", lambda s, p: R.build_site(1, "Thousand Sunny")(s, p)
                 and R.gabri(3)(s, p) and R.has_material("Iron Scrap")(s, p) and R.has_material("Gunpowder")(s, p))
            rule("Gorge Isle Monument - Hope", R.monument)
            # treasure map chests are dug up (Pickaxe, as on Wooded Isle)
            for chest, m, n in (("Golden Fruit", 4, 5), ("Mask Fragment", 6, 3), ("Enhanced Reel", 1, 4)):
                frags = tuple(f"Map {m}, Fragment {k + 1}" for k in range(n))
                rule(f"Gorge Isle - {chest} Chest",
                     lambda s, p, frags=frags: s.has("Pickaxe", p) and R.map_fragment(frags)(s, p))

        for room, row, result, _dummy in CRAFTS:
            if not self.craft_has_location(room, row):
                continue
            # room open, Art level (+ its owner with that option), key items, ingredients found or crafted
            name = f"{ROOM_LOCATION_PREFIX[room]} {result}"
            rule(name, R.craftable(room, row))
            if R.needs_sea_king(room, row) and not o.sea_kings_important.value:
                add_item_rule(mw.get_location(name, p), lambda item: not item.advancement)

        for name, thing in self.catch_locations.items():
            rule(name, R.has_material(thing))
            unimportant = (o.fishsanity.value if name.startswith("Fishing") else o.creaturesanity.value) == 2
            if thing in R.SEA_KINGS and not o.sea_kings_important.value:
                unimportant = True
            if unimportant:
                add_item_rule(mw.get_location(name, p), lambda item: not item.advancement)

        if self.island5:
            rule("Central Isle Monument - Inferno", R.monument)
            # final boss: the Final Door needs 1000 of five Energy colours (only reachable at Gabri level 13)
            rule(GOALS[2][0], lambda s, p: s.has("The Final Door", p) and R.gabri(13)(s, p))
        mw.completion_condition[p] = lambda s: s.has("Victory", p)

    @staticmethod
    def interpret_slot_data(slot_data: Dict[str, Any]) -> Dict[str, Any]:
        """Universal Tracker: hand the slot data back to generate_early (as re_gen_passthrough)."""
        return slot_data

    def fill_slot_data(self) -> Dict[str, Any]:
        return {
            "starting_character": self.starting_character,
            "goal": self.options.goal.value,
            "rod_upgrade_items": self.options.rod_upgrade_items.value,
            "combine_rod_and_line": self.options.combine_rod_and_line.value,
            "move_exp_multiplier": self.options.move_exp_multiplier.value,
            "super_move_locations": self.options.super_move_locations.value,
            # the Sunny's 5 dust spots (Map 10 fragments in vanilla) give these Orbs (Red..Gold = 80-85)
            "vacuum_orbs": self.vacuum_orbs,
            "fishsanity": self.options.fishsanity.value,
            "creaturesanity": self.options.creaturesanity.value,
            "fish_locations": self.fish_locations,
            "creature_locations": self.creature_locations,
            "dummy_recipes": DUMMY_RECIPES,
            "craft_locations": [[room, row] for room, row, _, _ in CRAFTS if self.craft_has_location(room, row)],
            "nami_required_for_maps": self.options.nami_required_for_maps.value,
            "treasure_maps_need_every_fragment": self.options.treasure_maps_need_every_fragment.value,
            "sea_kings_important": self.options.sea_kings_important.value,
            "disable_food_diminishing_returns": self.options.disable_food_diminishing_returns.value,
            "traps_never_expire": self.options.traps_never_expire.value,
            "iron_scrap_gives_gold_energy": self.options.iron_scrap_gives_gold_energy.value,
            "blue_orb_spot_gives_iron_ore": self.options.blue_orb_spot_gives_iron_ore.value,
            "bag_palette_upgrade_item_type": self.options.bag_palette_upgrade_item_type.value,
            "cat_burglar_item_type": self.options.cat_burglar_item_type.value,
            "light_weight_item_type": self.options.light_weight_item_type.value,
            "fast_traps": self.options.fast_traps.value,
            "recipes_discovered_through_arts": self.options.recipes_discovered_through_arts.value,
            "recipes_spoil_locations": self.options.recipes_spoil_locations.value,
            "robin_required_for_monuments": self.options.robin_required_for_monuments.value,
            "franky_required_for_build_sites": self.options.franky_required_for_build_sites.value,
            "workshop_unlock": self.options.workshop_unlock.value,
            "kitchen_unlock": self.options.kitchen_unlock.value,
            "pharmacy_unlock": self.options.pharmacy_unlock.value,
            "usopp_required_for_art": self.options.usopp_required_for_art.value,
            "sanji_required_for_art": self.options.sanji_required_for_art.value,
            "chopper_required_for_art": self.options.chopper_required_for_art.value,
        }
