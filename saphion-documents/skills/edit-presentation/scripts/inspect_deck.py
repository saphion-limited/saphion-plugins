"""List a template deck: its layouts and their placeholders, its slides, and what is already wrong on them.

    inspect_deck.py TEMPLATE.pptx [slides|layouts]

``TEMPLATE.pptx`` is the deck's issued file reference (it arrives as its path). The slides and the layouts are printed, or only the one named
when the whole is longer than the run shows (the last 2,000 characters). Nothing is written and nothing in the deck is changed. Use it before
``edit_deck.py`` to learn which layout to add and which placeholder number holds what.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))

from deck_fit import slide_findings
from deck_layouts import FURNITURE, kind_of, numbered_layouts, title_of
from pptx import Presentation

EMU = 914_400


def main(arguments: list[str]) -> None:
    if len(arguments) not in (1, 2) or (len(arguments) == 2 and arguments[1] not in ("slides", "layouts")):
        raise SystemExit("Usage: inspect_deck.py TEMPLATE.pptx [slides|layouts]")
    source = arguments[0]
    only = arguments[1] if len(arguments) == 2 else ""
    deck = Presentation(source)
    layouts = numbered_layouts(deck)
    summary = []
    for number, slide in enumerate(deck.slides, 1):
        found = slide_findings(slide, number, deck.slide_width, deck.slide_height)
        problems = [f"{finding.kind} ({finding.shape!r})" for finding in found]
        summary.append(f"{number:>3} {slide.slide_layout.name}: {title_of(slide)[:40]}" + (f"  !{'; '.join(problems)}" if problems else ""))
    if only != "layouts":
        print(f"Slides ({len(deck.slides)}; ! = found by measuring, 'not_measured' means check it in the render):")
        print("\n".join(summary) or "  none")
    if only != "slides":
        print(f"Size {deck.slide_width / EMU:.2f} x {deck.slide_height / EMU:.2f} in. Layouts ({len(layouts)}, {len(deck.slide_masters)} master(s)); "
              "placeholder number:kind WxH in (slide number, footer and date omitted):")
        for number, _, layout in layouts:
            print(f"{number:>3} {layout.name}: " + ", ".join(f"{shape.placeholder_format.idx}:{kind_of(shape)} {shape.width / EMU:.1f}x{shape.height / EMU:.1f}"
                                                             for shape in layout.placeholders
                                                             if shape.width is not None and shape.placeholder_format.type not in FURNITURE))


main(sys.argv[1:])
