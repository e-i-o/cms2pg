from polygon_api import Polygon, PointsPolicy, FeedbackPolicy

from lib.cli import manual
from lib.export_context import ExportContext, ScoringMode
from lib.genfile import parse_genfile
from lib.output_only import generate_output_only_concat_input
from lib.output_only_strategy import OutputOnlyStrategyType


def export_tests(polygon: Polygon, ctx: ExportContext):
    if ctx.is_output_only and ctx.output_only_strategy.strategy_type == OutputOnlyStrategyType.MANUAL:
        print("Skipping test upload as the problem is output-only and the MANUAL strategy was chosen.")
        return

    manual("""The next step requires manual intervention (API doesn't support the first two steps).
Go to the Tests section and:
- UNCHECK 'Tests well-formed' if task may contain unusual input files (e.g. multiple consecutive spaces),
- SELECT 'Treat points from checker as a percent' under 'Enable points',
- CHECK 'Enable groups'
- DELETE any existing tests.""")

    print("Uploading tests...")
    with open("gen/GEN") as gen_stream:
        ctx.gen_file = parse_genfile(gen_stream)

    test_index = 1
    for group in ctx.gen_file:
        if ctx.is_output_only and group.points == 0:
            print("Skipping group %s because the problem is output-only and the score is 0" % group.name)
            continue

        remaining_points = group.points * 100  # groupsum only

        for i, filename in enumerate(group.files):
            if ctx.scoring_mode == ScoringMode.GROUP_MIN:
                points = group.points if i == 0 else 0
            elif ctx.scoring_mode == ScoringMode.GROUP_SUM:
                # polygon only supports test points up to 2 decimal places
                # which necessitates this trickery
                # the first n - 1 tests get rounded down,
                # the last test gets the remainder
                if i == len(group.files) - 1:
                    points = remaining_points / 100
                else:
                    points = (100 * group.points // len(group.files))
                    remaining_points -= points
                    points /= 100
            else:
                assert False

            if ctx.is_output_only and ctx.output_only_strategy.strategy_type == OutputOnlyStrategyType.CONCAT:
                test_input, description = generate_output_only_concat_input(filename, test_index, ctx)
            else:
                file_path = "input/" + filename
                print("Choosing file %s for test %s" % (file_path, test_index))
                description = "file %s" % filename
                with open(file_path) as test_input_stream:
                    test_input = test_input_stream.read()

            ctx.test_group_by_polygon_id[test_index] = group.name
            ctx.test_points_by_polygon_id[test_index] = points

            print("Uploading test...")
            polygon.problem_save_test(ctx.polygon_id, "tests", test_index, test_input,
                                      test_group=group.name,
                                      test_points=points,
                                      test_description=description)
            test_index += 1

        print("Saving scoring policy for group %s..." % group.name)
        policy = PointsPolicy.COMPLETE_GROUP if ctx.scoring_mode == ScoringMode.GROUP_MIN else PointsPolicy.EACH_TEST
        polygon.problem_save_test_group(ctx.polygon_id, "tests", group.name,
                                        points_policy=policy,
                                        feedback_policy=FeedbackPolicy.COMPLETE)
