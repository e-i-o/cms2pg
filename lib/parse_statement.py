from typing import TextIO, Dict

from TexSoup import TexSoup
from TexSoup.data import *
from lib.conversions import *

import re

_NAME = "name"
_LEGEND = "legend"
_INPUT = "input"
_OUTPUT = "output"
_SCORING = "scoring"
_INTERACTION = "interaction"
_NOTES = "notes"


class ParsedStatement:
    def __init__(self):
        self.sections = {
            _NAME: "",
            _LEGEND: "",
            _INPUT: "",
            _OUTPUT: "",
            _SCORING: "",
            _INTERACTION: "",
            _NOTES: ""
        }
        self.figures = []
        self.examples = []

    @property
    def name(self) -> str:
        return self.sections[_NAME]

    @name.setter
    def name(self, value: str):
        self.sections[_NAME] = value

    @property
    def legend(self) -> str:
        return self.sections[_LEGEND]

    @legend.setter
    def legend(self, value: str):
        self.sections[_LEGEND] = value

    @property
    def input(self) -> str:
        return self.sections[_INPUT]

    @property
    def output(self) -> str:
        return self.sections[_OUTPUT]

    @property
    def scoring(self) -> str:
        return self.sections[_SCORING]

    @property
    def interaction(self) -> str:
        return self.sections[_INTERACTION]

    @property
    def notes(self) -> str:
        return self.sections[_NOTES]


def parse_statement(raw_statement: TextIO, task_config: Dict):
    raw_statement = norm_verb_args(raw_statement)
    soup = TexSoup(raw_statement)

    # these formatting tags are unnecessary for non-pdf output
    unneeded = soup.find_all(["vspace", "hspace", "pagebreak", "clearpage"])
    for un in unneeded:
        un.delete()

    # xitem and xenum are defined in our sty file - change them to regular itemizes and enumerates
    for xitem in soup.find_all("xitem"):
        xitem.name = "itemize"
    for xenum in soup.find_all("xenum"):
        xenum.name = "enumerate"

    # sisf and valf need to be changed to the actual file names
    for sisf in soup.find_all("sisf"):
        sisf.name = "t"
        sisf.args.append("{%s}" % task_config["infile"])

    for valf in soup.find_all("valf"):
        valf.name = "t"
        valf.args.append("{%s}" % task_config["outfile"])

    # polygon does not support quote. use an itemize with a single item instead
    for quote in soup.find_all("quote"):
        quote.name = "itemize"
        quote.insert(0, TexCmd("item"))

    # wrapfigure and figure are unsupported. use center instead
    for fig in soup.find_all(["wrapfigure", "figure"]):
        fig.name = "center"
        argc = len(fig.args)  # remove all [h] etc
        for i in range(argc):
            fig.args.pop(0)

    # verb is not supported. transform it to polygon's own \t{...} instead
    for verb in soup.find_all("verb"):
        verb.name = "t"

    statement = ParsedStatement()

    # figures need to be uploadexd. record all figures and make them available
    # in the statement return object
    for graphics in soup.find_all("includegraphics"):
        for arg in graphics.args:
            if arg.name == "BraceGroup":
                resolved = resolve_if_no_extension(arg.string)
                if resolved is None:
                    print("Failed to resolve file %s" % arg.string)
                    continue

                statement.figures.append(resolved)
                arg.string = get_converted_image_name(resolved)

    # examples need to all have "custom output" and in case of OO/interactive
    # problems, also "custom input". we need to upload all those to polygon.
    # record the numbers of examples used
    for nde in soup.find_all(["nde", "ndex", "ndey"]):
        statement.examples.append(nde.args[0].string)

    is_ylx = False
    yl = soup.yl
    if yl is None:
        yl = soup.ylx
        is_ylx = True

    statement.name = yl.args[1].string
    points = yl.args[3] if is_ylx else yl.args[4]
    statement.legend = "\\textbf%s.\n" % points

    section_map = {
        "sis": _INPUT,
        "val": _OUTPUT,
        "hnd": _SCORING,
        "suht": _INTERACTION,
        "mrk": _NOTES
    }

    # split statement in sections as necessary
    current_section = _LEGEND

    # trickery to get rid of AssertionError
    ylargs = len(yl.args)
    for i in range(ylargs):
        yl.args.pop(0)

    for node in yl.all:
        if node.name in section_map:
            current_section = section_map[node.name]
        elif node.name == "nde" or node.name == "ndex" or node.name == "ndey":
            current_section = _NOTES
            statement.sections[current_section] += "% " + str(node)
        else:
            statement.sections[current_section] += str(node)

    return statement


# takes a stream, returns a string
# \verb|a| -> \verb{a} everywhere
def norm_verb_args(raw_statement: TextIO) -> str:
    statement_str = raw_statement.read()

    # in theory, this doesn't work with nested verbs
    # leave it be for the moment
    verb_ends = [m.end() for m in re.finditer("\\\\verb", statement_str)]
    statement_mut = list(statement_str)
    for L in verb_ends:
        if L >= len(statement_mut):
            continue

        R = statement_str.find(statement_str[L], L + 1)
        if R == -1:
            continue

        statement_mut[L] = "{"
        statement_mut[R] = "}"

    return "".join(statement_mut)
