"""Unicode logo rendering and animation."""

from __future__ import annotations

import math
import os
from dataclasses import dataclass

from rich.style import Style
from rich.text import Text

from .logo_data import BADGE, BADGE_FINE

BRAND = "#0069a8"
BRAND_LIGHT = "#1e8fd6"
CYAN = "#38d3ff"
INK = "#cfe0f2" if os.environ.get("TV_THEME") != "light" else "#20334b"
DIM = "#7990ab" if os.environ.get("TV_THEME") != "light" else "#52677e"
OK = "#37e0a0"
GOLD = "#f5c97a"
DANGER = "#e0605c"
PURPLE = "#a877ff"
SLATE = "#2a3a52"


@dataclass(frozen=True)
class Geometry:
    """Bar positions in mask pixels; cell is pixels per character (width, height)."""
    mask: tuple[str, ...]
    cell: tuple[int, int]
    bar_columns: tuple[int, ...]
    bar_width: int
    bar_height: int
    check_tops: tuple[int, ...]   # the checkmark: 1 and 3 level, 2 low, 4 high
    rest_top: int                 # the loader's flat line, at rest
    lift: int                     # how far a dancing bar rises

    @property
    def flat_tops(self) -> tuple[int, ...]:
        return (self.rest_top,) * 4


# Half-blocks: one column and two rows of pixels per character.
BLOCKY = Geometry(BADGE, (1, 2), (1, 4, 7, 10), 2, 3, (6, 8, 6, 4), rest_top=7, lift=2)
# Sextants: two columns and three rows of pixels per character.
FINE = Geometry(BADGE_FINE, (2, 3), (1, 5, 9, 13), 3, 3, (5, 7, 5, 3), rest_top=6, lift=2)


def _sextants_drawn() -> bool:
    """Detect terminals that draw sextants without relying on font support."""
    choice = os.environ.get("TV_BADGE", "").lower()
    if choice in ("fine", "blocky"):
        return choice == "fine"
    term = os.environ.get("TERM", "")
    program = os.environ.get("TERM_PROGRAM", "").lower()
    return (term in ("xterm-kitty", "xterm-ghostty", "foot") or program in ("ghostty", "wezterm")
            or "KITTY_WINDOW_ID" in os.environ)


GEOMETRY = FINE if _sextants_drawn() else BLOCKY


def _mix(a: str, b: str, t: float) -> str:
    t = max(0.0, min(1.0, t))
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ca, cb, strict=True))


def _sextant(bits: int) -> str:
    """The sextant whose lit pixels are `bits` (1 2 / 4 8 / 16 32). Unicode
    skips the four that already exist as blocks: empty, ▌, ▐ and full."""
    if bits == 0:
        return " "
    if bits == 63:
        return "█"
    if bits == 21:
        return "▌"
    if bits == 42:
        return "▐"
    return chr(0x1FB00 + bits - 1 - (bits > 21) - (bits > 42))


def badge(tops=None, bars=("#ffffff",) * 4, ground: str = BRAND, g: Geometry | None = None) -> Text:
    """Draw the badge with its bars' top edges at `tops` (mask pixels)."""
    g = g or GEOMETRY
    tops = g.check_tops if tops is None else tops
    mask = g.mask

    def pixel(x: int, y: int) -> str | None:
        if y >= len(mask) or x >= len(mask[0]) or mask[y][x] != "#":
            return None
        for i, column in enumerate(g.bar_columns):
            top = round(tops[i])
            if column <= x < column + g.bar_width and top <= y < top + g.bar_height:
                return bars[i]
        return ground

    cw, ch = g.cell
    rows = (len(mask) + ch - 1) // ch
    cols = (len(mask[0]) + cw - 1) // cw
    text = Text(no_wrap=True, overflow="crop")
    for row in range(rows):
        for col in range(cols):
            pixels = [pixel(col * cw + dx, row * ch + dy) for dy in range(ch) for dx in range(cw)]
            colours = [c for c in dict.fromkeys(pixels) if c is not None]
            if not colours:
                text.append(" ")
                continue
            # Each glyph holds two colors; preserve transparency at the outline.
            if None in pixels or len(colours) == 1:
                fg, bg = max(colours, key=pixels.count), None
            else:
                bg, fg = sorted(colours, key=pixels.count, reverse=True)[:2]
            lit = [p == fg for p in pixels]
            if ch == 2:  # half-blocks
                glyph = {(True, True): "█", (True, False): "▀", (False, True): "▄", (False, False): " "}[tuple(lit)]
            else:
                glyph = _sextant(sum(1 << i for i, on in enumerate(lit) if on))
            text.append(glyph, Style(color=fg, bgcolor=bg))
        if row < rows - 1:
            text.append("\n")
    return text


PERIOD, STAGGER = 1.25, 0.14  # cycle length and per-bar delay, in seconds


def _bounce(t: float, bar: int) -> float:
    phase = ((t - bar * STAGGER) / PERIOD) % 1.0
    if phase < 0.4:
        return math.sin(phase / 0.4 * math.pi / 2)
    return math.cos((phase - 0.4) / 0.6 * math.pi / 2)


def dancing(t: float) -> Text:
    g = GEOMETRY
    lifts = [_bounce(t, bar) for bar in range(4)]
    tops = tuple(top - lift * g.lift for top, lift in zip(g.flat_tops, lifts, strict=True))
    bars = tuple(_mix("#6fb4e3", "#ffffff", lift) for lift in lifts)
    return badge(tops, bars)


def waiting_still() -> Text:
    """The loader with animation off: the flat line, at rest."""
    return badge(GEOMETRY.flat_tops, ("#cfe6f6",) * 4)


def settling(progress: float) -> Text:
    """Flat line into the checkmark, bars landing in an unordered sequence."""
    g = GEOMETRY
    order = (0.0, 0.35, 0.15, 0.5)
    tops = []
    for bar in range(4):
        local = max(0.0, min(1.0, (progress - order[bar]) / 0.5))
        eased = 1 - (1 - local) ** 3
        tops.append(g.flat_tops[bar] + (g.check_tops[bar] - g.flat_tops[bar]) * eased)
    return badge(tuple(tops))


def stopped() -> Text:
    return badge(GEOMETRY.flat_tops, (DIM,) * 4, SLATE)


# Left-column braille dots, from top to bottom.
_DOT_ROW = (0x01, 0x02, 0x04, 0x40)
_DOT_CHECK = (2, 3, 2, 1)   # 1 and 3 level, 2 low, 4 high, as in the logo
_DOT_FLAT = 2


def _dots(rows) -> str:
    return "".join(chr(0x2800 + _DOT_ROW[max(0, min(3, r))]) for r in rows)


def _hop(t: float, bar: int) -> int:
    """Hop briefly, then rest between cycles."""
    phase = ((t - bar * 0.12) / 1.0) % 1.0
    return round(math.sin(math.pi * phase / 0.36) * 2) if phase < 0.36 else 0


def inline_mark(t: float | None = None) -> str:
    """The checkmark in four dots; pass t for the loader's hop."""
    if t is None:
        return _dots(_DOT_CHECK)
    return _dots(_DOT_FLAT - _hop(t, bar) for bar in range(4))


BADGES = {
    "ok": ("[  OK  ]", OK),
    "wait": ("[ .... ]", CYAN),
    "code": ("[ CODE ]", GOLD),
    "info": ("[ INFO ]", BRAND_LIGHT),
    "fail": ("[ FAIL ]", DANGER),
}
