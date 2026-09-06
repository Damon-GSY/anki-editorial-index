"""A collection-free sample surface styled by the production theme script."""

BODY = """
<main id="outer" aria-label="外观示意，按钮不会进行学习或评分">
  <header class="palette-preview-heading">
    <div><p>样式示例 · 不会操作卡片</p><h1>每天记住一点</h1></div>
    <button id="ansbut" disabled tabindex="-1">显示答案</button>
  </header>
  <div id="middle"><center><table cellpadding="0" cellspacing="0"><tr>
    <td><button data-ease="1" disabled tabindex="-1">重来<span class="nobold">20 分</span></button></td>
    <td><button data-ease="2" disabled tabindex="-1">困难<span class="nobold">1 个月</span></button></td>
    <td><button data-ease="3" disabled tabindex="-1">良好<span class="nobold">1.2 个月</span></button></td>
    <td><button data-ease="4" disabled tabindex="-1">简单<span class="nobold">1.7 个月</span></button></td>
  </tr></table></center></div>
</main>
"""

HEAD = """<style>
:root[data-mistline-context="reviewer-bottom-bar"] body.palette-preview {
  margin:0!important;padding:16px!important;border:0!important;
  font-family:var(--cb-ui,var(--mist-sans));color:var(--mist-ink);box-sizing:border-box;
}
.palette-preview-heading {display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:16px}
.palette-preview-heading h1 {font:600 22px/1.3 var(--cb-ui,var(--mist-sans));color:var(--mist-ink);margin:3px 0 0}
.palette-preview-heading p {font-size:11px;color:var(--mist-label);margin:0}
:root[data-mistline-context="reviewer-bottom-bar"] body.palette-preview #middle {padding:0!important}
:root[data-mistline-context="reviewer-bottom-bar"] body.palette-preview #middle > center > table {display:block;border-spacing:0!important;max-width:none}
body.palette-preview #middle tbody {display:block}
body.palette-preview #middle tr {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}
body.palette-preview #middle td {display:block;min-width:0}
:root[data-mistline-context="reviewer-bottom-bar"] body.palette-preview #outer {margin:0!important;padding:0!important;border:0!important;background:none!important;box-shadow:none!important;width:100%!important}
:root[data-mistline-context="reviewer-bottom-bar"] body.palette-preview #ansbut {min-width:180px!important;box-sizing:border-box;margin:0!important}
body.palette-preview button:disabled {opacity:1;cursor:default}
</style>"""


def create_preview(parent):
    from aqt.qt import Qt
    from aqt.webview import AnkiWebView

    web = AnkiWebView(parent, title="editorial-palette-preview")
    web.setObjectName("EditorialIndexPalettePreview")
    web.requiresCol = False
    web.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    # This context is deliberately NOT a DeckBrowser or Reviewer. The only
    # accepted command closes the parent dialog; no preview can rate a card.
    web.set_bridge_command(lambda command: parent.window().reject() if command == "close" else None, parent)
    web.stdHtml(BODY, head=HEAD + '<script>document.addEventListener("DOMContentLoaded",()=>document.body.classList.add("palette-preview"));</script>', context=parent)
    return web
