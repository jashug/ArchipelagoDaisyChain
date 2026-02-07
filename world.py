import math
import os
from collections.abc import Mapping
from typing import Any

from worlds.AutoWorld import World
from worlds.Files import APPatch

from . import items, locations
from .constants import GAME_NAME, ROOT_REGION_NAME
from .options import LOGIC_DISTRIBUTION_NAMES, DaisyChainOptions


class FutureYaml(APPatch):
    game = GAME_NAME

    def __init__(
        self,
        yaml_contents,
        outfile_name: str,
        output_directory: str,
        player=None,
        player_name="",
        server="",
    ):
        self.yaml_contents = yaml_contents
        super().__init__(
            os.path.join(output_directory, outfile_name + ".yaml"),
            player,
            player_name,
            server,
        )

    def write_contents(self, opened_zipfile) -> None:
        opened_zipfile.writestr("DaisyChainFutureSlot.yaml", self.yaml_contents)


def random_binomial(random, n, p):
    """Number of successes with n iid probability p binary variables"""
    return random.binomialvariate(n=n, p=p)


def random_dual_uniform(random, n, p):
    """A flatter distribution than binomial but still with expected value n * p"""
    x = random.random()
    q = 1 - p
    if x < q:
        y = x / q * p
    else:
        y = 1 - (1 - x) / p * q
    return max(0, min(n, math.ceil(y * n - random.random())))


class DaisyChainWorld(World):
    """
    Daisy Chain for AP allows playing an archipelago
    with a group of people to be decided in the future.
    """

    game = GAME_NAME

    # TODO: WebWorld

    options_dataclass = DaisyChainOptions
    options: DaisyChainOptions

    location_name_to_id = locations.LOCATION_NAME_TO_ID
    item_name_to_id = items.ITEM_NAME_TO_ID

    origin_region_name = ROOT_REGION_NAME

    def generate_early(self) -> None:
        # past_logic is the transpose complement of what we will actually use
        self.past_logic = self.options.past_logic["logic"]
        self.past_nonce = self.options.past_logic["nonce"]
        if self.past_nonce is None:
            assert not self.past_logic
        self.total_past_items = sum(
            len(block["locations"]) for block in self.past_logic
        )
        self.total_past_locations = sum(block["items"] for block in self.past_logic)
        future_bias = int(self.options.future_bias) / 100.0
        random = self.random
        if "logic" not in self.options.future_logic:
            future_logic = [
                {"items": block["items"], "locations": len(block["locations"])}
                for block in self.past_logic
            ]
        else:
            future_logic = self.options.future_logic["logic"]
        random_count_fn = [random_binomial, random_dual_uniform][
            int(self.options.future_logic_distribution)
        ]
        self.future_logic = [
            {
                "items": block["items"],
                "locations": [
                    set(
                        random.sample(
                            range(block["items"]),
                            random_count_fn(random, block["items"], future_bias),
                        )
                    )
                    for _ in range(block["locations"])
                ]
                if isinstance(block["locations"], int)
                else block["locations"],
            }
            for block in future_logic
        ]
        self.total_future_locations = sum(
            len(block["locations"]) for block in self.future_logic
        )
        self.total_future_items = sum(block["items"] for block in self.future_logic)
        self.my_nonce = f"{random.randrange(2**128):032x}"

        disparity = (
            self.total_past_locations
            + self.total_future_locations
            - self.total_past_items
            - self.total_future_items
        )
        self.filler_items = max(0, disparity)
        self.filler_locations = max(0, -disparity)

    def create_regions(self) -> None:
        locations.create_locations(self)

    def create_items(self) -> None:
        items.create_all_items(self)

    def create_item(self, name: str) -> items.DaisyChainItem:
        return items.create_item(self, name)

    def get_filler_item(self) -> str:
        return items.FILLER_ITEM_NAME

    def fill_slot_data(self) -> Mapping[str, Any]:
        return {
            "past_logic": [
                {
                    "items": block["items"],
                    "locations": [[dep for dep in row] for row in block["locations"]],
                }
                for block in self.past_logic
            ],
            "past_nonce": self.past_nonce,
            "future_logic": [
                {
                    "items": block["items"],
                    "locations": [[dep for dep in row] for row in block["locations"]],
                }
                for block in self.future_logic
            ],
            "nonce": self.my_nonce,
            "past_item_id_start": items.PAST_ITEM_START,
            "future_item_id_start": items.FUTURE_ITEM_START,
            "past_location_id_start": locations.PAST_LOCATION_START,
            "future_location_id_start": locations.FUTURE_LOCATION_START,
            "filler_item_id": items.FILLER_ITEM_ID,
            "filler_location_id_start": locations.FILLER_LOCATION_START,
            "filler_location_count": self.filler_locations,
            "past_item_spoilers": [
                {"player": item.location.player, "location": item.location.address}
                for item in self.past_items
            ],
            "future_item_spoilers": [
                {"player": item.location.player, "location": item.location.address}
                for item in self.future_items
            ],
            "version": 1,
        }

    def generate_output(self, output_directory):
        outfile_name = self.multiworld.get_out_file_name_base(self.player) + ".yaml"
        with open(os.path.join(output_directory, outfile_name), "w") as yaml:
            yaml.write("description: Continue the chain!\n")
            yaml.write(f"name: {self.player_name}\n")
            yaml.write("game: DaisyChain Proxy\n")
            yaml.write("requires:\n")
            yaml.write("  version: 0.6.5\n")
            yaml.write("  game:\n")
            yaml.write("    DaisyChain Proxy: 0.0.1\n")
            yaml.write("DaisyChain Proxy:\n")
            yaml.write("  # DO NOT CHANGE the past_logic section\n")
            yaml.write("  past_logic:\n")
            yaml.write(f"    nonce: {self.my_nonce}\n")
            yaml.write("    logic:\n")
            for block in self.future_logic:
                yaml.write(f"      - items: {block['items']}\n")
                yaml.write("        locations:\n")
                for row in block["locations"]:
                    yaml.write(f"          - [{', '.join(str(dep) for dep in row)}]\n")
            yaml.write("  # May change settings below\n")
            yaml.write(f"  future_bias: {int(self.options.future_bias)}\n")
            yaml.write(
                f"  future_logic_distribution: {LOGIC_DISTRIBUTION_NAMES[int(self.options.future_logic_distribution)]}\n"
            )
            yaml.write("  future_logic:\n")
            yaml.write("    logic:\n")
            for block in self.future_logic:
                yaml.write(f"      - items: {block['items']}\n")
                yaml.write(f"        locations: {len(block['locations'])}\n")
