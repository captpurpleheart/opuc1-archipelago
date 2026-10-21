from dataclasses import dataclass

from .rules import CREATURES_IN_SCOPE, FISH_IN_SCOPE
from Options import Choice, DefaultOnToggle, OptionGroup, PerGameCommonOptions, Range, Toggle


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


class CombineRodAndLine(Toggle):
    """No Rod Line items: each Rod Level item also raises the line level by the same step (with 6 items of each,
    one Rod Level item = +5 rod and +5 line). Off: Rod Level and Rod Line items are separate."""
    display_name = "Combine Fishing Rod and Line Levels"


class RodUpgradeItems(Choice):
    """How many Rod Level and Rod Line upgrade items there are (of each).
    30: every item is one level.
    6: every item is five levels.
    4: Rod: Fishing Rod max -> Whopper -> Sea King -> MAX. Line: levels 8, 16, 23, 30."""
    display_name = "Rod Upgrade Items"
    option_30 = 30
    option_6 = 6
    option_4 = 4
    default = 30


class MoveExpMultiplier(Choice):
    """Moves gain levels faster: 2X or 3X move EXP (every per-level requirement divided by 2 or 3)."""
    display_name = "Move EXP Multiplier"
    option_off = 0
    option_2x = 1
    option_3x = 2
    alias_false = 0     # YAMLs from the old on/off toggle
    alias_true = 1
    default = 0


class MoveLocationsImportant(DefaultOnToggle):
    """Move level-up locations can hold progression items. Off: they only get useful items, filler or traps."""
    display_name = "Move Locations Are Important"


class SuperMoveLocationsImportant(Toggle):
    """Super move level-up locations can hold progression items. Off: useful items, filler or traps only.
    Has no effect when Move Locations Are Important is off."""
    display_name = "Super Move Locations Are Important"


class MoveImportanceMaxLevel(Range):
    """The highest move level whose level-up location can hold progression items.
    2: only Level 2 locations; 5: every level."""
    display_name = "Important Move Levels Up To"
    range_start = 2
    range_end = 5
    default = 5


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


class SeaKingsImportant(Toggle):
    """Catching the Sea Kings (and crafting recipes that need Sea King catches or materials) can hold
    progression items. Off: those locations only get useful items, filler or traps."""
    display_name = "Sea Kings Are Important"


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
    vanilla: open from the start, no item.
    own_item: the "Usopp's Workshop" item.
    usopp: having Usopp in the crew, no item.
    own_item_and_usopp: the item and Usopp."""
    display_name = "Usopp's Workshop Unlock Condition"
    option_vanilla = 0
    option_own_item = 1
    option_usopp = 2
    option_own_item_and_usopp = 3
    default = 1


class KitchenUnlock(Choice):
    """What opens Sanji's Kitchen (cooking).
    vanilla: opens after the Island 1 boss, like the base game. That is after the goal, so the
    cooking locations are removed and there is no item.
    own_item: the "Sanji's Kitchen" item.
    sanji: having Sanji in the crew, no item.
    own_item_and_sanji: the item and Sanji."""
    display_name = "Sanji's Kitchen Unlock Condition"
    option_vanilla = 0
    option_own_item = 1
    option_sanji = 2
    option_own_item_and_sanji = 3
    default = 1


class PharmacyUnlock(Choice):
    """What opens Chopper's Pharmacy (compounding).
    vanilla: opens after the Island 1 boss, like the base game. That is after the goal, so the
    compounding locations are removed and there is no item.
    own_item: the "Chopper's Pharmacy" item.
    chopper: having Tony Tony Chopper in the crew, no item.
    own_item_and_chopper: the item and Chopper."""
    display_name = "Chopper's Pharmacy Unlock Condition"
    option_vanilla = 0
    option_own_item = 1
    option_chopper = 2
    option_own_item_and_chopper = 3
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
    display_name = "Treasure Maps Need Every Fragment"


class DisableFoodDiminishingReturns(Toggle):
    """Feeding a Straw Hat the same food again always gives its full stat gain (vanilla: the gain drops each
    time until it stops)."""
    display_name = "Disable Diminishing Returns for Food"


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


@dataclass
class OPUCOptions(PerGameCommonOptions):
    starting_character: StartingCharacter
    combine_rod_and_line: CombineRodAndLine
    rod_upgrade_items: RodUpgradeItems
    move_exp_multiplier: MoveExpMultiplier
    move_locations_important: MoveLocationsImportant
    super_move_locations_important: SuperMoveLocationsImportant
    move_importance_max_level: MoveImportanceMaxLevel
    fishsanity: Fishsanity
    creaturesanity: Creaturesanity
    fish_locations: FishLocations
    creature_locations: CreatureLocations
    sea_kings_important: SeaKingsImportant
    workshop_unlock: WorkshopUnlock
    usopp_required_for_art: UsoppRequiredForArt
    kitchen_unlock: KitchenUnlock
    sanji_required_for_art: SanjiRequiredForArt
    pharmacy_unlock: PharmacyUnlock
    chopper_required_for_art: ChopperRequiredForArt
    treasure_maps_need_every_fragment: TreasureMapsNeedEveryFragment
    disable_food_diminishing_returns: DisableFoodDiminishingReturns
    recipes_discovered_through_arts: RecipesDiscoveredThroughArts
    recipes_spoil_locations: RecipesSpoilLocations
    nami_required_for_maps: NamiRequiredForMaps
    robin_required_for_monuments: RobinRequiredForMonuments
    franky_required_for_build_sites: FrankyRequiredForBuildSites
    filler_quality_weighting: FillerQualityWeighting
    include_bundle_filler: IncludeBundleFiller
    bundle_size_weighting: BundleSizeWeighting
    food_filler_weight: FoodFillerWeight
    medicine_filler_weight: MedicineFillerWeight
    other_filler_weight: OtherFillerWeight


OPTION_GROUPS = [
    OptionGroup("Item Settings", [CombineRodAndLine, RodUpgradeItems, TreasureMapsNeedEveryFragment,
                                   DisableFoodDiminishingReturns, RecipesDiscoveredThroughArts,
                                   RecipesSpoilLocations]),
    OptionGroup("Moves", [MoveExpMultiplier, MoveLocationsImportant, SuperMoveLocationsImportant, MoveImportanceMaxLevel]),
    OptionGroup("Fishing & Bug-Catching", [Fishsanity, Creaturesanity, FishLocations, CreatureLocations,
                                           SeaKingsImportant]),
    OptionGroup("Thousand Sunny & Crew Gating Options",
                [WorkshopUnlock, UsoppRequiredForArt, KitchenUnlock, SanjiRequiredForArt, PharmacyUnlock,
                 ChopperRequiredForArt, NamiRequiredForMaps, RobinRequiredForMonuments,
                 FrankyRequiredForBuildSites]),
    OptionGroup("Filler Weighting Options",
                [FillerQualityWeighting, IncludeBundleFiller, BundleSizeWeighting, FoodFillerWeight,
                 MedicineFillerWeight, OtherFillerWeight]),
]
