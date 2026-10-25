# Changelog

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
