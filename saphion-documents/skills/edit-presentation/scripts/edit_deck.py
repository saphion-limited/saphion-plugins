"""Edit a template deck: add slides on its own layouts, update the text of its slides, delete slides, and refuse a result that overflows.

    edit_deck.py TEMPLATE.pptx SPEC_JSON [OUTPUT.pptx]

``TEMPLATE.pptx`` is the deck's issued file reference (it arrives as its path). ``SPEC_JSON`` is one JSON text:

    {"slides": [
      {"update": 3, "set": {"title": "...", "1": ["first point", "second point"]}, "notes": "added to the notes it has"},
      {"update": 4, "replace_notes": "the notes it has are replaced: only when the person asked"},
      {"add": "Title and Content", "after": 3, "set": {"title": "...", "1": ["..."]}, "notes": "..."},
      {"delete": 6}
    ]}

Slide numbers are the template's own, whatever else is added or deleted. ``add`` names a layout of the deck (its name, or its number from
``inspect_deck.py``); the slide is placed after slide ``after`` (0 is the front; omitted is the end), in the order listed. ``set`` keys are
``title``, a placeholder number, or an exact shape name; a value is a text, or a list of paragraphs (a text, or ``{"text", "level"}``).
A slide's speaker notes are kept: ``notes`` on an update adds a paragraph after the notes it has, and only ``replace_notes`` replaces them.
The layouts, masters and theme are not touched. The deck is written to ``$SKILL_OUTPUT_DIR`` only if nothing on a slide that was added or updated
overflows its box, leaves the slide, or keeps sample wording; otherwise the script stops and says what, and writes nothing.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))

from deck_fit import slide_findings
from deck_layouts import (
    SpecError,
    carry_furniture,
    delete_slide,
    find_layout,
    find_shape,
    move_slide,
    remove_unfilled_placeholders,
    title_of,
    write_text,
)
from pptx import Presentation

KEYS = {"add": {"add", "after", "set", "notes"}, "update": {"update", "set", "notes", "replace_notes"}, "delete": {"delete"}}
SHOWN_FINDINGS = 12


def operations(text: str, count: int) -> list[dict]:
    try:
        spec = json.loads(text)
    except ValueError as failure:
        raise SpecError(f"The second argument is not JSON: {failure}") from failure
    slides = spec.get("slides") if isinstance(spec, dict) and set(spec) == {"slides"} else None
    if not isinstance(slides, list) or not slides:
        raise SpecError('The spec is {"slides": [ ...one operation each... ]}: each is an add, an update or a delete.')
    for number, op in enumerate(slides, 1):
        kinds = [kind for kind in KEYS if isinstance(op, dict) and kind in op]
        if len(kinds) != 1 or set(op) - KEYS[kinds[0]]:
            raise SpecError(f"Operation {number} must be exactly one of add, update or delete, with only its own keys "
                            f"({'; '.join(f'{kind}: {sorted(keys)}' for kind, keys in KEYS.items())}): {op!r}")
        kind = kinds[0]
        target = op["after"] if kind == "add" and "after" in op else op[kind] if kind != "add" else None
        if target is not None and (not isinstance(target, int) or isinstance(target, bool) or not (0 if kind == "add" else 1) <= target <= count):
            raise SpecError(f"Operation {number}: slide {target!r} is not one of the template's {count} slides"
                            f"{' (after: 0 is the front)' if kind == 'add' else ''}.")
        if not isinstance(op.get("set", {}), dict) or not all(isinstance(op.get(key, ""), str) for key in ("notes", "replace_notes")):
            raise SpecError(f"Operation {number}: set is an object of text by shape, notes and replace_notes are a text.")
        if "notes" in op and "replace_notes" in op:
            raise SpecError(f"Operation {number}: notes adds to the slide's notes and replace_notes replaces them: give one.")
    removed = [op["delete"] for op in slides if "delete" in op]
    clash = [op["update"] for op in slides if "update" in op and op["update"] in removed]
    if len(set(removed)) != len(removed) or clash:
        raise SpecError(f"A slide is deleted once and is not also updated (slide {(clash or removed)[0]}).")
    return slides


def main(arguments: list[str]) -> None:
    if len(arguments) not in (2, 3):
        raise SpecError("Usage: edit_deck.py TEMPLATE.pptx SPEC_JSON [OUTPUT.pptx]")
    source, text = arguments[0], arguments[1]
    output = arguments[2] if len(arguments) == 3 else os.path.basename(source)
    if not output.lower().endswith(".pptx") or os.sep in output:
        raise SpecError(f"The output is a plain file name ending .pptx, not {output!r}.")
    deck = Presentation(source)
    original = list(deck.slides)
    plan = operations(text, len(original))
    added, updated, tail, dropped = [], [], {}, []
    for op in plan:
        if "delete" in op:
            continue
        if "add" in op:
            layout = find_layout(deck, op["add"])
            after = op.get("after", len(original))
            anchor = tail.get(after) or (original[after - 1] if after else None)
            position = list(deck.slides).index(anchor) + 1 if anchor is not None else 0
            slide = deck.slides.add_slide(layout)
            added.append(slide)
            tail[after] = slide
            label = f"the new slide on {layout.name!r}"
        else:
            slide = original[op["update"] - 1]
            if slide not in updated:
                updated.append(slide)
            label = f"slide {op['update']}"
        for key, value in op.get("set", {}).items():
            write_text(find_shape(slide, label, key), value, label)
        if "replace_notes" in op:
            slide.notes_slide.notes_text_frame.text = op["replace_notes"]
        elif "notes" in op:
            frame = slide.notes_slide.notes_text_frame
            if frame.text.strip():
                frame.add_paragraph().text = op["notes"]
            else:
                frame.text = op["notes"]
        if "add" in op:
            dropped += [f"{shape} (slide on {layout.name!r})" for shape in remove_unfilled_placeholders(slide)]
            carry_furniture(slide, layout, original)
            move_slide(deck, slide, position)
    for op in plan:
        if "delete" in op:
            delete_slide(deck, original[op["delete"] - 1])
    findings = []
    slides = list(deck.slides)
    for number, slide in enumerate(slides, 1):
        findings += [(slide in added or slide in updated, finding) for finding in slide_findings(slide, number, deck.slide_width, deck.slide_height)]
    mine = [finding for touched, finding in findings if touched and finding.blocks]
    if mine:
        shown = "\n".join(f"- {finding}" for finding in mine[:SHOWN_FINDINGS])
        raise SystemExit(f"Nothing was written: {len(mine)} problem(s) on the slides you added or updated (numbers are the edited deck's).\n{shown}\n"
                         "Shorten the text, split it across slides, or choose a layout with a larger box, then run again.")
    path = os.path.join(os.environ["SKILL_OUTPUT_DIR"], output)
    deck.save(path)
    saved = Presentation(path)
    if len(saved.slides) != len(slides):
        raise SystemExit("The saved deck does not reopen with the slides it was given: nothing can be trusted.")
    for number, slide in enumerate(slides, 1):
        mark = "+" if slide in added else "~" if slide in updated else " "
        title = title_of(slide)
        print(f"{number:>3} {mark} {slide.slide_layout.name}: {title[:40]}{'...' if len(title) > 40 else ''}")
    old = [finding for touched, finding in findings if not touched and finding.blocks]
    check = [finding for touched, finding in findings if touched and not finding.blocks]
    print(f"Deck: {len(slides)} slides (template {len(original)}): {len(added)} added (+), {len(updated)} updated (~), "
          f"{sum('delete' in op for op in plan)} deleted.")
    print(f"Measured every slide: no overflow, off-slide shape or sample wording on the {len(added) + len(updated)} you changed.")
    for line in ([f"Unfilled placeholders dropped: {', '.join(dropped)}."] if dropped else []):
        print(line)
    for finding in check:
        print(f"Check in the render: {finding}")
    for finding in old[:SHOWN_FINDINGS]:
        print(f"Already in the template, untouched: {finding}")
    print(f"Next: read every page of {output} (read, with `at` 1-6, 7-12, ...) and look at each slide before saying it is ready.")


try:
    main(sys.argv[1:])
except SpecError as refusal:
    raise SystemExit(str(refusal)) from refusal
