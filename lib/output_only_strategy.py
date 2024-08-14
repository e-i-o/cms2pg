from dataclasses import dataclass
from enum import Enum


class OutputOnlyStrategyType(Enum):
    # Do not upload tests or a solution. in that case, it must be done
    # manually in Polygon instead.
    MANUAL = 0,
    # The "input" files on Polygon (not to be confused with the real "input", which are instead
    # attachments to the problem) are actually concatenated input + output with some special
    # separator. The fake solution in Polygon ignores input until the separator and outputs
    # the rest. Use this if the checker requires a 'hint' file.
    CONCAT = 1,
    # The "input" files on Polygon are authentic. The fake solution outputs an answer of
    # the form "-1 -1 -1 -1 -1 (irrelevant tokens) (secret token), which your checker must
    # accept as the correct solution.
    TOKEN = 2


@dataclass
class OutputOnlyStrategy:
    strategy_type: OutputOnlyStrategyType
    separator: str = None
    secret_token: str = None
