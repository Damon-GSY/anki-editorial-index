"""Real Qt/Anki test driver. All collection mutations target generated lab data."""

import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback

BASE = Path(os.environ["ANKI_CABINET_LAB_BASE"]).resolve()
OUTPUT = Path(os.environ["ANKI_CABINET_LAB_OUTPUT"]).resolve()
MODE = os.environ.get("ANKI_CABINET_LAB_MODE", "verify")
PACKAGE = os.environ.get("ANKI_CABINET_LAB_ADDON", "cabinet_lab")
if PACKAGE not in {"cabinet_lab", "mistline_ui"}:
    raise RuntimeError("Unexpected lab add-on package")
PRODUCTION = PACKAGE == "mistline_ui"
ADDON = BASE / "addons21" / PACKAGE
if not BASE.name.startswith("anki-cabinet-lab-") or not (BASE / ".CABINET_LAB_ONLY.json").is_file():
    raise RuntimeError("Refusing to run outside a marked disposable lab")
if BASE == Path.home() / "Library/Application Support/Anki2":
    raise RuntimeError("The real Anki profile is forbidden")

import anki
import anki.lang
import aqt
from aqt import gui_hooks
from aqt.profiles import ProfileManager
from aqt.qt import QTimer, QT_VERSION_STR, QMessageBox, QAction, QEvent


if PRODUCTION:
    # Reproduce the user's installed answer-colour add-on without loading any
    # user add-ons or collection. Native labels/commands stay unchanged.
    def legacy_answer_colours(buttons, _reviewer, _card):
        colours = ("red", "darkorange", "green", "blue")
        return tuple((ease, f'<font color="{colours[ease - 1]}">{label}</font>')
                     for ease, label in buttons)
    gui_hooks.reviewer_will_init_answer_buttons.append(legacy_answer_colours)


PROFILE = "CABINET LAB — Demo data only"
class LabApp(aqt.AnkiApp):
    KEY = "anki-cabinet-lab-" + hashlib.sha256(str(BASE).encode()).hexdigest()[:20]

    def event(self, event):
        # macOS's Python launcher can send its .py file as a FileOpen event.
        # It is not a deck import request. Ignore only our exact driver path.
        if event.type() == QEvent.Type.FileOpen and event.file() == str(Path(__file__).resolve()):
            return True
        return super().event(event)


aqt.AnkiApp = LabApp
anki.lang.set_lang("en")
pm = ProfileManager(BASE)
pm.setupMeta()
pm.create(PROFILE)
pm.load(PROFILE)
pm.meta.update(firstRun=False, defaultLang="en", check_for_updates=False,
               check_for_addon_updates=False)
pm.profile.update(autoSync=False, syncMedia=False, syncKey=None, numBackups=0)
pm.save()
pm.db.close()


def seed(col):
    """Create stock note types and self-contained media, never import a collection."""
    from anki.stdmodels import get_stock_notetypes
    stock = get_stock_notetypes(col)
    models = {}
    for label, position in (("basic", 0), ("typing", 3), ("cloze", 4)):
        model = stock[position][1](col)
        model["name"] = "Cabinet Lab " + label
        col.models.add(model)
        models[label] = model
    decks = {}
    records = [
        ("english", "LAB · English", "basic", ["What is spaced repetition?", "Reviewing knowledge at increasing intervals."]),
        ("typing", "LAB · Type answer", "typing", ["陷入孤立无援的处境", "be out on a limb"]),
        ("cloze", "LAB · Cloze", "cloze", ["Spaced repetition strengthens {{c1::long-term memory}}.", "A stock cloze template; no rewritten fields."]),
        ("media", "LAB · Media", "basic", ["<img src='cabinet-lab-shapes.svg' width='320'><br>What is the area of a circle?", r"\(A=\pi r^2\)<br>Images and MathJax remain in the original card template."]),
    ]
    for key, name, kind, fields in records:
        did = col.decks.id(name)
        note = col.new_note(models[kind])
        note.fields = fields
        note.tags = ["cabinet-lab-generated"]
        col.add_note(note, did)
        decks[key] = int(did)
    # A second English note makes post-grade advancement observable.
    note = col.new_note(models["basic"])
    note.fields = ["What does recall mean?", "Bringing learned information back to mind."]
    note.tags = ["cabinet-lab-generated"]
    col.add_note(note, decks["english"])
    nested = col.decks.id("LAB · English::Phrases")
    note = col.new_note(models["basic"])
    note.fields = ["Take your time.", "慢慢来。"]
    note.tags = ["cabinet-lab-generated"]
    col.add_note(note, nested)
    decks["phrases"] = int(nested)
    decks["empty"] = int(col.decks.id("LAB · Empty deck"))
    svg = '<svg xmlns="http://www.w3.org/2000/svg" width="320" height="180" viewBox="0 0 320 180"><rect width="320" height="180" rx="18" fill="#f1edf6"/><circle cx="160" cy="90" r="56" fill="#b6a0cc"/><path d="M160 90h56" stroke="#433550" stroke-width="3"/><text x="181" y="81" font-family="sans-serif" fill="#433550">r</text></svg>'
    col.media.write_data("cabinet-lab-shapes.svg", svg.encode())
    col.decks.select(decks["english"])
    return decks


class Driver:
    def __init__(self):
        self.mw = aqt.mw
        self.finished = False
        self.started = time.monotonic()
        self.report = {"runtime": "real aqt.AnkiQt + Qt WebEngine + Rust collection/scheduler",
                       "anki": anki.version, "qt": QT_VERSION_STR, "mode": MODE,
                       "addon_package": PACKAGE, "production_addon": PRODUCTION,
                       "scratch": str(BASE), "profile": PROFILE,
                       "user_collection_accessed": False, "checks": [], "screenshots": []}
        self.report["addon_sha256"] = {
            str(path.relative_to(ADDON)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in ADDON.rglob("*")
            if path.is_file() and path.suffix in {".py", ".js", ".css", ".json"}
        }
        self.decks = seed(self.mw.col)
        self.mw.resize(1280, 860)
        self.mw.setWindowTitle("Anki · 卡匣验证 — 仅生成的测试数据")
        if PRODUCTION:
            self.mw.setWindowTitle("Anki · 卡匣生产代码验证 — 仅生成的测试数据")
        self.mw.reset()
        self.report["generated_note_count"] = self.mw.col.note_count()
        if MODE == "open":
            (BASE / "demo-info.json").write_text(json.dumps(self.report, ensure_ascii=False, indent=2))
            print("Isolated Anki demo ready. Close this window normally when finished.", flush=True)
        elif MODE == "palette":
            self.production_addon = sys.modules[PACKAGE]
            self.later(2000, self.start_palette_checks)
        elif MODE == "footer":
            self.production_addon = sys.modules[PACKAGE]
            self.later(1600, self.start_footer_checks)
        else:
            self.later(1600, self.home)

    def start_palette_checks(self):
        from palette_verification import PaletteVerification
        self.palette_verification = PaletteVerification(self)

    def start_footer_checks(self):
        self.mw.moveToState("overview")
        self.wait(lambda: self.mw.state == "overview", lambda: self.study(self.footer_question),
                  "native overview for footer verification")

    def footer_question(self):
        self.wait(lambda: self.mw.reviewer.state == "question" and self.mw.bottomWeb.isVisible(),
                  lambda: self.footer_state("latte-mauve", self.footer_latte_checked),
                  "native question footer")

    def footer_state(self, label, then):
        script = """(()=>{
          const canvas=document.createElement('canvas');canvas.width=canvas.height=1;
          const ctx=canvas.getContext('2d',{willReadFrequently:true});
          const css=e=>getComputedStyle(e);
          const rgb=c=>{ctx.clearRect(0,0,1,1);ctx.fillStyle=c;ctx.fillRect(0,0,1,1);return [...ctx.getImageData(0,0,1,1).data].slice(0,3)};
          const lum=c=>rgb(c).map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4}).reduce((sum,v,i)=>sum+v*[.2126,.7152,.0722][i],0);
          const ratio=(a,b)=>{const x=lum(a),y=lum(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05)};
          const button=document.querySelector('#ansbut'),stats=button?.querySelector('.stattxt'),root=document.documentElement;
          const outer=document.querySelector('#outer'),left=document.querySelector('.stat:first-child button'),right=document.querySelector('.stat:last-child button');
          const b=button?.getBoundingClientRect(),s=stats?.getBoundingClientRect(),o=outer?.getBoundingClientRect();
          const bs=button&&getComputedStyle(button),ss=stats&&getComputedStyle(stats),os=outer&&getComputedStyle(outer),bodyStyle=getComputedStyle(document.body);
          const countTokens={new:'--mist-new',learn:'--mist-learn',review:'--mist-due'};
          const semanticCounts=[...stats.querySelectorAll('.new-count,.learn-count,.review-count')].map(node=>{
            const role=node.className.replace('-count',''),style=getComputedStyle(node);
            return {role,color:'rgb('+rgb(style.color).join(', ')+')',token:'rgb('+rgb(css(root).getPropertyValue(countTokens[role]).trim()).join(', ')+')',contrast:ratio(style.color,bodyStyle.backgroundColor)};
          });
          return {label:LABEL,text:stats?.innerText.trim(),onclick:button?.getAttribute('onclick'),
            button:{left:b?.left,right:b?.right,top:b?.top,bottom:b?.bottom,width:b?.width,height:b?.height,color:bs?.color,background:bs?.backgroundColor,contrast:bs&&ratio(bs.color,bs.backgroundColor)},
            stats:{top:s?.top,bottom:s?.bottom,color:ss?.color,contrast:ss&&ratio(ss.color,bodyStyle.backgroundColor),semanticCounts},
            outer:{top:o?.top,bottom:o?.bottom,left:o?.left,right:o?.right,padding:os?.padding},
            sideCenterDelta:Math.max(Math.abs((left.getBoundingClientRect().top+left.getBoundingClientRect().bottom-b.top-b.bottom)/2),Math.abs((right.getBoundingClientRect().top+right.getBoundingClientRect().bottom-b.top-b.bottom)/2)),
            overflow:document.documentElement.scrollWidth>innerWidth+1||document.documentElement.scrollHeight>innerHeight+1,
            palette:document.documentElement.dataset.mistlinePalette,accent:document.documentElement.dataset.mistlineAccent};
        })()""".replace("LABEL", json.dumps(label))
        self.js(script, lambda state: self.footer_state_checked(label, state, then), self.mw.bottomWeb)

    def footer_state_checked(self, label, state, then):
        button, stats, outer = state["button"], state["stats"], state["outer"]
        self.check(label + " keeps the native Show Answer command", state["onclick"] == 'pycmd("ans");', state)
        self.check(label + " uses a restrained answer button", 240 <= button["width"] <= 320 and 48 <= button["height"] <= 52, state)
        self.check(label + " separates readable counts above the button",
                   bool(state["text"]) and stats["bottom"] <= button["top"] - 2 and stats["top"] >= outer["top"] + 2
                   and button["contrast"] >= 4.5 and stats["contrast"] >= 4.5, state)
        self.check(label + " preserves new, learn, and review count colors",
                   [item["role"] for item in stats["semanticCounts"]] == ["new", "learn", "review"]
                   and all(item["color"] == item["token"] and item["contrast"] >= 4.5
                           for item in stats["semanticCounts"]), state)
        self.check(label + " aligns side actions to the visible answer control",
                   state["sideCenterDelta"] <= 1 and not state["overflow"], state)
        self.report.setdefault("reviewer_footer", []).append(state)
        self.capture("footer-" + label)
        if label == "latte-mauve":
            self.capture_footer("footer-latte-mauve-question")
        then()

    def footer_latte_checked(self):
        self.mw.resize(820, 760)
        self.later(450, lambda: self.footer_state("latte-mauve-820", self.footer_narrow_checked))

    def footer_narrow_checked(self):
        self.mw.resize(1280, 860)
        self.production_addon._select_palette("mocha")
        self.later(500, lambda: self.footer_state("mocha-mauve", self.footer_mocha_checked))

    def footer_mocha_checked(self):
        self.mw.col.conf["dueCounts"] = False
        self.mw.reviewer._showAnswerButton()
        self.later(350, self.footer_counts_off)

    def footer_counts_off(self):
        self.js("""(()=>{const b=document.querySelector('#ansbut').getBoundingClientRect(),s=document.querySelector('#ansbut .stattxt').getBoundingClientRect();return {text:document.querySelector('#ansbut .stattxt').innerText.trim(),buttonTop:b.top,statsWidth:s.width,statsHeight:s.height,onclick:document.querySelector('#ansbut').getAttribute('onclick')}})()""",
                self.footer_counts_off_checked, self.mw.bottomWeb)

    def footer_counts_off_checked(self, state):
        self.check("Disabled remaining counts leave no empty reserved row",
                   not state["text"] and state["buttonTop"] <= 26 and state["statsWidth"] == 0
                   and state["onclick"] == 'pycmd("ans");', state)
        self.mw.col.conf["dueCounts"] = True
        self.production_addon._select_palette("latte")
        self.mw.reviewer._showAnswerButton()
        self.later(250, lambda: self.show_answer(self.footer_answer))

    def footer_answer(self):
        self.js("""(()=>{const buttons=[...document.querySelectorAll('#middle button[data-ease]')],left=document.querySelector('.stat:first-child button'),right=document.querySelector('.stat:last-child button'),first=buttons[0].getBoundingClientRect();const center=r=>(r.top+r.bottom)/2;return {count:buttons.length,commands:buttons.map(b=>b.getAttribute('onclick')),inside:buttons.every(b=>{const r=b.getBoundingClientRect();return r.top>=0&&r.bottom<=innerHeight&&r.left>=0&&r.right<=innerWidth}),sideCenterDelta:Math.max(Math.abs(center(left.getBoundingClientRect())-center(first)),Math.abs(center(right.getBoundingClientRect())-center(first)))}})()""",
                self.footer_answer_checked, self.mw.bottomWeb)

    def footer_answer_checked(self, state):
        self.check("Question to answer keeps native ratings visible and wired",
                   state["count"] == 4 and state["inside"] and state["sideCenterDelta"] <= 1
                   and state["commands"] == ['pycmd("ease1");','pycmd("ease2");','pycmd("ease3");','pycmd("ease4");'], state)
        self.capture("footer-answer-latte-mauve")
        self.capture_footer("footer-latte-mauve-answer")
        self.finish()

    def later(self, ms, fn):
        def call():
            if self.finished:
                return
            try:
                fn()
            except Exception:
                self.fail(traceback.format_exc())
        QTimer.singleShot(ms, call)

    def check(self, name, passed, details=None):
        item = {"name": name, "passed": bool(passed)}
        if details is not None:
            item["details"] = details
        self.report["checks"].append(item)
        print(json.dumps(item, ensure_ascii=False), flush=True)
        if not passed:
            raise AssertionError(name)

    def wait(self, predicate, then, label, timeout=12):
        deadline = time.monotonic() + timeout
        def tick():
            if predicate():
                self.later(650, then)
            elif time.monotonic() >= deadline:
                raise TimeoutError(label)
            else:
                self.later(150, tick)
        self.later(100, tick)

    def js(self, expression, callback, web=None):
        def done(value):
            try:
                callback(value)
            except Exception:
                self.fail(traceback.format_exc())
        (web or self.mw.web).evalWithCallback(expression, done)

    def capture(self, name):
        folder = OUTPUT / "screenshots"
        folder.mkdir(exist_ok=True)
        path = folder / (name + ".png")
        self.check("Qt screenshot " + name, self.mw.grab().save(str(path)))
        self.report["screenshots"].append(str(path))

    def capture_footer(self, name):
        folder = OUTPUT / "screenshots"
        folder.mkdir(exist_ok=True)
        path = folder / (name + "-bottom-web.png")
        self.check("Qt reviewer footer screenshot " + name, self.mw.bottomWeb.grab().save(str(path)))
        self.report["screenshots"].append(str(path))

    def click(self, selector, then, web=None):
        script = "(()=>{const e=document.querySelector(" + json.dumps(selector) + "); if(!e)return false;e.click();return true})()"
        self.js(script, lambda ok: (self.check("native-linked control " + selector, ok), then()), web)

    def home(self):
        self.js("""(()=>{const home=document.querySelector('#cabinet-home');return {
            home:!!home, folders:document.querySelectorAll('.cabinet-folder').length,
            visible:!!home&&home.checkVisibility({checkOpacity:true,checkVisibilityCSS:true})&&home.getBoundingClientRect().height>50,
            fonts:document.fonts.status,
            overflow:document.documentElement.scrollWidth>innerWidth+2
        }})()""", self.after_home)

    def after_home(self, dom):
        if dom["folders"] != 5 and getattr(self, "home_refreshes", 0) < 3:
            # Seeding bypasses normal CollectionOp UI callbacks, so Anki's
            # initial empty-profile async render may finish after seed/reset.
            # Request a fresh native render before checking generated controls.
            self.home_refreshes = getattr(self, "home_refreshes", 0) + 1
            self.mw.deckBrowser.refresh()
            self.later(900, self.home)
            return
        self.check("Cabinet rendered in actual Anki deck browser", dom["home"], dom)
        self.check("Native deck render includes all generated root decks", dom["folders"] == 5, dom)
        self.check("Cabinet home is visible in real WebView layout", dom["visible"], dom)
        self.check("Home has no horizontal overflow", not dom["overflow"])
        # Qt WebEngine can report a complete DOM before its first GPU texture
        # is presented. Prime the native grab, then give Qt a paint cycle; never
        # substitute a browser rendering or a synthesized screenshot.
        self.mw.grab()
        self.later(700, self.capture_home)

    def capture_home(self):
        self.capture("01-home")
        self.js("({html:document.body.innerHTML,nav:[...document.querySelectorAll('a,button')].map(e=>({tag:e.tagName,id:e.id,classes:e.className,text:e.innerText,padding:getComputedStyle(e).padding,display:getComputedStyle(e).display}))})", lambda data: self.report.update(toolbar_dom=data), self.mw.toolbarWeb)
        if PRODUCTION:
            self.verify_heatmap_css("Cabinet", self.expand_child_deck)
        else:
            self.open_deck("english", self.overview)

    def verify_heatmap_css(self, label, then):
        script = """(()=>{
          const imported=[],errors=[],seen=new Set();
          const walk=sheet=>{
            if(!sheet||sheet.disabled||seen.has(sheet))return;
            seen.add(sheet);
            try {
              const rules=[...sheet.cssRules];
              if(sheet.href?.includes('/heatmap.css')) imported.push({
                href:sheet.href,rules:rules.length,
                heatmapSelectors:rules.filter(rule=>rule.selectorText?.includes('.rh-container')).length
              });
              for(const rule of rules) if(rule.type===CSSRule.IMPORT_RULE) walk(rule.styleSheet);
            }catch(error){errors.push(String(error));}
          };
          [...document.styleSheets].filter(sheet=>
            sheet.href?.includes('/_addons/mistline_ui/')&&/\\/(theme|cabinet)\\.css$/.test(sheet.href)
          ).forEach(walk);
          return {imported,errors};
        })()"""
        def after(result):
            self.check(label + " loaded shared Heatmap CSS through real CSSOM",
                       not result["errors"] and len(result["imported"]) == 1
                       and result["imported"][0]["heatmapSelectors"] > 0, result)
            then()
        self.js(script, after)

    def expand_child_deck(self):
        selector = '[data-cabinet-command="collapse:' + str(self.decks["english"]) + '"]'
        # The seed normally starts collapsed. If Anki defaults change, first
        # collapse using the same native command, then prove native expansion.
        def expand():
            self.click(selector, lambda: self.later(800, self.check_child_options))
        if self.mw.col.decks.get(self.decks["english"])["collapsed"]:
            expand()
        else:
            self.click(selector, lambda: self.later(700, expand))

    def check_child_options(self):
        self.check("Native collapse command expands persisted real deck state",
                   not self.mw.col.decks.get(self.decks["english"])["collapsed"])
        selector = '.cabinet-child-options[data-cabinet-command="opts:' + str(self.decks["phrases"]) + '"]'
        script = "(()=>{const e=document.querySelector(" + json.dumps(selector) + """
          );const row=e?.closest('.cabinet-child-row');
          const name=row?.querySelector('.cabinet-child-name');
          const counts=row?.querySelector('.cabinet-counts');
          let overlap=true;
          if(name&&counts){
            const range=document.createRange();range.selectNodeContents(name);
            const a=range.getBoundingClientRect(),b=counts.getBoundingClientRect();
            overlap=Math.min(a.right,b.right)-Math.max(a.left,b.left)>1&&
                    Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>1;
          }
          return {present:!!e,visible:!!e&&e.checkVisibility({checkOpacity:true,checkVisibilityCSS:true}),
            command:e?.dataset.cabinetCommand,label:e?.getAttribute('aria-label'),nameCountsOverlap:overlap};
        })()"""
        def after(dom):
            self.check("Expanded child has visible native-linked options entry",
                       dom["present"] and dom["visible"] and bool(dom["label"]), dom)
            self.check("Child deck name/path do not overlap its count labels", not dom["nameCountsOverlap"], dom)
            self.mw.grab()
            self.later(550, self.capture_child_options)
        self.js(script, after)

    def capture_child_options(self):
        self.capture("16-expanded-child-options")
        # Inspect the options entry only; do not open or change any option.
        selector = '[data-cabinet-command="collapse:' + str(self.decks["english"]) + '"]'
        self.click(selector, lambda: self.later(750, self.child_collapsed))

    def child_collapsed(self):
        self.check("Native collapse command restores collapsed real deck state",
                   self.mw.col.decks.get(self.decks["english"])["collapsed"])
        selector = '[data-cabinet-command="open:' + str(self.decks["empty"]) + '"]'
        script = "(()=>{const e=document.querySelector(" + json.dumps(selector) + ");if(!e)return false;e.dispatchEvent(new MouseEvent('click',{bubbles:true,shiftKey:true}));return true})()"
        def after(clicked):
            self.check("Shift-click dispatches from real folder button", clicked)
            self.wait(lambda: int(self.mw.col.decks.selected()) == self.decks["empty"],
                      self.shift_selection_checked, "native Shift-click selection")
        self.js(script, after)

    def shift_selection_checked(self):
        self.check("Shift-click selects generated deck without opening overview",
                   self.mw.state == "deckBrowser" and int(self.mw.col.decks.selected()) == self.decks["empty"])
        self.open_deck("english", self.overview)

    def open_deck(self, key, then):
        selector = '[data-cabinet-command="open:' + str(self.decks[key]) + '"]'
        self.click(selector, lambda: self.wait(lambda: self.mw.state == "overview", then, "native overview"))

    def overview(self):
        self.check("Real overview selected requested deck", int(self.mw.col.decks.selected()) == self.decks["english"])
        self.capture("02-native-overview")
        self.study(self.question)

    def study(self, then):
        self.click("#study", lambda: self.wait(lambda: self.mw.state == "review" and self.mw.reviewer.state == "question", then, "native review question"))

    def question(self):
        self.card_id = int(self.mw.reviewer.card.id)
        self.revlog_before = self.mw.col.db.scalar("select count(*) from revlog")
        card = self.mw.col.get_card(self.card_id)
        self.card_before = {"reps": card.reps, "queue": card.queue, "type": card.type}
        self.check("Question uses real scheduled card", card.did == self.decks["english"])
        self.capture("03-review-question")
        self.show_answer(self.answer)

    def show_answer(self, then):
        self.click("#ansbut", lambda: self.wait(lambda: self.mw.reviewer.state == "answer", then, "native review answer"), self.mw.bottomWeb)

    def answer(self):
        self.check("Anki reviewer answer state", self.mw.reviewer.state == "answer")
        self.capture("04-review-answer")
        if PRODUCTION:
            self.js("document.querySelector('#qa').innerHTML", self.start_production_switches)
        else:
            self.rate_buttons()

    def rate_buttons(self):
        self.js("[...document.querySelectorAll('button[data-ease]')].map(b=>{const r=b.getBoundingClientRect();return {ease:b.dataset.ease,bottom:r.bottom,height:r.height,viewport:innerHeight}})", self.grade, self.mw.bottomWeb)

    def start_production_switches(self, original_html):
        self.original_answer_html = original_html
        self.production_addon = sys.modules[PACKAGE]
        self.switch_queue = [
            ("editorial layout", lambda: self.production_addon._select_layout("editorial"),
             "editorial", "latte", True, "theme.css"),
            ("cabinet layout", lambda: self.production_addon._select_layout("cabinet"),
             "cabinet", "latte", True, "cabinet.css"),
            ("Mocha palette", lambda: self.production_addon._select_palette("mocha"),
             "cabinet", "mocha", True, "cabinet.css"),
            ("Latte palette", lambda: self.production_addon._select_palette("latte"),
             "cabinet", "latte", True, "cabinet.css"),
            ("reviewer styling disabled", lambda: self.set_reviewer_style(False),
             "cabinet", "latte", False, None),
            ("reviewer styling enabled", lambda: self.set_reviewer_style(True),
             "cabinet", "latte", True, "cabinet.css"),
        ]
        self.next_production_switch()

    def set_reviewer_style(self, enabled):
        self.production_addon._write_config_patch(style_reviewer=enabled)
        self.production_addon._apply_current_theme()

    def next_production_switch(self):
        if not self.switch_queue:
            from rating_verification import RatingVerification
            self.rating_verification = RatingVerification(self)
            return
        self.switch_case = self.switch_queue.pop(0)
        self.switch_case[1]()
        self.later(750, self.check_production_switch)

    def check_production_switch(self):
        name, _change, layout, palette, enabled, stylesheet = self.switch_case
        self.check(name + " preserves native answer/card",
                   self.mw.reviewer.state == "answer" and int(self.mw.reviewer.card.id) == self.card_id)
        self.check(name + " does not schedule a review",
                   self.mw.col.db.scalar("select count(*) from revlog") == self.revlog_before)
        script = """(()=>{
          const qa=document.querySelector('#qa');
          const canvas=document.createElement('canvas');canvas.width=canvas.height=1;
          const context=canvas.getContext('2d',{willReadFrequently:true});
          const parse=(value)=>{
            context.clearRect(0,0,1,1);context.fillStyle=value;context.fillRect(0,0,1,1);
            const parts=context.getImageData(0,0,1,1).data;
            return [parts[0],parts[1],parts[2],parts[3]/255];
          };
          const blend=(foreground,background)=>foreground.slice(0,3)
            .map((channel,index)=>channel*foreground[3]+background[index]*(1-foreground[3]));
          const ancestors=[];
          for(let node=qa;node;node=node.parentElement) ancestors.unshift(node);
          let background=[255,255,255];
          for(const node of ancestors) background=blend(parse(getComputedStyle(node).backgroundColor),background);
          const foreground=blend(parse(getComputedStyle(qa).color),background);
          const luminance=(rgb)=>rgb.map(channel=>{
            const normalized=channel/255;
            return normalized<=0.04045?normalized/12.92:((normalized+0.055)/1.055)**2.4;
          }).reduce((sum,value,index)=>sum+value*[0.2126,0.7152,0.0722][index],0);
          const light=luminance(foreground),dark=luminance(background);
          return {
            html:qa.innerHTML,
            layout:document.documentElement.dataset.mistlineLayout,
            palette:document.documentElement.dataset.mistlinePalette,
            enabled:document.documentElement.dataset.mistlineEnabled,
            background:getComputedStyle(document.body).backgroundColor,
            cardBackground:getComputedStyle(document.querySelector('#qa')).backgroundColor,
            cardText:getComputedStyle(qa).color,
            cardTextContrast:(Math.max(light,dark)+0.05)/(Math.min(light,dark)+0.05),
            styles:[...document.querySelectorAll('link[rel="stylesheet"]')]
              .filter(e=>e.href.includes('/_addons/mistline_ui/') &&
                  /\\/(theme|cabinet|editor)\\.css(?:\\?|$)/.test(e.href) && !e.disabled)
              .map(e=>e.href.split('/').pop())
          };
        })()"""
        def after(dom):
            self.check(name + " preserves original card HTML", dom["html"] == self.original_answer_html)
            self.check(name + " has one styling owner" if enabled else name + " removes styling owner",
                       dom["styles"] == ([stylesheet] if enabled else []), dom)
            if enabled:
                self.check(name + " matches requested layout/palette",
                           dom["layout"] == layout and dom["palette"] == palette, dom)
                self.check(name + " preserves readable stock card text",
                           dom["cardTextContrast"] >= 4.5,
                           {"text": dom["cardText"], "paper": dom["cardBackground"],
                            "contrast": round(dom["cardTextContrast"], 2)})
            if name == "Mocha palette":
                self.mocha_canvas = dom["background"]
            if name == "Latte palette":
                self.check("Palette switch changes real rendered canvas color",
                           self.mocha_canvas != dom["background"],
                           {"mocha": self.mocha_canvas, "latte": dom["background"]})
            self.report.setdefault("production_switches", []).append({"name": name, **dom})
            self.capture("13-switch-" + name.replace(" ", "-"))
            self.check_bottom_style_owner(enabled, stylesheet)
        self.js(script, after)

    def check_bottom_style_owner(self, enabled, stylesheet):
        def after(styles):
            self.check(self.switch_case[0] + " applies consistently to rating bar",
                       styles == ([stylesheet] if enabled else []), styles)
            self.next_production_switch()
        self.js("""[...document.querySelectorAll('link[rel="stylesheet"]')]
            .filter(e=>e.href.includes('/_addons/mistline_ui/') &&
                /\\/(theme|cabinet|editor)\\.css(?:\\?|$)/.test(e.href) && !e.disabled)
            .map(e=>e.href.split('/').pop())""", after, self.mw.bottomWeb)

    def grade(self, buttons):
        self.check("Native four ratings are present", len(buttons) == 4, buttons)
        self.check("Ratings stay inside bottom WebView", all(x["bottom"] <= x["viewport"] and x["height"] > 0 for x in buttons))
        self.click('button[data-ease="3"]', lambda: self.wait(lambda: self.mw.col.db.scalar("select count(*) from revlog") == self.revlog_before + 1, self.graded, "scheduler wrote review log"), self.mw.bottomWeb)

    def graded(self):
        card = self.mw.col.get_card(self.card_id)
        self.check("Native grade writes revlog", True, {"before": self.revlog_before, "after": self.mw.col.db.scalar("select count(*) from revlog")})
        self.check("Native grade updates card scheduling", card.reps == self.card_before["reps"] + 1, {"id": self.card_id, "reps": card.reps, "queue": card.queue, "type": card.type})
        self.check("Reviewer advances after grade", self.mw.reviewer.card.id != self.card_id)
        self.capture("05-after-grade")
        self.mw.undo()
        self.wait(lambda: self.mw.col.db.scalar("select count(*) from revlog") == self.revlog_before, self.undone, "native undo restores review log")

    def undone(self):
        card = self.mw.col.get_card(self.card_id)
        actual = {"reps": card.reps, "queue": card.queue, "type": card.type}
        self.check("Native undo restores card scheduling", actual == self.card_before, actual)
        # Anki defers its view refresh while the window is not focused. A test
        # started from an editor can have that state; run Anki's own focus handler
        # rather than overriding the scheduler or rebuilding a synthetic queue.
        self.mw.on_focus_did_change(self.mw.web, None)
        self.wait(lambda: self.mw.reviewer.card is not None and int(self.mw.reviewer.card.id) == self.card_id,
                  self.undo_refreshed, "native focus refresh after undo")

    def undo_refreshed(self):
        self.check("Native undo returns reviewed card", int(self.mw.reviewer.card.id) == self.card_id)
        self.capture("06-after-undo")
        self.template_queue = ["typing", "cloze", "media"]
        self.next_template()

    def next_template(self):
        if not self.template_queue:
            self.mw.moveToState("deckBrowser")
            self.mw.resize(820, 700)
            self.later(850, self.narrow_home)
            return
        self.template = self.template_queue.pop(0)
        self.mw.moveToState("deckBrowser")
        self.later(850, lambda: self.open_deck(self.template, lambda: self.study(self.template_question)))

    def template_question(self):
        key = self.template
        script = {"typing": "!!document.querySelector('#qa input#typeans')",
                  "cloze": "!!document.querySelector('#qa .cloze')",
                  "media": "[...document.querySelectorAll('#qa img')].some(i=>i.complete&&i.naturalWidth>0)"}[key]
        def after(value):
            self.check("Stock " + key + " question remains functional", value)
            self.capture("07-" + key + "-question")
            if key == "typing":
                self.js("(()=>{const e=document.querySelector('#typeans');e.value='be out on a tree';e.dispatchEvent(new Event('input',{bubbles:true}));return true})()", lambda _: self.show_answer(self.template_answer))
            else:
                self.show_answer(self.template_answer)
        self.js(script, after)

    def narrow_home(self):
        def after(dom):
            self.check("Narrow Anki home does not overflow", not dom["overflow"], dom)
            self.capture("09-home-820")
            self.open_deck("empty", self.empty_deck)
        self.js("({overflow:document.documentElement.scrollWidth>innerWidth+2,width:innerWidth,scroll:document.documentElement.scrollWidth})", after)

    def empty_deck(self):
        self.check("Empty deck uses native overview", self.mw.state == "overview" and int(self.mw.col.decks.selected()) == self.decks["empty"])
        self.capture("10-empty-overview")
        self.mw.moveToState("deckBrowser")
        self.mw.resize(1280, 860)
        self.later(650, self.toggle_off)

    def toggle_off(self):
        action_text = "Editorial Index 主题" if PRODUCTION else "卡匣实验主题（仅测试）"
        self.theme_action = next(a for a in self.mw.findChildren(QAction) if a.text() == action_text)
        self.theme_action.trigger()
        self.later(850, self.native_home)

    def native_home(self):
        def after(dom):
            self.check("Theme toggle restores native deck table", not dom["cabinet"] and dom["native"], dom)
            self.capture("11-disabled-native-home")
            self.theme_action.trigger()
            self.later(850, self.reenabled)
        self.js("({cabinet:!!document.querySelector('#cabinet-home'),native:!!document.querySelector('a.deck')})", after)

    def reenabled(self):
        def after(value):
            self.check("Theme toggle re-enables Cabinet", value)
            self.capture("12-reenabled-home")
            if PRODUCTION:
                self.production_addon._select_layout("editorial")
                self.later(850, self.editorial_home)
            else:
                self.finish()
        self.js("!!document.querySelector('#cabinet-home')", after)

    def editorial_home(self):
        def after(dom):
            self.check("Layout switch restores Editorial native deck table",
                       not dom["cabinet"] and dom["native"], dom)
            self.capture("14-editorial-home")
            def restore():
                self.production_addon._select_layout("cabinet")
                self.later(850, self.cabinet_home_restored)
            self.verify_heatmap_css("Editorial", restore)
        self.js("({cabinet:!!document.querySelector('#cabinet-home'),native:!!document.querySelector('a.deck')})", after)

    def cabinet_home_restored(self):
        def after(dom):
            self.check("Layout switch rebuilds Cabinet from real deck tree", dom["cabinet"], dom)
            self.check("Layout switch does not duplicate Cabinet root", dom["roots"] == 1, dom)
            self.capture("15-cabinet-home-restored")
            from display_verification import DisplayVerification
            self.display_verification = DisplayVerification(self)
        self.js("({cabinet:!!document.querySelector('#cabinet-home'),roots:document.querySelectorAll('#cabinet-home').length})", after)

    def template_answer(self):
        key = self.template
        script = {"typing": "!!document.querySelector('#qa .typeGood') && !!document.querySelector('#qa .typeBad') && document.querySelector('#qa').innerText.includes('be out on a limb') && document.documentElement.scrollWidth <= innerWidth + 2",
                  "cloze": "document.querySelector('#qa').innerText.includes('long-term memory')",
                  "media": "!!document.querySelector('#qa mjx-container')"}[key]
        def after(value):
            self.check("Stock " + key + " answer remains functional", value)
            self.capture("08-" + key + "-answer")
            self.next_template()
        self.js(script, after)

    def finish(self):
        self.report["open_message_boxes"] = [
            {"title": widget.windowTitle(), "text": widget.text(),
             "detail": widget.informativeText(), "visible": widget.isVisible()}
            for widget in self.mw.app.topLevelWidgets() if isinstance(widget, QMessageBox)
        ]
        print("Message boxes: " + json.dumps(self.report["open_message_boxes"], ensure_ascii=False), flush=True)
        self.check("No unexpected native error dialogs", not any(box["visible"] for box in self.report["open_message_boxes"]))
        self.report["passed"] = all(c["passed"] for c in self.report["checks"])
        self.stop()

    def fail(self, error):
        if self.finished:
            return
        self.report["passed"] = False
        self.report["error"] = error
        print(error, flush=True)
        self.stop()

    def stop(self):
        self.finished = True
        self.report["elapsed_seconds"] = round(time.monotonic() - self.started, 2)
        (OUTPUT / "runtime-report.json").write_text(json.dumps(self.report, ensure_ascii=False, indent=2), encoding="utf-8")
        (BASE / "runtime-report.json").write_text(json.dumps(self.report, ensure_ascii=False, indent=2), encoding="utf-8")
        self.mw.unloadProfileAndExit()


driver = None
def on_profile_open():
    global driver
    try:
        driver = Driver()
    except Exception:
        error = traceback.format_exc()
        print(error, flush=True)
        (OUTPUT / "runtime-report.json").write_text(json.dumps({"passed": False, "error": error, "scratch": str(BASE)}, indent=2))
        QTimer.singleShot(100, aqt.mw.unloadProfileAndExit)


gui_hooks.profile_did_open.append(on_profile_open)
app = aqt._run(["anki-cabinet-lab", "-b", str(BASE), "-p", PROFILE, "-l", "en"], exec=False)
if app is None:
    raise RuntimeError("Lab instance unexpectedly reused another process")
app.exec()
sys.exit(0 if MODE == "open" or (driver and driver.report.get("passed")) else 1)
