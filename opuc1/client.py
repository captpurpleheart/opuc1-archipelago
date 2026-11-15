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
import uuid
from collections import Counter
from typing import Dict, List, Optional, Set, Tuple

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

from .data import (GABRI_COLOUR_ITEMS, gabri_colour_bars, RETIRED_TRAPS, ROD_GRADE_BYTES_4, line_level, rod_level_from_items, BASE_ID, CHARACTERS, CRAFTS, DUMMY_RECIPES, GAME, GOALS, ITEM_IDS, ITEM_TABLE, ITEMS,
                   LOCATION_IDS, LOCATIONS, SHRINE_ACCESS, ROOM_OPTIONS, ART_ITEMS, ROOM_ART,
                   MAP_FRAGMENT_GROUPS, BUILD_SITE_IDS, FRANKY_TRADES, POOL_ITEM_IDS, ROOM_ITEM, LOCATION_TABLE,
                   final_door_bosses)

try:
    from .game_state import (GO_REQ, BAG_CAPACITY, HIDDEN_ALSO_COMMENT, HIDDEN_AP_COMMENT, NO_LOCATION_COMMENT, GameState,
                             also_comes_comment, placeholder_comment, rod_level_byte, item_kind, caption_pages,
                             CAPTION_POSITIONS)
except ImportError as e:  # dolphin_memory_engine missing
    GameState = None
    IMPORT_ERROR = e

ID_TO_ITEM = {v: k for k, v in ITEM_IDS.items()}
# On-screen messages (0.26.0): everything you send to other players; of what you receive, by default only items
# with no in-game popup or info box of their own (user): Straw Hats, Build Site / Shrine Access, the crafting rooms,
# traps, Progressive Fishing Rod Level / Line and Progressive Gabri Level. "/messages moves on" adds moves / skills /
# co-op moves, "/messages inventory on" everything else (tools, key items, food ...). Settings: /messages.
CAPTION_KINDS = {"character", "shrine", "room", "trap", "rod_level", "rod_line", "gabri", "gabri_colour", "cannon"}
CAPTION_MOVE_KINDS = {"move", "ability", "coop"}
CAPTION_COLOURS = {"Progression": "AF99EF", "Useful": "6D8BE8", "Filler": "00EEEE", "Trap": "FA8072"}   # AP's own
MESSAGE_DEFAULTS = {"on": True, "sent": True, "received": True, "inventory": False, "moves": False, "colour": True,
                    "scale": 0.8, "time": 4.0, "outline": 1.5, "position": "top"}
MESSAGE_SWITCHES = ("on", "sent", "received", "inventory", "moves", "colour")


# Energy Link (0.29.0, option energy_link): joules per Gabri Energy point (100 = one bar) per slot (Red, Green, Blue,
# White, Black, Gold): 10 MJ, Gold twice as expensive. Converting into the bank keeps 80% (a 20% cut).
EL_JOULES = [10_000_000] * 5 + [20_000_000]
EL_KEEP = 0.8
EL_NAMES = ["Red", "Green", "Blue", "White", "Black", "Gold"]


def caption_rgb(flags: int, colour: bool = True) -> Tuple[float, float, float]:
    if not colour:
        return (1.0, 1.0, 1.0)
    kind = "Trap" if flags & 4 else item_kind(flags) if GameState else "Filler"
    h = CAPTION_COLOURS[kind]
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _settings_path() -> str:
    return Utils.user_path("opuc1_messages.json")


def load_message_settings() -> dict:
    out = dict(MESSAGE_DEFAULTS)
    try:
        with open(_settings_path()) as f:
            out.update({k: v for k, v in json.load(f).items() if k in MESSAGE_DEFAULTS})
    except (OSError, ValueError):
        pass
    return out


def save_message_settings(st: dict) -> None:
    try:
        with open(_settings_path(), "w") as f:
            json.dump(st, f, indent=1)
    except OSError:
        pass


def caption_offset(pos) -> Tuple[float, float]:
    if isinstance(pos, (list, tuple)) and len(pos) == 2:
        return (float(pos[0]), float(pos[1]))
    return CAPTION_POSITIONS.get(str(pos), CAPTION_POSITIONS["top"])
GABRI_LEVELS = ITEM_TABLE["Progressive Gabri Level"].count     # 13
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
# net (and its "ever obtained" bit), so the client must not give the Broken net again (user report, 2026-10-26:
# Broken net back after crafting the net). (Rods and vacuum are handled through their slot bytes, not replaced.)
SUPERSEDED_BY = {3: (2,)}
SUNNY_FLAG = 11990          # "First Step on the Thousand Sunny": the Pickaxe is held back until then
# The first arrival on the Sunny (script 11990) then plays the crew meeting scene 10070 (several fades and a
# tutorial). An item event started during it (the Pickaxe's event 201 right on arrival, with Early Pickaxe) held the
# game on a black screen (user, 0.25.1 / 0.25.2). Nothing is handed over until 10070 has finished.
SUNNY_SCENE = 10070
MOVE_LOCS = [(lid, c[1], c[2], c[3]) for lid, c in CHECKS_BY_KIND.get("move", [])]
CATCH_LOCS = {c[1]: lid for lid, c in CHECKS_BY_KIND.get("catch", [])}     # fish / creature item -> location
MATERIAL_LOCS = {c[1]: lid for lid, c in CHECKS_BY_KIND.get("material", [])}  # Materialsanity: item -> location
DUMMY_CRAFTS = {(room, row) for room, row, _, dummy in CRAFTS if dummy}


def franky_on(sd: dict) -> bool:
    return bool(int(sd.get("franky_supplies", 0)))


def dust_spot_items(sd: dict) -> List[int]:
    """The Sunny's 5 dust spots: the seed's random Orbs, or Old Gold Coins with Franky's Supplies (0.33.4, user)."""
    return [79] * 5 if franky_on(sd) else list(sd.get("vacuum_orbs", [85] * 5))


def recipe_rooms(sd: dict) -> Tuple[str, ...]:
    """Crafting menus the client manages (Franky's Supplies = dev2 only with franky_supplies, 0.30.0)."""
    return ("workshop", "kitchen", "pharmacy") + (("franky",) if franky_on(sd) else ())


def custom_recipes(sd: dict) -> Dict[Tuple[str, int], Tuple[int, List[Tuple[int, int]], bool]]:
    """Rows the client writes (0.30.0): random recipes from the slot data (Archipelago results) and Franky's fixed
    trades (real results)."""
    out = {(room, int(row)): (0, [(int(g), int(n)) for g, n in ing], True)
           for room, row, ing in sd.get("extra_recipes", [])}
    if franky_on(sd):
        for row, (res, ing) in FRANKY_TRADES.items():
            out[("franky", row)] = (POOL_ITEM_IDS[res], [(POOL_ITEM_IDS[n], c) for n, c in ing], False)
    return out
CONSUMABLE_KINDS = {"filler"}
TRAP_MS, TRAP_GAP = 5000, 2.0      # each trap's status time (ms, as tested by the user) and a pause between traps


class OPUCCommandProcessor(ClientCommandProcessor):
    def _cmd_messages(self, *args: str) -> None:
        """On-screen messages. /messages = show settings. /messages on|off; sent|received|inventory|moves|colour on|off;
        scale 0.8; time 4 (seconds); outline 1.5 (0 = none); position top|topleft|topright|middle|bottom|lower|left|
        right or position X Y; test; reset."""
        ctx = self.ctx
        if not isinstance(ctx, OPUCContext):
            return
        st = ctx.msg
        a = [x.lower() for x in args]
        try:
            if not a:
                pass
            elif a[0] in ("on", "off"):
                st["on"] = a[0] == "on"
            elif a[0] in MESSAGE_SWITCHES and len(a) >= 2 and a[1] in ("on", "off"):
                st[a[0]] = a[1] == "on"
            elif a[0] in ("scale", "time", "outline") and len(a) >= 2:
                v = float(a[1])
                lo, hi = {"scale": (0.3, 2.0), "time": (1.0, 30.0), "outline": (0.0, 5.0)}[a[0]]
                st[a[0]] = max(lo, min(hi, v))
            elif a[0] == "position" and len(a) >= 2:
                if a[1] in CAPTION_POSITIONS:
                    st["position"] = a[1]
                elif len(a) >= 3:
                    st["position"] = [float(a[1]), float(a[2])]
                else:
                    raise ValueError(a[1])
            elif a[0] == "test":
                for kind, flags in (("Progression", 1), ("Useful", 2), ("Filler", 0), ("Trap", 4)):
                    ctx.queue_caption(f"Sent Example {kind} Item to Someone", flags)
                logger.info("Four test messages queued (they show in the game once a save is loaded).")
                return
            elif a[0] == "reset":
                st.clear()
                st.update(MESSAGE_DEFAULTS)
            else:
                raise ValueError(a[0])
        except ValueError:
            logger.info("Not understood. " + (self._cmd_messages.__doc__ or ""))
            return
        save_message_settings(st)
        pos = st["position"]
        logger.info("On-screen messages: " + ("on" if st["on"] else "off")
                    + " | " + ", ".join(f"{k} {'on' if st[k] else 'off'}" for k in MESSAGE_SWITCHES[1:])
                    + f" | scale {st['scale']:g}, time {st['time']:g} s, outline {st['outline']:g}, position "
                    + (pos if isinstance(pos, str) else f"{pos[0]:g} {pos[1]:g}"))

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
        self.custom_recipes: Dict[Tuple[str, int], Tuple[int, List[Tuple[int, int]], bool]] = {}
        self.ap_rows: Set[Tuple[str, int]] = set(DUMMY_CRAFTS)
        self.sent: Set[int] = set()
        self.goal_sent = False
        self.last_seen: Set[int] = set()
        self.owner_session = -1             # game session whose save owner was checked
        self.late_session = None            # session that was already running when the client connected
        self.costume_pending: Set[int] = set()     # Straw Hats still to get their Starting Costume (progress file)
        self.connect_checked = False
        self.save_ok = False
        self.delivered = 0          # how many received items have had their one-time delivery (consumables)
        self.traps_done = 0         # received traps already played (kept in the progress file, not the save)
        self.traps_ahead: Set[int] = set()   # traps played out of order (a Burn Trap waiting on the Sunny was skipped)
        self.death_pending: Optional[str] = None     # Death Link received, not applied yet (source)
        self.death_applied_at = 0.0                  # when we last applied one (its fall isn't sent back)
        self.fallen_prev: Optional[Set[int]] = None  # Straw Hats down on the last pass
        self.trap_state: Optional[dict] = None       # current trap: phase pending / active / ending, name, since, ms
        self.hp_prev: Optional[Dict[int, Tuple[int, int]]] = None   # Straw Hats' HP on the last pass (Death Link)
        self.owned_chars: Set[int] = set()           # Straw Hats you can play (start character + received)
        self.wardrobe_done = False                   # wardrobe spots switched on during this Sunny visit
        self.cannon_asked = -1e9                     # last time the Wherever Cannon's event 10010 was requested
        self.go_prev = False                         # Game Over revive flag on the last pass (Death Link)
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
        self.armed_traps: List[Tuple[str, str]] = []     # received traps not played yet
        self.bag_full_said = False
        self.last_give = "none"
        self.session_seen = 0       # GameState.sessions when per-session state was last reset
        self.keys_requested: Set[int] = set()
        self.last_was_event = False             # the last paced give started an event (0.25.11)
        self.settle_needed = False              # something was handed over and the game hasn't been quiet since
        # Paced deliveries (0.25.2): items with events, crew members and move unlock checks wait for a quiet game
        self.quiet_since: Optional[float] = None     # when the game last became idle (None while something plays)
        self.unlock_wanted = False                   # a move unlock check is due once the game is quiet
        self.unlock_retry_at = 0.0
        self.crew_given: Set[int] = set()            # Straw Hats handed over so far this session
        self.crew_session = -1
        self.repaired: Set[int] = set()              # leftover event items already cleaned up (logged once)
        self.arrival_scene = False                   # the first Sunny arrival scene (10070) is still to finish
        self.last_counter: Optional[int] = None      # hook frame counter on the last pass (game running?)
        self.captions: List[Tuple[str, Tuple[float, float, float]]] = []   # on-screen messages still to show
        self.msg = load_message_settings()                                  # /messages settings (own file)
        # Gabri Energy tab / Energy Link (0.29.0)
        self.gabri_view: Optional[Tuple[List[int], List[int]]] = None      # (max, current) per slot, from the game
        self.energy_requests: List[Tuple[str, int, int]] = []              # (convert / withdraw, slot, Energy)
        self.energy_pending: Dict[str, Tuple[int, int]] = {}               # Set tag -> (slot, Energy asked for)
        self.energy_reserved = [0] * 6                                      # room held for withdrawals on the way
        self.energy_incoming: List[Tuple[int, int, int]] = []              # (slot, Energy, asked) to add in game

    # ---- Energy Link (Gabri Energy tab)
    def energy_key(self) -> str:
        return f"EnergyLink{self.team}"

    def energy_link_on(self) -> bool:
        return bool(self.slot) and bool(int(self.slot_data.get("energy_link", 0)))

    def energy_bank(self) -> Optional[float]:
        v = self.stored_data.get(self.energy_key()) if self.team is not None else None
        if v is None:
            v = self.current_energy_link_value
        return v

    def request_energy(self, op: str, slot: int, amount: int) -> None:
        """From the tab's Convert / Withdraw buttons; done by the game loop (it owns the Dolphin connection)."""
        if not self.energy_link_on():
            logger.info("Energy Link is off for this slot (YAML option energy_link).")
            return
        if amount <= 0:
            return
        self.energy_requests.append((op, slot, amount))

    def energy_set(self, value: float, tag: Optional[str] = None) -> None:
        msg = {"cmd": "Set", "key": self.energy_key(), "default": 0,
               "operations": [{"operation": "add", "value": value}]}
        if tag:
            msg.update(want_reply=True, tag=tag)
            msg["operations"].append({"operation": "max", "value": 0})
        Utils.async_start(self.send_msgs([msg]))

    def energy_reply(self, args: dict) -> None:
        """SetReply to one of our withdrawals: what was really taken (the bank may have had less)."""
        slot, asked = self.energy_pending.pop(args["tag"])
        rate = EL_JOULES[slot]
        taken = max(0.0, float(args.get("original_value", 0) or 0) - float(args.get("value", 0) or 0))
        energy = min(asked, int(taken // rate))
        rest = taken - energy * rate
        if rest > 0:
            self.energy_set(rest)               # the part that doesn't make a whole Energy point goes back
        self.energy_incoming.append((slot, energy, asked))

    def queue_caption(self, text: str, flags: int) -> None:
        if not self.mem:
            return
        rgb = caption_rgb(flags, bool(self.msg.get("colour", True)))
        self.captions += [(page, rgb) for page in caption_pages(text)]
        del self.captions[:-20]                          # never pile up more than a screenful of backlog

    def on_print_json(self, args: dict) -> None:
        super().on_print_json(args)
        try:
            st = self.msg
            if args.get("type") != "ItemSend" or not self.mem or not self.slot or not st.get("on", True):
                return
            item = args.get("item")
            if not isinstance(item, NetworkItem):
                item = NetworkItem(*item)
            receiver = args.get("receiving")
            name = self.item_names.lookup_in_slot(item.item, receiver)
            if item.player == self.slot and receiver != self.slot:
                if not st.get("sent", True):
                    return
                text = f"Sent {name} to {self.player_names.get(receiver, 'someone')}"
            elif receiver == self.slot:
                d = ITEM_TABLE.get(ID_TO_ITEM.get(item.item, ""))
                if not d or not st.get("received", True):
                    return
                if d.kind in CAPTION_KINDS:
                    pass
                elif d.kind in CAPTION_MOVE_KINDS:
                    if not st.get("moves", False):
                        return
                elif not st.get("inventory", False):
                    return
                text = (f"Found {name}" if item.player == self.slot
                        else f"Received {name} from {self.player_names.get(item.player, 'someone')}")
            else:
                return
            self.queue_caption(text, item.flags)
        except Exception as e:
            logger.debug(f"on-screen message skipped: {e}")

    def on_deathlink(self, data: dict) -> None:
        super().on_deathlink(data)
        self.death_pending = data.get("source", "someone")

    async def server_auth(self, password_requested: bool = False):
        if password_requested and not self.password:
            await super().server_auth(password_requested)
        await self.get_username()
        await self.send_connect()

    def on_package(self, cmd: str, args: dict):
        if cmd == "Connected":
            self.slot_data = args.get("slot_data", {})
            Utils.async_start(self.update_death_link(bool(int(self.slot_data.get("death_link", 0)))))
            self.sent = set(args.get("checked_locations", []))
            self.load_progress()
            if self.mem:
                self.mem.seed_tag = zlib.crc32(f"{self.seed_name}:{self.slot}".encode()) or 1
            for room, rows in self.slot_data.get("dummy_recipes", {}).items():
                for row in rows:
                    if (room, row) not in CRAFT_LOCS or CRAFT_LOCS[(room, row)] not in self.server_locations:
                        self.comments[(room, row)] = NO_LOCATION_COMMENT
            # Rows whose result is the Archipelago Item: key-item recipes and the random recipes (0.30.0)
            self.custom_recipes = custom_recipes(self.slot_data)
            self.ap_rows = set(DUMMY_CRAFTS) | {k for k, v in self.custom_recipes.items() if v[2]}
            # vanilla-result recipes: "also comes with ..." when they're a location here, otherwise "not a Location"
            dummy_rows = {(room, row) for room, rows in self.slot_data.get("dummy_recipes", {}).items() for row in rows}
            dummy_rows |= self.ap_rows
            for room in recipe_rooms(self.slot_data):
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
                        self.comments[key] = HIDDEN_AP_COMMENT if key in self.ap_rows else HIDDEN_ALSO_COMMENT
            if scout:
                Utils.async_start(self.send_msgs([{"cmd": "LocationScouts", "locations": scout, "create_as_hint": 0}]))
            # Energy Link: watch the team's bank (0.29.0)
            self.energy_pending.clear()
            self.energy_reserved = [0] * 6
            if int(self.slot_data.get("energy_link", 0)):
                Utils.async_start(self.send_msgs([{"cmd": "Get", "keys": [self.energy_key()]},
                                                  {"cmd": "SetNotify", "keys": [self.energy_key()]}]))
        elif cmd == "SetReply" and args.get("tag") in self.energy_pending:
            self.energy_reply(args)
        elif cmd == "LocationInfo":
            by_id = {v: k for k, v in CRAFT_LOCS.items()}
            for item in args.get("locations", []):
                key = by_id.get(item.location)
                if key:
                    player = self.player_names.get(item.player, "someone")
                    name = self.item_names.lookup_in_slot(item.item, item.player)
                    kind = item_kind(item.flags)
                    self.comments[key] = (placeholder_comment(player, name, kind) if key in self.ap_rows
                                          else also_comes_comment(player, name, kind))
        super().on_package(cmd, args)    # Universal Tracker listens to the same messages

    # ---- one-time deliveries survive client restarts (per seed and slot)
    def _progress_file(self) -> str:
        return Utils.user_path(f"opuc1_{self.seed_name}_{self.slot}.json")

    def load_progress(self) -> None:
        try:
            with open(self._progress_file()) as f:
                data = json.load(f)
            self.delivered = data.get("delivered", 0)
            self.traps_done = data.get("traps", 0)
            self.traps_ahead = set(data.get("traps_ahead", []))
            self.costume_pending = set(data.get("costumes_pending", []))
        except (OSError, ValueError):
            self.delivered = 0
            self.traps_done = 0
            self.traps_ahead = set()
            self.costume_pending = set()

    def save_progress(self) -> None:
        try:
            with open(self._progress_file(), "w") as f:
                json.dump({"delivered": self.delivered, "traps": self.traps_done,
                           "traps_ahead": sorted(self.traps_ahead),
                           "costumes_pending": sorted(self.costume_pending)}, f)
        except OSError:
            pass

    def armed_text(self) -> str:
        rows = self.armed_keys + self.armed_items
        if not rows:
            return "Nothing is waiting: every item received so far has been given to you."
        return "\n".join(f"{name}  [color=#9a9a9a]({why})[/color]" for name, why in rows)

    def gabri_text(self) -> str:
        n = sum(1 for it in self.items_received if ID_TO_ITEM.get(it.item) == "Progressive Gabri Level")
        return f"Gabri Level: {min(n, GABRI_LEVELS)}/{GABRI_LEVELS}"

    def make_gui(self):
        ui = super().make_gui()          # Archipelago's window, or Universal Tracker's
        ctx = self

        class OPUCManager(ui):
            base_title = "One Piece Unlimited Cruise 1 Client"

            def build(self):
                container = super().build()
                try:
                    from .gabri_tab import build_gabri_tab
                    self.add_client_tab("Gabri Energy", build_gabri_tab(ctx))
                except Exception as e:   # never let the extra tab stop the client from opening
                    logger.warning(f"Gabri Energy tab not available: {e}")
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
                # (0.28.0: the Gabri Level counter by the Connect button is removed for now; user - that spot is
                # kept for something else later. ctx.gabri_text() still works for /status-style use.)
                return container

        return OPUCManager


def energy_link_pass(ctx: OPUCContext, g: "GameState") -> None:
    """Gabri Energy tab (0.29.0): refresh the meters, then carry out Convert / Withdraw requests and add Energy that
    arrived from the bank. Runs in a settled game (save loaded, this seed's)."""
    ctx.gabri_view = g.gabri_energy()
    if not ctx.energy_link_on():
        ctx.energy_requests.clear()
        return
    while ctx.energy_incoming:
        slot, energy, asked = ctx.energy_incoming.pop(0)
        ctx.energy_reserved[slot] = max(0, ctx.energy_reserved[slot] - asked)
        added = g.add_gabri_energy(slot, energy) if energy > 0 else 0
        if energy - added > 0:                       # no room after all: back into the bank, no cut
            ctx.energy_set((energy - added) * EL_JOULES[slot])
        if added:
            logger.info(f"Energy Link: withdrew {added} {EL_NAMES[slot]} Energy.")
        elif energy == 0:
            logger.info("Energy Link: the bank is empty.")
    while ctx.energy_requests:
        op, slot, amount = ctx.energy_requests.pop(0)
        view = g.gabri_energy()
        if not view:
            return
        mx, cur = view
        if op == "convert":
            taken = -g.add_gabri_energy(slot, -min(amount, cur[slot]))
            if taken > 0:
                ctx.energy_set(int(taken * EL_JOULES[slot] * EL_KEEP))
                logger.info(f"Energy Link: converted {taken} {EL_NAMES[slot]} Energy "
                            f"({Utils.format_SI_prefix(int(taken * EL_JOULES[slot] * EL_KEEP))}J into the bank).")
            else:
                logger.info(f"Energy Link: no {EL_NAMES[slot]} Energy to convert.")
        else:
            room = mx[slot] - cur[slot] - ctx.energy_reserved[slot]
            amount = min(amount, room)
            if amount <= 0:
                logger.info(f"Energy Link: {EL_NAMES[slot]} Energy is already at its cap.")
                continue
            tag = str(uuid.uuid4())
            ctx.energy_pending[tag] = (slot, amount)
            ctx.energy_reserved[slot] += amount
            ctx.energy_set(-amount * EL_JOULES[slot], tag)
    ctx.gabri_view = g.gabri_energy()


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
    ctx.owned_chars = owned_chars
    sunny_flags = g.script_flags([SUNNY_FLAG, SUNNY_SCENE])
    ctx.arrival_scene = SUNNY_FLAG in sunny_flags and SUNNY_SCENE not in sunny_flags
    update_quiet(ctx, g)
    g.enforce_crew(paced_crew(ctx, g, owned_chars, start), start)

    # Thousand Sunny options: 0 vanilla (Workshop open; Kitchen / Pharmacy from chapter 3, after the
    # Island 1 boss), 1 own item, 2 the room's owner, 3 both
    sd = ctx.slot_data
    rooms = set()
    for d in ITEMS:
        if d.kind != "room":
            continue
        unlock_opt, _a, ci = ROOM_OPTIONS[d.data]
        mode = int(sd.get(unlock_opt, 1))
        if d.data == "franky":            # Franky's Supplies (0.30.0): 0 start_with, 1 item, 2 Franky, 3 both
            ok = franky_on(sd) and (mode == 0 or ((mode == 2 or bool(have[d.name]))
                                                  and (mode == 1 or ci in owned_chars)))
        elif mode == 4:                     # start_with (Kitchen / Pharmacy)
            ok = True
        elif mode == 0:                   # Workshop start_with; Kitchen / Pharmacy vanilla
            ok = d.data == "workshop" or g.chapter() >= 3
        else:
            ok = (mode == 2 or bool(have[d.name])) and (mode == 1 or ci in owned_chars)
        if ok:
            rooms.add(d.data)
    g.set_rooms(rooms)
    # Next Island menu: islands in the seed open with their island item; the others keep the vanilla rule
    # (0.21.0 slot data lists them: every island; older seeds: decided by the goal)
    goal = int(sd.get("goal", 0))
    ch = g.chapter()
    log = {d.data: bool(have[d.name]) for d in ITEMS if d.kind == "island"}
    by_item = set(sd.get("islands", [n for n, need in ((2, 1), (5, 2)) if goal >= need]))
    vanilla = {2: ch > 2, 3: ch > 3, 4: ch > 4, 5: ch > 5}
    g.set_islands({1: True, **{n: (log.get(n, False) if n in by_item else vanilla[n]) for n in vanilla}})
    # Art of Development / Cooking / Compounding wait for their owner when that option is on
    art_held = {ci for _u, art_opt, ci in ROOM_OPTIONS.values() if int(sd.get(art_opt, 0)) and ci not in owned_chars}
    if int(sd.get("gabri_energy_items", 0)):        # one item per colour bar (0.28.0)
        mode = int(sd.get("gabri_level_items", 10))
        start = int(sd.get("starting_gabri_energy", 1))           # 0.28.0 - 0.29.x seeds: 1 Blue bar
        g.set_gabri_bars([gabri_colour_bars(ci, have[item], mode, start) for ci, item in enumerate(GABRI_COLOUR_ITEMS)])
    else:
        g.set_gabri(have["Progressive Gabri Level"])
    # Build Sites (x11-x16) also wait for Franky with franky_required_for_build_sites
    franky_ok = not int(sd.get("franky_required_for_build_sites", 0)) or 7 in owned_chars
    unlocked = {sid for name, sid in SHRINE_ACCESS.items()
                if have[name] and (sid not in BUILD_SITE_IDS or franky_ok)}
    # Extra Final Door Requirement (0.31.0): The Final Door also waits for the bosses
    door_flags = [LOCATION_TABLE[n].check[1] for n in final_door_bosses(int(sd.get("extra_final_door_requirement", 0)))]
    if door_flags and 500 in unlocked and len(g.script_flags(door_flags)) < len(door_flags):
        unlocked.discard(500)
    g.set_shrine_locks(unlocked)
    g.set_monuments(not int(sd.get("robin_required_for_monuments", 0)) or 6 in owned_chars)
    maps_held = bool(int(sd.get("nami_required_for_maps", 0))) and 4 not in owned_chars
    sunny = sunny_flags == {SUNNY_FLAG, SUNNY_SCENE}

    # "Armed" items (received, held back by the client) for the Armed Items tab, in delivery priority order
    armed: List[Tuple[str, str]] = []
    if have["Pickaxe"] and not sunny:
        armed.append(("Pickaxe", "Waiting for Thousand Sunny entry (and the crew's scene there)"))
    for room in recipe_rooms(sd):
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
            g.strip_fragment_drops(dust_spot_items(ctx.slot_data))
        g.set_blue_orb_spot(70 if int(ctx.slot_data.get("blue_orb_spot_gives_iron_ore", 0)) else 81)
        sd = ctx.slot_data
        better_dig = sd.get("better_random_dig_item_rates", sd.get("higher_random_dig_chance", 0))
        g.set_ground_dig_chance(0.25 if int(better_dig) else 0.05)
        g.set_creature_drops(bool(int(ctx.slot_data.get("guaranteed_creature_drops", 0))))
        # Enemy Gunpowder Drop Rate (0.25.0, %); older seeds: Easier Gunpowder Drops (on = 20, or the old % value)
        rate = sd.get("enemy_gunpowder_drop_rate")
        if rate is None and int(sd.get("easier_gunpowder_drops", 0)):
            rate = 20 if int(sd["easier_gunpowder_drops"]) == 1 else int(sd["easier_gunpowder_drops"])
        if rate is not None:
            g.set_gunpowder_drops(int(rate))
        if int(ctx.slot_data.get("better_plant_drop_rates", 0)):
            g.set_plant_drops()
        if int(sd.get("expanded_storage", 0)):
            g.manage_storage()                         # 45 Storage slots (0.32.0)
        if int(ctx.slot_data.get("equalise_fish_rates", 0)):
            g.set_fish_rates()
        if int(ctx.slot_data.get("quick_recipes", 0)):
            g.set_quick_recipes()
        g.set_max_stacks(craft_max=bool(int(sd.get("stack_craftables_make_max_copies", 0))))   # 100 stacks
        g.install_hook()
        if ctx.captions and g.caption_ready():          # on-screen messages: one hand-over per pass, the game queues
            text, rgb = ctx.captions.pop(0)
            st = ctx.msg
            g.show_caption(text, rgb, frames=int(float(st["time"]) * 60), scale=float(st["scale"]),
                           border=float(st["outline"]), offset=caption_offset(st["position"]))
        energy_link_pass(ctx, g)
        changed = g.write_tables(moves, abilities) | g.write_coop(coop)
        if changed or new_scan:
            ctx.unlock_wanted = True        # asked for once the game is quiet (paced_events)
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
        if int(ctx.slot_data.get("chopper_brook_cold_resistance", 0)):
            g.patch_cold_resistance()   # Chopper / Brook never get the cold mark
        if int(ctx.slot_data.get("aquarium_open", 1)):
            g.patch_aquarium()          # Aquarium (and the helm) open from the start
        g.write_exp(1 + int(ctx.slot_data.get("move_exp_multiplier", 0)))   # 0 off, 1-4 = 2x-5x
        # "Walk the Sunny" -> Costume Change was dropped (0.20.3: held the game early on); undo it if an older
        # client / the test tool left it in memory
        g.set_walk_costumes(False)
        apply_starting_costumes(ctx, g)

    paced_events(ctx, g)
    deliver(ctx, g, key_items)
    wardrobe(ctx, g, have)
    wherever_cannon(ctx, g, have)
    ctx.armed_traps = deliver_traps(ctx, g)
    death_link(ctx, g)


def apply_starting_costumes(ctx: "OPUCContext", g: "GameState") -> None:
    """Starting Costumes (new game): each Straw Hat gets their costume (+0xC0) / style (+0xEC) when they are the one
    in play, followed straight away by the game's own costume reload (hook command 4, CharaChangeCostume).
    0.25.5: costumes used to be written for all nine at once, leaving the eight not in play with a costume that
    differed from their loaded model (+0xC4); the first fade back from a menu then held the game on a black screen
    (user: only with Thriller Bark costumes, only until the save was reloaded). Who still needs theirs is kept in the
    progress file, so it survives saving and reloading."""
    if not ctx.costume_pending:
        return
    wanted = ctx.slot_data.get("starting_costumes")
    if not wanted:
        ctx.costume_pending = set()
        return
    player = g.player_index()
    if player is None or player not in ctx.costume_pending or not quiet_for(ctx, 1.0):
        return
    c, st = wanted[player]
    g.set_costume(player, c, st)
    if g.refresh_costume():
        ctx.costume_pending.discard(player)
        ctx.save_progress()
        used_quiet(ctx)


# ---- Paced deliveries (0.25.2) -------------------------------------------------------------------------------
# A burst of received items (someone goaling / releasing) used to start several item events, "new move" pop-ups and
# crew joins at once; the game dropped some of them, so their effects never happened (Palette Upgrade not applied,
# Jet Dial / Hammer Comet / Violin Strings not vanishing, maps not assembled; user 2026-11-03). Now each of those
# waits for a quiet game, and leftovers are cleaned up afterwards.
# 0.25.11 (user: receiving felt slower): filler 1.0 -> 0.5 s, key items 2.0 -> 1.0 s, except straight after another
# event (key item, crew join, move unlock check), which still gets the longer gap.
# 0.25.12 (user test): everything 0.5 s, 1.0 s when an event follows another event (crew joins and move unlock
# checks now get the longer gap too).
# 0.25.13 (user): crew joins are instant (no event; shrine unlocks were never paced), everything else 0.1 s, and
# 0.5 s when an event follows another event (key item, move unlock check).
KEY_QUIET, FILLER_QUIET, UNLOCK_QUIET, REPAIR_QUIET = 0.1, 0.1, 0.1, 4.0
EVENT_AFTER_EVENT_QUIET = 0.1   # 0.25.14 (user): no extra gap between events, the quiet check is what matters
UNLOCK_RETRY = 15.0
# Items the game uses up once their move / co-op is learned, and what proves it was learned. If it was but the item
# is still carried (the unlock pop-up was dropped in a burst), the client removes it; if it wasn't, the client asks
# the game for another move unlock check (the pop-up plays then). Bag / Palette upgrades aren't here: the client
# sets their sizes itself every pass.
EVENT_ITEM_RESULTS: Dict[int, Tuple[str, Tuple[int, ...]]] = {
    95: ("move", (4, 13)), 170: ("move", (2, 15)), 171: ("move", (5, 7)), 172: ("move", (2, 11)),
    173: ("move", (5, 6)), 174: ("move", (7, 13)), 175: ("move", (8, 7)), 176: ("move", (2, 14)),
    177: ("coop", (3,)),
}


def update_quiet(ctx: "OPUCContext", g: "GameState") -> None:
    """Quiet = idle AND the game actually running frames: the hook counter has moved since the last pass. While the
    game is paused or in a full-screen menu (pause / save / item menus) the hook doesn't run; a give requested then
    fired on the first frame after the menu closed, in the middle of the fade back in, and held the game on a black
    screen (user, 0.25.1 / 0.25.2: after unpausing / saving on the Sunny)."""
    counter = g.hook_counter()
    running = ctx.last_counter is not None and counter != ctx.last_counter
    ctx.last_counter = counter
    if running and g.settled() and g.game_idle() and not ctx.arrival_scene:
        if ctx.quiet_since is None:
            ctx.quiet_since = time.monotonic()
    else:
        ctx.quiet_since = None


def quiet_for(ctx: "OPUCContext", seconds: float) -> bool:
    return ctx.quiet_since is not None and time.monotonic() - ctx.quiet_since >= seconds


def used_quiet(ctx: "OPUCContext", event: bool = False) -> None:
    """Something was just handed to the game: the next thing waits for a fresh quiet stretch. event = it starts an
    event / pop-up of its own (key item, crew join, move unlock check)."""
    ctx.quiet_since = None
    ctx.last_was_event = event
    ctx.settle_needed = True


def paced_ready(ctx: "OPUCContext", seconds: float) -> bool:
    """0.25.16 (user): only bursts needed pacing. A delivery goes out straight away unless something was handed to
    the game and the game hasn't been quiet for `seconds` since; then it waits for that quiet stretch (which also
    ends the burst, so the next lone item is instant again). Death Link, traps and the costume fallback still use
    quiet_for."""
    if not getattr(ctx, "settle_needed", False):
        return True
    if quiet_for(ctx, seconds):
        ctx.settle_needed = False
        return True
    return False


def key_quiet(ctx: "OPUCContext", base: float = KEY_QUIET) -> float:
    return max(base, EVENT_AFTER_EVENT_QUIET) if getattr(ctx, "last_was_event", False) else base


def paced_crew(ctx: "OPUCContext", g: "GameState", owned: Set[int], start: int) -> Set[int]:
    """Which Straw Hats are in the crew. 0.25.2-0.25.12 let them join one at a time after a quiet stretch; joining
    starts no event, so since 0.25.13 everyone owned joins straight away."""
    if ctx.crew_session != g.sessions:
        ctx.crew_session = g.sessions
        ctx.crew_given = (g.joined() & owned) | {start}
    ctx.crew_given |= owned                     # 0.25.13: instant (joining starts no event)
    ctx.crew_given &= owned | {start}
    return set(ctx.crew_given)


def paced_events(ctx: "OPUCContext", g: "GameState") -> None:
    """Move unlock checks (the game's "new move" pop-ups) only on a quiet game, and a cleanup of event items whose
    event was dropped."""
    if not g.settled():
        return
    now = time.monotonic()
    if ctx.unlock_wanted and ctx.give_pending is None and paced_ready(ctx, key_quiet(ctx, UNLOCK_QUIET)):
        ctx.unlock_wanted = False
        ctx.unlock_retry_at = now + UNLOCK_RETRY
        g.request_unlock_check()
        used_quiet(ctx, event=True)
        return
    if ctx.give_pending is not None or not quiet_for(ctx, REPAIR_QUIET):
        return
    levels = coop = None
    for gid, (kind, arg) in EVENT_ITEM_RESULTS.items():
        if not g.find_slots(gid):
            continue
        if kind == "move":
            levels = levels if levels is not None else g.move_levels()
            done = levels.get(arg, 0) >= 1
        else:
            coop = coop if coop is not None else g.coop_levels()
            done = coop.get(arg[0], 0) >= 1
        if done:
            g.remove_item(gid)
            if gid not in ctx.repaired:
                ctx.repaired.add(gid)
                logger.info(f"Cleaned up item {gid}: its event had been skipped, but its effect is in place.")
        elif now >= ctx.unlock_retry_at:
            ctx.unlock_wanted = True             # the item is here but its move isn't: let the game check again


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
        if not g.found(gid) and gid not in ctx.keys_requested and not paced_ready(ctx, key_quiet(ctx)):
            return                                  # paced: key items (most have an event) wait for a quiet game
        if any(g.found(u) or g.find_slots(u) for u in SUPERSEDED_BY.get(gid, ())):
            continue                                # already upgraded in game (e.g. net crafted): don't give it back
        if not g.found(gid) and gid not in ctx.keys_requested:
            ctx.keys_requested.add(gid)
            g.request_give(gid)
            ctx.give_pending = ("key", gid, now, 0, None)
            used_quiet(ctx, event=True)
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
            if not paced_ready(ctx, FILLER_QUIET):
                return                              # paced: never on top of an event or another item's message
            before = g.item_count(gid)
            g.request_give(gid, n)
            ctx.give_pending = ("filler", gid, now, before, None)
            used_quiet(ctx)
            return
        ctx.delivered += 1
        g.write_delivered(ctx.delivered)
        ctx.save_progress()


def wardrobe(ctx: "OPUCContext", g: "GameState", have) -> None:
    """The Garment Box's own event only shows the Sunny's wardrobe spots if it is received on the Sunny (user,
    0.22.3). With the box received and known in game, switch them on once per visit to the Sunny (hook command 8)."""
    sunny = g.on_sunny() if g.settled(3) else None
    if sunny is not True:
        if sunny is False:
            ctx.wardrobe_done = False
        return
    if not ctx.wardrobe_done and have["Garment Box"] and g.found(92) and g.request_wardrobe():
        ctx.wardrobe_done = True


# The Wherever Cannon as an item (0.34.0, option wherever_cannon_unlock own_item / start_with). Vanilla: sailing back to
# Wooded Isle after Gorge Isle runs event 10009 (next_island script: Franky's message, then FieldGroupEnable(10010) =
# the build site's touch spot and FieldPartsEnable(39557) = the site on the deck) unless 10009 has already run.
# Building it runs 10010: FieldGroupEnable(10010, false), FieldPartsEnable(39557, false), FieldGroupEnable(10991) =
# the cannon's touch spot, a camera pan to the cannon, Franky's message (cev_sny_001) and tutorial 18.
CANNON_SITE_EVENT, CANNON_BUILT_EVENT = 10009, 10010


def wherever_cannon(ctx: "OPUCContext", g: "GameState", have) -> None:
    """With the cannon as an item the build site never appears (10009 marked done); once the item is in, the game's
    own build-finished event 10010 runs on the Sunny.
    1.0.1 (user: received before reaching the Sunny, the scene played twice): the request used to be repeated 30 s
    after it was made, counted from the request, not from the scene. The hook held it through the first-time Sunny
    scene, so the 30 s ran out while 10010 was still playing (its end flag is only set when it finishes) and a second
    copy was queued. Now it's only asked (or asked again) after 0.5 s of quiet (1.0.3; 3 s in 1.0.1) - no event running, so a 10010 that is
    still playing or waiting in the hook never gets a second request - and at most once a minute."""
    if not int(ctx.slot_data.get("wherever_cannon_unlock", 0)) or not g.settled(3):
        return
    g.set_script_flag(CANNON_SITE_EVENT)
    if not have["The Wherever Cannon"] or g.script_flags([CANNON_BUILT_EVENT]) or g.on_sunny() is not True:
        return
    now = time.monotonic()
    if now - ctx.cannon_asked > 60 and quiet_for(ctx, 0.5) and g.request_script(CANNON_BUILT_EVENT):
        ctx.cannon_asked = now
        used_quiet(ctx, event=True)


def death_link(ctx: "OPUCContext", g: "GameState") -> None:
    """Death Link: a Straw Hat's HP reaching 0 sends a death (and, with falling_death_link, a fall into the abyss /
    deep water: [obj + 0x9C] & 0x01000000 turning on). A received death gives the current Straw Hat a fatal hit
    through the pending hit record once it can be hit safely (same rules as traps). Deaths within 10 s of one we
    applied aren't sent back."""
    if "DeathLink" not in ctx.tags or not g.settled():
        ctx.fallen_prev = None
        ctx.hp_prev = None
        return
    now = time.monotonic()
    hp = g.crew_hp()
    down = g.fallen() if int(ctx.slot_data.get("falling_death_link", 1)) else set()
    go = bool(g.rd(GO_REQ, 1)[0])          # our Game Over routine revived the party (whole crew down)
    cause = None
    if go and not ctx.go_prev:
        ci = g.player_index()
        cause = f"{CHARACTERS[ci] if ci is not None else 'crew'} was defeated."
    if ctx.hp_prev is not None and cause is None:
        died = [ci for ci, (cur, _mx) in hp.items() if cur == 0 and ctx.hp_prev.get(ci, (0, 0))[0] > 0]
        if died:
            cause = f"{CHARACTERS[died[0]]} was defeated."
    if ctx.fallen_prev is not None and cause is None:
        new = down - ctx.fallen_prev
        if new:
            cause = f"{CHARACTERS[min(new)]} fell into the abyss."
    if cause and now - ctx.death_applied_at > 10:
        Utils.async_start(ctx.send_death(f"{ctx.player_names.get(ctx.slot, 'Someone')}'s {cause}"))
    ctx.hp_prev = hp
    ctx.fallen_prev = down
    ctx.go_prev = go
    if ctx.death_pending and g.on_sunny() is False and quiet_for(ctx, 0) and g.can_trap() and g.death_hit():   # never on the Sunny
        logger.info(f"Death Link from {ctx.death_pending}: your Straw Hat takes a fatal hit.")
        ctx.death_pending = None
        ctx.death_applied_at = now


# Trap lengths (ms). Burn: applied long and taken off once it has burned 25% of the character's max HP (or after
# BURN_MAX_MS, or at 10% HP when that Straw Hat is the only one left standing, so a trap never ends the run; with two
# or more alive it may knock one out, 0.23.0). Heat Trap retired (0.22.1).
TRAP_TIME_MS = {"Poison Trap": 10000, "Burn Trap": 60000}
BURN_SHARE, BURN_FLOOR, BURN_MAX_MS = 0.25, 0.10, 60000


def deliver_traps(ctx: "OPUCContext", g: "GameState") -> List[Tuple[str, str]]:
    """Status traps play one at a time, in the order received: a trap hits the current Straw Hat (no damage) through
    the pending hit record, and the next one waits until it has worn off plus TRAP_GAP. Played traps are counted in
    the progress file, so reloading a save doesn't play them again. Returns rows for the Armed tab."""
    traps = [ID_TO_ITEM.get(it.item, "") for it in ctx.items_received
             if ITEM_TABLE.get(ID_TO_ITEM.get(it.item, "")) and ITEM_TABLE[ID_TO_ITEM[it.item]].kind == "trap"
             and ID_TO_ITEM[it.item] not in RETIRED_TRAPS]
    ctx.traps_done = min(ctx.traps_done, len(traps))
    now = time.monotonic()
    st = ctx.trap_state
    if st and st["phase"] == "pending" and g.settled() and not g.hit_pending():
        st.update(phase="active", since=now)               # the game took the hit: its time starts now
        if st["name"] == "Burn Trap":                   # follow the burned Straw Hat, even after a switch
            st["obj"] = g.player_obj()
            h = g.hp(st["obj"]) if st["obj"] else None
            st.update(max=h[1] if h else 0, prev=h[0] if h else 0, lost=0)
    if st and st["phase"] == "active":
        if st["name"] == "Burn Trap":
            h = g.hp(st["obj"]) if st.get("obj") else None
            elapsed = now - st["since"]
            if h and st["max"]:
                st["lost"] += max(0, st["prev"] - h[0])
                st["prev"] = h[0]
                # the 10% floor only guards the last Straw Hat standing: with two or more alive a burn may knock
                # the burned one out (user, 0.23.0)
                alive = [ci for ci, (cur, _mx) in g.crew_hp().items() if cur > 0 and ci in ctx.owned_chars]
                floor = len(alive) <= 1 and h[0] <= BURN_FLOOR * st["max"]
                done = (st["lost"] >= BURN_SHARE * st["max"] or floor or h[0] == 0
                        or elapsed >= BURN_MAX_MS / 1000)
            else:                                          # HP not readable: a normal-length burn
                done = elapsed >= TRAP_MS / 1000
            done = done or g.on_sunny() is True            # went back to the Sunny: put it out
            if done and g.request_status(0, add=False):    # take the burn off (hook command 6)
                st.update(phase="ending", since=now)
        elif now - st["since"] >= st["ms"] / 1000:
            st.update(phase="ending", since=now)
    if st and st["phase"] == "ending" and now - st["since"] >= TRAP_GAP:
        st = ctx.trap_state = None
    sunny = g.on_sunny() if g.settled() else None
    # Burn Traps (and received deaths) stay armed while on the Thousand Sunny (dying there crashed the game, user
    # 0.22.1); other traps play past them. None = not known yet: Burn waits too.
    waiting = [i for i in range(ctx.traps_done, len(traps)) if i not in ctx.traps_ahead]
    playable = [i for i in waiting if traps[i] != "Burn Trap" or sunny is False]
    # 0.25.19 (user): no quiet wait, just the game running and idle right now plus the can_trap safety checks
    if st is None and playable and g.settled() and quiet_for(ctx, 0) and g.can_trap():
        i = playable[0]
        name = traps[i]
        ms = TRAP_TIME_MS.get(name, TRAP_MS)
        if g.trap_hit(ITEM_TABLE[name].data, ms):
            ctx.trap_state = {"phase": "pending", "name": name, "since": now, "ms": ms}
            ctx.traps_ahead.add(i)
            while ctx.traps_done in ctx.traps_ahead:      # keep the counter at the first trap not played yet
                ctx.traps_ahead.discard(ctx.traps_done)
                ctx.traps_done += 1
            ctx.save_progress()
            logger.info(f"{name}!")
            waiting.remove(i)
    rows = []
    if ctx.trap_state:
        rows.append((ctx.trap_state["name"], "Playing"))
    nxt = next((i for i in waiting if traps[i] != "Burn Trap" or sunny is False), None)
    for i in waiting:
        if i == nxt and not ctx.trap_state:
            rows.append((traps[i], "Next"))
        elif traps[i] == "Burn Trap" and sunny is not False:
            rows.append((traps[i], "Armed (on an island)"))
        else:
            rows.append((traps[i], "Armed"))
    return rows


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
    ctx.armed_items = out + ctx.armed_traps


def read_checks(ctx: OPUCContext, g: "GameState") -> Set[int]:
    found: Set[int] = set()
    goal_flag = GOALS[int(ctx.slot_data.get("goal", 0))][1]     # 11351 Eneru, 12351 Moria, 13355 Aokiji
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
    found |= {CRAFT_LOCS[k] for k in g.crafted(recipe_rooms(ctx.slot_data)) if k in CRAFT_LOCS}
    # first catch of a fish / creature: its "ever obtained" bit (only locations that exist in this seed)
    in_seed = ctx.server_locations
    # The Database records every fish / creature caught (Sea Kings too, which never reach the bag as themselves;
    # user 2026-10-23). The "ever obtained" bit is only a fallback while the Database can't be read.
    caught = g.database_caught()
    found |= {lid for gid, lid in CATCH_LOCS.items()
              if lid in in_seed and (gid in caught if caught is not None else g.found(gid))}
    # Materialsanity: first pickup of a material = its "ever obtained" bit
    found |= {lid for gid, lid in MATERIAL_LOCS.items() if lid in in_seed and g.found(gid)}
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
            if int(ctx.slot_data.get("expanded_storage", 0)):
                g.set_storage_count()                  # before the session's lists are built (title screen)
            g.check_low_code()
            # Starting Costumes: built into the Straw Hats at creation (anyone in the default costume / style)
            g.set_costume_table(ctx.slot_data.get("starting_costumes"))
            g.rename_placeholder()
            g.set_iron_scrap_gold(bool(int(ctx.slot_data.get("iron_scrap_gives_gold_energy", 0))))
            g.set_coin_gold()                     # Old Gold Coin: 10 Gold Energy instead of 100 (0.30.1)
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
                    if owner == "fresh":            # a new game: Starting Costumes
                        # normally already built in (creation override); anyone who isn't (client connected late,
                        # or Dolphin had already run the constructor before the patch) gets theirs when switched in.
                        # 0.25.9: decided by what each Straw Hat actually has, not by whether the patch is in place
                        wanted = ctx.slot_data.get("starting_costumes") or []
                        state = g.costume_state()
                        ctx.costume_pending = {ci for ci, cs in enumerate(wanted)
                                               if tuple(cs) != (0, 0) and ci in state and state[ci] != tuple(cs)}
                        ctx.save_progress()
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
            g.setup_recipes(ctx.comments, hidden, veiled, getattr(ctx, "custom_recipes", None),
                            recipe_rooms(ctx.slot_data))
            if franky_on(ctx.slot_data):
                g.rename_supply()                      # Supply -> "Art of Supplying"
                g.set_fish_junk_coins()                # fishing junk -> Old Gold Coins (0.31.0)
                g.set_gen_cells(g.ANEMONE_ROW, g.BLACK_ORB, new_item=g.OLD_GOLD_COIN_ITEM)   # Sea Anemone (0.33.4)
            if int(ctx.slot_data.get("easier_fish", 0)):
                g.easier_fish()
            if g.settled():
                g.strip_fragment_drops(dust_spot_items(ctx.slot_data))
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
