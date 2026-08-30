#!/usr/bin/env python3
"""Browser regression for the Catppuccin runtime color contract.

The test resolves the production Python tokens, applies those exact custom
properties to the real Deck, Editor, Stats, Reviewer, and Review Heatmap
fixtures, and switches every one of the 4 flavors x 14 accents in place.

Run with a Python environment that provides Playwright 1.60+::

    python -m pip install playwright==1.60.0
    python scripts/test_catppuccin_web.py

The script uses a locally installed Chrome when available, so downloading a
second browser is not required on the macOS development machine.
"""

from __future__ import annotations

from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
from threading import Thread
from typing import Any, Iterator

try:
    from playwright.sync_api import Page, sync_playwright
except ModuleNotFoundError as exc:  # pragma: no cover - dependency guidance
    raise SystemExit(
        "Python Playwright is required: "
        "python -m pip install playwright==1.60.0"
    ) from exc


ROOT = Path(__file__).resolve().parents[1]
COLOR_SOURCE = ROOT / "addon" / "color_themes.py"
RUNTIME_SOURCE = ROOT / "addon" / "__init__.py"
LOCAL_CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")

PRODUCTION_FIXTURE = "design-exploration/production-preview/index.html"
EDITOR_FIXTURE = "design-exploration/editor-preview/index.html"
STANDALONE_FIXTURE = "design-exploration/standalone-preview/index.html"

FLAVORS = ("latte", "frappe", "macchiato", "mocha")
ACCENTS = (
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
)

COLOR_PAIRS = (
    # Normal and readable accent text on every product surface.
    *( ("ink", "--mist-ink", surface, 4.5) for surface in (
        "--mist-paper", "--mist-paper-light", "--mist-paper-deep", "--mist-field"
    )),
    *( ("accent-text", "--mist-accent", surface, 4.5) for surface in (
        "--mist-paper", "--mist-paper-light", "--mist-paper-deep", "--mist-field"
    )),
    *( ("focus", "--mist-focus", surface, 3.0) for surface in (
        "--mist-paper", "--mist-paper-light", "--mist-paper-deep", "--mist-field"
    )),
    *( ("disabled", "--mist-disabled", surface, 3.0) for surface in (
        "--mist-paper", "--mist-paper-light", "--mist-paper-deep", "--mist-field"
    )),
    *( ("danger-text", "--mist-danger", surface, 4.5) for surface in (
        "--mist-paper", "--mist-paper-light", "--mist-paper-deep", "--mist-field"
    )),
    # Filled actions must retain readable foregrounds in every interaction state.
    ("on-accent", "--mist-on-accent", "--mist-accent-fill", 4.5),
    ("on-accent-hover", "--mist-on-accent", "--mist-accent-hover", 4.5),
    ("on-accent-pressed", "--mist-on-accent", "--mist-accent-pressed", 4.5),
    ("on-danger", "--mist-on-danger", "--mist-danger-fill", 4.5),
    # Deck/reviewer semantic roles are text, not raw decorative swatches.
    *( (role.removeprefix("--mist-"), role, surface, 4.5)
       for role in (
           "--mist-new", "--mist-learn", "--mist-due",
           "--mist-good", "--mist-easy",
       )
       for surface in (
           "--mist-paper", "--mist-paper-light", "--mist-paper-deep", "--mist-field"
       ) ),
)


APPLY_PAYLOAD_JS = """
async ({ payload, context }) => {
  const root = document.documentElement;
  window.__catppuccinManaged ??= [];
  for (const name of window.__catppuccinManaged) root.style.removeProperty(name);
  window.__catppuccinManaged = Object.keys(payload.variables);
  for (const [name, value] of Object.entries(payload.variables)) {
    root.style.setProperty(name, value);
  }
  root.dataset.mistlineFamily = payload.family;
  root.dataset.mistlinePalette = payload.flavor;
  root.dataset.mistlineTone = payload.tone;
  root.dataset.mistlineAccent = payload.accentName;
  root.dataset.mistlineEnabled = "on";
  if (context !== "reviewer" && context !== "reviewer-bottom-bar") {
    root.style.colorScheme = payload.tone;
    root.dataset.mistlineOwnsColorScheme = "true";
  } else if (root.dataset.mistlineOwnsColorScheme === "true") {
    root.style.removeProperty("color-scheme");
    delete root.dataset.mistlineOwnsColorScheme;
  }
  await new Promise(resolve => requestAnimationFrame(() => resolve()));
}
"""


REVIEWER_INHERITANCE_AUDIT_JS = """
() => {
  const root = document.documentElement;
  const selectors = ["#qa", ".user-card-inheritance-probe", ".user-card-button"];
  const read = () => Object.fromEntries(selectors.map(selector => {
    const style = getComputedStyle(document.querySelector(selector));
    return [selector, {
      colorScheme: style.getPropertyValue("color-scheme"),
      fontSynthesis: style.getPropertyValue("font-synthesis"),
      fontKerning: style.getPropertyValue("font-kerning"),
    }];
  }));
  const context = root.getAttribute("data-mistline-context");
  const active = read();
  root.removeAttribute("data-mistline-context");
  const unmanaged = read();
  root.setAttribute("data-mistline-context", context);
  const restored = read();
  return { active, unmanaged, restored };
}
"""


CORE_AUDIT_JS = """
({ payload, pairs }) => {
  const root = document.documentElement;
  const parse = value => (value.match(/[\\d.]+/g) || []).slice(0, 3).map(Number);
  const luminance = value => parse(value)
    .map(channel => channel / 255)
    .map(channel => channel <= .04045
      ? channel / 12.92
      : ((channel + .055) / 1.055) ** 2.4)
    .reduce((total, channel, index) => total + channel * [.2126, .7152, .0722][index], 0);
  const ratio = (foreground, background) => {
    const values = [luminance(foreground), luminance(background)].sort((a, b) => b - a);
    return (values[0] + .05) / (values[1] + .05);
  };
  const probe = document.createElement("span");
  probe.id = "catppuccin-runtime-contrast-probe";
  probe.style.cssText = "position:fixed;left:-9999px;top:-9999px;display:block;width:2px;height:2px";
  document.body.appendChild(probe);
  const contrasts = pairs.map(([label, foreground, background, minimum]) => {
    probe.style.color = `var(${foreground})`;
    probe.style.backgroundColor = `var(${background})`;
    const style = getComputedStyle(probe);
    return {
      label,
      foreground,
      background,
      minimum,
      actualForeground: style.color,
      actualBackground: style.backgroundColor,
      ratio: ratio(style.color, style.backgroundColor),
    };
  });
  probe.remove();
  const inline = Object.fromEntries(
    Object.keys(payload.variables).map(name => [name, root.style.getPropertyValue(name).trim()])
  );
  const bodyStyle = getComputedStyle(document.body);
  return {
    datasets: {
      family: root.dataset.mistlineFamily,
      palette: root.dataset.mistlinePalette,
      tone: root.dataset.mistlineTone,
      accent: root.dataset.mistlineAccent,
      ownsColorScheme: root.dataset.mistlineOwnsColorScheme || "",
    },
    colorScheme: root.style.colorScheme,
    cardTemplateCtpBlue: getComputedStyle(root).getPropertyValue("--ctp-blue").trim(),
    inline,
    body: {
      color: bodyStyle.color,
      background: bodyStyle.backgroundColor,
      backgroundImage: bodyStyle.backgroundImage,
    },
    contrasts,
  };
}
"""


HEX = re.compile(r"^#[0-9A-F]{6}$")


class Checks:
    def __init__(self) -> None:
        self.total = 0
        self.coverage: dict[str, int] = {}

    def require(self, condition: object, message: str, category: str = "general") -> None:
        self.total += 1
        self.coverage[category] = self.coverage.get(category, 0) + 1
        if not condition:
            raise AssertionError(message)


def load_color_module():
    spec = importlib.util.spec_from_file_location("catppuccin_web_tokens", COLOR_SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {COLOR_SOURCE}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def build_payloads(module) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for flavor in FLAVORS:
        for accent in ACCENTS:
            tokens = module.resolve_color_tokens(
                {
                    "color_theme": "catppuccin",
                    "catppuccin_flavor": flavor,
                    "catppuccin_accent": accent,
                },
                system_dark=False,
            )
            payloads.append(
                {
                    "label": f"{flavor}/{accent}",
                    "family": tokens.family,
                    "flavor": tokens.flavor,
                    "tone": "dark" if tokens.dark else "light",
                    "accentName": tokens.accent_name,
                    "accentRaw": tokens.accent_raw,
                    "palette": dict(tokens.palette),
                    "variables": module.web_color_variables(tokens),
                }
            )
    return payloads


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, _format: str, *args: object) -> None:
        return


@contextmanager
def local_server() -> Iterator[str]:
    handler = partial(QuietHandler, directory=str(ROOT))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address[:2]
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def rgb_from_hex(value: str) -> str:
    if not HEX.fullmatch(value):
        raise ValueError(f"not a normalized hex color: {value}")
    return f"rgb({int(value[1:3], 16)}, {int(value[3:5], 16)}, {int(value[5:7], 16)})"


def install_error_capture(page: Page, label: str) -> list[str]:
    errors: list[str] = []
    page.on(
        "console",
        lambda message: errors.append(f"{label}: {message.text}")
        if message.type == "error"
        else None,
    )
    page.on("pageerror", lambda error: errors.append(f"{label}: {error}"))
    return errors


def apply_payload(page: Page, payload: dict[str, Any], context: str) -> None:
    page.evaluate(APPLY_PAYLOAD_JS, {"payload": payload, "context": context})


def audit_core(
    page: Page,
    payload: dict[str, Any],
    context: str,
    checks: Checks,
) -> dict[str, Any]:
    label = f"{context}/{payload['label']}"
    page.evaluate(
        """
        () => {
          let style = document.getElementById("card-template-catppuccin-contract");
          if (!style) {
            style = document.createElement("style");
            style.id = "card-template-catppuccin-contract";
            style.textContent = ":root { --ctp-blue: #123456; }";
            document.head.appendChild(style);
          }
        }
        """
    )
    apply_payload(page, payload, context)
    audit = page.evaluate(
        CORE_AUDIT_JS,
        {"payload": payload, "pairs": COLOR_PAIRS},
    )

    expected_data = {
        "family": "catppuccin",
        "palette": payload["flavor"],
        "tone": payload["tone"],
        "accent": payload["accentName"],
    }
    for name, expected in expected_data.items():
        checks.require(
            audit["datasets"][name] == expected,
            f"{label}: data-{name} is {audit['datasets'][name]!r}, expected {expected!r}",
            "runtime-metadata",
        )

    if context in {"reviewer", "reviewer-bottom-bar"}:
        checks.require(
            audit["datasets"]["ownsColorScheme"] == "",
            f"{label}: reviewer unexpectedly owns color-scheme",
            "color-scheme-ownership",
        )
    else:
        checks.require(
            audit["datasets"]["ownsColorScheme"] == "true"
            and audit["colorScheme"] == payload["tone"],
            f"{label}: explicit tone was not applied ({audit['colorScheme']!r})",
            "color-scheme-ownership",
        )

    for name, expected in payload["variables"].items():
        checks.require(
            audit["inline"].get(name) == expected,
            f"{label}: {name} is {audit['inline'].get(name)!r}, expected {expected!r}",
            "exact-runtime-variables",
        )
    checks.require(
        audit["inline"]["--mist-accent-fill"] == payload["accentRaw"],
        f"{label}: selectable raw accent was replaced",
        "raw-accent",
    )
    checks.require(
        not any(name.startswith("--ctp-") for name in payload["variables"]),
        f"{label}: generic Catppuccin variables leaked into the runtime payload",
        "card-template-variable-ownership",
    )
    checks.require(
        audit["cardTemplateCtpBlue"] == "#123456",
        f"{label}: add-on overrode the card template's --ctp-blue variable",
        "card-template-variable-ownership",
    )
    checks.require(
        audit["body"]["backgroundImage"] == "none",
        f"{label}: warm paper texture survived Catppuccin ({audit['body']['backgroundImage']})",
        "catppuccin-surface",
    )
    for sample in audit["contrasts"]:
        checks.require(
            sample["ratio"] + 1e-9 >= sample["minimum"],
            (
                f"{label}: {sample['label']} contrast {sample['ratio']:.3f}:1 "
                f"({sample['actualForeground']} on {sample['actualBackground']}); "
                f"expected {sample['minimum']:.1f}:1"
            ),
            "computed-contrast",
        )
    return audit


def audit_runtime_source(checks: Checks) -> None:
    source = RUNTIME_SOURCE.read_text(encoding="utf-8")
    start = source.index("def _runtime_theme_script(")
    end = source.index("\ndef _inject_external_style", start)
    runtime = source[start:end]
    checks.require(
        "root.style.setProperty(name, value)" in runtime,
        "runtime no longer applies custom properties in place",
        "runtime-source",
    )
    checks.require(
        "root.style.colorScheme = settings.tone" in runtime,
        "runtime no longer applies an explicit Catppuccin tone",
        "runtime-source",
    )
    checks.require(
        'context !== "reviewer" && context !== "reviewer-bottom-bar"' in runtime,
        "runtime no longer excludes user-owned reviewer color-scheme",
        "runtime-source",
    )
    checks.require(
        "mw.reset(" not in source,
        "cosmetic switching can still reset Anki Editor/Reviewer state",
        "runtime-source",
    )
    checks.require(
        'candidate.href === resolvedHref' in runtime
        and 'href*="/web/theme.css"' not in runtime
        and 'href*="/web/editor.css"' not in runtime,
        "runtime stylesheet ownership is not restricted to the exact add-on URL",
        "runtime-source",
    )
    for destructive in (
        "location.reload",
        "window.location",
        "document.write",
        ".innerHTML",
        ".outerHTML",
        "replaceChildren",
    ):
        checks.require(
            destructive not in runtime,
            f"runtime uses destructive DOM/navigation operation: {destructive}",
            "runtime-source",
        )


def audit_deck(
    browser,
    base_url: str,
    payloads: list[dict[str, Any]],
    checks: Checks,
) -> None:
    page = browser.new_page(viewport={"width": 1120, "height": 820})
    errors = install_error_capture(page, "deck")
    try:
        page.goto(f"{base_url}/{PRODUCTION_FIXTURE}?context=deck-browser&state=deck")
        page.wait_for_load_state("networkidle")
        page.evaluate(
            """
            () => {
              window.__deckRootIdentity = document.querySelector("body > center");
              window.__deckRuntimeIdentity = crypto.randomUUID();
            }
            """
        )
        heatmap_before = page.locator(".heatmap .day").evaluate_all(
            "nodes => nodes.map(node => getComputedStyle(node).backgroundColor)"
        )
        checks.require(len(heatmap_before) == 3, "deck: Review Heatmap fixture missing", "deck")

        for payload in payloads:
            label = f"deck/{payload['label']}"
            audit = audit_core(page, payload, "deck-browser", checks)
            checks.require(
                audit["body"]["background"] == rgb_from_hex(payload["variables"]["--mist-paper"]),
                f"{label}: rendered canvas mismatch {audit['body']['background']}",
                "deck",
            )
            checks.require(
                audit["body"]["color"] == rgb_from_hex(payload["variables"]["--mist-ink"]),
                f"{label}: rendered ink mismatch {audit['body']['color']}",
                "deck",
            )
            semantic = page.evaluate(
                """
                () => ({
                  newColor: getComputedStyle(document.querySelector("tr.deck .new-count")).color,
                  learnColor: getComputedStyle(document.querySelector("tr.deck .learn-count")).color,
                  dueColor: getComputedStyle(document.querySelector("tr.deck .review-count")).color,
                  sameDeckNode: window.__deckRootIdentity === document.querySelector("body > center"),
                  runtimeIdentity: window.__deckRuntimeIdentity,
                  heatmap: [...document.querySelectorAll(".heatmap .day")]
                    .map(node => getComputedStyle(node).backgroundColor),
                })
                """
            )
            for role, css_name in (
                ("newColor", "--mist-new"),
                ("learnColor", "--mist-learn"),
                ("dueColor", "--mist-due"),
            ):
                checks.require(
                    semantic[role] == rgb_from_hex(payload["variables"][css_name]),
                    f"{label}: rendered {role} mismatch {semantic[role]}",
                    "deck-semantic-colors",
                )
            checks.require(
                semantic["sameDeckNode"] and bool(semantic["runtimeIdentity"]),
                f"{label}: Deck DOM was replaced during switch",
                "in-place-switch",
            )
            checks.require(
                semantic["heatmap"] == heatmap_before,
                f"{label}: Review Heatmap cell fills changed {semantic['heatmap']}",
                "heatmap-ownership",
            )
        checks.require(not errors, f"deck browser errors: {errors}", "browser-errors")
    finally:
        page.close()


def audit_editor(
    browser,
    base_url: str,
    payloads: list[dict[str, Any]],
    checks: Checks,
) -> None:
    page = browser.new_page(viewport={"width": 400, "height": 320})
    errors = install_error_capture(page, "editor")
    navigations = 0

    def count_navigation(_frame) -> None:
        nonlocal navigations
        navigations += 1

    page.on("framenavigated", count_navigation)
    try:
        page.goto(f"{base_url}/{EDITOR_FIXTURE}?theme=light&tags=expanded")
        page.wait_for_load_state("networkidle")
        initial_navigations = navigations
        sentinel = page.evaluate(
            """
            () => {
              const field = document.querySelector("[data-field='front']");
              field.innerHTML = '<strong data-unsaved="true">UNSAVED CATPPUCCIN SWITCH</strong>'
                + '<br>'.repeat(18) + '<em>keep this editor state</em>';
              field.focus();
              const text = field.querySelector("strong").firstChild;
              const range = document.createRange();
              range.setStart(text, 8);
              range.collapse(true);
              const selection = getSelection();
              selection.removeAllRanges();
              selection.addRange(range);
              const scroller = document.querySelector(".scroll-area");
              scroller.scrollTop = Math.min(72, scroller.scrollHeight - scroller.clientHeight);
              window.__editorFieldIdentity = field;
              window.__editorUnsavedIdentity = field.querySelector("[data-unsaved]");
              window.__editorRuntimeIdentity = crypto.randomUUID();
              document.querySelector('[aria-label="Bold"]').classList.add("active");
              return {
                html: field.innerHTML,
                scrollTop: scroller.scrollTop,
                windowScrollY: window.scrollY,
                selectionOffset: selection.anchorOffset,
                runtimeIdentity: window.__editorRuntimeIdentity,
              };
            }
            """
        )
        checks.require(sentinel["scrollTop"] > 0, "editor: scroll sentinel could not be established", "editor-state")

        for payload in payloads:
            label = f"editor/{payload['label']}"
            audit_core(page, payload, "editor", checks)
            # Production keeps the 150 ms color transition enabled. Wait for
            # its final state instead of depending on incidental audit timing.
            page.wait_for_function(
                """
                ({ background, color }) => {
                  const style = getComputedStyle(
                    document.querySelector('[aria-label="Bold"]')
                  );
                  return style.backgroundColor === background && style.color === color;
                }
                """,
                arg={
                    "background": rgb_from_hex(
                        payload["variables"]["--editorial-accent-fill"]
                    ),
                    "color": rgb_from_hex(
                        payload["variables"]["--editorial-on-accent"]
                    ),
                },
                timeout=1_000,
            )
            state = page.evaluate(
                """
                () => {
                  const field = document.querySelector("[data-field='front']");
                  const scroller = document.querySelector(".scroll-area");
                  const selection = getSelection();
                  const editorStyle = getComputedStyle(document.querySelector(".note-editor"));
                  const activeStyle = getComputedStyle(document.querySelector('[aria-label="Bold"]'));
                  return {
                    html: field.innerHTML,
                    sameField: window.__editorFieldIdentity === field,
                    sameUnsaved: window.__editorUnsavedIdentity === field.querySelector("[data-unsaved]"),
                    activeElement: document.activeElement === field,
                    selectionInside: selection.anchorNode && field.contains(selection.anchorNode),
                    selectionOffset: selection.anchorOffset,
                    scrollTop: scroller.scrollTop,
                    windowScrollY: window.scrollY,
                    runtimeIdentity: window.__editorRuntimeIdentity,
                    background: editorStyle.backgroundColor,
                    color: editorStyle.color,
                    activeBackground: activeStyle.backgroundColor,
                    activeColor: activeStyle.color,
                  };
                }
                """
            )
            checks.require(
                state["html"] == sentinel["html"] and state["sameField"] and state["sameUnsaved"],
                f"{label}: unsaved editor DOM/content changed",
                "editor-state",
            )
            checks.require(
                state["activeElement"] and state["selectionInside"]
                and state["selectionOffset"] == sentinel["selectionOffset"],
                f"{label}: editor focus/caret changed {state}",
                "editor-state",
            )
            checks.require(
                state["scrollTop"] == sentinel["scrollTop"]
                and state["windowScrollY"] == sentinel["windowScrollY"],
                f"{label}: editor scroll changed {state['scrollTop']}/{state['windowScrollY']}",
                "editor-state",
            )
            checks.require(
                state["runtimeIdentity"] == sentinel["runtimeIdentity"]
                and navigations == initial_navigations,
                f"{label}: switch reloaded/navigated the Editor",
                "in-place-switch",
            )
            checks.require(
                state["background"] == rgb_from_hex(payload["variables"]["--editorial-paper"])
                and state["color"] == rgb_from_hex(payload["variables"]["--editorial-ink"]),
                f"{label}: Editor chrome did not consume palette {state}",
                "editor-colors",
            )
            checks.require(
                state["activeBackground"] == rgb_from_hex(payload["variables"]["--editorial-accent-fill"])
                and state["activeColor"] == rgb_from_hex(payload["variables"]["--editorial-on-accent"]),
                f"{label}: active Editor action did not consume fill/on-fill roles {state}",
                "editor-colors",
            )
        checks.require(not errors, f"editor browser errors: {errors}", "browser-errors")
    finally:
        page.close()


def audit_stats(
    browser,
    base_url: str,
    payloads: list[dict[str, Any]],
    checks: Checks,
) -> None:
    page = browser.new_page(viewport={"width": 760, "height": 700})
    errors = install_error_capture(page, "stats")
    try:
        page.goto(f"{base_url}/{STANDALONE_FIXTURE}?context=stats&theme=light")
        page.wait_for_load_state("networkidle")
        page.locator("#statisticsSearchText").fill("tag:unsaved-switch")
        page.locator("#statisticsSearchText").focus()
        page.evaluate("window.__statsRootIdentity = document.querySelector('.statistics-page')")

        for payload in payloads:
            label = f"stats/{payload['label']}"
            audit = audit_core(page, payload, "stats", checks)
            state = page.evaluate(
                """
                () => {
                  const card = document.querySelector(".graphs-container > .container.light");
                  return {
                    input: document.querySelector("#statisticsSearchText").value,
                    focused: document.activeElement?.id === "statisticsSearchText",
                    sameRoot: window.__statsRootIdentity === document.querySelector(".statistics-page"),
                    cardBackground: getComputedStyle(card).backgroundColor,
                  };
                }
                """
            )
            checks.require(
                audit["body"]["background"] == rgb_from_hex(payload["variables"]["--mist-paper"]),
                f"{label}: Stats canvas mismatch {audit['body']['background']}",
                "stats",
            )
            checks.require(
                state["cardBackground"] == rgb_from_hex(payload["variables"]["--mist-paper-light"]),
                f"{label}: Stats card surface mismatch {state['cardBackground']}",
                "stats",
            )
            checks.require(
                state["input"] == "tag:unsaved-switch" and state["focused"] and state["sameRoot"],
                f"{label}: Stats control state/DOM changed {state}",
                "in-place-switch",
            )

        latte = next(item for item in payloads if item["label"] == "latte/blue")
        mocha = next(item for item in payloads if item["label"] == "mocha/blue")
        page.evaluate("document.documentElement.classList.add('night-mode')")
        latte_audit = audit_core(page, latte, "stats", checks)
        checks.require(
            latte_audit["body"]["background"] == rgb_from_hex(latte["variables"]["--mist-paper"])
            and latte_audit["colorScheme"] == "light",
            "Latte did not override a night-mode document",
            "explicit-flavor-vs-system",
        )
        page.evaluate("document.documentElement.classList.remove('night-mode')")
        mocha_audit = audit_core(page, mocha, "stats", checks)
        checks.require(
            mocha_audit["body"]["background"] == rgb_from_hex(mocha["variables"]["--mist-paper"])
            and mocha_audit["colorScheme"] == "dark",
            "Mocha did not override a non-night-mode document",
            "explicit-flavor-vs-system",
        )
        checks.require(not errors, f"stats browser errors: {errors}", "browser-errors")
    finally:
        page.close()


def audit_reviewer(
    browser,
    base_url: str,
    payloads: list[dict[str, Any]],
    checks: Checks,
) -> None:
    page = browser.new_page(viewport={"width": 1000, "height": 720})
    errors = install_error_capture(page, "reviewer")
    try:
        page.goto(f"{base_url}/{PRODUCTION_FIXTURE}?context=reviewer&state=answer")
        page.wait_for_load_state("networkidle")
        page.locator(".user-card-button").focus()
        baseline = page.locator(".user-card-button").evaluate(
            """
            node => {
              const style = getComputedStyle(node);
              window.__reviewerButtonIdentity = node;
              window.__reviewerRootIdentity = document.querySelector("#qa");
              return {
                background: style.backgroundColor,
                color: style.color,
                borderStyle: style.borderTopStyle,
                borderColor: style.borderTopColor,
                borderWidth: style.borderTopWidth,
                radius: style.borderRadius,
                shadow: style.boxShadow,
                fontFamily: style.fontFamily,
                fontWeight: style.fontWeight,
                animationDuration: style.animationDuration,
                transitionDuration: style.transitionDuration,
              };
            }
            """
        )
        initial_scheme = page.locator("html").evaluate("node => node.style.colorScheme")

        for payload in payloads:
            label = f"reviewer/{payload['label']}"
            audit_core(page, payload, "reviewer", checks)
            inheritance = page.evaluate(REVIEWER_INHERITANCE_AUDIT_JS)
            checks.require(
                all(
                    value
                    for sample in inheritance["unmanaged"].values()
                    for value in sample.values()
                ),
                f"{label}: computed inheritance audit returned an empty property",
                "reviewer-inherited-rendering-ownership",
            )
            checks.require(
                inheritance["active"] == inheritance["unmanaged"],
                (
                    f"{label}: add-on changed inherited card rendering preferences "
                    f"{json.dumps(inheritance, ensure_ascii=False)}"
                ),
                "reviewer-inherited-rendering-ownership",
            )
            checks.require(
                inheritance["restored"] == inheritance["active"],
                f"{label}: reviewer inheritance audit did not restore its context",
                "reviewer-inherited-rendering-ownership",
            )
            state = page.locator(".user-card-button").evaluate(
                """
                node => {
                  const style = getComputedStyle(node);
                  return {
                    visual: {
                      background: style.backgroundColor,
                      color: style.color,
                      borderStyle: style.borderTopStyle,
                      borderColor: style.borderTopColor,
                      borderWidth: style.borderTopWidth,
                      radius: style.borderRadius,
                      shadow: style.boxShadow,
                      fontFamily: style.fontFamily,
                      fontWeight: style.fontWeight,
                      animationDuration: style.animationDuration,
                      transitionDuration: style.transitionDuration,
                    },
                    sameButton: window.__reviewerButtonIdentity === node,
                    sameRoot: window.__reviewerRootIdentity === document.querySelector("#qa"),
                    focused: document.activeElement === node,
                    colorScheme: document.documentElement.style.colorScheme,
                  };
                }
                """
            )
            checks.require(
                state["visual"] == baseline,
                f"{label}: user card button style changed {json.dumps(state['visual'], ensure_ascii=False)}",
                "reviewer-ownership",
            )
            checks.require(
                state["sameButton"] and state["sameRoot"] and state["focused"],
                f"{label}: reviewer user DOM/focus changed {state}",
                "reviewer-ownership",
            )
            checks.require(
                state["colorScheme"] == initial_scheme,
                f"{label}: reviewer color-scheme ownership changed",
                "color-scheme-ownership",
            )
        checks.require(not errors, f"reviewer browser errors: {errors}", "browser-errors")
    finally:
        page.close()


def main() -> None:
    checks = Checks()
    module = load_color_module()
    payloads = build_payloads(module)
    checks.require(len(payloads) == 56, f"expected 56 palettes, found {len(payloads)}", "coverage")
    checks.require(
        {item["flavor"] for item in payloads} == set(FLAVORS),
        "browser payload is missing a Catppuccin flavor",
        "coverage",
    )
    checks.require(
        {item["accentName"] for item in payloads} == set(ACCENTS),
        "browser payload is missing a Catppuccin accent",
        "coverage",
    )
    audit_runtime_source(checks)

    launch_options: dict[str, Any] = {"headless": True}
    requested_chrome = os.environ.get("PLAYWRIGHT_CHROME")
    if requested_chrome:
        launch_options["executable_path"] = requested_chrome
    elif LOCAL_CHROME.is_file():
        launch_options["executable_path"] = str(LOCAL_CHROME)

    with local_server() as base_url, sync_playwright() as playwright:
        browser = playwright.chromium.launch(**launch_options)
        try:
            audit_deck(browser, base_url, payloads, checks)
            audit_editor(browser, base_url, payloads, checks)
            audit_stats(browser, base_url, payloads, checks)
            audit_reviewer(browser, base_url, payloads, checks)
        finally:
            browser.close()

    ordered = ", ".join(f"{name}={count}" for name, count in sorted(checks.coverage.items()))
    print(
        "PASS Catppuccin Web runtime: "
        f"4 flavors x 14 accents x 4 live contexts; {checks.total} assertions"
    )
    print(f"Coverage: {ordered}")


if __name__ == "__main__":
    main()
