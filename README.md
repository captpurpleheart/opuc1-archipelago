# One Piece Unlimited Cruise 1 - Archipelago

An [Archipelago](https://archipelago.gg) world and Dolphin client for **One Piece Unlimited Cruise Part 1: The
Treasure Beneath the Waves** (Wii, PAL `ROUPAF`).

> **Alpha.** This release covers the **Thousand Sunny, Island 1 (Wooded Isle), Island 2 (Gorge Isle) and the final
> island (Central Isle)**. Islands 3 and 4 are planned. Please report bugs!
>
> Latest: **0.19.7** (0.19.6 "The Gorge Isle Scope" + fixes) - see [CHANGELOG.md](CHANGELOG.md).

## What's randomized

**Locations** (about 400 with the default options): move level-ups (and optionally super / co-op move
level-ups), story events, ambushes and bosses (including the secret boss), treasure chests and map dig spots,
Stone Monuments, Gabri Shrines and Build Sites, the first craft of each Development / Cooking / Compounding
recipe, and (optionally) catching each fish and creature for the first time.

**Goal** (option): "God" Eneru, Gecko Moria, or the Doom Guardian on Central Isle (default). The Gorge Isle and
Central Isle are unlocked by Archipelago items, so they can be reached much earlier than in the base game.

**Items:** the Straw Hats (you start with one), moves, co-op moves and abilities (including the Arts), tools and
key items (Pickaxe, Bug-Catcher Net, Vacuum Cleaner, Fishing Rod and upgrades, etc), Usopp's Workshop / Sanji's
Kitchen / Chopper's Pharmacy, the islands, Gabri levels, shrine and build site access, "The Final Door",
treasure map fragments, and filler (food and medicine, also in packages of 3 and 5, Kuwagata and Orbs).

Other quality-of-life changes the client makes:
- No Game Over: the party is revived instead. Boss fights restart, ambushes carry on, and elsewhere you're
  taken back to the Thousand Sunny.
- Received items arrive through the game's own "obtained" messages. The **Armed Items** tab shows anything the
  client is still holding back and why (Pickaxe until you reach the Thousand Sunny, a full bag, YAML option settings).
- Recipe descriptions show which item a recipe's location holds (optional).
- The Database menu is open from the start (fish / creature checks are read from it).
- Treasure map drops from enemies are Gold Orbs instead; the Sunny's dust piles give Orbs.
- No "An Idea!" recipe popups (the client shows recipes itself).
- Optional: traps that never expire and catch faster, Iron Scrap giving Gold Energy, and the repeatable dig spot
  by the Thousand Sunny giving Pure Iron Ore.

## Requirements

- Archipelago **0.6.0** or newer
- Dolphin
- One Piece Unlimited Cruise Part 1, **European (PAL) version, game ID `ROUPAF`**, unmodified. Any disc format
  works (ISO, WBFS, RVZ, etc). The Japanese versions are **not** supported.
- The `dolphin-memory-engine` Python package, should be apart of Archipelago by default, but just in case.
- Optional: [Universal Tracker](https://github.com/FarisTheAncient/Archipelago/releases) - the client uses it
  automatically when installed.

## Setup

1. Download `opuc1.apworld` and `OPUC1.yaml` from the [Releases](../../releases) page.
2. Double-click `opuc1.apworld` (or put it in Archipelago's `custom_worlds` folder).
3. Edit `OPUC1.yaml` (every option is explained in it) and generate as usual.
4. In Dolphin, turn **cheats off** (Config > General > Enable Cheats). The client needs that memory.
5. Start the game and stay **at the title screen**.
6. Open **One Piece Unlimited Cruise 1 Client** from the Archipelago Launcher and connect.
   Several patches only work if they go in before the game first uses that code, so connect *before* loading a
   save. If a save was already loaded when the client connected, it sends no checks and gives no items for it:
   reset to the title screen and load again.
7. Start a new game (or load a save from this seed) and keep the client open while you play.

If the client reports that dolphin-memory-engine is missing, install it into the Python that runs Archipelago:
`pip install dolphin-memory-engine`.

## Options

Grouped as in the YAML:
- **General** - starting character, goal.
- **Item Options** - combined rod/line upgrades, how many rod upgrade items, treasure maps needing every
  fragment, no diminishing returns for food, recipe discovery through Arts, recipe descriptions that spoil
  locations, Iron Scrap giving Gold Energy, the Blue Orb dig spot giving Pure Iron Ore, Bag & Palette upgrade
  item type.
- **Move & Skill Options** - faster move EXP, Super Move Locations (off / on / unimportant), Cat Burglar and
  Light Weight item type.
- **Fishing & Bug-Catching Options** - Fishsanity, Creaturesanity, how many of each, Sea Kings important, Traps
  Never Expire, Fast Traps.
- **Thousand Sunny & Crew Gating Options** - what opens each crafting room, Arts requiring their Straw Hat, Nami for
  treasure maps, Robin for Stone Monuments, Franky for Build Sites.
- **Filler Weighting Options** - quality / bundle weighting and the food / medicine / other mix.

## Reporting bugs

Please include what happened and the output of the client's `/status` command (it starts with the
client version).

## Building from source

`python build_apworld.py` packs the `opuc1` folder into `opuc1.apworld`.
