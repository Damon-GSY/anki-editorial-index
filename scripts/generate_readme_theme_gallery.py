#!/usr/bin/env python3
"""Render the README theme gallery from the shipped color contracts."""

from __future__ import annotations

from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
from pathlib import Path
import sys
from threading import Thread

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "screenshots" / "themes"
CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass


@contextmanager
def local_server():
    handler = partial(QuietHandler, directory=str(ROOT))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def load_color_module():
    path = ROOT / "addon" / "color_themes.py"
    spec = importlib.util.spec_from_file_location("editorial_colors", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def apply_tokens(page, module, config: dict[str, str], dark: bool) -> None:
    tokens = module.resolve_color_tokens(config, system_dark=dark)
    variables = module.web_color_variables(tokens)
    page.evaluate(
        """({ variables, family, flavor, accent, dark }) => {
          const root = document.documentElement;
          for (const [name, value] of Object.entries(variables)) {
            root.style.setProperty(name, value);
          }
          root.dataset.mistlineFamily = family;
          root.dataset.mistlinePalette = flavor;
          root.dataset.mistlineAccent = accent;
          root.dataset.mistlineTone = dark ? "dark" : "light";
          root.dataset.mistlineEnabled = "on";
          root.dataset.mistlineMotion = "off";
          root.classList.toggle("night-mode", dark);
        }""",
        {
            "variables": variables,
            "family": tokens.family,
            "flavor": tokens.flavor,
            "accent": tokens.accent_name,
            "dark": dark,
        },
    )


def render_interface_gallery(browser, module, base_url: str) -> None:
    themes = (
        (
            "editorial-light.png",
            {"color_theme": "editorial", "accent_color": "#2F5BBC"},
            False,
        ),
        (
            "editorial-dark.png",
            {"color_theme": "editorial", "accent_color": "#2F5BBC"},
            True,
        ),
        *(
            (
                f"catppuccin-{flavor}-blue.png",
                {
                    "color_theme": "catppuccin",
                    "catppuccin_flavor": flavor,
                    "catppuccin_accent": "blue",
                },
                flavor != "latte",
            )
            for flavor in ("latte", "frappe", "macchiato", "mocha")
        ),
    )

    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    fixture_url = (
        f"{base_url}/design-exploration/production-preview/index.html"
        "?context=deck-browser&state=deck"
    )
    for filename, config, dark in themes:
        page.goto(
            f"{fixture_url}&theme={'dark' if dark else 'light'}",
            wait_until="networkidle",
        )
        apply_tokens(page, module, config, dark)
        page.add_style_tag(
            content="""
              .fixture-label { display: none !important; }
              *, *::before, *::after {
                animation: none !important;
                transition: none !important;
              }
            """
        )
        page.evaluate("document.fonts.ready")
        page.screenshot(path=str(OUTPUT / filename), full_page=False)
    page.close()


def palette_markup(data: dict) -> str:
    order = data["token_order"]
    accents = data["accent_order"]

    panels: list[str] = []
    for flavor_key, flavor in data["flavors"].items():
        palette = {
            name: flavor["hex"][index] for index, name in enumerate(order)
        }
        swatches = "".join(
            f"""
              <div class="swatch">
                <div class="color" style="background:{palette[name]}"></div>
                <strong>{name.capitalize()}</strong>
                <span>{palette[name].upper()}</span>
              </div>
            """
            for name in accents
        )
        panels.append(
            f"""
              <section class="panel" style="
                --base:{palette['base']};
                --mantle:{palette['mantle']};
                --surface:{palette['surface0']};
                --surface-strong:{palette['surface1']};
                --text:{palette['text']};
                --muted:{palette['subtext0']};
                --accent:{palette['blue']};
              ">
                <header>
                  <div>
                    <p>{flavor['emoji']} CATPPUCCIN</p>
                    <h2>{flavor['name']}</h2>
                  </div>
                  <span>{'Dark' if flavor['dark'] else 'Light'} flavor</span>
                </header>
                <div class="swatches">{swatches}</div>
              </section>
            """
        )

    return f"""<!doctype html>
      <html lang="en">
        <head>
          <meta charset="utf-8">
          <style>
            @font-face {{
              font-family: Inter;
              src: url('/addon/web/fonts/inter-regular.woff2') format('woff2');
              font-weight: 400;
            }}
            @font-face {{
              font-family: Inter;
              src: url('/addon/web/fonts/inter-semibold.woff2') format('woff2');
              font-weight: 600;
            }}
            * {{ box-sizing: border-box; }}
            html, body {{ margin: 0; min-height: 100%; }}
            body {{
              width: 1800px;
              padding: 64px;
              color: #252521;
              background: #f4f1ea;
              font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
            }}
            .intro {{
              display: flex;
              align-items: end;
              justify-content: space-between;
              margin-bottom: 32px;
            }}
            .intro p {{
              margin: 0 0 8px;
              color: #68655e;
              font-size: 18px;
              font-weight: 600;
              letter-spacing: .12em;
              text-transform: uppercase;
            }}
            .intro h1 {{ margin: 0; font-size: 46px; letter-spacing: -.04em; }}
            .intro > span {{ color: #68655e; font-size: 20px; }}
            .gallery {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }}
            .panel {{
              min-width: 0;
              padding: 28px;
              border: 1px solid var(--surface-strong);
              border-radius: 22px;
              color: var(--text);
              background: var(--base);
              box-shadow: 0 12px 28px color-mix(in srgb, var(--mantle) 72%, transparent);
            }}
            .panel header {{
              display: flex;
              align-items: end;
              justify-content: space-between;
              margin-bottom: 22px;
            }}
            .panel header p {{
              margin: 0 0 5px;
              color: var(--accent);
              font-size: 12px;
              font-weight: 600;
              letter-spacing: .14em;
            }}
            .panel h2 {{ margin: 0; font-size: 30px; letter-spacing: -.03em; }}
            .panel header > span {{ color: var(--muted); font-size: 15px; }}
            .swatches {{ display: grid; grid-template-columns: repeat(7, 1fr); gap: 10px; }}
            .swatch {{
              min-width: 0;
              padding: 8px;
              border: 1px solid var(--surface-strong);
              border-radius: 12px;
              background: var(--mantle);
            }}
            .color {{ height: 54px; margin-bottom: 9px; border-radius: 7px; }}
            .swatch strong, .swatch span {{ display: block; overflow: hidden; }}
            .swatch strong {{ font-size: 12px; line-height: 1.3; text-overflow: ellipsis; }}
            .swatch span {{ margin-top: 2px; color: var(--muted); font-size: 10px; }}
          </style>
        </head>
        <body>
          <div class="intro">
            <div>
              <p>Editorial Index palette reference</p>
              <h1>Catppuccin · 4 flavors × 14 accents</h1>
            </div>
            <span>Official palette v{data['source_version']}</span>
          </div>
          <main class="gallery">{''.join(panels)}</main>
        </body>
      </html>"""


def render_palette_matrix(browser, base_url: str) -> None:
    data = json.loads(
        (ROOT / "addon" / "catppuccin.json").read_text(encoding="utf-8")
    )
    page = browser.new_page(viewport={"width": 1800, "height": 1100})
    page.goto(base_url, wait_until="domcontentloaded")
    page.set_content(palette_markup(data), wait_until="networkidle")
    page.evaluate("document.fonts.ready")
    page.screenshot(
        path=str(OUTPUT / "catppuccin-accent-matrix.png"), full_page=True
    )
    page.close()


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    module = load_color_module()
    launch_options = {"headless": True}
    if CHROME.exists():
        launch_options["executable_path"] = str(CHROME)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(**launch_options)
        try:
            with local_server() as base_url:
                render_interface_gallery(browser, module, base_url)
                render_palette_matrix(browser, base_url)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
