from __future__ import annotations

from typing import TYPE_CHECKING

from BaseClasses import Entrance, Location, LocationProgressType, Region

from . import items
from .constants import GAME_NAME, MAX_ITEMS, ROOT_REGION_NAME

if TYPE_CHECKING:
    from .world import DaisyChainWorld


def past_location_name(index: int) -> str:
    """Takes a location index 0 <= index < MAX_ITEMS and returns a name"""
    assert 0 <= index < MAX_ITEMS
    return f"Location in Past #{index + 1:03}"


def future_location_name(index: int) -> str:
    """Takes a location index 0 <= index < MAX_ITEMS and returns a name"""
    assert 0 <= index < MAX_ITEMS
    return f"Location in Future #{index + 1:03}"


def filler_location_name(index: int) -> str:
    """Takes a location index 0 <= index < 2 * MAX_ITEMS and returns a name"""
    assert 0 <= index < 2 * MAX_ITEMS
    return f"Filler Location #{index + 1:03}"


PAST_LOCATION_START = 1000
FUTURE_LOCATION_START = 2000
FILLER_LOCATION_START = 3000
assert PAST_LOCATION_START > 100
assert FUTURE_LOCATION_START >= PAST_LOCATION_START + MAX_ITEMS
assert FILLER_LOCATION_START >= FUTURE_LOCATION_START + MAX_ITEMS

LOCATION_NAME_TO_ID = {
    name_gen(index): index + offset
    for name_gen, offset, count in (
        (past_location_name, PAST_LOCATION_START, MAX_ITEMS),
        (future_location_name, FUTURE_LOCATION_START, MAX_ITEMS),
        (filler_location_name, FILLER_LOCATION_START, 2 * MAX_ITEMS),
    )
    for index in range(count)
}


class DaisyChainLocation(Location):
    game = GAME_NAME


def create_locations(world: DaisyChainWorld):
    player = world.player

    def non_local_rule(allowed_category):
        return lambda item: (
            item.player != player or items.item_category(item.code) == allowed_category
        )

    root_region = Region(ROOT_REGION_NAME, player, world.multiworld)
    world.multiworld.regions.append(root_region)

    past_regions = [root_region]
    last_region = root_region
    last_past_item_index = 0
    last_past_location_index = 0

    def access_all(items):
        items = tuple(items)
        return lambda state: state.has_all(items, player)

    for region_index, block in enumerate(world.past_logic):
        for location_index in range(block["items"]):
            location_name = past_location_name(
                location_index + last_past_location_index
            )
            location = DaisyChainLocation(
                player,
                location_name,
                LOCATION_NAME_TO_ID[location_name],
                last_region,
            )
            location.progress_type = LocationProgressType.PRIORITY
            location.access_rule = access_all(
                items.past_item_name(i + last_past_item_index)
                for i, row in enumerate(block["locations"])
                if location_index not in row
            )
            location.item_rule = non_local_rule(items.ItemCategory.FUTURE)
            last_region.locations.append(location)

        new_region = Region(f"Past Region {region_index}", player, world.multiworld)
        last_region.connect(
            new_region,
            rule=access_all(
                items.past_item_name(i + last_past_item_index)
                for i in range(len(block["locations"]))
            ),
        )

        world.multiworld.regions.append(new_region)
        past_regions.append(new_region)
        last_region = new_region
        last_past_item_index += len(block["locations"])
        last_past_location_index += block["items"]

    last_region = past_regions[min(1, len(past_regions) - 1)]
    last_future_item_index = 0
    last_future_location_index = 0
    for region_index, block in enumerate(world.future_logic):
        for location_index, logic in enumerate(block["locations"]):
            location_name = future_location_name(
                location_index + last_future_location_index
            )
            location = DaisyChainLocation(
                player,
                location_name,
                LOCATION_NAME_TO_ID[location_name],
                last_region,
            )
            location.progress_type = LocationProgressType.PRIORITY
            location.access_rule = access_all(
                items.future_item_name(dep + last_future_item_index) for dep in logic
            )
            location.item_rule = non_local_rule(items.ItemCategory.PAST)
            last_region.locations.append(location)

        new_region = Region(
            f"Future Region {region_index + 1}", player, world.multiworld
        )
        entrance = Entrance(player, parent=last_region)

        def future_region_access(other_region, items):
            items = tuple(items)
            return lambda state: (
                other_region.can_reach(state) and state.has_all(items, player)
            )

        other_region = past_regions[min(2 + region_index, len(past_regions) - 1)]

        entrance.access_rule = future_region_access(
            other_region,
            (
                items.future_item_name(i + last_future_item_index)
                for i in range(block["items"])
            ),
        )
        last_region.exits.append(entrance)
        entrance.connect(new_region)
        world.multiworld.register_indirect_condition(other_region, entrance)

        world.multiworld.regions.append(new_region)
        last_region = new_region
        last_future_item_index += block["items"]
        last_future_location_index += len(block["locations"])

    def completion_condition(all_past_region, all_future_region):
        return lambda state: (
            all_past_region.can_reach(state) and all_future_region.can_reach(state)
        )

    world.multiworld.completion_condition[player] = completion_condition(
        past_regions[-1], last_region
    )

    for location_index in range(world.filler_locations):
        location_name = filler_location_name(location_index)
        location = DaisyChainLocation(
            player, location_name, LOCATION_NAME_TO_ID[location_name], root_region
        )
        location.progress_type = LocationProgressType.EXCLUDED
        root_region.locations.append(location)
