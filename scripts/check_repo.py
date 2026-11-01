"""Repository sanity check: the marketplace lists every plugin folder, and each plugin and skill is well formed.

Standard library only. The Beacon contract (which tools a skill may name, size ceilings) is judged separately by
`.saphion/plugin_contract.py`; this checks the layout Claude Code reads. Prints each problem; exits 1 when there is one.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
FIELD = re.compile(r'^([A-Za-z][\w-]*):\s*(.*)$', re.MULTILINE)


def plugin_folders() -> list[Path]:
    return sorted(p.parent.parent for p in ROOT.glob("*/.claude-plugin/plugin.json"))


def load(path: Path, problems: list[str]) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        problems.append(f"{path.relative_to(ROOT)}: not valid JSON ({error}).")
        return {}
    if not isinstance(value, dict):
        problems.append(f"{path.relative_to(ROOT)}: must be a JSON object.")
        return {}
    return value


def check_skill(skill: Path, problems: list[str]) -> None:
    rel = skill.relative_to(ROOT)
    try:
        text = skill.read_text(encoding="utf-8")
    except UnicodeError:
        problems.append(f"{rel}: not UTF-8 text.")
        return
    match = FRONTMATTER.match(text)
    if not match:
        problems.append(f"{rel}: must open with a --- frontmatter block.")
        return
    fields = {key: value.strip().strip("\"'") for key, value in FIELD.findall(match.group(1))}
    if fields.get("name") != skill.parent.name:
        problems.append(f"{rel}: frontmatter name {fields.get('name')!r} must equal its folder {skill.parent.name!r}.")
    if not fields.get("description"):
        problems.append(f"{rel}: frontmatter needs a description.")
    if not text[match.end():].strip():
        problems.append(f"{rel}: the skill has no body.")


def main() -> int:
    problems: list[str] = []
    marketplace = load(ROOT / ".claude-plugin" / "marketplace.json", problems)
    if not marketplace.get("name") or not isinstance(marketplace.get("owner"), dict) or not marketplace["owner"].get("name"):
        problems.append(".claude-plugin/marketplace.json: needs name and owner.name.")
    listed = {}
    for entry in marketplace.get("plugins", []):
        listed[entry.get("name")] = entry
    folders = {folder.name: folder for folder in plugin_folders()}
    for name in sorted(set(folders) - set(listed)):
        problems.append(f"{name}: a plugin folder the marketplace does not list.")
    for name, entry in listed.items():
        folder = folders.get(name)
        if folder is None or entry.get("source") != f"./{name}":
            problems.append(f"marketplace plugin {name!r}: source must be './{name}' and hold .claude-plugin/plugin.json.")
            continue
        manifest = load(folder / ".claude-plugin" / "plugin.json", problems)
        for key in ("name", "version", "description"):
            if manifest.get(key) != entry.get(key):
                problems.append(f"{name}: marketplace {key} {entry.get(key)!r} differs from plugin.json {manifest.get(key)!r}.")
        skills = sorted(folder.glob("skills/*/SKILL.md"))
        if not skills:
            problems.append(f"{name}: no skills/<name>/SKILL.md.")
        for skill in skills:
            check_skill(skill, problems)
    for line in problems:
        print(line)
    if not problems:
        print(f"{len(folders)} plugins, marketplace and skills well formed.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
