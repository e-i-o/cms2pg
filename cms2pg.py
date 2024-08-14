#! /usr/bin/python

import json
import os.path
import sys
import traceback
from pathlib import Path

import yaml
from polygon_api import *

from lib.cli import *
from lib.export_basic_info import export_basic_info
from lib.export_checker import export_checker
from lib.export_context import ExportContext, ScoringMode
from lib.export_solution import export_solution
from lib.export_statements import export_statements
from lib.export_tests import export_tests
from lib.output_only import generate_secret_token
from lib.output_only_strategy import OutputOnlyStrategyType, OutputOnlyStrategy
from lib.parse_statement import *

if __name__ == "__main__":
    ctx = ExportContext()
    if os.path.exists("task.yaml"):
        with open("task.yaml") as yaml_stream:
            ctx.task_config = yaml.safe_load(yaml_stream)
    else:
        early_short_name = Path(os.getcwd()).name
        yaml_path = "../" + early_short_name + ".yaml"
        with open(yaml_path) as yaml_stream:
            ctx.task_config = yaml.safe_load(yaml_stream)

    ctx.is_output_only = "output_only" in ctx.task_config and ctx.task_config["output_only"]
    if ctx.task_config["score_type"] == "GroupSum" or ctx.task_config["score_type"] == "Sum" \
            or ctx.task_config["score_type"] == "GroupSumConditional" \
            or ctx.task_config["score_type"] == "GroupSumAtLeastTwo":
        ctx.scoring_mode = ScoringMode.GROUP_SUM
    elif ctx.task_config["score_type"] == "GroupMin" or ctx.task_config["score_type"] == "GroupMul":
        ctx.scoring_mode = ScoringMode.GROUP_MIN
    else:
        raise Exception("unknown score_type in task.yaml")

    ctx.is_interactive = os.path.exists("check/batchmanager.cpp") or os.path.exists(
        "check/interactor.cpp") or os.path.exists("interactor")
    print("output only: %s, interactive: %s, scoring_mode: %s" %
          (ctx.is_output_only, ctx.is_interactive, ctx.scoring_mode))
    if not confirm("Is this correct?"):
        print("Please fix it.")
        sys.exit()

    contest_name = Path(os.getcwd()).parent.name
    polygon_name = ("eio-" + contest_name + "-" + ctx.task_config["name"]).lower()

    with open(os.environ["HOME"] + "/.cms2pg/auth.json") as auth_stream:
        auth = json.load(auth_stream)

    polygon = Polygon("https://polygon.codeforces.com/api/", auth["key"], auth["secret"])

    try:
        print("Creating problem with name %s on polygon..." % polygon_name)
        problem = polygon.problem_create(polygon_name)
        ctx.polygon_id = problem.id
        print("Done.")
    except PolygonRequestFailedException as ex:
        if str(ex) == "name: You already have such problem":
            ret = confirm("""A problem with name %s already exists. 
This script will now overwrite it. Is that ok?""" % polygon_name)
            if not ret:
                sys.exit()

            existing = polygon.problems_list(name=polygon_name)
            if len(existing) != 1:
                raise Exception("found multiple or no problems with that name")

            ctx.polygon_id = existing[0].id
        else:
            print(traceback.format_exc())
            sys.exit()

    print("Problem id is %s." % ctx.polygon_id)

    if ctx.is_output_only:
        print("""This problem is output-only.
Supporting an output-only problem on Polygon/Codeforces requires some trickery. We have the following 
strategies for doing that:
0: MANUAL. This script won't upload any solution or input/output pairs to Polygon.
1: CONCAT. The "input" files on Polygon (not to be confused with the real input files which are instead
attachments to the problem) are actually concatenated input + output, with a special separator.
The fake solution we will upload to Polygon ignores input until the separator, and echoes the rest.
Considerations:
- If your checker requires a 'hint' file, you need to use this strategy.
- Your checker needs to be able to ignore the extra content in the input.
- People using the archive will partially see the optimal outputs.
2. TOKEN: The input files on Polygon are authentic. The fake solution we upload to Polygon will output
an answer of the form '-1 -1 -1 -1 -1 (irrelevant tokens) (secret token)'. Your checker will need to
accept outputs like this as correct.
Considerations:
- Your checker must not require any 'hint' or 'answer' file.
- Your checker needs to be able to detect answers like this without compromising its correctness on
other solutions.""")

        while True:
            resp = input("Make your choice [0/1/2]: ")
            if resp == "0":
                ctx.output_only_strategy = OutputOnlyStrategy(OutputOnlyStrategyType.MANUAL)
                break
            elif resp == "1":
                ctx.output_only_strategy = OutputOnlyStrategy(OutputOnlyStrategyType.CONCAT)
                while True:
                    separator = input("Choose a separator (single character only): ")
                    if len(separator) == 1:
                        ctx.output_only_strategy.separator = separator
                        break
                    else:
                        print("Separator is not single-character, try again.")
                break
            elif resp == "2":
                token = generate_secret_token()
                ctx.output_only_strategy = OutputOnlyStrategy(OutputOnlyStrategyType.TOKEN)
                ctx.output_only_strategy.secret_token = token
                print("Your secret token is %s" % token)
                break
            else:
                print("Invalid response, try again...")

    export_basic_info(polygon, ctx)
    export_tests(polygon, ctx)
    export_checker(polygon, ctx)
    export_solution(polygon, ctx)
    export_statements(polygon, ctx)

    if ctx.is_interactive:
        print("""This problem is interactive. You will likely need to make significant changes to the interactor and/or 
checker. Commit the changes and package the problem when done.""")
    elif ctx.is_output_only:
        print("""This problem is output-only. You will need to upload the the input package and might need to make other
changes too. Commit the changes and package the problem when done.""")
    else:
        print("Committing changes...")
        polygon.problem_commit_changes(ctx.polygon_id, minor_changes=True, message="import with cms2pg")

        print("Initiating package build...")
        # lib doesn't have that method
        polygon._request_ok_or_raise("problem.buildPackage",
                                     args={
                                         "problemId": ctx.polygon_id,
                                         "full": False,
                                         "verify": True
                                     })
        print("Give READ access to 'codeforces' user. The problem is ready.")
