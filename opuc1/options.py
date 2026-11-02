from dataclasses import dataclass

from .data import COSTUME_CHOICES
from .rules import CREATURES_IN_SCOPE, FISH_IN_SCOPE
from Options import DeathLink, Choice, DefaultOnToggle, OptionGroup, PerGameCommonOptions, Range, Toggle


class StartingCharacter(Choice):
    """The Straw Hat you start with. The others are items. "random" picks one."""
    display_name = "Starting Character"
    option_luffy = 0
    option_zoro = 1
    option_usopp = 2
    option_sanji = 3
    option_nami = 4
    option_chopper = 5
    option_robin = 6
    option_franky = 7
    option_brook = 8
    default = 0


class Goal(Choice):
    """Which boss ends the game. Every island (Wooded Isle, Gorge Isle, Iceberg Isle and Central Isle) and its bosses
    are in every seed; islands other than the Wooded Isle open with their island item.
    god_eneru: "God" Eneru on the Wooded Isle. gecko_moria: Gecko Moria on the Gorge Isle. aokiji: Aokiji on the
    Iceberg Isle. doom_guardian: the Doom Guardian on Central Isle, behind The Final Door.
    With any goal but doom_guardian, the Doom Guardian fight is left out (no "The Final Door" item)."""
    display_name = "Goal"
    option_god_eneru = 0
    option_gecko_moria = 1
    option_aokiji = 3
    option_doom_guardian = 2
    alias_wooded_isle = 0     # older YAMLs
    alias_gorge_isle = 1
    alias_central_isle = 2
    default = 2


class CombineRodAndLine(Toggle):
    """No Rod Line items: each Rod Level item also raises the line level by the same step (with 6 items of each,
    one Rod Level item = +5 rod and +5 line). Off: Rod Level and Rod Line items are separate."""
    display_name = "Combine Fishing Rod & Line Levels"


class RodUpgradeItems(Choice):
    """How many Rod Level and Rod Line upgrade items there are (of each).
    30: every item is one level.
    6: every item is five levels.
    4: Rod: Fishing Rod max -> Whopper -> Sea King -> MAX. Line: levels 8, 16, 23, 30."""
    display_name = "Number of Rod Upgrade Items"
    option_30 = 30
    option_6 = 6
    option_4 = 4
    default = 30


class MoveExpMultiplier(Choice):
    """Moves gain levels faster: 2X to 5X move EXP (every per-level requirement divided by 2, 3, 4 or 5)."""
    display_name = "Move EXP Multiplier"
    option_off = 0
    option_2x = 1
    option_3x = 2
    option_4x = 3
    option_5x = 4
    alias_false = 0     # YAMLs from the old on/off toggle
    alias_true = 1
    default = 0


class SuperMoveLocations(Choice):
    """Level 2-5 of each super move and co-op move are locations.
    off: no super / co-op move locations. on: they can hold anything. unimportant: only useful items, filler or
    traps. (Standard move levels 2-5 are always locations and can always hold progression.)"""
    display_name = "Super Move Locations"
    option_off = 0
    option_on = 1
    option_unimportant = 2
    default = 2


class Fishsanity(Choice):
    """Catching each fish for the first time is a location.
    on: the locations can hold anything. unimportant: only useful items, filler or traps."""
    display_name = "Fishsanity"
    option_off = 0
    option_on = 1
    option_unimportant = 2
    default = 1


class Creaturesanity(Choice):
    """Catching each creature for the first time (Bug-Catcher Net) is a location.
    on: the locations can hold anything. unimportant: only useful items, filler or traps."""
    display_name = "Creaturesanity"
    option_off = 0
    option_on = 1
    option_unimportant = 2
    default = 1


class FishLocations(Range):
    """How many fish locations there are, picked at random from the fish catchable in this world."""
    display_name = "How Many Fish Locations"
    range_start = 1
    range_end = len(FISH_IN_SCOPE)
    default = len(FISH_IN_SCOPE)


class CreatureLocations(Range):
    """How many creature locations there are, picked at random from the creatures catchable in this world."""
    display_name = "How Many Creature Locations"
    range_start = 1
    range_end = len(CREATURES_IN_SCOPE)
    default = len(CREATURES_IN_SCOPE)


class WorkshopUnlock(Choice):
    """What opens Usopp's Workshop (crafting).
    start_with: open from the start, no item (like the base game).
    own_item: the "Usopp's Workshop" item.
    usopp: having Usopp in the crew, no item.
    own_item_and_usopp: the item and Usopp."""
    display_name = "Usopp's Workshop Unlock Condition"
    option_start_with = 0
    alias_vanilla = 0
    option_own_item = 1
    option_usopp = 2
    option_own_item_and_usopp = 3
    default = 1


class KitchenUnlock(Choice):
    """What opens Sanji's Kitchen (cooking).
    vanilla: opens after the first island boss you beat, like the base game; no item.
    own_item: the "Sanji's Kitchen" item.
    sanji: having Sanji in the crew, no item.
    own_item_and_sanji: the item and Sanji.
    start_with: open from the start, no item."""
    display_name = "Sanji's Kitchen Unlock Condition"
    option_vanilla = 0
    option_own_item = 1
    option_sanji = 2
    option_own_item_and_sanji = 3
    option_start_with = 4
    default = 1


class PharmacyUnlock(Choice):
    """What opens Chopper's Pharmacy (compounding).
    vanilla: opens after the first island boss you beat, like the base game; no item.
    own_item: the "Chopper's Pharmacy" item.
    chopper: having Tony Tony Chopper in the crew, no item.
    own_item_and_chopper: the item and Chopper.
    start_with: open from the start, no item."""
    display_name = "Chopper's Pharmacy Unlock Condition"
    option_vanilla = 0
    option_own_item = 1
    option_chopper = 2
    option_own_item_and_chopper = 3
    option_start_with = 4
    default = 1


class UsoppRequiredForArt(Toggle):
    """Art of Development levels are only given once Usopp has joined the crew (received items wait until then)."""
    display_name = "Usopp Is Required for Art of Development"


class SanjiRequiredForArt(Toggle):
    """Art of Cooking levels are only given once Sanji has joined the crew (received items wait until then)."""
    display_name = "Sanji Is Required for Art of Cooking"


class ChopperRequiredForArt(Toggle):
    """Art of Compounding levels are only given once Tony Tony Chopper has joined the crew
    (received items wait until then)."""
    display_name = "Chopper Is Required for Art of Compounding"


class TreasureMapsNeedEveryFragment(Toggle):
    """A treasure map's fragments are only given once every fragment of that map has been received, so its
    chest can't be dug up until the whole map is found (vanilla: any one fragment is enough)."""
    display_name = "Treasure Maps Require Every Fragment"


class DisableFoodDiminishingReturns(Toggle):
    """Feeding a Straw Hat the same food again always gives its full stat gain (vanilla: the gain drops each
    time until it stops)."""
    display_name = "Disable Diminishing Returns For Food"


class GuaranteedCreatureDrops(DefaultOnToggle):
    """Creatures caught with the Bug-Catcher Net always drop their item (vanilla: 25-60% for many of them, such as
    Royal Jelly from Honey Bees and Doctor Hornets, or Mystery Eggs from Seagulls)."""
    display_name = "Guaranteed Creature Drops"


class EqualiseFishRates(Toggle):
    """Every fish that can bite at a fishing spot is equally likely (vanilla: weighted, e.g. Shining Saury twice as
    likely as a Shark off the Thousand Sunny). Which fish can bite still depends on how far the lure lands."""
    display_name = "Equalise Fish Rates"


class QuickRecipes(Toggle):
    """Development, cooking and compounding recipes need only 1 of each fish or creature they use (e.g. Saury Full
    Course: 1 Shining Saury instead of 5; Special Item Bag: 1 Shark instead of 2). Sea King parts count too."""
    display_name = "Quick Recipes"


class IronScrapGivesGoldEnergy(DefaultOnToggle):
    """Feeding Gabri an Iron Scrap also gives 10 Gold Energy (vanilla: 15 Red, 25 Black, no Gold)."""
    display_name = "Iron Scrap Give Gold Energy"


class BlueOrbSpotGivesIronOre(DefaultOnToggle):
    """Every Blue Orb dig spot on the Wooded Isle gives Pure Iron Ore instead, including the repeatable one next to
    the Thousand Sunny (the Wooded Isle Pure Iron Ore spots can only be dug once)."""
    display_name = "Wooded Isle Blue Orbs Digspots Give Pure Iron Ore"


class BetterRandomDigItemRates(DefaultOnToggle):
    """Digging plain ground with the Pickaxe (no dig spot) finds a random dig item (Clay, Handy Rock, or Ice Shard on
    snow / ice) 25% of the time instead of 5%. It's distance based, not timed: a dig only counts when it's far
    enough from the last one, so wandering around while digging is recommended."""
    display_name = "Better Random Dig Item Rates"


class BetterPlantDropRates(DefaultOnToggle):
    """Bitter Grass, Medicinal Herbs and Nectar drop more often from their plants (Bitter Grass / Medicinal Herbs /
    Nectar): normal hits 25% / 60% / 25% (vanilla 10% / 60% / 15%), slash hits 50% / 80% / 50% (vanilla as normal
    hits), Vacuum Cleaner 75% / 100% / 75% (vanilla 30% / 100% / 30%). The Pickaxe counts as a normal hit; fire still
    burns them to Ashes."""
    display_name = "Better Plant Drop Rates"


class EarlyPickaxe(Toggle):
    """The Pickaxe is placed early (in the first sphere of the multiworld)."""
    display_name = "Early Pickaxe"


class EarlyBugCatcherNet(Toggle):
    """The Broken Bug-Catcher Net is placed early (in the first sphere of the multiworld)."""
    display_name = "Early Bug-Catcher Net"


class EarlyFishingRod(Toggle):
    """The Fishing Rod is placed early (in the first sphere of the multiworld)."""
    display_name = "Early Fishing Rod"


class EarlyVacuumCleaner(Toggle):
    """The first Progressive Vacuum Cleaner is placed early (in the first sphere of the multiworld)."""
    display_name = "Early Vacuum Cleaner"


class EarlyBagUpgrade(Choice):
    """Progressive Item Bag Upgrades placed early (in the first sphere of the multiworld).
    none: no early Bag Upgrade. only_one: the first one. both: both."""
    display_name = "Early Bag Upgrade"
    option_none = 0
    option_only_one = 1
    option_both = 2
    default = 0


class IncludeGunpowderLogic(DefaultOnToggle):
    """Gunpowder counts as another way through rock paths (Wooded Isle Part 2 right side, Iceberg Isle's ice rock
    routes, the chests and monument behind rock paths) and to blow open X dig spots (Clay, Marble, Pure Iron Ore).
    Random plain-ground digs and treasure map chests always need the Pickaxe. Off: only the Pickaxe is expected
    for any of these."""
    display_name = "Include Gunpowder Logic"


class EnemyGunpowderDropLogic(Choice):
    """Whether Gunpowder from enemies counts for logic (compounding it at Chopper's Pharmacy always does). Does
    nothing without Include Gunpowder Logic.
    none: enemy Gunpowder is never expected.
    included: gunners in Gorge Isle Part 3 / Iceberg Isle Part 1 count as a source.
    whirlwind: they count only with Nami and her Whirlwind (to steal it consistently)."""
    display_name = "Enemy Gunpowder Drop Logic"
    option_none = 0
    option_included = 1
    option_whirlwind = 2
    default = 1


class EnemyGunpowderDropRate(Range):
    """Chance (%) that the gunners (the enemies whose common drop is Gunpowder) drop Gunpowder when defeated, and that
    Nami's Whirlwind steals it from them (vanilla: 5% for Pirate and Agent gunners, 4% for Navy gunners; 5 is about
    vanilla). Cat Burglar multiplies the steal chance (Level 1 x3, Level 2 x4, Level 3 x5), up to 100%."""
    display_name = "Enemy Gunpowder Drop Rate"
    range_start = 5
    range_end = 100
    default = 20


class BetterTraps(DefaultOnToggle):
    """A set trap always catches something and keeps it until you check the trap, and catches after 10 minutes of
    play; leaving the trap's area once (another zone, or off the Thousand Sunny) finishes it straight away. What it
    catches is still random. (Vanilla: a trap has a random lifetime of 30-50 minutes and is destroyed with its catch
    when that runs out; the catch takes 30-50 minutes, and leaving the area takes 10 minutes off but never below
    20.)"""
    display_name = "Better Traps"


class _UsefulOrProgression(Choice):
    option_useful = 0
    option_progression = 1
    default = 0


class BagPaletteUpgradeItemType(_UsefulOrProgression):
    """Whether "Progressive Item Bag Upgrade" and "Progressive Palette Upgrade" are Useful or Progression items
    (progression here is progression that skips balancing)."""
    display_name = "Progressive Bag & Palette Item Type"


class CatBurglarItemType(_UsefulOrProgression):
    """Whether "Nami - Progressive Cat Burglar" is a Useful or Progression item (progression here is progression
    that skips balancing)."""
    display_name = "Nami's Cat Burglar Item Type"


class LightWeightItemType(_UsefulOrProgression):
    """Whether "Brook - Progressive Light Weight" is a Useful or Progression item (progression here is progression
    that skips balancing)."""
    display_name = "Brook's Light Weight Item Type"


class FlowerPowerItemType(_UsefulOrProgression):
    """Whether "Robin - Progressive Flower Flower Power" is a Useful or Progression item (progression here is
    progression that skips balancing)."""
    display_name = "Robin's Flower Flower Power Item Type"


class ChopperBrookColdResistance(DefaultOnToggle):
    """Chopper and Brook always have Cold Resistance, as if they had used an Anti-Cold Cream (cold areas stop SP
    from regenerating for everyone else)."""
    display_name = "Chopper & Brook Always Have Cold Resistance"


class RecipesDiscoveredThroughArts(DefaultOnToggle):
    """Development / Cooking / Compounding recipes only show in their menu once the Art level needed to craft them
    has been received (rows need Art 0-3). Off: every recipe is shown from the start. Purely visual: a recipe
    can't be crafted before its Art level either way."""
    display_name = "Crafting Recipes Are Discovered Through Arts"


class RecipesSpoilLocations(DefaultOnToggle):
    """Recipe descriptions say which item (and whose) the recipe's location holds. Off: they only say it holds an
    unclaimed Archipelago location."""
    display_name = "Crafting Recipes Spoil Locations"


class NamiRequiredForMaps(Toggle):
    """Treasure Map Fragments are only given once Nami has joined the crew (received fragments wait until then)."""
    display_name = "Nami Is Required for Treasure Maps"


class RobinRequiredForMonuments(Toggle):
    """Stone Monuments can't be read (touching them does nothing) until Nico Robin has joined the crew."""
    display_name = "Robin Is Required for Stone Monuments"


class FrankyRequiredForBuildSites(Toggle):
    """Build Sites stay locked (impossible cost) until Franky has joined the crew and their Access item is found.
    Everything behind a Build Site (like the secret boss) needs Franky as well."""
    display_name = "Franky Is Required for Build Sites"


class FillerQualityWeighting(DefaultOnToggle):
    """Stronger food and medicine is rarer in the filler pool. Off: every food / medicine / other item is
    equally likely within its group."""
    display_name = "Items Are Weighted Based on Quality"


class IncludeBundleFiller(DefaultOnToggle):
    """Small Packages (x3) and Large Packages (x5) of food, medicine and the Kuwagata are in the filler pool."""
    display_name = "Include Bundle Filler"


class BundleSizeWeighting(DefaultOnToggle):
    """Bigger packages are rarer: Small Packages are half as likely as the single item, Large ones a quarter.
    Off: packages are as likely as the single item. Does nothing without Include Bundle Filler."""
    display_name = "Bundle Filler Is Weighted Based on Size"


class IncludeTraps(Toggle):
    """Status traps are in the filler pool: Burn, Frozen, Poison, Paralysis, Sleep and Stun Trap. A trap hits the
    Straw Hat you're controlling with that status (no damage), like an enemy attack. Traps queue up and never play at
    the same time: the next one waits until the last one has worn off. How many there are is set by Trap Filler
    Weight."""
    display_name = "Include Traps"


class FoodFillerWeight(Range):
    """How much of the filler is food (relative to Medicine and Other Filler Weight). 0: no food filler."""
    display_name = "Food Filler Weight"
    range_start = 0
    range_end = 100
    default = 64


class MedicineFillerWeight(Range):
    """How much of the filler is medicine (relative to Food and Other Filler Weight). 0: no medicine filler."""
    display_name = "Medicine Filler Weight"
    range_start = 0
    range_end = 100
    default = 27


class OtherFillerWeight(Range):
    """How much of the filler is other items: the Kuwagata and the six Orbs (relative to Food and Medicine
    Filler Weight). 0: none of them."""
    display_name = "Other Filler Weight"
    range_start = 0
    range_end = 100
    default = 9


class TrapFillerWeight(Range):
    """How much of the filler is traps (relative to Food, Medicine and Other Filler Weight). Does nothing without
    Include Traps."""
    display_name = "Trap Filler Weight"
    range_start = 0
    range_end = 100
    default = 10


# ---- Starting Costumes (one choice per Straw Hat, built from data.COSTUME_CHOICES) ----
_COSTUME_DOC = ("{who}'s outfit at the start of the game. Costumes can be changed later on at the Thousand Sunny's "
                "wardrobes in the girls' dorm (open after Gecko Moria) once the Garment Box has been found.")
STARTING_COSTUME_OPTIONS = []
for _who, _choices in COSTUME_CHOICES:
    _attrs = {"__doc__": _COSTUME_DOC.format(who=_who), "display_name": f"{_who}'s Starting Costume", "default": 0}
    for _i, (_key, _label, _c, _s) in enumerate(_choices):
        _attrs["option_" + _key] = _i
    _cls = type(f"StartingCostume{_who}", (Choice,), dict(_attrs, __module__=__name__))
    globals()[_cls.__name__] = _cls
    STARTING_COSTUME_OPTIONS.append(_cls)


class OPUCDeathLink(DeathLink):
    """When any Straw Hat is defeated, everyone else in the multiworld with Death Link on dies too. When someone else
    dies, the Straw Hat you're controlling takes a fatal hit (the next crew member takes over as usual; a full party
    wipe still sends you back to the Thousand Sunny)."""
    display_name = "Death Link"


class FallingDeathLink(DefaultOnToggle):
    """With Death Link on: falling into the abyss or deep water also sends a death (it only costs some HP in game).
    Off: only a Straw Hat dying sends one. Does nothing without Death Link."""
    display_name = "Falling Causes a Death Link"


@dataclass
class OPUCOptions(PerGameCommonOptions):
    # Game Options
    starting_character: StartingCharacter
    goal: Goal
    death_link: OPUCDeathLink
    falling_death_link: FallingDeathLink
    # Item Options
    early_pickaxe: EarlyPickaxe
    early_bug_catcher_net: EarlyBugCatcherNet
    early_fishing_rod: EarlyFishingRod
    early_vacuum_cleaner: EarlyVacuumCleaner
    early_bag_upgrade: EarlyBagUpgrade
    bag_palette_upgrade_item_type: BagPaletteUpgradeItemType
    treasure_maps_need_every_fragment: TreasureMapsNeedEveryFragment
    include_gunpowder_logic: IncludeGunpowderLogic
    enemy_gunpowder_drop_logic: EnemyGunpowderDropLogic
    enemy_gunpowder_drop_rate: EnemyGunpowderDropRate
    # Characters, Moves & Skills Options
    move_exp_multiplier: MoveExpMultiplier
    super_move_locations: SuperMoveLocations
    cat_burglar_item_type: CatBurglarItemType
    light_weight_item_type: LightWeightItemType
    flower_power_item_type: FlowerPowerItemType
    chopper_brook_cold_resistance: ChopperBrookColdResistance
    # Fishing & Bug-Catching Options
    fishsanity: Fishsanity
    creaturesanity: Creaturesanity
    fish_locations: FishLocations
    creature_locations: CreatureLocations
    combine_rod_and_line: CombineRodAndLine
    rod_upgrade_items: RodUpgradeItems
    equalise_fish_rates: EqualiseFishRates
    better_traps: BetterTraps
    guaranteed_creature_drops: GuaranteedCreatureDrops
    quick_recipes: QuickRecipes
    # Quality of Life Options
    recipes_discovered_through_arts: RecipesDiscoveredThroughArts
    recipes_spoil_locations: RecipesSpoilLocations
    disable_food_diminishing_returns: DisableFoodDiminishingReturns
    iron_scrap_gives_gold_energy: IronScrapGivesGoldEnergy
    blue_orb_spot_gives_iron_ore: BlueOrbSpotGivesIronOre
    better_random_dig_item_rates: BetterRandomDigItemRates
    better_plant_drop_rates: BetterPlantDropRates
    # Thousand Sunny & Crew Gating Options
    workshop_unlock: WorkshopUnlock
    usopp_required_for_art: UsoppRequiredForArt
    kitchen_unlock: KitchenUnlock
    sanji_required_for_art: SanjiRequiredForArt
    pharmacy_unlock: PharmacyUnlock
    chopper_required_for_art: ChopperRequiredForArt
    nami_required_for_maps: NamiRequiredForMaps
    robin_required_for_monuments: RobinRequiredForMonuments
    franky_required_for_build_sites: FrankyRequiredForBuildSites
    # Starting Costumes
    luffy_starting_costume: StartingCostumeLuffy      # noqa: F821 (built above)
    zoro_starting_costume: StartingCostumeZoro        # noqa: F821
    usopp_starting_costume: StartingCostumeUsopp      # noqa: F821
    sanji_starting_costume: StartingCostumeSanji      # noqa: F821
    nami_starting_costume: StartingCostumeNami        # noqa: F821
    chopper_starting_costume: StartingCostumeChopper  # noqa: F821
    robin_starting_costume: StartingCostumeRobin      # noqa: F821
    franky_starting_costume: StartingCostumeFranky    # noqa: F821
    brook_starting_costume: StartingCostumeBrook      # noqa: F821
    # Filler & Trap Weighting Options
    filler_quality_weighting: FillerQualityWeighting
    include_bundle_filler: IncludeBundleFiller
    bundle_size_weighting: BundleSizeWeighting
    include_traps: IncludeTraps
    food_filler_weight: FoodFillerWeight
    medicine_filler_weight: MedicineFillerWeight
    other_filler_weight: OtherFillerWeight
    trap_filler_weight: TrapFillerWeight


OPTION_GROUPS = [
    # Game Options (Starting Character, Goal, Death Link, Falling Causes a Death Link) is Archipelago's default group
    # for options not listed here; they come first in OPUCOptions so they're in that order.
    OptionGroup("Item Options", [EarlyPickaxe, EarlyBugCatcherNet, EarlyFishingRod, EarlyVacuumCleaner,
                                 EarlyBagUpgrade, BagPaletteUpgradeItemType, TreasureMapsNeedEveryFragment,
                                 IncludeGunpowderLogic, EnemyGunpowderDropLogic, EnemyGunpowderDropRate]),
    OptionGroup("Characters, Moves & Skills Options", [MoveExpMultiplier, SuperMoveLocations, CatBurglarItemType,
                                                       LightWeightItemType, FlowerPowerItemType,
                                                       ChopperBrookColdResistance]),
    OptionGroup("Fishing & Bug-Catching Options", [Fishsanity, Creaturesanity, FishLocations, CreatureLocations,
                                                   CombineRodAndLine, RodUpgradeItems, EqualiseFishRates,
                                                   BetterTraps, GuaranteedCreatureDrops, QuickRecipes]),
    OptionGroup("Quality of Life Options", [RecipesDiscoveredThroughArts, RecipesSpoilLocations,
                                            DisableFoodDiminishingReturns, IronScrapGivesGoldEnergy,
                                            BlueOrbSpotGivesIronOre, BetterRandomDigItemRates,
                                            BetterPlantDropRates]),
    OptionGroup("Thousand Sunny & Crew Gating Options",
                [WorkshopUnlock, UsoppRequiredForArt, KitchenUnlock, SanjiRequiredForArt, PharmacyUnlock,
                 ChopperRequiredForArt, NamiRequiredForMaps, RobinRequiredForMonuments,
                 FrankyRequiredForBuildSites]),
    OptionGroup("Starting Costumes", STARTING_COSTUME_OPTIONS),
    OptionGroup("Filler & Trap Weighting Options",
                [FillerQualityWeighting, IncludeBundleFiller, BundleSizeWeighting, IncludeTraps, FoodFillerWeight,
                 MedicineFillerWeight, OtherFillerWeight, TrapFillerWeight]),
]
