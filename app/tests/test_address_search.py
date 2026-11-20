"""Offline address lookup must preserve house numbers and geographic qualifiers."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from engine.address_search import find_addresses, is_address_query, normalize


class AddressSearchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.geo = Path(self.temp.name)
        (self.geo / 'addresses').mkdir()
        self.write_state('MI', [
            ('18001', 'W Nine Mile Road', 'Novi', 'MI', '48375', 42.45, -83.47),
            ('18002', 'W Nine Mile Road', 'Novi', 'MI', '48375', 42.46, -83.47),
            ('18001', 'Nine Mile Rd', 'Farmington', 'MI', '48335', 42.47, -83.40),
        ])
        self.write_state('CA', [
            ('18001', 'Nine Mile Road', 'Example', 'CA', '90001', 34.0, -118.0),
            ('23001', 'Maple Avenue', 'Kansas City', 'MO', '64105', 39.0997, -94.5786),
            ('21', 'W 9 ST', 'Example', 'CA', '90001', 34.01, -118.01),
            ('12', 'Oak Court', 'Example', 'CA', '90001', 34.02, -118.02),
            ('100', 'Main Street', 'Inglewood', 'CA', '90301', 33.96, -118.35),
            ('100', 'Main Street', 'Newport Beach', 'CA', '92661', 33.60, -117.90),
        ])

    def tearDown(self):
        self.temp.cleanup()

    def write_state(self, state, rows):
        db = sqlite3.connect(self.geo / 'addresses' / f'{state}.sqlite')
        try:
            db.execute('CREATE TABLE addr(num TEXT,street TEXT,norm TEXT,city TEXT,state TEXT,zip TEXT,lat REAL,lon REAL)')
            db.execute('CREATE INDEX addr_num_norm ON addr(num,norm)')
            db.executemany('INSERT INTO addr VALUES(?,?,?,?,?,?,?,?)',
                           [(num, street, normalize(street), city, st, z, lat, lon)
                            for num, street, city, st, z, lat, lon in rows])
            db.commit()
        finally:
            db.close()      # the `with` form commits but does not close, and Windows will not remove an open file

    def test_numeric_words_directions_and_qualifiers(self):
        for query in ('18001 9 mile rd Novi MI', '18001 Nine Mile Road Novi Michigan',
                      '18001 nine mile Novi 48375', '18001 W Nine Mile Road, Novi, MI 48375'):
            with self.subTest(query=query):
                result = find_addresses(query, self.geo)
                self.assertEqual(len(result), 1)
                self.assertEqual(result[0]['name'], '18001 W Nine Mile Road')
                self.assertEqual(result[0]['lat'], 42.45)
                self.assertEqual(result[0]['kind'], 'Street address')

    def test_unknown_number_does_not_return_nearby_house(self):
        self.assertEqual(find_addresses('18003 nine mile Novi MI', self.geo), [])

    def test_city_and_zip_do_not_silently_fall_back(self):
        self.assertEqual(find_addresses('18001 nine mile Wrongtown MI', self.geo), [])
        self.assertEqual(find_addresses('18001 nine mile MI 99999', self.geo), [])

    def test_zip_plus_four_uses_its_five_digit_zip(self):
        for query in ('18001 nine mile Novi MI 48375-1234', '18001 nine mile Novi MI 48375 1234'):
            with self.subTest(query=query):
                result = find_addresses(query, self.geo)
                self.assertEqual(len(result), 1)
                self.assertEqual(result[0]['name'], '18001 W Nine Mile Road')
        self.assertEqual(find_addresses('18001 nine mile Novi MI 99999-1234', self.geo), [])

    def test_state_uses_only_that_index(self):
        result = find_addresses('18001 nine mile CA', self.geo)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['detail'], 'Example, CA, 90001')

    def test_street_ending_that_is_also_a_state_code(self):
        # 'Ct' is Court before it is Connecticut, and 'NE' is northeast before it is Nebraska: neither state is installed here.
        result = find_addresses('12 Oak Ct', self.geo)
        self.assertEqual([r['name'] for r in result], ['12 Oak Court'])
        self.write_state('DC', [
            ('500', '4th Street NE', 'Washington', 'DC', '20002', 38.896, -77.000),
            ('1600', 'Pennsylvania Avenue NW', 'Washington', 'DC', '20500', 38.8977, -77.0365),
        ])
        for query in ('500 4th St NE', '500 4th St NE 20002', '500 4th St NE Washington DC'):
            with self.subTest(query=query):
                self.assertEqual([r['name'] for r in find_addresses(query, self.geo)], ['500 4th Street NE'])

    def test_installed_state_is_still_read_after_a_street_ending(self):
        self.write_state('CT', [('12', 'Oak Street', 'Hartford', 'CT', '06103', 41.76, -72.67)])
        self.assertEqual(find_addresses('12 Oak Ct', self.geo)[0]['detail'], 'Example, CA, 90001')      # the Court, as typed
        self.assertEqual(find_addresses('12 Oak St CT', self.geo)[0]['detail'], 'Hartford, CT, 06103')
        self.assertEqual(find_addresses('12 Oak Connecticut', self.geo)[0]['detail'], 'Hartford, CT, 06103')

    def test_town_named_like_a_state(self):
        self.write_state('DC', [('1600', 'Pennsylvania Avenue NW', 'Washington', 'DC', '20500', 38.8977, -77.0365)])
        for query in ('1600 Pennsylvania Ave NW Washington', '1600 Pennsylvania Ave NW Washington DC'):
            with self.subTest(query=query):
                self.assertEqual([r['detail'] for r in find_addresses(query, self.geo)], ['Washington, DC, 20500'])

    def test_state_that_is_not_installed_is_never_read_as_a_town(self):
        # Indiana, Nebraska and Kansas are not installed. 'IN' must not find Inglewood, 'NE' Newport Beach, or 'Kansas' Kansas City.
        for query in ('100 Main St IN', '100 Main St NE', '100 Main St Indiana', '100 Main St IN 90301', '23001 Maple Ave Kansas'):
            with self.subTest(query=query):
                self.assertEqual(find_addresses(query, self.geo), [])

    def test_ordinal_street(self):
        result = find_addresses('21 ninth st Example CA', self.geo)
        self.assertEqual(result[0]['name'], '21 W 9 ST')

    def test_plain_zip_remains_place_query(self):
        self.assertFalse(is_address_query('48375'))
        self.assertFalse(is_address_query('Novi MI'))
        self.assertTrue(is_address_query('18001 nine mile'))

    def test_missing_indexes_and_legacy_database(self):
        empty = self.geo / 'empty'
        self.assertEqual(find_addresses('23001 Maple Ave', empty), [])
        empty.mkdir()
        db = sqlite3.connect(empty / 'addresses.sqlite')
        try:
            db.execute('CREATE TABLE addr(num TEXT,street TEXT,norm TEXT,city TEXT,state TEXT,zip TEXT,lat REAL,lon REAL)')
            db.execute("INSERT INTO addr VALUES('23001','Maple Avenue','maple ave','Kansas City','MO','64105',39.0997,-94.5786)")
            db.commit()
        finally:
            db.close()      # as in write_state: the `with` form does not close, and Windows will not remove an open file
        self.assertEqual(find_addresses('23001 Maple Ave Kansas City MO', empty)[0]['lat'], 39.0997)

    def test_app_route_preserves_address_number(self):
        import server
        with patch.object(server, 'HERE', self.geo.parent), patch.object(server.address_search, 'find_addresses', return_value=[]) as lookup:
            self.assertEqual(server.places('18003 nine mile'), [])
            lookup.assert_called_once_with('18003 nine mile', self.geo.parent / 'derived' / 'geo', limit=8, near=None)


class QuebecAddressTests(unittest.TestCase):
    """Invented Quebec addresses (issue #169). Every street, number and postal code here is made up; H0H 0H0 is Canada
    Post's well-known placeholder. Cases marked expectedFailure describe wanted behaviour the US parser does not have yet:
    when a change makes one pass, remove its marker."""

    ROWS = [
        ('1250', 'rue des Érables', 'Saint-Exemple', 'QC', 'H0H0H0', 46.10, -73.10),
        ('88', 'boulevard de la Rivière', 'Saint-Exemple', 'QC', 'H0H0H0', 46.11, -73.11),
        ('45', 'rue Sainte-Thérèse', 'Saint-Exemple', 'QC', 'H0H0H0', 46.12, -73.12),
        ('7', 'rue Saint-Exemple', 'Exempleville', 'QC', 'H0H0H0', 46.13, -73.13),
        ('500', 'Exemple Street', 'Exempleville', 'QC', 'H0H0H0', 46.14, -73.14),
        ('15', 'rue du Cœur-Vaillant', 'Exempleville', 'QC', 'H0H0H0', 46.15, -73.15),
        ('300', 'rang du Lac-Vert', 'Exempleville', 'QC', 'H0H0H0', 46.16, -73.16),
        ('9', "chemin d'Exemple", 'Exempleville', 'QC', 'H0H0H0', 46.17, -73.17),
        ('31', 'rue François', 'Exempleville', 'QC', 'H0H0H0', 46.18, -73.18),
    ]

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.geo = Path(self.temp.name)
        (self.geo / 'addresses').mkdir()
        db = sqlite3.connect(self.geo / 'addresses' / 'QC.sqlite')
        try:
            db.execute('CREATE TABLE addr(num TEXT,street TEXT,norm TEXT,city TEXT,state TEXT,zip TEXT,lat REAL,lon REAL)')
            db.execute('CREATE INDEX addr_num_norm ON addr(num,norm)')
            db.executemany('INSERT INTO addr VALUES(?,?,?,?,?,?,?,?)',
                           [(num, street, normalize(street), city, st, z, lat, lon)
                            for num, street, city, st, z, lat, lon in self.ROWS])
            db.commit()
        finally:
            db.close()

    def tearDown(self):
        self.temp.cleanup()

    def assertFinds(self, query, name):
        result = find_addresses(query, self.geo)
        self.assertTrue(result, f'{query!r} found nothing')
        self.assertEqual(result[0]['name'], name)

    # Works today -----------------------------------------------------------------------------------------------------

    def test_same_accents_on_both_sides(self):
        # Works because the query and the index lose the accented letters the same way, not because accents are handled.
        self.assertFinds('1250 rue des Érables', '1250 rue des Érables')
        self.assertFinds('88 boulevard de la Rivière', '88 boulevard de la Rivière')

    def test_hyphen_dash_and_apostrophe_forms(self):
        for query in ('300 rang du Lac-Vert', '300 rang du Lac Vert', '300 rang du Lac\u2013Vert', '300 rang du Lac\u2010Vert'):
            with self.subTest(query=query):
                self.assertFinds(query, '300 rang du Lac-Vert')
        for query in ("9 chemin d'Exemple", '9 chemin d\u2019Exemple', '9 chemin d Exemple'):
            with self.subTest(query=query):
                self.assertFinds(query, "9 chemin d'Exemple")

    def test_saint_before_a_name(self):
        for query in ('7 rue St-Exemple', '7 rue Saint-Exemple', '7 rue st exemple'):
            with self.subTest(query=query):
                self.assertFinds(query, '7 rue Saint-Exemple')

    def test_street_after_a_name(self):
        for query in ('500 Exemple Street', '500 Exemple St.', '500 Exemple St'):
            with self.subTest(query=query):
                self.assertFinds(query, '500 Exemple Street')

    def test_saint_and_street_do_not_cross(self):
        # "St" before a name is Saint, after it Street: neither form finds the other street.
        self.assertEqual(find_addresses('500 rue St-Exemple', self.geo), [])
        self.assertEqual(find_addresses('7 Exemple St', self.geo), [])

    # Wanted, not supported yet -------------------------------------------------------------------------------------

    @unittest.expectedFailure
    def test_query_without_accents_finds_accented_street(self):
        # Today "Érables" is stored as "rables", so a query typed without accents ("erables") misses it.
        self.assertFinds('1250 rue des Erables', '1250 rue des Érables')

    @unittest.expectedFailure
    def test_cedilla_folds_to_c(self):
        self.assertFinds('31 rue Francois', '31 rue François')

    @unittest.expectedFailure
    def test_ligature_oe_folds_to_oe(self):
        # NFKD does not decompose œ, so it needs its own rule.
        self.assertFinds('15 rue du Coeur-Vaillant', '15 rue du Cœur-Vaillant')

    @unittest.expectedFailure
    def test_sainte_and_ste_are_the_same(self):
        self.assertFinds('45 rue Ste-Thérèse', '45 rue Sainte-Thérèse')

    @unittest.expectedFailure
    def test_canadian_postal_code_with_or_without_space(self):
        for query in ('1250 rue des Érables H0H 0H0', '1250 rue des Érables h0h0h0'):
            with self.subTest(query=query):
                self.assertFinds(query, '1250 rue des Érables')

    @unittest.expectedFailure
    def test_unit_before_number(self):
        # In Canada "3-1250" is unit 3 at house number 1250.
        self.assertFinds('3-1250 rue des Érables', '1250 rue des Érables')


class OntarioAddressTests(unittest.TestCase):
    """Invented Ontario addresses, as written by people in Ontario.

    Every street name and house number is made up, and so is the postal code. Exampleton is an invented town; Sault
    Ste. Marie and St. Catharines are real cities, used only for how their names are written, with invented streets.

    The index follows the layout proposed in #143: its own `CA-ON.sqlite`, `CA-ON` as the region and postal codes
    stored without the space. Main has no Ontario index yet, so the format is a guess; the cases are the point. A US
    index with the same street is installed too, so a case that finds the Ohio row instead is caught.

    Cases marked `expectedFailure` are wanted but fail today by finding nothing, not by an error. Remove the marker
    when a change makes one pass.
    """

    POSTAL = 'M0M 0M0'      # made up

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.geo = Path(self.temp.name)
        (self.geo / 'addresses').mkdir()
        self.write_index('CA-ON', [
            ('120', 'Exemplar Street East', 'Exampleton', 'CA-ON', self.POSTAL.replace(' ', ''), 44.10, -79.10),
            ('4410', 'Highway 7', 'Exampleton', 'CA-ON', '', 44.11, -79.11),
            ('5521', '10th Line', 'Exampleton', 'CA-ON', '', 44.12, -79.12),
            ('3100', 'Concession Road 6', 'Exampleton', 'CA-ON', '', 44.13, -79.13),
            ('2210', 'County Road 2', 'Exampleton', 'CA-ON', '', 44.14, -79.14),
            ('45', 'Exemplar Road', 'Sault Ste. Marie', 'CA-ON', '', 46.50, -84.30),
            ('46', 'Exemplar Road', 'St. Catharines', 'CA-ON', '', 43.15, -79.24),
        ])
        self.write_index('OH', [
            ('120', 'Exemplar Street East', 'Exampleton', 'OH', '44000', 40.00, -82.00),
        ])

    def tearDown(self):
        self.temp.cleanup()

    def write_index(self, name, rows):
        db = sqlite3.connect(self.geo / 'addresses' / f'{name}.sqlite')
        try:
            db.execute('CREATE TABLE addr(num TEXT,street TEXT,norm TEXT,city TEXT,state TEXT,zip TEXT,lat REAL,lon REAL)')
            db.execute('CREATE INDEX addr_num_norm ON addr(num,norm)')
            db.executemany('INSERT INTO addr VALUES(?,?,?,?,?,?,?,?)',
                           [(num, street, normalize(street), city, region, code, lat, lon)
                            for num, street, city, region, code, lat, lon in rows])
            db.commit()
        finally:
            db.close()      # as in AddressSearchTests.write_state

    def assertFinds(self, query, name, lat):
        result = find_addresses(query, self.geo)
        self.assertTrue(result, f'{query!r} found nothing')
        self.assertEqual(result[0]['name'], name)
        self.assertEqual(result[0]['lat'], lat)

    def assertOntarioOnly(self, query):
        result = find_addresses(query, self.geo)
        self.assertEqual([r['lat'] for r in result], [44.10], f'{query!r}: {result}')

    # Pass today: regression guards.

    def test_direction_after_the_street(self):
        """Ontario writes the direction after the street ("King St E"), not before it as in "W Nine Mile Road"."""
        for query in ('120 Exemplar Street East', '120 Exemplar St E', '120 exemplar st. e.', '120 Exemplar St E Exampleton'):
            with self.subTest(query=query):
                self.assertFinds(query, '120 Exemplar Street East', 44.10)

    def test_highway_and_county_road(self):
        for query in ('4410 Highway 7', '4410 Hwy 7', '4410 Hwy. 7'):
            with self.subTest(query=query):
                self.assertFinds(query, '4410 Highway 7', 44.11)
        for query in ('2210 County Road 2', '2210 County Rd 2'):
            with self.subTest(query=query):
                self.assertFinds(query, '2210 County Road 2', 44.14)

    def test_numbered_line(self):
        """Rural townships number their roads: "10th Line", also written "Tenth Line"."""
        for query in ('5521 10th Line', '5521 Tenth Line'):
            with self.subTest(query=query):
                self.assertFinds(query, '5521 10th Line', 44.12)

    def test_concession_road(self):
        for query in ('3100 Concession Road 6', '3100 Concession Rd 6'):
            with self.subTest(query=query):
                self.assertFinds(query, '3100 Concession Road 6', 44.13)

    # Wanted: fail today.

    @unittest.expectedFailure
    def test_province_abbreviation(self):
        """"ON" is not read as a province, so it stays in the city: the city "exampleton on" matches nothing."""
        self.assertOntarioOnly('120 Exemplar St E Exampleton ON')

    @unittest.expectedFailure
    def test_province_name(self):
        self.assertOntarioOnly('120 Exemplar St E Exampleton Ontario')

    @unittest.expectedFailure
    def test_postal_code_with_space(self):
        """A postal code is letter-digit-letter digit-letter-digit; only a five-digit ZIP is read as a code today."""
        self.assertOntarioOnly(f'120 Exemplar St E, Exampleton, ON {self.POSTAL}')

    @unittest.expectedFailure
    def test_postal_code_without_space_or_capitals(self):
        for code in (self.POSTAL.replace(' ', ''), self.POSTAL.lower()):
            with self.subTest(code=code):
                self.assertOntarioOnly(f'120 Exemplar St E {code}')

    @unittest.expectedFailure
    def test_unit_before_the_house_number(self):
        """Canada writes unit 4 at number 120 as "4-120"; today "4-120" is read as the house number."""
        self.assertFinds('4-120 Exemplar St E', '120 Exemplar Street East', 44.10)

    @unittest.expectedFailure
    def test_city_with_ste(self):
        """The query's city is normalized ("ste marie"), the stored one is not ("ste. marie"). #196 compares both
        normalized."""
        for query in ('45 Exemplar Rd Sault Ste Marie', '45 Exemplar Rd Sault Ste. Marie'):
            with self.subTest(query=query):
                self.assertFinds(query, '45 Exemplar Road', 46.50)

    @unittest.expectedFailure
    def test_city_with_st(self):
        for query in ('46 Exemplar Rd St Catharines', '46 Exemplar Rd St. Catharines', '46 Exemplar Rd Saint Catharines'):
            with self.subTest(query=query):
                self.assertFinds(query, '46 Exemplar Road', 43.15)


if __name__ == '__main__':
    unittest.main()
