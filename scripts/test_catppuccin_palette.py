#!/usr/bin/env python3
"""Exhaustive, GUI-free checks for the bundled Catppuccin color contract."""

from __future__ import annotations

import colorsys
import hashlib
import importlib.util
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "addon" / "color_themes.py"

OFFICIAL_TOKEN_ORDER = (
    "rosewater",
    "flamingo",
    "pink",
    "mauve",
    "red",
    "maroon",
    "peach",
    "yellow",
    "green",
    "teal",
    "sky",
    "sapphire",
    "blue",
    "lavender",
    "text",
    "subtext1",
    "subtext0",
    "overlay2",
    "overlay1",
    "overlay0",
    "surface2",
    "surface1",
    "surface0",
    "base",
    "mantle",
    "crust",
)
OFFICIAL_ACCENT_ORDER = OFFICIAL_TOKEN_ORDER[:14]
OFFICIAL_FLAVORS = ("latte", "frappe", "macchiato", "mocha")
OFFICIAL_DARK_FLAGS = {
    "latte": False,
    "frappe": True,
    "macchiato": True,
    "mocha": True,
}
OFFICIAL_NAMES = {
    "latte": "Latte",
    "frappe": "Frappé",
    "macchiato": "Macchiato",
    "mocha": "Mocha",
}

# Independent pinned fingerprints cover all 26 official v1.8.0 hex tokens per
# flavor. Values are normalized to uppercase and joined with ``|`` first.
OFFICIAL_FLAVOR_DIGESTS = {
    "latte": "94942c37cd9d86d656bc0e7eb9ae1a88f9138928a97c941d20bcf8239928896a",
    "frappe": "692c36332183586ee853bceea4ee99656544a9d5e19bea50d69a71a50fef0624",
    "macchiato": "7a0251fea0b1dacaa828814d96d67e198c91ed7c6c31d4ce2cbbcaf1f33186b4",
    "mocha": "f76f5a4bcfcb87fb67860f4e02c864fab767089156a26057ea090e93cfe2fde0",
}

# Keep the 56 selectable raw swatches explicit. This prevents a semantic
# fallback or an accessibility-derived color from silently replacing the
# official accent shown in the switcher.
OFFICIAL_ACCENTS = {
    "latte": (
        "#DC8A78",
        "#DD7878",
        "#EA76CB",
        "#8839EF",
        "#D20F39",
        "#E64553",
        "#FE640B",
        "#DF8E1D",
        "#40A02B",
        "#179299",
        "#04A5E5",
        "#209FB5",
        "#1E66F5",
        "#7287FD",
    ),
    "frappe": (
        "#F2D5CF",
        "#EEBEBE",
        "#F4B8E4",
        "#CA9EE6",
        "#E78284",
        "#EA999C",
        "#EF9F76",
        "#E5C890",
        "#A6D189",
        "#81C8BE",
        "#99D1DB",
        "#85C1DC",
        "#8CAAEE",
        "#BABBF1",
    ),
    "macchiato": (
        "#F4DBD6",
        "#F0C6C6",
        "#F5BDE6",
        "#C6A0F6",
        "#ED8796",
        "#EE99A0",
        "#F5A97F",
        "#EED49F",
        "#A6DA95",
        "#8BD5CA",
        "#91D7E3",
        "#7DC4E4",
        "#8AADF4",
        "#B7BDF8",
    ),
    "mocha": (
        "#F5E0DC",
        "#F2CDCD",
        "#F5C2E7",
        "#CBA6F7",
        "#F38BA8",
        "#EBA0AC",
        "#FAB387",
        "#F9E2AF",
        "#A6E3A1",
        "#94E2D5",
        "#89DCEB",
        "#74C7EC",
        "#89B4FA",
        "#B4BEFE",
    ),
}

HEX = re.compile(r"^#[0-9A-F]{6}$")
CSS_VARIABLE = re.compile(r"^--[a-z0-9-]+$")

LATTE_READABLE_ROLES = {
    "accent_text": "#1851C2",
    "link": "#1851C2",
    "focus": "#5C6DCD",
    "cursor": "#A16558",
    "new": "#106368",
    "learn": "#7B4E10",
    "due": "#B20D30",
    "good": "#29661C",
    "easy": "#1851C2",
}


def load_module():
    spec = importlib.util.spec_from_file_location(
        "editorial_color_themes_under_test", SOURCE
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    # Dataclass resolves its defining module through sys.modules on Python 3.9.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def assert_contrast(module, label: str, color: str, backgrounds, minimum: float):
    for background in backgrounds:
        ratio = module.contrast_ratio(color, background)
        assert ratio >= minimum, (
            f"{label}: {color} on {background} is {ratio:.3f}:1; "
            f"expected at least {minimum:.1f}:1"
        )


def hue_degrees(color: str) -> float:
    red, green, blue = (
        int(color[index : index + 2], 16) / 255 for index in (1, 3, 5)
    )
    return colorsys.rgb_to_hsv(red, green, blue)[0] * 360


def hue_distance(first: str, second: str) -> float:
    distance = abs(hue_degrees(first) - hue_degrees(second))
    return min(distance, 360 - distance)


def test_official_snapshot(module) -> None:
    data = module.CATPPUCCIN_DATA
    assert data["source"] == (
        "https://github.com/catppuccin/palette/blob/v1.8.0/palette.json"
    )
    assert data["source_version"] == "1.8.0"
    assert data["source_commit"] == "07d02aa110ef9eb7e7427afca5c73ba9cf7f8ebd"
    assert data["style_guide"] == (
        "https://github.com/catppuccin/catppuccin/blob/"
        "d09787dd98ca6fba08af5ef2ae94a7e09f17daca/docs/style-guide.md"
    )
    assert data["style_guide_commit"] == (
        "d09787dd98ca6fba08af5ef2ae94a7e09f17daca"
    )
    assert data["license"] == "MIT"
    assert module.CATPPUCCIN_TOKEN_ORDER == OFFICIAL_TOKEN_ORDER
    assert module.CATPPUCCIN_ACCENTS == OFFICIAL_ACCENT_ORDER
    assert module.CATPPUCCIN_FLAVORS == OFFICIAL_FLAVORS
    assert module.CATPPUCCIN_FLAVOR_OPTIONS == ("auto", *OFFICIAL_FLAVORS)
    assert tuple(data["flavors"]) == OFFICIAL_FLAVORS

    for flavor in OFFICIAL_FLAVORS:
        source_flavor = data["flavors"][flavor]
        assert source_flavor["name"] == OFFICIAL_NAMES[flavor]
        assert source_flavor["dark"] is OFFICIAL_DARK_FLAGS[flavor]
        assert len(source_flavor["hex"]) == 26
        palette = module.catppuccin_palette(flavor)
        assert tuple(palette) == OFFICIAL_TOKEN_ORDER
        assert len(palette) == 26
        assert all(HEX.fullmatch(value) for value in palette.values())
        digest = hashlib.sha256(
            "|".join(palette.values()).encode("ascii")
        ).hexdigest()
        assert digest == OFFICIAL_FLAVOR_DIGESTS[flavor]


def test_auto_and_explicit_flavors(module) -> None:
    base = {
        "color_theme": "catppuccin",
        "catppuccin_flavor": "auto",
        "catppuccin_accent": "blue",
    }
    assert module.resolve_color_tokens(base, False).flavor == "latte"
    assert module.resolve_color_tokens(base, True).flavor == "mocha"

    for flavor in OFFICIAL_FLAVORS:
        config = {**base, "catppuccin_flavor": flavor}
        light_system = module.resolve_color_tokens(config, False)
        dark_system = module.resolve_color_tokens(config, True)
        assert light_system == dark_system, (
            f"explicit {flavor} must not depend on Anki's light/dark mode"
        )
        assert light_system.dark is OFFICIAL_DARK_FLAGS[flavor]


def test_every_selectable_combination(module) -> None:
    checked = 0
    for flavor in OFFICIAL_FLAVORS:
        expected_accents = dict(zip(OFFICIAL_ACCENT_ORDER, OFFICIAL_ACCENTS[flavor]))
        expected_palette = module.catppuccin_palette(flavor)
        for accent_name in OFFICIAL_ACCENT_ORDER:
            checked += 1
            label = f"{flavor}/{accent_name}"
            config = {
                "color_theme": "catppuccin",
                "catppuccin_flavor": flavor,
                "catppuccin_accent": accent_name,
            }
            tokens = module.resolve_color_tokens(config, system_dark=False)
            raw_accent = expected_accents[accent_name]

            assert tokens.family == "catppuccin"
            assert tokens.flavor == flavor
            assert tokens.dark is OFFICIAL_DARK_FLAGS[flavor]
            assert tokens.accent_name == accent_name
            assert tokens.palette == expected_palette
            assert tokens.accent_raw == raw_accent, label
            assert tokens.accent == raw_accent, label
            assert tokens.palette[accent_name] == raw_accent, label
            assert tokens.canvas == tokens.palette["base"], label
            assert tokens.surface == tokens.palette["mantle"], label
            assert tokens.crust == tokens.palette["crust"], label
            assert tokens.raised == tokens.palette["surface0"], label
            assert tokens.field == tokens.palette["surface0"], label
            assert tokens.text == tokens.palette["text"], label
            assert tokens.label == tokens.palette["subtext1"], label
            assert tokens.muted == tokens.palette["subtext0"], label
            assert tokens.faint == tokens.palette["overlay1"], label
            assert tokens.border == tokens.palette["surface1"], label
            assert tokens.border_strong == tokens.palette["surface2"], label
            assert tokens.hover == tokens.palette["surface1"], label
            assert tokens.selection == module._mix_hex(
                tokens.palette["overlay2"], tokens.palette["base"], 0.75
            ), label

            source_roles = {
                "accent_text": raw_accent,
                "link": tokens.palette["blue"],
                "focus": tokens.palette["lavender"],
                "cursor": tokens.palette["rosewater"],
                "danger_text": tokens.palette["red"],
                "new": tokens.palette["teal"],
                "learn": tokens.palette["yellow"],
                "due": tokens.palette["red"],
                "good": tokens.palette["green"],
                "easy": tokens.palette["blue"],
            }
            for role, source_color in source_roles.items():
                derived = getattr(tokens, role)
                assert hue_distance(source_color, derived) <= 3.0, (
                    f"{label} {role}: readable derivative {derived} rotated away "
                    f"from source hue {source_color}"
                )

            surfaces = (
                tokens.canvas,
                tokens.surface,
                tokens.raised,
                tokens.field,
            )
            assert_contrast(module, f"{label} normal text", tokens.text, surfaces, 4.5)
            assert_contrast(
                module, f"{label} accent text", tokens.accent_text, surfaces, 4.5
            )
            assert_contrast(module, f"{label} focus", tokens.focus, surfaces, 3.0)
            assert_contrast(module, f"{label} link", tokens.link, surfaces, 4.5)
            assert_contrast(module, f"{label} cursor", tokens.cursor, surfaces, 3.0)
            assert_contrast(
                module, f"{label} disabled", tokens.disabled, surfaces, 3.0
            )
            assert_contrast(
                module,
                f"{label} on-accent",
                tokens.on_accent,
                (tokens.accent, tokens.accent_hover, tokens.accent_pressed),
                4.5,
            )
            assert_contrast(
                module, f"{label} on-danger", tokens.on_danger, (tokens.danger,), 4.5
            )
            for role in ("danger_text", "new", "learn", "due", "good", "easy"):
                assert_contrast(
                    module,
                    f"{label} {role}",
                    getattr(tokens, role),
                    surfaces,
                    4.5,
                )

            variables = module.web_color_variables(tokens)
            assert all(CSS_VARIABLE.fullmatch(name) for name in variables)
            assert all(
                HEX.fullmatch(value)
                or (name == "--mist-paper-field" and value == "none")
                for name, value in variables.items()
            )
            assert variables["--mist-paper-field"] == "none"
            assert variables["--mist-user-accent"] == raw_accent
            assert variables["--mist-accent-fill"] == raw_accent
            assert variables["--mist-accent"] == tokens.accent_text
            assert variables["--mist-focus"] == tokens.focus
            assert variables["--mist-link"] == tokens.link
            assert variables["--mist-cursor"] == tokens.cursor
            assert variables["--mist-crust"] == tokens.crust
            assert variables["--mist-label"] == tokens.label
            assert variables["--mist-selection"] == tokens.selection
            assert variables["--mist-zero"] == module._ensure_contrast(
                tokens.faint, surfaces, 4.5, tokens.text
            )
            assert_contrast(
                module,
                f"{label} zero text",
                variables["--mist-zero"],
                surfaces,
                4.5,
            )
            assert variables["--mist-on-accent"] == tokens.on_accent
            assert variables["--editorial-user-accent"] == raw_accent
            assert variables["--editorial-accent-fill"] == raw_accent
            assert variables["--editorial-accent"] == tokens.accent_text
            assert variables["--editorial-focus"] == tokens.focus
            assert variables["--editorial-link"] == tokens.link
            assert variables["--editorial-cursor"] == tokens.cursor
            assert variables["--editorial-crust"] == tokens.crust
            assert variables["--editorial-label"] == tokens.label
            assert variables["--editorial-selection"] == tokens.selection
            assert variables["--editorial-on-accent"] == tokens.on_accent
            heatmap_fills = {
                "empty": tokens.raised,
                "future-1": module._mix_hex(tokens.faint, tokens.raised, 0.32),
                "future-2": module._mix_hex(tokens.faint, tokens.raised, 0.50),
                "future-3": module._mix_hex(tokens.faint, tokens.raised, 0.66),
                "future-4": module._mix_hex(tokens.faint, tokens.raised, 0.80),
                "history-1": module._mix_hex(tokens.accent, tokens.raised, 0.72),
                "history-2": module._mix_hex(tokens.accent, tokens.raised, 0.50),
                "history-3": module._mix_hex(tokens.accent, tokens.raised, 0.28),
                "history-4": tokens.accent,
            }
            for heatmap_role, heatmap_fill in heatmap_fills.items():
                outline = variables[f"--mist-heatmap-today-{heatmap_role}"]
                assert module.contrast_ratio(outline, heatmap_fill) >= 3.5, (
                    f"{label}: {heatmap_role} outline does not clear the "
                    "non-text contrast guard"
                )
            assert not any(name.startswith("--ctp-") for name in variables), (
                f"{label}: generic Catppuccin variables would override card templates"
            )

    assert checked == 4 * 14 == 56

    latte_blue = module.resolve_color_tokens(
        {
            "color_theme": "catppuccin",
            "catppuccin_flavor": "latte",
            "catppuccin_accent": "blue",
        },
        system_dark=False,
    )
    for role, expected in LATTE_READABLE_ROLES.items():
        assert getattr(latte_blue, role) == expected, (
            f"latte/blue {role} regressed from the hue-preserving readable value"
        )
    assert len(module.MANAGED_COLOR_VARIABLES) == len(
        set(module.MANAGED_COLOR_VARIABLES)
    )
    assert not any(
        name.startswith("--ctp-") for name in module.MANAGED_COLOR_VARIABLES
    ), "generic Catppuccin names must never become add-on-managed root variables"


def test_invalid_config_fallbacks(module) -> None:
    assert module.normalize_color_theme(" CATPPUCCIN ") == "catppuccin"
    assert module.normalize_color_theme("not-a-theme") == "editorial"
    assert module.normalize_color_theme(None) == "editorial"
    assert module.normalize_catppuccin_flavor(" MACCHIATO ") == "macchiato"
    assert module.normalize_catppuccin_flavor("not-a-flavor") == "auto"
    assert module.normalize_catppuccin_accent(" ROSEWATER ") == "rosewater"
    assert module.normalize_catppuccin_accent("not-an-accent") == "blue"

    invalid_catppuccin = {
        "color_theme": "catppuccin",
        "catppuccin_flavor": "not-a-flavor",
        "catppuccin_accent": "not-an-accent",
    }
    light = module.resolve_color_tokens(invalid_catppuccin, False)
    dark = module.resolve_color_tokens(invalid_catppuccin, True)
    assert (light.flavor, light.accent_name, light.accent_raw) == (
        "latte",
        "blue",
        "#1E66F5",
    )
    assert (dark.flavor, dark.accent_name, dark.accent_raw) == (
        "mocha",
        "blue",
        "#89B4FA",
    )

    invalid_family = module.resolve_color_tokens(
        {"color_theme": "not-a-theme", "accent_color": "not-a-color"}, False
    )
    assert invalid_family.family == "editorial"
    assert invalid_family.accent_raw == "#2F5BBC"
    assert module.catppuccin_palette("not-a-flavor") == module.catppuccin_palette(
        "latte"
    )
    assert module.catppuccin_color("latte", "not-a-color") == "#1E66F5"


def test_editorial_legacy_tokens(module) -> None:
    light = module.resolve_color_tokens(
        {"color_theme": "editorial", "accent_color": "#2f5bbc"}, False
    )
    dark = module.resolve_color_tokens(
        {"color_theme": "editorial", "accent_color": "#2f5bbc"}, True
    )

    assert (
        light.family,
        light.flavor,
        light.dark,
        light.accent_raw,
        light.accent,
        light.canvas,
        light.surface,
        light.raised,
        light.field,
        light.text,
        light.muted,
        light.border,
        light.danger,
        light.on_accent,
        light.on_danger,
    ) == (
        "editorial",
        "editorial-light",
        False,
        "#2F5BBC",
        "#2F5BBC",
        "#F1EDE4",
        "#F8F5ED",
        "#E7E0D4",
        "#FCFAF4",
        "#1D1D1B",
        "#6F6A62",
        "#D7D0C4",
        "#B9382F",
        "#FFFFFF",
        "#FFFFFF",
    )
    assert (
        dark.family,
        dark.flavor,
        dark.dark,
        dark.accent_raw,
        dark.accent,
        dark.canvas,
        dark.surface,
        dark.raised,
        dark.field,
        dark.text,
        dark.muted,
        dark.border,
        dark.danger,
        dark.on_accent,
        dark.on_danger,
    ) == (
        "editorial",
        "editorial-dark",
        True,
        "#2F5BBC",
        "#7894D3",
        "#1B1916",
        "#221F1A",
        "#2B2721",
        "#27231E",
        "#F1EADF",
        "#B3AB9E",
        "#514A40",
        "#E16D61",
        "#1D1D1B",
        "#1D1D1B",
    )
    assert light.palette == dark.palette == {}

    for tokens in (light, dark):
        surfaces = (tokens.canvas, tokens.surface, tokens.raised, tokens.field)
        assert_contrast(module, f"{tokens.flavor} text", tokens.text, surfaces, 4.5)
        assert_contrast(
            module, f"{tokens.flavor} accent text", tokens.accent_text, surfaces, 4.5
        )
        assert_contrast(module, f"{tokens.flavor} focus", tokens.focus, surfaces, 3.0)
        assert_contrast(
            module, f"{tokens.flavor} disabled", tokens.disabled, surfaces, 3.0
        )


def main() -> None:
    module = load_module()
    test_official_snapshot(module)
    test_auto_and_explicit_flavors(module)
    test_every_selectable_combination(module)
    test_invalid_config_fallbacks(module)
    test_editorial_legacy_tokens(module)
    print("Catppuccin palette tests passed: 4 flavors × 14 accents (56 combinations)")


if __name__ == "__main__":
    main()
