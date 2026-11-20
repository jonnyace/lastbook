"""Read a page's tables row by row before a model sees the page.

The library's PDF text comes from `pdftotext -layout`, so a table keeps its columns as runs of spaces. Chat squashed
every run of spaces to one, which reads the page line by line. When a row's label takes two lines and its amount sits
between them, or a column of prose runs beside the table, that interleaves the rows. Hesperian's bleach table:

    For 5 gallons or
                                1/2 teaspoon
    20 liters
    For a 200 liter
                                5 teaspoons
    barrel

squashed reads "20 liters For a 200 liter 5 teaspoons", and a small model gave 5 teaspoons for 20 litres (ten times the
dose). `for_model` finds columns of amounts (a number and a unit), attaches each line of the columns beside them to the
nearest amount, and writes the table as one line per row, "For 5 gallons or 20 liters | 1/2 teaspoon". The rest of the page
is squashed as before. Pages without such a column come back exactly as the old squash gave them. `page_text` is what
Chat calls: the page for the model, at most n characters.
"""
import collections, re

# an amount: a number (1, 2.5, 1/2, 1 1/2, ½, 1-2, 1 to 2) and then a unit, at the start of a short cell
_NUM = r'(?:\d+(?:[.,]\d+)?(?:\s*/\s*\d+)?(?:\s+\d/\d)?|[½¼¾⅓⅔]|\d+\s*[½¼¾])'
_UNIT = (r'(?:drops?|teaspoons?|teaspoonfuls?|tsp|tablespoons?|tablespoonfuls?|tbsp|spoons?|spoonfuls?|capfuls?|cups?|'
         r'glass(?:es)?|ml|mls|cc|l|liters?|litres?|gallons?|gal|quarts?|qt|pints?|ounces?|oz|fl\.? ?oz|mg|mcg|µg|ug|g|grams?|'
         r'kg|kilos?|lbs?|pounds?|tablets?|tabs?|capsules?|caps|pills?|sachets?|packets?|pinch(?:es)?|handfuls?|units?|iu|'
         r'kcal|kj|mmol|meq|puffs?|sprays?|doses?|times)')
_RANGE = rf'(?:[<>≤≥] ?)?{_NUM}(?:\s*(?:-|–|−|to|or)\s*{_NUM})?'
AMOUNT = re.compile(rf'^(?:about |up to |add )?(?:{_RANGE}\s*{_UNIT}\b|{_RANGE}\s*%$)', re.I)   # 1–2% only as a whole cell
CAPTION = re.compile(r'(table|figure|fig\.|source|note)\b', re.I)
_SEG = re.compile(r'\S+(?: {1,2}\S+)*')   # a cell: words with at most two spaces between them
WIDE = 45            # a segment this long is a line of prose, not a cell
NEAR = 2             # a label line joins an amount at most this many lines away


def _segments(lines):
    # some Hesperian pages have U+001A (SUB) where a blank line was
    return [[(m.start(), m.end(), m.group()) for m in _SEG.finditer(l.replace('\x1a', ' '))] for l in lines]


def _squash(text):
    return re.sub(r'[ \t]{2,}', ' ', text)


def _overlap(a, b, slack=1):
    return a[0] < b[1] + slack and b[0] < a[1] + slack


def _amount_columns(segs):
    """Amounts that stand apart (after a gap on their line, or indented), grouped into columns by x and closeness."""
    cands = []
    for i, row in enumerate(segs):
        for j, (x0, x1, t) in enumerate(row):
            if len(t) < WIDE and len(t.split()) <= 10 and AMOUNT.match(t) and (j > 0 or x0 >= 12):
                cands.append((i, x0, x1))
    cols = []
    for c in cands:
        for col in cols:
            if c[0] - col[-1][0] <= 8 and any(_overlap((c[1], c[2]), (d[1], d[2]), 2) for d in col):
                col.append(c)
                break
        else:
            cols.append([c])
    return [col for col in cols if len({c[0] for c in col}) >= 3]


def _bands(items):
    """Group (line, x0, x1, text) by overlapping x ranges."""
    items = sorted(items, key=lambda s: s[1])
    bands = []
    for s in items:
        if bands and s[1] < bands[-1]['x1'] + 1:
            bands[-1]['segs'].append(s)
            bands[-1]['x1'] = max(bands[-1]['x1'], s[2])
        else:
            bands.append({'x0': s[1], 'x1': s[2], 'segs': [s]})
    return bands


def _is_prose(band):
    lines = sorted({s[0] for s in band['segs']})
    run = best = 1
    for a, b in zip(lines, lines[1:]):
        run = run + 1 if b == a + 1 else 1
        best = max(best, run)
    mean = sum(len(s[3]) for s in band['segs']) / len(band['segs'])
    return best >= 5 and mean >= 18


def _table(lines, segs, col):
    """Rows for one column of amounts, and the segments they used (to take out of the page's lines)."""
    top, bottom = col[0][0], col[-1][0]
    lo, hi = max(0, top - NEAR - 1), min(len(lines) - 1, bottom + NEAR)
    cx0, cx1 = min(c[1] for c in col), max(c[2] for c in col)
    items = [(i, x0, x1, t) for i in range(lo, hi + 1) for (x0, x1, t) in segs[i] if x1 - x0 < WIDE]
    bands = _bands(items)
    anchor = next((b for b in bands if _overlap((b['x0'], b['x1']), (cx0, cx1))), None)
    if anchor is None:
        return None
    table = [b for b in bands if b is anchor or not _is_prose(b)]
    if len(table) < 2:
        return None
    # rows: each amount starts one; a line of the amount column without an amount continues the row above it
    rows = []
    for s in sorted(anchor['segs']):
        if AMOUNT.match(s[3]) and top <= s[0] <= bottom:
            rows.append({'a': s[0], 'b': s[0], 'cells': {id(anchor): [s]}})
        elif rows and s[0] - rows[-1]['b'] == 1 and s[0] <= bottom + 1:
            rows[-1]['b'] = s[0]
            rows[-1]['cells'][id(anchor)].append(s)
    if len(rows) < 3:
        return None
    used = {(s[0], s[1]) for r in rows for s in r['cells'][id(anchor)]}
    # a header: the nearest line above the first row with cells in two or more of the table's columns
    header = {}
    for i in range(rows[0]['a'] - 1, lo - 1, -1):
        on = [(b, s) for b in table for s in b['segs'] if s[0] == i]
        if len({id(b) for b, _ in on}) >= 2:
            for b, s in on:
                header.setdefault(id(b), []).append(s)
            used |= {(s[0], s[1]) for _, s in on}
            break
    top_row = max(i for i, _ in used if i < rows[0]['a']) + 1 if header else rows[0]['a'] - 1   # a label may start a line early
    for band in table:
        if band is anchor:
            continue
        for s in band['segs']:
            if (s[0], s[1]) in used or s[0] < top_row:
                continue
            dist = [(max(r['a'] - s[0], s[0] - r['b'], 0), k) for k, r in enumerate(rows)]
            d, k = min(dist)
            outside = s[0] < rows[0]['a'] or s[0] > rows[-1]['b']   # above the first row or below the last: only next to it
            if d <= (1 if outside else NEAR) and not CAPTION.match(s[3]):
                rows[k]['cells'].setdefault(id(band), []).append(s)
                used.add((s[0], s[1]))
    out, empty = [], 0
    for r in ([header] if header else []) + [r['cells'] for r in rows]:
        cells = [' '.join(s[3] for s in sorted(r.get(id(b), []))) for b in table]
        empty += r is not header and cells.count('')
        out.append(' | '.join(c or '-' for c in cells))
    tall = max(len({s[0] for s in c}) for r in rows for c in r['cells'].values())
    # a row with a label on its own line and more label lines that don't touch it has likely taken a neighbour's label
    # (one whose amount wasn't recognised)
    stray = 0
    for r in rows:
        mine = set(range(r['a'], r['b'] + 1))
        for b in table:
            got = {s[0] for s in r['cells'].get(id(b), [])}
            if b is not anchor and got & mine and got - mine:
                stray += any(not ({i - 1, i + 1} & (got | mine)) for i in got - mine) or len(got - mine) > 1
    # a label entirely above or entirely below its amount, not on the amount's line or around it: the nearest-line rule can
    # pair it with the next row's amount ("First crate / packed" over "1 kg" gave "packed Second crate | 1 kg")
    offside = any(got and not got & set(range(r['a'], r['b'] + 1)) and not (min(got) < r['a'] and max(got) > r['b'])
                  for r in rows for b in table if b is not anchor
                  for got in [{s[0] for s in r['cells'].get(id(b), [])}])
    merged = any(len({s[0] for s in b['segs']}) < len(b['segs']) for b in table)   # two cells of one line in one column
    # a cell of the amount column between rows that isn't an amount: a row whose value wasn't recognised, now merged
    # into its neighbour; or one cell holding amounts from two lines (two rows in one)
    unread = any((s[0], s[1]) not in used for s in anchor['segs'] if rows[0]['a'] < s[0] < rows[-1]['b'])
    doubled = any(len({s[0] for s in c if AMOUNT.match(s[3])}) > 1 for r in rows for c in r['cells'].values())
    sure = (empty <= 0.1 * len(rows) * len(table) and tall <= 3   # else cells wrap in ways nearest-amount can't follow
            and not stray and not offside and not merged and not unread and not doubled)
    first, last = min(i for i, _ in used), max(i for i, _ in used)
    # how many rows the old line-by-line reading got wrong: the row's pieces were not one run ending in its amount
    order = [(i, x0) for i, row in enumerate(segs) for (x0, _, _) in row]
    at = {k: n for n, k in enumerate(order)}
    mixed = 0
    for r in rows:
        mine = sorted(at[(s[0], s[1])] for c in r['cells'].values() for s in c)
        amount = max(at[(s[0], s[1])] for s in r['cells'][id(anchor)])
        mixed += mine[-1] - mine[0] + 1 != len(mine) or amount != mine[-1]
    return out, used, (first, last), mixed, sure


def _narrow(lines):
    """Printed lines with less space: a character column blank on every line goes, keeping two in a row, so what was
    lined up stays lined up."""
    width = max(len(l) for l in lines)
    lines = [l.ljust(width) for l in lines]
    keep, blank = [], 0
    for x in range(width):
        empty = all(l[x] == ' ' for l in lines)
        blank = blank + 1 if empty else 0
        if not empty or (blank <= 2 and keep):
            keep.append(x)
    return [''.join(l[x] for x in keep).rstrip() for l in lines]


def _down(block):
    """A table laid out across (weights or ages as columns, amounts in rows), as lines that each read down one column.
    A small model counting columns in the printed layout took the 6 kg column for the 7 kg one. Only for four or more
    lined-up columns of mostly amounts; anything less regular gives nothing."""
    starts = [x0 for row in block for x0, _, _ in row]
    if not starts:
        return []
    lx = min(starts)
    cells = [[s for s in row if s[0] > lx + 2] for row in block]
    full = [c for c in cells if len(c) >= 4]
    if len(full) < 2:
        return []
    k = collections.Counter(len(c) for c in full).most_common(1)[0][0]
    ref = [c for c in full if len(c) == k]
    mid = lambda s: (s[0] + s[1]) / 2   # noqa: E731
    best = max(ref, key=lambda c: sum(bool(AMOUNT.match(s[2])) for s in c))
    if len(ref) < 2 or sum(bool(AMOUNT.match(s[2])) for s in best) < k - 1:
        return []
    centres = [mid(s) for s in best]
    half = min(b - a for a, b in zip(centres, centres[1:])) / 2
    cols = [[] for _ in centres]
    for c in cells:
        seen = set()
        for s in c:
            j = min(range(k), key=lambda j: abs(mid(s) - centres[j]))
            if abs(mid(s) - centres[j]) > half or j in seen:
                return []        # a cell across two columns, or two in one: not a grid this can read
            seen.add(j)
            cols[j].append(s[2])
    labels = [s[2] for row in block for s in row if s[0] <= lx + 2]
    return (['', 'The same table read down each column (top to bottom' + (': ' + ', '.join(labels) if labels else '') + '):']
            + [f'Column {j + 1}: ' + ', '.join(col) for j, col in enumerate(cols)])


def clip(text, n):
    """At most n characters of the page as the old squashed text counted them (the spaces kept in a printed table
    don't count), cut at a line end when one is near."""
    if len(_squash(text)) <= n:
        return text
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        lo, hi = (mid, hi) if len(_squash(text[:mid])) <= n else (lo, mid - 1)
    end = text.rfind('\n', 0, lo)
    return text[:end if end > lo - 200 else lo]


def tables(text):
    """The amount tables on a layout page: [{'rows': [...], 'used': {(line, x)}, 'last': line, 'mixed': how many rows
    the old line-by-line reading interleaved}]."""
    if not text or not re.search(r'\d|[½¼¾⅓⅔]', text):
        return []
    lines = text.split('\n')
    segs = _segments(lines)
    found, taken = [], set()
    for col in sorted(_amount_columns(segs), key=lambda c: -min(x[1] for x in c)):   # amounts sit right of their labels
        if any((c[0], c[1]) in taken for c in col):
            continue
        t = _table(lines, segs, col)
        if t:
            taken |= t[1]
            found.append({'rows': t[0], 'used': t[1], 'first': t[2][0], 'last': t[2][1], 'mixed': t[3], 'sure': t[4]})
    return found


def for_model(text):
    """The page as a model should read it. A table whose rows can be told apart: one row per line. One whose cells wrap in
    ways that can't, and that the old reading interleaved: as printed, spaces kept. Everything else squashed as before."""
    found = tables(text)
    rebuilt = [t for t in found if t['sure']]
    printed = [t for t in found if not t['sure'] and t['mixed']]
    if not rebuilt and not printed:
        return _squash(text)
    lines = text.replace('\x1a', ' ').split('\n')
    segs = _segments(lines)
    taken = set().union(*(t['used'] for t in rebuilt)) if rebuilt else set()
    for t in printed:   # a printed table goes on over the lines next to it that still have two or more columns
        # ... and over lines whose cells all start at a column the table uses ("10 to", "0.9% NaCl"); one blank line may
        # sit between
        def part(i):
            if not 0 <= i < len(segs) or not segs[i]:
                return False
            xs = {x0 for row in segs[t['first']:t['last'] + 1] for x0, _, _ in row}
            return len(segs[i]) >= 2 or all(any(abs(x0 - x) <= 1 for x in xs) and len(c) <= 30 for x0, _, c in segs[i])
        while part(t['first'] - 1) or t['first'] >= 2 and not segs[t['first'] - 1] and part(t['first'] - 2):
            t['first'] -= 1
        while part(t['last'] + 1) or t['last'] + 1 < len(segs) and not segs[t['last'] + 1] and part(t['last'] + 2):
            t['last'] += 1
    keep = {i for t in printed for i in range(t['first'], t['last'] + 1)}
    after = {}
    for t in rebuilt:
        after.setdefault(t['last'], []).append(['Table (one row per line, columns split by |):'] + t['rows'])
    for t in printed:
        after.setdefault(t['last'], []).append(['Table as printed (read each column by its position; a row may take '
                                                'several lines):'] + _narrow(lines[t['first']:t['last'] + 1])
                                               + _down(segs[t['first']:t['last'] + 1]))
    out = []
    for i, row in enumerate(segs):
        rest = ' '.join(s[2] for s in row if (i, s[0]) not in taken)
        if i not in keep and (rest or not row):
            out.append(rest)
        for block in after.get(i, []):
            out.extend(block)
            out.append('')
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out))


def page_text(text, n):
    """A page as the model reads it, at most n characters. A page with no table to rebuild is exactly the old squashed
    text cut at n."""
    body = for_model(text)
    if body == _squash(text):
        return body.strip()[:n]
    return clip(body.strip(), n)
