"""
One Piece Unlimited Cruise Part 1 (PAL, ROUPAF) - game memory logic for the Archipelago client.
No Archipelago imports: everything here reads and writes Dolphin memory through dolphin_memory_engine.
Addresses come from the research notes (project docs opuc-*.md); every write checks what is there first.
"""
import struct
import time
from typing import Dict, Iterable, List, Optional, Set, Tuple

import dolphin_memory_engine as dme

from .data import BASE_ID, CRAFTS, DUMMY_RECIPES, ITEM_TABLE, ITEMS, LOCATIONS, COOP_MEMBERS
from .tables import ABILITY_EXP, EXP_TABLES, LVL_TABLES, RECIPE_COMMENTS, SHRINE_COSTS

GAME_ID = b"ROUPAF"
MEM_REGIONS = [(0x80000000, 0x01800000), (0x90000000, 0x04000000)]

# ---- pointers ------------------------------------------------------------------------------------
CHARA_MGR_PTR = 0x8068A18C      # character manager
PLAYER_ITEMS_PTR = 0x8068A190   # player item object: bag list +0x120, Storage +0x150, palette +0x180
ITEM_MGR_PTR = 0x8068A280       # +0/+4/+8 recipe state objects (Workshop, Kitchen, Pharmacy)
TREASURE_PTR = 0x8068A238       # chests
SHRINE_MGR_PTR = 0x8068A148
GABRI_PTR = 0x8068A158
COOP_PTR = 0x8068A650
EXP_CACHE, EXP_CACHE_SLOTS = 0x650, 8   # per-slot copies of move EXP requirements on CharaObj
_EXP_SWAP: Dict[Tuple[str, int], Dict[bytes, bytes]] = {}
EXP_FACTORS = (1, 2, 3)
FLAG_LIST = 0x805E8B04          # save-data sections, found by name
# Received-item counter kept in the save file, so a reload (Game Over, quitting without saving) gives back
# the items received since that save. Last word of EventFuncEndFlag (0xD6C bytes = flags 0-27487; the game
# uses ids around 11000-21000). High half = marker, low half = count. The word before it (data+0xD64) holds
# a tag of the seed and slot, so a save reused with a new seed starts counting from 0.
DELIVERED_SECTION, DELIVERED_OFFSET, DELIVERED_MARK = "EventFuncEndFlag", 0xD68, 0x4150
ITEM_NAMES_PTR = 0x805E91E8     # item table, 0x224-byte rows
RECIPE_ROWS = 0x805E9220        # + room*4 -> 252-byte recipe rows
ROOM_INDEX = {"workshop": 0, "kitchen": 1, "pharmacy": 2}

PLACEHOLDER = 86                # "Archipelago Item"
PLACEHOLDER_NAME = "Archipelago Item"
PLACEHOLDER_DESC = "An item from the Multiworld!\nThis Location has already been\nchecked off."

CHAR_NAMES = ["luf", "zor", "uso", "snj", "nam", "cho", "nic", "fra", "blk"]
START_MOVE = [0, 512, 1024, 1536, 2056, 2560, 3072, 3592, 4096]
MIN_MAX_SP = [120, 120, 110, 110, 120, 125, 120, 100, 115]   # every super and co-op usable

# ---- code patches (go in at the title screen, before the code first runs; Dolphin cheats off) -------
ADD_USE_CALL, ADD_USE_ORIG, NOP = 0x800A67D8, 0x4BF9A125, 0x60000000   # scripts can't add Straw Hats
CHANGE_RESULT, CHANGE_ORIG = 0x800A6270, 0x7C7D1B78                    # start-character redirect
ROOM_SITES = {"kitchen": (0x801B07B8, 0x80002F02), "pharmacy": (0x801B0808, 0x80002F03)}
ROOM_ORIG_MR, ROOM_ORIG_CMP = 0x7FE3FB78, 0x2C030002
SPOT_GATE = 0x80002E00
SPOT_GATE_CODE = [0x2806000F, 0x4181001C, 0x3C808000, 0x38842F10, 0x7C8430AE,
                  0x2C040000, 0x40820008, 0x38C0000A, 0x7CC43378, 0x4E800020]
SPOT_TABLE = 0x80002F10
SPOT_CALL, SPOT_ORIG = 0x800BA914, 0x7CC43378
ROOM_SPOT = {"kitchen": 2, "pharmacy": 3, "workshop": 4}
WS_TABLE_ENTRY, WS_ORIG, WS_CODE_AT, WS_BYTE = 0x8059E8CC, 0x801B0794, 0x80002E40, 0x80002F04
WS_CODE = [0x3C608000, 0x88632F04, 0x48000000 | ((0x801B0858 - 0x80002E48) & 0x3FFFFFC)]
# Stone Monument gate (robin_required_for_monuments). Monuments are field objects whose touch runs their
# script by id (obj+0x12C = 11651 etc.) through 0x8009F018 (scriptmgr, id, ...), which formats the id and calls
# 0x8009EB10. 0.10.0 gated case 7 of the touch switch (0x800456EC), but that case isn't the monument (user:
# still readable). Now the first instruction of 0x8009F018 branches to our routine: if STELE_BYTE is 0 and the
# id is a monument script (event/stele/stele.bin), it returns 0 without running it; otherwise it does the
# original stwu and continues. Code patch, so it goes in at the title screen.
STELE_IDS = [11651, 11652, 11653, 12651, 12652, 13651, 13652, 14651, 14652, 15800]
RUN_SCRIPT, RUN_SCRIPT_ORIG = 0x8009F018, 0x9421FFB0
STELE_CODE_AT, STELE_BYTE = 0x80002E60, 0x80002F09


def stele_code():
    at = STELE_CODE_AT
    n = len(STELE_IDS)
    kill = 4 + 2 * n + 1                     # index of "li r3,0"
    cont = kill + 2                          # index of the original stwu
    code = [0x3D808000,                                          # lis r12,0x8000
            lbz(12, 0x2F09, 12),                                 # lbz r12,STELE_BYTE
            cmpwi(12, 0),
            0x40820000 | (((cont - 3) * 4) & 0xFFFC)]            # bne -> cont
    for i, sid in enumerate(STELE_IDS):
        idx = 4 + 2 * i
        code += [cmpwi(4, sid), 0x41820000 | (((kill - (idx + 1)) * 4) & 0xFFFC)]   # beq -> kill
    code.append(0x48000000 | (((cont - len(code)) * 4) & 0x3FFFFFC))              # b cont
    code += [li(3, 0), 0x4E800020]                               # kill: li r3,0; blr
    code += [RUN_SCRIPT_ORIG, 0x48000000 | ((RUN_SCRIPT + 4 - (at + 4 * (cont + 1))) & 0x3FFFFFC)]
    return code


# Pause-menu Instructions (view-only recipe lists). 0x8015A4F0(n) says whether tab n is available
# (n = -1: any tab, used for the menu entry itself); vanilla: n=0 / n=1 need recipes in the Kitchen object and
# chapter > 2, n=2 needs Workshop recipes, all need 0x800FE8BC. The entry now branches to our routine: for
# n = 0..2 it returns the room byte the client keeps (0x80002F02 Kitchen, F03 Pharmacy, F04 Workshop), so each
# tab opens with its crafting room; other n run the original (which loops over 0..2). Code patch (title screen).
INSTR_FUNC, INSTR_ORIG, INSTR_CODE_AT = 0x8015A4F0, 0x9421FFE0, 0x80002ED8
INSTR_CODE = [0x28030002,                                                   # cmplwi r3,2
              0x41810014,                                                   # bgt -> original
              0x3C808000, 0x38842F02,                                       # r4 = 0x80002F02
              (31 << 26) | (3 << 21) | (4 << 16) | (3 << 11) | (87 << 1),   # lbzx r3,r4,r3
              0x4E800020,                                                   # blr
              INSTR_ORIG,                                                   # stwu r1,-32(r1)
              0x48000000 | ((INSTR_FUNC + 4 - (INSTR_CODE_AT + 28)) & 0x3FFFFFC)]
# instant unlock hook (per-frame callback slot 3 of the character manager)
STUB, HOOK_FLAG, HOOK_COUNTER = 0x80002C00, 0x80002F20, 0x80002F21
MOVE_CHECKER, ABILITY_CHECKER = 0x800680B8, 0x80067E88
HOOK_SLOT = 3
GIVE_FLAG, GIVE_ITEM_AT, GIVE_COUNT_AT = 0x80002F22, 0x80002F24, 0x80002F28
ITEM_HANDLE_CTOR, ITEM_HANDLE_DTOR, GIVE_ITEM = 0x800F8934, 0x800F8958, 0x80040B4C

# ---- Game Over -> back to the Thousand Sunny ------------------------------------------------------
# 0x8003FCD4 (character manager, per frame) handles a fallen player. When nobody in the party can take
# over, 0x8003FE60 schedules _GameOverStart (0x80040874), whose end callback 0x800408EC asks the main loop
# (0x80009AA0) for a full soft reset, i.e. the title screen. The patch branches 0x8003FE60 to the routine
# below instead: revive the player like the game's own revive (0x8003FD58), refill everyone's HP, and run
# the "ashore" script for the current island (reloads it with the player at the Sunny's landing spot, the
# same place Continue puts you). GO_BYTE makes it a one-shot until the client clears it, so a failed revive
# falls back to the vanilla Game Over instead of looping.
# Two places in 0x8003FCD4 schedule the Game Over (status-flag death 0x8003FE60, actor-flag death 0x800400FC);
# each gets its own copy of the routine (the second one mirrors the game's revive at 0x8003FFFC, which skips
# 0x8006F7A4).
GO_SITE_ORIG, GO_EPILOGUE, GO_BYTE = 0x809F0408, 0x80040160, 0x80002F05
GO_SITES = [(0x8003FE60, 0x80002800, True), (0x800400FC, 0x80002A00, False)]   # site, code address, 0x8006F7A4
GO_AT = GO_SITES[0][1]
RETRY_SCRIPT = 0x80002F60     # u32 start script of the fight to retry; 0x80002F68: 8 zero bytes (empty args)
# Scripted fights: (start script, clear script). The start script ends with FuncSetEnable(clear, true); the
# clear script runs when the enemy group / boss is beaten (EnemyCreate(clear) / BossNew + BossStart).
FIGHTS = [  # from event/script2 (all 989 scripts, 2026-10-18); later phases after earlier ones
    (11250, 11251), (11252, 11253),   # Wooded Isle Mud Puppet ambush (tutorial, 2 phases, barrier 20055)
    (11260, 11261), (11270, 11271), (11280, 11281),   # Wooded Isle ambushes (barriers 20056-20058)
    (11300, 11301),                   # Kuma (bos_kma)
    (11350, 11351),                   # Island 1 boss (bos_enl)
    (11400, 11401),                   # Buggy (bos_bgy)
    (12250, 12251), (12262, 12263), (12270, 12271), (12300, 12301), (12350, 12351), (12400, 12401),
    (13250, 13251), (13262, 13263), (13270, 13271), (13280, 13281), (13300, 13301), (13350, 13352),
    (13353, 13355), (13400, 13401),
    (14252, 14253), (14260, 14261), (14270, 14271), (14280, 14281), (14300, 14301), (14350, 14351),
    (14400, 14401), (15010, 15020)]
GO_REQ, CAMP_CMD = 0x80002F06, 0x80002F07   # revive done (routine) -> run the dinghy script (client tells the hook)
RESET_OBJ_PTR = 0x8068A298      # +4 = soft reset requested (title screen / Game Over), +0x10 chapter

def lwz(rd, d, ra): return (32 << 26) | (rd << 21) | (ra << 16) | (d & 0xFFFF)
def stw(rs, d, ra): return (36 << 26) | (rs << 21) | (ra << 16) | (d & 0xFFFF)
def lbz(rd, d, ra): return (34 << 26) | (rd << 21) | (ra << 16) | (d & 0xFFFF)
def stb(rs, d, ra): return (38 << 26) | (rs << 21) | (ra << 16) | (d & 0xFFFF)
def addi(rd, ra, v): return (14 << 26) | (rd << 21) | (ra << 16) | (v & 0xFFFF)
def li(rd, v): return addi(rd, 0, v)
def lis(rd, v): return (15 << 26) | (rd << 21) | (v & 0xFFFF)
def stwu(rs, d, ra): return (37 << 26) | (rs << 21) | (ra << 16) | (d & 0xFFFF)
def mr(ra, rs): return (31 << 26) | (rs << 21) | (ra << 16) | (rs << 11) | (444 << 1)
def rlwinm(ra, rs, sh, mb, me): return (21 << 26) | (rs << 21) | (ra << 16) | (sh << 11) | (mb << 6) | (me << 1)
def andi_(ra, rs, v): return (28 << 26) | (rs << 21) | (ra << 16) | (v & 0xFFFF)
def ori(ra, rs, v): return (24 << 26) | (rs << 21) | (ra << 16) | (v & 0xFFFF)
def cmpwi(ra, v): return (11 << 26) | (ra << 16) | (v & 0xFFFF)

def gameover_code(GO_AT: int = 0x80002800, GO_RET: int = 0x8003FE64, refresh: bool = True):
    code, fix, lab = [], [], {}
    def e(*xs): code.extend(xs)
    def br(op, label): fix.append((len(code), op, label)); code.append(0)
    def call(t): code.append(0x48000001 | ((t - (GO_AT + 4 * len(code))) & 0x3FFFFFC))
    def jump(t): code.append(0x48000000 | ((t - (GO_AT + 4 * len(code))) & 0x3FFFFFC))
    # r31 = character manager (callee-saved r30/r31 belong to 0x8003FCD4's frame)
    # GO_BYTE counts passes: the revive is repeated on following frames if the fall isn't over yet (a single
    # crew member in a boss fight stayed down after one pass, 0.6.3); after 120 passes (~2 s) without
    # success the vanilla Game Over takes over. The client resets the count 3 s after it first moved.
    e(lis(3, 0x8000), lbz(5, 0x2F05, 3), cmpwi(5, 120)); br(0x40800000, "vanilla")
    e(lwz(4, 0x88, 31), cmpwi(4, 0)); br(0x41820000, "vanilla")                         # no player
    e(addi(5, 5, 1), stb(5, 0x2F05, 3))
    e(stwu(1, -32, 1), stw(29, 24, 1), stw(28, 28, 1))     # 8..16(r1) = stack arguments below
    # Revive every Straw Hat object, [mgr+0xFC] and the player [mgr+0x88] the way the game's own revive
    # does (0x8003FD58):
    # 0x8006E1C0(obj, 0), 0x80128C94(0x804CE1AC(obj), 0), HP and SP gauges full. Reviving only [mgr+0x88]
    # wasn't enough in boss fights (0.6.0: with two crew the other one came back and the active one stayed
    # down; with one crew the second pass found it still down and went to the vanilla Game Over).
    def revive(label):                     # revive the object in r30 (skipped if null)
        e(cmpwi(30, 0)); br(0x41820000, label)
        e(mr(3, 30), li(4, 0)); call(0x8006E1C0)
        e(mr(3, 30)); call(0x804CE1AC); e(li(4, 0)); call(0x80128C94)
        e(addi(3, 30, 0xA48)); call(0x80075EE8); call(0x804D8E10)                     # HP full
        e(addi(3, 30, 0xA48)); call(0x80075F10); call(0x804D8E10)                     # SP full
        # the death handler's own test: [obj+0x9C] & 0x01000000 (0.6.2: with a single crew member nobody
        # else could take over and the flag stayed set)
        e(lwz(0, 0x9C, 30), rlwinm(0, 0, 0, 8, 6), stw(0, 0x9C, 30))
        lab[label] = len(code)
    # Outside boss fights only the character who fell is revived (user, 2026-10-19: earlier fallen crew stay
    # down). In a boss fight everyone is revived before the fight restarts. Boss = slots 4-7 of the array at
    # [r13-0x5CF0] (see BossIsNull, 0x800B69F4).
    e(lwz(5, -0x5CF0, 13), cmpwi(5, 0)); br(0x41820000, "player")
    for off in (0x10, 0x14, 0x18, 0x1C):
        e(lwz(0, off, 5), cmpwi(0, 0)); br(0x40820000, "everyone")
    br(0x48000000, "player")
    lab["everyone"] = len(code)
    e(addi(28, 31, 0x90), li(29, 9))
    lab["loop"] = len(code)
    e(lwz(30, 0, 28)); revive("skip")
    e(addi(28, 28, 4), addi(29, 29, -1), cmpwi(29, 0)); br(0x40820000, "loop")       # slots 0-8
    e(lwz(30, 0xFC, 31)); revive("skip2")                                            # [mgr+0xFC]
    lab["player"] = len(code)
    e(lwz(30, 0x88, 31)); revive("skip3")                                            # the player
    # End the player's current action (the fall), like the script native CharaClearAction (0x800A6AAC):
    # 0x804CFB50(0x804CE1C4(player), 0, 0, 0, 1, 1). Without it a single crew member in a boss fight kept
    # replaying the fall every frame (death sound each frame, full HP) until the vanilla Game Over (0.6.4).
    e(lwz(3, 0x88, 31), cmpwi(3, 0)); br(0x41820000, "noact")
    call(0x804CE1C4)
    e(li(4, 0), li(5, 0), li(6, 0), li(7, 1), li(8, 1)); call(0x804CFB50)
    lab["noact"] = len(code)
    if refresh:
        e(lwz(3, 0x88, 31)); call(0x8006F7A4)
    # No transition from inside the death handler: 0.5.1 (script "ashore" from the field) crashed at
    # 0x801C0364 during the field reload, 0.5.2 (camp opened from here) crashed at 0x800EBA54. The revive
    # alone is stable (0.5.5); the trip to the Sunny is requested here and started by the per-frame hook
    # a couple of seconds later (client: GO_REQ -> CAMP_CMD).
    e(lis(3, 0x8000), li(0, 1), stb(0, 0x2F06, 3))                                    # ask for the Sunny trip
    lab["out"] = len(code)
    e(lwz(29, 24, 1), lwz(28, 28, 1), addi(1, 1, 32)); jump(GO_EPILOGUE)
    lab["vanilla"] = len(code)
    e(GO_SITE_ORIG); jump(GO_RET)
    for i, op, label in fix:
        mask = 0x3FFFFFC if op == 0x48000000 else 0xFFFC
        code[i] = op | (((lab[label] - i) * 4) & mask)
    return code


# ---- Gabri levels: max bars per slot (Red, Green, Blue, White, Black, Gold) after each level --------
GABRI_MAX = [[0, 0, 3, 0, 0, 0], [0, 3, 4, 0, 0, 0], [0, 4, 5, 0, 0, 1], [5, 5, 6, 0, 0, 1],
             [6, 6, 7, 0, 0, 2], [7, 7, 8, 5, 0, 3], [8, 8, 9, 6, 0, 4], [9, 9, 10, 8, 5, 5],
             [10, 10, 10, 9, 10, 6], [10, 10, 10, 9, 10, 7], [10, 10, 10, 9, 10, 8],
             [10, 10, 10, 9, 10, 9], [10, 10, 10, 9, 10, 10], [10, 10, 10, 10, 10, 10]]
SHRINE_LOCKED = 9999

# items stored in the bag when given; the rest only set their found bits (gadgets / upgrades)
STORE_ITEMS = {1, 3, 6, 8, 62, 87, 89, 90, 91, 92, 93, 94, 95, 96} | set(range(190, 226))
BAG_CAPACITY = {162: ("bag", 28), 163: ("bag", 35), 164: ("palette", 6), 165: ("palette", 9)}
LIST_OFFSET = {"bag": 0x120, "storage": 0x150, "palette": 0x180}
FRAGMENT_ITEMS = set(range(190, 226))      # every treasure map fragment (they are all AP items eventually)


def valid(p: int) -> bool:
    return 0x80000000 <= p < 0x81800000 or 0x90000000 <= p < 0x94000000


def rod_level_byte(upgrades: int) -> int:
    """Rod level byte for n Progressive Fishing Rod Level items (skips the duplicate grade boundaries)."""
    n = max(0, min(30, upgrades))
    return n if n < 10 else n + 1 if n < 20 else n + 2


def bl(frm: int, to: int) -> int:
    return 0x48000001 | ((to - frm) & 0x3FFFFFC)


# ---- recipe comment word wrap (box does not wrap by itself; calibrated in game) -------------------
def _char_width(c: str) -> float:
    if c in "MW":
        return 1.0
    if c in "mw":
        return 0.85
    if c in "iIlj.,'!:;|":
        return 0.24
    if c == " ":
        return 0.3
    return 0.7 if c.isupper() else 0.5


def wrap_comment(lines: List[str], limit: float = 16.0, max_lines: int = 3) -> Optional[str]:
    """Word-wrap for recipe comments. The box shows 3 lines; the widest vanilla line measures 15.8 here and
    text past ~18 is cut off at the panel edge (screenshots 2026-10-18), so the limit is the vanilla width."""
    out = []
    for text in lines:
        cur, width = "", 0.0
        for word in text.split(" "):
            w = sum(_char_width(c) for c in word)
            if w > limit:
                return None
            if cur and width + _char_width(" ") + w > limit:
                out.append(cur)
                cur, width = word, w
            else:
                width += (_char_width(" ") if cur else 0) + w
                cur = f"{cur} {word}" if cur else word
        out.append(cur)
    text = "\n".join(out)
    return text if len(out) <= max_lines and len(text) <= 111 else None


def placeholder_comment(player: str, item: str) -> str:
    for lines in (["An Archipelago Item!", f"It's {player}'s {item}!"],
                  [f"It's {player}'s {item}!"],
                  ["An Archipelago Item!", f"It belongs to {player}!"]):
        text = wrap_comment(lines)
        if text and all(ord(c) < 0x2000 for c in text):
            return text
    return "An Archipelago Item!"


def also_comes_comment(player: Optional[str], item: Optional[str]) -> str:
    """Comment for a vanilla-result recipe that is a location, until it's made (then the vanilla one)."""
    if player and item:
        text = wrap_comment([f"This recipe also comes with {player}'s {item}!"])
        if text and all(ord(c) < 0x2000 for c in text):
            return text
    return wrap_comment(["This recipe also comes with an Archipelago Item!"]) or "An Archipelago Item!"


# "Crafting Recipes Spoil Locations" off: key-item recipes / vanilla-result recipes
HIDDEN_AP_COMMENT = wrap_comment(["It's an Archipelago Item!", "This Location has not been claimed!"]) \
    or "It's an Archipelago Item!"
HIDDEN_ALSO_COMMENT = wrap_comment(["This Recipe also holds an Archipelago Item!",
                                    "This Location has not been claimed!"]) or "An Archipelago Item!"


# Recipes that aren't locations in this world (materials out of scope, or room after the goal)
NO_LOCATION_COMMENT = wrap_comment(["This recipe is not a Location in this World yet!"]) or "Not a Location yet!"


class GameState:
    """Memory side of the client. Call poll() a few times a second while hooked."""

    def __init__(self, log=print):
        self.log = log
        self.hooked = False
        self.patched = False
        self.scan_cache: Dict[str, List[int]] = {}
        self.last_scan = 0.0
        self.scan_new = False
        self.unreadable = 0
        self.last_report = ""
        self.messages_said: Set[str] = set()
        self.game_since: Optional[float] = None   # when the current play session (character manager) appeared
        self.session_mgr = 0
        self.sessions = 0                         # bumped when a session ends (client forgets per-session state)
        self.go_seen: Optional[float] = None
        self.sp_writes: Dict[int, int] = {}
        self.go_req_seen: Optional[float] = None
        self.last_retry = 0
        self.retry_pending: Optional[Tuple[int, int, Optional[float]]] = None
        self.retry_time = 0.0
        self.seed_tag = 0                         # crc32 of seed + slot: the save's item count belongs to one seed

    # ------------------------------------------------------------------ low level
    def hook(self) -> bool:
        if not dme.is_hooked():
            dme.hook()
        if not dme.is_hooked():
            self.hooked = False
            return False
        try:
            ok = dme.read_bytes(0x80000000, 6) == GAME_ID
        except RuntimeError:
            ok = False
        if not ok:
            dme.un_hook()
        self.hooked = ok
        return ok

    def rd(self, a: int, n: int) -> bytes:
        return dme.read_bytes(a, n)

    def u32(self, a: int) -> int:
        return struct.unpack(">I", dme.read_bytes(a, 4))[0]

    def w(self, a: int, b: bytes) -> None:
        dme.write_bytes(a, b)

    def w32(self, a: int, v: int) -> None:
        dme.write_bytes(a, struct.pack(">I", v & 0xFFFFFFFF))

    def say_once(self, key: str, msg: str) -> None:
        if key not in self.messages_said:
            self.messages_said.add(key)
            self.log(msg)

    def chara_mgr(self) -> Optional[int]:
        m = self.u32(CHARA_MGR_PTR)
        return m if valid(m) else None

    def in_game(self) -> bool:
        return self.chara_mgr() is not None

    # ------------------------------------------------------------------ code patches
    def reset(self) -> None:
        """Forget everything about the running game (Dolphin or the game was restarted)."""
        self.patched = False
        self.scan_cache = {}
        self.last_scan = 0.0
        self.messages_said.discard("late")
        self.game_since = None
        self.session_mgr = 0
        self.sessions += 1

    def check_restart(self) -> None:
        """The game was reset without Dolphin closing: our patch is gone, so start over."""
        if self.patched and self.u32(ADD_USE_CALL) == ADD_USE_ORIG:
            self.reset()

    def session_tick(self) -> None:
        """Track the play session. A soft reset (title screen, Game Over) frees the character manager and
        everything loaded with it, so the table addresses found by the scan must be forgotten before the
        next save is loaded (writing to them afterwards corrupts whatever lives there now)."""
        m = self.chara_mgr()
        ro = self.u32(RESET_OBJ_PTR)
        resetting = valid(ro) and self.rd(ro + 4, 1)[0] != 0
        if m is None or resetting or (self.game_since is not None and m != self.session_mgr):
            if self.game_since is not None or self.scan_cache:
                self.scan_cache = {}
                self.last_scan = 0.0
                self.scan_new = False
                self.sessions += 1
            self.game_since = None
            self.session_mgr = 0
            self.retry_pending = None
            if m is None or resetting:
                return
        if self.game_since is None:
            self.game_since = time.monotonic()
            self.session_mgr = m
        # after a Game Over revive: back to the Thousand Sunny (dinghy script 11990) through the hook 2 s later
        if self.rd(GO_REQ, 1)[0]:
            if self.go_req_seen is None:
                self.go_req_seen = time.monotonic()
            elif time.monotonic() - self.go_req_seen > 2 and not self.event_playing():
                self.w(GO_REQ, b"\0")
                fight = self.fight_in_progress()
                if fight and not self.boss_active():
                    # ambush (no boss): stay in the fight, revived. Restarting doesn't work there: the
                    # enemies removed for the restart empty the group while its clear script is off, and
                    # the restarted group then never fires the clear script (0.6.5, Enforcer ambush).
                    pass
                elif fight:
                    # boss fight: restart it. Its clear script is switched off first so removing
                    # the boss / enemies can't count as a win; the start script switches it on again.
                    start, clear = fight
                    self.set_func_enable(clear, False)
                    self.w(RETRY_SCRIPT, struct.pack(">I", start) + bytes(12))
                    self.w(CAMP_CMD, b"\x02")
                    self.last_retry = start
                    self.retry_pending = (start, clear, None)
                    self.retry_time = time.monotonic()
                # back to the Sunny only once it has been reached in the story (script 11990 has run
                # before) and no unknown boss fight is running (leaving one leaves it running: boss HUD,
                # barrier, softlock); otherwise the revive alone has to do
                elif self.script_flags([11990]) and not self.boss_active():
                    self.w(CAMP_CMD, b"\x01")
                self.go_req_seen = None
        else:
            self.go_req_seen = None
        # retry step 2: once the hook has removed the old boss / enemies, wait 1 s, then restart the fight
        if self.retry_pending:
            start, clear, done_at = self.retry_pending
            if self.rd(CAMP_CMD, 1)[0] == 0:
                if done_at is None:
                    self.retry_pending = (start, clear, time.monotonic())
                elif time.monotonic() - done_at > 1.0:
                    self.set_func_enable(clear, False)
                    self.w(CAMP_CMD, b"\x03")
                    self.retry_pending = None
                    self.retry_time = time.monotonic()
        # Watchdog: a running fight must have its clear script armed, or winning does nothing (softlock; seen
        # after loading a Dolphin save state taken before a retry had switched it off). Leave it alone while
        # a retry is in progress and for 20 s after one started (the start script arms it itself).
        if not self.retry_pending and not self.rd(GO_REQ, 2)[0] and not self.rd(CAMP_CMD, 1)[0] \
                and time.monotonic() - self.retry_time > 20:
            fight = self.fight_in_progress()
            if fight and self.script_flags([fight[0]]) and not self.func_enabled(fight[1]):
                self.set_func_enable(fight[1], True)
        # Game Over pass counter (120 passes, then vanilla): reset it 3 s after it first moved
        if self.rd(GO_BYTE, 1)[0]:
            if self.go_seen is None:
                self.go_seen = time.monotonic()
            elif time.monotonic() - self.go_seen > 3:
                self.w(GO_BYTE, b"\0")
                self.go_seen = None
        else:
            self.go_seen = None

    def settled(self, wait: float = 5.0) -> bool:
        """In a loaded save for a few seconds (not on the title screen, loading or resetting)."""
        return self.game_since is not None and time.monotonic() - self.game_since >= wait

    def apply_patches(self) -> None:
        """Code patches. They only work if written before the game first runs that code (title screen)."""
        if self.patched:
            return
        if self.in_game():
            self.say_once("late", "The client connected after the game was started. Some changes (rooms, Straw Hat "
                                  "locks) only work from the title screen: save, reset to the title screen and reload.")
        for a in (STUB, SPOT_GATE, WS_CODE_AT, 0x80002F00, GO_AT):
            if self.u32(a) != 0 and not self.patched_before(a):
                self.say_once("cheats", "Low memory at 80002C00-80002FFF is in use. Turn Dolphin's cheats off "
                                        "and restart the game, or rooms / instant unlocks may not work.")
                break
        cur = self.u32(ADD_USE_CALL)
        if cur not in (ADD_USE_ORIG, NOP):
            return                                    # game code not loaded yet (Dolphin still booting)
        # scripts can no longer add Straw Hats
        if cur == ADD_USE_ORIG:
            self.w32(ADD_USE_CALL, NOP)
        # Kitchen / Pharmacy menu entries read our bytes
        for room, (site, byte) in ROOM_SITES.items():
            mr, _, blw, cmp = (self.u32(site + i * 4) for i in range(4))
            if mr == ROOM_ORIG_MR and cmp == ROOM_ORIG_CMP and (blw >> 26) == 18:
                self.w(byte, b"\0")
                self.w32(site, 0x3C608000)
                self.w32(site + 8, 0x88630000 | (byte & 0xFFFF))
                self.w32(site + 12, 0x2C030000)
        # touch spots read our table
        if self.u32(SPOT_CALL) == SPOT_ORIG:
            self.w(SPOT_TABLE, b"\x01" * 16)
            for k in ROOM_SPOT.values():
                self.w(SPOT_TABLE + k, b"\0")
            for i, x in enumerate(SPOT_GATE_CODE):
                self.w32(SPOT_GATE + i * 4, x)
            self.w32(SPOT_CALL, bl(SPOT_CALL, SPOT_GATE))
        # Workshop menu entry (data pointer, safe at any time)
        if self.u32(WS_TABLE_ENTRY) == WS_ORIG:
            self.w(WS_BYTE, b"\0")
            for i, x in enumerate(WS_CODE):
                self.w32(WS_CODE_AT + i * 4, x)
            self.w32(WS_TABLE_ENTRY, WS_CODE_AT)
        # Instructions tabs follow the crafting rooms
        if self.u32(INSTR_FUNC) == INSTR_ORIG:
            for i, x in enumerate(INSTR_CODE):
                self.w32(INSTR_CODE_AT + i * 4, x)
            self.w32(INSTR_FUNC, 0x48000000 | ((INSTR_CODE_AT - INSTR_FUNC) & 0x3FFFFFC))
        # Stone Monument gate (open until the client says otherwise)
        if self.u32(0x8051D868) == STELE_CODE_AT:
            self.w32(0x8051D868, 0x80045750)           # undo 0.10.0's touch-switch patch (same game session)
        if self.u32(RUN_SCRIPT) == RUN_SCRIPT_ORIG:
            self.w(STELE_BYTE, b"\x01")
            for i, x in enumerate(stele_code()):
                self.w32(STELE_CODE_AT + i * 4, x)
            self.w32(RUN_SCRIPT, 0x48000000 | ((STELE_CODE_AT - RUN_SCRIPT) & 0x3FFFFFC))
        # Game Over -> Thousand Sunny
        # The game's own one-shot revive in boss fights (0x80048C5C: boss in slot 4, 7+ of 9 crew down ->
        # revive [mgr+0xFC], run script "778", which isn't on the disc) is skipped so every party wipe
        # reaches the routine below: 0x8003FD40 / 0x8003FFE4 beq -> b.
        for site, orig in ((0x8003FD40, 0x41820098), (0x8003FFE4, 0x41820090)):
            if self.u32(site) == orig:
                self.w32(site, 0x48000000 | (orig & 0xFFFF))
        for site, at, refresh in GO_SITES:
            if self.u32(site) == GO_SITE_ORIG:
                self.w(GO_BYTE, b"\0\0\0")              # GO_BYTE, GO_REQ, CAMP_CMD
                self.w(at, b"".join(struct.pack(">I", x) for x in gameover_code(at, site + 4, refresh)))
                self.w32(site, 0x48000000 | ((at - site) & 0x3FFFFFC))
        self.patched = True

    def patched_before(self, a: int) -> bool:
        """True if the word at a is one of our own patches (client restarted without resetting the game)."""
        mine = {STUB: None, SPOT_GATE: SPOT_GATE_CODE[0], WS_CODE_AT: WS_CODE[0], 0x80002F00: None,
                GO_AT: gameover_code()[0]}
        v = self.u32(a)
        if a == STUB:
            return v == 0x9421FFE0
        if a == 0x80002F00:
            return v & 0xFEFEFEFE == 0
        return v == mine[a]

    def set_monuments(self, open_: bool) -> None:
        if self.u32(RUN_SCRIPT) >> 26 != 18:
            return
        v = b"\x01" if open_ else b"\0"
        if self.rd(STELE_BYTE, 1) != v:
            self.w(STELE_BYTE, v)

    def set_rooms(self, owned: Set[str]) -> None:
        for room in ("workshop", "kitchen", "pharmacy"):
            v = b"\x01" if room in owned else b"\0"
            menu = WS_BYTE if room == "workshop" else ROOM_SITES[room][1]
            for a in (menu, SPOT_TABLE + ROOM_SPOT[room]):
                if self.rd(a, 1) != v:
                    self.w(a, v)

    # ------------------------------------------------------------------ Straw Hats
    def enforce_crew(self, owned: Set[int], start: int) -> None:
        m = self.chara_mgr()
        obj = self.u32(m + 0x88) if m else 0
        act = self.u32(obj + 0xB8) if valid(obj) else None
        if act is not None and act >= 79:
            act = None
        want = CHANGE_ORIG if act is not None else (0x3BA00000 | start)
        cur = self.u32(CHANGE_RESULT)
        if cur != want and (cur == CHANGE_ORIG or (cur & 0xFFFF0000) == 0x3BA00000):
            self.w32(CHANGE_RESULT, want)
        if not m:
            return
        keep = set(owned) | ({start, 0} if act is None else set())
        for i in range(9):
            a = m + 0x1CC + i * 4
            v = self.u32(a)
            if i in keep:
                if not v & 1 and self.u32(m + 0x90 + i * 4):
                    self.w32(a, v | 1)
            elif v & 1 and i != act:
                self.w32(a, v & ~1)

    # Food diminishing-returns setters (found from the user's read breakpoint at 0x80076068, 2026-10-20):
    # 0x8007607C(Z, food id, value) and 0x800760E8(Z, index, value) store min(value, 255) at Z + 0x6B8 + index
    # (Z = object + 0xA48, so object + 0x1100). Both "li r0,255" / "mr r0,r5" pairs become "li r0,0", so the
    # byte always stays 0: no diminishing returns, and the eat screen shows the full gain too.
    FOOD_DR_SITES = [(0x800760D0, 0x380000FF), (0x800760D8, 0x7CA02B78),
                     (0x800760EC, 0x380000FF), (0x800760F4, 0x7CA02B78)]

    def patch_food_returns(self) -> None:
        if all(self.u32(a) == orig for a, orig in self.FOOD_DR_SITES):
            for a, _ in self.FOOD_DR_SITES:
                self.w32(a, 0x38000000)

    def reset_food_returns(self) -> None:
        """Food diminishing returns (user, 2026-10-20): character object + 0x1100 + (food id - 140) is a per-food
        byte that lowers the next stat gain; setting it to 0 gives the full gain again. (+0x1124 + 4 * (id - 140)
        is a plain u32 times-eaten counter, left alone.) Foods are items 140-161."""
        m = self.chara_mgr()
        if not m:
            return
        zero = bytes(22)
        for i in range(9):
            o = self.u32(m + 0x90 + i * 4)
            if valid(o) and self.rd(o + 0x1100, 22) != zero:
                self.w(o + 0x1100, zero)

    def min_sp(self) -> None:
        m = self.chara_mgr()
        if not m:
            return
        for i in range(9):
            o = self.u32(m + 0x90 + i * 4)
            if not valid(o):
                continue
            st = self.u32(o + 0x60)
            if not valid(st):
                continue
            mx, third = struct.unpack(">2i", self.rd(st + 0x14, 8))
            # Using a super lowers max SP for a while (the vanilla "pseudo-cap", +0x14 below +0x18). Raising
            # it back to the minimum then cancelled the super's cost (SP refilled like after a dash; user,
            # 2026-10-19). Only the real max (+0x14 == +0x18, no pseudo-cap running) is raised.
            if 0 < mx < MIN_MAX_SP[i] and mx == third:
                self.w(st + 0x14, struct.pack(">2i", MIN_MAX_SP[i], MIN_MAX_SP[i]))
                self.sp_writes[i] = self.sp_writes.get(i, 0) + 1

    def sp_report(self) -> str:
        """Each loaded Straw Hat's SP values (status +0x10 SP, +0x14 max, +0x18) and how often the client
        raised the max this session (for the SP refill bug)."""
        m = self.chara_mgr()
        if not m:
            return "Not in game."
        out = []
        for i, c in enumerate(CHAR_NAMES):
            o = self.u32(m + 0x90 + i * 4)
            st = self.u32(o + 0x60) if valid(o) else 0
            if not valid(st):
                continue
            sp, mx, third = struct.unpack(">3i", self.rd(st + 0x10, 12))
            out.append(f"{c}: SP {sp} / max {mx} / +0x18 {third}; client raised max {self.sp_writes.get(i, 0)}x "
                       f"(minimum {MIN_MAX_SP[i]})")
        return "\n".join(out) or "No Straw Hats loaded."

    # ------------------------------------------------------------------ RAM scans (tables loaded per stage)
    def _scan(self) -> Dict[str, List[int]]:
        found: Dict[str, List[int]] = {"enemy": []}
        lvl = {c: bytes.fromhex(h) for c, h in LVL_TABLES.items()}
        abil = {c: bytes.fromhex(h) for c, h in ABILITY_EXP.items()}
        for c in CHAR_NAMES:
            found["lvl_" + c] = []
            found["abil_" + c] = []
        for start, size in MEM_REGIONS:
            data = bytearray()
            for off in range(0, size, 0x100000):
                data += self._read_chunk(start + off, 0x100000)
            for c, orig in lvl.items():
                n = struct.unpack_from(">I", orig, 0)[0]
                targets = [orig[4 + 40 * k: 8 + 40 * k] for k in range(n)]
                i = data.find(orig[:8])
                while i != -1:
                    if all(data[i + 4 + 40 * k: i + 8 + 40 * k] == targets[k] for k in range(n)):
                        found["lvl_" + c].append(start + i)
                    i = data.find(orig[:8], i + 1)
            for ci, c in enumerate(CHAR_NAMES):
                # search on the second record {id, row 1}: the first one is all zeros for Luffy
                head = struct.pack(">II", ci * 512, 1)
                i = data.find(head)
                while i != -1:
                    t = i - 44
                    if t >= 0 and t + 44 * 18 <= len(data) and all(
                            struct.unpack_from(">II", data, t + 44 * k) == (ci * 512 + k // 6, k % 6) for k in range(18)):
                        found["abil_" + c].append(start + t)
                    i = data.find(head, i + 4)
            i = data.find(b"ALTB")
            while i != -1:
                if data.find(b"item_dorp_id", i, i + 0x400) != -1 and data.find(b"enemy_id", i, i + 0x100) != -1:
                    nrows, doff, rs = (struct.unpack_from(">H", data, i + o)[0] for o in (6, 10, 12))
                    if rs == 40:
                        found["enemy"].append((start + i + doff, nrows, start + i))
                i = data.find(b"ALTB", i + 4)
        return found

    def _read_chunk(self, a: int, n: int) -> bytes:
        """Read n bytes; if Dolphin refuses a big read, retry in 64 KB pieces (unreadable pieces = zeros)."""
        try:
            return self.rd(a, n)
        except RuntimeError:
            out = bytearray()
            for off in range(0, n, 0x10000):
                try:
                    out += self.rd(a + off, 0x10000)
                except RuntimeError:
                    out += bytes(0x10000)
                    self.unreadable += 1
            return bytes(out)

    def scan_report(self) -> str:
        lvl = sum(1 for c in CHAR_NAMES if self.scan_cache.get("lvl_" + c))
        abil = sum(1 for c in CHAR_NAMES if self.scan_cache.get("abil_" + c))
        msg = (f"Game tables found: moves {lvl}/9, abilities {abil}/9, "
               f"enemy tables {len(self.scan_cache.get('enemy', []))}.")
        if self.unreadable:
            msg += f" ({self.unreadable} blocks of memory could not be read - remove Dolphin memory breakpoints.)"
        return msg

    def needs_scan(self) -> bool:
        return not self.tables_still_there() and time.monotonic() - self.last_scan >= 5

    def do_scan(self) -> None:
        """Slow (several seconds): run it in a worker thread."""
        self.last_scan = time.monotonic()
        self.unreadable = 0
        self.scan_cache = self._scan()
        self.scan_new = True

    def tables_still_there(self) -> bool:
        if not self.scan_cache:
            return False
        try:
            for c in CHAR_NAMES:
                orig = bytes.fromhex(LVL_TABLES[c])
                for a in self.scan_cache.get("lvl_" + c, []):
                    if self.rd(a, 8) != orig[:8]:
                        return False
            for _, _, header in self.scan_cache.get("enemy", []):
                if self.rd(header, 4) != b"ALTB":
                    return False
            for key, addrs in self.live_tables().items():
                if not set(addrs) <= set(self.scan_cache.get(key, [])):
                    return False                      # a save / stage load put the tables somewhere new
            return any(self.scan_cache.get("lvl_" + c) for c in CHAR_NAMES)
        except RuntimeError:
            return False

    def ensure_scan(self) -> bool:
        """Returns True when a new scan was made (tables need rewriting)."""
        new, self.scan_new = self.scan_new, False
        return new

    # ------------------------------------------------------------------ moves / abilities / co-op
    def move_table_bytes(self, c: str, allowed: Set[int]) -> bytes:
        """lvl table with every move-level requirement impossible, except moves in `allowed` (always met).
        Item requirements (type 2) are left alone: giving the item's found bits unlocks those moves."""
        orig = bytes.fromhex(LVL_TABLES[c])
        new = bytearray(orig)
        ci = CHAR_NAMES.index(c)
        n = struct.unpack_from(">I", orig, 0)[0]
        for i in range(n):
            base = 4 + 40 * i
            target = struct.unpack_from(">I", orig, base)[0] - ci * 512
            for j in range(3):
                a = base + 4 + 12 * j
                typ, pre, lv = struct.unpack_from(">3I", orig, a)
                if typ == 1:
                    struct.pack_into(">3I", new, a, *((0, pre, lv) if target in allowed else (1, pre, 99)))
        return bytes(new)

    def ability_table_bytes(self, c: str, owned: List[int]) -> bytes:
        t = bytearray(bytes.fromhex(ABILITY_EXP[c]))
        ci = CHAR_NAMES.index(c)
        for k in range(18):
            n, row = k // 6, k % 6
            if row >= (5 if n == 2 else 3):
                continue
            a = 44 * k + 8
            if row < owned[n]:
                # type 0 means "end of list" for abilities, so open the row with an always-true requirement
                struct.pack_into(">9I", t, a, 1, START_MOVE[ci], 1, 0, 0, 0, 0, 0, 0)
            else:
                # one impossible requirement, the rest "end of list", so the menu shows a single line
                struct.pack_into(">9I", t, a, 1, START_MOVE[ci], 99, 0, 0, 0, 0, 0, 0)
        return bytes(t)

    def live_tables(self) -> Dict[str, List[int]]:
        """Move / ability tables the loaded characters actually use (CharaObj +0x173C / +0x1748)."""
        out: Dict[str, List[int]] = {}
        m = self.chara_mgr()
        if not m:
            return out
        for ci, c in enumerate(CHAR_NAMES):
            o = self.u32(m + 0x90 + ci * 4)
            if not valid(o):
                continue
            lvl, abil = self.u32(o + 0x173C), self.u32(o + 0x1748)
            orig = bytes.fromhex(LVL_TABLES[c])
            if valid(lvl) and self.rd(lvl, 4) == orig[:4] and self.rd(lvl + 4, 4) == orig[4:8]:
                out.setdefault("lvl_" + c, []).append(lvl)
            if valid(abil) and self.rd(abil, 8) == struct.pack(">II", ci * 512, 0):
                out.setdefault("abil_" + c, []).append(abil)
        return out

    def write_tables(self, moves: Dict[int, Set[int]], abilities: Dict[int, List[int]]) -> bool:
        changed = False
        written = 0
        live = self.live_tables()
        for ci, c in enumerate(CHAR_NAMES):
            mb = self.move_table_bytes(c, moves.get(ci, set()))
            for a in set(self.scan_cache.get("lvl_" + c, [])) | set(live.get("lvl_" + c, [])):
                if self.rd(a, 8) != mb[:8]:
                    continue                              # not this table any more (memory was reused)
                if self.rd(a, len(mb)) != mb:
                    self.w(a, mb)
                    changed = True
                    written += 1
            ab = self.ability_table_bytes(c, abilities.get(ci, [0, 0, 0]))
            for a in set(self.scan_cache.get("abil_" + c, [])) | set(live.get("abil_" + c, [])):
                if self.rd(a, 8) != struct.pack(">II", ci * 512, 0) or \
                        self.rd(a + 44, 8) != struct.pack(">II", ci * 512, 1):
                    continue                              # not this table any more (memory was reused)
                if self.rd(a, len(ab)) != ab:
                    self.w(a, ab)
                    changed = True
        return changed

    @staticmethod
    def exp_table_bytes(c: str, factor: int) -> bytes:
        """EXP table with every per-level requirement divided by factor (rounded up, at least 1; caps of
        999 stay). factor 1 = vanilla."""
        t = bytearray(bytes.fromhex(EXP_TABLES[c]))
        if factor > 1:
            for r in range(len(t) // 64):
                for k in range(30):
                    a = r * 64 + 4 + k * 2
                    v = struct.unpack_from(">H", t, a)[0]
                    if 0 < v < 999:
                        struct.pack_into(">H", t, a, max(1, -(-v // factor)))
        return bytes(t)

    def write_exp(self, factor: int) -> None:
        m = self.chara_mgr()
        if not m:
            return
        for ci, c in enumerate(CHAR_NAMES):
            o = self.u32(m + 0x90 + ci * 4)
            if not valid(o):
                continue
            p = self.u32(o + 0x1738)
            if not valid(p):
                continue
            want = self.exp_table_bytes(c, factor)
            cur = self.rd(p, len(want))
            # only touch it if it is one of the known versions (never a table we don't recognise)
            if cur != want and cur in [self.exp_table_bytes(c, f) for f in EXP_FACTORS]:
                self.w(p, want)
            # The level-up check doesn't read the table: when a move is set into one of the 8 move
            # slots its 29 per-level requirements are copied to CharaObj+0x650 + slot*58 (0x80073b84),
            # and 0x80073738 reads that copy. Swap each slot's copy for the wanted version of its row.
            swap = self.exp_row_swap(c, factor)
            slots = self.rd(o + EXP_CACHE, EXP_CACHE_SLOTS * 58)
            for s in range(EXP_CACHE_SLOTS):
                blk = slots[s * 58:(s + 1) * 58]
                new = swap.get(blk)
                if new is not None and new != blk:
                    self.w(o + EXP_CACHE + s * 58, new)

    @staticmethod
    def exp_row_swap(c: str, factor: int) -> Dict[bytes, bytes]:
        """Maps each row's cached requirement block (any known version) to the wanted version. Blocks
        already in the wanted form map to themselves first, so a block is never divided twice."""
        key = (c, factor)
        if key not in _EXP_SWAP:
            want = GameState.exp_table_bytes(c, factor)
            rows = range(len(want) // 64)
            m: Dict[bytes, bytes] = {want[r * 64 + 4:r * 64 + 62]: want[r * 64 + 4:r * 64 + 62] for r in rows}
            for f in EXP_FACTORS:
                other = GameState.exp_table_bytes(c, f)
                for r in rows:
                    m.setdefault(other[r * 64 + 4:r * 64 + 62], want[r * 64 + 4:r * 64 + 62])
            m.pop(bytes(58), None)
            _EXP_SWAP[key] = m
        return _EXP_SWAP[key]

    def write_coop(self, allowed: Set[int]) -> bool:
        o = self.u32(COOP_PTR)
        if not valid(o):
            return False
        n, recs = self.u32(o + 0x14), self.u32(o + 0x18)
        nd, defs = self.u32(o + 0x1C), self.u32(o + 0x0C)
        if not valid(recs) or not valid(defs) or n > 16 or nd > 16:
            return False
        masks = {}
        for i in range(nd):
            cid = self.u32(defs + 72 * i)
            if cid & 0x80000000:
                masks[cid & 0xFFFFFF] = self.u32(defs + 72 * i + 0x44)
        changed = False
        for i in range(n):
            base = recs + 84 * i
            cid = self.u32(base) & 0xFFFFFF
            if cid not in (1, 2, 3):
                continue
            members = [c for c in range(9) if masks.get(cid, 0) >> c & 1]
            lv = 1 if cid in allowed else 99
            body = struct.pack(">2i", -1, -1) + b"".join(struct.pack(">2I", START_MOVE[c], lv) for c in members[:9])
            body = body.ljust(80, b"\0")
            if self.rd(base + 4, 80) != body:
                self.w(base + 4, body)
                changed = True
        return changed

    def install_hook(self) -> None:
        m = self.chara_mgr()
        if not m:
            return
        entry = m + 8 + HOOK_SLOT * 12
        cur = self.u32(entry)
        if cur == STUB:
            return
        if cur == 0:
            return                                    # still being set up; try again next poll
        if not (0x80003000 <= cur < 0x80600000) or self.u32(entry - 4) != 0xFFFFFFFF:
            self.say_once("hookslot", f"Unexpected callback {cur:08X}; instant unlocks are off.")
            return
        code = self._stub_code(cur)
        packed = b"".join(struct.pack(">I", x) for x in code)
        if self.rd(STUB, len(packed)) != packed:
            if self.u32(STUB) != 0:
                self.say_once("stub", "Old hook code is in memory (callback changed). Restart Dolphin if moves "
                                      "stop unlocking straight away.")
            self.w(HOOK_FLAG, b"\0\0\0")
            self.w(STUB, packed)
        self.w32(entry, STUB)

    def hook_active(self) -> bool:
        m = self.chara_mgr()
        return bool(m) and self.u32(m + 8 + HOOK_SLOT * 12) == STUB

    def boss_active(self) -> bool:
        """A boss is in one of slots 4-7 of the array at [0x8068A1B0] (see BossIsNull, 0x800B69F4)."""
        a = self.u32(0x8068A1B0)
        return valid(a) and any(self.u32(a + 4 * i) for i in range(4, 8))

    def event_playing(self) -> bool:
        """The hook doesn't give items while this is set (character manager +0x78 & 0x8000)."""
        m = self.chara_mgr()
        return bool(m) and bool(self.u32(m + 0x78) & 0x8000)

    def give_busy(self) -> bool:
        return self.rd(GIVE_FLAG, 1)[0] != 0

    def request_give(self, item: int, count: int = 1) -> None:
        """Ask the hook to give an item through the game's own code (messages, discovery, found bits)."""
        self.w(GIVE_ITEM_AT, struct.pack(">II", item, count))
        self.w(GIVE_FLAG, b"\x01")

    def cancel_give(self) -> None:
        self.w(GIVE_FLAG, b"\0")

    def request_unlock_check(self) -> None:
        self.w(HOOK_FLAG, b"\x01")

    @staticmethod
    def _stub_code(orig: int) -> List[int]:
        code, fix, lab = [], [], {}

        def emit(x): code.append(x)
        def br(kind, label): fix.append((len(code), kind, label)); code.append(0)
        def blto(t): code.append(bl(STUB + 4 * len(code), t))

        for x in (0x9421FFE0, 0x7C0802A6, 0x90010024, 0x93E1001C, 0x93C10018, 0x93A10014, 0x7C7F1B78):
            emit(x)
        blto(orig)
        emit(0x7C7D1B78)
        for x in (0x3C808000, 0x88A42F21, 0x38A50001, 0x98A42F21):   # call counter
            emit(x)
        # Give an item the way chests do, when the client asks (flag 0x80002F22, item 0x80002F24,
        # count 0x80002F28, item handle buffer 0x80002F30): ctor 0x800F8934, give 0x80040B4C(mgr, &h, n, 1, 1)
        emit(0x88042F22); emit(0x2C000000)
        br(0x41820000, "camp")
        emit(0x801F0078); emit(0x70008000)                 # not while an event is playing
        br(0x40820000, "camp")
        emit(0x38000000); emit(0x98042F22)
        emit(0x38642F30); emit(0x80842F24); emit(0x38A00000); emit(0x38C00000)
        blto(ITEM_HANDLE_CTOR)
        emit(0x7FE3FB78); emit(0x3C808000); emit(0x80A42F28); emit(0x38842F30)
        emit(0x38C00001); emit(0x38E00001)
        blto(GIVE_ITEM)
        emit(0x3C608000); emit(0x38632F30); emit(0x3880FFFF)
        blto(ITEM_HANDLE_DTOR)
        # After a Game Over revive the client sets byte 0x80002F07 a moment later:
        #   1 = back to the Thousand Sunny: run script 11990, the dinghy's touch script (fade, EnemyDestroy,
        #       FieldChange(19614) = the Sunny, CampIn);
        #   2 = retry, step 1: BossDelete() and EnemyDestroy() (natives 0x800B60B4 / 0x800BB000, called
        #       with an empty argument record at 0x80002F68 like a script call without arguments) while
        #       the fight's clear script is switched off. Destroyed enemies count as defeated a moment
        #       later; doing it inside the start script (which arms the clear script right after its own
        #       EnemyDestroy()) finished the ambush (0.6.2, Enforcer ambush 11280).
        #   3 = retry, step 2 (client, 1 s later): run the fight's start script (id at 0x80002F60), which
        #       fades out, places the party, raises the barrier, plays the intro, creates the enemies /
        #       boss again and arms its clear script.
        # Scripts are started the way the field touch dispatcher does (0x8004596C: 0x8009F018(scriptmgr,
        # id, 0, 0, 0, 0, 0, 0)), from a normal frame, not the death handler; never while an event or a
        # menu is up ([mgr+0x78] & 0x8180) or the camp menu is open.
        lab["camp"] = len(code)
        emit(lis(4, 0x8000)); emit(lbz(0, 0x2F07, 4)); emit(cmpwi(0, 0))
        br(0x41820000, "unlock")
        emit(lwz(0, 0x78, 31)); emit(andi_(0, 0, 0x8180))
        br(0x40820000, "unlock")
        emit(lwz(0, 0x30C, 31)); emit(cmpwi(0, 0))
        br(0x40820000, "unlock")                           # wait until the camp menu is closed
        emit(lis(4, 0x8000)); emit(lbz(0, 0x2F07, 4)); emit(cmpwi(0, 3))
        br(0x41820000, "restart")
        emit(cmpwi(0, 2))
        br(0x40820000, "trip")
        emit(lis(3, 0x8000)); emit(addi(3, 3, 0x2F68))
        blto(0x800B60B4)                                   # BossDelete()
        emit(lis(3, 0x8000)); emit(addi(3, 3, 0x2F68))
        blto(0x800BB000)                                   # EnemyDestroy()
        br(0x48000000, "campclear")
        lab["restart"] = len(code)
        emit(lis(4, 0x8000)); emit(lwz(4, 0x2F60, 4))
        br(0x48000000, "run")
        lab["trip"] = len(code)
        emit(li(4, 11990))
        lab["run"] = len(code)
        for x in (lwz(3, -0x5CA4, 13), li(5, 0), li(6, 0), li(7, 0), li(8, 0), li(9, 0), li(10, 0)):
            emit(x)
        blto(0x8009F018)
        lab["campclear"] = len(code)
        emit(lis(4, 0x8000)); emit(li(0, 0)); emit(stb(0, 0x2F07, 4))
        lab["unlock"] = len(code)
        emit(0x3C808000); emit(0x88042F20); emit(0x2C000000)
        br(0x41820000, "done")
        emit(0x801F0078); emit(0x70008000)
        br(0x40820000, "done")
        emit(0x38000000); emit(0x98042F20)
        emit(0x3BC00090)
        lab["loop"] = len(code)
        emit(0x7C7FF02E); emit(0x2C030000)
        br(0x41820000, "next")
        emit(0x38800000); blto(MOVE_CHECKER)
        emit(0x7C7FF02E); blto(ABILITY_CHECKER)
        lab["next"] = len(code)
        emit(0x3BDE0004); emit(0x2C1E00B4)
        br(0x41800000, "loop")
        lab["done"] = len(code)
        for x in (0x7FA3EB78, 0x80010024, 0x83E1001C, 0x83C10018, 0x83A10014, 0x7C0803A6, 0x38210020, 0x4E800020):
            emit(x)
        for i, kind, label in fix:
            code[i] = kind | (((lab[label] - i) * 4) & (0x3FFFFFC if kind == 0x48000000 else 0xFFFC))
        return code

    def strip_fragment_drops(self) -> None:
        """No treasure map fragment drops (kills, steals, Break Rush). Checked every poll: the enemy
        table is reloaded with stage changes, sometimes at the same address."""
        for base, nrows, header in self.scan_cache.get("enemy", []):
            if self.rd(header, 4) != b"ALTB" or not 0 < nrows <= 512:
                continue
            data = self.rd(base, nrows * 40)
            for r in range(nrows):
                d0, d1 = struct.unpack_from(">2I", data, r * 40 + 24)
                a = base + r * 40
                if d1 in FRAGMENT_ITEMS:
                    self.w32(a + 28, 0 if d0 in FRAGMENT_ITEMS else d0)
                    self.w(a + 38, b"\0\0")       # rare drop chance 0
                if d0 in FRAGMENT_ITEMS:
                    self.w32(a + 24, 0)
                    self.w(a + 36, b"\0\0")

    # ------------------------------------------------------------------ items: bag / found bits
    def _player_items(self) -> Optional[int]:
        o = self.u32(PLAYER_ITEMS_PTR)
        return o if valid(o) else None

    def _list(self, name: str) -> Optional[Tuple[int, int, int]]:
        o = self._player_items()
        if not o:
            return None
        base = o + LIST_OFFSET[name]
        cap, slots = self.u32(base), self.u32(base + 8)
        if not valid(slots) or not 0 < cap <= 256:
            return None
        return base, cap, slots

    def _item_mgr(self) -> Optional[int]:
        bag = self._list("bag")
        if not bag:
            return None
        m = self.u32(bag[0] + 0x10)
        return m if valid(m) else None

    def find_slots(self, item: int) -> List[int]:
        out = []
        for name in ("bag", "palette", "storage"):
            lst = self._list(name)
            if not lst:
                continue
            _, cap, slots = lst
            data = self.rd(slots, cap * 16)
            for k in range(cap):
                if struct.unpack_from(">I", data, k * 16)[0] == item:
                    out.append(slots + k * 16)
        return out

    def has_room(self, item: int, count: int = 1) -> bool:
        """Can the game's give put this consumable (count of it) somewhere? It tries the bag, then the palette
        (0x80040B4C: ItemBag, then ItemEquip); with both full it shows its "can't carry" message instead."""
        for name in ("bag", "palette"):
            lst = self._list(name)
            if not lst:
                continue
            _, cap, slots = lst
            data = self.rd(slots, cap * 16)
            for k in range(cap):
                sid = struct.unpack_from(">I", data, k * 16)[0]
                if sid == 0 or (sid == item and data[k * 16 + 4] + count <= 99):
                    return True
        return False

    def item_count(self, item: int) -> int:
        """How many of an item the player carries (bag, palette and Storage)."""
        return sum(self.rd(a + 4, 1)[0] for a in self.find_slots(item))

    def found(self, item: int) -> bool:
        m = self._item_mgr()
        if not m:
            return False
        return bool(self.rd(m + 0x18 + item // 4, 1)[0] >> ((item % 4) * 2) & 1)

    def set_found(self, item: int) -> None:
        m = self._item_mgr()
        if not m:
            return
        a = m + 0x18 + item // 4
        v = self.rd(a, 1)[0]
        nv = v | (3 << ((item % 4) * 2))
        if nv != v:
            self.w(a, bytes([nv]))
            c = self.rd(m + 0x57 + item, 1)[0]
            self.w(m + 0x57 + item, bytes([min(255, c + 1)]))

    def add_to_bag(self, item: int, count: int = 1) -> bool:
        """Put an item in the bag (or Storage if the bag is full). Stacks with an existing slot."""
        for name in ("bag", "storage"):
            lst = self._list(name)
            if not lst:
                continue
            _, cap, slots = lst
            data = self.rd(slots, cap * 16)
            for k in range(cap):
                if struct.unpack_from(">I", data, k * 16)[0] == item and data[k * 16 + 4] < 99:
                    self.w(slots + k * 16 + 4, bytes([min(99, data[k * 16 + 4] + count)]))
                    self.set_found(item)
                    return True
            for k in range(cap):
                if struct.unpack_from(">I", data, k * 16)[0] == 0:
                    self.w(slots + k * 16, struct.pack(">I", item) + bytes([count]) + bytes(11))
                    self.set_found(item)
                    return True
        return False

    def remove_placeholders(self) -> None:
        for a in self.find_slots(PLACEHOLDER):
            self.w(a, bytes(16))

    def ensure_key_item(self, item: int) -> None:
        """Give a one-off item if it isn't owned yet (found bits are the 'already given' marker)."""
        if item in STORE_ITEMS:
            if not self.find_slots(item) and not self.found(item):
                self.add_to_bag(item)
            elif not self.found(item):
                self.set_found(item)
        else:
            self.set_found(item)

    def ensure_slot_byte(self, item: int, offset: int, value: int) -> None:
        for a in self.find_slots(item):
            if self.rd(a + offset, 1)[0] != value:
                self.w(a + offset, bytes([value]))

    def set_capacity(self, list_name: str, value: int) -> None:
        o = self._player_items()
        if not o:
            return
        a = o + LIST_OFFSET[list_name]
        if self.u32(a) < value:
            self.w32(a, value)

    # ------------------------------------------------------------------ Gabri and shrines
    def set_gabri(self, level: int) -> None:
        g = self.u32(GABRI_PTR)
        if not valid(g):
            return
        want = [b * 100 for b in GABRI_MAX[min(level, 13)]]
        mx = list(struct.unpack(">6h", self.rd(g, 12)))
        if mx != want:
            self.w(g, struct.pack(">6h", *want))
            cur = list(struct.unpack(">6h", self.rd(g + 0xC, 12)))
            self.w(g + 0xC, struct.pack(">6h", *(min(c, m) for c, m in zip(cur, want))))

    def _shrines(self) -> Iterable[Tuple[int, int, int]]:
        """(shrine id, row address, state byte address) for zones 0-1."""
        m = self.u32(SHRINE_MGR_PTR)
        if not valid(m):
            return
        for z, rows in ((0, 1), (1, 7)):
            t = self.u32(m + 0x18 + z * 4)
            if not valid(t):
                continue
            for r in range(rows):
                a = t + r * 0x38
                yield self.u32(a), a, m + 0x48 + z * 0x80 + r

    def set_shrine_locks(self, unlocked: Set[int]) -> None:
        for sid, row, _ in self._shrines():
            if sid not in SHRINE_COSTS or sid == 1010:
                continue
            cost = SHRINE_COSTS[sid] if sid in unlocked else [SHRINE_LOCKED] * 7
            b = struct.pack(">7H", *cost)
            if self.rd(row + 0xC, 14) != b:
                self.w(row + 0xC, b)

    def activated_shrines(self) -> Set[int]:
        return {sid for sid, _, st in self._shrines() if self.rd(st, 1)[0] & 0x02}

    # ------------------------------------------------------------------ flags
    def _section(self, name: str) -> Optional[int]:
        lst = self.u32(FLAG_LIST)
        node = self.u32(lst) if valid(lst) else 0
        seen = set()
        while valid(node) and node not in seen:
            seen.add(node)
            np = self.u32(node + 8)
            if valid(np) and self.rd(np, len(name) + 1) == name.encode() + b"\0":
                d = self.u32(node + 0x10)
                return d if valid(d) else None
            node = self.u32(node)
        return None

    def read_delivered(self) -> Optional[Tuple[bool, int]]:
        """(save has our marker, count) or None when the save data isn't there."""
        d = self._section(DELIVERED_SECTION)
        if not d:
            return None
        v = self.u32(d + DELIVERED_OFFSET)
        same_seed = self.u32(d + DELIVERED_OFFSET - 4) == self.seed_tag
        return (v >> 16 == DELIVERED_MARK and same_seed, v & 0xFFFF)

    def write_delivered(self, n: int) -> None:
        d = self._section(DELIVERED_SECTION)
        if d:
            self.w32(d + DELIVERED_OFFSET - 4, self.seed_tag)
            self.w32(d + DELIVERED_OFFSET, DELIVERED_MARK << 16 | min(n, 0xFFFF))

    def fight_in_progress(self) -> Optional[Tuple[int, int]]:
        """A scripted fight is running when its start script has finished (EventScriptEndFlag) and its
        clear script hasn't."""
        flags = self.script_flags([n for pair in FIGHTS for n in pair])
        for start, clear in FIGHTS:
            if clear in flags:
                continue
            # start script finished, or its clear script armed (FuncSetEnable(clear, true) at its end)
            if start in flags or self.func_enabled(clear):
                return start, clear
        return None

    def func_enabled(self, n: int) -> bool:
        d = self._section("EventFuncEnableFlag")
        return bool(d) and bool(self.u32(d + (n >> 5) * 4) >> (n & 31) & 1)

    def debug_state(self) -> str:
        m = self.chara_mgr()
        flags = self.script_flags([n for pair in FIGHTS for n in pair])
        fights = " ".join(f"{a}:{int(a in flags)}/{b}:{int(b in flags)}/arm{int(self.func_enabled(b))}"
                          for a, b in FIGHTS if a < 12000) or "none"
        return (f"mgr+0x78 {self.u32(m + 0x78) if m else 0:08X}; camp menu {self.u32(m + 0x30C) if m else 0:08X}; "
                f"Game Over bytes {self.rd(GO_BYTE, 3).hex()}; fight flags {fights}")

    def set_func_enable(self, n: int, on: bool) -> None:
        d = self._section("EventFuncEnableFlag")
        if not d:
            return
        a = d + (n >> 5) * 4
        v = self.u32(a)
        nv = v | (1 << (n & 31)) if on else v & ~(1 << (n & 31))
        if nv != v:
            self.w32(a, nv & 0xFFFFFFFF)

    def script_flags(self, flags: Iterable[int]) -> Set[int]:
        d = self._section("EventScriptEndFlag")
        if not d:
            return set()
        out = set()
        for n in flags:
            if self.u32(d + (n >> 5) * 4) >> (n & 31) & 1:
                out.add(n)
        return out

    # ------------------------------------------------------------------ chests
    def _chest_table(self):
        p = self.u32(TREASURE_PTR)
        if not valid(p):
            return None
        t = self.u32(p + 0x30)
        if not valid(t):
            return None
        recs, cont, n = self.u32(t + 0x3C), self.u32(t + 0x40), self.u32(t + 0x44)
        if not valid(recs) or not valid(cont) or not 0 < n <= 64:
            return None
        return p, recs, cont, n

    def set_chest_placeholders(self, chest_ids: Set[int]) -> None:
        tab = self._chest_table()
        if not tab:
            return
        _, recs, cont, n = tab
        for i in range(n):
            cid, _, idx = struct.unpack(">3I", self.rd(recs + i * 12, 12))
            if cid in chest_ids:
                a = cont + idx * 8
                if self.rd(a, 8) != struct.pack(">2I", PLACEHOLDER, 1):
                    self.w(a, struct.pack(">2I", PLACEHOLDER, 1))

    def opened_chests(self, chest_ids: Set[int]) -> Set[int]:
        tab = self._chest_table()
        if not tab:
            return set()
        p, _, _, n = tab
        out = set()
        data = self.rd(p + 0x238, n * 8)
        for i in range(n):
            cid, got = struct.unpack_from(">2I", data, i * 8)
            if cid in chest_ids and got:
                out.add(cid)
        return out

    # ------------------------------------------------------------------ placeholder item and recipes
    def rename_placeholder(self) -> None:
        t = self.u32(ITEM_NAMES_PTR)
        if not valid(t):
            return
        row = t + PLACEHOLDER * 0x224
        if struct.unpack(">H", self.rd(row + 0x42, 2))[0] != PLACEHOLDER:
            return
        name = PLACEHOLDER_NAME.encode("utf-16-be").ljust(0x42, b"\0")
        desc = PLACEHOLDER_DESC.encode("utf-16-be").ljust(0xA0, b"\0")
        if self.rd(row, 0x42) != name:
            self.w(row, name)
        if self.rd(row + 0x44, 0xA0) != desc:
            self.w(row + 0x44, desc)

    def _recipe_state_obj(self, room: str) -> Optional[int]:
        m = self.u32(ITEM_MGR_PTR)
        if not valid(m):
            return None
        o = self.u32(m + ROOM_INDEX[room] * 4)
        return o if valid(o) else None

    def _recipe_row(self, room: str, row: int) -> Optional[int]:
        p = self.u32(RECIPE_ROWS + ROOM_INDEX[room] * 4)
        return p + row * 252 if valid(p) else None

    def setup_recipes(self, comments: Dict[Tuple[str, int], str], hidden: Set[Tuple[str, int]] = frozenset(),
                      veiled: Set[Tuple[str, int]] = frozenset()) -> None:
        """Every recipe listed + discovered (no recipe chains), key-item recipes give the placeholder for good,
        and their comments say whose item it is."""
        for room in ("workshop", "kitchen", "pharmacy"):
            o = self._recipe_state_obj(room)
            p = self._recipe_row(room, 0)
            if not o or not p:
                continue
            st = bytearray(self.rd(o + 4, 32))
            rows = self.rd(p, 252 * 32)
            new = bytearray(st)
            for r in range(32):
                # State bits: 0x01 listed (shown in the menu, counted by 0x800F5C9C), 0x04 "idea" already had
                # (0x800F5B54 skips those when an obtained item could discover a recipe), 0x08 made.
                if (room, r) in hidden:
                    if not new[r] & 0x08:
                        new[r] &= ~0x05 & 0xFF            # undiscovered: the game can discover it ("An Idea!")
                elif (room, r) in veiled:
                    if not new[r] & 0x08:
                        # shown as ????? but marked as already had: the game's own "An Idea!" popup must not fire
                        # for these (on an Archipelago Item recipe it reads a null string, user 2026-10-22)
                        new[r] = (new[r] | 0x04) & ~0x01 & 0xFF
                elif struct.unpack_from(">H", rows, r * 252)[0]:
                    new[r] |= 0x05
            if new != st:
                self.w(o + 4, bytes(new))
            # vanilla-result recipes: the AP comment until made, then the game's own comment again
            dummies = set(DUMMY_RECIPES.get(room, []))
            for r in range(32):
                if r in dummies or not struct.unpack_from(">H", rows, r * 252)[0]:
                    continue
                text = RECIPE_COMMENTS.get(room, {}).get(r) if new[r] & 0x08 else comments.get((room, r))
                if text:
                    b = (text.encode("utf-16-be") + b"\0\0").ljust(224, b"\0")
                    if rows[r * 252 + 28:r * 252 + 252] != b:
                        self.w(p + r * 252 + 28, b)
            for r in DUMMY_RECIPES.get(room, []):
                a = p + r * 252
                if struct.unpack_from(">H", rows, r * 252)[0] not in (0, PLACEHOLDER):
                    self.w(a, struct.pack(">H", PLACEHOLDER))
                # Once made (check sent), the recipe asks for one Archipelago Item, which the player never
                # carries (the client removes it), so it can't be made again by accident.
                # Row: +0 u16 result, +2 u16, +4 4 x {u16 ingredient, u8 count, u8 flag}.
                if new[r] & 0x08:
                    locked = struct.pack(">HBB", PLACEHOLDER, 1, 0) + bytes(12)
                    if rows[r * 252 + 4:r * 252 + 20] != locked:
                        self.w(a + 4, locked)
                text = comments.get((room, r))
                if text:
                    b = (text.encode("utf-16-be") + b"\0\0").ljust(224, b"\0")
                    if self.rd(a + 28, 224) != b:
                        self.w(a + 28, b)

    def crafted(self) -> Set[Tuple[str, int]]:
        out = set()
        for room in ("workshop", "kitchen", "pharmacy"):
            o = self._recipe_state_obj(room)
            if not o:
                continue
            st = self.rd(o + 4, 32)
            for r in range(32):
                if st[r] & 0x08:
                    out.add((room, r))
        return out

    def chapter(self) -> int:
        """Story chapter (island bosses beaten + 2), [0x8068A298] + 0x10; 0 if not readable."""
        ro = self.u32(RESET_OBJ_PTR)
        return self.u32(ro + 0x10) if valid(ro) else 0

    # ------------------------------------------------------------------ co-op move levels
    def coop_levels(self) -> Dict[int, int]:
        """Co-op n level = byte at Z + 0x568 + n * 2 of its members (highest one counts)."""
        m = self.chara_mgr()
        out: Dict[int, int] = {}
        if not m:
            return out
        for cid, members in COOP_MEMBERS.items():
            for ci in members:
                o = self.u32(m + 0x90 + ci * 4)
                if valid(o):
                    out[cid] = max(out.get(cid, 0), self.rd(o + 0xA48 + 0x568 + cid * 2, 1)[0])
        return out

    # ------------------------------------------------------------------ move levels
    def move_levels(self) -> Dict[Tuple[int, int], int]:
        m = self.chara_mgr()
        out = {}
        if not m:
            return out
        for ci in range(9):
            o = self.u32(m + 0x90 + ci * 4)
            if not valid(o):
                continue
            z = o + 0xA48
            data = self.rd(z + 0x28, 64)
            for n in range(32):
                out[(ci, n)] = data[n * 2]
        return out
