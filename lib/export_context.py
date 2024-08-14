from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List

from lib.genfile import TestGroup
from lib.output_only_strategy import OutputOnlyStrategy


class ScoringMode(Enum):
    GROUP_SUM = 0
    GROUP_MIN = 1


@dataclass
class ExportContext:
    task_config: dict = field(default_factory=dict)
    is_interactive: bool = False
    is_output_only: bool = False
    scoring_mode: ScoringMode = ScoringMode.GROUP_SUM
    polygon_id: Any = None
    output_only_strategy: OutputOnlyStrategy = None

    # various bookkeeping fields that need to be kept track of between phases
    gen_file: List[TestGroup] = None
    has_custom_checker: bool = False
    custom_checker_path: str = None
    # map polygon test id -> group name
    test_group_by_polygon_id: dict = field(default_factory=dict)
    # map polygon test id -> point value
    test_points_by_polygon_id: dict = field(default_factory=dict)