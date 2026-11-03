"""Edit a Word file the way a careful person would: change words, add comments, track the changes, and leave everything else as it was.

    word_edit.py <file.docx> '<request json>'

The request is one JSON object: ``{"author": "...", "edits": [ ... ]}``. ``author`` is who the comments and tracked changes are from (default
"Beacon"). Each edit is one of

    {"op": "replace", "find": "words as they read", "text": "the new words", "tracked": true, "comment": "why", "occurrence": 2}
    {"op": "comment", "find": "words as they read", "text": "the comment", "occurrence": 2}
    {"op": "insert_after", "find": "words in the paragraph to follow", "text": "new paragraph\\nanother", "tracked": true, "comment": "why"}

``tracked`` is always stated; ``comment`` and ``occurrence`` are optional. The edited file is written to ``$SKILL_OUTPUT_DIR`` under the supplied file's own name (a new version of it),
and only if every edit was made and every check passed: a refused run writes nothing. The run's own verification is printed.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

from redline.checks import Before, verify
from redline.comments import Comments
from redline.edits import Session, comment, insert_after, replace
from redline.ooxml import Refusal
from redline.package import Package

DEFAULT_AUTHOR = "Beacon"
MAX_EDITS = 60
MAX_TEXT = 20_000
_KEYS = {
    "replace": {"op", "find", "text", "tracked", "comment", "occurrence"},
    "comment": {"op", "find", "text", "occurrence"},
    "insert_after": {"op", "find", "text", "tracked", "comment", "occurrence"},
}
_REQUIRED = {"replace": {"find", "text", "tracked"}, "comment": {"find", "text"}, "insert_after": {"find", "text", "tracked"}}


def parse(raw: str) -> tuple[str, list[dict]]:
    try:
        request = json.loads(raw)
    except ValueError as bad:
        raise Refusal(f"The request is not valid JSON ({bad}). It is one object: {{\"author\": ..., \"edits\": [...]}}.") from bad
    if not isinstance(request, dict) or set(request) - {"author", "edits"} or not isinstance(request.get("edits"), list):
        raise Refusal('The request is one JSON object with "edits" (a list) and optionally "author".')
    author = request.get("author", DEFAULT_AUTHOR)
    if not isinstance(author, str) or not author.strip() or len(author) > 60:
        raise Refusal('"author" is the name the changes are from: 1 to 60 characters.')
    edits = request["edits"]
    if not 1 <= len(edits) <= MAX_EDITS:
        raise Refusal(f"A run makes 1 to {MAX_EDITS} edits.")
    for number, edit in enumerate(edits, 1):
        label = f"Edit {number}"
        if not isinstance(edit, dict) or edit.get("op") not in _KEYS:
            raise Refusal(f'{label}: "op" is one of {sorted(_KEYS)}.')
        op = edit["op"]
        if (unknown := set(edit) - _KEYS[op]):
            raise Refusal(f"{label}: a {op} edit has no {sorted(unknown)}; its fields are {sorted(_KEYS[op])}.")
        if (missing := _REQUIRED[op] - set(edit)):
            raise Refusal(f"{label}: a {op} edit needs {sorted(missing)}.")
        for name in ("find", "text", "comment"):
            if name in edit and (not isinstance(edit[name], str) or len(edit[name]) > MAX_TEXT):
                raise Refusal(f"{label}: {name} is text of at most {MAX_TEXT} characters.")
            if name in edit:
                edit[name] = edit[name].replace("\r\n", "\n").replace("\r", "\n")
        if not edit["find"].strip():
            raise Refusal(f"{label}: find needs the words to look for.")
        if "\n" in edit["find"]:
            raise Refusal(f"{label}: find is words within one paragraph; it cannot hold a line break.")
        if op != "replace" and not edit["text"].strip():
            raise Refusal(f"{label}: text needs words.")
        if "tracked" in edit and not isinstance(edit["tracked"], bool):
            raise Refusal(f'{label}: "tracked" is true or false.')
        if "comment" in edit and not edit["comment"].strip():
            raise Refusal(f"{label}: comment needs words, or leave it out.")
        if "occurrence" in edit and (not isinstance(edit["occurrence"], int) or isinstance(edit["occurrence"], bool) or edit["occurrence"] < 1):
            raise Refusal(f'{label}: "occurrence" is a whole number from 1.')
    return author.strip(), edits


def initials(author: str) -> str:
    return "".join(word[0] for word in re.findall(r"\w+", author))[:3].upper() or author[:1].upper()


def run(source: Path, raw: str) -> tuple[str, bytes, list[str]]:
    author, edits = parse(raw)
    package = Package(source.read_bytes())
    comments = Comments(package)
    before = Before(package, comments)
    package.touch(package.main)
    root = package.root(package.main)
    session = Session(root, comments, author, initials(author), datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                      package.highest_annotation_id())
    lines = []
    for number, edit in enumerate(edits, 1):
        try:
            if edit["op"] == "replace":
                said = replace(session, edit["find"], edit["text"], edit["tracked"], edit.get("comment"), edit.get("occurrence"))
            elif edit["op"] == "comment":
                said = comment(session, edit["find"], edit["text"], edit.get("occurrence"))
            else:
                said = insert_after(session, edit["find"], edit["text"], edit["tracked"], edit.get("comment"), edit.get("occurrence"))
        except Refusal as refused:
            raise Refusal(f"Edit {number} ({edit['op']}) was not made: {refused} Nothing was saved.") from refused
        lines.append(f"{number}. {edit['op']}: {said}")
    saved = package.save()
    if (problems := verify(package, before, session, saved)):
        raise Refusal("The edited file failed its checks, so nothing was saved: " + "; ".join(problems))
    made = ", ".join(f"{count} {name}" for name, count in session.made.items() if count) or "nothing"
    lines.append(f"Checked: opens in python-docx; {before.comment_count} earlier comment(s) and {len(before.revision_ids)} earlier tracked change(s) "
                 f"intact; every other part and paragraph unchanged. Added by {author}: {made}.")
    return source.name, saved, lines


def main(argv: list[str]) -> None:
    if len(argv) != 2:
        sys.exit("Usage: word_edit.py <file.docx> '<request json>'")
    try:
        name, data, lines = run(Path(argv[0]), argv[1])
    except Refusal as refused:
        sys.exit(str(refused))
    (Path(os.environ["SKILL_OUTPUT_DIR"]) / name).write_bytes(data)
    print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1:])
