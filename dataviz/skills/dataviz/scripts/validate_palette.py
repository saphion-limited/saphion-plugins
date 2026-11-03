"""Check chart colours before an app draws them: measured, never judged by eye.

    validate_palette.py "#hex,#hex,..." [--mode light|dark] [--surface #hex] [--kind categorical|ordinal|sequential|text]
                        [--pairs adjacent|all] [--band LOW,HIGH]

Run it once per mode, against the surface the chart really sits on (`references/palette.md` gives Saphion's, which are the defaults). The
colours are given in the order the app will assign them. Nothing is read or written: it prints one line per check and a verdict, last.

Kinds, and what each is checked for:

* categorical (default): series that are told apart by colour. Lightness inside the mode's band, enough chroma to read as a hue, colour-blind
  separation between neighbours (protanopia and deuteranopia simulated), separation under normal vision, contrast against the surface.
* ordinal: ordered categories (a funnel, size tiers) in one hue. Steps run one way in lightness, each visibly apart, one hue, and the
  palest step still shows on the surface.
* sequential: a magnitude ramp in one hue. Lightness runs one way and the hue holds. (A ramp spans the lightness band and its steps sit close,
  so judging it as categorical fails by design.)
* text: each colour is used as text on the surface and needs 4.5:1 (WCAG 2).

The verdict is the printed result, and the exit code is 0 whenever the checks ran: a palette that fails is an answer, not a crashed run.
A malformed colour or option exits 2 with the reason.

Three measures are used throughout. Lightness and chroma are OKLCH's. Difference is the straight distance between two colours in OKLab
times 100. Colour-blind vision is simulated with Machado, Oliveira and Fernandes (2009) at full severity; the limits below are calibrated
to that model, so it is part of the standard.
"""
from __future__ import annotations

import argparse
import math
import re
import sys
from dataclasses import dataclass

#: Saphion's surfaces (`references/palette.md`): the card a chart sits on, per mode.
SURFACE = {"light": "#ffffff", "dark": "#1d1d1c"}
#: OKLCH lightness a categorical mark may take, per mode. Dark is wider and lighter than the method's usual because Saphion's dark data
#: colours are one lighter set (`--color-night-label-*`); on the dark surface they all clear 3:1 by a wide margin, which is what the band protects.
BAND = {"light": (0.43, 0.77), "dark": (0.60, 0.80)}
CHROMA_FLOOR = 0.10
CVD_TARGET, CVD_FLOOR = 8.0, 6.0
NORMAL_FLOOR = 15.0
MARK_CONTRAST = 3.0
TEXT_CONTRAST = 4.5
ORDINAL_STEP, ORDINAL_PALE_CONTRAST, ONE_HUE_DEGREES = 0.06, 2.0, 40.0

_MACHADO = {
    "protanopia": ((0.152286, 1.052583, -0.204868), (0.114503, 0.786281, 0.099216), (-0.003882, -0.048116, 1.051998)),
    "deuteranopia": ((0.367322, 0.860646, -0.227968), (0.280085, 0.672501, 0.047413), (-0.011820, 0.042940, 0.968881)),
}
_HEX = re.compile(r"#[0-9a-fA-F]{6}")


@dataclass(frozen=True)
class Finding:
    name: str
    level: str  # "pass", "warn" (legal only with a second channel) or "fail"
    detail: str


# --- colour maths ---------------------------------------------------------------------------------------------------------------------

def linear(colour: str) -> tuple[float, float, float]:
    channels = (int(colour[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels)  # type: ignore[return-value]


def oklab(rgb: tuple[float, float, float]) -> tuple[float, float, float]:
    r, g, b = rgb
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def lightness_chroma_hue(colour: str) -> tuple[float, float, float]:
    lightness, a, b = oklab(linear(colour))
    return lightness, math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360


def difference(first: str, second: str, vision: str | None = None) -> float:
    def seen(colour: str) -> tuple[float, float, float]:
        rgb = linear(colour)
        if vision is None:
            return oklab(rgb)
        return oklab(tuple(min(1.0, max(0.0, sum(w * c for w, c in zip(row, rgb)))) for row in _MACHADO[vision]))  # type: ignore[arg-type]
    return 100 * math.dist(seen(first), seen(second))


def contrast(first: str, second: str) -> float:
    def luminance(colour: str) -> float:
        r, g, b = linear(colour)
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    high, low = sorted((luminance(first), luminance(second)), reverse=True)
    return (high + 0.05) / (low + 0.05)


# --- the checks -----------------------------------------------------------------------------------------------------------------------

def _pairs(count: int, scope: str) -> list[tuple[int, int]]:
    return [(i, j) for i in range(count) for j in range(i + 1, count)] if scope == "all" else [(i, i + 1) for i in range(count - 1)]


def categorical(colours: list[str], surface: str, band: tuple[float, float], scope: str) -> list[Finding]:
    found = []
    off = [f"{c} L{lightness_chroma_hue(c)[0]:.2f}" for c in colours if not band[0] <= lightness_chroma_hue(c)[0] <= band[1]]
    found.append(Finding("Lightness band", "fail" if off else "pass", f"outside {band[0]}-{band[1]}: {', '.join(off)}" if off else f"all {len(colours)} within {band[0]}-{band[1]}"))
    grey = [f"{c} C{lightness_chroma_hue(c)[1]:.3f}" for c in colours if lightness_chroma_hue(c)[1] < CHROMA_FLOOR]
    found.append(Finding("Chroma floor", "fail" if grey else "pass", f"reads as grey (under {CHROMA_FLOOR}): {', '.join(grey)}" if grey else f"all {len(colours)} at {CHROMA_FLOOR} or more"))
    pairs = _pairs(len(colours), scope)
    label = "all-pairs" if scope == "all" else "adjacent"
    if pairs:
        worst_cvd = min((difference(colours[i], colours[j], vision), vision, colours[i], colours[j]) for i, j in pairs for vision in _MACHADO)
        level = "pass" if worst_cvd[0] >= CVD_TARGET else "warn" if worst_cvd[0] >= CVD_FLOOR else "fail"
        found.append(Finding("Colour-blind separation", level,
                             f"worst pair ({label}) {worst_cvd[2]} / {worst_cvd[3]}: {worst_cvd[0]:.1f} ({worst_cvd[1]}); target {CVD_TARGET:g}, floor {CVD_FLOOR:g}"))
        worst_normal = min((difference(colours[i], colours[j]), colours[i], colours[j]) for i, j in pairs)
        found.append(Finding("Normal-vision floor", "pass" if worst_normal[0] >= NORMAL_FLOOR else "fail",
                             f"worst pair ({label}) {worst_normal[1]} / {worst_normal[2]}: {worst_normal[0]:.1f}; floor {NORMAL_FLOOR:g}"))
    weak = [f"{c} {contrast(c, surface):.2f}:1" for c in colours if contrast(c, surface) < MARK_CONTRAST]
    found.append(Finding("Contrast on surface", "warn" if weak else "pass",
                         f"under {MARK_CONTRAST:g}:1, so labels or a table must carry the value: {', '.join(weak)}" if weak else f"all {len(colours)} at {MARK_CONTRAST:g}:1 or more"))
    return found


def _steps(colours: list[str]) -> tuple[list[float], list[float]]:
    lightness = [lightness_chroma_hue(c)[0] for c in colours]
    return lightness, [b - a for a, b in zip(lightness, lightness[1:])]


def ramp(colours: list[str], surface: str, ordinal: bool) -> list[Finding]:
    lightness, gaps = _steps(colours)
    one_way = all(g > 0 for g in gaps) or all(g < 0 for g in gaps)
    found = [Finding("Lightness runs one way", "pass" if one_way else "fail",
                     "each step is lighter (or darker) than the last" if one_way else "out of order: " + ", ".join(f"{v:.2f}" for v in lightness))]
    hues = [h for _, c, h in map(lightness_chroma_hue, colours) if c >= 0.02]
    spread = max(((a - b + 180) % 360 - 180 for a in hues for b in hues), key=abs, default=0.0)
    found.append(Finding("One hue", "pass" if abs(spread) <= ONE_HUE_DEGREES else "fail", f"hue spread {abs(spread):.0f} degrees; limit {ONE_HUE_DEGREES:g}"))
    if ordinal:
        thin = [f"{colours[i]} / {colours[i + 1]} {abs(g):.3f}" for i, g in enumerate(gaps) if abs(g) < ORDINAL_STEP]
        found.append(Finding("Steps apart", "fail" if thin else "pass", f"under {ORDINAL_STEP} in lightness: {', '.join(thin)}" if thin else f"every step at {ORDINAL_STEP} or more"))
        pale = min(colours, key=lambda c: contrast(c, surface))
        found.append(Finding("Palest step on surface", "pass" if contrast(pale, surface) >= ORDINAL_PALE_CONTRAST else "fail",
                             f"{pale} at {contrast(pale, surface):.2f}:1; needs {ORDINAL_PALE_CONTRAST:g}:1"))
    return found


def text(colours: list[str], surface: str) -> list[Finding]:
    weak = [f"{c} {contrast(c, surface):.2f}:1" for c in colours if contrast(c, surface) < TEXT_CONTRAST]
    return [Finding("Text contrast", "fail" if weak else "pass", f"under {TEXT_CONTRAST:g}:1: {', '.join(weak)}" if weak else f"all {len(colours)} at {TEXT_CONTRAST:g}:1 or more")]


# --- the command ----------------------------------------------------------------------------------------------------------------------

def _hex_list(value: str) -> list[str]:
    colours = [part.strip().lower() for part in value.split(",") if part.strip()]
    bad = [c for c in colours if not _HEX.fullmatch(c)]
    if bad or not colours:
        raise SystemExit(f"Colours are written #rrggbb, separated by commas; not understood: {', '.join(bad) or 'none given'}.")
    return colours


def main(arguments: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="validate_palette.py", description="Check chart colours.")
    parser.add_argument("colours")
    parser.add_argument("--mode", choices=("light", "dark"), default="light")
    parser.add_argument("--surface")
    parser.add_argument("--kind", choices=("categorical", "ordinal", "sequential", "text"), default="categorical")
    parser.add_argument("--pairs", choices=("adjacent", "all"), default="adjacent")
    parser.add_argument("--band")
    try:
        options = parser.parse_args(arguments)
    except SystemExit as stop:
        return int(stop.code or 0)
    colours = _hex_list(options.colours)
    surface = _hex_list(options.surface)[0] if options.surface else SURFACE[options.mode]
    band = BAND[options.mode]
    if options.band:
        try:
            low, high = (float(part) for part in options.band.split(","))
        except ValueError:
            raise SystemExit("--band is two lightness values such as 0.43,0.77.")
        band = (low, high)
    findings = (text(colours, surface) if options.kind == "text" else ramp(colours, surface, options.kind == "ordinal") if options.kind in ("ordinal", "sequential")
                else categorical(colours, surface, band, options.pairs))
    print(f"{options.kind}, {options.mode}, surface {surface}, {len(colours)} colours")
    for item in findings:
        print(f"[{item.level.upper():4}] {item.name}: {item.detail}")
    failed = [item.name for item in findings if item.level == "fail"]
    warned = [item.name for item in findings if item.level == "warn"]
    print("FAILED: " + ", ".join(failed) + ". Change the colours (or the series count, or the chart form) and run again." if failed else
          "PASSED" + (f", with a second channel required for: {', '.join(warned)} (direct labels, gaps or a table)." if warned else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
