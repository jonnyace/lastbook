# Detailed maps for Mexico: a proposal

This is a proposal for discussion, not a decision. It answers, for Mexico, the questions [MAPS.md](MAPS.md) asks before
coverage can go beyond the United States: which open source replaces each federal list, under what licence, what a
"state" is there, and how addresses are written. It follows the shape of [REGIONS.md](REGIONS.md),
[REGIONS-ES.md](REGIONS-ES.md) and [REGIONS-AR.md](REGIONS-AR.md) and is meant to feed the same design discussion
(issues #23, #25, #31 and #54). The machine-readable version is [regions-mx-proposed.json](regions-mx-proposed.json).

Nothing here changes the app, the engine or a build. No code reads the JSON, and nothing here ships: builds package
`web/` and `content/` only.

**How things were checked.** Research was done on 18 November 2026, with AI research agents reading the publishers' own
pages and a person reviewing the result. The boxes were computed from the data itself, as described in each section.
Each source carries one of three marks:

- **opened**: the dataset or licence page itself was opened and read;
- **search only**: the fact was seen in a search result from the publisher's own site, but the page itself was not
  opened;
- **not checked**: the page could not be reached or read; the row says what is missing.

## Why Mexico is a useful case

Mexico is close to the US in the way its data is organised. In the Overture addresses guide it is third by address
count, after the United States (126,202,222) and Brazil (89,887,635), with 30,726,687 Mexican rows (the publisher's
guide counts, not a count made for this proposal). One national mapping agency (INEGI) publishes nationwide elevation,
hydrography, names, boundaries, land use and the statistical framework under one licence, the "Términos de Libre Uso
de la Información del INEGI" (INEGI Libre Uso), which permits copying, redistribution, adaptation and commercial use
with attribution and no share-alike. Overture already carries a nationwide address set from INEGI. Two things are
different from the US and worth deciding once, because other Latin American countries will raise them too:

- **No open postcode-area layer.** SEPOMEX (the postal service) owns postcode areas but does not publish them as open
  data. INEGI's framework includes locality points, not postcode areas. The five-digit *código postal* (CP) attached
  to each Overture address is a different thing and is what address search needs.
- **Crop types specific to Mexico.** INEGI's land-use and vegetation series includes agave, agostadero, temporal
  (rain-fed) and other classes that have no US class in `tools/build_crops.py`.

## What a region is

Mexico has 32 states (*entidades federativas*): 31 states and Mexico City (Ciudad de México, which was the Federal
District until 2016). The proposal is one region per state, 32 in all. A state is the level closest to a US state in
size and in what it runs (health, civil protection, most open data portals): the largest, Chihuahua (about 247,000
km²), is about the size of Idaho; the smallest is Mexico City (about 1,500 km²). INEGI's 2024 geographic compendium,
drawn on the December 2023 Marco Geoestadístico, gives Mexico City 1,494.3 km² and ranks it 32nd. Tlaxcala (about
4,000 km²) is the next smallest and a little smaller than Delaware; the Chihuahua and Tlaxcala areas were not
reopened for this change.

### Codes

ISO 3166-2:MX gives each state three letters after `MX-`: `MX-AGU` Aguascalientes, `MX-BCN` Baja California,
`MX-CMX` Mexico City, and so on (not checked against the ISO site, as the other proposals also note for their codes).

- The three-letter suffixes do not collide with any US state code in `STATE_CODES` (`engine/address_search.py`), which
  are two letters. A bare `MX` is not a US code either.
- A hyphenated code is still needed for the manifest `id` and for `Lastbook-Map-<id>.zip`, for the same reason as in
  the other proposals: `carry_over()` in `engine/setup/install.py` keeps only address indexes named `[A-Z]{2}.sqlite`
  or `.json`, so an index named `MX-AGU.sqlite` (or `AGU.sqlite`, which is three letters) would be left behind in the
  old library without a message.

### Boxes

The boxes were computed from INEGI's Marco Geoestadístico, AGEE layer (*Área Geoestadística Estatal*, the state
boundary), December 2023 version, in geographic coordinates (WGS84, EPSG:4326). The shapefile was downloaded through
CONABIO's mirror (`dest23gw.zip`, which is INEGI data; opened) and read with `geopandas`. Each state was taken as one
polygon feature. Every vertex of every polygon was read; the bounding box was then widened by 0.15° and rounded
outward to 0.01°, the same margin `map_sets.state` uses for US states.

As a check, the outer edges match Mexico's known extreme points: Isla de Guadalupe (29.09° N, 118.28° W) in the
northwest, the coast of Quintana Roo (21.61° N, 86.71° W) in the east, the mouth of the Suchiate River in Chiapas
(about 14.53° N) in the south, and the US border in the north (32.72° N). That southern latitude is the Chiapas
south edge in this table (14.5321° N). Published coordinates for the river mouth sit next to it (about 14.53° N;
one extreme-points list gives 14°32′27″ N, about 14.54° N). The Revillagigedo Islands belong to Colima. Colima's
west edge at -114.76° is Isla Clarión (about 18.36° N, 114.73° W), not Socorro (about 18.78° N, 110.98° W).

| Code | INEGI | Name | Box (west, south, east, north) | Box with 0.15° margin |
|---|---|---|---|---|
| `MX-AGU` | 01 | Aguascalientes | -102.8742, 21.6223, -101.8353, 22.4596 | -103.03, 21.47, -101.68, 22.61 |
| `MX-BCN` | 02 | Baja California | -118.3653, 28.0000, -112.2968, 32.7187 | -118.52, 27.85, -112.14, 32.87 |
| `MX-BCS` | 03 | Baja California Sur | -115.7661, 22.8717, -109.4131, 28.0000 | -115.92, 22.72, -109.26, 28.15 |
| `MX-CAM` | 04 | Campeche | -92.4688, 17.8129, -89.1212, 20.8483 | -92.62, 17.66, -88.97, 21.00 |
| `MX-COA` | 05 | Coahuila de Zaragoza | -103.9600, 24.5427, -99.8431, 29.8800 | -104.11, 24.39, -99.69, 30.03 |
| `MX-COL` | 06 | Colima | -114.7595, 18.3389, -103.4863, 19.5125 | -114.91, 18.18, -103.33, 19.67 |
| `MX-CHP` | 07 | Chiapas | -94.1392, 14.5321, -90.3702, 17.9853 | -94.29, 14.38, -90.22, 18.14 |
| `MX-CHH` | 08 | Chihuahua | -109.0749, 25.5588, -103.3068, 31.7845 | -109.23, 25.40, -103.15, 31.94 |
| `MX-CMX` | 09 | Ciudad de México | -99.3649, 19.0482, -98.9403, 19.5928 | -99.52, 18.89, -98.79, 19.75 |
| `MX-DUR` | 10 | Durango | -107.2101, 22.3451, -102.4727, 26.8449 | -107.37, 22.19, -102.32, 27.00 |
| `MX-GUA` | 11 | Guanajuato | -102.0970, 19.9128, -99.6713, 21.8394 | -102.25, 19.76, -99.52, 21.99 |
| `MX-GRO` | 12 | Guerrero | -102.1844, 16.3160, -98.0073, 18.8878 | -102.34, 16.16, -97.85, 19.04 |
| `MX-HID` | 13 | Hidalgo | -99.8595, 19.5978, -97.9849, 21.3985 | -100.01, 19.44, -97.83, 21.55 |
| `MX-JAL` | 14 | Jalisco | -105.6954, 18.9259, -101.5105, 22.7502 | -105.85, 18.77, -101.36, 22.91 |
| `MX-MEX` | 15 | México | -100.6131, 18.3669, -98.5969, 20.2859 | -100.77, 18.21, -98.44, 20.44 |
| `MX-MIC` | 16 | Michoacán de Ocampo | -103.7381, 17.9134, -100.0630, 20.3946 | -103.89, 17.76, -99.91, 20.55 |
| `MX-MOR` | 17 | Morelos | -99.4944, 18.3324, -98.6329, 19.1317 | -99.65, 18.18, -98.48, 19.29 |
| `MX-NAY` | 18 | Nayarit | -106.6877, 20.6032, -103.7209, 23.0845 | -106.84, 20.45, -103.57, 23.24 |
| `MX-NLE` | 19 | Nuevo León | -101.2068, 23.1627, -98.4216, 27.7991 | -101.36, 23.01, -98.27, 27.95 |
| `MX-OAX` | 20 | Oaxaca | -98.5527, 15.6569, -93.8674, 18.6697 | -98.71, 15.50, -93.71, 18.82 |
| `MX-PUE` | 21 | Puebla | -99.0705, 17.8609, -96.7247, 20.8400 | -99.23, 17.71, -96.57, 20.99 |
| `MX-QUE` | 22 | Querétaro | -100.5965, 20.0150, -99.0431, 21.6700 | -100.75, 19.86, -98.89, 21.82 |
| `MX-ROO` | 23 | Quintana Roo | -89.2966, 17.8940, -86.7104, 21.6055 | -89.45, 17.74, -86.56, 21.76 |
| `MX-SLP` | 24 | San Luis Potosí | -102.2960, 21.1602, -98.3260, 24.4915 | -102.45, 21.01, -98.17, 24.65 |
| `MX-SIN` | 25 | Sinaloa | -109.4447, 22.4671, -105.3922, 27.0423 | -109.60, 22.31, -105.24, 27.20 |
| `MX-SON` | 26 | Sonora | -115.0530, 26.2970, -108.4243, 32.4939 | -115.21, 26.14, -108.27, 32.65 |
| `MX-TAB` | 27 | Tabasco | -94.1300, 17.2509, -90.9875, 18.6510 | -94.28, 17.10, -90.83, 18.81 |
| `MX-TAM` | 28 | Tamaulipas | -100.1450, 22.2070, -97.1443, 27.6791 | -100.30, 22.05, -96.99, 27.83 |
| `MX-TLA` | 29 | Tlaxcala | -98.7084, 19.1051, -97.6254, 19.7289 | -98.86, 18.95, -97.47, 19.88 |
| `MX-VER` | 30 | Veracruz de Ignacio de la Llave | -98.6815, 17.1370, -93.6079, 22.4718 | -98.84, 16.98, -93.45, 22.63 |
| `MX-YUC` | 31 | Yucatán | -92.3263, 19.5512, -87.5331, 22.5860 | -92.48, 19.40, -87.38, 22.74 |
| `MX-ZAC` | 32 | Zacatecas | -104.3535, 21.0419, -100.7423, 25.1252 | -104.51, 20.89, -100.59, 25.28 |

Notes:

- **The Baja California peninsula** is split between `MX-BCN` (north) and `MX-BCS` (south) at the 28° N line. Both
  are long, narrow peninsulas with coast on both sides, so each must be its own region.
- **Colima's box** stretches far into the Pacific because it includes the Revillagigedo Islands (Socorro, San
  Benedicto, Clarión, Roca Partida). The western edge, -114.76°, is Isla Clarión, about 700 km from the mainland,
  not Socorro. The mainland part of Colima is a small coastal state around -103.5° W.
- **Mexico City (MX-CMX)** borders the State of Mexico (MX-MEX) to the north, east and west and Morelos (MX-MOR) to
  the south, so it is not fully surrounded by MX-MEX. It is the smallest region by area (about 1,500 km²), smaller
  than Tlaxcala. The Mexico City and State of Mexico boxes overlap heavily. An address index cannot be cut by
  reading the first two postcode digits as the INEGI state code; that split is future work (a state polygon, or a
  CP→state table whose rights are checked).
- **Tlaxcala (MX-TLA)** borders Puebla (MX-PUE), Hidalgo (MX-HID) and the State of Mexico (MX-MEX), so it is not
  fully surrounded by Puebla. The same postcode caveat applies.
- **Sonora and Chihuahua** are the two largest by area; their northern edges reach the US border (Arizona, New Mexico
  and Texas).
- **Quintana Roo** includes Cozumel and Isla Mujeres; it is the easternmost region.

## Sources, layer by layer

| Layer (file) | US source today | Proposed for Mexico | Publisher | Licence | Checked |
|---|---|---|---|---|---|
| Terrain (`terrain.sqlite`) | USGS 3DEP, 1 arc-second | **CEM 4.0** (~15 m, bare-earth DTM, national coverage, COG); Copernicus DEM GLO-30 as alternative | INEGI; ESA / Airbus | INEGI Libre Uso; Copernicus licence | CEM product page and INEGI terms opened; Copernicus as in REGIONS-ES.md |
| Water (`water.sqlite`) | NHD | INEGI Red Hidrográfica Nacional (1:250,000, SHP); CONAGUA Ríos Principales (WMS/WFS); OSM | INEGI; CONAGUA; OSM contributors | INEGI Libre Uso; not stated (CONAGUA); ODbL | INEGI hydrography page search only; CONAGUA service search only; OSM as for US |
| Dams | NID | **CONAGUA Catálogo de Presas** (~210 dams with coordinates, state, municipality); OSM `waterway=dam` as fallback | CONAGUA; OSM contributors | not stated (CONAGUA); ODbL | catalog page opened; CSV not downloaded (redirect loop); count from search results; licence not confirmed |
| Crops (`crops.sqlite`) | USDA Cropland Data Layer | **INEGI Uso del suelo y vegetación** 1:250,000 series VII (2018); ESA WorldCover 2021 as fallback | INEGI; ESA WorldCover | INEGI Libre Uso; CC BY 4.0 | INEGI product page search only; WorldCover as in REGIONS-AR.md |
| Buildings (`buildings.sqlite`) | Microsoft US footprints, OSM heights | **Google Open Buildings V3** (building footprints from satellite imagery, CC BY 4.0 / ODbL); OSM buildings to fill gaps | Google Research; OSM contributors | CC BY 4.0 (or ODbL); ODbL | Google Open Buildings page opened; OSM as for US |
| Places (`places.sqlite`) | GNIS, Census gazetteers, OSM | **INEGI Marco Geoestadístico** (AGEE, AGEM, localidades; names and codes); OSM named places | INEGI; OSM contributors | INEGI Libre Uso; ODbL | INEGI Marco Geoestadístico page and shapefile opened (used for bbox computation) |
| Addresses (`addresses/<code>.sqlite`) | Overture addresses | **Overture addresses: 30,726,687 Mexican rows**, source INEGI through OpenAddresses | Overture Maps Foundation / INEGI | INEGI Libre Uso (see Overture attribution page) | Overture address guide and attribution page opened |
| Points of interest (`poi` rows) | OSM | OSM, as today | OSM contributors | ODbL | taginfo for Mexico (API) read |

Notes:

- **Terrain.** CEM 4.0 is a national bare-earth model at ~15 m, built from ALOS PALSAR (JAXA) with LiDAR/photogrammetry
  gap-filling. It is closer to the 30 m the app uses today than Copernicus GLO-30, and it is bare earth (not surface),
  so it avoids the canopy and roof problem. Coverage is complete over continental Mexico and partial over islands.
  Download is by state or by area from the INEGI elevation portal. The exact attribution label ("Fuente: INEGI,
  Continuo de Elevaciones Mexicano 4.0") comes from the INEGI terms, which were opened.
- **Dams.** The CONAGUA catalog lists ~210 dams with fields: name, latitude, longitude, altitude, state, municipality,
  basin and hydrological region. The CSV is at `sih.conagua.gob.mx/basedatos/Presas/0_Catalogo_de_presas.csv`, but
  the site has a redirect loop that prevented a direct download for this proposal. The count was confirmed in search
  results. The catalogue is also available as an ArcGIS REST service (`sigagis.conagua.gob.mx`). The licence is not
  stated on the page; whether CONAGUA's data follows the same "Términos de Libre Uso" framework as INEGI was not
  confirmed. A build would need to check the licence before using it.
- **Crops.** `tools/build_crops.py` keeps orchards, vineyards and berries. In Mexico the most important permanent
  crops are agave (for tequila and mezcal), coffee, sugarcane, citrus and avocado. INEGI's land-use and vegetation
  series (1:250,000, series VII, 2018) includes crop-type classes such as *agostadero* (pasture/rangeland),
  *temporal* (rain-fed agriculture), *agave*, *caña* (sugarcane) and *cafetal* (coffee plantation), which have no
  US class. Whether the crop layer should grow new kinds for these Mexican crops is a decision for the maintainers,
  as noted for olives, citrus and nuts in REGIONS-ES.md. ESA WorldCover 2021 (10 m, CC BY 4.0) is a coarser fallback
  that shows cropland as a class, not crop types.
- **Buildings.** Google Open Buildings V3 provides 1.8 billion building footprints across Africa, Latin America,
  the Caribbean, South Asia and SE Asia, including all of Mexico. Each footprint has a confidence score [0.65–1.0],
  an area and a Plus Code. The licence is CC BY 4.0 and ODbL; the user may choose either. Microsoft Global ML Building
  Footprints also covers Mexico and remains an alternative. The repository is public and not archived (GitHub API,
  19 November 2026; last push 18 November 2026). The README's direct licence for the data is CDLA-Permissive-2.0
  (README opened the same day; an update entry is dated 12 November 2026). OSM has building footprints in urban
  areas but coverage is thinner in rural Mexico.
- **Places.** INEGI's Marco Geoestadístico is the national framework: states (AGEE, 32), municipalities (AGEM,
  ~2,467), and localities (urban and rural). It is updated yearly; the December 2023 version was used for the boxes
  in this proposal, and the December 2025 version is available. The shapefile was downloaded through CONABIO's
  mirror (`dest23gw.zip`), which is INEGI data. The framework is in Lambert Conformal Conic (CCL) but available in
  geographic coordinates (WGS84) as well.

## Addresses in Overture, from the publisher's guide

The Mexican rows of Overture release `2026-11-18.0` were read from the address guide on 18 November 2026. The counts
below are the publisher's, not a measurement made for this proposal:

- **30,726,687 addresses**, third after the United States (126,202,222) and Brazil (89,887,635). One source: "INEGI,
  Censos Económicos. TÉRMINOS DE LIBRE USO DE LA INFORMACIÓN DEL INEGI. Distributed by OpenAddresses. Accessed:
  2026-11-17." (Overture attribution page, opened).
- Per-state counts were not computed. Splitting on the first two postcode digits as if they were the INEGI state
  code would put addresses in the wrong state: Aguascalientes (INEGI 01) starts at 20000, and Zacatecas (INEGI 32)
  at 98000. The state split is left as future work, for example by state polygon, or by a CP→state table whose
  rights are checked. The national total in the guide is about a quarter of the US total and larger than any
  European country listed there.

## Help points

OSM is the practical source for help points across Mexico: no national open list with coordinates was confirmed for
hospitals, pharmacies, fire stations or police. The Ministry of Health's national catalogue is not published as open
data with coordinates. Counts from taginfo for Geofabrik's Mexico extract, data until 17 November 2026 21:19 UTC
(API, opened):

| Tag | Count | Notes |
|---|---|---|
| `amenity=pharmacy` | 7,943 | |
| `amenity=hospital` | 3,507 | |
| `amenity=clinic` | 5,117 | includes *centros de salud* of primary care |
| `amenity=fire_station` | 426 | |
| `amenity=police` | 1,491 | |
| `amenity=drinking_water` | 548 | far below the 44,411 in Spain; drinking fountains are less common in OSM in Mexico |
| `man_made=water_well` | 685 | |
| `natural=spring` | 247 | not drinkable by default |
| `emergency=water_tank` | 49 | mostly firefighting water |
| `emergency=defibrillator` | 23 | very thin; a national register was not found |
| `tourism=alpine_hut` | 103 | mostly in the Sierra Madre |
| `tourism=wilderness_hut` | 16 | |
| `amenity=shelter` | 2,139 | needs `shelter_type` filter; includes bus stops and picnic roofs |
| `amenity=fountain` | 3,074 | count only when `drinking_water=yes` |

Three Mexican kinds of point are worth a decision:

- **Drinking water.** With 548 `amenity=drinking_water` points, OSM's coverage is thin in Mexico. The CONAGUA
  *Sistema Nacional de Información del Agua* (SINA) has a WMS service for water infrastructure, but its licence and
  point coverage were not confirmed.
- **Mountain huts and shelters.** The Sierra Madre Occidental and Oriental run the length of Mexico; the 103
  `tourism=alpine_hut` and 16 `tourism=wilderness_hut` points are thin. Plain `amenity=shelter` (2,139) needs the
  `shelter_type` filter as in Spain.
- **CENAPRED and Protección Civil.** The Centro Nacional de Prevención de Desastres (CENAPRED) and state-level
  Protección Civil publish hazard maps and shelter inventories, but their datasets are not published as open data
  with coordinates and a clear licence. A help-point layer in Mexico would be OSM with a plain "incomplete" note,
  unless a provincial source is found.

## Licence notes and attribution

All proposed licences allow redistribution in a free offline library, including commercial reuse. What each asks:

- **INEGI Libre Uso.** Attribution: "Fuente: INEGI, *product name*" and the date of last update when applicable
  (e.g. "Fuente: INEGI, Marco Geoestadístico 2023"). Notify end users of any analysis or transformation, and do not
  suggest INEGI endorses the result. No share-alike. The terms are at
  `https://www.inegi.org.mx/contenidos/inegi/doc/terminos_info.pdf` (opened).
- **CC BY 4.0** (Google Open Buildings, ESA WorldCover). Credit the publisher: "Google Open Buildings" for buildings;
  "© ESA WorldCover project 2021" for WorldCover.
- **ODbL** (OSM, Overture buildings). Credit "© OpenStreetMap contributors", state the data is under the ODbL, and
  offer a database built from it under the ODbL too. The US map already carries ODbL data, so this is not new.
- **Copernicus WorldDEM-30.** As in REGIONS-ES.md and REGIONS.md: a modified copy must say "produced using Copernicus
  WorldDEM-30 © DLR e.v. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the
  European Union and ESA; all rights reserved", and carry the liability disclaimer forward.
- **CONAGUA.** The licence for the dam catalog was not confirmed. Whether CONAGUA's data follows the same "Términos
  de Libre Uso" framework as INEGI, or has its own terms, was not checked. This should be confirmed before a build.

These notices would belong wherever the map already credits its sources, and in `THIRD_PARTY_NOTICES.md` if that is
where the maintainers keep data licences.

## How addresses are written

- **Order.** Street type, street name, then the number, then postcode and town: "Av. Reforma, 123, 06600 Ciudad de
  México". The type comes first (*Avenida*, *Calle*, *Boulevard*, *Privada*, *Andador*, *Calzada*) and is often
  abbreviated (*Av.*, *C.*, *Blvd.*, *Priv.*, *And.*).
- **Postcode.** Five digits (*código postal*, CP), the same shape as a US ZIP code. A postcode must stay text,
  because leading zeros occur (for example 06600 Ciudad de México). The first two digits are not the INEGI state
  code: Aguascalientes (INEGI 01) starts at 20000 and Zacatecas (INEGI 32) at 98000. A per-state split of those
  codes is future work.
- **Spanish characters.** Street names carry accents (á, é, í, ó, ú) and ñ. `normalize()` in
  `engine/address_search.py` and `norm()` in `tools/build_addresses.py` keep only `a-z` and `0-9`, so "Reforma"
  matches but "Niños Héroes" becomes "ni os" and "Privada de la Cañada" becomes "privada de la ca ada". Accent and ñ
  folding (á→a, ñ→n) on both sides would fix this, as noted for Spain in REGIONS-ES.md.
- **S/N.** Many rural and suburban addresses have no number; OSM uses `S/N` (*sin número*, "no number"), the same as
  the Spanish *S-N* in Overture's ES rows. The builder keeps `S-N` rows as if `S-N` were a number.
- **What the current code does with that** (read in this repository on 18 November 2026):
  - `tools/build_addresses.py` keeps only `country = 'US'`; it would need to accept `country = 'MX'`.
  - `is_address_query()` needs a number first, so "Av. Reforma 123, 06600" is not treated as an address today.
  - The five-digit CP rule itself fits Mexico unchanged, like Spain.

## Still undecided

Each of these needs the maintainers' decision before any code changes. The first two are shared with REGIONS.md and
the other proposals.

1. **Codes in setup.** Whether `MX-AGU` and the others are acceptable as a manifest `id`, in `map-set.json` and in
   `Lastbook-Map-<id>.zip`, and how setup groups 32 Mexican states. The same `carry_over()` concern as the other
   proposals applies: a hyphenated or three-letter code does not match `[A-Z]{2}.sqlite`.
2. **The box rule**, as in REGIONS.md, here from INEGI's Marco Geoestadístico.
3. **Postcodes.** SEPOMEX owns the postcode areas but does not publish them as open data. The five-digit CP attached
   to each address in Overture's INEGI-sourced data is a different thing and is what address search needs; whether
   SEPOMEX's rights reach it was not checked.
4. **New crop kinds**: agave, agostadero, coffee, sugarcane, avocado.
5. **CONAGUA licence.** Whether the dam catalog's licence is confirmed as open, and whether CONAGUA follows the same
   "Términos de Libre Uso" framework as INEGI.
6. **Google Open Buildings vs. Overture buildings.** Whether to use Google Open Buildings (CC BY 4.0 / ODbL) or
   wait for Overture buildings, which may include Mexico.
7. **Overlapping boxes.** Mexico City's box overlaps the State of Mexico, and Mexico City also borders Morelos.
   Tlaxcala borders Puebla, Hidalgo and the State of Mexico. Whether an index per region can be cut by state
   polygon, or by a CP→state table whose rights are checked, or whether the box overlap is acceptable. The first
   two postcode digits are not the INEGI state code, so they are not that cut.
8. **The map credit line.** INEGI's terms ask for attribution at the source of the work; whether "a pie de mapa" (at
   the foot of the map) is required, as for IGN in Spain, should be confirmed.

## What was checked, and what was not

- Opened on 18 November 2026: INEGI's terms of free use (terminos_info.pdf); the CEM elevation portal; the INEGI
  Marco Geoestadístico page and shapefile (through CONABIO's mirror, which is INEGI data, in geographic WGS84
  coordinates); the CONAGUA dam catalog page; the Google Open Buildings V3 page; the Overture address guide and
  attribution page; Geofabrik's taginfo for Mexico (API).
- Computed on 18 November 2026: the 32 tight boxes, from the INEGI Marco Geoestadístico AGEE shapefile as described
  above. On 19 November 2026 the 0.15° margins were recomputed from those tight bounds, rounding outward (floor for
  west and south, ceiling for east and north) to 0.01°.
- Checked on 19 November 2026, for the review: the Overture address guide's per-country counts (US, Brazil, Mexico);
  the Microsoft Global ML Building Footprints repository (public, not archived; README licence CDLA-Permissive-2.0);
  INEGI's 2024 geographic compendium for Mexico City (1,494.3 km²; borders the State of Mexico and Morelos); INEGI's
  *Conociendo Tlaxcala* for Tlaxcala's borders (Hidalgo, Puebla and the State of Mexico); published coordinates for
  Isla Clarión, Isla Socorro and the mouth of the Suchiate. The SEPOMEX catalogue file was not re-downloaded; the
  Aguascalientes 20000 and Zacatecas 98000 examples were read from Correos de México's published state ranges.
- Seen only in search results: the INEGI hydrography page; the CONAGUA Ríos Principales WMS/WFS; the INEGI land-use
  and vegetation series; the CONAGUA dam count (~210) from search results of the catalog CSV.
- Not checked: the CONAGUA dam catalog CSV (redirect loop on `sih.conagua.gob.mx`); the CONAGUA licence; the INEGI
  land-use use-code table; the Copernicus DEM collection page (its licence was read in full for REGIONS-ES.md);
  whether Overture's buildings cover Mexico; the ISO 3166-2:MX codes against the ISO site; per-state Overture address
  counts (would need a DuckDB query); the national hospital catalogue's format or licence; CENAPRED or Protección
  Civil datasets with coordinates.