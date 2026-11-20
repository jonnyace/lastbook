# Detailed maps for Austria: a proposal

This is a proposal for discussion, not a decision. It answers, for Austria, the questions [MAPS.md](MAPS.md) asks before
coverage can go beyond the United States: which open source replaces each federal list, under what licence, what a
"state" is there, and how addresses are written. It follows the shape of [REGIONS.md](REGIONS.md) and
[REGIONS-DE.md](REGIONS-DE.md) and is meant to feed the same design discussion (issues #23, #25 and #31). Pull
request #84 already proposes a whole-country Austria map, `eu-at`; how this proposal fits with it is under "Relation to
pull request #84". The machine-readable version is [regions-at-proposed.json](regions-at-proposed.json).

Nothing here changes the app, the engine or a build. No code reads the JSON, and nothing here ships: builds package
`web/` and `content/` only.

**How things were checked.** Research was done on 17 November 2026, with an AI assistant reading the publishers' own
catalogues and pages. Most official records were read through the catalogue APIs of the surveying agency
(`data.bev.gv.at`) and of Austria's INSPIRE geoportal, which return the same record the web page shows; data.gv.at pages
need JavaScript and were read in a browser. Each source carries one of three marks:

- **opened**: the dataset record, licence statement or page itself was read;
- **search only**: the fact was seen in a search result from the publisher's own site, but the page itself was not
  opened;
- **not checked**: the page could not be reached or read, or the fact was not looked for; the row says what is missing.

## Why Austria is a useful next case

Germany's question was "which of 16 sources, under which of four licences" ([REGIONS-DE.md](REGIONS-DE.md)). Austria's
is simpler. The federal surveying agency (BEV, Bundesamt für Eich- und Vermessungswesen) publishes nationwide
boundaries, a lidar elevation model, building outlines with heights, place names and the national address register as
open data, and every one of those records names CC BY 4.0. The agriculture agency (AMA), the water ministry (BMLUK) and
the interior ministry (BMI) publish the crop, river and police layers under the same licence. Overture already carries
Austria's address register.

So Austria needs no state-by-state table for its primary terrain, river, crop, building, place, address and police
sources: each is nationwide and names CC BY 4.0. The dam and hospital lists remain cross-checks with unverified terms,
as noted below. Code work is still needed, mostly in address search (see "How addresses are written").

## What a region is

Austria has nine states (Bundesländer). Vienna is both a city and a state, and lies wholly inside Lower Austria. The
proposal is one region per state, nine in all, the same level as a US state. Austria as a whole covers about
83,900 km² (computed from the boundaries used below), so one region for the whole country is a real alternative; it is
listed under "Still undecided".

### Codes

ISO 3166-2:AT numbers the states 1 to 9: `AT-1` Burgenland to `AT-9` Vienna. The Austrian Environment Agency's code
list and Wikipedia agree on the numbers (search only); one ontology site found in the same search lists them in a
different order and should not be used. The same numbers are the state key (`BL_KZ`) in BEV's boundary data, which was
checked in the files: each state's file holds only its own key.

- A hyphenated code is needed for the same reason as Germany: it keeps Austrian regions apart from US state codes at a
  glance. A bare `AT` is not one of the 52 entries in `STATE_CODES` (`engine/address_search.py`), so a single
  whole-country region could use it without a collision. Pull request #84 names whole countries `eu-<iso>` instead,
  because other bare country codes do collide (`DE`, `AL`, `ME`, `MT`); if that lands, the whole-country region here
  is its `eu-at`.
- The part after the hyphen is a digit, unlike every code in use so far. `Lastbook-Map-AT-9.zip` is unambiguous but
  says little to a person, so setup would need to show the state's name next to it.

### Vienna and the other special cases

- **Vienna inside Lower Austria.** The `AT-3` box contains the whole `AT-9` box, so a Lower Austria map would show
  Vienna's streets and help points without any extra rule. Address search reads one index per state, so a Lower Austria
  map would not find Vienna addresses unless the index is cut by box, not by state. This is the same decision as Berlin
  inside Brandenburg in [REGIONS-DE.md](REGIONS-DE.md).
- **Tyrol is in two parts.** North Tyrol and East Tyrol do not touch, so the `AT-7` box spans the land between them
  in Salzburg and South Tyrol (Italy), and its edges also take in parts of Vorarlberg, Carinthia, Bavaria and
  Switzerland. A Tyrol map would carry those rows too.
- **Kleinwalsertal and Jungholz.** The cadastral municipality of Mittelberg in the Kleinwalsertal sets Vorarlberg's east
  edge (10.24° E). Jungholz lies inside the `AT-7` box. Both are reached by road through Germany (from general
  knowledge, not checked); for a map that matters only in that the nearest help may be across the border.
- **Lake Constance (Bodensee).** BEV's boundary data has no lake polygons: Vorarlberg's boundary follows the shore, and
  its box ends at 47.60° N. Germany's VG250 does carry the lake ([REGIONS-DE.md](REGIONS-DE.md), "Still undecided"). The
  lake's border has never been agreed, so this belongs with the disputed boundaries question in REGIONS.md.
- **The boxes overlap a lot.** Austria is long and narrow and its states interlock, so most boxes reach into two or
  three neighbours. Because a state map holds every row inside its box, that is extra data, not missing data.

### Boxes

The boxes were computed from BEV's **Verwaltungsgrenzen (VGD) BEV Stichtag 01.04.2026**, opened in BEV's catalogue
(record `2d7b8f24-deb9-42eb-82f2-c7c1c7ff7075`, CC BY 4.0). It comes as one shapefile per state
(`VGD_<State>_20260402.zip`, 1.6 to 13.3 MB each, 52 MB in all). The catalogue record gives no checksums, so the
SHA-256 of each file used is in the JSON. Each file holds the state's cadastral municipalities (Katastralgemeinden),
7,850 in all.

Every vertex, about 6.5 million, was transformed from MGI / Austria Lambert (EPSG:31287; the files' `.prj` gives the
same parameters) to WGS 84 with pyproj 3.8.0 and PROJ 9.8.1. PROJ chose "MGI to WGS 84 (3)", with a stated accuracy of
1.5 m. Each box was then widened by 0.15° and rounded outward to 0.01°, the same margin `map_sets.state` uses for US
states.

As a check, the outer edges fall in the municipalities that hold Austria's known extreme points: Nofels in Feldkirch in
the west (9.53° E), Deutsch Jahrndorf in the east (17.16° E), Rottal in Haugschlag in the north (49.02° N) and Bad
Vellach in Eisenkappel-Vellach in the south (46.37° N). The state areas, computed on the WGS 84 ellipsoid, add up to
83,927 km², 43 km² more than the official 83,884 km² (BEV and Statistik Austria, as of 1 January 2025, in WKO's table
"Fläche und Benützungsarten"; Statistik Austria's "Österreich. Zahlen. Daten. Fakten" 2024/25 gives 83,883.87 km²;
both opened on 19 November 2026).

| Code | `BL_KZ` | Name | Box (west, south, east, north) | Box with 0.15° margin | Area (km²) |
|---|---|---|---|---|---|
| `AT-1` | 1 | Burgenland | 15.9962, 46.8306, 17.1608, 48.1187 | 15.84, 46.68, 17.32, 48.27 | 3,964 |
| `AT-2` | 2 | Kärnten (Carinthia) | 12.6568, 46.3723, 15.0651, 47.1313 | 12.50, 46.22, 15.22, 47.29 | 9,543 |
| `AT-3` | 3 | Niederösterreich (Lower Austria) | 14.4526, 47.4222, 17.0688, 49.0205 | 14.30, 47.27, 17.22, 49.18 | 19,195 |
| `AT-4` | 4 | Oberösterreich (Upper Austria) | 12.7492, 47.4611, 14.9922, 48.7726 | 12.59, 47.31, 15.15, 48.93 | 11,985 |
| `AT-5` | 5 | Salzburg | 12.0761, 46.9439, 13.9961, 48.0415 | 11.92, 46.79, 14.15, 48.20 | 7,161 |
| `AT-6` | 6 | Steiermark (Styria) | 13.5633, 46.6120, 16.1718, 47.8279 | 13.41, 46.46, 16.33, 47.98 | 16,413 |
| `AT-7` | 7 | Tirol (Tyrol) | 10.0978, 46.6514, 12.9660, 47.7430 | 9.94, 46.50, 13.12, 47.90 | 12,648 |
| `AT-8` | 8 | Vorarlberg | 9.5307, 46.8409, 10.2372, 47.5961 | 9.38, 46.69, 10.39, 47.75 | 2,603 |
| `AT-9` | 9 | Wien (Vienna) | 16.1818, 48.1179, 16.5775, 48.3227 | 16.03, 47.96, 16.73, 48.48 | 415 |
| `AT` | | Austria, as one region | 9.5307, 46.3723, 17.1608, 49.0205 | 9.38, 46.22, 17.32, 49.18 | 83,927 |

A newer boundary release, as of 1 October 2026, is already on BEV's download server (`.../shp/20261001/`, files dated
2 October 2026) but was not yet in BEV's catalogue on 17 November 2026, so the catalogued April release was used.
Boundaries between states rarely move, so the boxes should not change.

## Relation to pull request #84

Pull request #84 ("Maps: European country map sets, built and published like state maps", open, description read on
17 November 2026) builds one map set per European country with the same cutting code as the US states. Austria is its
worked example, `eu-at`. The two proposals answer different questions and fit together:

- **Region level.** #84 cuts whole countries. This proposal cuts states, with the whole country as an alternative
  (`AT` in the table above). If #84 lands, the whole-country option here is simply its `eu-at`, and the open question
  becomes whether Austria also needs the nine state regions on top.
- **Boxes.** #84 takes each country's box from the polygon of Geofabrik's OpenStreetMap extract. Its stored `eu-at.box`
  is [9.5268, 46.3698, 17.1641, 49.024]; `build_packs.py` adds a 0.15° margin, giving 9.3768–17.3141° E and
  46.2198–49.174° N. The stored box is within 0.004° (about 400 m) of the official boundary computed here on every side, the extract's polygon
  being a little wider. For a whole-country map the two methods give the same result. For states only the official
  boundary helps, because the extract has no state lines.
- **Sources.** #84 cuts from the existing source layers, which [MAPS.md](MAPS.md) describes as US datasets or
  worldwide ones filtered to the US, so an `eu-at` set holds only what those layers hold for Austria. The Austrian
  sources below would fill it.
- **Addresses.** #84 keeps address search US-only, because the address index is split by Overture's US state column.
  Overture already carries the Austrian Address Register (see below), so an Austrian index needs a split by country,
  and the parsing changes under "How addresses are written".

## Sources, layer by layer

All are nationwide. "BEV catalogue" is `data.bev.gv.at/geonetwork`; each BEV record says "Für dieses Produkt gilt die
Standardlizenz CC-BY-4.0".

| Layer (file) | US source today | Proposed for Austria | Publisher | Licence | Checked |
|---|---|---|---|---|---|
| Terrain (`terrain.sqlite`) | USGS 3DEP, 1 arc-second | Digitales Geländemodell (DGM) Österreich, 10 m, from airborne laser scanning, resampled to the size the app uses | geoland.at | CC BY 4.0 | data.gv.at record opened |
| Terrain, up to date | | ALS DTM Höhenraster 1 m, as of 15 September 2025, in 55 tiles | BEV, with the states | CC BY 4.0 | BEV catalogue opened |
| Terrain, ready-made | | DGM Höhenraster 25 m (one Cloud Optimized GeoTIFF, 786 MB) | BEV | CC BY 4.0 | BEV catalogue opened |
| Water (`water.sqlite`) | NHD | Gesamtgewässernetz (GGN): rivers (v19, June 2026) and lakes | BMLUK | CC BY 4.0 | rivers opened on data.gv.at; lakes search only |
| Springs and water lines | | DLM Gewässer, as of 23 March 2026: rivers and streams, water supply lines, springs, waterfalls (GeoPackage, 396 MB) | BEV | CC BY 4.0 | BEV catalogue opened |
| Dams | NID | "Liste großer Stauanlagen" (XLSX, August 2025); OSM `waterway=dam` | linked from BMLUK under the ATCOLD heading; OSM contributors | not stated; ODbL | page linking the list opened; list itself not opened |
| Crops (`crops.sqlite`) | USDA Cropland Data Layer | INVEKOS Schläge 2026-1: every farm field declared for EU subsidy, with its crop (GeoPackage, 1,255 MB) | AMA (Agrarmarkt Austria) | CC BY 4.0 | INSPIRE record for 2025-1 opened; 2026-1 sampled through AMA's OGC API |
| Buildings (`buildings.sqlite`) | Microsoft US footprints, OSM heights | DLM Bauwerke, as of 23 March 2026: building outlines with ground, mean and maximum height (GeoPackage, 2,646 MB) | BEV | CC BY 4.0 | BEV catalogue opened |
| Places (`places.sqlite`) | GNIS, Census gazetteers, OSM | DLM Geographische Namen, as of 23 March 2026, over 220,000 names (GeoPackage, 59 MB); VGD municipality names; OSM named places | BEV; OSM contributors | CC BY 4.0; ODbL | BEV catalogue opened |
| Addresses (`addresses/<code>.sqlite`) | Overture addresses | **Overture addresses, which carry the Austrian Address Register**; BEV's own register as a direct source (CSV, as of 1 October 2026, 118.5 MB ZIP) | Overture Maps Foundation, from BEV through OpenAddresses; BEV | CC BY 4.0 | Overture attribution page and BEV catalogue opened |
| Points of interest (`poi` rows) | OSM | OSM, as today; police stations from BMI | OSM contributors; BMI | ODbL; CC BY 4.0 | taginfo counts read; BMI record opened |

No product this proposal needs was found behind a fee or a restricted user group, unlike Germany's nationwide BKG
products.

Notes:

- **Terrain.** All three models are bare earth, so contours follow the ground in forest and towns, which Copernicus
  GLO-30 does not. The geoland 10 m model is the practical choice: one download, already close to the app's 30 m, from
  laser scanning. Its data.gv.at record was last updated on 15 April 2021, and its download is one ZIP of
  1,938,031,542 bytes (about 1.9 GB, file dated 18 June 2019, read from the server on 19 November 2026). BEV's
  1 m model is newer, but one of its 55 tiles alone is 7.6 GB. BEV's 25 m raster is the smallest single file, but BEV
  says it comes from aerial photographs and has not been updated since 2020.
- **Water.** GGN is the federal network used for the EU Water Framework Directive (its keywords say so). From version 19
  it marks stretches that are not waters under the Water Act, such as dry gullies, and those should be left out. BEV's
  DLM Gewässer adds **springs** (Quellen), which suit Lastbook's purpose better than almost any other water feature.
  Whether DLM Gewässer also carries lakes was not checked: its description lists flowing waters only.
- **Dams.** The Umweltbundesamt also runs a "Dashboard Große Stauanlagen". Whether the XLSX list has coordinates, and
  under what terms it can be reused, was not checked. OSM has 1,258 `waterway=dam` objects in Austria.
- **Crops.** This is where Austria is richer than the US. Instead of a 30 m raster class, every field carries a crop
  name (`snar_bezeichnung`) and code (`snar_code`). AMA's API was sampled in three areas on 17 November 2026 (800 fields
  each): `WEIN` (901) was the most common crop in the Wachau and Seewinkel samples (a later, smaller Seewinkel
  sample disagreed, so this is a sample result, not a regional fact), and the samples also hold `MARILLEN`
  (813, apricots), `TAFELÄPFEL` (817), `TAFELBIRNEN` (818) and `ZWETSCHKEN` (820, plums). Three things to know:
  - `tools/build_crops.py` reads the USDA raster, so this needs either rasterising the fields or a vector path.
  - The code list was not read, so berry codes were not found in the samples.
  - The layer holds only fields someone applied for a subsidy on. Gardens and farms that did not apply are missing.
- **Buildings.** BEV describes DLM Bauwerke as complete and uniform for all of Austria, with heights for a 2.5D block
  model (LoD1). Where a building matches one address, it links to the address register through the AGWR object number.
  That covers both US sources at once: the outline and the height.
- **Places.** DLM Geographische Namen holds settlements, areas, mountains, glaciers, waters and field names
  (Riednamen). BEV also publishes small CSV tables of mountains and lakes with their heights.
- **Addresses.** Overture's attribution page lists "Austrian Address Register", CC BY 4.0, distributed by
  OpenAddresses, "Accessed: 2026-11-17" when read on 19 November 2026 (it said 15 October 2026 two days earlier; the
  page refreshes this date). So `tools/build_addresses.py` would only need a different country filter.
  How Overture fills the region field for Austrian rows was not checked.

## Help points

Counts from taginfo for Geofabrik's Austria extract, data until 16 November 2026 21:21 UTC (opened):

| Tag | Count | Notes |
|---|---|---|
| `amenity=pharmacy` | 1,520 | |
| `amenity=fire_station` | 4,066 | may hold both a building and a node for one station, as in Germany; not measured |
| `amenity=police` | 952 | cross-check with BMI's list (below) |
| `amenity=hospital` | 223 | cross-check with the ministry's list (below) |
| `amenity=drinking_water` | 8,560 | |
| `man_made=water_well` | 2,131 | |
| `emergency=water_tank` | 859 | firefighting water, not drinking water |
| `emergency=drinking_water` | 2 | Germany's emergency well layer has no Austrian counterpart in OSM |
| `emergency=assembly_point` | 186 | |
| `emergency=defibrillator` | 2,071 | |

Austria has one kind of help point worth a decision:

- **Police stations as blackout contact points.** The federal portal oesterreich.gv.at says, on a page by the interior
  ministry (last updated 16 February 2026, opened), that in a blackout "bleiben alle Polizeiinspektionen bundesweit
  personell besetzt", as contact points for the public. The same ministry publishes the locations and areas of all
  police offices as open data: "Polizeidienststellen Österreich (BMI)", CSV and GeoPackage, files dated
  11 November 2026, CC BY 4.0 (opened on data.gv.at; the portal shows a wrong "updated" date for this record and
  says so itself). A help point backed by an official, complete list and an official promise is exactly what
  Lastbook is for. The map could say so in the ministry's words and cite the page.
  - **Only the inspections.** The promise names *Polizeiinspektionen*, the local stations, but the list holds every
    kind of office. Of its 924 rows (`ArtLang`, counted on 19 November 2026), 744 are `Polizeiinspektion`. The rest are
    76 district commands, 32 motorway inspections, 25 city commands, 13 traffic inspections, 9 state directorates, 6
    border inspections and 19 special or combined units. The map should take only `ArtLang = Polizeiinspektion`, so
    that no row promises more than the ministry does. Whether the motorway, border and other inspection kinds count as
    *Polizeiinspektionen* in the ministry's sense is for BMI to say.

Not proposed:

- **Municipal blackout contact points.** The same page says that in a blackout the municipal office or the local fire
  station may be the contact point. Each municipality decides this itself, and no national list was found. Lower
  Austria's civil protection association tells people to ask their municipality (search only).
- **Hospitals from the ministry.** The health ministry publishes "Liste der Krankenanstalten in Österreich" (XLSX, as of
  18 September 2026, opened). The page says the list "steht zur Weiterverarbeitung als Download zur Verfügung", so
  reuse is invited, but it calls the list a voluntary service and names no licence or credit line. Whether it has
  coordinates was not checked. Like Germany's register, it could cross-check OSM's 223 hospitals; replacing them would
  need the ministry to name the terms.

## Licence notes and attribution

The official sources proposed for the primary layers above name CC BY 4.0: credit the source, link the licence, note
changes. The dam and hospital lists have separate, unresolved terms as noted above. The credit lines found
so far:

- **Austrian Address Register.** Its BEV record (opened) sets the line itself, for every form of distribution and every
  derived product: "© Österreichisches Adressregister, Stichtagsdaten vom TT.MM.JJJJ", with the date of the extract.
  If the data comes through Overture, Overture's credit is added.
- **AMA (INVEKOS).** Free use under CC BY 4.0 "und der verpflichtenden Angabe der Datenquelle", with a disclaimer
  (opened). The same text calls the licence "CC-BY-AT 4.0", while the record's licence field says "Namensnennung 4.0
  International (CC BY 4.0)". Creative Commons made no national versions of 4.0, so this is most likely the
  international licence under another name. AMA should confirm that.
- **BEV, geoland.at, BMLUK, BMI.** CC BY 4.0 in each record (opened). The exact credit wording each asks for was not
  read.
- **ODbL** (OSM). As for the US map.
- **Overture addresses.** "Overture Maps Foundation, overturemaps.org" and the credit of the source, here the Austrian
  Address Register.

These notices would belong wherever the map already credits its sources, and in `THIRD_PARTY_NOTICES.md` if that is
where the maintainers keep data licences.

## How addresses are written

Austrian Post's guide "Richtig adressieren" (February 2020, opened) gives the form:

- **Order.** Street, then house number, then postcode and town: "Grünwaldweg 16/13/5, 2283 Obersiebenbrunn".
- **Staircase and door.** Where a house has several entrances or flats, block, staircase (Stiege) and door number follow
  the house number, separated by slashes: `16/13/5`.
- **Locality, where an address repeats.** When the same address occurs twice in one postcode area and municipality,
  the guide writes the locality that tells them apart, either in place of the municipality ("Elisabethgasse 3, 3400
  Weidling") or on its own line before the postcode ("Elisabethgasse 3, Weidling, 3400 Klosterneuburg"). So for those
  addresses the town after the postcode may be the locality rather than the municipality.
- **Postcode.** Four digits.
- **Street words.** Mostly single compound words or two words ending in *-straße* (often *-str.*), *-gasse*, *-weg* or
  *-platz*, as in German. *ß* and umlauts raise the same typing problems as in Germany.
- **What the current code does with that** (read in this repository and tried on the examples above on 17 November
  2026):
  - `normalize()` in `engine/address_search.py` and `norm()` in `tools/build_addresses.py` keep only `a-z` and `0-9`,
    so "Grünwaldweg" becomes `gr nwaldweg`, as in Germany.
  - `is_address_query()` needs a number first, so "Grünwaldweg 16/13/5, 2283 Obersiebenbrunn" is not treated as an
    address. Neither is "16/13/5 Grünwaldweg": the slash ends the number before the space the rule looks for.
  - **A postcode with its town is taken for an address.** "1060 Wien" and "5020 Salzburg" pass `is_address_query()`,
    and `_parts()` reads them as house number 1060 on a street called "wien". A four-digit postcode has the same shape
    as a house number, so this needs a rule that knows the postcode list.
  - `_parts()` takes a postcode only as the last word and only with five digits, so "2283" stays among the street
    words. Since #121 it also reads a last word of four digits as a ZIP+4 suffix when five digits come before it; an
    Austrian rule for four-digit postcodes would have to live beside that one.
  - `tools/build_addresses.py` keeps only `country = 'US'`; `left(postcode, 5)` leaves a four-digit postcode as it is.

## Still undecided

Each of these needs the maintainers' decision before any code changes. The first two are shared with REGIONS.md and
REGIONS-DE.md.

1. **Codes in setup.** Whether `AT-1` to `AT-9` are acceptable as a manifest `id`, in `map-set.json` and in
   `Lastbook-Map-<id>.zip`, how setup shows names for codes that are only digits, and how state codes sit next to #84's
   `eu-<iso>` country codes.
2. **The box rule**, as in REGIONS.md, here from BEV's VGD.
3. **Nine regions or one.** The whole country, about 83,900 km², could be a single region, #84's `eu-at`. That would
   remove the Vienna address question and the two-part Tyrol box, at the cost of a bigger download for someone who
   needs only one state.
4. **Vienna.** If there are nine regions, whether the Lower Austria map should also carry Vienna's addresses.
5. **Terrain.** geoland's 10 m model, BEV's 1 m tiles resampled, or BEV's ready-made 25 m raster.
6. **Crops.** Rasterising the INVEKOS fields or reading them as vectors, the mapping from AMA's crop codes to the app's
   orchard, vineyard and berry kinds, and how the map says that only subsidised fields are shown.
7. **Address search.** Four-digit postcodes, slash house numbers, and "postcode town" as a place query.
8. **Police stations** as a help point that says it is staffed in a blackout, citing the ministry, limited to
   `Polizeiinspektion` rows; whether motorway and border inspections belong too.
9. **Lake Constance**, with Germany's question in REGIONS-DE.md.

## What was checked, and what was not

- Opened on 17 November 2026: BEV catalogue records for the VGD boundaries (1 October 2025 and 1 April 2026), the
  address register (relational tables, 1 October 2026), DLM Geographische Namen, DLM Gewässer, DLM Bauwerke and DLM
  Bauten (23 March 2026), ALS DTM 1 m (15 September 2025) and the 25 m DGM; the INSPIRE record for INVEKOS Schläge
  2025-1, and AMA's OGC API collections for 2015 to 2026-1; the data.gv.at records for the geoland 10 m DGM, the BEV
  addresses, the GGN rivers and BMI's police stations; Overture's attribution page; BMLUK's page on dams; the health
  ministry's hospital list page; oesterreich.gv.at's blackout page; Austrian Post's "Richtig adressieren"; Geofabrik's
  Austria page; taginfo for the counts above; the description of pull request #84 (its code was not read).
- Computed on 17 November 2026: the nine boxes and areas, from VGD as described above; the extreme points; the crop
  samples, from AMA's API in three areas.
- Tried in this repository on 17 November 2026: the address examples above, against `normalize()`,
  `is_address_query()` and `_parts()`.
- Seen only in search results: the ISO 3166-2:AT codes (Umweltbundesamt list and Wikipedia; the ISO site was not
  opened); the GGN lakes record; Lower Austria's civil protection advice; the Umweltbundesamt dam dashboard.
- Not checked: INVEKOS's full crop code list; whether DLM Gewässer has lakes; the dam list's contents and terms; the
  hospital list's columns; the credit wording BEV, geoland.at, BMLUK and BMI ask for; how Overture fills the region
  field for Austrian addresses; the road access of the Kleinwalsertal and Jungholz.
- Checked again on 19 November 2026: Overture's attribution page; the health ministry's hospital list page;
  oesterreich.gv.at's blackout page; BMI's police CSV (downloaded, rows counted by `ArtLang`); Carinthia's VGD file
  (same checksum, box recomputed); Austrian Post's "Richtig adressieren" (the duplicate-address section); the geoland
  10 m download's size; WKO's area table and Statistik Austria's "Österreich. Zahlen. Daten. Fakten" 2024/25.
