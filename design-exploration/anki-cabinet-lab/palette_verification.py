"""Exercise the production palette dialog in the marked, disposable Anki lab."""

from pathlib import Path
import os

from aqt import gui_hooks
from aqt.qt import QLabel, QPoint, QPushButton, QRect, QScrollArea, QTabWidget, Qt
from aqt.webview import AnkiWebView


class PaletteVerification:
    def __init__(self, driver):
        self.d, self.mw, self.addon = driver, driver.mw, driver.production_addon
        scratch = Path(driver.report["scratch"])
        if not scratch.name.startswith("anki-cabinet-lab-") or not (scratch / ".CABINET_LAB_ONLY.json").is_file():
            raise RuntimeError("Palette verification requires the disposable lab")
        self.before = self.fingerprint()
        self.hooks_before = self.hooks()
        self.rating_colors = {}
        self.cases = [(flavor, accent) for flavor in ("latte", "frappe", "macchiato", "mocha")
                      for accent in self.addon.CATPPUCCIN_ACCENTS]
        self.d.js("""(()=>{window._paletteHome=document.querySelector('#cabinet-home');
          const c=[...document.querySelectorAll('.cabinet-display-controls button')],
            footer=document.querySelector('.cabinet-folder-footer'), f=[...footer.children],
            box=e=>e.getBoundingClientRect(),css=e=>getComputedStyle(e);
          return {margins:[...document.querySelectorAll('#cabinet-home button')].every(b=>
            ['marginLeft','marginRight','marginTop','marginBottom'].every(p=>parseFloat(css(b)[p])===0)),
            controls:c.slice(1).filter((b,i)=>Math.abs(box(b).top-box(c[i]).top)<1).map((b)=>{
              const i=c.indexOf(b);return box(b).left-box(c[i-1]).right;}),
            footer:box(f[1]).left-box(f[0]).right};})()""", self.home_spacing)

    def home_spacing(self, result):
        self.d.check("Homepage spacing is not doubled by native button margins", result["margins"]
                     and all(abs(gap - 8) <= 1 for gap in result["controls"])
                     and abs(result["footer"] - 10) <= 1, result)
        self.open(self.opened)

    def fingerprint(self):
        return (self.mw.col.db.all("select id,did,queue,type,due,ivl,factor,reps,lapses from cards order by id"),
                self.mw.col.db.all("select id,mid,flds,tags from notes order by id"),
                self.mw.col.db.scalar("select count(*) from revlog"))

    @staticmethod
    def hooks():
        return (gui_hooks.theme_did_change.count(), gui_hooks.body_classes_need_update.count())

    def open(self, then):
        self.d.click('[data-cabinet-display="palette"]', lambda: self.d.later(450, then))

    def button(self, name):
        button = self.dialog.findChild(QPushButton, name)
        if button is None:
            raise AssertionError("Missing native palette button: " + name)
        return button

    def opened(self):
        self.dialog = self.addon._palette_dialog_ref()
        self.d.check("Homepage palette entry opens a native dialog", self.dialog is not None and self.dialog.isVisible())
        self.web = self.dialog.findChild(AnkiWebView, "EditorialIndexPalettePreview")
        self.d.check("Palette preview is an isolated AnkiWebView", self.web is not None and not self.web.requiresCol
                     and self.addon._webview_context(self.web) is None)
        self.open(self.same_dialog)

    def same_dialog(self):
        self.d.check("Opening palette twice reuses its live native dialog", self.addon._palette_dialog_ref() is self.dialog
                     and self.hooks() == tuple(n + 1 for n in self.hooks_before))
        self.check_native_spacing("default")
        self.initial_geometry = self.choice_geometry()
        self.button("PaletteAccent_green").setFocus(Qt.FocusReason.TabFocusReason)
        self.d.later(150, self.focused_choice)

    def focused_choice(self):
        self.d.check("Keyboard focus preserves palette tile positions and sizes",
                     self.choice_geometry() == self.initial_geometry
                     and self.button("PaletteAccent_green").hasFocus())
        self.button("PaletteAccent_green").clearFocus()
        self.index = 0
        self.next_pair()

    def choice_geometry(self):
        return {b.objectName(): b.geometry().getRect() for b in self.dialog.findChildren(QPushButton)
                if b.objectName().startswith(("PaletteFlavor_", "PaletteAccent_"))}

    def check_native_spacing(self, size):
        def rect(widget):
            return QRect(widget.mapTo(self.dialog, QPoint(0, 0)), widget.size())

        for prefix in ("PaletteFlavor_", "PaletteAccent_"):
            buttons = [b for b in self.dialog.findChildren(QPushButton) if b.objectName().startswith(prefix)]
            widths, heights = [b.width() for b in buttons], [b.height() for b in buttons]
            self.d.check(size + " equal palette tile sizes: " + prefix,
                         max(widths) - min(widths) <= 1 and max(heights) - min(heights) <= 1,
                         {"widths": widths, "heights": heights})
            rows = sorted({b.y() for b in buttons})
            row_gaps = [rows[i] - rows[i - 1] - heights[0] for i in range(1, len(rows))]
            self.d.check(size + " palette row gaps never overlap: " + prefix,
                         all(gap == 8 for gap in row_gaps), {"gaps": row_gaps})
        labels = {label.text(): label for label in self.dialog.findChildren(QLabel)}
        flavor_bottom = max(rect(self.button("PaletteFlavor_" + name)).bottom() + 1
                            for name in ("editorial", "auto", "latte", "frappe", "macchiato", "mocha"))
        accent_top = min(rect(self.button("PaletteAccent_" + name)).top() for name in self.addon.CATPPUCCIN_ACCENTS)
        label = rect(labels["强调色 · 14 种"])
        gap_before, gap_after = label.top() - flavor_bottom, accent_top - label.bottom() - 1
        self.d.check(size + " palette groups have a clear spacing hierarchy",
                     gap_before >= 18 and 6 <= gap_after <= 10,
                     {"groupGap": gap_before, "labelGap": gap_after})
        scroll = self.dialog.findChild(QScrollArea, "EditorialIndexPaletteScroll")
        self.d.check(size + " palette choices never scroll horizontally", scroll.horizontalScrollBar().maximum() == 0)
        if size == "default":
            self.d.check("Default palette shows all choices without scrolling", scroll.verticalScrollBar().maximum() == 0)

    def preview_state(self, then):
        self.d.js("""(()=>{const root=document.documentElement, buttons=[...document.querySelectorAll('#middle button[data-ease]')];
          const css=e=>getComputedStyle(e), box=e=>e.getBoundingClientRect();
          const canvas=document.createElement('canvas');canvas.width=canvas.height=1;const ctx=canvas.getContext('2d',{willReadFrequently:true});
          const rgb=c=>{ctx.clearRect(0,0,1,1);ctx.fillStyle=c;ctx.fillRect(0,0,1,1);return [...ctx.getImageData(0,0,1,1).data].slice(0,3)};
          const lum=c=>rgb(c).map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4}).reduce((sum,v,i)=>sum+v*[.2126,.7152,.0722][i],0);
          const ratio=(a,b)=>{const x=lum(a),y=lum(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05)};
          const answer=document.querySelector('#ansbut'),answerStyle=css(answer);
          const heading=box(document.querySelector('.palette-preview-heading')),first=box(buttons[0]),last=box(buttons[3]);return {
            flavor:root.dataset.mistlinePalette,accent:root.dataset.mistlineAccent,
            colors:buttons.map(b=>css(b).color),
            inert:buttons.length===4&&buttons.every(b=>b.disabled&&!b.hasAttribute('onclick')),
            accentRaw:'rgb('+rgb(css(root).getPropertyValue('--mist-accent-fill').trim()).join(', ')+')',
            answer:{color:answerStyle.color,background:answerStyle.backgroundColor,contrast:ratio(answerStyle.color,answerStyle.backgroundColor)},
            noOverflow:root.scrollWidth<=innerWidth+2&&root.scrollHeight<=innerHeight+2,
            spacing:{left:Math.abs(first.left-heading.left),right:Math.abs(last.right-heading.right),
              top:heading.top,bottom:innerHeight-last.bottom,gap:first.top-heading.bottom},
            fonts:document.fonts.status,
            stylesheet:[...document.querySelectorAll('link[rel=stylesheet]')].some(l=>!l.disabled&&l.href.endsWith('/cabinet.css'))
          };})()""", then, self.web)

    def next_pair(self):
        if self.index == len(self.cases):
            self.d.check("All 56 Catppuccin combinations preserve semantic rating colors", len(self.rating_colors) == 4)
            self.extra_flavors()
            return
        self.flavor, self.accent = self.cases[self.index]
        if self.index % len(self.addon.CATPPUCCIN_ACCENTS) == 0:
            self.button("PaletteFlavor_" + self.flavor).click()
        self.button("PaletteAccent_" + self.accent).click()
        self.d.later(210, lambda: self.preview_state(self.check_pair))

    def check_pair(self, preview):
        config = self.addon._get_config()
        label = self.flavor + " / " + self.accent
        expected = self.addon._resolved_tokens(config)
        geometry = self.choice_geometry()
        self.d.check("Palette selection does not shift tiles: " + label,
                     geometry == self.initial_geometry,
                     {name: {"before": self.initial_geometry[name], "after": rect}
                      for name, rect in geometry.items() if rect != self.initial_geometry[name]})
        spacing = preview["spacing"]
        self.d.check("Preview alignment and breathing room: " + label,
                     spacing["left"] <= 1 and spacing["right"] <= 1
                     and 12 <= spacing["top"] <= 24 and 12 <= spacing["bottom"] <= 24
                     and 12 <= spacing["gap"] <= 20, spacing)
        self.d.check("Native palette selection and preview: " + label,
                     config["color_theme"] == "catppuccin" and config["catppuccin_flavor"] == self.flavor
                     and config["catppuccin_accent"] == self.accent
                     and preview["flavor"] == self.flavor and preview["accent"] == self.accent
                     and preview["inert"] and preview["stylesheet"]
                     and self.button("PaletteFlavor_" + self.flavor).isChecked()
                     and self.button("PaletteAccent_" + self.accent).isChecked(), preview)
        self.rating_colors.setdefault(self.flavor, preview["colors"])
        self.d.check("Semantic ratings stay distinct and independent of accent: " + label,
                     len(set(preview["colors"])) == 4 and preview["colors"] == self.rating_colors[self.flavor])
        self.d.check("Answer preview remains readable with a soft accent surface: " + label,
                     preview["answer"]["contrast"] >= 4.5, preview["answer"])

        def after_home(home):
            rgb = "rgb(" + ", ".join(str(int(expected.accent[i:i + 2], 16)) for i in (1, 3, 5)) + ")"
            self.d.check("Homepage badge updates without rebuilding decks: " + label,
                         home["same"] and home["flavor"] == self.flavor.capitalize()
                         and home["swatch"] == rgb and home["swatch"] == preview["accentRaw"]
                         and self.accent in home["accessible"], home)
            if self.accent == "blue" and self.flavor in {"latte", "mocha"}:
                self.capture("24-palette-latte" if self.flavor == "latte" else "25-palette-mocha")
            self.index += 1
            self.next_pair()

        self.d.js("""(()=>{const b=document.querySelector('.cabinet-palette');return {
          same:window._paletteHome===document.querySelector('#cabinet-home'),
          flavor:b.querySelector('.cabinet-palette-current').textContent,
          swatch:getComputedStyle(b.querySelector('.cabinet-palette-swatch')).backgroundColor,
          accessible:b.getAttribute('aria-label')};})()""", after_home)

    def extra_flavors(self):
        self.button("PaletteFlavor_editorial").click()
        self.d.check("Warm-paper choice disables Catppuccin accent controls",
                     self.addon._get_config()["color_theme"] == "editorial"
                     and not self.button("PaletteAccent_blue").isEnabled())
        self.button("PaletteFlavor_auto").click()
        self.d.check("Automatic flavor remains available", self.addon._get_config()["catppuccin_flavor"] == "auto"
                     and self.button("PaletteFlavor_auto").isChecked())
        self.button("PaletteFlavor_latte").click()
        self.button("PaletteAccent_blue").click()
        self.dialog.resize(680, 600)
        self.d.later(450, self.narrow_dialog)

    def narrow_dialog(self):
        def inside(widget):
            return widget.isVisible() and self.dialog.rect().contains(QRect(widget.mapTo(self.dialog, QPoint(0, 0)), widget.size()))
        tabs = self.dialog.findChild(QTabWidget, "EditorialIndexPaletteTabs")
        self.d.check("680 × 600 palette keeps preview and Close inside its window",
                     self.dialog.width() == 680 and self.dialog.height() == 600
                     and inside(self.web) and inside(self.button("PaletteClose")),
                     {"width": self.dialog.width(), "height": self.dialog.height()})
        self.check_native_spacing("compact")
        self.capture("26-palette-compact")
        tabs.setCurrentIndex(1)
        self.d.check("Semantic role details remain available", tabs.currentWidget().isVisible())
        panel = tabs.currentWidget()
        margins = panel.layout().contentsMargins()
        self.d.check("Semantic detail tiles have room inside their panel",
                     min(margins.left(), margins.top(), margins.right(), margins.bottom()) >= 12)
        self.capture("27-palette-semantic-spacing")
        tabs.setCurrentIndex(0)
        self.preview_state(self.check_narrow_preview)

    def check_narrow_preview(self, preview):
        self.d.check("Small-window preview has no clipped content or overflow", preview["noOverflow"], preview)
        spacing = preview["spacing"]
        self.d.check("Small-window preview keeps aligned edges and balanced padding",
                     spacing["left"] <= 1 and spacing["right"] <= 1
                     and 12 <= spacing["top"] <= 24 and 12 <= spacing["bottom"] <= 24, spacing)
        self.saved_display = self.addon._get_config()["cabinet_display"]
        self.d.js("""(()=>{pycmd('ease3');pycmd('ans');pycmd('editorial-cabinet:fold-all');
          pycmd('editorial-cabinet:settings');return true;})()""",
                  lambda _: self.d.later(250, self.check_isolation), self.web)

    def check_isolation(self):
        self.d.check("Preview bridge cannot grade cards or change cabinet visibility",
                     self.fingerprint() == self.before
                     and self.addon._get_config()["cabinet_display"] == self.saved_display
                     and self.mw.state == "deckBrowser"
                     and getattr(self.mw, "_editorial_cabinet_display_dialog", None) is None)
        self.button("PaletteClose").click()
        self.d.later(300, self.closed)

    def closed(self):
        self.d.check("Closing palette releases dialog reference and WebView hooks",
                     self.addon._palette_dialog_ref is None and self.hooks() == self.hooks_before)
        self.old_dialog = self.dialog
        self.open(self.reopened)

    def reopened(self):
        self.dialog = self.addon._palette_dialog_ref()
        self.d.check("Closed palette reopens as a fresh dialog with saved choices",
                     self.dialog is not self.old_dialog and self.dialog.isVisible()
                     and self.button("PaletteFlavor_latte").isChecked()
                     and self.button("PaletteAccent_blue").isChecked())
        self.button("PaletteClose").click()
        self.d.later(300, self.finish)

    def finish(self):
        self.d.check("Repeated palette usage leaves no hooks or collection changes",
                     self.hooks() == self.hooks_before and self.fingerprint() == self.before)
        self.d.finish()

    def capture(self, name):
        directory = Path(os.environ["ANKI_CABINET_LAB_OUTPUT"]) / "screenshots"
        directory.mkdir(exist_ok=True)
        path = directory / (name + ".png")
        self.d.check("Qt palette screenshot " + name, self.dialog.grab().save(str(path)))
        self.d.report["screenshots"].append(str(path))
