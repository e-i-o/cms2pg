import random
import string
from typing import Tuple

from polygon_api import Polygon

from lib.export_context import ExportContext
from lib.output_only_strategy import OutputOnlyStrategyType


def generate_secret_token() -> str:
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(16))


def generate_output_only_concat_input(filename: str, test_index: int, ctx: ExportContext) -> Tuple[str, str]:
    authentic_input_path = "input/" + filename
    authentic_output_path = "output/" + filename.replace("input", "output")
    print("Concatenating %s and %s for output-only test %s."
          % (authentic_input_path, authentic_output_path, test_index))

    with open(authentic_input_path) as authentic_input_stream:
        authentic_input = authentic_input_stream.read()

    with open(authentic_output_path) as authentic_output_stream:
        authentic_output = authentic_output_stream.read()

    test_content = authentic_input + ctx.output_only_strategy.separator + authentic_output
    description = "fake input: concatenated %s and %s" % (filename, filename.replace("input", "output"))
    return test_content, description


def upload_output_only_solution(polygon: Polygon, ctx: ExportContext):
    if ctx.output_only_strategy.strategy_type == OutputOnlyStrategyType.MANUAL:
        print("""Because you chose the MANUAL strategy for output-only problems,
we will skip uploading a solution.""")
        return

    if ctx.output_only_strategy.strategy_type == OutputOnlyStrategyType.CONCAT:
        fake_sol = "#define SEPARATOR '%s'\n" % ctx.output_only_strategy.separator
        fake_sol += CONCAT_SOL_TEMPLATE
    elif ctx.output_only_strategy.strategy_type == OutputOnlyStrategyType.TOKEN:
        fake_sol = '#define TOKEN "%s"\n' % ctx.output_only_strategy.secret_token
        fake_sol += TOKEN_SOL_TEMPLATE
    else:
        assert False

    print("Uploading the fake solution...")
    polygon.problem_save_solution(ctx.polygon_id,
                                  "fakesol.cpp",
                                  fake_sol,
                                  None,  # source_type
                                  "MA")  # tag
    print("Done.")


CONCAT_SOL_TEMPLATE = """
#include <iostream>
#include <iomanip>

using namespace std;

int main () {
  ios::sync_with_stdio(false);
  cin.tie(0);

  bool separator_seen = false;
  char c;
  while (cin >> noskipws >> c) {
    if (separator_seen) {
      cout << c;
    } else if (c == SEPARATOR) {
      separator_seen = true;
    }
  }
}
"""

TOKEN_SOL_TEMPLATE = """
#include <iostream>

using namespace std;

int main () {
  for (int i = 0; i < 5; i++)
    cout << "-1 ";
  cout << "this is just a really dumb hack to make output-only work. ";
  cout << "and this next part is just filler so you don't find out how to get accepted ";
  cout << "by looking at the input/output pairs in the judging log. ";
  for (int i = 0; i < 10000; i++)
    cout << "filler ";
  cout << TOKEN << '\\n';
}
"""
