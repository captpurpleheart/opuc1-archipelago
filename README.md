# One Piece Unlimited Cruise 1 - Archipelago

An [Archipelago](https://archipelago.gg) world and Dolphin client for **One Piece Unlimited Cruise Part 1: The
Treasure Beneath the Waves** (Wii, PAL `ROUPAF`).

> **Feature complete.** Every island is in: the **Thousand Sunny, Wooded Isle, Gorge Isle, Iceberg Isle, Cave Isle
> and the final island (Central Isle)**. Please report bugs!
>
> Latest: **1.0.0** (First Feature Complete Build) - see [CHANGELOG.md](CHANGELOG.md).

## What's randomized

**Locations** (about 560 with the default options): move level-ups (and optionally super / co-op move
level-ups), story events, ambushes and bosses (including the secret boss), treasure chests and map dig spots,
Stone Monuments, Gabri Shrines and Build Sites, the first craft of each Development / Cooking / Compounding
recipe (plus the Extra Recipes and Franky's Supplies trades), and (optionally) catching each fish and creature for
the first time and picking up each material for the first time (Materialsanity).

**Goal** (option): "God" Eneru, Gecko Moria, Aokiji, Blackbeard, or the Doom Guardian on Central Isle (default),
optionally after beating every island boss or every boss. Every island is in every seed. The Gorge Isle, Iceberg
Isle, Cave Isle and Central Isle are unlocked by Archipelago items, so they can be reached much earlier than in the
base game.

**Items:** the Straw Hats (you start with one), moves, co-op moves and abilities (including the Arts), tools and
key items (Pickaxe, Bug-Catcher Net, Vacuum Cleaner, Fishing Rod and upgrades, etc), Usopp's Workshop / Sanji's
Kitchen / Chopper's Pharmacy / Franky's Supplies, the islands, Gabri levels (or per-colour Energy levels), shrine
and build site access, The Wherever Cannon, "The Final Door", treasure map fragments, and filler (food and medicine,
also in packages of 3 and 5, Kuwagata, Orbs and Old Gold Coins), plus optional status traps (Burn, Poison, Frozen,
Paralysis, Sleep, Stun).

**Energy Link** (option): convert Gabri's Energy into the multiworld's shared bank and withdraw it again, in the
client's Gabri Energy tab (1 Energy = 10 MJ, Gold 20 MJ; converting keeps 80%).

**Death Link** (option): a Straw Hat being defeated (and, optionally, falling into the abyss / deep water) sends a
death; a received death knocks out the Straw Hat you're controlling once it's safe (never on the Thousand Sunny).

Other quality-of-life changes the client makes:
- No Game Over: the party is revived instead. Boss fights restart, ambushes carry on, and elsewhere you're
  taken back to the Thousand Sunny.
- Archipelago messages in game: items you send and receive are shown on screen (`/messages` in the client to
  change or turn them off).
- Received items arrive through the game's own "obtained" messages. The **Armed Items** tab shows anything the
  client is still holding back and why (Pickaxe until you reach the Thousand Sunny, a full bag, YAML option settings).
- Recipe descriptions show which item a recipe's location holds (optional).
- The Database menu is open from the start (fish / creature checks are read from it).
- Treasure map drops from enemies are Gold Orbs instead; the Sunny's dust piles give Orbs (Old Gold Coins with
  Franky's Supplies).
- No "An Idea!" recipe popups (the client shows recipes itself).
- The Sunny's Aquarium (fish tank storage) and the helm's Next Island menu are open from the start.
- The **Gabri Energy** tab shows each Energy colour's level and cap.
- Storage holds 45 items (option, on by default).
- Optional (see the YAML): better creature traps, guaranteed creature drops, better plant / random dig / Gunpowder
  drop rates, equal fish rates, easier fish, quick fish / creature recipes, Iron Scrap giving Gold Energy, the repeatable dig
  spot by the Thousand Sunny giving Pure Iron Ore, Chopper & Brook immune to the cold, starting costumes.

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

**Known issue:** don't load a save after quitting to the title screen (it can hang on a black screen). Close the
game, start it again (client at the title screen) and load.

If the client reports that dolphin-memory-engine is missing, install it into the Python that runs Archipelago:
`pip install dolphin-memory-engine`.

## Options

Grouped as in the YAML (every option is explained there):
- **Game Options** - starting character, goal, extra Final Door requirement, Death Link, falling causes a Death Link.
- **Gabri Options** - Gabri Energy items (levels or per colour), starting Gabri Energy, how many Gabri level items,
  Energy Link, Wherever Cannon unlock.
- **Item Options** - Materialsanity, early Pickaxe / Bug-Catcher Net / Fishing Rod / Vacuum Cleaner / Bag Upgrades, Bag & Palette
  upgrade item type, treasure maps requiring every fragment, Gunpowder logic (on / off, enemy drops in logic or
  not, or only with Nami's Whirlwind), the gunners' Gunpowder drop rate, craftables making max copies.
- **Crafting Recipe Options** - what opens each crafting room (including start with it), Arts requiring their Straw
  Hat, Franky's Supplies (on / off, unlock, Franky for Art of Supplying), Extra Crafting Recipes, quick recipes.
- **Characters, Moves & Skills Options** - faster move EXP (2X-5X), Super Move Locations (off / on / unimportant),
  Chopper & Brook always cold-resistant, Nami for treasure maps, Robin for Stone Monuments, Franky for Build Sites,
  Cat Burglar, Light Weight and Flower Flower Power item types.
- **Fishing & Bug-Catching Options** - Fishsanity, Creaturesanity, how many of each, combined rod / line levels,
  number of rod upgrade items, equal fish rates, easier fish, better traps, guaranteed creature drops.
- **Quality of Life Options** - recipe discovery through Arts, recipe descriptions that spoil locations, no
  diminishing returns for food, Iron Scrap giving Gold Energy, Blue Orb dig spots giving Pure Iron Ore, better random
  dig item rates, better plant drop rates, Expanded Storage.
- **Starting Costumes** - each Straw Hat's outfit (Unlimited or Thriller Bark, and its style).
- **Filler & Trap Weighting Options** - quality / bundle weighting, the food / medicine / other mix, and traps.

## Reporting bugs

Please include what happened and the output of the client's `/status` command (it starts with the
client version).

## Building from source

`python build_apworld.py` packs the `opuc1` folder into `opuc1.apworld`.
