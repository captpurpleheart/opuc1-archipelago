# Changelog

## ALPHA Build v0.25.1 - "The Iceberg Isle Scope"
The Iceberg Isle is here! Our biggest update yet, with tons of new options and quality of life changes!

> Generate a new seed with this version and the new `OPUC1.yaml`. A lot of options were renamed or regrouped, so older YAMLs will quietly fall back to the defaults for those.

### What's New?
#### **The Iceberg Isle, Unexplored Ice Region**
The main feature of this update, adds the 3rd Island to the AP run. This means Locations for Wapol, Spandam & Aokiji, all the various ambushes, shrines, stone monuments, treasure chests and more!
This also means new locations for Usopp's Workshop / Sanji's Kitchen / Chopper's Pharmacy for all the newly accessible materials found on the new Island as well as all the new fish & creatures to Fish/Catch for those sanity options!
- **NEW GOAL** - Aokiji can now be chosen as the goal. Every island is in every seed, whichever goal you pick.

#### **Death Link & Trap Items!**
- Death Link support has been added. When a Straw Hat is defeated, it sends out a Death Link. Receiving a Death Link causes your current active character to be defeated (it waits until it's safe, and never happens on the Thousand Sunny).
- Additional Option to choose whether or not falling in the abyss/deep water sends out a Death Link.
- Trap Items have been added. You can weight them in the Filler Weighting category, now renamed to include Traps. Only 1 Trap can be active at a time, the rest get queued.
```
Included Trap Items:
Burn Trap - Inflicts burn status on your active character until 25% of your Max HP has been depleted. If you only have 1 character left, you will never go below 10% HP. Burn Traps wait until you're off the Thousand Sunny.
Poison Trap - Inflicts Poison for 10 Seconds on your active character.
Frozen Trap / Paralysis Trap / Sleep Trap / Stun Trap - applies the respective status on your active character for 5 seconds.
```
#### **Optional Gunpowder Logic**
- Logic for Gunpowder has been added, and various options regarding it. Since Gunpowder can be used to break rock paths and X digspots (Clay / Marble / Pure Iron Ore), it can do a lot of things the Pickaxe can do. Random ground digs and treasure map chests still need the Pickaxe.
- You can turn off Gunpowder logic completely, so the Pickaxe will be the only logical requirement for the things it's needed for, or only have Gunpowder go into logic when it's craftable, or when you can get it from enemy drops, and whether or not Nami's Whirlwind is logically important for farming enemy gunpowder drops.
- You can choose a new Drop Rate for Gunpowder for the Gunners (5-100%, 20% by default; vanilla is 4-5%). Nami's Whirlwind steals at the same rate, and Cat Burglar multiplies it (Level 1 x3, Level 2 x4, Level 3 x5).

#### **New Features & YAML Options!**
- **NEW FEATURE** - Fish Tank Storage & Ship Steering Wheel are open from the start
- **NEW FEATURE** - Gabri Level Tracker next to the Connect button of the Client
- **NEW OPTION** - Starting Costumes YAML Category, where you can choose between the Unlimited Outfits or the Thriller Bark outfits *(and their styles)* at the start of the run
- **NEW OPTION** - 4X and 5X Move EXP Multipliers
- **NEW OPTION** - Flower Flower Power Item Type option (Useful/Progression)
- **NEW OPTION** - Early Tool and Bag Upgrade Options *(Pickaxe / Bug-Catcher Net / Fishing Rod / Vacuum Cleaner / one or both Bag Upgrades)*
- **NEW OPTION** - Kitchen & Pharmacy open from the start *("Start With" unlock option; Usopp's Workshop "Vanilla" is now called "Start With" too)*
- **NEW OPTION** - Increased random dig item rates (Clay / Handy Rock / Ice Shard)
  *(25% per counted dig instead of 5%)*
- **NEW OPTION** - Increased Bitter Grass / Nectar / Medicinal Herb drop rates depending on the move type (Normal/Slash/Vacuum)
  *(Standard Hits increased drop chances, Slash Hits increased even more, Vacuum increased even more again)*
- **NEW OPTION** - Chopper & Brook to be immune to the cold weather of the Iceberg Isle
- **NEW OPTION** - Equalise Fish Rates
  *(All Fish have the same hook chance for their respective ranges)*
- **NEW OPTION** - Quick Recipes for Fish/Creature recipes
  *(All Recipes only require 1 of any given Fish/Creature)*
- **NEW OPTION** - Guaranteed Creature Drops
  *(All the Item Drop Rates from Creatures have been increased to 100%)*

#### **Bug-Fixes and Other Changes**
- **NEW LOCATION** - Added a "First Step on Central Isle" Location.
- **CHANGE** - Changed the options page layout, should look a lot cleaner now
- **CHANGE** - Changed some Item/Location names
- **CHANGE** - Tone Dial & Vision Dial are now Useful items
- **CHANGE** - Crafting Recipes now say what type of item they hold if the Item Name is too long, or if the player's name cannot be displayed due to a lack of font
  *(EXAMPLE: This recipe also comes with PurpleHeart's Progression Item! / This recipe also comes with an Archipelago Filler Item!)*
- **CHANGE** - Removed the "Sea Kings are Important" option, they're not a big deal to catch with the Sea King Rod (which is logically expected)
- **CHANGE** - Removed the "Aquarium Open from the Start" option, it's always on now
- **CHANGE** - Elephant Tuna goes into logic with Level 5 Fishing Rod & Level 11 Line
- **CHANGE** - Traps Never Expire and Fast Traps are now a single YAML Option called "Better Traps"
- **FIX** - Honey Bees & Royal Jelly are no longer a part of the Wooded Isle Part 1 Region
- **FIX** - Garment Box now correctly turns on the Wardrobe touch spots on the Sunny if found on an Island
- **FIX** - Sharks now require the Whopper Rod as a minimum

## 0.19.9
- Removed the 0.19.8 "put the missing Bug-Catcher Net back" safeguard: it could give a second net. The tool upgrade
  fix from 0.19.8 stays. A spare net from 0.19.8 is harmless and can be discarded.

## 0.19.8
- Fixed the real cause of the Bug-Catcher Net issue: crafting the net (and other tool upgrades, like the Power Vacuum
  Cleaner) didn't swap out the old tool, so the Broken net stayed and the net went missing. Client-side fix: 0.19.6 / 0.19.7 seeds keep working.

## 0.19.7
- Fixed the Broken Bug-Catcher Net coming back after crafting the Bug-Catcher Net. Client-side fix: seeds from
  0.19.6 keep working, just replace the apworld.

## ALPHA Build v0.19.6 - "The Gorge Isle Scope"

The Gorge Isle is here, and with it, a mountain of changes, features and fixes!

> Generate a new seed with this version and the new `OPUC1.yaml` (0.15.x seeds aren't supported by this client).

### What's New?

#### The Gorge Isle
The main feature of this update, adds the 2nd Island to the AP run. This means Locations for Don Krieg & Captain
Kuro, Gecko Moria, all the various ambushes, shrines, stone monuments, treasure chests and more!

This also means new locations for Usopp's Workshop / Sanji's Kitchen / Chopper's Pharmacy for all the newly
accessible materials found on Island 2, as well as all the new creatures to Fish/Catch for those sanity options!

#### The Central Isle & Goal Options
The Central Isle has been added (the final/5th Island), and is now the new default goal, where you must collect
all 13 Gabri Levels as well as "The Final Door" shrine access item, take on the Doom Guardian and win the run! The
single Stone Monument "Inferno", is the only non-goal related location on the island. Other Goal Options include
Eneru and Gecko Moria. If choosing one of those, Doom Guardian will be inaccessible for that run, but you can still
visit that island for the Stone Monument check.

Both The Gorge Isle and The Central Isle are unlocked via Archipelago Items, so you'll be able to access those
islands way earlier than you're supposed to!

#### New Quality of Life Features!
- Iron Scrap gives Gold Energy.
  - *(10 per Iron Scrap. 10 Iron Scrap = 1 Gold Energy Level)* *(YAML OPTION)*
- The Repeatable Blue Orb Digspot outside the Thousand Sunny on the Wooded Isle now gives Pure Iron Ore instead of
  the Blue Orb. Logic now no-longer counts the one-time digspots for Pure Iron Ore, and now requires Brook +
  Pickaxe for the crafting recipes that require it to go into logic, just in case you lose your one-time Pure Iron
  Ores. If this option is off, it removes the locations for the Crafting Recipes that require Pure Iron Ore (until
  we add Island 4).
  - *(YAML OPTION)*
- The Treasure Map drop slot for enemies now drop Gold Orbs instead.
- The Treasure Map 10 drops for the dust piles on the Thousand Sunny give random orbs out instead.
- Creature Traps no longer expire (compared to the 6 minute timer post-catching a creature), and catch things
  after 10 minutes (compared to the vanilla game's 30-50 minute range). When you leave the location you set the
  trap up (Sunny -> Island for example), it shaves off 10 minutes from the timer. So if you set up a trap, leave
  and come back, you'll immediately get a catch.
  - *(2 DIFFERENT YAML OPTIONS)*
- Progressive Bag Upgrade / Progressive Palette Upgrade / Progressive Cat Burglar / Progressive Light Weight can
  now be chosen to be either Useful or Progression-Skip Balancing, if you don't want those items to be locked
  behind unimportant Super Level Ups.
- The Database Menu is unlocked from the Start (usually unlocks post-Gecko Moria), and the client now uses that
  database for Creature/Fishing checks, which fixes Sea King checks not being sent.

### Bug-Fixes and Other Changes
- Fixed the "Idea!" pop-up causing errors that was still affecting Key Items (like the Tone Dial).
- Attempted to fix the checks being sent on reload.
  - *(I could not replicate this issue on my end, so hopefully this'll help guard against this.)*
- Sea King checks not being sent.
- Pickaxe and Red Fruit chests now also go into logic if you beat Moria before Eneru, as the Kitchen/Medical Rooms
  get opened up if Moria is defeated before Eneru as well as the girl's dorms.
- The Fishing Rod level must match the Line Level for harder fish to go into logic.
- Healing Capsule, Stamina Tonic, Mock Cherry Pie and Dual-Action Tonic are no longer filler for now, since the
  Shrines ask for them as offerings, I'd rather not have people access big areas of islands out of logic. I will
  most likely change this again another time.
- Changed a few Item/Location names.

## 0.15.1
- Fixed the "An Idea!" crash with Crafting Recipes Are Discovered Through Arts.

## 0.15.0
- First public alpha: the Thousand Sunny and Island 1 (Wooded Isle).
