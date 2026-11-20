"""Chat reads a library page's tables row by row (engine/page_tables.py, assistant.page_body). The page text comes from
`pdftotext -layout`; squashing every run of spaces, as Chat did, ran some tables' rows together (Hesperian's bleach table
read "20 liters For a 200 liter 5 teaspoons", and a small model gave ten times the dose). Checks that each label keeps its
own value once a table is rebuilt, and that pages without such a table, and ordinary prose, read exactly as before.

Needs no library. Never packaged."""
import os, re, sys, unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine import page_tables as T   # noqa: E402


def old(text, cap):
    """Chat's reading before: every run of spaces squashed to one."""
    return re.sub(r'[ \t]{2,}', ' ', text).strip()[:cap]


# Two printings of Hesperian's bleach table, as `pdftotext -layout` gives them. In the first ("Water and Sanitation: Keys
# to Staying Healthy" p. 23) a column of prose runs beside it; in the second ("Protecting Community Water" p. 36) each
# amount sits between the two lines of its label.
BLEACH_BESIDE_PROSE = '\n'.join([
    '    If the water is cloudy or                     Water                 Add Bleach (5%)',
    'has a lot of solid matter in it,',
    '                                       For 1 liter or',
    'filter the water before adding                                                 2 drops',
    '                                         1 quart',
    'chlorine.',
    '   After adding the right              For 1 gallon or',
    'amount of chlorine, stir well              4 liters                            8 drops',
    'and wait at least 30 minutes',
    'before drinking. If the water',
    '                                       For 5 gallons or                     1/2 teaspoon',
    'does not smell or taste just               20 liters',
    'slightly of chlorine after',
    'adding the amount listed, add',
    'the same amount again. Stir            For a 200 liter',
    '                                                                            5 teaspoons',
    '                                           barrel',
    'and wait before drinking.'])
BLEACH_CENTRED = '\n'.join([
    'water is cloudy, use twice as much bleach as what is shown in the chart below.', '',
    '                            Water                   5% Chlorine Bleach', '',
    '                For 1 liter or',
    '                1 quart                                        2 drops', '', '',
    '                For 1 gallon or',
    '                4 liters                                       8 drops', '', '',
    '                For 5 gallons or',
    '                                                               1/2 teaspoon',
    '                20 liters', '', '', '',
    '                For a 200 liter',
    '                                                               5 teaspoons',
    '                barrel', '',
    '   Add these amounts of bleach to filtered or settled water and wait at least 30 minutes'])
BLEACH = {'For 1 liter or 1 quart': '2 drops', 'For 1 gallon or 4 liters': '8 drops',
          'For 5 gallons or 20 liters': '1/2 teaspoon', 'For a 200 liter barrel': '5 teaspoons'}

# A dose table whose cells wrap in several columns (Hesperian, "Where There Is No Dentist"): rows can't be told apart
# by the nearest amount, so it is kept as printed.
WRAPPED = '\n'.join([
    '     Name of medicine              Age                   Dose                  How to take',
    '         Metronidazole          1 to 2 years      50 mg, 3 times a day       By mouth for 5 to 7',
    '                                                                                   days.',
    '                                3 to 6 years      100 mg, 2 times a day',
    '                                                                            Do not give to people',
    '                                7 to 9 years      100 mg, 3 times a day       during the first 3',
    '                                                                            months of pregnancy.',
    '                               10 to 17 years     250 mg, 3 times a day', '',
    '                            18 years and older    500 mg, 3 times a day', '',
    'Once the area is clean and the infection is controlled, take out any teeth that'])
WRAPPED_DOSES = {'1 to 2 years': '50 mg, 3 times a day', '3 to 6 years': '100 mg, 2 times a day',
                 '7 to 9 years': '100 mg, 3 times a day', '10 to 17 years': '250 mg, 3 times a day',
                 '18 years and older': '500 mg, 3 times a day'}

# A table laid across (MSF, nebulised epinephrine by weight): each weight's doses are down its column.
ACROSS = '\n'.join([
    '      Weight          4 kg        5 kg             6 kg       7 kg        8 kg         9 kg',
    '      Dosage in',
    '                      2 mg        2.5 mg           3 mg       3.5 mg      4 mg         4.5 mg',
    '      mg',
    '      Epinephrine',
    '      (1 mg/mL        2 mL        2.5 mL           3 mL       3.5 mL      4 mL         4.5 mL',
    '      ampoule)',
    '      0.9% NaCl',
    '      to add',
    '                      2 mL        2 mL             1 mL       1 mL               -            -'])

PROSE = '\n'.join([
    'Boiling is the surest way to kill germs in water.   Bring the water to a rolling boil',
    'for 1 minute.  At altitudes above 2,000 metres, boil for 3 minutes.',
    '',
    '   Let it cool,   then store it covered in a clean container.   Use 2 drops of bleach',
    'per litre only if you cannot boil it.',
    '        Wash your hands before touching stored water.'])
# Each label entirely above its amount (from review, invented): the nearest line to "1 kg" is "Second crate".
CRATES = '\n'.join([
    '    Crate                     Quantity',
    '    First crate',
    '    packed',
    '                                      1 kg',
    '    Second crate',
    '    packed',
    '                                      2 kg',
    '    Third crate',
    '    packed',
    '                                      3 kg'])
# Columns without a unit (a timetable), side-by-side prose columns, a list of numbers: no table to rebuild.
NO_AMOUNTS = '\n'.join([
    '   Day        Morning        Evening',
    '   Monday     6              18',
    '   Tuesday    7              19',
    '   Wednesday  6              18',
    '',
    'Signs of dehydration:              What to do:',
    '  - dry mouth                        - give small sips often',
    '  - little or dark urine             - keep giving breast milk',
    '  - sunken eyes                      - go for help if it gets worse'])


def rows(text):
    """The rebuilt tables of a page as the model reads it: {label: value}."""
    lines = text.split('\n')
    out = {}
    for i, l in enumerate(lines):
        if l == 'Table (one row per line, columns split by |):':
            for row in lines[i + 2:]:   # the line after the marker is the header
                if ' | ' not in row:
                    break
                label, value = row.split(' | ')
                out[label] = value
    return out


class LabelsKeepTheirValues(unittest.TestCase):
    def test_bleach_rows(self):
        """Squashed, "20 liters" sat next to "5 teaspoons". Rebuilt, each quantity of water has its own amount, and each
        amount appears once, in its row."""
        self.assertIn('20 liters\nslightly of chlorine after\nadding the amount listed, add\n'
                      'the same amount again. Stir For a 200 liter\n 5 teaspoons', old(BLEACH_BESIDE_PROSE, 9999))
        for page, head in ((BLEACH_BESIDE_PROSE, 'Water | Add Bleach (5%)'), (BLEACH_CENTRED, 'Water | 5% Chlorine Bleach')):
            text = T.for_model(page)
            self.assertEqual(rows(text), BLEACH, text)
            self.assertIn('Table (one row per line, columns split by |):\n' + head + '\n', text)
            for amount in ('2 drops', '8 drops', '1/2 teaspoon', '5 teaspoons', '20 liters', '200 liter'):
                self.assertEqual(text.count(amount), 1, amount)

    def test_prose_beside_a_table_stays_whole(self):
        text = T.for_model(BLEACH_BESIDE_PROSE)
        self.assertIn('If the water is cloudy or\nhas a lot of solid matter in it,\nfilter the water before adding\n'
                      'chlorine.\nAfter adding the right\namount of chlorine, stir well\nand wait at least 30 minutes', text)
        self.assertIn('before drinking. If the water\ndoes not smell or taste just\nslightly of chlorine after\n'
                      'adding the amount listed, add\nthe same amount again. Stir\nTable (', text)
        self.assertTrue(text.endswith('\n\nand wait before drinking.'), text)

    def test_wrapped_table_kept_as_printed(self):
        """Rows that can't be told apart safely keep their printed columns (blank columns dropped), so each age stays on
        the line of its dose, and the dose column still lines up."""
        text = T.for_model(WRAPPED)
        self.assertIn('Table as printed', text)
        self.assertEqual(rows(text), {})
        lines = text.split('\n')
        for age, dose in WRAPPED_DOSES.items():
            [line] = [l for l in lines if re.search(r'(?<!\d)' + dose, l)]
            self.assertIn(age, line)
        at = {m.start() for l in lines for m in re.finditer(r'(?<!\d)\d+ mg, \d times a day', l)}
        self.assertEqual(len(at), 1, text)   # the dose column still lines up
        self.assertLess(max(map(len, lines)), max(map(len, WRAPPED.split('\n'))))
        self.assertTrue(text.rstrip().endswith('take out any teeth that'))

    def test_labels_above_their_amounts_not_paired_one_row_off(self):
        """When each label sits wholly above its amount, the nearest line to an amount is the next row's label. Such a
        table is either paired right or not called sure, and then kept as printed, where each label stays over its own
        amount."""
        [t] = T.tables(CRATES)
        right = {'First crate packed': '1 kg', 'Second crate packed': '2 kg', 'Third crate packed': '3 kg'}
        text = T.for_model(CRATES)
        if t['sure']:
            self.assertEqual(rows(text), right, text)
        else:
            self.assertEqual(rows(text), {})
            self.assertIn('Table as printed', text)
            lines = [l.strip() for l in text.split('\n')]
            for label, amount in (('First crate', '1 kg'), ('Second crate', '2 kg'), ('Third crate', '3 kg')):
                at = lines.index(label)
                self.assertEqual(lines[at + 1:at + 3], ['packed', amount], text)
        self.assertNotRegex(text, r'Second crate[^\n]*\| 1 kg|Third crate[^\n]*\| 2 kg')   # never one row off

    def test_table_laid_across_read_down_each_column(self):
        down = T._down(T._segments(ACROSS.split('\n')))
        for col, cells in ((1, '4 kg, 2 mg, 2 mL, 2 mL'), (3, '6 kg, 3 mg, 3 mL, 1 mL'), (4, '7 kg, 3.5 mg, 3.5 mL, 1 mL'),
                           (6, '9 kg, 4.5 mg, 4.5 mL, -')):
            self.assertIn(f'Column {col}: {cells}', down)


class PagesWithoutTablesUnchanged(unittest.TestCase):
    def assertUnchanged(self, text):
        self.assertEqual(T.for_model(text), re.sub(r'[ \t]{2,}', ' ', text))
        for cap in (3200, 3500, 4000, 40, 1):
            self.assertEqual(T.page_text(text, cap), old(text, cap), cap)

    def test_prose(self):
        self.assertUnchanged(PROSE)

    def test_columns_without_amounts(self):
        self.assertUnchanged(NO_AMOUNTS)

    def test_empty_and_blank(self):
        for text in ('', '\n', '   \n\f\n  ', 'one line'):
            self.assertUnchanged(text)

    def test_long_page_cut_where_it_was(self):
        """A page longer than the cap is cut at the same character as before, not at a line end."""
        self.assertUnchanged((PROSE + '\n') * 60)

    def test_cap_on_a_table_page(self):
        """With a table the cap counts characters as the old squashed text did: the spaces kept in a printed table
        count as one."""
        page = 'word ' * 900 + '\n' + BLEACH_CENTRED
        self.assertLessEqual(len(re.sub(r'[ \t]{2,}', ' ', T.page_text(page, 3200))), 3200)
        self.assertEqual(T.clip('a' + ' ' * 50 + 'b\n' + 'c' * 10, 4), 'a' + ' ' * 50 + 'b')


class ChatReadsThroughPageBody(unittest.TestCase):
    def setUp(self):
        self.fresh = [n for n in ('assistant', 'retrieval') if n not in sys.modules]

    def tearDown(self):
        for n in self.fresh:
            sys.modules.pop(n, None)

    def test_read_pages_and_switch(self):
        """read_pages (and "ask about this page" and the first search's pages, which call the same page_body) gives the
        table by row; LASTBOOK_AI_TABLES=0 gives the old squashed text; a page without a table is as before."""
        import assistant
        rec = {'id': 'hes', 'kind': 'pdf', 'notes': ''}
        S = mock.Mock(catalog=lambda: {'by_id': {'hes': rec}}, page_texts=lambda r: [PROSE, BLEACH_CENTRED],
                      public=lambda r: {'title': 'Protecting Community Water', 'publisher': 'Hesperian', 'year': '2011',
                                        'trust': 'reviewed', 'pages': 2})
        sess = assistant.Session()
        read = lambda p: assistant.run_tool('read_pages', {'doc_id': 'hes', 'pages': [p]}, sess, [])[0]
        with mock.patch.object(assistant, 'S', S, create=True), mock.patch.dict(os.environ, {'LASTBOOK_AI_TABLES': ''}):
            self.assertIn('\nFor 5 gallons or 20 liters | 1/2 teaspoon\n', read(2))
            self.assertIn(old(PROSE, 3500), read(1))
            self.assertEqual(assistant.page_body(PROSE, 3500), old(PROSE, 3500))
            os.environ['LASTBOOK_AI_TABLES'] = '0'
            out = read(2)
            self.assertNotIn('Table (', out)
            self.assertIn(old(BLEACH_CENTRED, 3500), out)


if __name__ == '__main__':
    unittest.main()
