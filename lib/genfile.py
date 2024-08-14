from dataclasses import dataclass
from typing import List


@dataclass
class TestGroup:
    points: int
    files: List[str]
    name: str


def parse_genfile(genfile_stream) -> List[TestGroup]:
    unused_name = 0
    unused_id = 0
    groups = []

    for raw_line in genfile_stream:
        line = raw_line.rstrip()
        if len(line) == 0:
            continue
        elif line.startswith("# ST:") or line.startswith("# ST-COMPULSORY:"):
            if line.startswith("# ST:"):
                points = int(line[5:].strip())
            else:
                points = int(line[16:].strip())

            if points != 0 and unused_name == 0:
                unused_name += 1

            groups.append(TestGroup(points, [], str(unused_name)))
            unused_name += 1
        elif line.startswith("#"):
            continue
        else:
            groups[-1].files.append("input" + str(unused_id) + ".txt")
            unused_id += 1

    return groups
