import os.path
import shutil
import subprocess
import traceback
from enum import Enum
from pathlib import Path

from lib.export_context import ExportContext


class RunResult(Enum):
    EXACT_MATCH = 0,
    ACCEPTED = 1,
    TIME_LIMIT_EXCEEDED = 2,
    WRONG_ANSWER = 3,
    RUNTIME_ERROR = 4,
    NOT_RUN = 5,
    INCONSISTENT = 6


class Language(Enum):
    CPP = 0,
    PY2 = 1,
    PY3 = 2,
    C = 3


def validate_solution(model_solution_path: str, ctx: ExportContext) -> RunResult:
    # TODO: checker integration
    assert not ctx.is_interactive
    assert not ctx.is_output_only

    working_dir = "polygon/working"
    Path(working_dir).mkdir(parents=True, exist_ok=True)
    _, ext = os.path.splitext(model_solution_path)
    if ext == ".cpp":
        subprocess.run(["g++", "-O2", model_solution_path, "-o", os.path.join(working_dir, "sol")],
                       check=True)
        sol_filename = "sol"
        language = Language.CPP
    elif ext == ".c":
        subprocess.run(["gcc", "-O2", model_solution_path, "-o", os.path.join(working_dir, "sol"), "-lm"],
                       check=True)
        sol_filename = "sol"
        language = Language.C
    elif ext == ".py":
        shutil.copyfile(model_solution_path, os.path.join(working_dir, "sol.py"))
        sol_filename = "sol.py"
        language = Language.PY2
    else:
        print("Solution files with extension %s are not supported." % ext)
        return RunResult.NOT_RUN

    if language == Language.PY2:
        print("Which version of Python is this?")
        while True:
            response = input("Select 2 or 3: ")
            if response == "3":
                language = Language.PY3
                break
            elif response == "2":
                language = Language.PY2
                break
            else:
                print("Unknown response.")

    if ctx.has_custom_checker and ctx.custom_checker_path is not None:
        print("Compiling checker...")
        subprocess.run(["g++", "-O2", os.path.join("polygon/checker", ctx.custom_checker_path),
                        "-o", os.path.join(working_dir, "check")],
                       check=True)

    overall_verdict = RunResult.EXACT_MATCH
    for group in ctx.gen_file:
        for test in group.files:
            infile = ctx.task_config["infile"]
            input_path = os.path.join("input", test)
            if len(infile) != 0:
                shutil.copyfile(input_path, os.path.join(working_dir, infile))
                proc_input = None
            else:
                with open(input_path) as infile_stream:
                    proc_input = infile_stream.read()

            print("Running solution on test %s..." % test)
            args = []
            if language == Language.PY3:
                args.append("pypy3")
                args.append(sol_filename)
            elif language == Language.PY2:
                args.append("python2")
                args.append(sol_filename)
            else:
                args.append("./" + sol_filename)

            try:
                result = subprocess.run(args,
                                        text=True,
                                        input=proc_input,
                                        capture_output=True,
                                        timeout=ctx.task_config["time_limit"],
                                        cwd=working_dir)
                if result.returncode != 0:
                    print("Got runtime error.")
                    return RunResult.RUNTIME_ERROR
            except subprocess.TimeoutExpired:
                print("Time limit exceeded.")
                return RunResult.TIME_LIMIT_EXCEEDED

            expected_output_path = os.path.join("output", test.replace("input", "output"))

            outfile = ctx.task_config["outfile"]
            if len(outfile) != 0:
                actual_output_path = os.path.join(working_dir, outfile)
            else:
                actual_output_path = os.path.join(working_dir, "out.txt")
                with open(actual_output_path, "w") as actual_output_stream:
                    actual_output_stream.write(result.stdout)

            diff = subprocess.run(["diff", "--ignore-trailing-space", "--strip-trailing-cr",
                                   actual_output_path, expected_output_path])

            if diff.returncode == 0:
                verdict = RunResult.EXACT_MATCH
            else:
                verdict = RunResult.WRONG_ANSWER

            if ctx.has_custom_checker:
                if ctx.custom_checker_path is not None:
                    check = subprocess.run(["polygon/working/check",
                                            os.path.join("input", test),
                                            actual_output_path,
                                            expected_output_path],
                                           text=True,
                                           capture_output=True)

                    checker_ok = check.returncode == 0 or \
                                 (check.returncode == 7 and check.stderr.startswith("points 100"))

                    if checker_ok:
                        if verdict == RunResult.EXACT_MATCH:
                            pass
                        if verdict == RunResult.WRONG_ANSWER:
                            verdict = RunResult.ACCEPTED
                    else:
                        if verdict == RunResult.EXACT_MATCH:
                            print("Conflict: output matches input exactly but checker returns WA.")
                            print("Are you sure that the checker is correct?")
                            return RunResult.INCONSISTENT
                        else:
                            pass

                    reverse_check = subprocess.run(["polygon/working/check",
                                                    os.path.join("input", test),
                                                    expected_output_path,
                                                    actual_output_path],
                                                   text=True,
                                                   capture_output=True)

                    reverse_checker_ok = reverse_check.returncode == 0 or \
                                         (reverse_check.returncode == 7 and reverse_check.stderr.startswith(
                                             "points 100"))

                    if checker_ok and not reverse_checker_ok:
                        print("""Checker returns OK but not with reversed output. Are you sure output files 
are not 'hints'?""")
                        return RunResult.INCONSISTENT
                else:
                    print("Warning: can't run checker because you skipped that step.")

            if verdict == RunResult.EXACT_MATCH:
                print("OK")
            elif verdict == RunResult.ACCEPTED:
                if group.points == 0:
                    print("Output file doesn't match output generated by solution exactly, tolerating because example")
                else:
                    print("Output file doesn't match output generated by solution exactly, but still passes.")
                    overall_verdict = RunResult.ACCEPTED
            else:
                if group.points == 0:
                    print("Output file is wrong, tolerating because example, but please check!")
                else:
                    return RunResult.WRONG_ANSWER

    return overall_verdict
