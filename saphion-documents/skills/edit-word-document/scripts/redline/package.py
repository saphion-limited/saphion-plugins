"""A .docx as a zip of parts. Only the parts an edit changes are rewritten; every other part is copied byte for byte, so styles,
numbering, settings, themes, headers, footers, notes, media and every custom part of the person's file come back exactly as they went in."""
from __future__ import annotations

import io
import posixpath
import re
import zipfile

from lxml import etree

from .ooxml import Refusal

MAIN_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
COMMENTS_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"
REL_BASE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
PACKAGE_RELS = "http://schemas.openxmlformats.org/package/2006/relationships"
CONTENT_TYPES = "http://schemas.openxmlformats.org/package/2006/content-types"
MAX_PARTS = 2_000
MAX_UNPACKED_BYTES = 200 * 1024 * 1024
#: Entities are never expanded and nothing is fetched: the file comes from someone else.
_PARSER = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False, huge_tree=False)


def _rels_name(part: str) -> str:
    folder, name = posixpath.split(part)
    return posixpath.join(folder, "_rels", name + ".rels")


class Package:
    def __init__(self, data: bytes) -> None:
        try:
            archive = zipfile.ZipFile(io.BytesIO(data))
        except zipfile.BadZipFile as bad:
            raise Refusal("This is not a .docx file: it is not a zip archive.") from bad
        infos = archive.infolist()
        if len(infos) > MAX_PARTS or sum(info.file_size for info in infos) > MAX_UNPACKED_BYTES:
            raise Refusal("This file unpacks to more than the sandbox edits: it has too many parts or is too large.")
        self._infos = infos
        self._original = {info.filename: archive.read(info) for info in infos if not info.is_dir()}
        self._trees: dict[str, etree._ElementTree] = {}
        self._changed: set[str] = set()
        self._added: dict[str, bytes] = {}
        if "[Content_Types].xml" not in self._original or "_rels/.rels" not in self._original:
            raise Refusal("This is not a Word file: it has no [Content_Types].xml and package relationships.")
        self.main = self._main_part()

    # --- reading -------------------------------------------------------------------------------------------------------------------

    def has(self, name: str) -> bool:
        return name in self._original or name in self._added

    def raw(self, name: str) -> bytes:
        return self._added.get(name) or self._original[name]

    def names(self) -> list[str]:
        return [*self._original, *self._added]

    def tree(self, name: str) -> etree._ElementTree:
        if name not in self._trees:
            try:
                self._trees[name] = etree.ElementTree(etree.fromstring(self.raw(name), _PARSER))
            except etree.XMLSyntaxError as bad:
                raise Refusal(f"The part {name} of this file is not valid XML ({bad}).") from bad
        return self._trees[name]

    def root(self, name: str):
        return self.tree(name).getroot()

    def touch(self, name: str) -> None:
        """The part is edited: it is written back from its tree. A part never touched is written from its original bytes."""
        self.tree(name)
        self._changed.add(name)

    # --- structure -----------------------------------------------------------------------------------------------------------------

    def _target(self, source_part: str, target: str) -> str:
        return target.lstrip("/") if target.startswith("/") else posixpath.normpath(posixpath.join(posixpath.dirname(source_part), target))

    def _related(self, rels_part: str, source_part: str, kind: str) -> list[str]:
        if not self.has(rels_part):
            return []
        return [self._target(source_part, rel.get("Target", "")) for rel in self.root(rels_part)
                if rel.get("Type") == REL_BASE + kind and rel.get("TargetMode") != "External"]

    @property
    def main_rels(self) -> str:
        return _rels_name(self.main)

    def related(self, kind: str) -> list[str]:
        """The parts the main document part relates to as ``kind`` (``styles``, ``comments``, ...)."""
        return self._related(self.main_rels, self.main, kind)

    def _main_part(self) -> str:
        mains = self._related("_rels/.rels", "", "officeDocument")
        if len(mains) != 1 or not self.has(mains[0]):
            raise Refusal("This is not a Word file: its package names no main document part.")
        declared = {
            (override.get("PartName") or "").lstrip("/"): override.get("ContentType")
            for override in self.root("[Content_Types].xml") if etree.QName(override).localname == "Override"
        }
        if declared.get(mains[0]) != MAIN_TYPE:
            raise Refusal("Only an ordinary Word document (.docx) is edited here: a template, a macro-enabled file or a strict-format file is not.")
        return mains[0]

    def comments_part(self) -> str:
        """The comments part, made (with its relationship and content type) when the file has none."""
        found = self.related("comments")
        if found:
            return found[0]
        name = posixpath.join(posixpath.dirname(self.main), "comments.xml")
        if self.has(name):
            raise Refusal(f"This file holds {name} but the document does not relate to it as its comments.")
        from .ooxml import W
        self._added[name] = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:comments xmlns:w="{W}"/>').encode()
        self._trees.pop(name, None)
        self._changed.add(name)
        rels = self.main_rels
        if not self.has(rels):
            self._added[rels] = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="{PACKAGE_RELS}"/>').encode()
        self.touch(rels)
        taken = {rel.get("Id") for rel in self.root(rels)}
        number = 1
        while f"rId{number}" in taken:
            number += 1
        etree.SubElement(self.root(rels), f"{{{PACKAGE_RELS}}}Relationship", Id=f"rId{number}", Type=REL_BASE + "comments",
                         Target=posixpath.relpath(name, posixpath.dirname(self.main)))
        self.touch("[Content_Types].xml")
        etree.SubElement(self.root("[Content_Types].xml"), f"{{{CONTENT_TYPES}}}Override", PartName="/" + name, ContentType=COMMENTS_TYPE)
        return name

    def highest_annotation_id(self) -> int:
        """The highest ``w:id`` any word part holds, so a new revision or comment never repeats one (ids are read from the bytes, as Word writes them)."""
        found = [int(value) for name in self.names() if name.startswith(posixpath.dirname(self.main) + "/") and name.endswith(".xml")
                 for value in re.findall(rb'\bw:id="(-?\d+)"', self.raw(name))]
        return max(found, default=0)

    # --- writing -------------------------------------------------------------------------------------------------------------------

    def changed_parts(self) -> set[str]:
        return set(self._changed)

    def _serialised(self, name: str) -> bytes:
        tree = self.tree(name)
        return etree.tostring(tree, xml_declaration=True, encoding="UTF-8", standalone=tree.docinfo.standalone)

    def save(self) -> bytes:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as out:
            for info in self._infos:
                copy = zipfile.ZipInfo(info.filename, date_time=info.date_time)
                copy.compress_type, copy.external_attr, copy.create_system = zipfile.ZIP_DEFLATED, info.external_attr, info.create_system
                out.writestr(copy, b"" if info.is_dir() else self._serialised(info.filename) if info.filename in self._changed
                             else self._original[info.filename])
            for name in self._added:
                out.writestr(zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0)), self._serialised(name), zipfile.ZIP_DEFLATED)
        return buffer.getvalue()

    def unchanged_bytes_kept(self, saved: bytes) -> list[str]:
        """The parts of ``saved`` that differ from the original but were never edited: always empty, and checked because it is the claim."""
        with zipfile.ZipFile(io.BytesIO(saved)) as written:
            return [name for name, data in self._original.items()
                    if name not in self._changed and written.read(name) != data]
