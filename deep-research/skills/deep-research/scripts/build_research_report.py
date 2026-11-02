"""Check a research report's citations and hand the verified report back, with a bundle of it and its source list.

    build_research_report.py "<the report's Markdown>" ["<file name without extension>"]

The Markdown cites a source only by the citation Beacon writes after a sentence. Before this script runs, the host has resolved each
citation from the sources the conversation actually found or read, and replaced it with the source's number (between the private-use
characters ``OPEN`` and ``CLOSE``); the sources arrive in ``cited_sources.json`` with the name, publisher, date and address the host holds for
each. The script is handed no address, title or source from the model, builds none, and refuses any it finds in the text (a link, an image, a
typed web address). The sandbox has no network and nothing here reads one.

It writes nothing, and names every fault, unless all of these hold:

* a title (`# `), then the sections in `##` and `###`; no Sources section (the host adds it from what was cited);
* every sentence of a finding carries a citation, and so does every list item, every body row of a table and every table cell that holds a
  figure. The findings are every section except `What this means`, `Method` and `What could not be established` (and what sits under them);
* the findings cite at least one source: a report nothing was read for is not written.

It never styles a file. It writes `<name>.docx.md`, the VERIFIED Markdown of the report, and `<name>-bundle.zip` holding that and
`sources.md`; the host renders the Markdown into the Word file in the Organisation's own document design, with the numbers as links and the
Sources list, and delivers both, only because the script finished.
"""
from __future__ import annotations

import json
import os
import re
import sys
import zipfile
from collections import Counter


#: The host's own bounds of a citation in text (``web_research.citations``); a sandbox script cannot import them.
OPEN, CLOSE = "\ue000", "\ue001"
SOURCES_FILE = "cited_sources.json"
#: Sections that state no finding. Their text still has no web address or link; it needs no citation.
NO_FINDING = ("what this means", "method", "what could not be established")
RUN = re.compile(rf"((?:\s*{OPEN}\d+{CLOSE})+)|\*\*(.+?)\*\*|\*(.+?)\*")
TOKEN = re.compile(rf"{OPEN}(\d+){CLOSE}")
SENTENCE_END = re.compile(rf"(?<=[.!?])((?:\s*{OPEN}\d+{CLOSE})*)(?=\s|$)")
FORBIDDEN = (
    (re.compile(r"\]\("), "a Markdown link"), (re.compile(r"!\["), "an image"),
    (re.compile(r"(?i)\b(?:https?://|www\.)"), "a typed web address"))


def blocks(markdown: str) -> list[tuple]:
    """The report as ``(kind, ...)`` blocks: heading (level, text), para, bullet, number (text), table (rows)."""
    found, paragraph, lines = [], [], markdown.splitlines()

    def flush() -> None:
        if paragraph:
            found.append(("para", " ".join(paragraph)))
            paragraph.clear()

    at = 0
    while at < len(lines):
        line = lines[at].strip()
        at += 1
        if not line:
            flush()
        elif heading := re.match(r"^(#{1,6})\s+(.+)$", line):
            flush()
            found.append(("heading", len(heading.group(1)), heading.group(2).strip()))
        elif item := re.match(r"^[-*]\s+(.+)$", line):
            flush()
            found.append(("bullet", item.group(1)))
        elif item := re.match(r"^\d+[.)]\s+(.+)$", line):
            flush()
            found.append(("number", item.group(1)))
        elif line.startswith("|"):
            flush()
            rows = [line]
            while at < len(lines) and lines[at].strip().startswith("|"):
                rows.append(lines[at].strip())
                at += 1
            cells = [[cell.strip() for cell in row.strip("|").split("|")] for row in rows]
            found.append(("table", [row for row in cells if not all(re.fullmatch(r":?-{2,}:?", cell) for cell in row)]))
        else:
            paragraph.append(line)
    flush()
    return found


def judge(parts: list[tuple], sources: list[dict]) -> tuple[list[str], dict]:
    faults, cited, units, alone = [], Counter(), 0, 0
    title = next((part for part in parts if part[0] == "heading"), None)
    if title is None or title[1] != 1:
        faults.append("The report starts with its title as a `# ` heading.")
    stack: list[tuple[int, str]] = []
    for part in parts:
        if part[0] == "heading":
            if part[1] > 3:
                faults.append(f"Headings go to three levels (`{part[2][:40]}`).")
            while stack and stack[-1][0] >= part[1]:
                stack.pop()
            stack.append((part[1], part[2].lower()))
            if part[2].strip().lower() == "sources":
                faults.append("Leave out the Sources section: it is added from the sources you cited.")
            continue
        texts = [part[1]] if part[0] != "table" else [cell for row in part[1] for cell in row]
        for text in texts:
            for found, what in FORBIDDEN:
                if found.search(text):
                    faults.append(f"{what} in \"{TOKEN.sub('', text)[:50]}\": cite a source with its citation, never by writing its address.")
        if any(name in NO_FINDING for _, name in stack):
            continue
        if part[0] == "table":
            for number, row in enumerate(part[1][1:], start=1):
                row_cited = sorted({int(n) for cell in row for n in TOKEN.findall(cell)})
                if not row_cited:
                    faults.append(f"Table row {number} carries no source: \"{TOKEN.sub('', ' | '.join(row))[:60]}\".")
                for cell in row:
                    if re.search(r"\d", TOKEN.sub("", cell)) and not TOKEN.search(cell):
                        faults.append(f"A figure carries no source: \"{cell[:40]}\" (cite it in its own cell).")
                cited.update(row_cited)
                units += 1
                alone += len(row_cited) == 1
            continue
        for sentence in sentences(part[1]):
            marks = sorted({int(n) for n in TOKEN.findall(sentence)})
            if not marks:
                faults.append(f"A finding carries no source: \"{sentence[:70]}\" (cite it, or move it to What could not be established).")
            cited.update(marks)
            units += 1
            alone += len(marks) == 1
    if not cited and not faults:
        faults.append("Nothing in the findings cites a source this conversation read: a report is not written without one. "
                      "Say plainly in your reply what was searched and why it did not answer the question.")
    unknown = sorted(n for n in cited if not 1 <= n <= len(sources))
    if unknown:
        faults.append(f"Citation {unknown[0]} names no source the host resolved.")
    return faults, {"units": units, "alone": alone, "cited": len(cited)}


#: Abbreviations whose full stop never ends a sentence, even before a capital (``e.g. The``, ``Dr. Jones``).
ABBREVIATIONS = ("e.g", "i.e", "nos", "vs", "cf", "approx", "mr", "mrs", "ms", "dr", "st", "fig", "figs", "reg", "regs", "para", "paras", "art",
                 "sec", "ref", "est", "viz")
WORD_BEFORE = re.compile(r"([A-Za-z]+(?:\.[A-Za-z]+)*)\.$")


def sentences(text: str) -> list[str]:
    """One finding's sentences, each with the citations written after its full stop. A full stop does not end a sentence when a lowercase
    letter or a digit follows (9 a.m. the, the U.K. and, c. 1900, No. 4, Ltd. requires, etc. are), nor after a named abbreviation before a
    capital (e.g. The, Dr. Jones)."""
    found, start = [], 0
    for end in SENTENCE_END.finditer(text):
        if text[end.start() - 1] == ".":
            word = WORD_BEFORE.search(text[:end.start()])
            following = text[end.end():].lstrip()
            if following[:1].islower() or following[:1].isdigit() or (word and word.group(1).lower() in ABBREVIATIONS):
                continue
        found.append(text[start:end.end()])
        start = end.end()
    found.append(text[start:])
    return [sentence.strip() for sentence in found if sentence.strip()]


def entry(source: dict) -> str:
    by = ", ".join(part for part in (source["publisher"], source["published"]) if part)
    return source["name"] + (f" ({by})" if by else "")


def sources_list(sources: list[dict]) -> str:
    lines = ["# Sources", ""]
    for n, source in enumerate(sources, start=1):
        lines += [f"{n}. {entry(source)}", f"   Address: {source['address']}" if source["address"] else "   A record held in Saphion.", ""]
    return "\n".join(lines)


def main(arguments: list[str]) -> int:
    if len(arguments) not in (1, 2):
        sys.exit('Usage: build_research_report.py "<the report\'s Markdown>" ["<file name>"]')
    if not os.path.exists(SOURCES_FILE):
        sys.exit("Nothing was written: the report cites no source, so there is nothing it was researched from. A report is not written without one.")
    with open(SOURCES_FILE, encoding="utf-8") as held:
        sources = json.load(held)
    parts = blocks(arguments[0])
    faults, summary = judge(parts, sources)
    if faults:
        sys.exit("Nothing was written. Fix these and run it again:\n- " + "\n- ".join(faults))
    title = next(part[2] for part in parts if part[0] == "heading")
    stem = arguments[1] if len(arguments) == 2 else re.sub(r"\s+", " ", re.sub(r"[^A-Za-z0-9 _-]+", "", title)).strip()[:80] or "Research report"
    if re.search(r"[/\\:]", stem) or stem.startswith("."):
        sys.exit(f"The file name must be plain text (got {stem!r}).")
    out = os.environ["SKILL_OUTPUT_DIR"]
    document = f"{stem}.docx.md"
    with open(os.path.join(out, document), "w", encoding="utf-8") as written:
        written.write(arguments[0].strip() + "\n")
    with zipfile.ZipFile(os.path.join(out, f"{stem}-bundle.zip"), "w", zipfile.ZIP_DEFLATED) as bundle:
        bundle.write(os.path.join(out, document), document)
        bundle.writestr("sources.md", sources_list(sources))
    print(f"Verified {stem}: {len(sources)} sources cited; {summary['units']} cited sentences, items and rows, {summary['alone']} of them "
          "resting on one source. The Word file and the bundle are written when this run ends.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
