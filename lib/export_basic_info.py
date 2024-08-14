from polygon_api import Polygon, ProblemInfo

from lib.export_context import ExportContext


def export_basic_info(polygon: Polygon, ctx: ExportContext):
    if ctx.is_output_only:
        return

    problem_info = ProblemInfo()

    problem_info.input_file = ctx.task_config["infile"]
    if problem_info.input_file == "" or ctx.is_interactive:
        problem_info.input_file = "stdin"

    problem_info.output_file = ctx.task_config["outfile"]
    if problem_info.output_file == "" or ctx.is_interactive:
        problem_info.output_file = "stdout"

    time_limit = ctx.task_config["time_limit"]  # in seconds
    time_limit *= 20
    time_limit = 50 * int(time_limit)  # in milliseconds, but must be multiple of 50
    time_limit = max(time_limit, 250)
    time_limit = min(time_limit, 15000)  # polygon constraints
    problem_info.time_limit = time_limit

    memory_limit = ctx.task_config["memory_limit"]  # in MB
    memory_limit = max(memory_limit, 4)
    memory_limit = min(memory_limit, 1024)  # still in MB
    problem_info.memory_limit = memory_limit

    if ctx.is_interactive:
        problem_info.interactive = True

    polygon.problem_update_info(ctx.polygon_id, problem_info)
    print("Done.")
