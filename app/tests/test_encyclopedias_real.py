#!/usr/bin/env python3
"""Integration tests against a real Kiwix ZIM (the Small-pack Appropedia file, or another via LASTBOOK_TEST_ZIM).

Skipped when the file is not on this computer. The ZIM is not in the repository. No model, no internet once the file is present.

  LASTBOOK_TEST_ZIM=/path/to/appropedia_en_all_maxi_2026-02.zim python3 -B -m unittest app.tests.test_encyclopedias_real
"""
import json, os, shutil, socket, subprocess, sys, tempfile, threading, time, unittest, urllib.error, urllib.request
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]

ZIM_NAME = 'appropedia_en_all_maxi_2026-02.zim'
QUERIES = (
    ('water purification', ('purif', 'water', 'filter', 'chlor', 'disinfect', 'boil', 'treat')),
    ('oral rehydration solution', ('rehydrat', 'ors', 'diarr', 'cholera', 'electrolyte', 'saline', 'solution')),
    ('burn first aid', ('burn', 'scald', 'first aid', 'wound', 'cool', 'dressing', 'thermal')),
)


def find_zim():
    """The real encyclopedia file, or None if this machine does not have one."""
    env = os.environ.get('LASTBOOK_TEST_ZIM')
    if env:
        p = Path(env).expanduser()
        return p if p.is_file() else None
    places = [
        ROOT.parent / 'zim-fixtures' / ZIM_NAME,
        Path('/workspace/lastbook/zim-fixtures') / ZIM_NAME,
    ]
    for p in places:
        if p.is_file() and p.stat().st_size > 1_000_000:
            return p
    return None


# Lastbook's own top-level modules and package: what load() may import and must not leave behind.
PROJECT_MODULES = ('assistant', 'retrieval', 'server', 'llm_local', 'bridge', 'engine')


def ours(name):
    return name.split('.')[0] in PROJECT_MODULES


def load():
    before, env = dict(sys.modules), dict(os.environ)
    sys.path.insert(0, str(ROOT))
    sys.modules['onnxruntime'] = None
    try:
        from engine import encyclopedias
        import assistant
        return encyclopedias, assistant
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))
        for name in set(sys.modules) - set(before):   # Lastbook's own modules only; NumPy and the like stay loaded
            if ours(name):
                del sys.modules[name]
        sys.modules.update(before)
        if 'onnxruntime' not in before:
            sys.modules.pop('onnxruntime', None)
        os.environ.clear()
        os.environ.update(env)


ZIM = find_zim()


@unittest.skipUnless(ZIM, 'no real ZIM file (set LASTBOOK_TEST_ZIM, or put the Small-pack Appropedia ZIM in zim-fixtures/)')
class RealZim(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.encyclopedias, cls.assistant = load()
        cls.tmpdir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        cls.data = Path(cls.tmpdir.name)
        collections = cls.data / 'library-data' / 'collections'
        collections.mkdir(parents=True)
        dest = collections / ZIM.name
        # The file must really sit in collections/: a symlink to it is refused, like the /zim/ reader refuses it.
        try:
            os.link(ZIM.resolve(), dest)   # same filesystem: a hard link, no copy
        except OSError:
            shutil.copyfile(ZIM.resolve(), dest)
        cls.lib = cls.data / 'library-data'
        cls.zim_name = ZIM.name
        cls.root = cls.lib

    @classmethod
    def tearDownClass(cls):
        cls.tmpdir.cleanup()

    def setUp(self):
        self.E = self.encyclopedias
        self.A = self.assistant
        self.saved_s = self.A.S
        self.A.S = mock.Mock()
        self.A.S.catalog.return_value = {'by_id': {}}
        self.A.S.zim_names.return_value = [self.zim_name]

    def tearDown(self):
        self.A.S = self.saved_s

    def test_search_and_read_caps_and_relevance(self):
        E = self.E
        report = []
        for query, needles in QUERIES:
            hits = E.search(query, root=self.root, limit=8, excerpt=E.SEARCH_EXCERPT)
            self.assertLessEqual(len(hits), 8, query)
            relevant = []
            for h in hits:
                self.assertEqual(h['kind'], 'zim')
                self.assertEqual(h['zim'], self.zim_name)
                self.assertTrue(h['zim_key'].startswith('zim/' + self.zim_name + '/'))
                self.assertTrue(h['path'].startswith('zim/'))
                self.assertLessEqual(len(h.get('excerpt') or ''), E.SEARCH_EXCERPT, h['title'])
                blob = f"{h['title']} {h.get('excerpt') or ''}".lower()
                if any(n in blob for n in needles):
                    relevant.append(h['title'])
            report.append((query, len(hits), relevant[:5]))
            if query == 'water purification':
                self.assertTrue(hits, 'Appropedia should have water-purification articles')
                self.assertTrue(relevant, f'hits were not about the query: {[h["title"] for h in hits]}')
        # Medical queries may be thin in Appropedia (MDWiki is the medical file, and is larger than 1.5 GB).
        # Hits that do come back must still be well-formed; relevance is recorded, not required.
        self.assertTrue(any(n for _, _, n in report), report)

        # Initial-retrieval caps (what chat() fuses in).
        initial = E.search('water purification', root=self.root, limit=E.INITIAL_LIMIT, excerpt=E.INITIAL_CHARS)
        self.assertLessEqual(len(initial), E.INITIAL_LIMIT)
        for h in initial:
            self.assertLessEqual(len(h.get('excerpt') or ''), E.INITIAL_CHARS)

        # Read a capped section of the best water-purification hit.
        key = initial[0]['zim_key']
        got = E.read(key, query='purification', cap=E.READ_CHARS, root=self.root)
        self.assertIsNotNone(got)
        self.assertLessEqual(len(got['text']), E.READ_CHARS)
        self.assertIn('purif', (got['title'] + ' ' + got['text']).lower())
        tight = E.read(key, query='purification', cap=400, root=self.root)
        self.assertLessEqual(len(tight['text']), 400)

    def test_path_traversal_is_rejected(self):
        E = self.E
        name = self.zim_name
        for key in (
            'zim/../' + name + '/Water',
            'zim/' + name + '/../../etc/passwd',
            'zim/' + name + '/%2e%2e/etc/passwd',
            'zim/evil.zim/Water',
            '',
        ):
            self.assertIsNone(E.read(key, root=self.root), key)
            self.assertFalse(E.key_ok(key, names=[name]), key)

    def test_chat_tools_and_citation_validation(self):
        A, E = self.A, self.E
        sess = A.Session()
        # The same path chat() uses for the initial fused wiki hits.
        wiki = A.encyclopedia_hits('water purification', limit=E.INITIAL_LIMIT, excerpt=E.INITIAL_CHARS, root=self.root)
        self.assertTrue(wiki)
        self.assertLessEqual(len(wiki), E.INITIAL_LIMIT)
        blocks = []
        for it in wiki:
            src = A.wiki_row(it)
            k = sess.add(src)
            self.assertTrue(k.startswith('S'))
            self.assertTrue(A.source_known(src))
            blocks.append(k)
        text, summary = A.run_tool('search_encyclopedia', {'query': 'water purification', 'limit': 6}, sess, [], root=self.root)
        self.assertGreater(summary['count'], 0, text)
        self.assertIn('[S', text)
        self.assertIn('<<SOURCE', text)
        first = next(k for k in sess.sources if k.startswith('S'))
        answer, valid, invalid = A.validate_citations(f'Filter or disinfect water. [{first}][S99]', sess)
        self.assertEqual(valid, [first])
        self.assertEqual(invalid, ['S99'])
        grouped, valid, invalid = A.validate_citations(f'Boil when you can. [{first}, S99]', sess)
        self.assertIn(f'[{first}]', grouped)
        self.assertEqual(valid, [first])
        self.assertEqual(invalid, ['S99'])

        # Read via a citation key, as the model often does.
        text, summary = A.run_tool('read_encyclopedia', {'article': first, 'query': 'filter'}, sess, [], root=self.root)
        self.assertNotIn('error', summary, text)
        self.assertLessEqual(len(text), E.READ_CHARS + 800)  # source wrapper around the capped body
        self.assertTrue(summary.get('title'))
        # Invented or unsafe article paths.
        text, summary = A.run_tool('read_encyclopedia', {'article': 'zim/' + self.zim_name + '/../x'}, sess, [], root=self.root)
        self.assertEqual(summary.get('error'), 'unknown')

    def test_collection_search_http(self):
        """The Encyclopedias page API, through engine/library.py, against the same real file."""
        env = {**os.environ, 'LASTBOOK_LIBRARY': str(self.lib), 'LASTBOOK_DATA': str(self.data),
               'SURVIVAL_DISABLE_INDEX_WATCH': '1'}
        # Bind an ephemeral port ourselves so we do not have to parse a race on stdout.
        sock = socket.socket()
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
        sock.close()
        proc = subprocess.Popen(
            [sys.executable, '-B', str(ROOT / 'engine' / 'library.py'), 'serve', '--port', str(port)],
            cwd=str(ROOT), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        try:
            deadline = time.time() + 20
            ready = False
            buf = []

            def _pump():
                for line in proc.stdout:
                    buf.append(line)
                    if 'Offline library' in line:
                        break

            t = threading.Thread(target=_pump, daemon=True)
            t.start()
            while time.time() < deadline and proc.poll() is None:
                try:
                    urllib.request.urlopen(f'http://127.0.0.1:{port}/api/collection-search?q=water%20purification', timeout=2)
                    ready = True
                    break
                except Exception:
                    time.sleep(0.15)
            self.assertIsNone(proc.poll(), ''.join(buf) or f'server exited early, port {port}')
            url = f'http://127.0.0.1:{port}/api/collection-search?q=water%20purification'
            with urllib.request.urlopen(url, timeout=60) as resp:
                data = json.loads(resp.read().decode())
            self.assertIsInstance(data, list, data)
            self.assertTrue(data, 'collection-search returned no hits for water purification')
            for h in data:
                self.assertEqual(set(h), {'title', 'collection', 'path'}, h)
                self.assertTrue(h['path'].startswith('zim/'), h)
                self.assertIn('appropedia', h['collection'].lower())
            # A request that should not 500.
            with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/collection-search?q=', timeout=30) as resp:
                empty = json.loads(resp.read().decode())
            self.assertEqual(empty, [])
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
            if proc.stdout:
                proc.stdout.close()


if __name__ == '__main__':
    unittest.main()
