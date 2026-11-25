"""
One Piece Unlimited Cruise Part 1 (Wii, PAL ROUPAF) - Archipelago world.
Prologue, Thousand Sunny, Wooded Isle, Gorge Isle, Iceberg Isle, Cave Isle and Central Isle (every island in every
seed). Goal: "God" Eneru, Gecko Moria, Aokiji, Blackbeard or the Doom Guardian.
"""
from typing import Any, Dict, List, Tuple

from BaseClasses import Item, ItemClassification, Location, Region, Tutorial
from worlds.AutoWorld import WebWorld, World
from worlds.generic.Rules import add_item_rule
from worlds.LauncherComponents import Component, Type, components, icon_paths, launch as launch_component

from . import rules as R
from .data import (COSTUME_CHOICES, CHARACTERS, CHAR_INDEX, CRAFTS, DUMMY_RECIPES, FILLER_ITEMS, GAME, GOAL_EVENT, ITEM_IDS,
                   ITEM_TABLE, ITEMS, LOCATION_IDS, LOCATIONS, MOVE_LEVELS, MOVE_LOCATIONS, ROOM_ART,
                   ROOM_ITEM, ROOM_LOCATION_PREFIX, SUPER_MOVES, SUPER_LOCATION_NAMES, COOP_LOCATIONS, ROOM_OPTIONS,
                   FILLER_COUNTS, filler_group, GOALS, SHRINE_OFFERING_FILLER, TRAP_ITEMS, ACTIVE_TRAPS,
                   GABRI_COLOUR_ITEMS, gabri_colour_copies, EXTRA_POOLS, EXTRA_SLOTS, FRANKY_AP_ROWS, FRANKY_TRADES,
                   RARITY_WEIGHTS, INGREDIENT_COUNT_WEIGHTS, POOL_ITEM_IDS, amount_choices, EXTRA_RECIPE_LOCATIONS,
                   OLD_GOLD_COIN, final_door_bosses)
from .options import OPTION_GROUPS, OPUCOptions

def launch_client(*args: str) -> None:
    from .client import launch
    launch_component(launch, name="OPUCClient", args=args)


# Launcher icon (user's image, 0.30.3)
icon_paths["opuc1"] = f"ap:{__name__}/icon.png"
components.append(Component("One Piece Unlimited Cruise 1 Client", func=launch_client,
                            component_type=Type.CLIENT, game_name=GAME, icon="opuc1"))

CLASS = {"progression": ItemClassification.progression,
         "progression_skip_balancing": ItemClassification.progression_skip_balancing,
         "useful": ItemClassification.useful, "filler": ItemClassification.filler,
         "trap": ItemClassification.trap}

REGIONS = ["Menu", "Prologue Part 1", "Prologue Part 2", "Prologue Part 3", R.P1, R.SUNNY, R.IRON_SPOT,
           "Wooded Isle Mid-Boss", R.P2, R.P2R, "An Unclimbable Area", "An Incomplete Path", "Island Boss",
           R.POST_ENERU, R.SUNNY_CH3, R.G1, R.G2, R.G3, R.G4, R.GBRIDGE, R.GLADDER, R.GPOISON, R.GBOSS,
           R.POST_MORIA, R.CENTRAL, R.I1, R.I2, R.I3, R.I4, R.I5, R.I6, R.ILADDER, R.IBOSS, R.POST_AOKIJI,
           R.C1, R.C2, R.CPOISON, R.CWATER, R.CMID, R.CBOSS, R.CSECRET, R.POST_BLACKBEARD,
           R.WHIDDEN, R.GHIDDEN, R.GSECRET, R.IOBST1, R.IOBST2]


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
        "Traps": set(ACTIVE_TRAPS),
        "Gabri Energy": set(GABRI_COLOUR_ITEMS) | {"Progressive Gabri Level"},
        "Old Gold Coins": {i.name for i in ITEMS if i.kind == "filler" and i.data["item"] == OLD_GOLD_COIN},
    }
    location_name_groups = {
        "Fishing": {l.name for l in LOCATIONS if l.name.startswith("Fishing - ")},
        "Creatures": {l.name for l in LOCATIONS if l.name.startswith("Creatures - ")},
        "Co-op Moves": {l.name for l in LOCATIONS if l.name.startswith("Co-op - ")},
        "Materials": {l.name for l in LOCATIONS if l.check[0] == "material"},
        "Extra Recipes": {n for n in EXTRA_RECIPE_LOCATIONS.values() if " - Extra Recipe #" in n},
        "Franky's Supplies": {n for n in EXTRA_RECIPE_LOCATIONS.values() if n.startswith("Franky's Supplies")},
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
            for key in ("super_move_locations", "materialsanity", "gabri_energy_items", "gabri_level_items",
                        "fishsanity", "creaturesanity", "workshop_unlock", "kitchen_unlock", "pharmacy_unlock",
                        "usopp_required_for_art", "sanji_required_for_art", "chopper_required_for_art",
                        "nami_required_for_maps", "robin_required_for_monuments", "franky_required_for_build_sites",
                        "treasure_maps_need_every_fragment", "include_gunpowder_logic",
                        "enemy_gunpowder_drop_logic", "enemy_gunpowder_drop_rate",
                        "bag_palette_upgrade_item_type", "cat_burglar_item_type", "light_weight_item_type",
                        "flower_power_item_type",
                        "blue_orb_spot_gives_iron_ore", "starting_gabri_energy", "franky_supplies",
                        "franky_supplies_unlock", "franky_required_for_art", "extra_crafting_recipes",
                        "extra_final_door_requirement", "wherever_cannon_unlock"):
                if key in passthrough:
                    getattr(o, key).value = passthrough[key]
            if "starting_gabri_energy" not in passthrough:
                o.starting_gabri_energy.value = 1          # 0.28.0 - 0.29.x seeds: 1 Blue bar
            for key in ("franky_supplies", "extra_crafting_recipes"):
                if key not in passthrough:
                    getattr(o, key).value = 0              # seeds from before 0.30.0
            self.fish_locations = list(passthrough.get("fish_locations", []))
            self.creature_locations = list(passthrough.get("creature_locations", []))
        # Every island is in every seed (user, 2026-10-28). Only the region after the goal boss is left out
        # (and the Doom Guardian unless he is the goal).
        self.post_goal = R.POST_GOAL.get(o.goal.value)
        self.scope_regions = (set(REGIONS) - {self.post_goal}
                              - (set() if o.blue_orb_spot_gives_iron_ore.value else {R.IRON_SPOT}))
        if not passthrough:
            def pick(on: bool, pool: List[str], count: int) -> List[str]:
                pool = [n for n in pool if R.material_in_scope(n, self.scope_regions)]
                return sorted(self.random.sample(pool, min(count, len(pool)))) if on else []
            self.fish_locations = pick(o.fishsanity.value != 0, R.FISH_IN_SCOPE, o.fish_locations.value)
            self.creature_locations = pick(o.creaturesanity.value != 0, R.CREATURES_IN_SCOPE,
                                           o.creature_locations.value)
        if passthrough:
            names = {gid: n for n, gid in POOL_ITEM_IDS.items()}
            self.extra_recipes = {(room, row): [(names[gid], n) for gid, n in ing]
                                  for room, row, ing in passthrough.get("extra_recipes", [])}
        else:
            self.extra_recipes = self.make_extra_recipes()
        self.catch_locations = {f"Fishing - {n}": n for n in self.fish_locations}
        self.catch_locations.update({f"Creatures - {n}": n for n in self.creature_locations})
        self.starting_character = o.starting_character.value
        self.vacuum_orbs = [self.random.randint(80, 85) for _ in range(5)]
        # The Prologue has few locations (enemies don't respawn there), so the vanilla way out of it
        # (Shrine 1) is always placed in this world's first sphere.
        for name in ("Crystal", "Wooded Isle Shrine 1 Access"):
            self.multiworld.local_early_items[self.player][name] = 1
        # Early item options (0.25.0): first sphere of the multiworld
        early = self.multiworld.early_items[self.player]
        for opt, name in ((o.early_pickaxe, "Pickaxe"), (o.early_bug_catcher_net, "Broken Bug-Catcher Net"),
                          (o.early_fishing_rod, "Fishing Rod"), (o.early_vacuum_cleaner, "Progressive Vacuum Cleaner")):
            if opt.value and name != CHARACTERS[self.starting_character]:
                early[name] = 1
        if o.early_bag_upgrade.value:
            early["Progressive Item Bag Upgrade"] = o.early_bag_upgrade.value

    def make_extra_recipes(self) -> Dict[Tuple[str, int], List[Tuple[str, int]]]:
        """Random recipes (0.30.0) for the empty rows (Extra Crafting Recipes) and Franky's Archipelago Trades: 1-4
        different ingredients (20 / 50 / 25 / 5%), each from the room's pool: a rarity first (Common 45% ...
        Legendary 2%, among the rarities left), then an ingredient of that rarity, then its amount. Only ingredients
        this seed can get (found, or crafted from such)."""
        o = self.options
        rooms = list(EXTRA_SLOTS.items()) if o.extra_crafting_recipes.value else []
        if o.franky_supplies.value:
            rooms.append(("franky", FRANKY_AP_ROWS))
        out: Dict[Tuple[str, int], List[Tuple[str, int]]] = {}
        counts, count_w = list(INGREDIENT_COUNT_WEIGHTS), list(INGREDIENT_COUNT_WEIGHTS.values())
        for room, rows in rooms:
            pool = [x for x in EXTRA_POOLS[room] if R.material_in_scope(x[0], self.scope_regions)]
            for row in rows:
                left = list(pool)
                picked: List[Tuple[str, int]] = []
                for _ in range(min(self.random.choices(counts, count_w)[0], len(left))):
                    tiers = sorted({r for _n, r, _a in left}, key=list(RARITY_WEIGHTS).index)
                    tier = self.random.choices(tiers, [RARITY_WEIGHTS[t] for t in tiers])[0]
                    entry = self.random.choice([x for x in left if x[1] == tier])
                    left.remove(entry)
                    picked.append((entry[0], self.random.choice(amount_choices(entry[2]))))
                out[(room, row)] = picked
        return out

    # ---------------------------------------------------------------------------------- items
    # items whose class follows an option (useful, or progression that skips balancing)
    CLASS_OPTIONS = {"Progressive Item Bag Upgrade": "bag_palette_upgrade_item_type",
                     "Progressive Palette Upgrade": "bag_palette_upgrade_item_type",
                     "Nami - Progressive Cat Burglar": "cat_burglar_item_type",
                     "Brook - Progressive Light Weight": "light_weight_item_type",
                     "Robin - Progressive Flower Flower Power": "flower_power_item_type"}

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
            if gid == OLD_GOLD_COIN and not o.franky_supplies.value:
                continue                    # Old Gold Coins are only filler with Franky's Supplies
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
        if o.include_traps.value and o.trap_filler_weight.value:
            groups["trap"] = [(n, 1.0) for n in ACTIVE_TRAPS]      # every trap equally likely
            totals["trap"] = o.trap_filler_weight.value
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
            if d.kind == "room" and getattr(self.options, ROOM_OPTIONS[d.data][0]).value in (0, 2, 4):
                count = 0                   # this room isn't opened by its own item
            if d.data == "franky" and not self.options.franky_supplies.value:
                count = 0                   # no Franky's Supplies in this seed
            if d.name == "The Final Door" and self.options.goal.value != 2:
                count = 0                   # the Doom Guardian is only fought with his goal
            cannon = self.options.wherever_cannon_unlock.value
            if (d.name == "Thousand Sunny Build Site 1 Access" and cannon) or (d.kind == "cannon" and cannon != 1):
                count = 0                   # Wherever Cannon Unlock: its build site, or the cannon itself
            if d.kind == "cannon" and cannon == 2:
                self.multiworld.push_precollected(self.create_item(d.name))
            per_colour = bool(self.options.gabri_energy_items.value)
            if (d.kind == "gabri" and per_colour) or (d.kind == "gabri_colour" and not per_colour):
                count = 0                   # Gabri Energy Items: levels or one item per colour bar
            elif d.kind == "gabri_colour":
                count = gabri_colour_copies(d.data, self.options.gabri_level_items.value,
                                            self.options.starting_gabri_energy.value)
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
    @staticmethod
    def prologue_exit(s, p) -> bool:
        """Out of the Prologue: Wooded Isle Shrine 1 with the Crystal."""
        return s.has_all(("Wooded Isle Shrine 1 Access", "Crystal"), p)

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
        connect("Prologue Part 3", R.P1, self.prologue_exit)
        connect(R.P1, R.SUNNY)
        if self.options.blue_orb_spot_gives_iron_ore.value:
            connect(R.P1, R.IRON_SPOT, lambda s, p: s.has("Brook", p))
        # Shrine 2 (200 Blue): free at Gabri level 0, but with per-colour Energy (Blue starts at 1) it needs Blue
        connect(R.P1, "Wooded Isle Mid-Boss", lambda s, p: s.has("Wooded Isle Shrine 2 Access", p) and R.energy(100)(s, p))
        connect("Wooded Isle Mid-Boss", R.P2)
        connect(R.P2, "Island Boss", lambda s, p: s.has("Wooded Isle Shrine 3 Access", p)
                and R.energy(101)(s, p) and R.net(s, p))
        connect(R.P2, "An Unclimbable Area", lambda s, p: s.has("Pickaxe", p) and R.build_site(1)(s, p)
                and R.energy(111)(s, p))
        connect(R.P2, R.P2R, R.rock_path)         # rock path: Pickaxe or Gunpowder (0.24.0)
        connect(R.P2R, "An Incomplete Path", lambda s, p: R.build_site(2)(s, p)
                and R.energy(112)(s, p))
        # The region after each island boss also opens the Sunny's chapter-3 rooms (chapter = latest boss beaten);
        # the goal boss has no "after" region.
        for boss, post in (("Island Boss", R.POST_ENERU), (R.GBOSS, R.POST_MORIA), (R.IBOSS, R.POST_AOKIJI),
                           (R.CBOSS, R.POST_BLACKBEARD)):
            if post != self.post_goal:
                connect(boss, post)
                connect(post, R.SUNNY_CH3)
        # Gorge Isle (user's region map, 2026-10-22). Shrine / build site offerings are part of the way in.
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
        # the net needs the Sunny (Workshop) region; Gunpowder (P2 -> P2R) can come from anywhere
        for e in list(regions[R.P2].exits):
            for reg in regions.values():
                self.multiworld.register_indirect_condition(reg, e)

        # Iceberg Isle (user's region map, 2026-10-28)
        connect(R.SUNNY, R.I1, lambda s, p: s.has(R.ICEBERG_LOG_POSE, p))
        # ice rock routes: Pickaxe or Gunpowder (0.24.0)
        connect(R.I1, R.I2, lambda s, p: R.ice_path(s, p) or self.iceberg_site_1(s, p))
        connect(R.I2, R.I3, self.iceberg_shrine_1)
        connect(R.I3, R.I4, R.ice_path)          # Ice Rock paths: Pickaxe, Gunpowder or a fire attack (0.25.18)
        connect(R.I4, R.I5, R.ice_path)
        connect(R.I4, R.ILADDER, self.iceberg_site_2)
        connect(R.I5, R.I6, self.iceberg_shrine_2)
        connect(R.I6, R.IBOSS, R.power_vacuum)
        for e in [x for r in (R.I1, R.I2, R.I3, R.I4, R.I5) for x in regions[r].exits]:
            for reg in regions.values():
                self.multiworld.register_indirect_condition(reg, e)
        # Cave Isle (user's notes 2026-11-06). Part 2 past a rock: the Pickaxe or Gunpowder (user, 0.27.0).
        connect(R.SUNNY, R.C1, lambda s, p: s.has(R.CAVE_LOG_POSE, p))
        connect(R.C1, R.C2, R.rock_path)
        connect(R.C2, R.CPOISON, R.power_vacuum)
        connect(R.C2, R.CWATER, lambda s, p: s.has("Brook", p))
        connect(R.C2, R.CMID, self.cave_shrine_1)
        connect(R.C2, R.CBOSS, self.cave_shrine_2)
        connect(R.C2, R.CSECRET, self.cave_site_1)
        # Obstructed Paths on every island: Mole + 50 Bombs build sites (0.27.0)
        connect(R.P1, R.WHIDDEN, lambda s, p: self.wooded_site_3(s, p) or self.wooded_site_4(s, p))
        connect(R.G1, R.GHIDDEN, self.gorge_site_5)
        connect(R.GPOISON, R.GSECRET, self.gorge_site_6)
        connect(R.I2, R.IOBST1, self.iceberg_site_3)
        connect(R.ILADDER, R.IOBST2, self.iceberg_site_4)
        for e in [x for r in (R.P1, R.G1, R.GPOISON, R.I2, R.ILADDER, R.C1, R.C2) for x in regions[r].exits]:
            for reg in regions.values():
                self.multiworld.register_indirect_condition(reg, e)
        # The final island: its island item, then the Final Door (500: 1000 of five Energy colours = Gabri 13)
        connect(R.SUNNY, R.CENTRAL, lambda s, p: s.has(R.CENTRAL_LOG_POSE, p))
        goal_name, _flag, goal_region = GOALS[self.options.goal.value]
        for loc in LOCATIONS:
            if loc.region not in self.scope_regions or loc.name == goal_name:
                continue                    # after the goal, or the goal itself (an event below)
            if loc.check == ("shrine", 1010) and self.options.wherever_cannon_unlock.value:
                continue                    # the Wherever Cannon is an item, no build site
            if loc.name in SUPER_LOCATION_NAMES and not self.options.super_move_locations.value:
                continue                    # Super Move Locations: off
            if loc.check[0] == "catch" and loc.name not in self.catch_locations:
                continue                    # fishing / creature location not picked for this seed
            if loc.check[0] == "material" and not (self.options.materialsanity.value
                                                   and R.material_in_scope(loc.name[4:], self.scope_regions)):
                continue                    # Materialsanity off (or the material isn't in this seed)
            if loc.check[0] == "craft" and loc.check[1:] in EXTRA_RECIPE_LOCATIONS:
                if not (loc.check[1:] in self.extra_recipes or (loc.check[1] == "franky" and loc.check[2] in
                                                                FRANKY_TRADES and self.options.franky_supplies.value)):
                    continue                # random recipe / Franky's trade not in this seed
            elif loc.check[0] == "craft" and not self.craft_has_location(loc.check[1], loc.check[2]):
                continue                    # room opens after the goal, or an ingredient isn't on Island 1
            regions[loc.region].locations.append(OPUCLocation(p, loc.name, LOCATION_IDS[loc.name], regions[loc.region]))

        goal = OPUCLocation(p, goal_name, None, regions[goal_region])
        goal.place_locked_item(OPUCItem("Victory", ItemClassification.progression, None, p))
        regions[goal_region].locations.append(goal)

    # Gorge Isle shrines / build sites: access item, Gabri level, offered items (event/epoint/zone2.bin)
    @staticmethod
    def gorge_shrine_1(s, p) -> bool:   # The Silent Ancient Creature: 3 Mysterious Bone, 1 Healing Capsule
        return (s.has("Gorge Isle Shrine 1 Access", p) and R.energy(200)(s, p)
                and R.has_material("Mysterious Bone")(s, p) and R.has_material("Healing Capsule")(s, p))

    @staticmethod
    def gorge_shrine_2(s, p) -> bool:   # The Ruins in the Sunset: 30 Gunpowder, 3 Clay
        return (s.has("Gorge Isle Shrine 2 Access", p) and R.energy(201)(s, p)
                and R.has_material("Gunpowder")(s, p) and R.has_material("Clay")(s, p))

    @staticmethod
    def gorge_site_1(s, p) -> bool:     # An Incomplete Path: 2 Marble
        return R.build_site(1, "Gorge Isle")(s, p) and R.energy(211)(s, p) and R.has_material("Marble")(s, p)

    @staticmethod
    def gorge_site_2(s, p) -> bool:     # An Incomplete Path (2): 3 Marble
        return R.build_site(2, "Gorge Isle")(s, p) and R.energy(212)(s, p) and R.has_material("Marble")(s, p)

    @staticmethod
    def gorge_site_3(s, p) -> bool:     # An Unclimbable Path: 5 Bamboo
        return R.build_site(3, "Gorge Isle")(s, p) and R.energy(213)(s, p) and R.has_material("Bamboo")(s, p)

    @staticmethod
    def gorge_site_4(s, p) -> bool:     # An Incomplete Path (3): 5 Marble
        return R.build_site(4, "Gorge Isle")(s, p) and R.energy(214)(s, p) and R.has_material("Marble")(s, p)

    # Iceberg Isle shrines / build sites (event/epoint/zone3.bin)
    @staticmethod
    def iceberg_shrine_1(s, p) -> bool:   # The Cliff of Ice: 1 Anti-Cold Cream, 1 Stamina Tonic (Gabri 4)
        return (s.has("Iceberg Isle Shrine 1 Access", p) and R.energy(300)(s, p)
                and R.has_material("Anti-Cold Cream")(s, p) and R.has_material("Stamina Tonic")(s, p))

    @staticmethod
    def iceberg_shrine_2(s, p) -> bool:   # The Hall of Blizzards: 1 Ice Beetle, 15 Ice Shard (Gabri 5)
        return (s.has("Iceberg Isle Shrine 2 Access", p) and R.energy(301)(s, p)
                and R.has_material("Ice Beetle")(s, p) and R.has_material("Ice Shard")(s, p))

    @staticmethod
    def iceberg_site_1(s, p) -> bool:     # An Unclimbable Path: 5 Bamboo (Gabri 2)
        return R.build_site(1, "Iceberg Isle")(s, p) and R.energy(311)(s, p) and R.has_material("Bamboo")(s, p)

    @staticmethod
    def iceberg_site_2(s, p) -> bool:     # An Unclimbable Path (2): 5 Bamboo (Gabri 5)
        return R.build_site(2, "Iceberg Isle")(s, p) and R.energy(312)(s, p) and R.has_material("Bamboo")(s, p)

    # Cave Isle shrines / build sites (event/epoint/zone4.bin); Gabri levels from the costs (rules.gabri_level)
    @staticmethod
    def cave_shrine_1(s, p) -> bool:      # The Burning Cavity: 50 Bombs, 1 Fire Hercules (800 R, 400 G, 300 B, 500 W)
        return (s.has("Cave Isle Shrine 1 Access", p) and R.energy(400)(s, p)
                and R.ingredient("Bombs")(s, p) and R.has_material("Fire Hercules")(s, p))   # craftable Bombs

    @staticmethod
    def cave_shrine_2(s, p) -> bool:      # The Abyss: 1 Mock Cherry Pie, 3 Dual-Action Tonic, 3 Volcanic Rock
        return (s.has("Cave Isle Shrine 2 Access", p) and R.energy(401)(s, p)
                and R.has_material("Mock Cherry Pie")(s, p) and R.has_material("Dual-Action Tonic")(s, p)
                and R.has_material("Volcanic Rock")(s, p))

    @staticmethod
    def cave_site_1(s, p) -> bool:        # An Obstructed Path: Mole, 50 Bombs (500 G, 500 W, 800 Gold)
        return R.obstructed(R.build_site(1, "Cave Isle"), 411)(s, p)

    @staticmethod
    def cave_site_2(s, p) -> bool:        # An Incomplete Path: 5 Marble (300 R, 300 G, 100 Gold)
        return (R.build_site(2, "Cave Isle")(s, p) and R.energy(412)(s, p)
                and R.has_material("Marble")(s, p))

    # Obstructed Paths on the other islands (1 Mole, 50 Bombs each)
    @staticmethod
    def wooded_site_3(s, p) -> bool:      # 300 Red, 300 Gold
        return R.obstructed(R.build_site(3), 113)(s, p)

    @staticmethod
    def wooded_site_4(s, p) -> bool:      # 300 Red, 300 Gold
        return R.obstructed(R.build_site(4), 114)(s, p)

    @staticmethod
    def gorge_site_5(s, p) -> bool:       # 200 Blue, 200 Gold
        return R.obstructed(R.build_site(5, "Gorge Isle"), 215)(s, p)

    @staticmethod
    def gorge_site_6(s, p) -> bool:       # 500 Red, 500 Black, 900 Gold
        return R.obstructed(R.build_site(6, "Gorge Isle"), 216)(s, p)

    @staticmethod
    def iceberg_site_3(s, p) -> bool:     # 200 Blue, 200 Gold
        return R.obstructed(R.build_site(3, "Iceberg Isle"), 313)(s, p)

    @staticmethod
    def iceberg_site_4(s, p) -> bool:     # 200 Blue, 700 Gold
        return R.obstructed(R.build_site(4, "Iceberg Isle"), 314)(s, p)

    def room_has_locations(self, room: str) -> bool:
        """Every room can open before any goal (vanilla Kitchen / Pharmacy: after any non-goal island boss)."""
        return True

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

        rule("Wooded Isle Shrine - An Odd Stone & A Strange Creature", self.prologue_exit)
        rule("Prologue Part 3 Completed", self.prologue_exit)
        rule('Wooded Isle Monument - "Far, Far Away"', lambda s, p: R.rock_path(s, p) and R.monument(s, p))
        rule('Wooded Isle Monument - "Eternity"', R.monument)
        rule("Wooded Isle - Nectar Chest", R.rock_path)                 # rock path: Pickaxe or Gunpowder
        rule("Wooded Isle - Restorative Drug Chest", R.rock_path)
        rule("Wooded Isle - Steel Chain Chest", lambda s, p: s.has("Pickaxe", p) and
             R.map_fragment(("Map 8, Fragment 1", "Map 8, Fragment 2", "Map 8, Fragment 3"))(s, p))
        rule("Wooded Isle - Flour Chest", lambda s, p: s.has("Pickaxe", p) and
             R.map_fragment(("Map 2, Fragment 1", "Map 2, Fragment 2", "Map 2, Fragment 3", "Map 2, Fragment 4"))(s, p))
        rule("Wooded Isle Shrine - An Enormous Boulder",
             lambda s, p: s.has("Wooded Isle Shrine 2 Access", p) and R.energy(100)(s, p))
        rule("Wooded Isle Shrine - What Lies Asleep in the Amber",
             lambda s, p: s.has("Wooded Isle Shrine 3 Access", p) and R.energy(101)(s, p) and R.net(s, p))
        rule("Wooded Isle Build Site - An Unclimbable Area",
             lambda s, p: s.has("Pickaxe", p) and R.build_site(1)(s, p) and R.energy(111)(s, p))
        rule("Wooded Isle Build Site - An Incomplete Path",
             lambda s, p: R.build_site(2)(s, p) and R.energy(112)(s, p))

        rule("Gorge Isle Shrine - The Silent Ancient Creature", self.gorge_shrine_1)
        rule("Gorge Isle Shrine - The Ruins in the Sunset", self.gorge_shrine_2)
        rule("Gorge Isle Build Site - An Incomplete Path", self.gorge_site_1)
        rule("Gorge Isle Build Site - An Incomplete Path (2)", self.gorge_site_2)
        rule("Gorge Isle Build Site - An Unclimbable Path", self.gorge_site_3)
        rule("Gorge Isle Build Site - An Incomplete Path (3)", self.gorge_site_4)
        rule('Gorge Isle Monument - "Creation"', R.monument)
        # The Wherever Cannon: 300 Red (Gabri 3), 7 Iron Scrap, 10 Gunpowder
        if not o.wherever_cannon_unlock.value:
            rule("Thousand Sunny - Wherever Cannon", lambda s, p: R.build_site(1, "Thousand Sunny")(s, p)
                 and R.energy(1010)(s, p) and R.has_material("Iron Scrap")(s, p) and R.has_material("Gunpowder")(s, p))
        rule('Gorge Isle Monument - "Hope"', R.monument)
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

        # 0.30.0: random recipes (Extra Crafting Recipes, Franky's Archipelago Trades) and Franky's fixed trades
        for (room, row), ing in self.extra_recipes.items():
            rule(EXTRA_RECIPE_LOCATIONS[(room, row)], R.recipe(room, row, [n for n, _c in ing]))
        if o.franky_supplies.value:
            for row in FRANKY_TRADES:
                rule(EXTRA_RECIPE_LOCATIONS[("franky", row)], R.franky_trade(row))

        if o.materialsanity.value:
            for loc in LOCATIONS:
                if loc.check[0] == "material" and R.material_in_scope(loc.name[4:], self.scope_regions):
                    rule(loc.name, R.got_material(loc.name[4:]))

        for name, thing in self.catch_locations.items():
            rule(name, R.caught(thing) if name.startswith("Creatures - ") else R.has_material(thing))
            unimportant = (o.fishsanity.value if name.startswith("Fishing") else o.creaturesanity.value) == 2
            if unimportant:
                add_item_rule(mw.get_location(name, p), lambda item: not item.advancement)

        # Iceberg Isle
        rule("Iceberg Isle Shrine - The Cliff of Ice", self.iceberg_shrine_1)
        rule("Iceberg Isle Shrine - The Hall of Blizzards", self.iceberg_shrine_2)
        rule("Iceberg Isle Build Site - An Unclimbable Path", self.iceberg_site_1)
        rule("Iceberg Isle Build Site - An Unclimbable Path (2)", self.iceberg_site_2)
        rule("Iceberg Isle - Vision Dial Chest", lambda s, p: s.has("Pickaxe", p) and
             R.map_fragment(("Map 3, Fragment 1", "Map 3, Fragment 2", "Map 3, Fragment 3"))(s, p))
        rule('Central Isle Monument - "Inferno"', R.monument)

        # Cave Isle (0.27.0)
        rule("Cave Isle Shrine - The Burning Cavity", self.cave_shrine_1)
        rule("Cave Isle Shrine - The Abyss", self.cave_shrine_2)
        rule("Cave Isle Build Site - An Obstructed Path", self.cave_site_1)
        rule("Cave Isle Build Site - An Incomplete Path", self.cave_site_2)
        for name in ('Cave Isle Monument - "Drifting Away"', 'Cave Isle Monument - "A Certain Island"',
                     'Wooded Isle Monument - "Seal"', 'Iceberg Isle Monument - "Reward"',
                     'Iceberg Isle Monument - "Orbs"'):
            rule(name, R.monument)
        # treasure map chests are dug up: Pickaxe + the map's fragments
        for loc, m, n in (("Cave Isle - Tone Dial Chest", 7, 3), ("Cave Isle - Pure Iron Ore Chest", 5, 3),
                          ("Iceberg Isle - Revival Elixir Chest", 9, 3), ("Wooded Isle - Ultimate Reel Chest", 10, 5)):
            frags = tuple(f"Map {m}, Fragment {k + 1}" for k in range(n))
            rule(loc, lambda s, p, frags=frags: s.has("Pickaxe", p) and R.map_fragment(frags)(s, p))
        # the other islands' Obstructed Path build sites
        rule("Wooded Isle Build Site - An Obstructed Path", self.wooded_site_3)
        rule("Wooded Isle Build Site - An Obstructed Path (2)", self.wooded_site_4)
        rule("Gorge Isle Build Site - An Obstructed Path", self.gorge_site_5)
        rule("Gorge Isle Build Site - An Obstructed Path (2)", self.gorge_site_6)
        rule("Iceberg Isle Build Site - An Obstructed Path", self.iceberg_site_3)
        rule("Iceberg Isle Build Site - An Obstructed Path (2)", self.iceberg_site_4)
        if self.options.goal.value == 2:
            # final boss: the Final Door needs 1000 of five Energy colours (only reachable at Gabri level 13)
            bosses = [mw.get_location(n, p) for n in final_door_bosses(o.extra_final_door_requirement.value)]
            rule(GOALS[2][0], lambda s, p: s.has("The Final Door", p) and R.energy(500)(s, p)
                 and all(b.can_reach(s) for b in bosses))
        mw.completion_condition[p] = lambda s: s.has("Victory", p)

    @staticmethod
    def interpret_slot_data(slot_data: Dict[str, Any]) -> Dict[str, Any]:
        """Universal Tracker: hand the slot data back to generate_early (as re_gen_passthrough)."""
        return slot_data

    def fill_slot_data(self) -> Dict[str, Any]:
        return {
            "starting_character": self.starting_character,
            "goal": self.options.goal.value,
            "extra_final_door_requirement": (self.options.extra_final_door_requirement.value
                                             if self.options.goal.value == 2 else 0),
            "death_link": self.options.death_link.value,
            "falling_death_link": self.options.falling_death_link.value,
            # islands that open with their island item (0.21.0: all of them; older seeds: by goal)
            "islands": [2, 3, 4, 5],
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
            "disable_food_diminishing_returns": self.options.disable_food_diminishing_returns.value,
            "better_traps": self.options.better_traps.value,
            "traps_never_expire": self.options.better_traps.value,     # older clients
            "fast_traps": self.options.better_traps.value,
            "iron_scrap_gives_gold_energy": self.options.iron_scrap_gives_gold_energy.value,
            "blue_orb_spot_gives_iron_ore": self.options.blue_orb_spot_gives_iron_ore.value,
            "better_random_dig_item_rates": self.options.better_random_dig_item_rates.value,
            "higher_random_dig_chance": self.options.better_random_dig_item_rates.value,   # older clients
            "better_plant_drop_rates": self.options.better_plant_drop_rates.value,
            "expanded_storage": self.options.expanded_storage.value,
            "wherever_cannon_unlock": self.options.wherever_cannon_unlock.value,
            "include_gunpowder_logic": self.options.include_gunpowder_logic.value,
            "enemy_gunpowder_drop_logic": self.options.enemy_gunpowder_drop_logic.value,
            "enemy_gunpowder_drop_rate": self.options.enemy_gunpowder_drop_rate.value,
            "stack_craftables_make_max_copies": self.options.stack_craftables_make_max_copies.value,
            "materialsanity": self.options.materialsanity.value,
            "gabri_energy_items": self.options.gabri_energy_items.value,
            "gabri_level_items": self.options.gabri_level_items.value,
            "energy_link": self.options.energy_link.value,
            # Starting Costumes: per Straw Hat (Luffy..Brook) [costume, style] for the client
            "starting_costumes": [list(COSTUME_CHOICES[i][1][getattr(self.options, f"{w.lower()}_starting_costume")
                                                            .value][2:4]) for i, (w, _c) in enumerate(COSTUME_CHOICES)],
            "bag_palette_upgrade_item_type": self.options.bag_palette_upgrade_item_type.value,
            "cat_burglar_item_type": self.options.cat_burglar_item_type.value,
            "light_weight_item_type": self.options.light_weight_item_type.value,
            "flower_power_item_type": self.options.flower_power_item_type.value,
            "chopper_brook_cold_resistance": self.options.chopper_brook_cold_resistance.value,
            "guaranteed_creature_drops": self.options.guaranteed_creature_drops.value,
            "equalise_fish_rates": self.options.equalise_fish_rates.value,
            "quick_recipes": self.options.quick_recipes.value,
            "aquarium_open": 1,          # always on since 0.25.0 (option removed)
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
            # 0.30.0
            "starting_gabri_energy": self.options.starting_gabri_energy.value,
            "franky_supplies": self.options.franky_supplies.value,
            "franky_supplies_unlock": self.options.franky_supplies_unlock.value,
            "franky_required_for_art": self.options.franky_required_for_art.value,
            "extra_crafting_recipes": self.options.extra_crafting_recipes.value,
            "easier_fish": self.options.easier_fish.value,
            # random recipes: [room, row, [[game item id, count], ...]]
            "extra_recipes": [[room, row, [[POOL_ITEM_IDS[n], c] for n, c in ing]]
                              for (room, row), ing in sorted(self.extra_recipes.items())],
        }
