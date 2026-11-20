"""Saved web pages keep their content and run none of their code. What their scripts used to unfold, nothing unfolds any more,
so it is unfolded here as the page is served: no library file changes and no page needs code of its own.

Measured on 642 real pages against scripts on with every toggle opened: 0.5% of the words and no links lost, most of the words
being labels of buttons hidden on purpose. A convenience, not a defense: the Content-Security-Policy is what stops scripts.
Not done: MathJax pages keep their raw TeX, because typesetting it here needs a new third-party package. An accepted limit: 511 pages in the packs, 490 of them in the statistics handbook.
"""
import html
import itertools
import re

MAX_PAGE = 16 * 1024 * 1024   # a larger page is served as it is, unless taking out its blank spreadsheet rows brings it under this
MAX_READ = 64 * 1024 * 1024   # larger than this and it is not even read to find out
MAX_TRANSCRIPT = 4 * 1024 * 1024

# :where() keeps the specificity at zero, so a page's own responsive !important rules still win. The description's ids need their weight: they must beat .d-none!important.
CSS = rb"""<style>
:where(.collapse:not(.navbar-collapse),.collapsing,.tab-pane,.accordion-collapse){display:block!important;height:auto!important;visibility:visible!important}
:where(.partial-collapse){height:auto!important;overflow:visible!important}
:where(.partial-collapse-overlay){display:none!important}
:where(button)[data-toggle="collapse"]:not(:has(span)),:where(button)[data-bs-toggle="collapse"]:not(:has(span)){display:none!important}
:where(button[data-toggle],button[data-bs-toggle]){pointer-events:none}
:where(a[data-toggle="collapse"],a[data-bs-toggle="collapse"]){pointer-events:none;color:inherit;text-decoration:none}
.navbar-offcanvas:target{left:0!important;transform:none!important;opacity:1!important;box-shadow:0 0 20px #0000004d}
:where(.navbar-toggler){display:none!important}
#expanded-description{display:block!important}
#collapsed-description:has(~#expanded-description),#collapse-description{display:none!important}
:where(a.offcanvas-toggle,a[id^="close-mobile-"]){pointer-events:auto;cursor:pointer}
:where(.video-tab-download-popup){position:static!important;visibility:visible!important;width:auto!important;box-shadow:none!important;border:0!important}
:where(.download-menu-submenu){display:block!important}
:where(.video-download-icons,.download-transcript-submenu-btn,.download-submenu-back-btn,.video-tab-toggle-section .tab-toggle-button){display:none!important}
:where(.download-menu-main a[href^="http"]){display:none!important}
:where(.download-menu-submenu a)::before{content:"Transcript PDF: "}
.lb-transcript{margin:.8em 0;font:inherit;line-height:1.5}
.lb-transcript summary{cursor:pointer;font-weight:600}
</style>"""

# A page is whatever it is, up to MAX_PAGE, and these run on it as it is served. So none of this may take quadratic time on a page that never closes
# a tag: one regular expression holding the interpreter would stop the whole window. <x[^>]*> over the text up to its last '>' always succeeds and moves on,
# and everything else looks only inside one tag it has found, or finds the closing tag with bytes.find and stops for good when there is none.
_HEAD = re.compile(rb'<head\b[^>]*>', re.I)
_DOCTYPE = re.compile(rb'<!doctype\b[^>]*>', re.I)
_ANCHOR = re.compile(rb'<a\b[^>]*>', re.I)
_LOCAL = re.compile(rb"""\bhref\s*=\s*(?:["']|(?!["']))(?![a-z][a-z0-9+.-]*:|//)""", re.I)
_TARGET = re.compile(rb"""\starget\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+)""", re.I)
_DOWNLOAD = re.compile(rb"""\sdownload(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+))?(?=[\s>/])""", re.I)
_BUTTON = re.compile(rb'<button\b([^>]*)>', re.I)
_OPENS = re.compile(rb"""\bdata-target=["'](#[\w-]+)["']""", re.I)
_IS_OPENER = re.compile(rb"""\bdata-toggle=["']offcanvas["']""", re.I)
_IS_CLOSER = re.compile(rb"""\bid=["']close-mobile-[\w-]+["']""", re.I)
_DIV = re.compile(rb'<div\b[^>]*>', re.I)
_IS_GALLERY = re.compile(rb"""\bclass=["'][^"']*\bimage-gallery\b""", re.I)
_BASE_URL = re.compile(rb"""\bdata-base-url=["']([^"']*)["']""", re.I)
_HREF = re.compile(rb"""\bhref=["']([^"']+)["']""", re.I)
_TRACK = re.compile(rb'<track\b[^>]*>', re.I)
_TRACK_SRC = re.compile(rb"""\bsrc=["']([^"'>]+\.vtt)["']""", re.I)
_TAG = re.compile(r'<[^>]+>')
# A saved spreadsheet whose rows name their cells and hold nothing. The largest page in the library is 99.7% these: a million table rows, which no web view can lay out
# within its memory limit, around 150 KB of real content.
_BLANK_ROW = re.compile(rb'<tr>(?:<td><small>[A-Z]+\d+</small>\s*</td>)+</tr>')
MAX_TAG = 64 * 1024     # no real tag is this long. One that is gets left as it is.
# WebKit opens a socket for preconnect even with a Content-Security-Policy of default-src 'none'. The window has its own switches for these; a browser over HTTP does not.
_LINK = re.compile(rb'<link\b[^>]*>', re.I)
_HINT_REL = re.compile(rb"""\brel\s*=\s*(?:"[^"]*|'[^']*|[^\s>]+)""", re.I)
_HINT = re.compile(rb'preconnect|dns-prefetch|prefetch|prerender', re.I)


def _no_hint(m):
    tag = m.group(0)
    rel = _HINT_REL.search(tag) if len(tag) <= MAX_TAG else None
    return b'' if rel and _HINT.search(rel.group(0)) else tag


def no_hints(data):
    """Takes out <link> tags that ask the browser to reach for another address before anything loads. Plain bytes matching, so not for UTF-16."""
    end = _upto(data)
    return _LINK.sub(_no_hint, data[:end]) + data[end:]


def _upto(data):
    return data.rfind(b'>') + 1


# Encyclopedia files stay byte for byte as they came, so their scripts come out here, as each article is served. The block in the Content-Security-Policy stays on regardless.
_ARTICLE_TAG = re.compile(rb"""<!--|<(/?)([a-z][^\s/>"'=<]*)((?:[^>"']|"[^"]*"|'[^']*')*)>""", re.I)   # each choice starts with a different character, so a tag that fails fails once
_ATTRIBUTE = re.compile(rb"""([^\s=/>"']+)(\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>"']+))?""")
_RAW_TEXT = (b'style', b'title', b'textarea', b'xmp', b'noembed', b'noframes', b'iframe')   # what is inside these is not markup
_SCRIPT_URL = re.compile(rb'[\x00-\x20]*(?:javascript|vbscript)[\x00-\x20]*:', re.I)
_WEB_URL = re.compile(rb'[\x00-\x20]*(?:[a-z][a-z0-9+.\-]*:|[/\\][/\\])', re.I)   # http:, mailto:, //host and the like: any address that leaves the encyclopedia


def _no_code_attribute(m):
    name, value = m.group(1).lower(), m.group(2)
    if name.startswith(b'on') and len(name) > 2:
        return b''
    if value and (b':' in value or b'&' in value):   # the address may be written with entities: java&#115;cript:
        raw = value.split(b'=', 1)[1].strip(b' \t\r\n"\'')
        if _SCRIPT_URL.match(html.unescape(raw.decode('latin-1')).encode('latin-1', 'replace')):
            return b''
    return m.group(0)


def _web_link(attrs):
    """Whether this <a> or <area> points out of the encyclopedia. Its words stay, as plain text, as in a saved page."""
    if len(attrs) > MAX_TAG or b'ref' not in attrs.lower():
        return False
    for m in _ATTRIBUTE.finditer(attrs):
        if m.group(1).lower() in (b'href', b'xlink:href') and m.group(2):
            raw = m.group(2).split(b'=', 1)[1].strip(b' \t\r\n"\'')
            if _WEB_URL.match(html.unescape(raw.decode('latin-1')).encode('latin-1', 'replace')):
                return True
    return False


def article(data):
    """One encyclopedia article or drawing, with its script elements, event handlers and script addresses taken out, a link to the web
    made plain text (its tag and end tag go, its words stay), and every other byte left as it came.
    A <script> that never closes runs to the end of the page in a browser too, so what it would have hidden is all that goes with it."""
    if b'\0' in data[:512]:   # UTF-16: none of this would match
        return data
    data = no_hints(data)
    low = data.lower()
    out, pos, scan, end = [], 0, 0, _upto(data)
    bare_a = False   # the open <a> was a web link and lost its tag, so its end tag goes too
    while True:
        m = _ARTICLE_TAG.search(data, scan, end)
        if not m:
            break
        scan = m.end()
        if m.group(0) == b'<!--':
            close = data.find(b'-->', scan)
            if close < 0:
                break
            scan = close + 3
            continue
        if m.group(1):
            if bare_a and m.group(2).lower() == b'a':
                out.append(data[pos:m.start()])
                pos, bare_a = m.end(), False
            continue
        name = m.group(2).lower()
        if name == b'a':
            bare_a = False   # a new <a> closes any open one
        if name in (b'a', b'area') and _web_link(m.group(3)):
            out.append(data[pos:m.start()])
            pos = m.end()
            bare_a = name == b'a' and not m.group(0).endswith(b'/>')
            continue
        if name == b'script':
            out.append(data[pos:m.start()])
            close = low.find(b'</script', scan) if not m.group(0).endswith(b'/>') else -2   # <script/> closes itself only in a drawing
            gt = data.find(b'>', close) if close >= 0 else -1
            pos = scan = scan if close == -2 else gt + 1 if gt >= 0 else len(data)   # '</script' with no '>' after it: the rest goes, as with no end tag
            continue
        if name in _RAW_TEXT:
            close = low.find(b'</' + name, scan)
            if close < 0:
                break
            scan = close
        attrs = m.group(3)
        if len(attrs) <= MAX_TAG and (b'on' in attrs.lower() or b'script' in attrs.lower() or b'&' in attrs):
            clean = _ATTRIBUTE.sub(_no_code_attribute, attrs)
            if clean != attrs:
                out += [data[pos:m.start(3)], clean]
                pos = m.end(3)
    out.append(data[pos:])
    return b''.join(out)


# How an encyclopedia article looks inside the app: its title, text and links in the window's own font, text colours and accent,
# its left edge on the page's, and the window's colour behind it. The file stays as it came; this is added as the article is served.
# The page that shows the article sets the --lb-* values (web/app.js, lookOf); what is here is what shows before it does, and in a page
# opened on its own. Tables, infoboxes and pictures keep the skin's own look, which already follows light and dark.
ARTICLE_LOOK = b"""<style id="lb-article">
:root{--lb-ink:#1d1d1f;--lb-ink2:#55555a;--lb-line:#e6e6e9;--lb-link:#10805c;--lb-font:-apple-system,BlinkMacSystemFont,"Segoe UI Variable Text","Segoe UI",system-ui,sans-serif;--lb-display:-apple-system,BlinkMacSystemFont,"Segoe UI Variable Display","Segoe UI",system-ui,sans-serif}
@media (prefers-color-scheme:dark){:root{--lb-ink:#f2f2f3;--lb-ink2:#c2c2c7;--lb-line:#313134;--lb-link:#3cc690}}
html:root:not(#lb){--color-base:var(--lb-ink)!important;--color-emphasized:var(--lb-ink)!important;--color-subtle:var(--lb-ink2)!important;--color-progressive:var(--lb-link)!important;--color-progressive--hover:var(--lb-link)!important;--color-progressive--active:var(--lb-link)!important;--color-progressive--focus:var(--lb-link)!important;--color-visited:var(--lb-link)!important;--color-link:var(--lb-link)!important;--color-link--visited:var(--lb-link)!important;--border-color-base:var(--lb-line)!important;--border-color-subtle:var(--lb-line)!important;--background-color-base:transparent!important;--background-color-interactive-subtle:transparent!important}
html:not(#lb),html:not(#lb) body,.mw-page-container,.mw-page-container-inner,.mw-content-container,.mw-body,.vector-body{background:transparent!important}
html:not(#lb) body{margin:0!important;padding:0!important;color:var(--lb-ink)!important;font-family:var(--lb-font)!important}
.mw-page-container,.mw-page-container-inner,.mw-content-container,.mw-body,#content,.vector-body,#bodyContent,.mw-body-header,.vector-page-titlebar{margin-left:0!important;margin-right:0!important;padding-left:0!important;padding-right:0!important;max-width:none!important;border:0!important;box-shadow:none!important}
.mw-page-container{padding-top:0!important}
.vector-page-titlebar::after,.mw-body-header::after{display:none!important}
.mw-body,.mw-body-content,.vector-body,.mw-parser-output,#content,#bodyContent{font-family:var(--lb-font)!important;color:var(--lb-ink)}
.mw-body-content,.vector-body{font-size:18px!important;line-height:1.6!important}
h1,h2,h3,h4,h5,h6,.mw-body h1,.mw-body-content h1,.mw-body-content h2,.mw-body-content h3,.mw-heading h2,.mw-heading h3{font-family:var(--lb-display)!important;color:var(--lb-ink)!important}
#firstHeading,.firstHeading{font-weight:700!important;font-size:34px!important;line-height:1.15!important;letter-spacing:-.018em;margin:.1em 0 .3em!important;padding:0!important;border:0!important}
.mw-body-content h2,.mw-heading2 h2,.mw-heading2{font-weight:650!important;font-size:22px!important;line-height:1.25!important;border-bottom-color:var(--lb-line)!important}
.mw-body-content h3,.mw-heading3 h3{font-weight:650!important;font-size:19px!important}
a,a:visited,a.new,a.extiw,.mw-body-content a:not(.mw-selflink),.mw-body-content a:visited{color:var(--lb-link)!important}
.hatnote,.dablink,.rellink{background:none!important;color:var(--lb-ink2)!important}
html:not(#lb) .hatnote,html:not(#lb) .dablink,html:not(#lb) .rellink{color:var(--lb-ink2)!important}
.mw-parser-output table{font-size:15.5px}
.navbox{font-size:14px!important}
.mw-parser-output .navbox table{font-size:inherit}
div.navbox{overflow-x:auto}
ul.gallery{margin-left:0!important;margin-right:0!important;max-width:100%}
li.gallerybox,li.gallerybox .thumb,li.gallerybox .gallerytextwrapper{max-width:100%!important;box-sizing:border-box}
.mw-parser-output img:not(table img){max-width:100%;height:auto}   /* not in a table: there a share of the cell's width collapses a picture in a cell sized by its content, and the table's box scrolls instead */
.smooth-pie{overflow:hidden}
.mw-parser-output{overflow-wrap:break-word}
.references,.reflist,.reference-text{overflow-wrap:anywhere}
/* a table or picture group wider than the column scrolls inside its own box, so the article never scrolls sideways. A table keeps its
   table layout: web/app.js (tidyArticle) puts it in a .lb-wide box, which fades at an edge that has more to scroll to */
.lb-wide{max-width:100%;overflow-x:auto;overflow-y:hidden;position:relative}
div.navbox{position:relative}   /* a screen-reader label placed absolutely inside stays inside the box, and does not widen the page */
@media (max-width:639px){html[data-lb-tidy] table{display:table}}   /* the skin makes every table a block on a narrow page, which fixes its width; the box scrolls it instead */
/* a narrow page: a formula set on one line may break at its spaces, and a box set to a share of the width counts its padding in it, so neither runs past the column */
@media (max-width:639px){.mw-parser-output .chemf,.mw-parser-output .texhtml{white-space:normal!important}.mw-parser-output div[style*="width"][style*="%"]{box-sizing:border-box}}
.lb-wide.lb-r{-webkit-mask-image:linear-gradient(to left,transparent,#000 36px);mask-image:linear-gradient(to left,transparent,#000 36px)}
.lb-wide.lb-l{-webkit-mask-image:linear-gradient(to right,transparent,#000 36px);mask-image:linear-gradient(to right,transparent,#000 36px)}
.lb-wide.lb-l.lb-r{-webkit-mask-image:linear-gradient(to right,transparent,#000 36px,#000 calc(100% - 36px),transparent);mask-image:linear-gradient(to right,transparent,#000 36px,#000 calc(100% - 36px),transparent)}
/* the web page's editing links do nothing offline: [edit], and a template's view / talk / edit row */
.mw-editsection,.mw-editsection-like,.mw-parser-output .navbar,.mw-parser-output .sidebar-navbar{display:none!important}
.mw-parser-output img:is([src*="OOjs_UI_icon_edit"],[src$="Red_Pencil_Icon.png"],[src$="Blue_pencil.svg.png"]){display:none!important}   /* the pencil that edited an infobox or taxobox */
/* a paragraph set in small type (the front page's licence note) gets line spacing for that type, not the body's */
.mw-parser-output p:has(>span:is([style*="font-size:10px"],[style*="font-size: 10px"],[style*="font-size:11px"],[style*="font-size: 11px"],[style*="font-size:12px"],[style*="font-size: 12px"],[style*="font-size:13px"],[style*="font-size: 13px"],[style*="font-size:small"],[style*="font-size: small"],[style*="font-size:x-small"],[style*="font-size: x-small"],[style*="font-size:80%"],[style*="font-size: 80%"],[style*="font-size:85%"],[style*="font-size: 85%"],[style*="font-size:90%"],[style*="font-size: 90%"]):only-child){font-size:14.5px;line-height:1.5;color:var(--lb-ink2);margin-top:1.75em}
.mw-parser-output p>span:is([style*="font-size:10px"],[style*="font-size: 10px"],[style*="font-size:11px"],[style*="font-size: 11px"],[style*="font-size:12px"],[style*="font-size: 12px"],[style*="font-size:13px"],[style*="font-size: 13px"],[style*="font-size:small"],[style*="font-size: small"],[style*="font-size:x-small"],[style*="font-size: x-small"],[style*="font-size:80%"],[style*="font-size: 80%"],[style*="font-size:85%"],[style*="font-size: 85%"],[style*="font-size:90%"],[style*="font-size: 90%"]):only-child{font-size:inherit!important}
.mw-parser-output .thumbinner{max-width:100%!important;overflow-x:auto}
/* the encyclopedia's licence line at the end of every page, in the same small secondary type as the front page's own licence note */
html:not(#lb) .zim-footer{font-size:14.5px!important;line-height:1.5!important;color:var(--lb-ink2)!important;border-top:1px solid var(--lb-line)!important;margin:2.5em 0 1em!important;padding:.9em 0 0!important}
/* the front page's logo is a picture on white: in dark mode it shows as a tile, with rounded corners, not a white square */
@media (prefers-color-scheme:dark){.mw-parser-output img[src$="/MedLogoNoWiFi.png"]{border-radius:18%}}
.mw-parser-output div[style*="inline-table"]{overflow-wrap:anywhere;display:inline-block!important;max-width:100%}   /* tables set side by side: each fits the column, and one wider scrolls in its box */
.mw-parser-output math:not([display=block]){display:inline-block;vertical-align:middle}
.mw-parser-output img.mwe-math-fallback-image-display:not(table img){max-width:calc(100% - 1.6em)}   /* a formula set on its own line is indented 1.6em by the skin: with that, it still fits the column */
.mw-parser-output dd dd{margin-left:min(1.6em,8%)}   /* indentation many levels deep (':::: ...') takes a share of what is left, so the text never runs out of room and past the column */
.mw-parser-output math{max-width:100%;overflow-x:auto;overflow-y:hidden}
@media (min-width:760px){.mw-parser-output .thumb.tright{float:right!important;clear:right;width:auto!important;margin:.3em 0 1em 1.5em!important}}
</style>"""


# Lastbook's own pages in a pack (Sources and permissions): the window's font and colours, light and dark, clear so the window shows behind,
# and disclosure rows with the app's chevron. Their page title is the reading page's own, so it is not shown twice.
OWN_LOOK = b"""<style id="lb-own">
:root{color-scheme:light dark;--ink:#1d1d1f;--ink2:#55555a;--line:#e6e6e9;--link:#10805c}
@media (prefers-color-scheme:dark){:root{--ink:#f2f2f3;--ink2:#c2c2c7;--line:#313134;--link:#3cc690}}
html{background:transparent}
body{font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI Variable Text","Segoe UI",system-ui,sans-serif!important;color:var(--ink);background:transparent;max-width:46em;margin:4px 0 24px!important;padding:0 2px!important;-webkit-font-smoothing:antialiased}
body>h1:first-child{display:none}
h2{font:650 19px/1.3 -apple-system,BlinkMacSystemFont,"Segoe UI Variable Display","Segoe UI",system-ui,sans-serif;margin:1.5em 0 .3em}
p{margin:.4em 0}a{color:var(--link)}
details{border-bottom:1px solid var(--line);padding:4px 0 8px}
summary{list-style:none;color:var(--ink2);font-size:15px;padding:4px 0}summary::-webkit-details-marker{display:none}
summary::before{content:"";display:inline-block;width:7px;height:7px;margin:0 10px 0 2px;border-right:2px solid currentColor;border-bottom:2px solid currentColor;transform:rotate(-45deg);vertical-align:2px;transition:transform .15s}
details[open]>summary::before{transform:rotate(45deg)}
ul{color:var(--ink2);font-size:14.5px;overflow-wrap:anywhere;padding-left:22px}
</style>"""


def own_look(data):
    """One of Lastbook's own pages with OWN_LOOK added, as article_look does."""
    return article_look(data, OWN_LOOK)


def article_look(data, look=None):
    """An encyclopedia page (HTML) with ARTICLE_LOOK added at the end of its head, or at its end when it has no head."""
    at = data.lower().find(b'</head>', 0, _upto(data) or len(data))
    look = look or ARTICLE_LOOK
    return data[:at] + look + data[at:] if at >= 0 else data + look


def _anchor(m):
    """A local link opens where it is. In a saved page target= and download= would only make it do nothing."""
    a = m.group(0)
    return _DOWNLOAD.sub(b'', _TARGET.sub(b'', a)) if len(a) <= MAX_TAG and _LOCAL.search(a) else a


def _gallery_links(base, inner):
    low = inner.lower()
    out, pos, end = [], 0, _upto(inner)
    while True:
        m = _ANCHOR.search(inner, pos, end)
        close = low.find(b'</a>', m.end()) if m else -1
        if close < 0:
            break
        href = _HREF.search(m.group(0)) if len(m.group(0)) <= MAX_TAG else None
        if href:
            out += [inner[pos:m.start()], b'<figure style="margin:1em 0"><img style="max-width:100%" alt="" src="', base, href.group(1), b'"><figcaption>', inner[m.end():close], b'</figcaption></figure>']
            pos = close + 4
        else:
            out.append(inner[pos:m.end()])
            pos = m.end()
    out.append(inner[pos:])
    return b''.join(out)


def _galleries(data):
    low = data.lower()
    if b'image-gallery' not in low:
        return data
    out, pos, scan, end = [], 0, 0, _upto(data)
    while True:
        m = _DIV.search(data, scan, end)
        if not m:
            break
        scan = m.end()
        tag = m.group(0)
        if len(tag) > MAX_TAG or b'image-gallery' not in tag.lower() or not _IS_GALLERY.search(tag):
            continue
        base = _BASE_URL.search(tag)
        if not base:
            continue
        close = low.find(b'</div>', m.end())
        if close < 0:
            break
        out += [data[pos:m.end()], _gallery_links(base.group(1), data[m.end():close])]
        pos = scan = close
    out.append(data[pos:])
    return b''.join(out)


def _drawers(data):
    """A slide-in drawer opens by a plain in-page link and the CSS's :target. Attributes in either order: engine/library.py's parser sorts them."""
    low = data.lower()
    out, pos, scan, end = [], 0, 0, _upto(data)
    while True:
        m = _BUTTON.search(data, scan, end)
        close = low.find(b'</button>', m.end()) if m else -1
        if close < 0:
            break
        scan = close + 9
        attrs = m.group(1)
        if len(attrs) > MAX_TAG:
            continue
        opens = _OPENS.search(attrs) if _IS_OPENER.search(attrs) else None
        if not opens and not _IS_CLOSER.search(attrs):
            continue
        out += [data[pos:m.start()], b'<a href="', opens.group(1) if opens else b'#', b'"', attrs, b'>', data[m.end():close], b'</a>']
        pos = scan
    out.append(data[pos:])
    return b''.join(out)


_CUE_TIME = re.compile(r'(?:(\d+):)?(\d\d):(\d\d)[.,]\d+[ \t]+-->')
_VTT_HEADER = re.compile(r'^WEBVTT(?:[ \t]|$)')
_VTT_NOTE = re.compile(r'^NOTE(?:[ \t]|$)')


def caption_blocks(vtt):
    """Yield (start seconds, payload lines) from timed captions. Identifiers and metadata are not spoken text.

    An empty line ends a block; its timing line follows at most one identifier. Keep numbers inside the payload,
    including a line containing only digits. Comma timestamps remain accepted for existing subtitle files."""
    lines = vtt.decode('utf-8-sig', 'replace').splitlines()
    for number, (nonempty, block) in enumerate(itertools.groupby(lines, key=bool)):
        if not nonempty:
            continue
        block = list(block)
        if (number == 0 and _VTT_HEADER.match(block[0])) or _VTT_NOTE.match(block[0]):
            continue
        timing = 0
        match = _CUE_TIME.match(block[0])
        if not match and len(block) > 1 and '-->' not in block[0]:
            timing = 1
            match = _CUE_TIME.match(block[1])
        if match:
            hours, minutes, seconds = match.groups()
            start = int(hours or 0) * 3600 + int(minutes) * 60 + int(seconds)
            yield start, block[timing + 1:]


def transcript_text(vtt):
    out, last = [], None
    for _, lines in caption_blocks(vtt):
        for line in lines:
            s = line.strip()
            if not s:
                continue
            end = s.rfind('>') + 1      # past the last '>' nothing can match, and a line of nothing but '<' would take quadratic time to find that out
            s = _TAG.sub('', s[:end]) + s[end:]
            if s != last:
                out.append(s)
            last = s
    return ' '.join(out)


def rewrite(data, read_local=None):
    """data: a saved page's bytes. read_local(src) gives the bytes of a file the page names, or None. Nothing here adds a script or an address outside the library."""
    if b'\0' in data[:512]:   # UTF-16: none of this would match, and the style block would break it
        return data
    data = no_hints(data)
    if len(data) > MAX_PAGE:
        data = _BLANK_ROW.sub(b'', data)
        if len(data) > MAX_PAGE:
            return data
    end = _upto(data)
    data = _ANCHOR.sub(_anchor, data[:end]) + data[end:]
    data = _galleries(data)
    data = _drawers(data)
    track = None
    if b'<track' in data.lower():
        end = _upto(data)
        for t in _TRACK.finditer(data, 0, end):
            track = _TRACK_SRC.search(t.group(0)) if len(t.group(0)) <= MAX_TAG else None
            if track:
                break
    vtt = read_local(track.group(1).decode('utf-8', 'replace')) if track and read_local else None
    if vtt:
        block = b'<details class="lb-transcript" open><summary>Transcript</summary><p>' + html.escape(transcript_text(vtt)).encode() + b'</p></details>'
        i = data.find(b'video-tab-content-section')
        i = data.find(b'>', i) + 1 if i >= 0 else data.find(b'</video>') + 8
        data = data[:i] + block + data[i:]
    end = _upto(data)
    m = _HEAD.search(data, 0, end) or _DOCTYPE.search(data, 0, end)
    i = m.end() if m else 0
    return data[:i] + CSS + data[i:]
