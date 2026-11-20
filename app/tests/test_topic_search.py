#!/usr/bin/env python3
"""Topic search beyond a-z: web/words.js run in Node, with Intl.Segmenter, without it, and with one that throws.

  python3 -B -m unittest app.tests.test_topic_search [-v]

Accented words stay whole and fold (niño finds nino), short words in Chinese, Hindi, Hebrew and Arabic count,
typed symbols never reach a RegExp, Turkish İ folds to i, and every English query in the list ranks exactly as it
did before. Words used outside the US (torch, rubbish, 999, 108, 1122, power cut, loadshedding, hydro, forest fire)
find the guide their US word finds. Needs Node on PATH; skipped without it. Never packaged."""
import json, re, shutil, subprocess, tempfile, unicodedata, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
NODE = shutil.which('node')
WORDS = ROOT / 'web' / 'words.js'

# The stop words app.js passes in, read from app.js so the test follows it.
QSTOP = re.search(r"const QSTOP = new Set\('([^']*)'\.split", (ROOT / 'web' / 'app.js').read_text(encoding='utf-8')).group(1).split(' ')
TOPICS = [json.loads(p.read_text(encoding='utf-8')) for p in sorted((ROOT / 'content' / 'topics').glob('*.json'))]

# Everyday English questions. Each must give the same topics and choices as the old a-z matching,
# including words joined by punctuation, which the old split took apart.
ENGLISH = [
    'how do I purify water', 'boil water', 'is the tap water safe', 'bleach for drinking water', 'find water',
    'deep cut bleeding', 'broken leg', 'burn on my hand', 'cpr', 'choking', 'fever', 'dehydration', 'snake bite',
    'hypothermia', 'the power is out', 'generator', 'solar panel', 'car battery', 'earthquake', 'flood',
    'wildfire smoke', 'store food', 'cook without power', 'stay warm', 'shelter', 'toilet', 'radio',
    'grow vegetables', 'save seeds', 'first aid kit', "water's gone brown", "don't have power", "can't breathe",
    'how to start a fire', 'baby', 'medicine', 'keep food cold', 'clean water storage container',
    'water.boil', 'first_aid kit', 'e.coli', 'boil:water', 'https://example.org/water',
]

# Everyday words a guide covers, and the guide and choice search must show first, with and without Intl.Segmenter.
# Most found nothing or the wrong guide until the word was added to the hint of the choice that covers it. A word only
# in a topic's keywords is not enough: another word then picks the choice ("poisoned water" went to burns, for "hot water").
EVERYDAY = {
    'burned my hand': ['hurt', 'burn'], 'burnt': ['hurt', 'burn'],
    'fractured arm': ['hurt', 'bone'], 'dislocated shoulder': ['hurt', 'bone'], 'poisoned': ['hurt', 'poison'],
    'heatstroke': ['hurt', 'heatcold'], 'throwing up': ['hurt', 'diarrhea'], 'dehydrated': ['hurt', 'diarrhea'],
    'diarrhoea': ['hurt', 'diarrhea'], 'suicidal': ['health', 'mind'],
    'bushfire smoke': ['disaster', 'smoke'],
    'poisoned water': ['water', 'chemical'], 'drank poisoned water': ['water', 'chemical'],
    'dehydrated water': ['hurt', 'diarrhea'], 'throwing up water': ['hurt', 'diarrhea'], 'diarrhoea water': ['hurt', 'diarrhea'],
    'fractured neck': ['hurt', 'head'], 'fractured back': ['hurt', 'head'], 'dislocated neck': ['hurt', 'head'],
    'fractured skull': ['hurt', 'head'], 'fractured spine': ['hurt', 'head'], 'dislocated spine': ['hurt', 'head'],
    'spinal fracture': ['hurt', 'head'], 'fractured vertebra': ['hurt', 'head'], 'fractured vertebrae': ['hurt', 'head'],
    'vertebral fracture': ['hurt', 'head'], 'fractured vertebral column': ['hurt', 'head'],
    'I drank from the stream and have diarrhea': ['hurt', 'diarrhea'], 'I drank and feel dehydrated': ['hurt', 'diarrhea'],
}

# Injuries in a forest: since "forest fires" joined the wildfire hint, "forest" also picks wildfire, so these only have
# to show Broken bone somewhere in the results, not first.
LISTED = {
    'I fractured my arm in the forest': ['hurt', 'bone'], 'I dislocated my shoulder in the forest': ['hurt', 'bone'],
    'I had a fall in the forest': ['hurt', 'bone'],
}

# Query -> words, the same with or without Intl.Segmenter (every script here uses spaces).
WORDS_BOTH = {
    '¿Cómo purifico el agua para el niño?': ['como', 'purifico', 'agua', 'para', 'nino'],   # accents whole, then folded
    'niño': ['nino'],                                     # precomposed ñ
    'niño': ['nino'],                                    # n + combining tilde (NFD)
    'crème brûlée': ['creme', 'brulee'],        # every accent goes, not just the first
    "How do I purify water's taste?": ['purify', 'water', 'taste'],   # water's -> water, as before
    'don’t have water': ['water'],                         # curly apostrophe, stop words
    'ｗａｔｅｒ': ['water'],                # full-width Latin
    'water.boil first_aid e.coli boil:water': ['water', 'boil', 'first', 'aid', 'coli', 'boil', 'water'],
    'water­proof': ['water', 'proof'],                     # soft hyphen separates, as in FTS5
    'می‌خواهم': ['می', 'خواهم'],   # ZWNJ separates
    'आग אש دم': ['आग', 'אש', 'دم'],   # two-letter words without case
    'पानी उबालें': ['पानी', 'उबालें'],   # marks stay in words
    'ab 42 112 go': ['112'],                                    # short Latin words and numbers dropped, as before
    '\U00010428\U0001042f': [],                                # two letters outside the BMP: still two, still too short
    'c++ (water': ['water'],
    '[a': [], '(': [], '\\': [], '*?+{': [], '': [],            # symbols: no words, no exception
    'İstanbul': ['istanbul'],
    'éclair': ['eclair'],
}

FOLD = {
    'İstanbul': 'istanbul', 'ISTANBUL': 'istanbul', 'ılık': 'ılık',   # dotless ı stays
    'Straße': 'straße', 'ΣΟΦΟΣ': 'σοφοσ',   # ß stays, ς -> σ, as FTS5
    'ｗａｔｅｒ': 'water', 'niño': 'nino', 'niño': 'nino', 'Jalapeño': 'jalapeno',
    'καφές': 'καφέσ',   # Greek accents kept, as in FTS5
    'crème brûlée': 'creme brulee',
}

MATCH = [  # text, word, expected
    ['chocolate éclair', 'eclair', True], ['Chocolate Éclair', 'eclair', True],
    ['煮沸 水', '水', True], ['怎么净化水', '净化', True],
    ['drink water', 'rink', False], ['drink water', 'drin', True], ['Rainwater', 'water', False],
    ['Straße', 'strasse', False], ['ΣΟΦΟΣ', 'σοφοσ', True],
    ['İstanbul', 'istanbul', True], ['72-hour kit', 'hour', True], ['Water: purify, boil', 'purif', True],
]

# Words used outside the US, each with the US word the guides already had. A search for the first must give
# the same guides and choices, in the same order, as a search for the second.
SAME_AS = {
    'torch': 'flashlight', 'rubbish': 'garbage', 'rubbish pickup': 'trash pickup', 'tinned food': 'canned food',
    '999': '911', '112': '911', '111': '911', 'adrenaline': 'epinephrine',
    '108': '911', 'geyser': 'water heater',
    '1122': '911', '115': '911',   # Rescue 1122 and Edhi in Pakistan
}
# These sit in a guide's keywords only, so they open the same guide first but pick no choice of their own.
# In a hint, "bushfire" would also answer "bus" and "barbecue" would answer "bar" (a search word matches the
# start of a word), and "heatwave" or "sanitiser" beside the US spelling would read oddly.
SAME_GUIDE = {
    'bushfire': 'wildfire', 'bushfire smoke': 'wildfire smoke', 'heatwave': 'heat wave', 'barbecue': 'grill',
    'bbq': 'grill', 'sanitiser': 'sanitizer', 'hand sanitiser': 'hand sanitizer',
    'heatstroke': 'heat stroke',
    'snowstorm': 'winter storm', 'snow squall': 'winter storm', 'whiteout': 'winter storm',
    'polar vortex': 'winter storm', 'wind chill': 'winter storm', 'arctic outflow': 'winter storm',
    'warming centre': 'winter storm', 'aqhi': 'air quality', 'AQHI': 'air quality',
    'cooling centre': 'cooling center', 'washroom': 'sanitation',
    # Pakistan's scheduled power cuts. Written as one word in the keywords: "load shedding" as two would let
    # "shed" open the power guide, and "load" in a hint would take "generator load" away from the generator choice.
    'loadshedding': 'power cut', 'load shedding': 'power cut', 'load-shedding': 'power cut',
}
# Words used in South Asia and Canada with no single US twin among the guides: [guide, choice] that comes first.
FIRST = {
    'power cut': ['power', 'first-hours'], 'cyclone': ['disaster', 'flood'], 'monsoon': ['disaster', 'flood'],
    'borewell': ['water', 'outside'], 'tubewell': ['water', 'outside'], 'loose motions': ['hurt', 'diarrhea'],
    'hydro': ['power', 'first-hours'], 'hydro is out': ['power', 'first-hours'],
    'hydro outage': ['power', 'first-hours'], 'ice storm': ['shelter', 'cold'], 'freezing rain': ['shelter', 'cold'],
    'extreme cold': ['shelter', 'cold'], 'cold snap': ['shelter', 'cold'], 'blizzard': ['shelter', 'cold'],
    'furnace': ['shelter', 'cold'], 'furnace is out': ['shelter', 'cold'], 'frostnip': ['hurt', 'heatcold'],
    'forest fire': ['disaster', 'wildfire'], 'forest fires': ['disaster', 'wildfire'],
    'forest fire smoke': ['disaster', 'smoke'], 'Hydro': ['power', 'first-hours'], 'Frostnip': ['hurt', 'heatcold'],
    'cold': ['shelter', 'cold'], 'its cold': ['shelter', 'cold'],
    'house fire': ['disaster', 'home-fire'], 'my house is on fire': ['disaster', 'home-fire'],
    'smog': ['shelter', 'smoke'],   # winter smog in Lahore and Delhi; the choice cites a page on particles and ozone
}
# Searches the new words must not disturb: [guide, choice] that comes first.
UNDISTURBED = {
    'bus': ['disaster', 'no-car'], 'no bus': ['disaster', 'no-car'], 'bar soap': ['sanitation', 'hands'],
    'heat wave': ['shelter', 'heat'], 'grill': ['food', 'cook'], 'canned food': ['food', 'cook'],
    'cut': ['hurt', 'bleeding'], 'well': ['land', 'water-source'], 'storm': ['disaster', 'flood'],
    'ice': ['water', 'inhome'], 'micro-hydro': ['energy', None], 'wind': ['disaster', 'hurricane'],
    'winter storm': ['shelter', 'cold'], 'furnace smells like gas': ['power', 'gas'], 'gas furnace': ['power', 'gas'],
    'lost in the forest': ['comms', 'signal'],
    'cold frame': ['repair', 'build'], 'freezing': ['shelter', 'cold'],
    'fire alarm': ['disaster', 'home-fire'], 'smoke alarm': ['disaster', 'home-fire'], 'smoke': ['disaster', 'smoke'],
    'fires after an earthquake': ['disaster', 'earthquake-after'],
    'shed': ['repair', None], 'generator load': ['power', 'generator'], 'air quality': ['shelter', 'smoke'],
}
# A search that names a sign of a life-threatening emergency shows that choice, even if another choice in the guide
# matches more words. The rest don't say the person isn't breathing or is unconscious, and keep their choice.
URGENT = {
    'burn and not breathing': ['hurt', 'breathing'], 'broken leg and not breathing': ['hurt', 'breathing'],
    'cut and not breathing': ['hurt', 'breathing'], 'fractured neck and not breathing': ['hurt', 'breathing'],
    'dislocated neck unconscious': ['hurt', 'breathing'], 'my baby stopped breathing': ['hurt', 'breathing'],
    "he isn't breathing": ['hurt', 'breathing'], 'choking': ['hurt', 'breathing'],
    'allergic reaction trouble breathing': ['hurt', 'allergy'], "can't breathe after a bee sting": ['hurt', 'allergy'],
    'gas burn': ['hurt', 'burn'], 'broken leg stuck under rubble': ['hurt', 'bone'],
    'wound infection not responding to antibiotics': ['hurt', 'bleeding'],
    'allergic reaction not responding to epinephrine': ['hurt', 'allergy'],
    'allergic reaction choking': ['hurt', 'allergy'], 'burn and choking on smoke': ['hurt', 'burn'],
}
# A breathing emergency after a sting must not open routine sting care.
NOT_STING = ["bee sting can't breathe", 'bee sting cannot breathe', 'bee sting unconscious', 'wasp sting unconscious']
TOPS = sorted({*SAME_AS, *SAME_AS.values(), *SAME_GUIDE, *SAME_GUIDE.values(), *FIRST, *UNDISTURBED, *URGENT, *EVERYDAY, *LISTED, *NOT_STING})

# A made-up topic in Spanish and Chinese: found by Spanish words and by a single Han character.
OWN = {'id': 'own', 'title': 'Agua potable', 'short': 'Hervir el agua', 'keywords': ['水'], 'choices': []}
RANK_OWN = [['agua', [OWN]], ['水', [OWN]], ['hervir', [OWN]]]

# Emergencies where the first choice decides what someone reads first. A cardiac arrest needs CPR, not the
# long-term care guide that "heart" also matches: [guide, choice] that comes first.
EMERGENCY_FIRST = {
    'cardiac arrest': ['hurt', 'breathing'], 'heart stopped': ['hurt', 'breathing'], 'AED': ['hurt', 'breathing'],
    'aed': ['hurt', 'breathing'], 'defibrillator': ['hurt', 'breathing'], 'heart attack': ['hurt', 'sudden'],
    'having a heart attack': ['hurt', 'sudden'], 'signs of heart attack': ['hurt', 'sudden'],
}
# Searches those words must not disturb: [guide, choice] that comes first.
EMERGENCY_UNDISTURBED = {
    'heart': ['health', 'chronic'], 'heart disease': ['health', 'chronic'], 'blood pressure': ['health', 'chronic'],
    'chest pain': ['hurt', 'sudden'], 'collapsed': ['hurt', 'breathing'], 'not breathing': ['hurt', 'breathing'],
    'drowning': ['hurt', 'breathing'], 'cpr': ['hurt', None], 'stopped': ['disaster', 'earthquake-after'],
}
TOPS = sorted({*TOPS, *EMERGENCY_FIRST, *EMERGENCY_UNDISTURBED})

# A guide whose urgent phrase the search names comes first, even when the other words pull another guide ahead or
# below the cut; that guide is still offered: query -> (first row, a row that must still be shown).
GUIDE_URGENT = {
    'unconscious in the flood water': (['hurt', 'breathing'], ['water', 'unsafe']),
    'unconscious after drinking flood water': (['hurt', 'breathing'], ['water', 'unsafe']),
    'not breathing after falling in the well water': (['hurt', 'breathing'], ['land', 'water-source']),
    'unconscious after the generator ran indoors': (['hurt', 'breathing'], ['shelter', 'co']),
    'child unconscious after pet food': (['hurt', 'breathing'], None), 'pet food unconscious': (['hurt', 'breathing'], None),
}
# Searches without an urgent phrase keep their guide order: [guide, choice] that comes first.
GUIDE_ORDINARY = {
    'how do i light a campfire': ['power', 'first-hours'], 'treat water': ['water', 'keepclean'],
    "make the water safe for a baby's formula": ['food', 'outage'], 'not responding to antibiotics': ['health', 'medicine'],
    'radio not responding': ['comms', 'alerts-radio'], 'dental abscess': ['health', 'teeth'], 'propane burns': ['hurt', 'shock'],
}
TOPS = sorted({*TOPS, *GUIDE_URGENT, *GUIDE_ORDINARY})

CASES = {
    'stop': QSTOP, 'fold': list(FOLD), 'match': [m[:2] for m in MATCH], 'rank': ENGLISH, 'topics': TOPICS,
    'rankOwn': RANK_OWN,
    'words': list(WORDS_BOTH) + ['怎么净化水', '水をきれいにする方法',
                                 '물 끓이기', 'น้ำ'],
    'tops': TOPS,
}


def run(mode):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / 'cases.json'
        p.write_text(json.dumps(CASES, ensure_ascii=False), encoding='utf-8')
        r = subprocess.run([NODE, str(HERE / 'topic_search_test.mjs'), str(WORDS), str(p), mode],
                           capture_output=True, text=True, encoding='utf-8', timeout=60)
    if r.returncode:
        raise AssertionError(r.stderr[-1500:])
    return json.loads(r.stdout)


def ok(entry):
    if 'error' in entry:
        raise AssertionError(entry['error'])
    return entry['ok']


@unittest.skipUnless(NODE, 'needs node on PATH')
class TopicSearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seg, cls.wk, cls.fb, cls.thr = run('segmenter'), run('webkit'), run('fallback'), run('throwing')
        cls.modes = (cls.seg, cls.wk, cls.fb, cls.thr)

    def words(self, r):
        return dict(zip(CASES['words'], (ok(e) for e in r['words'])))

    def test_modes(self):
        self.assertTrue(self.seg['segmenter'])
        self.assertTrue(self.wk['segmenter'])
        self.assertFalse(self.fb['segmenter'])
        self.assertFalse(self.thr['segmenter'])
        self.assertEqual(self.thr, self.fb)                       # a throwing Segmenter falls back cleanly

    def test_fold(self):
        for r in self.modes:
            self.assertEqual(dict(zip(FOLD, r['fold'])), FOLD)

    def test_turkish_i_order(self):
        # Shows why the order matters: removing marks from NFC "İ" finds none, and lower-casing it afterwards
        # leaves "i" + U+0307, which no longer matches "istanbul". The fold assertions check words.js itself.
        marks_first = ''.join(ch for ch in unicodedata.normalize('NFC', 'İ') if not unicodedata.combining(ch)).lower()
        self.assertEqual(marks_first, 'i̇')
        for r in self.modes:
            self.assertEqual(r['fold'][0], 'istanbul')

    def test_query_words(self):
        for r in self.modes:
            w = self.words(r)
            for q, expect in WORDS_BOTH.items():
                with self.subTest(q=q, segmenter=r['segmenter']):
                    self.assertEqual(w[q], expect)

    def test_scripts_without_spaces(self):
        for r in (self.seg, self.wk):
            w = self.words(r)
            zh = w['怎么净化水']
            self.assertEqual(''.join(zh), '怎么净化水')      # nothing dropped
            self.assertTrue(all(1 <= len(x) <= 2 for x in zh))                  # one- and two-character words count
            ja = w['水をきれいにする方法']
            self.assertIn('水', ja)
            self.assertIn('方法', ja)
            self.assertIn('물', w['물 끓이기'])              # Korean 물 (water), one syllable
            self.assertTrue(w['น้ำ'])                            # Thai น้ำ (water)
        for r in (self.fb, self.thr):                                           # no segmenter: the run stays whole
            self.assertEqual(self.words(r)['怎么净化水'], ['怎么净化水'])

    def test_match(self):
        for r in self.modes:
            self.assertEqual([ok(e) for e in r['match']], [m[2] for m in MATCH])

    def test_emergency_words_open_first_aid(self):
        for r in self.modes:
            top = dict(zip(TOPS, (ok(e) for e in r['tops'])))
            for q, first in [*EMERGENCY_FIRST.items(), *EMERGENCY_UNDISTURBED.items()]:
                with self.subTest(q=q, segmenter=r['segmenter']):
                    self.assertEqual(top[q][:1], [first])   # an empty result fails, not errors

    def test_rank_non_english_topic(self):
        for r in self.modes:
            self.assertEqual([ok(e) for e in r['rankOwn']], [[['own', None]]] * 3)

    def test_everyday_words_find_their_guide(self):
        for r in self.modes:
            top = dict(zip(TOPS, (ok(e) for e in r['tops'])))
            for q, first in EVERYDAY.items():
                with self.subTest(q=q, segmenter=r['segmenter']):
                    self.assertEqual(top[q][0] if top[q] else None, first)
            for q, choice in LISTED.items():
                with self.subTest(q=q, segmenter=r['segmenter']):
                    self.assertIn(choice, top[q])

    def test_english_ranks_as_before(self):
        for r in self.modes:
            for case in r['rank']:
                with self.subTest(q=case['q'], segmenter=r['segmenter']):
                    self.assertEqual(ok(case['now']), case['before'])
        self.assertGreater(sum(1 for c in self.seg['rank'] if c['before']), 30)   # the list does reach the guides

    def test_words_used_outside_the_us(self):
        for r in self.modes:
            top = dict(zip(TOPS, (ok(e) for e in r['tops'])))
            for q, us in SAME_AS.items():
                with self.subTest(q=q, us=us, segmenter=r['segmenter']):
                    self.assertTrue(top[us])                       # the US word does find a guide
                    self.assertEqual(top[q], top[us])
            for q, us in SAME_GUIDE.items():
                with self.subTest(q=q, us=us, segmenter=r['segmenter']):
                    self.assertTrue(top[q])
                    self.assertEqual(top[q][0][0], top[us][0][0])
            for q, first in [*FIRST.items(), *UNDISTURBED.items()]:
                with self.subTest(q=q, segmenter=r['segmenter']):
                    self.assertEqual(top[q][0], first)

    def test_urgent_choice_wins(self):
        for r in self.modes:
            top = dict(zip(TOPS, (ok(e) for e in r['tops'])))
            for q, first in URGENT.items():
                with self.subTest(q=q, segmenter=r['segmenter']):
                    self.assertEqual(top[q][0] if top[q] else None, first)

    def test_breathing_after_a_sting(self):
        for r in self.modes:
            top = dict(zip(TOPS, (ok(e) for e in r['tops'])))
            for q in NOT_STING:
                with self.subTest(q=q, segmenter=r['segmenter']):
                    self.assertTrue(top[q])
                    self.assertNotIn(['hurt', 'sting'], top[q])

    def test_urgent_guide_comes_first(self):
        for r in self.modes:
            top = dict(zip(TOPS, (ok(e) for e in r['tops'])))
            for q, (first, offered) in GUIDE_URGENT.items():
                with self.subTest(q=q, segmenter=r['segmenter']):
                    self.assertEqual(top[q][:1], [first])
                    if offered:
                        self.assertIn(offered, top[q])
                    self.assertLessEqual(len(top[q]), 3)
            for q, first in GUIDE_ORDINARY.items():
                with self.subTest(q=q, segmenter=r['segmenter']):
                    self.assertEqual(top[q][:1], [first])


if __name__ == '__main__':
    unittest.main()
