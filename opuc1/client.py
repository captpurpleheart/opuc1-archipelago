"""
One Piece Unlimited Cruise Part 1 (PAL, ROUPAF) - Archipelago client for Dolphin.

Start it from the Archipelago Launcher while the game is at the title screen, connect, then start a new
game. Four times a second it reads checks from game memory and makes the game match the items received.
"""
import asyncio
import json
import zlib
import os
import time
import traceback
from collections import Counter
from typing import Dict, List, Set, Tuple

import Utils
from CommonClient import ClientCommandProcessor, get_base_parser, gui_enabled, logger, server_loop

# Universal Tracker, when installed, provides the tracker tab and in-logic checks; its context is a
# drop-in replacement for the normal one.
tracker_loaded = False
try:
    from worlds.tracker.TrackerClient import TrackerGameContext as CommonContext
    tracker_loaded = True
except ImportError:
    from CommonClient import CommonContext
from NetUtils import ClientStatus, NetworkItem

from .data import (ROD_GRADE_BYTES_4, line_level, rod_level_from_items, BASE_ID, CHARACTERS, CRAFTS, DUMMY_RECIPES, GAME, GOALS, ITEM_IDS, ITEM_TABLE, ITEMS,
                   LOCATION_IDS, LOCATIONS, SHRINE_ACCESS, ROOM_OPTIONS, ART_ITEMS, ROOM_ART,
                   MAP_FRAGMENT_GROUPS, BUILD_SITE_IDS)

try:
    from .game_state import (BAG_CAPACITY, HIDDEN_ALSO_COMMENT, HIDDEN_AP_COMMENT, NO_LOCATION_COMMENT, GameState,
                             also_comes_comment, placeholder_comment, rod_level_byte)
except ImportError as e:  # dolphin_memory_engine missing
    GameState = None
    IMPORT_ERROR = e

ID_TO_ITEM = {v: k for k, v in ITEM_IDS.items()}
try:
    import json as _json, pkgutil as _pkgutil
    WORLD_VERSION = _json.loads(_pkgutil.get_data(__package__, "archipelago.json"))["world_version"]
except Exception:
    WORLD_VERSION = "unknown"
CHECKS_BY_KIND: Dict[str, List[Tuple[int, tuple]]] = {}
for _l in LOCATIONS:
    CHECKS_BY_KIND.setdefault(_l.check[0], []).append((LOCATION_IDS[_l.name], _l.check))
FLAG_LOCS = {c[1]: lid for lid, c in CHECKS_BY_KIND.get("flag", [])}
CHEST_LOCS = {c[1]: lid for lid, c in CHECKS_BY_KIND.get("chest", [])}
SHRINE_LOCS = {c[1]: lid for lid, c in CHECKS_BY_KIND.get("shrine", [])}
CRAFT_LOCS = {(c[1], c[2]): lid for lid, c in CHECKS_BY_KIND.get("craft", [])}
COOP_LOCS = [(lid, c[1], c[2]) for lid, c in CHECKS_BY_KIND.get("coop", [])]
MAP_FRAGMENTS = {d.name for d in ITEMS if d.name.startswith("Map ") and ", Fragment " in d.name}
# Tools that the game replaces when they're upgraded at the Workshop: crafting the Bug-Catcher Net uses up the Broken
# net (and its "ever obtained" bit), so the client must not give the Broken net again (0.19.7).
SUPERSEDED_BY = {3: (2,)}
SUNNY_FLAG = 11990          # "First Step on the Thousand Sunny": the Pickaxe is held back until then
MOVE_LOCS = [(lid, c[1], c[2], c[3]) for lid, c in CHECKS_BY_KIND.get("move", [])]
CATCH_LOCS = {c[1]: lid for lid, c in CHECKS_BY_KIND.get("catch", [])}     # fish / creature item -> location
DUMMY_CRAFTS = {(room, row) for room, row, _, dummy in CRAFTS if dummy}
CONSUMABLE_KINDS = {"filler"}


class OPUCCommandProcessor(ClientCommandProcessor):
    def _cmd_dolphin(self) -> None:
        """Show the Dolphin connection status."""
        self._cmd_status()

    def _cmd_sp(self) -> None:
        """Show each Straw Hat's SP values (for the SP refill bug)."""
        ctx = self.ctx
        if isinstance(ctx, OPUCContext) and ctx.mem and ctx.mem.hooked:
            try:
                logger.info(ctx.mem.sp_report())
            except RuntimeError as e:
                logger.info(f"(memory read failed: {e})")

    def _cmd_status(self) -> None:
        """Show what the client sees in the game (for bug reports)."""
        ctx = self.ctx
        if not isinstance(ctx, OPUCContext) or not ctx.mem:
            return
        g = ctx.mem
        lines = [f"Client version: {WORLD_VERSION}", f"Dolphin hooked: {g.hooked}", f"Server slot: {ctx.slot}", f"Loop passes: {ctx.passes}",
                 f"Last loop step: {ctx.step}", f"Last error: {ctx.last_error or 'none'}"]
        try:
            if g.hooked:
                lines += [f"In game: {g.in_game()} (settled: {g.settled()})", f"Code patches applied: {g.patched}",
                          f"Recipe discovery off: {g.discovery_patch_state()}",
                          f"Hook installed: {g.hook_active()}", g.scan_report(),
                          f"Item being given: {ctx.give_pending}", f"Consumables delivered: {ctx.delivered}",
                          f"Last consumable give: {ctx.last_give}; failed gives: {ctx.give_failures}",
                          f"Items received: {len(ctx.items_received)}; hook give flag: {g.give_busy()}; "
                          f"event playing: {g.event_playing()}; boss fight: {g.boss_active()}; "
                          f"scripted fight: {g.fight_in_progress()}; last retry: {g.last_retry or 'none'}",
                          f"Save item count: {g.read_delivered()} (seed tag {g.seed_tag:08X})",
                          f"Debug: {g.debug_state()}"]
        except RuntimeError as e:
            lines.append(f"(memory read failed: {e})")
        logger.info("\n".join(lines))


class OPUCContext(CommonContext):
    game = GAME
    command_processor = OPUCCommandProcessor
    items_handling = 0b111

    def __init__(self, server_address, password):
        super().__init__(server_address, password)
        self.mem = GameState(log=logger.info) if GameState else None
        self.slot_data: Dict = {}
        self.comments: Dict[Tuple[str, int], str] = {}
        self.sent: Set[int] = set()
        self.goal_sent = False
        self.last_seen: Set[int] = set()
        self.owner_session = -1             # game session whose save owner was checked
        self.late_session = None            # session that was already running when the client connected
        self.connect_checked = False
        self.save_ok = False
        self.delivered = 0          # how many received items have had their one-time delivery (consumables)
        self.passes = 0
        self.step = "starting"
        self.last_error = ""
        self.give_pending = None    # (kind, game item id, start time) while the hook is giving an item
        self.retry_at = 0.0         # don't retry a failed consumable give before this time
        self.give_failed: Set[int] = set()
        self.give_failures = 0
        self.pickaxe_note = False
        self.armed_keys: List[Tuple[str, str]] = []      # held-back key items / Arts (name, reason)
        self.armed_items: List[Tuple[str, str]] = []     # received consumables not given yet
        self.bag_full_said = False
        self.last_give = "none"
        self.session_seen = 0       # GameState.sessions when per-session state was last reset
        self.keys_requested: Set[int] = set()

    async def server_auth(self, password_requested: bool = False):
        if password_requested and not self.password:
            await super().server_auth(password_requested)
        await self.get_username()
        await self.send_connect()

    def on_package(self, cmd: str, args: dict):
        if cmd == "Connected":
            self.slot_data = args.get("slot_data", {})
            self.sent = set(args.get("checked_locations", []))
            self.load_progress()
            if self.mem:
                self.mem.seed_tag = zlib.crc32(f"{self.seed_name}:{self.slot}".encode()) or 1
            for room, rows in self.slot_data.get("dummy_recipes", {}).items():
                for row in rows:
                    if (room, row) not in CRAFT_LOCS or CRAFT_LOCS[(room, row)] not in self.server_locations:
                        self.comments[(room, row)] = NO_LOCATION_COMMENT
            # vanilla-result recipes: "also comes with ..." when they're a location here, otherwise "not a Location"
            dummy_rows = {(room, row) for room, rows in self.slot_data.get("dummy_recipes", {}).items() for row in rows}
            for room in ("workshop", "kitchen", "pharmacy"):
                for row in range(32):
                    if (room, row) in dummy_rows or (room, row) in DUMMY_CRAFTS:
                        continue
                    lid = CRAFT_LOCS.get((room, row))
                    self.comments[(room, row)] = (also_comes_comment(None, None) if lid in self.server_locations
                                                  else NO_LOCATION_COMMENT)
            if int(self.slot_data.get("recipes_spoil_locations", 1)):
                scout = [lid for lid in CRAFT_LOCS.values() if lid in self.server_locations]
            else:                                         # no item names: fixed texts, nothing scouted
                scout = []
                for key, lid in CRAFT_LOCS.items():
                    if lid in self.server_locations:
                        self.comments[key] = HIDDEN_AP_COMMENT if key in DUMMY_CRAFTS else HIDDEN_ALSO_COMMENT
            if scout:
                Utils.async_start(self.send_msgs([{"cmd": "LocationScouts", "locations": scout, "create_as_hint": 0}]))
        elif cmd == "LocationInfo":
            by_id = {v: k for k, v in CRAFT_LOCS.items()}
            for item in args.get("locations", []):
                key = by_id.get(item.location)
                if key:
                    player = self.player_names.get(item.player, "someone")
                    name = self.item_names.lookup_in_slot(item.item, item.player)
                    self.comments[key] = (placeholder_comment(player, name) if key in DUMMY_CRAFTS
                                          else also_comes_comment(player, name))
        super().on_package(cmd, args)    # Universal Tracker listens to the same messages

    # ---- one-time deliveries survive client restarts (per seed and slot)
    def _progress_file(self) -> str:
        return Utils.user_path(f"opuc1_{self.seed_name}_{self.slot}.json")

    def load_progress(self) -> None:
        try:
            with open(self._progress_file()) as f:
                self.delivered = json.load(f).get("delivered", 0)
        except (OSError, ValueError):
            self.delivered = 0

    def save_progress(self) -> None:
        try:
            with open(self._progress_file(), "w") as f:
                json.dump({"delivered": self.delivered}, f)
        except OSError:
            pass

    def armed_text(self) -> str:
        rows = self.armed_keys + self.armed_items
        if not rows:
            return "Nothing is waiting: every item received so far has been given to you."
        return "\n".join(f"{name}  [color=#9a9a9a]({why})[/color]" for name, why in rows)

    def make_gui(self):
        ui = super().make_gui()          # Archipelago's window, or Universal Tracker's
        ctx = self

        class OPUCManager(ui):
            base_title = "One Piece Unlimited Cruise 1 Client"

            def build(self):
                container = super().build()
                try:
                    from kivy.clock import Clock
                    from kivy.metrics import dp
                    from kivy.uix.scrollview import ScrollView
                    try:
                        from kivymd.uix.label import MDLabel as Label
                    except ImportError:
                        from kivy.uix.label import Label
                    view = ScrollView(do_scroll_x=False)
                    label = Label(text=ctx.armed_text(), markup=True, size_hint_y=None, valign="top",
                                  padding=(dp(12), dp(12)))
                    label.bind(width=lambda w, v: setattr(w, "text_size", (v, None)),
                               texture_size=lambda w, v: setattr(w, "height", v[1]))
                    view.add_widget(label)
                    self.add_client_tab("Armed Items", view)
                    Clock.schedule_interval(lambda _dt: setattr(label, "text", ctx.armed_text()), 0.5)
                except Exception as e:   # never let the extra tab stop the client from opening
                    logger.warning(f"Armed Items tab not available: {e}")
                return container

        return OPUCManager


def received_counts(ctx: OPUCContext) -> Counter:
    c = Counter()
    for it in ctx.items_received:
        name = ID_TO_ITEM.get(it.item)
        if name:
            c[name] += 1
    return c


def apply_items(ctx: OPUCContext, g: "GameState", have: Counter) -> None:
    start = int(ctx.slot_data.get("starting_character", 0))
    owned_chars = {start} | {i for i, n in enumerate(CHARACTERS) if have[n]}
    g.enforce_crew(owned_chars, start)

    # Thousand Sunny options: 0 vanilla (Workshop open; Kitchen / Pharmacy from chapter 3, after the
    # Island 1 boss), 1 own item, 2 the room's owner, 3 both
    sd = ctx.slot_data
    rooms = set()
    for d in ITEMS:
        if d.kind != "room":
            continue
        unlock_opt, _a, ci = ROOM_OPTIONS[d.data]
        mode = int(sd.get(unlock_opt, 1))
        if mode == 0:
            ok = d.data == "workshop" or g.chapter() >= 3
        else:
            ok = (mode == 2 or bool(have[d.name])) and (mode == 1 or ci in owned_chars)
        if ok:
            rooms.add(d.data)
    g.set_rooms(rooms)
    # Next Island menu: islands in the seed open with their Log Pose; the others keep the vanilla rule
    goal = int(sd.get("goal", 0))
    ch = g.chapter()
    log = {d.data: bool(have[d.name]) for d in ITEMS if d.kind == "island"}
    g.set_islands({1: True,
                   2: log.get(2, False) if goal >= 1 else ch > 2,
                   3: ch > 3, 4: ch > 4,
                   5: log.get(5, False) if goal >= 2 else ch > 5})
    # Art of Development / Cooking / Compounding wait for their owner when that option is on
    art_held = {ci for _u, art_opt, ci in ROOM_OPTIONS.values() if int(sd.get(art_opt, 0)) and ci not in owned_chars}
    g.set_gabri(have["Progressive Gabri Level"])
    # Build Sites (x11-x16) also wait for Franky with franky_required_for_build_sites
    franky_ok = not int(sd.get("franky_required_for_build_sites", 0)) or 7 in owned_chars
    g.set_shrine_locks({sid for name, sid in SHRINE_ACCESS.items()
                        if have[name] and (sid not in BUILD_SITE_IDS or franky_ok)})
    g.set_monuments(not int(sd.get("robin_required_for_monuments", 0)) or 6 in owned_chars)
    maps_held = bool(int(sd.get("nami_required_for_maps", 0))) and 4 not in owned_chars
    sunny = bool(g.script_flags([SUNNY_FLAG]))

    # "Armed" items (received, held back by the client) for the Armed Items tab, in delivery priority order
    armed: List[Tuple[str, str]] = []
    if have["Pickaxe"] and not sunny:
        armed.append(("Pickaxe", "Waiting for Thousand Sunny entry"))
    for room in ("workshop", "kitchen", "pharmacy"):
        ci = ROOM_OPTIONS[room][2]
        k = have[ROOM_ART[room]]
        if k and ci in art_held:
            art = ROOM_ART[room].split("Progressive ", 1)[1]
            armed.append((art + (f" x{k}" if k > 1 else ""), f"Waiting for {CHARACTERS[ci]} to join the Crew"))
    # Map fragments wait for Nami, and/or until every fragment of their map has arrived
    whole_maps = bool(int(sd.get("treasure_maps_need_every_fragment", 0)))
    frag_held: Set[str] = set()
    for map_name, frags in MAP_FRAGMENT_GROUPS.items():
        got = [f for f in frags if have[f]]
        if not got:
            continue
        if maps_held:
            why = "Waiting for Nami to join the Crew"
        elif whole_maps and len(got) < len(frags):
            why = f"Waiting for every fragment of {map_name} ({len(got)}/{len(frags)})"
        else:
            continue
        frag_held.update(got)
        armed += [(f, why) for f in got]
    ctx.armed_keys = armed
    # Art levels the game actually has (held-back Arts count as 0), for recipe discovery
    ctx.art_levels = {room: (0 if ROOM_OPTIONS[room][2] in art_held else min(3, have[ROOM_ART[room]]))
                      for room in ROOM_ART}

    key_items: List[int] = []
    moves: Dict[int, Set[int]] = {}
    abilities: Dict[int, List[int]] = {}
    coop: Set[int] = set()
    for d in ITEMS:
        k = have[d.name]
        if not k:
            continue
        if d.kind == "move":
            ci, ids = d.data
            moves.setdefault(ci, set()).update(ids[:k])
        elif d.kind == "ability":
            ci, slot = d.data
            if slot == 1 and ci in art_held and d.name in ART_ITEMS:
                continue
            abilities.setdefault(ci, [0, 0, 0])[slot] = min(k, 5 if slot == 2 else 3)
        elif d.kind == "coop":
            coop.add(d.data["record"])
            if "item" in d.data:
                key_items.append(d.data["item"])
        elif d.kind == "key":
            if d.name in frag_held:
                continue                                  # waits for Nami / the rest of its map
            if d.name == "Pickaxe" and not sunny:
                # held back until the first step on the Thousand Sunny (no Prologue sequence break)
                if not ctx.pickaxe_note:
                    ctx.pickaxe_note = True
                    logger.info("Pickaxe received: it will be given once you reach the Thousand Sunny.")
                continue
            items = d.data["item"] if isinstance(d.data["item"], list) else [d.data["item"]]
            for gid in items[:k]:
                if gid in BAG_CAPACITY:
                    g.set_capacity(*BAG_CAPACITY[gid])
                key_items.append(gid)
    if have["Progressive Clima-Tact"] >= 1:
        key_items.append(178)                             # Clima-Tact Repair -> Thunder Ball
    if have["Progressive Clima-Tact"] >= 2:
        moves.setdefault(4, set()).add(25)                # repeatable Thunder Ball
    vac = have["Progressive Vacuum Cleaner"]
    if vac >= 1:
        key_items.append(8)
        g.ensure_slot_byte(8, 0x0B, 1 if vac >= 2 else 0)
        if vac >= 2:
            g.set_found(7)
    if have["Fishing Rod"]:
        mode = int(ctx.slot_data.get("rod_upgrade_items", 30))
        k = have["Progressive Fishing Rod Level"]
        rod = ROD_GRADE_BYTES_4[min(k, 4) - 1] if mode == 4 and k else rod_level_byte(rod_level_from_items(mode, k))
        g.ensure_slot_byte(6, 0x0B, rod)
        lines = have["Progressive Fishing Rod Level" if int(ctx.slot_data.get("combine_rod_and_line", 0))
                     else "Progressive Fishing Rod Line"]
        g.ensure_slot_byte(6, 0x0F, line_level(mode, lines))

    if g.settled():
        new_scan = g.ensure_scan()
        if new_scan:
            g.strip_fragment_drops(list(ctx.slot_data.get("vacuum_orbs", [85] * 5)))
        g.set_blue_orb_spot(70 if int(ctx.slot_data.get("blue_orb_spot_gives_iron_ore", 0)) else 81)
        g.install_hook()
        changed = g.write_tables(moves, abilities) | g.write_coop(coop)
        if changed or new_scan:
            g.request_unlock_check()
        g.min_sp()
        if int(ctx.slot_data.get("disable_food_diminishing_returns", 0)):
            g.patch_food_returns()      # the game's setter always stores 0
            g.reset_food_returns()      # fallback if the patch went in after the code was first used
        # code patches below also go in at the title screen (apply_patches); repeated here for a late start
        g.patch_database_menu()         # Database menu open from the start (catch locations follow it)
        g.patch_recipe_discovery()      # no "An Idea!" popups: the client lists recipes itself
        g.patch_idea_popup()
        if int(ctx.slot_data.get("traps_never_expire", 0)):
            g.patch_traps()             # creatures never escape a trap
        if int(ctx.slot_data.get("fast_traps", 0)):
            g.patch_fast_traps()        # 10 min catch, leaving the field once finishes it
        g.write_exp(1 + int(ctx.slot_data.get("move_exp_multiplier", 0)))   # 0 off, 1 = 2x, 2 = 3x

    deliver(ctx, g, key_items)


def deliver(ctx: "OPUCContext", g: "GameState", key_items: List[int]) -> None:
    """Give items through the game's own code (one at a time, via the hook) so they show the normal
    'obtained' / discovery messages. Key items: once each (found bits). Filler: once per copy, in order.
    The filler count lives in the save data, so loading an older save (Game Over, quitting without saving)
    gives back everything received since that save."""
    if not g.settled():
        return
    st = g.read_delivered()
    if st is None:
        return
    marked, count = st
    if not marked or count > len(ctx.items_received):
        # new game, a save last used with another seed, or a count that can't be right: give every
        # received consumable from the start
        count = 0
        g.write_delivered(count)
    ctx.delivered = count
    pending_list(ctx, g)
    now = time.monotonic()
    p = ctx.give_pending
    if p:
        kind, gid, started, before, done_at = p
        if not g.give_busy():
            if kind == "key":
                ctx.give_pending = None
                if not g.found(gid):
                    g.ensure_key_item(gid)                 # the game didn't take it: give it directly
                return
            # filler: count it only once it is really in the bag / Storage (checked a moment later)
            if done_at is None:
                ctx.give_pending = (kind, gid, started, before, now)
                return
            if now - done_at < 0.5:
                return
            ctx.give_pending = None
            after = g.item_count(gid)
            ctx.last_give = f"item {gid}: carried {before} -> {after}"
            if after > before:
                ctx.delivered = count + 1
                g.write_delivered(ctx.delivered)
                ctx.save_progress()
            else:
                ctx.retry_at = now + 10                    # the game didn't add it: try again shortly
                ctx.give_failures += 1
                if gid not in ctx.give_failed:
                    ctx.give_failed.add(gid)
                    logger.info(f"Item {gid} wasn't added (carried {before} -> {after}); retrying every 10 s. "
                                f"Please send /status if this keeps happening.")
        elif now - started > 20:
            if kind == "key":
                g.cancel_give()                            # hook not running: fall back to direct writes
                ctx.give_pending = None
                g.ensure_key_item(gid)
            elif not g.hook_active():
                g.cancel_give()                            # filler waits for the hook (never direct writes)
                ctx.give_pending = None
        return
    if not g.hook_active():
        return
    for gid in key_items:
        if any(g.found(u) or g.find_slots(u) for u in SUPERSEDED_BY.get(gid, ())):
            continue                                # already upgraded in game (e.g. net crafted): don't give it back
        if not g.found(gid) and gid not in ctx.keys_requested:
            ctx.keys_requested.add(gid)
            g.request_give(gid)
            ctx.give_pending = ("key", gid, now, 0, None)
            return
        if not g.found(gid) and gid in ctx.keys_requested:
            g.ensure_key_item(gid)                         # asked once already this session
    while ctx.delivered < len(ctx.items_received):
        d = ITEM_TABLE.get(ID_TO_ITEM.get(ctx.items_received[ctx.delivered].item, ""))
        if d and d.kind in CONSUMABLE_KINDS:
            if now < ctx.retry_at:
                return
            gid, n = d.data["item"], d.data.get("count", 1)
            if not g.has_room(gid, n):
                ctx.last_give = f"{d.name}: waiting, bag and palette are full"
                if not ctx.bag_full_said:
                    ctx.bag_full_said = True
                    logger.info(f"Your bag is full: {d.name} (and anything after it) will arrive once there's room.")
                return
            ctx.bag_full_said = False
            before = g.item_count(gid)
            g.request_give(gid, n)
            ctx.give_pending = ("filler", gid, now, before, None)
            return
        ctx.delivered += 1
        g.write_delivered(ctx.delivered)
        ctx.save_progress()


def pending_list(ctx: "OPUCContext", g: "GameState", limit: int = 40) -> None:
    """Received consumables not given yet, for the Armed Items tab (they arrive in this order)."""
    out: List[Tuple[str, str]] = []
    room: Dict[Tuple[int, int], bool] = {}
    blocked = False
    for it in ctx.items_received[ctx.delivered:]:
        d = ITEM_TABLE.get(ID_TO_ITEM.get(it.item, ""))
        if not d or d.kind not in CONSUMABLE_KINDS:
            continue
        if len(out) >= limit:
            out.append((f"... and {len(ctx.items_received) - ctx.delivered - limit} more", "Queued"))
            break
        gid, n = d.data["item"], d.data.get("count", 1)
        if (gid, n) not in room:
            room[(gid, n)] = g.has_room(gid, n)
        if not room[(gid, n)]:
            blocked = True
            out.append((d.name, "Full Inventory"))
        else:
            out.append((d.name, "Queued behind a full item" if blocked else "Arriving"))
    ctx.armed_items = out


def read_checks(ctx: OPUCContext, g: "GameState") -> Set[int]:
    found: Set[int] = set()
    goal_flag = GOALS[int(ctx.slot_data.get("goal", 0))][1]     # 11351 Eneru, 12351 Gecko Moria
    flags = g.script_flags(list(FLAG_LOCS) + [goal_flag])
    found |= {FLAG_LOCS[f] for f in flags if f in FLAG_LOCS}
    # Doom Guardian: script 15030 (final form beaten -> ending -> GameClear) only sets its end flag after the
    # credits, so its function flag (set when 15030 starts, to be confirmed in game) counts as well.
    final = int(ctx.slot_data.get("goal", 0)) == 2 and (bool(g.func_flags([15030])) or g.game_cleared())
    if (goal_flag in flags or final) and not ctx.goal_sent:
        ctx.goal_sent = True
        Utils.async_start(ctx.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}]))
        ctx.finished_game = True
    found |= {CHEST_LOCS[c] for c in g.opened_chests(set(CHEST_LOCS))}
    found |= {SHRINE_LOCS[s] for s in g.activated_shrines() if s in SHRINE_LOCS}
    found |= {CRAFT_LOCS[k] for k in g.crafted() if k in CRAFT_LOCS}
    # first catch of a fish / creature: its "ever obtained" bit (only locations that exist in this seed)
    in_seed = ctx.server_locations
    # The Database records every fish / creature caught (Sea Kings too, which never reach the bag as themselves;
    # user 2026-10-23). The "ever obtained" bit is only a fallback while the Database can't be read.
    caught = g.database_caught()
    found |= {lid for gid, lid in CATCH_LOCS.items()
              if lid in in_seed and (gid in caught if caught is not None else g.found(gid))}
    levels = g.move_levels()
    for lid, ci, mid, lv in MOVE_LOCS:
        if levels.get((ci, mid), 0) >= lv:
            found.add(lid)
    coop = g.coop_levels()
    for lid, cid, lv in COOP_LOCS:
        if coop.get(cid, 0) >= lv:
            found.add(lid)
    return found


async def game_loop(ctx: OPUCContext) -> None:
    g = ctx.mem
    if g is None:
        logger.error(f"dolphin-memory-engine is not installed ({IMPORT_ERROR}). "
                     f"Install it with: pip install dolphin-memory-engine")
        return
    was_hooked = False
    while not ctx.exit_event.is_set():
        await asyncio.sleep(0.25)
        try:
            if not g.hooked and not g.hook():
                if was_hooked:
                    logger.info("Lost Dolphin. Waiting for it to come back...")
                    was_hooked = False
                await asyncio.sleep(1)
                continue
            if not was_hooked:
                logger.info("Connected to Dolphin (ROUPAF).")
                was_hooked = True
                g.reset()                                # Dolphin may have been restarted
            if not ctx.slot:
                if g.in_game():
                    g.say_once("noslot", "Connect to the Archipelago server before loading a save "
                                         "(back to the title screen first).")
                continue                                 # change nothing until the server is connected
            ctx.step = "patches"
            # final boss: GameClear() sets the clear byte and asks for a reset right away, so look every pass
            if int(ctx.slot_data.get("goal", 0)) == 2 and not ctx.goal_sent and g.game_cleared():
                ctx.goal_sent = True
                ctx.finished_game = True
                Utils.async_start(ctx.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}]))
            g.check_restart()
            g.session_tick()
            if g.sessions != ctx.session_seen:              # title screen / Game Over / reload: start over
                ctx.session_seen = g.sessions
                ctx.keys_requested.clear()
                if ctx.give_pending:
                    g.cancel_give()
                    ctx.give_pending = None
            # Connected while a save was already loaded (user report: checks sent when connecting to the room after
            # the game was running): the title-screen patches and the locked move tables came too late for this
            # save, e.g. the game turns move EXP gathered while a move was locked into levels with the vanilla
            # tables. Nothing is read or given until the player goes back to the title screen and loads again.
            if not ctx.connect_checked:
                ctx.connect_checked = True
                if g.in_game():
                    ctx.late_session = g.sessions
                    logger.warning("A save was already loaded when the client connected. No checks are sent and no "
                                   "items are given for it: go back to the title screen (reset) and load your save "
                                   "again. Next time, connect the client at the title screen before loading.")
            g.apply_patches(ctx.slot_data)
            g.rename_placeholder()
            g.set_iron_scrap_gold(bool(int(ctx.slot_data.get("iron_scrap_gives_gold_energy", 0))))
            ctx.step = "table search"
            if g.settled() and g.needs_scan():
                await asyncio.to_thread(g.do_scan)       # finds the move / ability / enemy tables (slow)
            # A save from another seed / slot or one never played with this client (user report on 0.15.0: a save
            # from another folder sent Nami's Level 5 moves, fish and story flags) must not send its progress as
            # checks or get this seed's items. Decided once per loaded save, before the client marks it.
            if g.settled() and ctx.owner_session != g.sessions:
                owner = g.save_owner()
                if owner is not None:
                    ctx.owner_session = g.sessions
                    ctx.save_ok = owner in ("this", "fresh")
                    if not ctx.save_ok:
                        logger.warning("This save doesn't belong to this seed and slot ("
                                       + ("made with another seed or slot" if owner == "other"
                                          else "never played with the Archipelago client")
                                       + "). No checks are sent and no items are given. Load this seed's save "
                                         "(or start a new game) from the title screen.")
            if not g.settled():
                ctx.owner_session = -1
                ctx.save_ok = False
            elif not ctx.save_ok or g.sessions == ctx.late_session:
                ctx.step = "waiting for this seed's save"
                await asyncio.sleep(0.25)
                continue
            ctx.step = "applying items"
            have = received_counts(ctx)
            apply_items(ctx, g, have)
            ctx.step = "recipes and chests"
            g.set_chest_placeholders(set(CHEST_LOCS))
            # the vanilla Bug-Catcher Net recipe is only discovered once the Broken net has arrived
            hidden = set() if have["Broken Bug-Catcher Net"] else {("workshop", 1)}
            # recipes are discovered with their Art level: rows 8-15 need Art 1, 16-23 Art 2, 24-31 Art 3
            if int(ctx.slot_data.get("recipes_discovered_through_arts", 1)):
                levels = getattr(ctx, "art_levels", {})
                veiled = {(room, r) for room in ROOM_ART for r in range(32) if r // 8 > levels.get(room, 0)} - hidden
            else:
                veiled = set()
            g.clear_idea_callbacks()
            g.setup_recipes(ctx.comments, hidden, veiled)
            if g.settled():
                g.strip_fragment_drops(list(ctx.slot_data.get("vacuum_orbs", [85] * 5)))
            ctx.step = "reading checks"
            # Only once a save has been loaded for a few seconds, and only checks seen on two passes in a row: while
            # a save loads, flag sections and move tables can hold stale or half-written data (public 0.15.0
            # report: random checks sent on every boot of a French save).
            seen = (read_checks(ctx, g) & set(ctx.server_locations)) if g.settled() else set()
            new = (seen & ctx.last_seen) - ctx.sent - set(ctx.checked_locations)
            ctx.last_seen = seen
            ctx.passes += 1
            ctx.step = "done"
            g.remove_placeholders()
            if new:
                ctx.sent |= new
                await ctx.send_msgs([{"cmd": "LocationChecks", "locations": sorted(new)}])
        except RuntimeError:
            # Dolphin paused / closed, or a read outside game memory. Say where, once per place.
            where = traceback.format_exc().strip().splitlines()[-3:]
            key = " | ".join(where)
            if key not in g.messages_said:
                g.messages_said.add(key)
                logger.info("Memory read failed (will retry):\n" + "\n".join(where))
            ctx.last_error = f"{ctx.step}: " + " / ".join(where)
            g.hooked = False
        except Exception:
            ctx.last_error = f"{ctx.step}: " + traceback.format_exc().strip().splitlines()[-1]
            logger.error("Client error:\n" + traceback.format_exc())
            await asyncio.sleep(2)


def launch(*args) -> None:
    async def main(argv):
        parser = get_base_parser()
        a = parser.parse_args(argv)
        ctx = OPUCContext(a.connect, a.password)
        ctx.server_task = asyncio.create_task(server_loop(ctx), name="server loop")
        if tracker_loaded:
            ctx.run_generator()            # Universal Tracker's own copy of the world, for logic
            ctx.tags.discard("Tracker")    # this is a real game client, not a tracker-only one
        if gui_enabled:
            ctx.run_gui()
        ctx.run_cli()
        loop_task = asyncio.create_task(game_loop(ctx), name="game loop")
        await ctx.exit_event.wait()
        await ctx.shutdown()
        loop_task.cancel()

    import colorama
    colorama.just_fix_windows_console()
    asyncio.run(main(list(args)))
    colorama.deinit()
