"""A PDF form's fields as a viewer fills them: listed with the values each accepts, filled by name, and read back from the written file.

Only AcroForm fields (what Acrobat, Preview and a browser fill) are handled. The library fills; this module decides what a field may hold, so a
value that would be silently dropped or stored in a form the viewer shows as empty is refused by field name before anything is written.
"""
import difflib
from dataclasses import dataclass, field

from pypdf import PdfWriter
from pypdf.generic import NameObject

from pdf_pages import refuse

READ_ONLY, MULTILINE, RADIO, PUSHBUTTON, COMBO, EDITABLE, MULTISELECT = 1, 1 << 12, 1 << 15, 1 << 16, 1 << 17, 1 << 18, 1 << 21
OFF = "/Off"


@dataclass
class FormField:
    name: str
    kind: str  # text, checkbox, radio, choice, button or signature
    pages: list[int] = field(default_factory=list)
    value: object = ""
    states: list[str] = field(default_factory=list)  # a checkbox's and a radio group's on-states, without the leading slash
    options: list[tuple[str, str]] = field(default_factory=list)  # a choice's (value, shown text)
    flags: int = 0
    max_length: int = 0
    widgets: list = field(default_factory=list)
    missing_appearance: bool = False  # a button widget that stores no appearances, so no state it could be set to

    @property
    def read_only(self) -> bool:
        return bool(self.flags & READ_ONLY)

    @property
    def settable(self) -> bool:
        """Whether a check box or radio group can be set: the PDF stores the appearance of each state on every widget (the library sets a
        button by choosing among them). A form that leaves them to the viewer, as one flagged NeedAppearances often does, has no state to set."""
        return bool(self.states) and not self.missing_appearance


def _inherited(node, key):
    while node is not None:
        if key in node:
            return node[key]
        node = node["/Parent"].get_object() if "/Parent" in node else None
    return None


def _field_node(widget):
    """The dictionary that holds the field's own value: the widget itself when it is named, else the parent that names it."""
    return widget if "/T" in widget or "/Parent" not in widget else widget["/Parent"]


def _qualified_name(widget) -> str:
    parts, node = [], widget
    while node is not None:
        if "/T" in node:
            parts.append(str(node["/T"]))
        node = node["/Parent"].get_object() if "/Parent" in node else None
    return ".".join(reversed(parts))


def _state_of(widget) -> str:
    return str(widget.get("/AS", OFF))


def _on_states(widget) -> list[str]:
    appearance = widget["/AP"] if "/AP" in widget else {}
    normal = appearance["/N"] if "/N" in appearance else {}
    return [str(key).lstrip("/") for key in normal.keys() if str(key) != OFF]


def _widgets_of(page) -> list:
    return [reference.get_object() for reference in (page["/Annots"] if "/Annots" in page else [])]


def has_xfa(reader) -> bool:
    root = reader.trailer["/Root"]
    return "/AcroForm" in root and "/XFA" in root["/AcroForm"].get_object()


def form_fields(reader) -> dict[str, FormField]:
    """Every named field of the form, in the order its first widget appears, with the page(s) it sits on."""
    found: dict[str, FormField] = {}
    for number, page in enumerate(reader.pages, 1):
        for widget in _widgets_of(page):
            name = _qualified_name(widget) if widget.get("/Subtype") == "/Widget" else ""
            if not name:
                continue
            kind_of, flags = _inherited(widget, "/FT"), int(_inherited(widget, "/Ff") or 0)
            kind = {"/Tx": "text", "/Sig": "signature"}.get(kind_of)
            if kind_of == "/Btn":
                kind = "button" if flags & PUSHBUTTON else "radio" if flags & RADIO else "checkbox"
            elif kind_of == "/Ch":
                kind = "choice"
            if kind is None:
                continue
            entry = found.setdefault(name, FormField(name, kind, flags=flags, max_length=int(_inherited(widget, "/MaxLen") or 0)))
            if number not in entry.pages:
                entry.pages.append(number)
            entry.widgets.append(widget)
            value = _inherited(_field_node(widget), "/V")
            if kind in ("checkbox", "radio"):
                entry.missing_appearance |= "/AP" not in widget or "/N" not in widget["/AP"]
                entry.states += [state for state in _on_states(widget) if state not in entry.states]
                entry.value = str(value).lstrip("/") if value is not None and str(value) != OFF else ""
            elif kind == "choice":
                entry.options = entry.options or [(str(item[0]), str(item[1])) if isinstance(item, list) else (str(item), str(item))
                                                  for item in (_inherited(widget, "/Opt") or [])]
                entry.value = [str(item) for item in value] if isinstance(value, list) else "" if value is None else str(value)
            elif kind == "text":
                entry.value = "" if value is None else str(value)
    return found


def _accepted(entry: FormField, given) -> tuple[object, str]:
    """The value to store for ``given`` and the reason it is refused (empty when it is accepted)."""
    name = entry.name
    if entry.read_only:
        return None, f"'{name}' is read only: the form does not let it be changed."
    if entry.kind in ("button", "signature"):
        return None, f"'{name}' is a {'push button' if entry.kind == 'button' else 'signature field'}, which this skill does not fill."
    if entry.kind == "text":
        if isinstance(given, bool) or not isinstance(given, (str, int)):
            return None, f"'{name}' takes text: give its value as a string, written as it should read."
        text = str(given)
        if entry.max_length and len(text) > entry.max_length:
            return None, f"'{name}' holds at most {entry.max_length} characters and the value has {len(text)}."
        if "\n" in text and not entry.flags & MULTILINE:
            return None, f"'{name}' is a single line and the value has a line break."
        return text, ""
    if entry.kind in ("checkbox", "radio") and not entry.settable:
        return None, (f"'{name}' stores no checked state in the PDF (its appearances are left to the viewer), "
                      f"so it cannot be {'ticked' if entry.kind == 'checkbox' else 'chosen'} here.")
    if entry.kind == "checkbox":
        if given is True:
            return "/" + entry.states[0], ""
        if given is False:
            return OFF, ""
        if isinstance(given, str) and given.lstrip("/") in entry.states:
            return "/" + given.lstrip("/"), ""
        return None, f"'{name}' is a check box: give true or false (its checked state is '{entry.states[0]}')."
    if entry.kind == "radio":
        if isinstance(given, str) and given.lstrip("/") in entry.states:
            return "/" + given.lstrip("/"), ""
        return None, f"'{name}' is a group of radio buttons: give one of {', '.join(repr(state) for state in entry.states)}."
    wanted = given if isinstance(given, list) else [given]
    chosen = []
    for item in wanted:
        if not isinstance(item, str):
            return None, f"'{name}' takes the text of one of its options."
        match = next((value for value, shown in entry.options if item == value), None) or next((value for value, shown in entry.options if item == shown), None)
        if match is None and not entry.flags & EDITABLE:
            return None, f"'{name}' has no option {item!r}: its options are {', '.join(repr(shown) for _, shown in entry.options)}."
        chosen.append(match if match is not None else item)
    if len(chosen) > 1 and not entry.flags & MULTISELECT:
        return None, f"'{name}' allows one choice and was given {len(chosen)}."
    return (chosen if entry.flags & MULTISELECT and isinstance(given, list) else chosen[0]), ""


def resolve_values(fields: dict[str, FormField], values: dict) -> dict:
    """Every value, checked against its field, or one refusal naming each one that cannot be filled (the unknown first, with the nearest names)."""
    problems, resolved = [], {}
    for name, given in values.items():
        if name not in fields:
            near = difflib.get_close_matches(name, list(fields), n=3, cutoff=0.4)
            problems.append(f"There is no field named '{name}'." + (f" Nearest: {', '.join(repr(item) for item in near)}." if near else ""))
            continue
        stored, reason = _accepted(fields[name], given)
        if reason:
            problems.append(reason)
        else:
            resolved[name] = stored
    if problems:
        shown = problems[:10] + ([f"... and {len(problems) - 10} more."] if len(problems) > 10 else [])
        raise refuse("\n".join(shown) + f"\nThis form has {len(fields)} fields; inspect_pdf.py lists them.")
    return resolved


def fill(reader, resolved: dict) -> PdfWriter:
    writer = PdfWriter(clone_from=reader)
    for page in writer.pages:
        if any(widget.get("/Subtype") == "/Widget" for widget in _widgets_of(page)):
            writer.update_page_form_field_values(page, resolved, auto_regenerate=False)
    # The library stores a button's value as text on the field and on each widget; the PDF holds it as a name on the field alone.
    for name, entry in form_fields(writer).items():
        if entry.kind in ("checkbox", "radio") and name in resolved:
            for widget in entry.widgets:
                node = _field_node(widget)
                if node is not widget:
                    widget.pop("/V", None)
                node[NameObject("/V")] = NameObject(resolved[name])
    return writer


def _held(entry: FormField):
    """What a field holds, comparable with what was asked of it."""
    return entry.value if isinstance(entry.value, list) else str(entry.value).replace("\r\n", "\n").replace("\r", "\n")


def read_back(written, before: dict[str, FormField], resolved: dict) -> list[str]:
    """What the written file does not hold: each asked field must hold its value and every other field exactly what it held."""
    after, problems = form_fields(written), []
    for name, entry in before.items():
        if name not in after:
            problems.append(f"'{name}' is missing from the written file.")
        elif name in resolved:
            wanted = resolved[name]
            if entry.kind in ("checkbox", "radio"):
                state = "" if wanted == OFF else wanted.lstrip("/")
                shown = [_state_of(widget).lstrip("/") for widget in after[name].widgets]
                if _held(after[name]) != state or (state and state not in shown) or (not state and any(item != "Off" for item in shown)):
                    problems.append(f"'{name}' holds {_held(after[name])!r} in the written file, not {state or 'unchecked'!r}.")
            elif _held(after[name]) != (wanted if isinstance(wanted, list) else wanted.replace("\r\n", "\n")):
                problems.append(f"'{name}' holds {_held(after[name])!r} in the written file, not {wanted!r}.")
        elif _held(after[name]) != _held(entry):
            problems.append(f"'{name}' was not asked for but changed from {_held(entry)!r} to {_held(after[name])!r}.")
    problems += [f"'{name}' is new in the written file." for name in after if name not in before]
    return problems
