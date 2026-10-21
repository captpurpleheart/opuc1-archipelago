# One Piece Unlimited Cruise 1 - Archipelago

An [Archipelago](https://archipelago.gg) world and Dolphin client for **One Piece Unlimited Cruise Part 1: The
Treasure Beneath the Waves** (Wii, PAL `ROUPAF`).

> **Alpha.** This release covers the **Thousand Sunny and Island 1 (Wooded Isle)** only. The goal is to defeat
> the Wooded Isle boss. Later islands are planned. Please report bugs!

## What's randomized

**Locations** (about 340 with the default options): move and co-op move level-ups, story events, ambushes and
bosses (including the secret boss), treasure chests and map dig spots, Stone Monuments, Gabri Shrines and Build
Sites, the first craft of each Development / Cooking / Compounding recipe, and (optionally) catching each fish
and creature for the first time.

**Items:** the Straw Hats (you start with one), moves, co-op moves and abilities (including the Arts), tools and
key items (Pickaxe, Bug-Catcher Net, Vacuum Cleaner, Fishing Rod and upgrades, ...), Usopp's Workshop / Sanji's
Kitchen / Chopper's Pharmacy, Gabri levels, shrine and build site access, treasure map fragments, and filler
(food and medicine, also in packages of 3 and 5, Kuwagata and Orbs).

Other quality-of-life changes the client makes:
- No Game Over: the party is revived instead. Boss fights restart, ambushes carry on, and elsewhere you're
  taken back to the Thousand Sunny.
- Received items arrive through the game's own "obtained" messages. The **Armed Items** tab shows anything the
  client is still holding back and why (Pickaxe until you reach the Thousand Sunny, a full bag, ...).
- Recipe descriptions show which item a recipe's location holds (optional).

## Requirements

- Archipelago **0.6.0** or newer
- Dolphin
- One Piece Unlimited Cruise Part 1, **European (PAL) version, game ID `ROUPAF`**, unmodified. Any disc format
  works (ISO, WBFS, RVZ, ...). The US and Japanese versions are **not** supported.
- The `dolphin-memory-engine` Python package
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
   save. The client warns you if it was started too late.
7. Start a new game (or load a save from this seed) and keep the client open while you play.

If the client reports that dolphin-memory-engine is missing, install it into the Python that runs Archipelago:
`pip install dolphin-memory-engine`.

## Options

Grouped as in the YAML:
- **Item Settings** - combined rod/line upgrades, how many rod upgrade items, treasure maps needing every
  fragment, no diminishing returns for food, recipe discovery through Arts, recipe descriptions that spoil
  locations.
- **Moves** - faster move EXP, and whether move / super move level-ups can hold progression.
- **Fishing & Bug-Catching** - Fishsanity, Creaturesanity, how many of each, Sea Kings important.
- **Thousand Sunny & Crew Gating Options** - what opens each crafting room, Arts requiring their Straw Hat, Nami for
  treasure maps, Robin for Stone Monuments, Franky for Build Sites.
- **Filler Weighting Options** - quality / bundle weighting and the food / medicine / other mix.

## Reporting bugs

Please include what happened and the output of the client's `/status` command (it starts with the
client version).

## Building from source

`python build_apworld.py` packs the `opuc1` folder into `opuc1.apworld`.
