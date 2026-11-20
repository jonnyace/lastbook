"""Offline encyclopedia (ZIM) search and article text, shared by the library UI and Chat.

Uses libzim the same way engine/library.py already does for /api/collection-search. Nothing here opens a
socket or reaches the network. libzim is optional at import time: if it is missing, search returns no hits
and Chat keeps working with manuals and videos.
"""
import html
import re
import threading
import urllib.parse
from pathlib import Path

from engine import paths, safe_paths

PER_FILE = 8
SEARCH_LIMIT = 24
SEARCH_EXCERPT = 900
INITIAL_LIMIT = 3
INITIAL_CHARS = 2000
READ_CHARS = 3500
TRUST = 'Community-written encyclopedia'

# Short names as they appear on the Encyclopedias page (web/app.js ZIMNAMES / ZIMS).
LABELS = (
    ('mdwiki', 'Medical encyclopedia (MDWiki)'),
    ('wikipedia', 'Wikipedia (text only)'),
    ('wikibooks', 'Wikibooks — how-to textbooks'),
    ('appropedia', 'Appropedia — appropriate technology'),
)

# zim/<file>.zim/<Article_path> as used in content/topics and #/wiki/ addresses.
KEY = re.compile(r'^(?:zim/)?([^/]+\.zim)/(.+)$', re.I)

_lock = threading.Lock()
_archives = {}


def collections_dir(root=None):
    """The folder of ZIM files for this library (library-data/collections)."""
    base = Path(root) if root is not None else paths.LIB
    return Path(base) / 'collections'


def library_dir(root=None):
    return Path(root) if root is not None else paths.LIB


def zim_path(name, root=None):
    """The file for an encyclopedia name, or None when the /zim/ reader would refuse it.

    Same check as engine/library.py zim_file(): links and junctions are followed, and a file whose real path is
    outside collections/ (or has a refused name, or an unsafe Windows segment) is refused. So Chat never searches,
    reads or cites a file whose source card could not then open.
    """
    try:
        path = safe_paths.zim_file(library_dir(root), name)
    except (ValueError, OSError):
        return None
    try:
        return path if path.is_file() else None
    except OSError:
        return None


def list_files(root=None):
    """Filenames of encyclopedia files that are actually present and that the /zim/ reader would open."""
    folder = collections_dir(root)
    try:
        names = sorted(p.name for p in folder.glob('*.zim'))
    except OSError:
        return []
    return [n for n in names if zim_path(n, root) is not None]


def publisher(name):
    stem = (name or '').lower()
    for prefix, label in LABELS:
        if stem.startswith(prefix):
            return label
    return Path(name or '').stem.replace('_', ' ') or 'Encyclopedia'


def year_of(name):
    m = re.search(r'(20\d{2})(?:-\d{2})?', name or '')
    return int(m.group(1)) if m else None


def parse_key(key):
    """Split a zim/file/Article key. None if the shape is unsafe or empty."""
    raw = urllib.parse.unquote((key or '').strip()).lstrip('/')
    m = KEY.match(raw)
    if not m:
        return None
    name, article = m.group(1), m.group(2).strip()
    if Path(name).name != name or not article or article.startswith('/') or '..' in article.split('/'):
        return None
    return name, article


def key_ok(key, names=None, root=None):
    """True when key names a real article path in a present (or provided) encyclopedia file."""
    parsed = parse_key(key)
    if not parsed:
        return False
    name, article = parsed
    # names: a list the caller already checked the same way (server.zim_names uses list_files).
    present = set(names) if names is not None else set(list_files(root))
    return bool(article) and name in present


def ui_path(name, article):
    """The /zim/... address the encyclopedia reader already understands."""
    return 'zim/' + urllib.parse.quote(name) + '/' + urllib.parse.quote(article, safe='/')


def zim_key(name, article):
    return 'zim/' + name + '/' + article


def html_to_text(raw):
    """Plain text from an encyclopedia page, with markup and scripts removed."""
    raw = raw or ''
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode('utf-8', 'replace')
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        BeautifulSoup = None
    if BeautifulSoup is not None:
        soup = BeautifulSoup(raw, 'html.parser')
        for tag in soup(['script', 'style', 'noscript']):
            tag.decompose()
        text = soup.get_text(' ', strip=True)
    else:
        text = re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>', ' ', raw)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = html.unescape(text)
    return re.sub(r'\s+', ' ', text).strip()


def pick_section(text, query, cap=READ_CHARS):
    """A capped slice of text, starting at a paragraph that matches query when one does."""
    text = text or ''
    cap = max(0, int(cap))
    if len(text) <= cap and not (query or '').strip():
        return text
    words = [w for w in re.findall(r'[a-z0-9]{3,}', (query or '').lower())]
    if not words:
        return text[:cap]
    paras = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()] or [text]
    # Fall back to sentence-like splits when the article arrived as one line of HTML text.
    if len(paras) == 1 and len(paras[0]) > cap:
        paras = [p.strip() for p in re.split(r'(?<=\.)\s+', paras[0]) if p.strip()] or paras
    best_i, best_n = 0, -1
    for i, p in enumerate(paras):
        low = p.lower()
        n = sum(1 for w in words if w in low)
        if n > best_n:
            best_i, best_n = i, n
    if best_n <= 0:
        return text[:cap]
    chunk = ' '.join(paras[best_i:best_i + 6])
    return chunk[:cap].strip()


def _open_archive(path):
    from libzim.reader import Archive
    path = Path(path)
    stamp = (str(path), path.stat().st_mtime_ns)
    with _lock:
        cached = _archives.get(path.name)
        if cached and cached[0] == stamp:
            return cached[1]
        arc = Archive(path)
        _archives[path.name] = (stamp, arc)
        return arc


def prefer_primary(paths):
    """Put untranslated article paths first; drop a /lang variant when the same article is already present.

    Appropedia (and some other ZIM files) index translations as Article/es, Article/hi, … and those
    often rank above the English page. Chat and the Encyclopedias search are English-first.
    """
    primary, variants, seen = [], [], set()
    for raw in paths:
        p = getattr(raw, 'path', raw)
        tail = p.rsplit('/', 1)
        suffix = tail[1] if len(tail) == 2 and 2 <= len(tail[1]) <= 3 and tail[1].isalpha() and tail[1].islower() else None
        if suffix:
            variants.append(p)
        elif p not in seen:
            primary.append(p)
            seen.add(p)
    out = list(primary)
    seen_bases = set(primary)
    for p in variants:
        if p in seen:
            continue
        base = p.rsplit('/', 1)[0]
        if base in seen_bases:
            continue
        out.append(p)
        seen.add(p)
        seen_bases.add(base)
    return out


def _search_paths(arc, q, per_file):
    from libzim.search import Searcher, Query
    if not getattr(arc, 'has_fulltext_index', False):
        return []
    result = Searcher(arc).search(Query().set_query(q))
    # libzim 3.x (what Lastbook pins) uses getResults; 4.x renamed it to get_results
    # and yields SearchResult objects instead of path strings.
    if hasattr(result, 'getResults'):
        return list(result.getResults(0, per_file))
    return [getattr(r, 'path', r) for r in result.get_results(0, per_file)]


def _follow(entry):
    for _ in range(8):
        if not getattr(entry, 'is_redirect', False):
            return entry
        entry = entry.get_redirect_entry()
    return entry


def entry_text(arc, article, cap=READ_CHARS):
    """Plain text of one article in an already-open archive, capped. None if it cannot be read."""
    try:
        entry = _follow(arc.get_entry_by_path(article))
        item = entry.get_item()
        mime = (getattr(item, 'mimetype', None) or '').lower()
        raw = bytes(item.content) if not isinstance(item.content, (str, bytes, bytearray)) else item.content
        if isinstance(raw, bytes):
            raw = raw.decode('utf-8', 'replace')
        if 'html' in mime or 'xml' in mime or '<html' in raw[:200].lower() or '<p' in raw[:400].lower():
            text = html_to_text(raw)
        else:
            text = re.sub(r'\s+', ' ', raw).strip()
        title = getattr(entry, 'title', None) or article
        return title, (text[:cap] if cap is not None else text)
    except Exception:
        return None


def iter_archives(root=None, opener=None):
    """Yield (filename, path, archive) for each encyclopedia file that can be opened."""
    opener = opener or _open_archive
    for name in list_files(root):
        path = zim_path(name, root)
        if path is None:
            continue
        try:
            yield path.name, path, opener(path)
        except Exception as e:
            print(f'encyclopedia skipped {path.name}: {type(e).__name__}', flush=True)


def search(q, per_file=PER_FILE, limit=SEARCH_LIMIT, root=None, archives=None, search_paths=None,
           read_text=True, excerpt=SEARCH_EXCERPT, collection=None):
    """Search the offline encyclopedias. Each hit is a dict with title, zim file, article path and excerpt.

    archives: optional list of (filename, archive) for tests, so libzim is not required.
    collection: optional filename, stem, or short name (mdwiki, wikipedia, …) to limit to one file.
    If every present file fails to open or search, raises RuntimeError, matching the existing API.
    """
    q = (q or '').strip()
    if not q:
        return []
    per_file = max(1, min(PER_FILE, int(per_file or PER_FILE)))
    limit = max(1, min(SEARCH_LIMIT, int(limit or SEARCH_LIMIT)))
    excerpt = max(0, int(excerpt if excerpt is not None else SEARCH_EXCERPT))
    search_paths = search_paths or _search_paths
    wanted = (collection or '').strip().lower()
    hits, tried, failed = [], 0, 0
    if archives is not None:
        rows = list(archives)
    else:
        rows = []
        for name in list_files(root):
            path = zim_path(name, root)
            if path is None:
                continue
            try:
                rows.append((path.name, _open_archive(path)))
            except Exception as e:
                tried += 1
                failed += 1
                print(f'collection search skipped {path.name}: {type(e).__name__}', flush=True)
    for name, arc in rows:
        if wanted and wanted not in name.lower() and wanted not in publisher(name).lower():
            continue
        tried += 1
        try:
            paths = prefer_primary(search_paths(arc, q, per_file))
            for article in paths:
                entry = _follow(arc.get_entry_by_path(article))
                title = getattr(entry, 'title', None) or article
                text = ''
                if read_text:
                    got = entry_text(arc, article, cap=max(excerpt, 1) if excerpt else 0)
                    if got:
                        title, text = got
                hits.append({
                    'title': title,
                    'collection': Path(name).stem,
                    'zim': name,
                    'article': article,
                    'zim_key': zim_key(name, article),
                    'path': ui_path(name, article),
                    'publisher': publisher(name),
                    'year': year_of(name),
                    'trust': TRUST,
                    'kind': 'zim',
                    'excerpt': re.sub(r'\s+', ' ', text)[:excerpt] if excerpt else '',
                })
                if len(hits) >= limit:
                    return hits
        except Exception as e:
            failed += 1
            print(f'collection search skipped {name}: {type(e).__name__}', flush=True)
    if tried and failed == tried:
        raise RuntimeError('no collection could be searched')
    return hits


def read(key, query='', cap=READ_CHARS, root=None, archives=None):
    """Read one article by zim/file/Article key. Returns a hit dict, or None if it is missing or unsafe."""
    parsed = parse_key(key)
    if not parsed:
        return None
    name, article = parsed
    cap = max(0, int(cap if cap is not None else READ_CHARS))
    arc = None
    if archives is not None:
        for n, a in archives:
            if n == name:
                arc = a
                break
    else:
        path = zim_path(name, root)
        if path is not None:
            try:
                arc = _open_archive(path)
            except Exception:
                return None
    if arc is None:
        return None
    got = entry_text(arc, article, cap=None)
    if not got:
        return None
    title, text = got
    body = pick_section(text, query, cap)
    return {
        'title': title,
        'collection': Path(name).stem,
        'zim': name,
        'article': article,
        'zim_key': zim_key(name, article),
        'path': ui_path(name, article),
        'publisher': publisher(name),
        'year': year_of(name),
        'trust': TRUST,
        'kind': 'zim',
        'excerpt': re.sub(r'\s+', ' ', body)[:900],
        'text': body,
    }
