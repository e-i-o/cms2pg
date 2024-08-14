import os
import traceback
from pathlib import Path

from polygon_api import Polygon, SolutionTag

from lib.cli import manual, confirm
from lib.export_context import ExportContext
from lib.output_only import upload_output_only_solution
from lib.validate_solution import validate_solution, RunResult


def export_solution(polygon: Polygon, ctx: ExportContext):
    print("Checking for existing solutions...")
    sols = polygon.problem_solutions(ctx.polygon_id)
    for sol in sols:
        if sol.tag == SolutionTag.MA:
            manual("""This problem already has a main correct solution. Delete it or change its
tag before continuing.""")

    if ctx.is_output_only:
        upload_output_only_solution(polygon, ctx)
        return
    else:
        print("""In Codeforces/Polygon, output files can not be uploaded; instead they must be
generated by the model solution. We will now attempt to find a full correct solution from
the task directory.""")

        solution_dirs = []
        if os.path.isdir("sol"):
            solution_dirs.append("sol")
        if os.path.isdir("solution"):
            solution_dirs.append("solution")

        solutions = []
        for sol_dir in solution_dirs:
            for filename in os.listdir(sol_dir):
                if os.path.isdir(os.path.join(sol_dir, filename)):
                    continue

                bad_ends = [".tex", ".txt",  # probably text explanations
                            ".png", ".gif", ".pdf", ".svg", ".xopp", ".jpg",  # probably their resources
                            ".in", ".out", "~",  # temp files
                            ]
                if any([filename.endswith(bad) for bad in bad_ends]):
                    continue

                solutions.append(os.path.join(sol_dir, filename))

        print("We found the following files that might be solutions.")
        for i, path in enumerate(solutions):
            print(str(i) + ".", path)
        print("Please choose the correct one by typing its number.")
        print("If you want to not upload a solution (and upload one manually later), type 'X'.")

        model_solution_path = None
        while True:
            resp = input("Make your selection: ")
            if resp == "X":
                break

            try:
                choice = int(resp)
                if choice < 0 or choice >= len(solutions):
                    print("Value out of range, try again...")
                else:
                    model_solution_path = solutions[choice]
                    validation_result = offer_to_validate(model_solution_path, ctx)
                    if validation_result:
                        break
            except ValueError:
                print("Not an integer, try again...")

        if model_solution_path is not None:
            print("Uploading %s as the main correct solution..." % model_solution_path)
            with open(model_solution_path) as solution_stream:
                solution_content = solution_stream.read()
                polygon.problem_save_solution(ctx.polygon_id,
                                              Path(model_solution_path).name,
                                              solution_content,
                                              None,  # source_type
                                              "MA")  # tag
                print("Done.")


def offer_to_validate(model_solution_path: str, ctx: ExportContext):
    if ctx.is_interactive:
        return True

    choice = confirm("Do you want to validate this solution?")
    if choice:
        # noinspection PyBroadException
        try:
            validate_result = validate_solution(model_solution_path, ctx)
        except Exception as ex:
            print(traceback.format_exc())
            validate_result = RunResult.NOT_RUN

        print("Validation result is %s." % validate_result)
        if validate_result != RunResult.EXACT_MATCH:
            print("""The output files generated by this solution don't exactly match the ones 
in the output directory.""")
            return confirm("Do you want to proceed anyway?")
        else:
            return True
    else:
        return True
