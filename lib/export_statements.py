from pathlib import Path

from polygon_api import *

from lib.cli import manual
from lib.export_context import ExportContext
from lib.output_only_strategy import OutputOnlyStrategyType
from lib.parse_statement import *


def clone_statement(source: ParsedStatement, is_interactive: bool) -> Statement:
    target = Statement()
    target.name = source.name
    target.legend = source.legend
    target.input = source.input
    target.output = source.output
    target.scoring = source.scoring
    if is_interactive:
        target.interaction = source.interaction
    target.notes = source.notes

    return target


def export_statements(polygon: Polygon, ctx: ExportContext):
    if os.path.exists("statement/statement.et.tex"):
        export_statements_tex(polygon, ctx)
    elif os.path.exists("statement/statement.et.pdf"):
        export_statements_pdf(polygon, ctx)
    else:
        print("No statements found, skipping statement upload...")


def export_statements_tex(polygon: Polygon, ctx: ExportContext):
    with open("statement/statement.et.tex") as statement_et_stream:
        print("Parsing Estonian statement...")
        parsed = parse_statement(statement_et_stream, ctx.task_config)

    upload_samples(polygon, ctx, parsed)
    print("Uploading statement resources...")
    for figure in parsed.figures:
        Path("polygon/resources").mkdir(parents=True, exist_ok=True)
        path = os.path.join("statement", figure)
        name = figure
        if should_convert(figure):
            new_name = get_converted_image_name(figure)
            new_path = os.path.join("polygon", "resources", new_name)
            print("Converting from %s to %s" % (path, new_path))
            convert(path, new_path)
            path = new_path
            name = new_name

        with open(path, "rb") as resource_stream:
            print("Uploading resource from %s" % path)
            resource_content = resource_stream.read()
            polygon.problem_save_statement_resource(ctx.polygon_id, name, resource_content)

    print("Uploading Estonian statement...")
    pg_statement = clone_statement(parsed, ctx.is_interactive)
    polygon.problem_save_statement(ctx.polygon_id, "english", pg_statement)

    locale_map = {"ru": "russian", "en": "other"}
    for locale in locale_map:
        translation_path = "statement/statement.%s.tex" % locale
        if os.path.exists(translation_path):
            with open(translation_path) as translation_stream:
                print("Parsing translation for locale %s" % locale)
                parsed = parse_statement(translation_stream, ctx.task_config)

            pg_statement = clone_statement(parsed, ctx.is_interactive)
            print("Uploading translation for locale %s" % locale)
            polygon.problem_save_statement(ctx.polygon_id, locale_map[locale], pg_statement)

    manual("Go to the statement page, check if HTML renders for all translations, fix all errors.")


def upload_samples(polygon: Polygon, ctx: ExportContext, parsed: ParsedStatement):
    if ctx.is_output_only and ctx.output_only_strategy.strategy_type == OutputOnlyStrategyType.MANUAL:
        print("Skipping sample upload as output-only strategy is MANUAL.")
        return

    print("Uploading samples...")
    polygon_test_index = 1
    for example in parsed.examples:
        input_path = "input/input%s.txt" % example
        output_path = "output/output%s.txt" % example

        if os.path.exists("statement/input%s.txt" % example):
            input_path = "statement/input%s.txt" % example
        if os.path.exists("statement/output%s.txt" % example):
            output_path = "statement/output%s.txt" % example

        with open(input_path) as example_input_stream:
            example_input = example_input_stream.read()

        with open(output_path) as example_output_stream:
            example_output = example_output_stream.read()

        print("Uploading example input/output to polygon test %s from paths %s and %s" %
              (polygon_test_index, input_path, output_path))
        polygon.problem_save_test(ctx.polygon_id, "tests", polygon_test_index,
                                  None,  # test input - not changing
                                  test_group=ctx.test_group_by_polygon_id[polygon_test_index],
                                  test_points=ctx.test_points_by_polygon_id[polygon_test_index],
                                  test_use_in_statements=True,
                                  test_input_for_statements=example_input,
                                  test_output_for_statements=example_output,
                                  verify_input_output_for_statements=False)

        polygon_test_index += 1


def export_statements_pdf(polygon: Polygon, ctx: ExportContext):
    problem_display_name = ctx.task_config["name"]
    if "title" in ctx.task_config:
        problem_display_name = ctx.task_config["title"]

    Path("polygon/resources").mkdir(parents=True, exist_ok=True)
    locale_map = {"et": "english", "ru": "russian", "en": "other"}
    for locale in locale_map:
        pdf_name = "statement.%s.pdf" % locale
        pdf_path = os.path.join("statement", pdf_name)
        if os.path.exists(pdf_path):
            print("Converting PDF for locale %s..." % locale)
            new_name = get_converted_image_name(pdf_name)
            new_path = os.path.join("polygon", "resources", new_name)
            os.system("convert -density 100 %s -append %s" % (pdf_path, new_path))

            print("Uploading PDF for locale %s..." % locale)
            with open(new_path, "rb") as resource_stream:
                resource_content = resource_stream.read()
                polygon.problem_save_statement_resource(ctx.polygon_id, new_name, resource_content)

            statement = Statement()
            statement.name = problem_display_name
            statement.legend = "\\begin{center}\\includegraphics{%s}\\end{center}" % new_name
            polygon.problem_save_statement(ctx.polygon_id, locale_map[locale], statement)