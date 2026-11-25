"""Logic for the PopTracker pack, worked out by the client with this world's own rules (1.0.6).

The client rebuilds this world's regions and rules from the slot data, the way Universal Tracker does (the world's
generate_early already takes its settings from multiworld.re_gen_passthrough), then asks which locations the items
received so far can reach. The answer goes to data storage (opuc1_logic_<team>_<slot>) for the tracker, so the map
follows the apworld's logic exactly, with no copy of the rules in the pack.
"""
from typing import Any, Dict, Iterable, Optional, Set

from BaseClasses import CollectionState, MultiWorld


class TrackerLogic:
    def __init__(self, slot_data: Dict[str, Any]) -> None:
        from . import OPUCWorld
        mw = MultiWorld(1)
        mw.game = {1: OPUCWorld.game}
        mw.player_name = {1: "Tracker"}
        mw.set_seed(0)
        mw.re_gen_passthrough = {OPUCWorld.game: dict(slot_data)}
        world = OPUCWorld(mw, 1)
        mw.worlds[1] = world
        dc = OPUCWorld.options_dataclass
        world.options = dc(**{key: option.from_any(option.default) for key, option in dc.type_hints.items()})
        world.generate_early()
        world.create_regions()
        world.set_rules()
        self.mw, self.world = mw, world
        self.locations = [loc for loc in mw.get_locations(1) if loc.address is not None]

    def reachable(self, item_names: Iterable[str]) -> Set[int]:
        """Ids of the locations these items (received so far, starting items included) can reach."""
        state = CollectionState(self.mw)
        for name in item_names:
            try:
                state.collect(self.world.create_item(name), True)
            except Exception:
                continue                     # an item this version doesn't know
        state.sweep_for_advancements()       # events (the goal is the only one)
        return {loc.address for loc in self.locations if loc.can_reach(state)}


def build(slot_data: Dict[str, Any]) -> Optional[TrackerLogic]:
    try:
        return TrackerLogic(slot_data)
    except Exception:
        import logging
        logging.getLogger("Client").exception("Couldn't build the tracker logic; the map shows every location.")
        return None
