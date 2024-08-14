import os
from pathlib import Path

from polygon_api import Polygon

from lib.export_context import ExportContext


def export_checker(polygon: Polygon, ctx: ExportContext):
    if ctx.is_interactive:
        print("""Skipping checker for now. You will likely need to make significant
changes in the interactor and checker.""")
    elif not os.path.isdir("check") and not os.path.isdir("checker"):
        print("check directory not found. Setting the checker to std::lcmp.cpp...")
        polygon.problem_set_checker(ctx.polygon_id, "std::lcmp.cpp")
    else:
        Path("polygon/checker").mkdir(parents=True, exist_ok=True)
        ctx.has_custom_checker = True
        print("""This problem appears to have a custom checker. You need to change it
to use Polygon's protocol. Put this checker as the only .cpp file in the
polygon/checker directory.""")

        while True:
            resp = input("""Write 'done' without quotes if done. If you want to skip this
step for now, write 'skip' without quotes for now. """)

            if resp == "done":
                files = [name for name in os.listdir("polygon/checker")
                         if name.endswith(".cpp")]
                if len(files) != 1:
                    print("Too many or too few files in the directory. Try again.")
                    continue

                ctx.custom_checker_path = files[0]
                print("Uploading file %s to polygon..." % ctx.custom_checker_path)
                with open(os.path.join("polygon/checker", ctx.custom_checker_path)) as checker_stream:
                    checker_content = checker_stream.read()
                    polygon.problem_save_file(ctx.polygon_id,
                                              "source",
                                              ctx.custom_checker_path,
                                              checker_content)

                print("Setting file %s as checker..." % ctx.custom_checker_path)
                polygon.problem_set_checker(ctx.polygon_id, ctx.custom_checker_path)
                break
            elif resp == "skip":
                ctx.custom_checker_path = None
                break
            else:
                print("Unexpected response.")
