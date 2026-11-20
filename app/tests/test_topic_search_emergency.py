#!/usr/bin/env python3
"""Topic search regression questions for #154: an injury question that mentions a how-to phrase.

  python3 -B -m unittest app.tests.test_topic_search_emergency [-v]      # the checks
  python3 -B app/tests/test_topic_search_emergency.py                    # the scored report

Issue #154 reports that a question naming an injury can lose its first-aid guide when the same question also
holds a how-to phrase ("make a fire", "treat water"). This module keeps the questions, the first result each
one should give, a scorer and the non-emergency counterexamples, so a change to the phrase handling in
`server.PHRASES` can be measured instead of argued about.

This is a test only: no search code is touched. The questions run through `web/words.js` `rankTopics`, which is
the function the app calls (web/app.js `topicMatches`), so no library or data folder is needed. The document
search in `server.find` and `assistant._fts` needs the packs and is not covered here; #154's own table was
measured on the Medium pack. That gap is stated in the pull request rather than hidden.

Every situation is invented. Needs Node on PATH, as test_topic_search does; never packaged.
"""
import json, re, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
NODE = shutil.which('node')
WORDS = ROOT / 'web' / 'words.js'
TOPICS = [json.loads(p.read_text(encoding='utf-8')) for p in sorted((ROOT / 'content' / 'topics').glob('*.json'))]

# The stop words app.js passes in, read from app.js so this benchmark follows it rather than copying it.
QSTOP = re.search(r"const QSTOP = new Set\('([^']*)'\.split", (ROOT / 'web' / 'app.js').read_text(encoding='utf-8')).group(1).split(' ')

# upstream/main when these numbers were measured. Re-measure BASE_FIRST on a new main and record the new one.
BASELINE = '1d847d0 + #44'   # 9542e80 before; #44's burn hints moved the two burn rows to the burn choice

# ----------------------------------------------------------------------------------------------------------
# The measure. #154 counts "the top 8 hits whose title or excerpt has a word a useful page would have". At
# guide level the same idea is: does the guide that describes the situation lead, and is its matching choice
# picked? A question scores 1.0 when both are right, 0.5 when the right guide leads with another choice, and
# 0.0 when another guide leads. "No question gets worse" is then a number, not an opinion.
#
#   (question, the first result the guides say should lead, why, in the guides' own words)
#
# A choice of None means the guide's leading choice may be any of them: the guide is what matters.
EMERGENCY = [
    ('treat water in the lungs after drowning', ('hurt', 'breathing'),
     'drowning: "Not breathing, unconscious or choking" lists drowning in its hint; #154 reports 5/8 become 0/8'),
    ('someone fell in the rainwater pool and is not breathing', ('hurt', 'breathing'),
     'not breathing: the same choice, which #167 makes urgent; the pool words must not outvote it'),
    ('my son nearly drowned in the rainwater pool', ('hurt', 'breathing'),
     'drowning; #154 lists this as weak before any phrase is involved (2 of 8)'),
    ('i burnt my fingers lighting the campfire', ('hurt', 'burn'),
     'a burn: "Burn or scald" is the choice for fire, hot water and cooking oil'),
    ('burned my hand trying to light a fire', ('hurt', 'burn'),
     'a burn plus the how-to phrase "light a fire" from #128; #154 measures 4 of 8 before, 2 of 8 with it'),
    ('my clothes caught fire while starting the fire', ('hurt', 'burn'),
     'clothing on fire: #154 measures 2 of 8, the worst row in its table'),
    ('i burned my hand on the camp stove', ('hurt', 'burn'),
     'a burn from a stove; #154 lists this weak (3 of 8) before any phrase is involved'),
    ('my child swallowed lamp oil', ('hurt', 'poison'),
     '"Poisoning: swallowed a chemical, medicine or pesticide" names fuel and a child getting into something'),
    ('carbon monoxide from making a fire in the tent', ('shelter', 'co'),
     '"Using a generator, heater, grill or stove" names headache or dizziness indoors, and the shelter guide '
     'lists carbon monoxide and CO in its keywords'),
]

# Questions that must not move. These are the words #167 deliberately left out of `urgent`, because they also
# describe a non-emergency, plus ordinary how-to searches that should keep finding their own guides.
COUNTER = [
    ('not responding to antibiotics', ('health', 'medicine'), 'a treatment that is not working, not a person'),
    ('the pump is not responding', ('hurt', 'breathing'), 'equipment, not a person; breathing is a keyword match'),
    ('choking on smoke', ('disaster', 'smoke'), 'smoke in the air, not a blocked airway'),
    ('allergic reaction choking', ('hurt', 'allergy'), 'names the cause; the allergy choice is the right one'),
    ('how do i light a campfire', ('power', None), 'a how-to question; it must keep finding its own guide'),
    ('how do i start a fire', ('disaster', None), 'a how-to question; the guide may lead with any choice'),
    ('boil water', ('water', 'unsafe'), 'making water safe, no injury named'),
    ('make a fire escape plan for my family', ('disaster', None), 'a plan, not an injury'),
    ('what could make a fire spread faster', ('disaster', None), 'a question about fire behaviour'),
    ('trouble breathing', ('hurt', 'allergy'), 'a severe allergy, as #167 says ("trouble breathing" is not urgent)'),
    ('someone fainted', ('hurt', 'breathing'), 'fainting is the breathing choice, as server.PHRASES has it'),
    ('food went bad', ('food', None), 'no injury; the food guide may lead with any choice'),
]

# The first result on main (BASELINE) for every question above, measured rather than guessed with the
# command in this file's docstring. Where this differs from EMERGENCY, that difference is #154: the gap this
# fixture exists to make visible.
BASE_FIRST = {
    'treat water in the lungs after drowning': ['water', 'keepclean'],
    'someone fell in the rainwater pool and is not breathing': ['hurt', 'breathing'],
    'my son nearly drowned in the rainwater pool': ['water', 'outside'],
    'i burnt my fingers lighting the campfire': ['hurt', 'burn'],             # ['hurt', 'heatcold'] on 9542e80
    'burned my hand trying to light a fire': ['hurt', 'burn'],                # ['disaster', 'earthquake-after'] on 9542e80
    'my clothes caught fire while starting the fire': ['disaster', 'earthquake-after'],
    'i burned my hand on the camp stove': ['food', 'cook'],
    'my child swallowed lamp oil': ['hurt', 'poison'],
    'carbon monoxide from making a fire in the tent': ['shelter', 'damaged'],
    'not responding to antibiotics': ['health', 'medicine'],
    'the pump is not responding': ['hurt', 'breathing'],
    'choking on smoke': ['disaster', 'smoke'],
    'allergic reaction choking': ['hurt', 'allergy'],
    'how do i light a campfire': ['power', 'first-hours'],
    'how do i start a fire': ['disaster', 'earthquake-after'],
    'boil water': ['water', 'unsafe'],
    'make a fire escape plan for my family': ['disaster', 'earthquake-after'],
    'what could make a fire spread faster': ['disaster', 'earthquake-after'],
    'trouble breathing': ['hurt', 'allergy'],
    'someone fainted': ['hurt', 'breathing'],
    'food went bad': ['food', 'outage'],
}

# The emergency questions main does not yet answer the way the guides describe, and the score they get today.
# A fix for #154 should shrink this to nothing without touching BASE_FIRST for COUNTER. When this changes, the
# PR changes this table on purpose, which is the point: the score is reviewed, not assumed.
KNOWN_GAPS = {
    'treat water in the lungs after drowning': 0.0,
    'my son nearly drowned in the rainwater pool': 0.0,
    'my clothes caught fire while starting the fire': 0.0,
    'i burned my hand on the camp stove': 0.0,
    'carbon monoxide from making a fire in the tent': 0.5,
}

CASES = {
    'stop': QSTOP,
    'topics': TOPICS,
    'questions': [q for q, _, _ in EMERGENCY] + [q for q, _, _ in COUNTER],
}


def run():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / 'cases.json'
        p.write_text(json.dumps(CASES, ensure_ascii=False), encoding='utf-8')
        r = subprocess.run([NODE, str(HERE / 'topic_search_emergency.mjs'), str(WORDS), str(p)],
                           capture_output=True, text=True, encoding='utf-8', timeout=60)
    if r.returncode:
        raise AssertionError(r.stderr[-1500:])
    return json.loads(r.stdout)


def first(result):
    """The guide and choice that lead, as [guide, choice], or None when no guide matched."""
    top = result[0] if result else None
    return [top[0], top[1]] if top else None


def score(want, got):
    """1.0 for the guide and the choice, 0.5 for the guide with another choice, 0.0 otherwise."""
    if not got:
        return 0.0
    if want[0] != got[0]:
        return 0.0
    return 1.0 if want[1] is None or want[1] == got[1] else 0.5


@unittest.skipUnless(NODE, 'needs node on PATH')
class TopicSearchEmergency(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.got = dict(zip(CASES['questions'], (first(r) for r in run())))

    def test_reproduces_the_baseline(self):
        # If this fails, the search changed: re-measure BASE_FIRST and KNOWN_GAPS and record the new commit,
        # rather than adjusting the expectations to whatever the code now does.
        for q, want in BASE_FIRST.items():
            with self.subTest(q=q, baseline=BASELINE):
                self.assertEqual(self.got[q], want)

    def test_scorer(self):
        self.assertEqual(score(('hurt', 'burn'), ['hurt', 'burn']), 1.0)
        self.assertEqual(score(('hurt', 'burn'), ['hurt', 'heatcold']), 0.5)
        self.assertEqual(score(('hurt', 'burn'), ['food', 'cook']), 0.0)
        self.assertEqual(score(('disaster', None), ['disaster', 'flood']), 1.0)
        self.assertEqual(score(('hurt', 'burn'), None), 0.0)

    def test_known_gaps_only_shrink(self):
        # Recorded, not asserted as a failure: this is a benchmark, and a test that fails on main would make
        # every other PR red. A change to the phrase handling may close a gap, never open one.
        gaps = {q: score(want, self.got[q]) for q, want, _ in EMERGENCY if score(want, self.got[q]) < 1.0}
        self.assertLessEqual(set(gaps), set(KNOWN_GAPS))
        for q, got in gaps.items():
            with self.subTest(q=q):
                self.assertGreaterEqual(got, KNOWN_GAPS[q], 'worse than recorded on ' + BASELINE)

    def test_no_emergency_question_is_worse_than_baseline(self):
        for q, want, why in EMERGENCY:
            with self.subTest(q=q, why=why):
                self.assertGreaterEqual(score(want, self.got[q]), score(want, BASE_FIRST[q]))

    def test_counterexamples_do_not_move(self):
        for q, _, why in COUNTER:
            with self.subTest(q=q, why=why):
                self.assertEqual(self.got[q], BASE_FIRST[q], f'{q!r} moved: {self.got[q]}')


def report():
    got = dict(zip(CASES['questions'], (first(r) for r in run())))
    print(f'baseline: {BASELINE}  (score 1.0 = guides agree, 0.5 = right guide, 0.0 = another guide)')
    print('\nEmergency questions')
    for q, want, why in EMERGENCY:
        print(f'  {score(want, got[q]):.1f}  {q!r}\n       want {want}  got {got[q]}\n       {why}')
    print('\nCounterexamples (must not move)')
    for q, _, why in COUNTER:
        mark = 'ok ' if got[q] == BASE_FIRST[q] else 'MOVED'
        print(f'  {mark}  {q!r}  {got[q]}  ({why})')
    total = sum(score(w, got[q]) for q, w, _ in EMERGENCY)
    print(f'\nemergency score: {total:.1f} of {len(EMERGENCY)}')


if __name__ == '__main__':
    if NODE and len(sys.argv) == 1:
        report()
    else:
        unittest.main()
