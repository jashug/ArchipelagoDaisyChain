from dataclasses import dataclass

from schema import And, Or, Schema, Use

from Options import OptionDict, PerGameCommonOptions, ProgressionBalancing, Range


class DaisyChainProgressionBalancing(ProgressionBalancing):
    default = 0


class PastLogic(OptionDict):
    """Specification of the logic used to generate the past game.

    This should not be modified: either use the default
    if this is the first game in a (branch of a) chain,
    or use the generated value from the past game.

    Blocks denote checks accessible with successive links.
    The first block should be accessible with only this link."""

    display_name = "Past Logic"

    schema = Schema(
        {
            "nonce": Or(None, str),
            "logic": [
                And(
                    {"items": int, "locations": [And([int], Use(set))]},
                    lambda block: all(
                        0 <= dep < block["items"]
                        for row in block["locations"]
                        for dep in row
                    ),
                )
            ],
        }
    )

    default = {"nonce": None, "logic": []}


class FutureBias(Range):
    """Percentage chance that a future location will require an item.
    At least 50 strongly recommended."""

    display_name = "Future Bias"

    range_start = 0
    range_end = 100
    default = 75


class FutureLogic(OptionDict):
    """Define the logic for the future game.

    Default value mirrors the past game, but rerolls
    individual blocks according to future_bias.

    Blocks denote checks accessible with successive links.
    The first block is accessible with just one more link in the chain.

    To be friendly, logic should be no more than one
    shorter than past_logic.logic

    Example:
    logic:
      - items: 5
        locations: 3
      - items: 2
        locations: 4
    """

    display_name = "Future Logic"

    schema = Schema(
        Or(
            {},
            {
                "logic": [
                    And(
                        {
                            "items": int,
                            "locations": Or(
                                int,
                                [And([int], Use(set))],
                            ),
                        },
                        lambda block: (
                            isinstance(block["locations"], int)
                            or all(
                                0 <= dep < block["items"]
                                for row in block["locations"]
                                for dep in row
                            )
                        ),
                    )
                ]
            },
        )
    )

    default = {}


@dataclass
class DaisyChainOptions(PerGameCommonOptions):
    progression_balancing: DaisyChainProgressionBalancing
    past_logic: PastLogic
    future_bias: FutureBias
    future_logic: FutureLogic
