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
EXP_FACTORS = (1, 2, 3, 4, 5)
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
# Next Island menu: 0x801C2488(n) says whether island n can be picked (n = 0: the menu entry itself; vanilla
# n 1-2 always but the menu needs chapter > 2, n 3-5 need chapter > n). The entry branches to our routine:
# n = 0..6 return a byte of ISLAND_TABLE, which the client fills from the Log Pose items (opuc-sunny-state.md;
# tested with tools/opuc_sunny.py, Gorge Isle before Eneru plays fine, user 2026-10-22). Code patch.
ISLAND_FUNC, ISLAND_ORIG, ISLAND_CODE_AT, ISLAND_TABLE = 0x801C2488, 0x9421FFE0, 0x80002700, 0x80002780
ISLAND_CODE = [0x28030006, 0x41810014, 0x3C808000, 0x38842780,
               (31 << 26) | (3 << 21) | (4 << 16) | (3 << 11) | (87 << 1), 0x4E800020, ISLAND_ORIG,
               0x48000000 | ((ISLAND_FUNC + 4 - (ISLAND_CODE_AT + 28)) & 0x3FFFFFC)]
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
    (12250, 12251), (12262, 12263), (12270, 12271),
    (12300, 12301), (12300, 12302),   # Gorge Isle mid-boss: Kuro (12301) and Krieg (12302) in one fight
    (12350, 12351), (12400, 12401),
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

# Traps wait while one of these is out: Bug-Catcher Net (2), Broken net (3), Fishing Rods (6, 166-168); -1 = a tool
# whose item couldn't be read (be safe).
TRAP_BLOCKING_TOOLS = {2, 3, 6, 166, 167, 168, -1}

# Status routine for hook commands 5 / 6 (r3 = character manager): add / remove status [0x80002F74] (time
# [0x80002F78]) on the current character. Free low memory 0x80002790-0x800027FF (after the island table).
STATUS_AT = 0x80002790

# Thousand Sunny check. Current field = script native FieldGetID (0x800A9538) = [[0x8068A218] + 0x20], a field index:
# 0 = the Thousand Sunny, 1 = Wooded Isle (user test 0.22.2; the scripts compare it with IdxToID(19614..19619) =
# Sunny, Wooded, Gorge, Iceberg, Island 4, Central Isle).
FIELD_MGR_PTR, SUNNY_FIELD = 0x8068A218, 0

# Wardrobe touch spots (0.23.0). The Garment Box's item event 354 runs FieldGroupEnable(10808 / 10809) wherever it
# is received, so a box received away from the Sunny never shows them (user). Hook command 8 runs the script native
# FieldGroupEnable (0x800A8F40: r3 = group id arg, r4 = on arg, r5 = field arg; script args are 8 bytes {value,
# u32 type}, type 0 = not given -> current field) for both, from routine WARDROBE_AT (free space after the second
# Game Over block) with the argument records at WARDROBE_ARGS (2 x 24 bytes).
WARDROBE_AT, WARDROBE_ARGS, FIELD_GROUP_ENABLE = 0x80002BC0, 0x80002F80, 0x800A8F40
WARDROBE_SPOTS = (10808, 10809)


def wardrobe_code() -> List[int]:
    at, a = WARDROBE_AT, WARDROBE_ARGS & 0xFFFF
    def b(i, t, link=1): return 0x48000000 | link | ((t - (at + 4 * i)) & 0x3FFFFFC)
    return [0x9421FFF0, 0x7C0802A6, 0x90010014,                      # 0-2 frame
            lis(3, 0x8000), addi(3, 3, a), addi(4, 3, 8), addi(5, 3, 16), b(7, FIELD_GROUP_ENABLE),   # 3-7 10808
            0x80010014, 0x7C0803A6, 0x38210010,                      # 8-10 frame off
            lis(3, 0x8000), addi(3, 3, a + 24), addi(4, 3, 8), addi(5, 3, 16),
            b(15, FIELD_GROUP_ENABLE, 0)]                            # 11-15 10809, tail call


def wardrobe_args() -> bytes:
    return b"".join(struct.pack(">IIIIII", sid, 2, 1, 2, 0, 0) for sid in WARDROBE_SPOTS)


def status_code() -> List[int]:
    at = STATUS_AT
    def call(i, t): return 0x48000001 | ((t - (at + 4 * i)) & 0x3FFFFFC)
    return [0x9421FFF0, 0x7C0802A6, 0x90010014,                 # 0-2  frame
            lwz(3, 0x88, 3), cmpwi(3, 0), 0x41820040,           # 3-5  player? else -> out (word 21)
            call(6, 0x804CE1A4), cmpwi(3, 0), 0x41820034,       # 6-8  status object? else -> out
            lis(6, 0x8000), lbz(0, 0x2F07, 6), lwz(4, 0x2F74, 6), lwz(5, 0x2F78, 6),   # 9-12
            cmpwi(0, 6), 0x41820010,                            # 13-14 remove? -> word 18
            call(15, 0x804DF60C), 0x48000014,                   # 15-16 add, -> out (word 21)
            0x60000000,                                         # 17
            li(5, 0), call(19, 0x804DFB34), 0x60000000,         # 18-20 remove
            0x80010014, 0x7C0803A6, 0x38210010, 0x4E800020]     # 21-24 out


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
GOLD_ORB = 85
GUNPOWDER = 15
ORB_ITEMS = [80, 81, 82, 83, 84, 85]     # Red, Blue, White, Green, Black, Gold
# field/fobj_gen_item_table.atb (items from breaking / burning / vacuuming field objects): ALTB, 103 rows of
# 300 bytes at +0x10, 25 x {u32 item, u32 count, f32 chance} per row. Rows 96-100 column 22 = the Sunny's
# Map 10 fragments (vacuumed dust).
GEN_ITEM_OFF, GEN_ITEM_ROW, GEN_ITEM_ROWS, GEN_ITEM_VACUUM = 0x10, 300, 103, 22
GEN_ITEM_MAP_ROWS = [96, 97, 98, 99, 100]
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


def item_kind(flags: int) -> str:
    """Archipelago item flags -> the word used in recipe comments."""
    return "Progression" if flags & 1 else "Useful" if flags & 2 else "Trap" if flags & 4 else "Filler"


def _first_fit(options: List[List[str]]) -> Optional[str]:
    for lines in options:
        text = wrap_comment(lines)
        if text and all(ord(c) < 0x2000 for c in text):
            return text
    return None


def placeholder_comment(player: str, item: str, kind: Optional[str] = None) -> str:
    """Comment for a recipe whose result is the Archipelago Item. Falls back to the item's type when the name doesn't
    fit (or the player's name can't be shown)."""
    opts = [["An Archipelago Item!", f"It's {player}'s {item}!"], [f"It's {player}'s {item}!"]]
    if kind:
        opts += [["An Archipelago Item!", f"It's {player}'s {kind} Item!"], [f"It's {player}'s {kind} Item!"],
                 [f"An Archipelago {kind} Item!"]]
    opts += [["An Archipelago Item!", f"It belongs to {player}!"]]
    return _first_fit(opts) or "An Archipelago Item!"


def also_comes_comment(player: Optional[str], item: Optional[str], kind: Optional[str] = None) -> str:
    """Comment for a vanilla-result recipe that is a location, until it's made (then the vanilla one). Item name too
    long -> "(player)'s <type> Item"; player's name not showable either -> "an Archipelago <type> Item" (user,
    0.23.1: a long item name fell back to the plain text)."""
    opts = []
    if player and item:
        opts.append([f"This recipe also comes with {player}'s {item}!"])
    if kind:
        if player:
            opts.append([f"This recipe also comes with {player}'s {kind} Item!"])
        opts.append([f"This recipe also comes with an Archipelago {kind} Item!"])
    opts.append(["This recipe also comes with an Archipelago Item!"])
    return _first_fit(opts) or "An Archipelago Item!"


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
                    for c in self.fight_clears(start):    # every unfinished clear script of this fight
                        self.set_func_enable(c, False)
                    self.w(RETRY_SCRIPT, struct.pack(">I", start) + bytes(12))
                    self.w(CAMP_CMD, b"\x02")
                    self.last_retry = start
                    self.retry_pending = (start, clear, None)
                    self.retry_time = time.monotonic()
                # back to the Sunny only once it has been reached in the story (script 11990 has run
                # before) and no unknown boss fight is running (leaving one leaves it running: boss HUD,
                # barrier, softlock); otherwise the revive alone has to do
                elif self.script_flags([11990]) and not self.boss_active() and self.on_sunny() is False:
                    self.w(CAMP_CMD, b"\x01")             # (already on the Sunny: the trip there crashed, 0.22.1)
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
                    for c in self.fight_clears(start):
                        self.set_func_enable(c, False)
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

    # Starting Costumes (0.25.10): the save-data getters. Every Straw Hat's costume and style come from the save data
    # through two getters: costume 0x80103850(data, id, slot) (u16 at slot * 132 + id * 12 + 0x9C) and style
    # 0x80103944 (u32 at + 0xA0); id is kept in r30. Readers: the character constructor 0x80057014 (0x800573C0 /
    # 0x800573D4, then +0xC4 = +0xC0 and the model loads) AND the save loader 0x8006ECA8 (0x8006F0A8 / 0x8006F374),
    # which runs after the constructor and re-reads +0xC0 / +0xEC. 0.25.8 only patched the constructor, so the
    # models loaded in the Starting Costume (+0xC4 = 1) and the loader then put +0xC0 back to 0 (user test on
    # 0.25.9: costume 0, loaded 1). Now the getters themselves turn a 0 into the client's table (0x80002FB0: 9
    # costumes, then 9 styles) for ids 0-8, so every reader agrees: built in the costume, no mismatch, no reload.
    # The save serializer 0x8006E8A0 writes +0xC0 / +0xEC back, so it sticks once saved. A costume other than the
    # default in the save (changed at a wardrobe) is kept; choosing Unlimited / style 0 again at a wardrobe falls
    # back to the Starting Costume on the next load.
    #   0x801038B4 rlwinm r3, r0, 0, 16, 31 (costume)  -> bl COSTUME_AT
    #   0x801039A4 lwz r3, 160(r3)          (style)    -> bl COSTUME_AT + 12
    COSTUME_GETTERS = ((0x801038B4, 0x5403043E), (0x801039A4, 0x806300A0))
    COSTUME_STORES = ((0x800573C4, 0x907400C0), (0x800573D8, 0x907400EC))   # 0.25.8 patch: undo if still there
    COSTUME_OLD_SITES = ((0x800573C0, 0x80103850), (0x800573D4, 0x80103850))  # 0.25.6 patch: undo if still there
    COSTUME_AT, COSTUME_TABLE = 0x800029C0, 0x80002FB0

    @classmethod
    def costume_code(cls) -> List[int]:
        t = cls.COSTUME_TABLE & 0xFFFF
        return [0x5403043E, 0x39800000 | t, 0x48000010,          # 0-2  costume: original ; li r12, table ; b 6
                0x806300A0, 0x39800000 | (t + 9),                # 3-4  style: original ; li r12, table + 9
                0x60000000,                                      # 5
                0x2C030000, 0x4C820020,                          # 6-7  not 0 -> return it
                0x281E0009, 0x4C800020,                          # 8-9  id >= 9 -> return it
                0x3D8C8000, 0x7C6CF0AE,                          # 10-11 r3 = table[id] (lbzx r3, r12, r30)
                0x4E800020]                                      # 12

    def patch_costume_creation(self) -> None:
        for a, target in self.COSTUME_OLD_SITES:          # a 0.25.6 patch from this Dolphin session
            if self.u32(a) != bl(a, target) and (self.u32(a) >> 26) == 18:
                self.w32(a, bl(a, target))
        for a, orig in self.COSTUME_STORES:               # a 0.25.8 patch from this Dolphin session
            if self.u32(a) != orig and (self.u32(a) >> 26) == 18:
                self.w32(a, orig)
        if all(self.u32(a) == orig for a, orig in self.COSTUME_GETTERS):
            for i, x in enumerate(self.costume_code()):
                self.w32(self.COSTUME_AT + i * 4, x)
            for k, (a, _orig) in enumerate(self.COSTUME_GETTERS):
                self.w32(a, bl(a, self.COSTUME_AT + 12 * k))

    def set_costume_table(self, wanted: Optional[List[List[int]]]) -> None:
        """[costume, style] per Straw Hat used for anyone built with the default (0) costume / style."""
        wanted = list(wanted or [])[:9] + [[0, 0]] * (9 - len(wanted or []))
        data = bytes([c for c, _ in wanted] + [st for _, st in wanted])
        if self.rd(self.COSTUME_TABLE, len(data)) != data:
            self.w(self.COSTUME_TABLE, data)

    def costume_override_live(self) -> bool:
        a = self.COSTUME_GETTERS[0][0]
        return self.u32(a) == bl(a, self.COSTUME_AT)

    def apply_patches(self, slot_data: Optional[dict] = None) -> None:
        """Code patches. They only work if written before the game first runs that code (title screen)."""
        if self.patched:
            return
        sd = slot_data or {}
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
        self.patch_costume_creation()                  # Starting Costumes at character creation (title screen)
        self.patch_craft_copies()                      # stack craftables come in their vanilla amount (0.25.17)
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
        # Next Island menu follows the Log Pose items (vanilla until the client fills the table)
        if self.u32(ISLAND_FUNC) == ISLAND_ORIG:
            self.w(ISLAND_TABLE, bytes(8))
            for i, x in enumerate(ISLAND_CODE):
                self.w32(ISLAND_CODE_AT + i * 4, x)
            self.w32(ISLAND_FUNC, 0x48000000 | ((ISLAND_CODE_AT - ISLAND_FUNC) & 0x3FFFFFC))
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
        # 0.18.2: these went in only once a save had loaded (0.18.0 / 0.18.1), too late for code the game had
        # already run (Dolphin's JIT keeps the old code): "An Idea!" still fired for Tone Dial / Mystery Gadget.
        self.patch_recipe_discovery()
        self.patch_item_flash()
        self.patch_idea_popup()
        self.patch_database_menu()
        if int(sd.get("disable_food_diminishing_returns", 0)):
            self.patch_food_returns()
        if int(sd.get("traps_never_expire", 0)):
            self.patch_traps()
        if int(sd.get("fast_traps", 0)):
            self.patch_fast_traps()
        if int(sd.get("chopper_brook_cold_resistance", 0)):
            self.patch_cold_resistance()
        if int(sd.get("aquarium_open", 1)):
            self.patch_aquarium()
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

    # Trap lifetime (docs/traps.md): 0x80047CE4 ticks each trap's catch timer (+0xB0) and lifetime (+0xB4). The
    # lifetime running out destroys the trap, before or after the catch. The lifetime stores become nops and the
    # two "lifetime > 0" branches always taken, so a trap always catches and waits until it's checked.
    TRAP_SITES = [(0x80047E38, 0x901E00B4, 0x60000000), (0x80047E3C, 0x4181001C, 0x4800001C),
                  (0x80047E80, 0x901E00B4, 0x60000000), (0x80047E84, 0x41810018, 0x48000018)]

    # Chopper & Brook always have Cold Resistance (docs/status_effects.md): 0x800CB2E4 (every frame) marks the player
    # cold (+0x9C |= 0x800, no SP regen) in a cold area unless they have status 17 (endure_ice). Its
    # "has status" branch 0x800CB35C (bne 0x800CB374) goes to a stub (free since the Walk the Sunny routine went,
    # 0x80002740-0x80002773) that also skips the mark when the player is Chopper ([mgr]+0xA4) or Brook ([mgr]+0xB0).
    COLD_SITE, COLD_ORIG, COLD_AT = 0x800CB35C, 0x40820018, 0x80002740

    @classmethod
    def cold_code(cls) -> List[int]:
        at, end = cls.COLD_AT, 0x800CB374
        def b(i, t): return 0x48000000 | ((t - (at + 4 * i)) & 0x3FFFFFC)
        return [0x2C030000, 0x4082002C,                    # cmpwi r3,0 ; bne -> end (word 12)
                0x3C808069, 0x8084A18C,                    # r4 = [0x8068A18C] (character manager)
                0x80A40088,                                # r5 = player
                0x80C400A4, 0x7C053000, 0x41820014,        # Chopper? -> end
                0x80C400B0, 0x7C053000, 0x41820008,        # Brook? -> end
                b(11, 0x800CB360),                         # not resistant: mark cold (original path)
                b(12, end)]

    # Aquarium / helm open from the start: the script native GameGetChapter (0x800A0F74) is only used by the Sunny
    # touch scripts 10806 (helm: "can't" message while chapter <= 2, else Next Island menu) and 10807 (Aquarium: only
    # after game clear or chapter > 4). Its chapter read (0x800A0F8C bl 0x800FD7C8) -> li r3,5. Code patch.
    CHAPTER_SITE, CHAPTER_ORIG, CHAPTER_NEW = 0x800A0F8C, 0x4805C83D, 0x38600005

    def patch_aquarium(self) -> None:
        if self.u32(self.CHAPTER_SITE) == self.CHAPTER_ORIG:
            self.w32(self.CHAPTER_SITE, self.CHAPTER_NEW)

    def patch_cold_resistance(self) -> None:
        if self.u32(self.COLD_SITE) == self.COLD_ORIG:
            for i, x in enumerate(self.cold_code()):
                self.w32(self.COLD_AT + i * 4, x)
            self.w32(self.COLD_SITE, 0x48000000 | ((self.COLD_AT - self.COLD_SITE) & 0x3FFFFFC))

    def patch_traps(self) -> None:
        if all(self.u32(a) == orig for a, orig, _ in self.TRAP_SITES):
            for a, _, new in self.TRAP_SITES:
                self.w32(a, new)

    # Fast traps (docs/traps.md): the catch timer set at 0x800416B4/B8 (1,800,000 + rand % 1,200,000 ms) becomes a
    # fixed 600,000 (10 min), and the leave-the-field cut in 0x80047CE4 (-10 min while above 20 min, never below
    # 20 min; both use r5 = 1,200,000 from 0x80047DA0) uses 0 instead, so leaving the trap's field once finishes it.
    FAST_TRAP_SITES = [(0x800416B4, 0x3CA5001B, 0x3CA00009), (0x800416B8, 0x38A57740, 0x38A527C0),
                       (0x80047DA0, 0x38A34F80, 0x38A00000)]

    # "An Idea!" recipe discovery (0x800F5B54, called only from 0x800F6DF8): when an item is obtained, a recipe
    # whose ingredients are all in the bag and whose state lacks 0x04 is discovered with a popup. The client
    # lists recipes itself, so discovery is switched off: the call returns 0xFF ("nothing found"). Key items
    # (Mystery Gadget, Tone Dial...) still set it off with Arts discovery on (user, 2026-10-23), most likely
    # when they arrive before the client re-marks the rows.
    DISCOVERY_CALL, DISCOVERY_ORIG, DISCOVERY_NEW = 0x800F6DF8, 0x4BFFED5D, 0x386000FF

    # The second way in (0.18.2): 0x800F7054(objs, mode, item, ...) mode 3 = "item obtained". Its hard-coded cases
    # replace the old tool when the new one arrives (0x800F6EA4: Bug-Catcher Net 2 -> Broken net 3 goes, Power Vacuum
    # 7 -> Vacuum 8, rods / bag / palette upgrades), then all fall through to the default case 0x800F7874: for key
    # items (0x800F8BD0(item) == 1: Tone Dial, Mystery Gadget...) it discovers every recipe using the item with the
    # popup (ori 5 at 0x800F7914). 0.18.2 skipped the whole of mode 3, which also stopped the tool replacement
    # (user: Broken net kept, no net after crafting it). Now only the default case exits (0x800F7874 -> b 0x800F79F0);
    # the old patch at 0x800F70C8 is undone if it's still in memory.
    ITEM_DISCOVERY, ITEM_DISCOVERY_ORIG, ITEM_DISCOVERY_NEW = 0x800F7874, 0x7F83E378, 0x4800017C
    OLD_ITEM_PATCH, OLD_ITEM_ORIG, OLD_ITEM_NEW = 0x800F70C8, 0x48000100, 0x48000928

    def patch_recipe_discovery(self) -> None:
        if self.u32(self.DISCOVERY_CALL) == self.DISCOVERY_ORIG:
            self.w32(self.DISCOVERY_CALL, self.DISCOVERY_NEW)
        if self.u32(self.OLD_ITEM_PATCH) == self.OLD_ITEM_NEW:
            self.w32(self.OLD_ITEM_PATCH, self.OLD_ITEM_ORIG)
        if self.u32(self.ITEM_DISCOVERY) == self.ITEM_DISCOVERY_ORIG:
            self.w32(self.ITEM_DISCOVERY, self.ITEM_DISCOVERY_NEW)
        # Third way in (0.18.3): 0x800417B8(chara mgr, item) lists the recipe that makes the item and fires the
        # popup (0x800F5CE0). Called by the script natives ItemFlash / ItemFlashOpen (item pick-ups, chests) and
        # the new-game setup. Location chests give the Archipelago Item (86), which is also the result of the
        # placeholder recipes, so opening e.g. the Tone Dial / Mystery Gadget chest "discovered" one of them and the
        # popup crashed on it. Now returns 0 straight away (li r3,0 / blr).
        # Two words, so only at the title screen (apply_patches), never while the game may be running it.

    # Fourth (0.18.4, the actual "An Idea!" from the user's reports): key items like the Tone Dial start an item
    # event (scripts 351-5xx: dialogue, then ItemFlashOpen(IdxToID(n))). The natives ItemFlashOpen (0x800AA850)
    # and ItemEventRunFlash (0x800BE4DC) call 0x80044DFC(chara mgr, item), which starts the "An Idea!" popup task
    # (0x80007B30, callback 0x80044E64) for the recipe that makes the item; for a recipe the client turned into an
    # Archipelago Item recipe it reads a null pointer. Both calls become nops (the dialogue still plays).
    IDEA_CALLS = [(0x800AA8DC, 0x4BF9A521), (0x800BE57C, 0x4BF86881)]

    def patch_idea_popup(self) -> None:
        for a, orig in self.IDEA_CALLS:
            if self.u32(a) == orig:
                self.w32(a, NOP)

    def patch_item_flash(self) -> None:
        if self.u32(self.FLASH_FUNC) == self.FLASH_ORIG and not self.in_game():
            self.w32(self.FLASH_FUNC + 4, 0x4E800020)
            self.w32(self.FLASH_FUNC, 0x38600000)

    FLASH_FUNC, FLASH_ORIG = 0x800417B8, 0x9421FFD0

    def discovery_patch_state(self) -> str:
        return (f"ingredient {self.u32(self.DISCOVERY_CALL) == self.DISCOVERY_NEW}, "
                f"item {self.u32(self.ITEM_DISCOVERY) == self.ITEM_DISCOVERY_NEW}, "
                f"flash {self.u32(self.FLASH_FUNC) == 0x38600000}, "
                f"popup {all(self.u32(a) == NOP for a, _ in self.IDEA_CALLS)}")

    def patch_fast_traps(self) -> None:
        if all(self.u32(a) == orig for a, orig, _ in self.FAST_TRAP_SITES):
            for a, _, new in self.FAST_TRAP_SITES:
                self.w32(a, new)

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
        found: Dict[str, List[int]] = {"enemy": [], "gen_item": []}
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
            i = data.find(b"ALTB")
            while i != -1:      # the generated-items table: 103 rows of 300 bytes at +0x10, Map 10 in row 96
                if i + 16 <= len(data) and struct.unpack_from(">HHHH", data, i + 6) == (GEN_ITEM_ROWS, 0, GEN_ITEM_OFF,
                                                                                          GEN_ITEM_ROW):
                    row = i + GEN_ITEM_OFF + GEN_ITEM_MAP_ROWS[0] * GEN_ITEM_ROW + GEN_ITEM_VACUUM * 12
                    if row + 4 <= len(data) and struct.unpack_from(">I", data, row)[0] in FRAGMENT_ITEMS | set(ORB_ITEMS):
                        found["gen_item"].append(start + i + GEN_ITEM_OFF)
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
            for base in self.scan_cache.get("gen_item", []):
                if self.rd(base - GEN_ITEM_OFF, 4) != b"ALTB":
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
        sc = b"".join(struct.pack(">I", x) for x in status_code())
        if self.rd(STATUS_AT, len(sc)) != sc:
            self.w(STATUS_AT, sc)
        wc = b"".join(struct.pack(">I", x) for x in wardrobe_code())
        if self.rd(WARDROBE_AT, len(wc)) != wc:
            self.w(WARDROBE_AT, wc)
        if self.rd(WARDROBE_ARGS, 48) != wardrobe_args():
            self.w(WARDROBE_ARGS, wardrobe_args())

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

    def game_idle(self) -> bool:
        """Nothing is playing (0.25.2, paced deliveries): in the field, no event / dialogue / menu (manager +0x78 &
        0x8180), camp menu closed, no item-get sequence (player + 0x13A4), and no hook command, give or unlock check
        waiting. Items, crew members and move unlock checks are only handed over after a stretch of this, so their
        events and pop-ups play one at a time (a burst of them made the game drop some, user 2026-11-03)."""
        m = self.chara_mgr()
        p = self.u32(m + 0x88) if m else 0
        if not m or not valid(p) or (self.u32(m + 0x78) & 0x8180) or self.u32(m + 0x30C):
            return False
        if self.rd(p + 0x13A4, 1)[0]:
            return False
        return not (self.rd(CAMP_CMD, 1)[0] or self.rd(GIVE_FLAG, 1)[0] or self.rd(HOOK_FLAG, 1)[0])

    def hook_counter(self) -> int:
        """Bumped by the hook every frame the game runs its field update (not while paused or in a full-screen
        menu)."""
        return self.rd(HOOK_COUNTER, 1)[0]

    def joined(self) -> Set[int]:
        """Straw Hats whose joined flag (manager + 0x1CC + i * 4, bit 0) is set."""
        m = self.chara_mgr()
        return {i for i in range(9) if m and self.u32(m + 0x1CC + i * 4) & 1}

    def capacity(self, list_name: str) -> int:
        o = self._player_items()
        return self.u32(o + LIST_OFFSET[list_name]) if o else 0

    def remove_item(self, item: int) -> int:
        """Clear every bag / palette / Storage slot holding this item; returns how many slots were cleared."""
        slots = self.find_slots(item)
        for a in slots:
            self.w(a, bytes(16))
        return len(slots)

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
        emit(cmpwi(0, 4))
        br(0x41820000, "costume")
        emit(cmpwi(0, 5))
        br(0x41820000, "status")
        emit(cmpwi(0, 6))
        br(0x41820000, "status")
        emit(cmpwi(0, 8))
        br(0x41820000, "wardrobe")
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
        #   4 = Starting Costumes: the script native CharaChangeCostume with no argument (0x800A64B4; r3 = result
        #       slot 0x80002F70 holding the "no value" object 0x8067EE4C, r4 = empty argument 0x80002F68) on the
        #       current character: reloads it when costume +0xC0 != loaded costume +0xC4, else applies style +0xEC.
        lab["costume"] = len(code)
        emit(lis(3, 0x8000)); emit(addi(3, 3, 0x2F70))
        emit(lis(4, 0x8000)); emit(addi(4, 4, 0x2F68))
        blto(0x800A64B4)
        br(0x48000000, "campclear")
        #   5 / 6 = add / remove a status on the current character (status traps, tools/opuc_status_test.py):
        #       0x804CE1A4(player) = status object; 0x804DF60C(obj, id, time) adds, 0x804DFB34(obj, id, 0) removes;
        #       id at 0x80002F74, time at 0x80002F78 (docs/status_effects.md).
        #       The work is in its own routine (STATUS_AT, below the Game Over code) to keep the stub small.
        lab["status"] = len(code)
        emit(0x7FE3FB78)                                   # mr r3, r31 (character manager)
        blto(STATUS_AT)
        br(0x48000000, "campclear")
        #   8 = switch the Sunny's wardrobe touch spots on (routine WARDROBE_AT, FieldGroupEnable 10808 / 10809).
        lab["wardrobe"] = len(code)
        blto(WARDROBE_AT)
        br(0x48000000, "campclear")
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

    # ---- costumes (docs/garment_vision.md) ----
    # Character object +0xC0 costume (0 Unlimited, 1 Thriller Bark), +0xC4 costume currently loaded, +0xEC style.
    def costume_state(self) -> Dict[int, Tuple[int, int]]:
        m = self.chara_mgr()
        out = {}
        if not m:
            return out
        for ci in range(9):
            o = self.u32(m + 0x90 + ci * 4)
            if valid(o):
                out[ci] = (self.u32(o + 0xC0), self.u32(o + 0xEC))
        return out

    def set_costume(self, ci: int, costume: int, style: int) -> bool:
        m = self.chara_mgr()
        o = self.u32(m + 0x90 + ci * 4) if m else 0
        if not valid(o):
            return False
        self.w32(o + 0xC0, costume)
        self.w32(o + 0xEC, style)
        return True

    def player_index(self) -> Optional[int]:
        m = self.chara_mgr()
        if not m:
            return None
        p = self.u32(m + 0x88)
        for ci in range(9):
            if self.u32(m + 0x90 + ci * 4) == p:
                return ci
        return None

    # ---- status traps (docs/status_effects.md) ----
    # A hit with no damage that carries a status, through the current character's pending hit record (processed by
    # the game next frame like an enemy attack, so frozen / paralysis / sleep / stun also get their reaction):
    # player + 0x34 -> damage object -> [+0] inner; record inner + 0x4C (0x34 bytes, +0x00 pending byte); status
    # list at [inner + 0x80] = {u32 count, 12-byte entries {u32 id, u32 power, u32 time ms}}.
    def _hit_record(self) -> Optional[Tuple[int, int]]:
        m = self.chara_mgr()
        p = self.u32(m + 0x88) if m else 0
        d = self.u32(p + 0x34) if valid(p) else 0
        inner = self.u32(d) if valid(d) else 0
        lst = self.u32(inner + 0x80) if valid(inner) else 0
        return (inner + 0x4C, lst) if valid(lst) else None

    def hit_pending(self) -> bool:
        r = self._hit_record()
        return bool(r) and self.rd(r[0], 1)[0] != 0

    def trap_hit(self, status: int, ms: int = 5000, power: int = 100) -> bool:
        r = self._hit_record()
        if not r or self.rd(r[0], 1)[0]:
            return False                                   # no character, or a hit is already pending
        rec, lst = r
        self.w(lst, struct.pack(">IIII", 1, status, power, ms))
        self.w(rec + 1, bytes(0x33))                       # flags, damage 0, reaction 0, direction 0
        self.w32(rec + 0x34, lst)
        self.w(rec, b"\x01")                              # pending: the game processes it next frame
        return True

    def death_hit(self) -> bool:
        """Death Link received: a hit through the pending hit record with 9999 HP damage (+0x08 s16) at scale 1.0
        (+0x30 f32; HP -= damage * scale, 0x8012E700, clamped at 0), so the game's own fall / next-crew-member /
        Game Over handling plays. Trap hits leave the scale at 0, which is why they do no damage."""
        r = self._hit_record()
        if not r or self.rd(r[0], 1)[0]:
            return False
        rec, lst = r
        self.w(lst, struct.pack(">I", 0))                  # no statuses
        body = bytearray(0x33)
        struct.pack_into(">h", body, 0x08 - 1, 9999)       # +0x08 HP damage
        struct.pack_into(">f", body, 0x30 - 1, 1.0)        # +0x30 damage scale
        self.w(rec + 1, bytes(body))
        self.w32(rec + 0x34, lst)
        self.w(rec, b"\x01")
        return True

    def hp(self, obj: int) -> Optional[Tuple[int, int]]:
        """(current, max) HP of a character object: gauge = [inner + 0x40] with inner = [[obj + 0x34]] (the damage
        object that also holds the pending hit record; 0x8012EFFC); current = [[gauge]] (0x804D8DCC), max =
        [[gauge + 4]] (0x804D8B00)."""
        d = self.u32(obj + 0x34) if valid(obj) else 0
        inner = self.u32(d) if valid(d) else 0
        gauge = self.u32(inner + 0x40) if valid(inner) else 0
        if not valid(gauge):
            return None
        a, b = self.u32(gauge), self.u32(gauge + 4)
        if not (valid(a) and valid(b)):
            return None
        return self.u32(a), self.u32(b)

    def crew_hp(self) -> Dict[int, Tuple[int, int]]:
        m = self.chara_mgr()
        out: Dict[int, Tuple[int, int]] = {}
        for ci in range(9 if m else 0):
            h = self.hp(self.u32(m + 0x90 + ci * 4))
            if h and 0 < h[1] < 100000:
                out[ci] = h
        return out

    def player_obj(self) -> int:
        m = self.chara_mgr()
        p = self.u32(m + 0x88) if m else 0
        return p if valid(p) else 0

    def player_hp(self) -> Optional[Tuple[int, int]]:
        p = self.player_obj()
        return self.hp(p) if p else None

    def fallen(self) -> Set[int]:
        """Straw Hats (character index) that fell into the abyss / deep water: [obj + 0x9C] & 0x01000000 (user test
        2026-10-28: set by a fall, which only costs some HP; it is not death)."""
        m = self.chara_mgr()
        out: Set[int] = set()
        if not m:
            return out
        for ci in range(9):
            o = self.u32(m + 0x90 + ci * 4)
            if valid(o) and self.u32(o + 0x9C) & 0x01000000:
                out.add(ci)
        return out

    def can_trap(self) -> bool:
        """A trap may hit now: in the field, no event / menu (manager +0x78 & 0x8180), camp menu closed."""
        m = self.chara_mgr()
        p = self.u32(m + 0x88) if m else 0
        if not m or not valid(p) or (self.u32(m + 0x78) & 0x8180) or self.u32(m + 0x30C):
            return False
        # Not during an item-get sequence (net catch result, chara_digup.cpp: player + 0x13A4 set by 0x800317D8
        # until the result window closes); a trap there softlocked the game (user, 2026-10-28).
        if self.rd(p + 0x13A4, 1)[0]:
            return False
        # Not while the Bug-Catcher Net or a Fishing Rod is out (catch / fishing animations, user's idea).
        held = self.held_tool()
        return held not in TRAP_BLOCKING_TOOLS

    def held_tool(self) -> Optional[int]:
        """Item id of the tool the current character has out, None if none (0x8006B654: player + 0x16C4 = the tool
        object while one is out). The held item (0x8006B630): palette S = [player + 0x16C0], slot = [S + 0x14] +
        3 * [S + 0x10], entry = [[S + 8] + 8] + slot * 16 = {u32 item id, u8 valid} (0x800F3DC0 / 0x800F89B4 turn the
        id into a row pointer). -1 if a tool is out but its item can't be read."""
        m = self.chara_mgr()
        p = self.u32(m + 0x88) if m else 0
        if not valid(p) or self.u32(p + 0x16C4) == 0:
            return None
        s = self.u32(p + 0x16C0)
        lst = self.u32(s + 8) if valid(s) else 0
        arr = self.u32(lst + 8) if valid(lst) else 0
        if not valid(arr):
            return -1
        slot = (self.u32(s + 0x14) + 3 * self.u32(s + 0x10)) & 0xFFFF
        e = arr + slot * 16
        item = self.u32(e)
        if not self.rd(e + 4, 1)[0] or not 0 < item < 0x200:
            return -1
        return item

    def field_id(self) -> Optional[int]:
        f = self.u32(FIELD_MGR_PTR)
        return self.u32(f + 0x20) if valid(f) else None

    def on_sunny(self) -> Optional[bool]:
        """True on the Thousand Sunny, False on an island, None if the field can't be read."""
        fid = self.field_id()
        return None if fid is None else fid == SUNNY_FIELD

    def request_status(self, status: int, add: bool = True, time: int = 625) -> bool:
        """Ask the hook to add (or remove) a status on the current character (hook command 5 / 6)."""
        if self.rd(CAMP_CMD, 1)[0] or not self.hook_active():
            return False
        self.w(0x80002F74, struct.pack(">II", status, time))
        self.w(CAMP_CMD, b"\x05" if add else b"\x06")
        return True

    def request_wardrobe(self) -> bool:
        """Ask the hook to switch the wardrobe touch spots on (hook command 8; only call on the Sunny)."""
        if self.rd(CAMP_CMD, 1)[0] or not self.hook_active():
            return False
        self.w(CAMP_CMD, b"\x08")
        return True

    def refresh_costume(self) -> bool:
        """Ask the hook to run CharaChangeCostume on the current character (reload with +0xC0 / +0xEC)."""
        if self.rd(CAMP_CMD, 1)[0] or not self.hook_active():
            return False
        self.w(0x80002F68, bytes(8))
        self.w32(0x80002F70, 0x8067EE4C)
        self.w(CAMP_CMD, b"\x04")
        return True

    # "Walk the Sunny" (camp menu id 8) -> the wardrobe script 10809 (Costume Change, like at the wardrobe) once the
    # Garment Box has been received: screen table entry 8 (0x8059E870 + 32) -> routine at 0x80002740 that queues
    # the script through the hook (0x80002F60 = 10809, 0x80002F07 = 3) and then does the original "no screen" case.
    WALK_ENTRY, WALK_ORIG, WALK_AT = 0x8059E890, 0x801AFF24, 0x80002740
    WALK_CODE = [0x3CA08000, 0x38C02A39, 0x90C52F60, 0x38C00003, 0x98C52F07, 0x481AD7D0]

    def set_walk_costumes(self, on: bool) -> None:
        cur = self.u32(self.WALK_ENTRY)
        if on and cur == self.WALK_ORIG:
            for i, x in enumerate(self.WALK_CODE):
                self.w32(self.WALK_AT + i * 4, x)
            self.w32(self.WALK_ENTRY, self.WALK_AT)
        elif not on and cur == self.WALK_AT:
            self.w32(self.WALK_ENTRY, self.WALK_ORIG)

    # Plant drops (fobj_gen_item_table rows 0-14 Bitter Grass / Medicinal Herbs bushes, 39-46 Nectar flowers). The
    # column is the hit's attack type (attribute -> column table 0x80506B10): 11 = slash (bamboo only drops in 11 /
    # 17), 17 = Pickaxe, 22 = Vacuum Cleaner; 10 / 12 / 16 / 18 / 19 = the other hits; 14 / 20 / 23 = Ashes (fire).
    PLANT_ITEMS = {34: "Bitter Grass", 31: "Medicinal Herbs", 37: "Nectar"}
    PLANT_ROWS = list(range(0, 15)) + list(range(39, 47))
    PLANT_NORMAL_COLS, PLANT_SLASH_COL, PLANT_VACUUM_COL = (10, 12, 16, 17, 18, 19), 11, 22
    # (normal, slash, vacuum) chance %: Better Plant Drop Rates (user, 0.23.3)
    PLANT_RATES = {34: (25.0, 50.0, 75.0), 31: (60.0, 80.0, 100.0), 37: (25.0, 50.0, 75.0)}

    def set_plant_drops(self) -> None:
        for base in self.scan_cache.get("gen_item", []):
            if self.rd(base - GEN_ITEM_OFF, 4) != b"ALTB":
                continue
            for r in self.PLANT_ROWS:
                row = base + r * GEN_ITEM_ROW
                data = self.rd(row, GEN_ITEM_ROW)
                for cols, k in ((self.PLANT_NORMAL_COLS, 0), ((self.PLANT_SLASH_COL,), 1),
                                ((self.PLANT_VACUUM_COL,), 2)):
                    for c in cols:
                        item, _n, chance = struct.unpack_from(">IIf", data, c * 12)
                        want = self.PLANT_RATES.get(item, (None,) * 3)[k]
                        if want is not None and chance != want:
                            self.w(row + c * 12 + 8, struct.pack(">f", want))

    def set_blue_orb_spot(self, item: int) -> None:
        """Every Blue Orb dig spot (fobj_param row 96 land_shineA_type2 -> item row 71, Pickaxe columns 14 / 17 =
        Blue Orb; all on the Wooded Isle, the one by the Sunny is the repeatable one, user 2026-10-28) gives this
        item instead (70 = Pure Iron Ore; 81 = vanilla)."""
        for base in self.scan_cache.get("gen_item", []):
            if self.rd(base - GEN_ITEM_OFF, 4) != b"ALTB":
                continue
            for col in (14, 17):
                a = base + 71 * GEN_ITEM_ROW + col * 12
                if self.u32(a) in (81, 70) and self.u32(a) != item:
                    self.w32(a, item)

    # Plain-ground Pickaxe digs (0x800CF340): 12 ground types x {u32 item, f32 chance} x 2 at 0x805065C8 (main.dol
    # data, vanilla 5% each: Handy Rock + Clay, snow / ice Ice Shard x2). A dig only counts 20 units from the last.
    GROUND_DIG_TABLE, GROUND_DIG_ROWS = 0x805065C8, 12
    GROUND_DIG_CHANCES = (0.05, 0.25)

    def set_ground_dig_chance(self, chance: float) -> None:
        """Higher Chance of Random Dig Items: every ground dig item chance -> chance (only known values are touched)."""
        want = struct.pack(">f", chance)
        known = [struct.pack(">f", c) for c in self.GROUND_DIG_CHANCES]
        data = self.rd(self.GROUND_DIG_TABLE, self.GROUND_DIG_ROWS * 16)
        for r in range(self.GROUND_DIG_ROWS):
            for k in (0, 1):
                o = r * 16 + k * 8 + 4
                cur = data[o:o + 4]
                if cur != want and cur in known:
                    self.w(self.GROUND_DIG_TABLE + o, want)

    # Creature drops (item/insect_prm.bin, 20 x 152 bytes at [item manager 0x805E91E0 + 0x24], count at + 0x20):
    # +0x08 u16 drop chance in 1/100 % (rolled only when the creature is caught with the net, 0x8011F1A0).
    INSECT_MGR, INSECT_REC = 0x805E91E0, 152
    INSECT_VANILLA = [5000, 5000, 10000, 10000, 6000, 2500, 6000, 10000, 10000, 10000,
                      10000, 3000, 3000, 4000, 10000, 10000, 5000, 10000, 6000, 5000]

    def set_creature_drops(self, guaranteed: bool) -> None:
        """Guaranteed Creature Drops: every net drop chance 100% (off: the vanilla chances)."""
        n, tab = self.u32(self.INSECT_MGR + 0x20), self.u32(self.INSECT_MGR + 0x24)
        if n != len(self.INSECT_VANILLA) or not valid(tab):
            return
        for i, van in enumerate(self.INSECT_VANILLA):
            a = tab + i * self.INSECT_REC + 8
            cur, want = struct.unpack(">H", self.rd(a, 2))[0], (10000 if guaranteed else van)
            if cur != want and cur in (van, 10000):
                self.w(a, struct.pack(">H", want))

    def strip_fragment_drops(self, vacuum_orbs: List[int]) -> None:
        """Treasure map fragment drops (kills, steals, Break Rush) become Gold Orbs with the same count and
        chance (0.18.0, user 2026-10-23; before: no drop). Orbs aren't one-of-a-kind items like the fragments
        (flagFlagOnlyItem 0, carry up to 10), so they can be farmed. Checked every poll: the enemy table is
        reloaded with stage changes, sometimes at the same address.
        Also the Thousand Sunny's dust spots (field/fobj_gen_item_table.atb rows 96-100, Vacuum column 22 =
        Map 10 fragments 1-5) give the seed's Orbs instead."""
        for base, nrows, header in self.scan_cache.get("enemy", []):
            if self.rd(header, 4) != b"ALTB" or not 0 < nrows <= 512:
                continue
            data = self.rd(base, nrows * 40)
            for r in range(nrows):
                for k in range(2):
                    if struct.unpack_from(">I", data, r * 40 + 24 + 4 * k)[0] in FRAGMENT_ITEMS:
                        self.w32(base + r * 40 + 24 + 4 * k, GOLD_ORB)
        for base in self.scan_cache.get("gen_item", []):
            if self.rd(base - GEN_ITEM_OFF, 4) != b"ALTB":
                continue
            for i, row in enumerate(GEN_ITEM_MAP_ROWS):
                a = base + row * GEN_ITEM_ROW + GEN_ITEM_VACUUM * 12
                cur = self.u32(a)
                if cur in FRAGMENT_ITEMS and i < len(vacuum_orbs):
                    self.w32(a, vacuum_orbs[i])

    def set_gunpowder_drops(self, chance: int) -> None:
        """Easier Gunpowder Drops (0.24.0): the gunners' common drop chance (u16 item_dorp_ratio<0> at row + 0x24,
        percent) where the common drop is Gunpowder. Kill drops and Nami's steals both roll it; Cat Burglar multiplies
        the steal roll by steal_scale / 100 (300 / 400 / 500 / 550 / 600), user-tested 2026-11-02."""
        want = struct.pack(">H", max(0, min(100, chance)))
        for base, nrows, header in self.scan_cache.get("enemy", []):
            if self.rd(header, 4) != b"ALTB" or not 0 < nrows <= 512:
                continue
            data = self.rd(base, nrows * 40)
            for r in range(nrows):
                if struct.unpack_from(">I", data, r * 40 + 0x18)[0] == GUNPOWDER and data[r * 40 + 0x24:r * 40 + 0x26] != want:
                    self.w(base + r * 40 + 0x24, want)

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

    # Database (encyclopedia) books: [ITEM_MGR_PTR] + 0x16C / + 0x170 (book types 0 / 1, found by item param
    # +285). Book: +0 type, +4 entry count, +8 -> entries of 12 bytes: +0 u32 best size (0 = never caught), +4 u32
    # item id, +8 u16 flags (|= 0xA000 when a record is set, 0x800F3824). Saved as ItemPicb0 / ItemPicb1.
    def database_caught(self) -> Optional[Set[int]]:
        m = self.u32(ITEM_MGR_PTR)
        if not valid(m):
            return None
        out: Set[int] = set()
        for off in (0x16C, 0x170):
            b = self.u32(m + off)
            if not valid(b):
                return None
            n, e = self.u32(b + 4), self.u32(b + 8)
            if not valid(e) or not 0 < n <= 64:
                return None
            raw = self.rd(e, n * 12)
            for i in range(n):
                size, item, flags = struct.unpack_from(">IIH", raw, i * 12)
                if size or flags & 0x2000:
                    out.add(item)
        return out

    # The Database menu entry (camp menu case 5 -> 0x801F47C4(4)) needs chapter > 3 (vanilla: after Gecko Moria,
    # with the girls' room). "ble" after the chapter compare becomes a nop: open from the start.
    DATABASE_SITE, DATABASE_ORIG = 0x801F4858, 0x4081002C

    def patch_database_menu(self) -> None:
        if self.u32(self.DATABASE_SITE) == self.DATABASE_ORIG:
            self.w32(self.DATABASE_SITE, NOP)

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
        """(shrine id, row address, state byte address). Rows per zone from event/epoint/zone0-5.bin: Sunny 1,
        Wooded Isle 7, Gorge Isle 8, Island 3 6, Island 4 4, Central Isle 1. (0.17.x only read zones 0-1, so the
        Gorge Isle shrines / build sites were never locked or checked; user 2026-10-23.)"""
        m = self.u32(SHRINE_MGR_PTR)
        if not valid(m):
            return
        for z, rows in enumerate((1, 7, 8, 6, 4, 1)):
            t = self.u32(m + 0x18 + z * 4)
            if not valid(t):
                continue
            for r in range(rows):
                a = t + r * 0x38
                yield self.u32(a), a, m + 0x48 + z * 0x80 + r

    def set_shrine_locks(self, unlocked: Set[int]) -> None:
        for sid, row, _ in self._shrines():
            if sid not in SHRINE_COSTS:
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

    def save_owner(self) -> Optional[str]:
        """Whose save is loaded: "this" (our marker + this seed's tag), "other" (marker of another seed / slot),
        "fresh" (no marker, no progress: a new game), "foreign" (no marker but progress: a save never played with
        this client, e.g. a vanilla save). None while the data isn't there."""
        d = self._section(DELIVERED_SECTION)
        if not d:
            return None
        v = self.u32(d + DELIVERED_OFFSET)
        if v >> 16 == DELIVERED_MARK:
            return "this" if self.u32(d + DELIVERED_OFFSET - 4) == self.seed_tag else "other"
        return "foreign" if self.script_flags([11011, 11251, 11990]) else "fresh"

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

    def fight_clears(self, start: int) -> List[int]:
        """Clear scripts of a fight that haven't run yet (Kuro / Krieg share one start script)."""
        clears = [c for st, c in FIGHTS if st == start]
        done = self.script_flags(clears)
        return [c for c in clears if c not in done]

    def func_enabled(self, n: int) -> bool:
        d = self._section("EventFuncEnableFlag")
        return bool(d) and bool(self.u32(d + (n >> 5) * 4) >> (n & 31) & 1)

    def debug_state(self) -> str:
        m = self.chara_mgr()
        flags = self.script_flags([n for pair in FIGHTS for n in pair])
        fights = " ".join(f"{a}:{int(a in flags)}/{b}:{int(b in flags)}/arm{int(self.func_enabled(b))}"
                          for a, b in FIGHTS if a < 13000) or "none"
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

    def func_flags(self, flags: Iterable[int]) -> Set[int]:
        """EventFuncEndFlag bits (field functions that have fired; the script itself may still be running)."""
        return self.script_flags(flags, "EventFuncEndFlag")

    def script_flags(self, flags: Iterable[int], section: str = "EventScriptEndFlag") -> Set[int]:
        d = self._section(section)
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
    # Item table rows (0x224 bytes, item_src.<lang>.atb): +0x125..+0x12A Energy given to Gabri, one byte each
    # (element0-5; element5 = Gold: Gold Orb 100). Iron Scrap (73) = 15 / 0 / 0 / 0 / 25 / 0.
    IRON_SCRAP, ELEMENT_GOLD = 73, 0x12A

    def set_iron_scrap_gold(self, on: bool) -> None:
        t = self.u32(ITEM_NAMES_PTR)
        if not valid(t):
            return
        row = t + self.IRON_SCRAP * 0x224
        if struct.unpack(">H", self.rd(row + 0x42, 2))[0] != self.IRON_SCRAP:
            return
        want = 10 if on else 0
        if self.rd(row + self.ELEMENT_GOLD, 1)[0] != want:
            self.w(row + self.ELEMENT_GOLD, bytes([want]))

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

    # Fishing data (item manager, static at 0x805E91E0: +0x64 -> field/fishp.bin). 0x5C-byte spot records: +0x00
    # island, +0x04 spot, +0x08 5 x {u32 fish, u16 weight, u16}. A bite picks among the fish whose distance window
    # holds the lure, weighted (0x80036254), so equal weights give equal chances (Equalise Fish Rates, 0.23.0).
    FISH_MGR, FISHP_OFF, FISHP_REC, FISHP_MAX = 0x805E91E0, 0x64, 0x5C, 8

    def set_fish_rates(self, weight: int = 100) -> None:
        p = self.u32(self.FISH_MGR + self.FISHP_OFF)
        if not valid(p):
            return
        # 8 spot records; what follows in the buffer is other data (0.23.0 wrote into it: the records after the
        # 8th don't start with 0, which held the game on New Game, user). Only records whose island is a real
        # island id (global ids 0x4C9E-0x4CA2 = islands 0-4) are touched, and only weights that look like weights.
        for r in range(self.FISHP_MAX):
            rec = self.rd(p + r * self.FISHP_REC, self.FISHP_REC)
            if not 0x4C9E <= struct.unpack_from(">I", rec, 0)[0] <= 0x4CA2:
                break
            for k in range(5):
                fish, w = struct.unpack_from(">IH", rec, 8 + 8 * k)
                if fish and 0 < w <= 1000 and w != weight:
                    self.w(p + r * self.FISHP_REC + 8 + 8 * k + 4, struct.pack(">H", weight))

    # Quick Recipes (0.23.0): every recipe ingredient that is a creature (97-116), a fish (117-136) or a Sea King part
    # (137-139) needs just 1. Recipe rows: +4 4 x {u16 ingredient, u8 count, u8 flag}.
    QUICK_ITEMS = range(97, 140)

    # Max hold count (0.25.15, user test): item/item_src.en.atb, loaded at [item manager 0x805E91E0 + 8], 250 rows of
    # 548 bytes (+0x40 u32 id, +286 u8 maxHave, read through 0x800F8B84 / 0x800F8BA0 by every bag / palette / Storage
    # / give path). Vanilla: creatures 5; medicine, Traps, Kuwagata, Orbs, food 10; materials 20; powders, Bitter
    # Grass 30; Flamethrowers / Batteries / Bombs 50; 綿毛 already 99. Every stackable row (maxHave > 1) -> 99;
    # one-per-slot items (tools, key items, fish, maps; 0 or 1) are left alone. The count is a byte everywhere (slot
    # +4, save data), and 99 already exists in vanilla, so the menus show it.
    ITEM_TABLE_REF, ITEM_ROW, ITEM_ROWS, MAX_HAVE_OFF = 0x805E91E0 + 8, 548, 250, 286

    #
    # Stack craftables (0.25.17): the game crafts / hands out "stack craftable" items (0x800F626C: maxHave > 1 and
    # type 3, or Traps) as a whole stack of maxHave - crafting at 0x801CFF94 (bl 0x800F8BA0, id in r3) and the
    # item-get at 0x800448FC (bl 0x800F8B84, r3 -> handle, [r3] = row). With 99 that made 99 Traps / Bombs /
    # powders (user). Both calls go to CRAFT_AT, which returns the row's spare byte +311 (align00, 0 in every row)
    # or maxHave if that's 0. The row's other spare byte +310 keeps the vanilla maxHave (written once, before it's
    # raised), and +311 = vanilla (Stack Craftables Make Max Copies off) or 0 (on -> the 99 stack).
    VANILLA_OFF, CRAFT_OFF = 310, 311
    CRAFT_SITES = ((0x801CFF94, 0x800F8BA0, 2), (0x800448FC, 0x800F8B84, 0))   # site, original target, entry word
    CRAFT_AT = 0x80002FC4                                                      # 11 words, ends 0x80002FF0

    @classmethod
    def craft_code(cls) -> List[int]:
        return [0x81830000,                     # 0  handle entry: lwz r12, 0(r3) (row)
                0x48000014,                     # 1  b 6
                0x3D60805F, 0x816B91E8,         # 2-3 id entry: r11 = [0x805E91E8] (item table)
                0x1D830224, 0x7D8B6214,         # 4-5 r12 = r11 + id * 548
                0x886C0000 | cls.CRAFT_OFF,     # 6  lbz r3, 311(r12)
                0x2C030000, 0x4C820020,         # 7-8 not 0 -> return it
                0x886C0000 | cls.MAX_HAVE_OFF,  # 9  lbz r3, 286(r12)
                0x4E800020]                     # 10

    def patch_craft_copies(self) -> None:
        if all(self.u32(a) == bl(a, t) for a, t, _ in self.CRAFT_SITES):
            for i, x in enumerate(self.craft_code()):
                self.w32(self.CRAFT_AT + i * 4, x)
            for a, _t, entry in self.CRAFT_SITES:
                self.w32(a, bl(a, self.CRAFT_AT + 4 * entry))

    def set_max_stacks(self, value: int = 99, craft_max: bool = False) -> None:
        base = self.u32(self.ITEM_TABLE_REF)
        if not valid(base):
            return
        data = self.rd(base, self.ITEM_ROW * self.ITEM_ROWS)
        if struct.unpack_from(">I", data, self.ITEM_ROW * 40 + 0x40)[0] != 40:      # row 40 = Wood (id 40)
            return
        for r in range(self.ITEM_ROWS):
            row = r * self.ITEM_ROW
            have, vanilla = data[row + self.MAX_HAVE_OFF], data[row + self.VANILLA_OFF]
            if 1 < have < value:
                if not vanilla:
                    vanilla = have
                    self.w(base + row + self.VANILLA_OFF, bytes([vanilla]))
                self.w(base + row + self.MAX_HAVE_OFF, bytes([value]))
            craft = 0 if craft_max else vanilla
            if data[row + self.CRAFT_OFF] != craft:
                self.w(base + row + self.CRAFT_OFF, bytes([craft]))

    def set_quick_recipes(self) -> None:
        for room in ("workshop", "kitchen", "pharmacy"):
            p = self._recipe_row(room, 0)
            if not p:
                continue
            rows = self.rd(p, 252 * 32)
            for r in range(32):
                for k in range(4):
                    o = r * 252 + 4 + 4 * k
                    item, n = struct.unpack_from(">HB", rows, o)
                    if item in self.QUICK_ITEMS and n > 1:
                        self.w(p + o + 2, b"\x01")

    def _recipe_state_obj(self, room: str) -> Optional[int]:
        m = self.u32(ITEM_MGR_PTR)
        if not valid(m):
            return None
        o = self.u32(m + ROOM_INDEX[room] * 4)
        return o if valid(o) else None

    def _recipe_row(self, room: str, row: int) -> Optional[int]:
        p = self.u32(RECIPE_ROWS + ROOM_INDEX[room] * 4)
        return p + row * 252 if valid(p) else None

    def clear_idea_callbacks(self) -> None:
        """The "An Idea!" popup is a callback in each recipe object (+0x34 function, +0x38 argument), called only
        when it isn't null (0x800F5D5C, 0x800F7148, ...) after a recipe gets listed. There are several discovery
        paths (item obtained, ingredient check, script natives ItemFlash / ItemFlashOpen -> 0x800417B8), so the
        callback itself is cleared (0.18.3, user: Tone Dial / Mystery Gadget still crashed with 0.18.2). Data,
        not code: works at any time. The client re-applies the Art veil on the next pass."""
        m = self.u32(ITEM_MGR_PTR)
        if not valid(m):
            return
        for i in range(4):
            o = self.u32(m + i * 4)
            if valid(o) and valid(self.u32(o + 0x28)) and self.u32(o + 0x34):
                self.w32(o + 0x34, 0)

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
                        new[r] = (new[r] | 0x04) & ~0x01 & 0xFF   # not listed yet (listed once it's unhidden)
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

    def set_islands(self, open_: Dict[int, bool]) -> None:
        """Next Island menu: island n (1 Wooded .. 5 Central) selectable; byte 0 = the menu entry."""
        if self.u32(ISLAND_FUNC) >> 26 != 18:
            return
        t = bytearray(8)
        for n, ok in open_.items():
            t[n] = 1 if ok else 0
        t[0] = 1 if any(t[n] for n in range(2, 6)) else 0
        if self.rd(ISLAND_TABLE, 8) != bytes(t):
            self.w(ISLAND_TABLE, bytes(t))

    def game_cleared(self) -> bool:
        """GameIsClear: [0x8068A298] + 6, set by GameClear() at the end of the final boss (script 15030)."""
        ro = self.u32(RESET_OBJ_PTR)
        return valid(ro) and self.rd(ro + 6, 1)[0] != 0

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
