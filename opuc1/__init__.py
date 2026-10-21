"""
One Piece Unlimited Cruise Part 1 (Wii, PAL ROUPAF) - Archipelago world.
Island 1 foundation test: Prologue, Wooded Isle and the Thousand Sunny. Goal: defeat the Island 1 boss.
"""
from typing import Any, Dict, List, Tuple

from BaseClasses import Item, ItemClassification, Location, Region, Tutorial
from worlds.AutoWorld import WebWorld, World
from worlds.generic.Rules import add_item_rule
from worlds.LauncherComponents import Component, Type, components, launch as launch_component

from . import rules as R
from .data import (CHARACTERS, CHAR_INDEX, CRAFTS, DUMMY_RECIPES, FILLER_ITEMS, GAME, GOAL_EVENT, ITEM_IDS,
                   ITEM_TABLE, ITEMS, LOCATION_IDS, LOCATIONS, MOVE_LEVELS, MOVE_LOCATIONS, ROOM_ART,
                   ROOM_ITEM, ROOM_LOCATION_PREFIX, SUPER_MOVES, COOP_LOCATIONS, ROOM_OPTIONS,
                   FILLER_COUNTS, filler_group)
from .options import OPTION_GROUPS, OPUCOptions

def launch_client(*args: str) -> None:
    from .client import launch
    launch_component(launch, name="OPUCClient", args=args)


components.append(Component("One Piece Unlimited Cruise 1 Client", func=launch_client,
                            component_type=Type.CLIENT, game_name=GAME))

CLASS = {"progression": ItemClassification.progression,
         "progression_skip_balancing": ItemClassification.progression_skip_balancing,
         "useful": ItemClassification.useful, "filler": ItemClassification.filler}

REGIONS = ["Menu", "Prologue Part 1", "Prologue Part 2", "Prologue Part 3", R.P1, R.SUNNY,
           "Wooded Isle Mid-Boss", R.P2, R.P2R, "An Unclimbable Area", "An Incomplete Path", "Island Boss"]


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
            o.rod_upgrade_items.value = passthrough.get("rod_upgrade_items", 30)
            o.combine_rod_and_line.value = passthrough.get("combine_rod_and_line", 0)
            for key in ("move_locations_important", "super_move_locations_important", "move_importance_max_level",
                        "fishsanity", "creaturesanity", "workshop_unlock", "kitchen_unlock", "pharmacy_unlock",
                        "usopp_required_for_art", "sanji_required_for_art", "chopper_required_for_art",
                        "nami_required_for_maps", "robin_required_for_monuments", "franky_required_for_build_sites",
                        "treasure_maps_need_every_fragment", "sea_kings_important"):
                if key in passthrough:
                    getattr(o, key).value = passthrough[key]
            self.fish_locations = list(passthrough.get("fish_locations", []))
            self.creature_locations = list(passthrough.get("creature_locations", []))
        else:
            def pick(on: bool, pool: List[str], count: int) -> List[str]:
                return sorted(self.random.sample(pool, min(count, len(pool)))) if on else []
            self.fish_locations = pick(o.fishsanity.value != 0, R.FISH_IN_SCOPE, o.fish_locations.value)
            self.creature_locations = pick(o.creaturesanity.value != 0, R.CREATURES_IN_SCOPE,
                                           o.creature_locations.value)
        self.catch_locations = {f"Fishing - {n}": n for n in self.fish_locations}
        self.catch_locations.update({f"Creatures - {n}": n for n in self.creature_locations})
        self.starting_character = o.starting_character.value
        # The Prologue has few locations (enemies don't respawn there), so the vanilla way out of it
        # (Shrine 1) is always placed in this world's first sphere.
        for name in ("Crystal", "Wooded Isle Shrine 1 Access"):
            self.multiworld.local_early_items[self.player][name] = 1

    # ---------------------------------------------------------------------------------- items
    def create_item(self, name: str) -> OPUCItem:
        d = ITEM_TABLE[name]
        return OPUCItem(name, CLASS[d.cls], ITEM_IDS[name], self.player)

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
            for _ in range(count):
                if d.name != start:
                    pool.append(self.create_item(d.name))
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
        connect(R.P1, "Wooded Isle Mid-Boss", lambda s, p: s.has("Wooded Isle Shrine 2 Access", p))
        connect("Wooded Isle Mid-Boss", R.P2)
        connect(R.P2, "Island Boss", lambda s, p: s.has("Wooded Isle Shrine 3 Access", p)
                and R.gabri(1)(s, p) and R.net(s, p))
        connect(R.P2, "An Unclimbable Area", lambda s, p: s.has("Pickaxe", p) and R.build_site(1)(s, p)
                and R.gabri(2)(s, p))
        connect(R.P2, R.P2R, R.pickaxe)
        connect(R.P2R, "An Incomplete Path", lambda s, p: R.build_site(2)(s, p)
                and R.gabri(6)(s, p))

        for loc in LOCATIONS:
            if loc.check[0] == "catch" and loc.name not in self.catch_locations:
                continue                    # fishing / creature location not picked for this seed
            if loc.check[0] == "craft" and not self.craft_has_location(loc.check[1], loc.check[2]):
                continue                    # room opens after the goal, or an ingredient isn't on Island 1
            regions[loc.region].locations.append(OPUCLocation(p, loc.name, LOCATION_IDS[loc.name], regions[loc.region]))

        goal = OPUCLocation(p, GOAL_EVENT, None, regions["Island Boss"])
        goal.place_locked_item(OPUCItem("Victory", ItemClassification.progression, None, p))
        regions["Island Boss"].locations.append(goal)

    def room_has_locations(self, room: str) -> bool:
        return room == "workshop" or getattr(self.options, ROOM_OPTIONS[room][0]).value != 0

    def craft_has_location(self, room: str, row: int) -> bool:
        """Room usable before the goal and every ingredient in scope (no Gunpowder on Island 1)."""
        return self.room_has_locations(room) and R.craft_in_scope(room, row)

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
                rule(name, lambda s, p, who=who, req=req: s.has(who, p) and all(s.has(n, p, k) for n, k in req))
                important = (o.move_locations_important.value
                             and ((c, m) not in SUPER_MOVES or o.super_move_locations_important.value)
                             and lv <= o.move_importance_max_level.value)
                if not important:
                    add_item_rule(mw.get_location(name, p), lambda item: not item.advancement)

        for m, _cid, item, members in COOP_LOCATIONS:
            need = (item,) + tuple(CHARACTERS[CHAR_INDEX[c]] for c in members)
            for lv in MOVE_LEVELS:
                name = f"Co-op - {m} Level {lv}"
                rule(name, lambda s, p, need=need: s.has_all(need, p))
                important = (o.move_locations_important.value and o.super_move_locations_important.value
                             and lv <= o.move_importance_max_level.value)    # co-op moves count as supers
                if not important:
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

        for room, row, result, _dummy in CRAFTS:
            if not self.craft_has_location(room, row):
                continue
            mats, keys = R.RECIPE_NEEDS[(room, row)]
            checks = [R.has_material(m) for m in mats]
            _u, art_opt, ci = ROOM_OPTIONS[room]
            # Art levels wait for the room's owner when that option is on (client holds them back)
            if row // 8 and getattr(o, art_opt).value:
                keys = keys + (CHARACTERS[ci],)
            name = f"{ROOM_LOCATION_PREFIX[room]} {result}"
            rule(name,
                 lambda s, p, room=room, row=row, keys=keys, checks=checks:
                 R.room_open(s, p, room) and s.has(ROOM_ART[room], p, row // 8)
                 and s.has_all(keys, p) and all(c(s, p) for c in checks))
            if R.needs_sea_king(room, row) and not o.sea_kings_important.value:
                add_item_rule(mw.get_location(name, p), lambda item: not item.advancement)

        for name, thing in self.catch_locations.items():
            rule(name, R.has_material(thing))
            unimportant = (o.fishsanity.value if name.startswith("Fishing") else o.creaturesanity.value) == 2
            if thing in R.SEA_KINGS and not o.sea_kings_important.value:
                unimportant = True
            if unimportant:
                add_item_rule(mw.get_location(name, p), lambda item: not item.advancement)

        mw.completion_condition[p] = lambda s: s.has("Victory", p)

    @staticmethod
    def interpret_slot_data(slot_data: Dict[str, Any]) -> Dict[str, Any]:
        """Universal Tracker: hand the slot data back to generate_early (as re_gen_passthrough)."""
        return slot_data

    def fill_slot_data(self) -> Dict[str, Any]:
        return {
            "starting_character": self.starting_character,
            "rod_upgrade_items": self.options.rod_upgrade_items.value,
            "combine_rod_and_line": self.options.combine_rod_and_line.value,
            "move_exp_multiplier": self.options.move_exp_multiplier.value,
            "move_locations_important": self.options.move_locations_important.value,
            "super_move_locations_important": self.options.super_move_locations_important.value,
            "move_importance_max_level": self.options.move_importance_max_level.value,
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
