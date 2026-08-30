"""Shared Editorial Index and Catppuccin color contracts.

The bundled Catppuccin data is a pinned, hex-only snapshot of the official
palette. Raw swatches remain exact; semantic text and focus roles are derived
only when contrast would otherwise be insufficient.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Mapping


_HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")
_DATA_PATH = Path(__file__).with_name("catppuccin.json")

COLOR_THEMES = ("editorial", "catppuccin")
CATPPUCCIN_AUTO = "auto"


def _load_catppuccin_data() -> dict[str, Any]:
    data = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    token_order = tuple(data.get("token_order", ()))
    accent_order = tuple(data.get("accent_order", ()))
    flavors = data.get("flavors", {})
    if data.get("source_version") != "1.8.0":
        raise ValueError("unexpected Catppuccin palette version")
    if len(token_order) != 26 or len(accent_order) != 14:
        raise ValueError("Catppuccin palette token contract is incomplete")
    if tuple(flavors) != ("latte", "frappe", "macchiato", "mocha"):
        raise ValueError("unexpected Catppuccin flavor order")
    for flavor_name, flavor in flavors.items():
        values = flavor.get("hex", ())
        if len(values) != len(token_order):
            raise ValueError(f"Catppuccin {flavor_name} token count mismatch")
        if not all(isinstance(value, str) and _HEX_COLOR.fullmatch(value) for value in values):
            raise ValueError(f"Catppuccin {flavor_name} contains an invalid color")
    return data


CATPPUCCIN_DATA = _load_catppuccin_data()
CATPPUCCIN_TOKEN_ORDER = tuple(CATPPUCCIN_DATA["token_order"])
CATPPUCCIN_ACCENTS = tuple(CATPPUCCIN_DATA["accent_order"])
CATPPUCCIN_FLAVORS = tuple(CATPPUCCIN_DATA["flavors"])
CATPPUCCIN_FLAVOR_OPTIONS = (CATPPUCCIN_AUTO, *CATPPUCCIN_FLAVORS)


def _normalized_hex(value: object, fallback: str) -> str:
    candidate = str(value)
    return candidate.upper() if _HEX_COLOR.fullmatch(candidate) else fallback.upper()


def _mix_hex(source: str, target: str, target_weight: float) -> str:
    """Mix two #RRGGBB colors without a GUI dependency."""

    try:
        source_channels = [int(source[index : index + 2], 16) for index in (1, 3, 5)]
        target_channels = [int(target[index : index + 2], 16) for index in (1, 3, 5)]
    except (TypeError, ValueError):
        return source

    weight = min(1.0, max(0.0, target_weight))
    mixed = [
        round(source_channel * (1 - weight) + target_channel * weight)
        for source_channel, target_channel in zip(source_channels, target_channels)
    ]
    return "#" + "".join(f"{channel:02X}" for channel in mixed)


def _relative_luminance(color: str) -> float:
    channels = [int(color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [
        channel / 12.92
        if channel <= 0.04045
        else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(foreground: str, background: str) -> float:
    lighter = max(_relative_luminance(foreground), _relative_luminance(background))
    darker = min(_relative_luminance(foreground), _relative_luminance(background))
    return (lighter + 0.05) / (darker + 0.05)


def _ensure_contrast(
    color: str,
    backgrounds: tuple[str, ...],
    target: float,
    toward: str,
) -> str:
    if min(contrast_ratio(color, background) for background in backgrounds) >= target:
        return color.upper()
    for step in range(1, 101):
        candidate = _mix_hex(color, toward, step / 100)
        if min(contrast_ratio(candidate, background) for background in backgrounds) >= target:
            return candidate
    return toward.upper()


def _best_contrast_text(
    backgrounds: tuple[str, ...], candidates: tuple[str, ...]
) -> str:
    ranked = sorted(
        candidates,
        key=lambda candidate: min(
            contrast_ratio(candidate, background) for background in backgrounds
        ),
        reverse=True,
    )
    return ranked[0].upper()


def _first_contrasting_color(
    background: str, candidates: tuple[str, ...], target: float = 3.5
) -> str:
    """Prefer semantic colors, falling back to black/white only when needed."""

    for candidate in candidates:
        if contrast_ratio(candidate, background) >= target:
            return candidate.upper()
    return _best_contrast_text((background,), candidates)


def _contrast_text(background: str) -> str:
    """Compatibility helper for callers that need a black/white decision."""

    return _best_contrast_text((background,), ("#1D1D1B", "#FFFFFF"))


def catppuccin_palette(flavor: str) -> dict[str, str]:
    resolved = flavor if flavor in CATPPUCCIN_FLAVORS else "latte"
    values = CATPPUCCIN_DATA["flavors"][resolved]["hex"]
    return {
        name: value.upper()
        for name, value in zip(CATPPUCCIN_TOKEN_ORDER, values)
    }


def catppuccin_color(flavor: str, color_name: str) -> str:
    palette = catppuccin_palette(flavor)
    return palette.get(color_name, palette["blue"])


def normalize_color_theme(value: object) -> str:
    candidate = str(value).strip().lower()
    return candidate if candidate in COLOR_THEMES else "editorial"


def normalize_catppuccin_flavor(value: object) -> str:
    candidate = str(value).strip().lower()
    return candidate if candidate in CATPPUCCIN_FLAVOR_OPTIONS else CATPPUCCIN_AUTO


def normalize_catppuccin_accent(value: object) -> str:
    candidate = str(value).strip().lower()
    return candidate if candidate in CATPPUCCIN_ACCENTS else "blue"


@dataclass(frozen=True)
class ColorTokens:
    family: str
    flavor: str
    dark: bool
    accent_name: str
    accent_raw: str
    accent: str
    accent_text: str
    focus: str
    link: str
    cursor: str
    accent_hover: str
    accent_pressed: str
    accent_soft: str
    canvas: str
    surface: str
    crust: str
    raised: str
    field: str
    text: str
    label: str
    muted: str
    faint: str
    border: str
    border_strong: str
    hover: str
    selection: str
    disabled: str
    danger: str
    danger_text: str
    on_accent: str
    on_danger: str
    new: str
    learn: str
    due: str
    good: str
    easy: str
    palette: Mapping[str, str]


def _semantic_text(color: str, tokens: tuple[str, ...], text: str) -> str:
    return _ensure_contrast(color, tokens, 4.5, text)


def _chromatic_text(
    color: str,
    backgrounds: tuple[str, ...],
    target: float,
    dark: bool,
) -> str:
    """Make a Catppuccin swatch readable without washing it into blue-grey.

    Catppuccin's ``text`` token is deliberately purple-grey. Mixing a pale
    Latte accent toward it can rotate the accent hue by more than 90 degrees
    and collapse its saturation. Black/white are neutral endpoints, so this
    adjustment preserves the source hue while meeting the product contrast
    contract. Raw palette values remain untouched in ``tokens.palette``.
    """

    return _ensure_contrast(
        color,
        backgrounds,
        target,
        "#FFFFFF" if dark else "#000000",
    )


def _editorial_tokens(accent_value: object, system_dark: bool) -> ColorTokens:
    user_accent = _normalized_hex(accent_value, "#2F5BBC")
    accent = _mix_hex(user_accent, "#FFFFFF", 0.35) if system_dark else user_accent
    if system_dark:
        canvas = "#1B1916"
        surface = "#221F1A"
        raised = "#2B2721"
        field = "#27231E"
        text = "#F1EADF"
        muted = "#B3AB9E"
        faint = "#80786D"
        border = "#514A40"
        border_strong = "#71685B"
        disabled_seed = "#8F877C"
        accent_hover = _mix_hex(accent, "#FFFFFF", 0.14)
        accent_pressed = _mix_hex(accent, "#000000", 0.16)
        danger = "#E16D61"
        semantic = {
            "learn": "#D49A46",
            "due": "#E4786B",
            "good": "#69B38B",
            "easy": "#7CA6D2",
        }
    else:
        canvas = "#F1EDE4"
        surface = "#F8F5ED"
        raised = "#E7E0D4"
        field = "#FCFAF4"
        text = "#1D1D1B"
        muted = "#6F6A62"
        faint = "#989184"
        border = "#D7D0C4"
        border_strong = "#AAA193"
        disabled_seed = "#8D867B"
        accent_hover = _mix_hex(accent, "#FFFFFF", 0.12)
        accent_pressed = _mix_hex(accent, "#000000", 0.14)
        danger = "#B9382F"
        semantic = {
            "learn": "#8F5200",
            "due": "#B2352B",
            "good": "#28704F",
            "easy": "#346492",
        }

    text_backgrounds = (canvas, surface, raised, field)
    accent_text = _ensure_contrast(accent, text_backgrounds, 4.5, text)
    focus = _ensure_contrast(accent, text_backgrounds, 3.0, text)
    danger_text = _ensure_contrast(danger, text_backgrounds, 4.5, text)
    disabled = _ensure_contrast(disabled_seed, text_backgrounds, 3.0, text)
    on_accent = _best_contrast_text(
        (accent, accent_hover, accent_pressed), ("#1D1D1B", "#FFFFFF")
    )
    on_danger = _best_contrast_text((danger,), ("#1D1D1B", "#FFFFFF"))
    return ColorTokens(
        family="editorial",
        flavor="editorial-dark" if system_dark else "editorial-light",
        dark=system_dark,
        accent_name="custom",
        accent_raw=user_accent,
        accent=accent,
        accent_text=accent_text,
        focus=focus,
        link=accent_text,
        cursor=focus,
        accent_hover=accent_hover,
        accent_pressed=accent_pressed,
        accent_soft=_mix_hex(accent, surface, 0.86),
        canvas=canvas,
        surface=surface,
        crust=raised,
        raised=raised,
        field=field,
        text=text,
        label=muted,
        muted=muted,
        faint=faint,
        border=border,
        border_strong=border_strong,
        hover=raised,
        selection=_mix_hex(accent, surface, 0.74),
        disabled=disabled,
        danger=danger,
        danger_text=danger_text,
        on_accent=on_accent,
        on_danger=on_danger,
        new=accent_text,
        learn=_semantic_text(semantic["learn"], text_backgrounds, text),
        due=_semantic_text(semantic["due"], text_backgrounds, text),
        good=_semantic_text(semantic["good"], text_backgrounds, text),
        easy=_semantic_text(semantic["easy"], text_backgrounds, text),
        palette={},
    )


def _catppuccin_tokens(flavor: str, accent_name: str) -> ColorTokens:
    palette = catppuccin_palette(flavor)
    dark = bool(CATPPUCCIN_DATA["flavors"][flavor]["dark"])
    accent = palette[accent_name]
    canvas = palette["base"]
    surface = palette["mantle"]
    crust = palette["crust"]
    raised = palette["surface0"]
    field = palette["surface0"]
    text = palette["text"]
    # Catppuccin's upstream style guide owns the semantic split: Base is the
    # background pane; Mantle/Crust are secondary panes; Surface 0-2 are
    # components; Text/Subtext/Overlay form the type hierarchy; Blue, Green,
    # Yellow, Red, Rosewater, and Lavender keep their functional identities.
    # Readable derivatives preserve those source hues when a raw swatch falls
    # short on one of Anki's actual surfaces.
    text_backgrounds = (canvas, surface, raised, field)

    accent_hover = _mix_hex(accent, text, 0.10)
    accent_pressed = _mix_hex(accent, text, 0.18)
    accent_text = _chromatic_text(accent, text_backgrounds, 4.5, dark)
    link = _chromatic_text(palette["blue"], text_backgrounds, 4.5, dark)
    focus = _chromatic_text(palette["lavender"], text_backgrounds, 3.0, dark)
    cursor = _chromatic_text(palette["rosewater"], text_backgrounds, 3.0, dark)
    danger = palette["red"]
    neutral_candidates = (
        palette["crust"],
        palette["base"],
        palette["text"],
        "#11111B",
        "#000000",
        "#FFFFFF",
    )
    on_accent = _best_contrast_text(
        (accent, accent_hover, accent_pressed), neutral_candidates
    )
    on_danger = _best_contrast_text((danger,), neutral_candidates)
    return ColorTokens(
        family="catppuccin",
        flavor=flavor,
        dark=dark,
        accent_name=accent_name,
        accent_raw=accent,
        accent=accent,
        accent_text=accent_text,
        focus=focus,
        link=link,
        cursor=cursor,
        accent_hover=accent_hover,
        accent_pressed=accent_pressed,
        accent_soft=_mix_hex(accent, surface, 0.86),
        canvas=canvas,
        surface=surface,
        crust=crust,
        raised=raised,
        field=field,
        text=text,
        label=palette["subtext1"],
        muted=palette["subtext0"],
        faint=palette["overlay1"],
        border=palette["surface1"],
        border_strong=palette["surface2"],
        hover=palette["surface1"],
        selection=_mix_hex(palette["overlay2"], canvas, 0.75),
        disabled=_ensure_contrast(
            palette["overlay1"], text_backgrounds, 3.0, text
        ),
        danger=danger,
        danger_text=_chromatic_text(danger, text_backgrounds, 4.5, dark),
        on_accent=on_accent,
        on_danger=on_danger,
        new=_chromatic_text(palette["teal"], text_backgrounds, 4.5, dark),
        learn=_chromatic_text(palette["yellow"], text_backgrounds, 4.5, dark),
        due=_chromatic_text(palette["red"], text_backgrounds, 4.5, dark),
        good=_chromatic_text(palette["green"], text_backgrounds, 4.5, dark),
        easy=_chromatic_text(palette["blue"], text_backgrounds, 4.5, dark),
        palette=palette,
    )


def resolve_color_tokens(config: Mapping[str, Any], system_dark: bool) -> ColorTokens:
    family = normalize_color_theme(config.get("color_theme", "editorial"))
    if family == "catppuccin":
        requested_flavor = normalize_catppuccin_flavor(
            config.get("catppuccin_flavor", CATPPUCCIN_AUTO)
        )
        flavor = (
            "mocha" if system_dark else "latte"
        ) if requested_flavor == CATPPUCCIN_AUTO else requested_flavor
        accent_name = normalize_catppuccin_accent(
            config.get("catppuccin_accent", "blue")
        )
        return _catppuccin_tokens(flavor, accent_name)
    return _editorial_tokens(config.get("accent_color", "#2F5BBC"), system_dark)


def web_color_variables(tokens: ColorTokens) -> dict[str, str]:
    text_backgrounds = (tokens.canvas, tokens.surface, tokens.raised, tokens.field)
    zero_text = _ensure_contrast(tokens.faint, text_backgrounds, 4.5, tokens.text)
    heatmap_fills = {
        "empty": tokens.raised,
        "future-1": _mix_hex(tokens.faint, tokens.raised, 0.32),
        "future-2": _mix_hex(tokens.faint, tokens.raised, 0.50),
        "future-3": _mix_hex(tokens.faint, tokens.raised, 0.66),
        "future-4": _mix_hex(tokens.faint, tokens.raised, 0.80),
        "history-1": _mix_hex(tokens.accent, tokens.raised, 0.72),
        "history-2": _mix_hex(tokens.accent, tokens.raised, 0.50),
        "history-3": _mix_hex(tokens.accent, tokens.raised, 0.28),
        "history-4": tokens.accent,
    }
    heatmap_outline_candidates = (
        tokens.text,
        tokens.on_accent,
        "#000000",
        "#FFFFFF",
    )
    variables = {
        "--mist-user-accent": tokens.accent_raw,
        "--mist-accent-fill": tokens.accent,
        "--mist-accent": tokens.accent_text,
        "--mist-focus": tokens.focus,
        "--mist-link": tokens.link,
        "--mist-cursor": tokens.cursor,
        "--mist-accent-hover": tokens.accent_hover,
        "--mist-accent-pressed": tokens.accent_pressed,
        "--mist-accent-soft": tokens.accent_soft,
        "--mist-on-accent": tokens.on_accent,
        "--mist-paper": tokens.canvas,
        "--mist-paper-light": tokens.surface,
        "--mist-crust": tokens.crust,
        "--mist-paper-deep": tokens.raised,
        "--mist-field": tokens.field,
        "--mist-ink": tokens.text,
        "--mist-label": tokens.label,
        "--mist-muted": tokens.muted,
        "--mist-faint": tokens.faint,
        "--mist-zero": zero_text,
        "--mist-rule": tokens.border,
        "--mist-rule-strong": tokens.border_strong,
        "--mist-selection": tokens.selection,
        "--mist-disabled": tokens.disabled,
        "--mist-danger-fill": tokens.danger,
        "--mist-danger": tokens.danger_text,
        "--mist-on-danger": tokens.on_danger,
        "--mist-new": tokens.new,
        "--mist-learn": tokens.learn,
        "--mist-due": tokens.due,
        "--mist-good": tokens.good,
        "--mist-easy": tokens.easy,
        "--editorial-user-accent": tokens.accent_raw,
        "--editorial-accent-fill": tokens.accent,
        "--editorial-accent": tokens.accent_text,
        "--editorial-focus": tokens.focus,
        "--editorial-link": tokens.link,
        "--editorial-cursor": tokens.cursor,
        "--editorial-accent-hover": tokens.accent_hover,
        "--editorial-accent-pressed": tokens.accent_pressed,
        "--editorial-soft-accent": tokens.accent_soft,
        "--editorial-on-accent": tokens.on_accent,
        "--editorial-paper": tokens.canvas,
        "--editorial-surface": tokens.surface,
        "--editorial-crust": tokens.crust,
        "--editorial-field": tokens.field,
        "--editorial-raised": tokens.raised,
        "--editorial-ink": tokens.text,
        "--editorial-label": tokens.label,
        "--editorial-muted": tokens.muted,
        "--editorial-disabled": tokens.disabled,
        "--editorial-rule": tokens.border,
        "--editorial-rule-strong": tokens.border_strong,
        "--editorial-selection": tokens.selection,
    }
    variables.update(
        {
            f"--mist-heatmap-today-{name}": _first_contrasting_color(
                fill, heatmap_outline_candidates
            )
            for name, fill in heatmap_fills.items()
        }
    )
    if tokens.family == "catppuccin":
        variables["--mist-paper-field"] = "none"
        # The full official palette remains available through ``tokens.palette``.
        # Do not publish generic ``--ctp-*`` properties on documentElement:
        # card templates commonly own those names, and add-on inline styles
        # would otherwise override the user's Catppuccin variables.
    return variables


MANAGED_COLOR_VARIABLES = tuple(
    dict.fromkeys(
        [
            *web_color_variables(
                _catppuccin_tokens("latte", "blue")
            ).keys(),
            *web_color_variables(
                _editorial_tokens("#2F5BBC", False)
            ).keys(),
        ]
    )
)
