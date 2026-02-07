from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from BaseClasses import Item, ItemClassification

from .constants import GAME_NAME, MAX_ITEMS

if TYPE_CHECKING:
    from .world import DaisyChainWorld


def past_item_name(index: int) -> str:
    """Takes an item index 0 <= index < MAX_ITEMS and returns a name"""
    assert 0 <= index < MAX_ITEMS
    return f"Item for Past #{index + 1:03}"


def future_item_name(index: int) -> str:
    """Takes an item index 0 <= index < MAX_ITEMS and returns a name"""
    assert 0 <= index < MAX_ITEMS
    return f"Item for Future #{index + 1:03}"


FILLER_ITEM_ID = 10
FILLER_ITEM_NAME = "Nothing"

PAST_ITEM_START = 1000
FUTURE_ITEM_START = 2000
assert PAST_ITEM_START > FILLER_ITEM_ID
assert FUTURE_ITEM_START >= PAST_ITEM_START + MAX_ITEMS

ITEM_NAME_TO_ID = {
    name_gen(index): index + offset
    for name_gen, offset in (
        (past_item_name, PAST_ITEM_START),
        (future_item_name, FUTURE_ITEM_START),
    )
    for index in range(MAX_ITEMS)
}
ITEM_NAME_TO_ID[FILLER_ITEM_NAME] = FILLER_ITEM_ID


class DaisyChainItem(Item):
    game = GAME_NAME


def create_item(world: DaisyChainWorld, name: str) -> DaisyChainItem:
    # Could be a little more fine grained with marking some
    # items as non-progression
    if name == FILLER_ITEM_NAME:
        classification = ItemClassification.filler
    else:
        # Do I want this to be ItemClassification.useful as well?
        classification = ItemClassification.progression
    return DaisyChainItem(name, classification, ITEM_NAME_TO_ID[name], world.player)


def create_all_items(world: DaisyChainWorld) -> None:
    world.past_items = [
        world.create_item(past_item_name(i)) for i in range(world.total_past_items)
    ]
    world.future_items = [
        world.create_item(future_item_name(i)) for i in range(world.total_future_items)
    ]
    world.multiworld.itempool += world.past_items
    world.multiworld.itempool += world.future_items
    world.multiworld.itempool += [
        world.create_item(FILLER_ITEM_NAME) for _ in range(world.filler_items)
    ]


class ItemCategory(enum.Enum):
    PAST = 0
    FUTURE = 1
    FILLER = 2


def item_category(item_id):
    if item_id is None or item_id == FILLER_ITEM_ID:
        return ItemCategory.FILLER
    elif item_id < FUTURE_ITEM_START:
        return ItemCategory.PAST
    else:
        return ItemCategory.FUTURE
