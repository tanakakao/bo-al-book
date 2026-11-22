"""Build the Quarto index from the term table and the chapter's section labels."""

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "editorial/index-terms.tsv"
DESTINATION = ROOT / "appendices/term-index.qmd"
HEADING = re.compile(r"^#{2,3} ([0-9]+\.[0-9]+) .+ \{#([a-z0-9-]+)\}$", re.M)
PDF_TARGET = r"\label{ix-"


def section_map():
    result = {}
    for chapter in sorted((ROOT / "chapters").glob("*.qmd")):
        text = chapter.read_text(encoding="utf-8")
        for number, identifier in HEADING.findall(text):
            if PDF_TARGET + identifier + "}" in text:
                if number in result:
                    raise ValueError(f"Duplicate section number {number}")
                result[number] = (chapter.name, identifier)
    return result


def read_terms():
    sections = section_map()
    groups = defaultdict(list)
    with SOURCE.open(encoding="utf-8", newline="") as stream:
        for group, term, targets in csv.reader(stream, delimiter="\t"):
            refs = [(number, *sections[number]) for number in targets.split(";")]
            if any(other == term for entries in groups.values() for other, _ in entries):
                raise ValueError(f"Duplicate index entry {term}")
            groups[group].append((term, refs))
    return groups


def render(groups):
    lines = [
        "# 索引 {-}",
        "",
        "節番号から本文へ移動できます。PDFでは、括弧内に本文のページ番号を示します。",
        "",
    ]
    for group, terms in groups.items():
        lines += [f"## {group}", "", '::: {.content-visible when-format="html"}', "", "| 用語 | 節 |", "|---|---|"]
        for term, refs in terms:
            links = "、".join(
                f"[{number}節](../chapters/{source}#{anchor})"
                for number, source, anchor in refs
            )
            lines.append(f"| {term} | {links} |")
        lines += [
            "", ":::", "", "~~~{=latex}",
            r"\begin{longtable}{@{}p{0.43\linewidth}p{0.53\linewidth}@{}}",
            r"\toprule 用語 & 節（ページ） \\ \midrule",
            r"\endfirsthead",
            r"\toprule 用語 & 節（ページ） \\ \midrule",
            r"\endhead",
            r"\bottomrule",
            r"\endfoot",
        ]
        for term, refs in terms:
            links = "、".join(
                rf"\hyperref[ix-{anchor}]{{{number}節（\pageref*{{ix-{anchor}}}）}}"
                for number, _, anchor in refs
            )
            lines.append(rf"{term} & {links} \\")
        lines += [r"\end{longtable}", "~~~", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    book_index = render(read_terms())
    if args.check:
        if DESTINATION.read_text(encoding="utf-8") != book_index:
            raise SystemExit("Rebuild the book index with scripts/build_index.py.")
    else:
        DESTINATION.write_text(book_index, encoding="utf-8")


if __name__ == "__main__":
    main()
