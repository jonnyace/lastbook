# Detailed maps for Chile: a proposal

> **Companion research from PR #140 (cd7d26c).** This retains the contributor’s DPA 2023 study and its paired Spanish text. It supplements [the existing Chile proposal](REGIONS-CL.md); it does not replace its provisional boxes or settle which bounds to build. The existing proposal keeps five separate Valparaíso island boxes and a Magallanes south edge of −56.60°. This study uses three island groups and its DPA-derived south edge of −56.5378°. The checks and calculations below are contributor-reported, not independently recomputed during integration. Nothing here is a delivered map.

This is a proposal for discussion, not a decision. It answers, for Chile, the questions [MAPS.md](MAPS.md) asks before
coverage can go beyond the United States: which open source replaces each federal list, under what licence, what a
"state" is there, and how addresses are written. It follows the shape of [REGIONS.md](REGIONS.md) and
[REGIONS-AR.md](REGIONS-AR.md), and is meant to feed the same design discussion (issues #23, #25 and #31). The
machine-readable version is [regions-cl-dpa2023-proposed.json](regions-cl-dpa2023-proposed.json), and a Spanish translation is
[REGIONS-CL-DPA2023.es.md](REGIONS-CL-DPA2023.es.md).

Nothing here changes the app, the engine or a build. No code reads the JSON, and none of this ships: builds package
`web/` and `content/` only.

**How it was checked.** The research was done on 17 November 2026. Each source carries one of three marks, as in
REGIONS-AR.md:

- **opened**: the dataset, record or licence page was fetched and read, including through a public API (the service is
  named in the JSON); "counted" is a count read the same way;
- **search only**: the fact was seen in a search result from the publisher's own site, but the page was not opened;
- **not verified**: the page could not be reached or read; the row says what is missing.

Chile has no single page like Argentina's IGN "Capas SIG". The layers are spread over IDE Chile (`geoportal.cl`), the
Ministry of Public Works (GeoMOP: Vialidad, DOH, DGA), IDE Minagri (CIREN, CONAF, ODEPA), INE's ArcGIS services, the
Library of Congress (BCN), MINSAL, MINEDUC and SENAPRED. Few of them state a licence, and that is the main finding of
this proposal.

## What a region is

Chile has 16 regions (Ñuble, the newest, was created in 2018). The proposal is one map per region, at the same level as
a US state.

### Codes

ISO 3166-2:CL gives each region two letters after `CL-`: `CL-RM` Metropolitana, `CL-VS` Valparaíso, `CL-BI` Biobío,
and so on. These were cross-checked against Natural Earth's admin-1 file (`iso_3166_2`), not against the ISO site, as
REGIONS.md also says for its codes.

- The prefix matters here as much as for Argentina. Three of the two-letter parts are US codes in `STATE_CODES`
  (`engine/address_search.py`): `AR` (La Araucanía and Arkansas), `CO` (Coquimbo and Colorado) and `MA` (Magallanes
  and Massachusetts). The others do not collide today, but nothing stops a future one.
- Chilean data sources use the CUT region code (Código Único Territorial), a two-digit string from `01` (Tarapacá) to
  `16` (Ñuble), not the ISO letters. Every official layer below carries CUT, so the JSON keeps both. CUT codes keep
  their leading zero; a source that stores them as numbers (`1101` for comuna `01101`) loses it.

### Three places that need a decision

- **Valparaíso's islands.** `CL-VS` includes Rapa Nui (Easter Island) and Salas y Gómez, 3,700 km out in the Pacific,
  and the Juan Fernández and Desventuradas islands. A single box around all of them would span 40 degrees of longitude
  of open ocean, and the terrain layer is cut by box. The proposal gives `CL-VS` one box for the mainland and three
  small boxes for the island groups (below), so a region can have more than one box. The other option is to make Rapa
  Nui its own map; ISO has no code for it.
- **The Chilean Antarctic Territory.** Magallanes legally includes the comuna Antártica (CUT `12202`). The official
  boundary layer leaves it out ("no incluye el Territorio Antártico Chileno"), and so does the box below. The claim
  overlaps with Argentina's and the United Kingdom's and is held in abeyance by the Antarctic Treaty, so like `AR-V` it
  belongs to the decision on disputed boundaries (item 6 of REGIONS.md).
- **The Southern Patagonian Ice Field.** Part of the border with Argentina, along Magallanes and just south of Aysén's
  southern tip, has not been demarcated. BCN's region file shows it as a separate polygon, "Zona sin demarcar"
  (codregion 0, 3,937 km²; opened), with extent -73.64, -49.81, -72.87, -49.17. Points spread across it fall in neither
  Aysén's nor Magallanes's polygon in the 2023 official layer, so that layer leaves it out too. The zone lies wholly
  inside the padded box of `CL-MA` and partly inside that of `CL-AI`.

### Boxes

The boxes were computed from the **official boundary layer, "División Política Administrativa 2023" (DPA 2023)**,
published by SUBDERE with the Instituto Geográfico Militar (IGM), the border agency DIFROL and INE through IDE Chile's
DPA working group (SIRGAS-Chile, EPSG:5360, scale 1:50,000). The file was downloaded from SUBDERE
(`ide.subdere.gov.cl/descargas/SHP/Limite_DPA_03082023.rar`) and its `REGIONES_v1` shapefile read on 17 November 2026.
It has 16 features, one per region, with `CUT_REG`, `REGION` and `SUPERFICIE`. Each box is the extent of every vertex
of the region's parts east of 76° W (all of them, except Valparaíso's Pacific islands), minus or plus 0.15° and rounded
outward to 0.01°, the same margin `map_sets.state` uses for US states. SIRGAS-Chile and WGS 84 differ by far less than
the rounding.

The last column is new for Chile: the region's own area (`SUPERFICIE`, km²) divided by the area of its unpadded box.
Chile is long and narrow, and its borders run along the Andes on a diagonal, so boxes hold a lot of sea and of
Argentina and Bolivia. In Magallanes, only about a quarter of the box is the region. For Valparaíso the area includes
its islands (about 275 km²), so its share is slightly high.

| Code | CUT | Name | Box (west, south, east, north) | Box with 0.15° margin | Share of box |
|---|---|---|---|---|---|
| `CL-AI` | 11 | Aysén del General Carlos Ibáñez del Campo | -75.6779, -49.1588, -71.0913, -43.6380 | -75.83, -49.31, -70.94, -43.48 | 0.49 |
| `CL-AN` | 02 | Antofagasta | -70.7430, -26.0623, -66.9905, -20.9345 | -70.90, -26.22, -66.84, -20.78 | 0.58 |
| `CL-AP` | 15 | Arica y Parinacota | -70.3776, -19.2291, -68.9113, -17.4984 | -70.53, -19.38, -68.76, -17.34 | 0.57 |
| `CL-AR` | 09 | La Araucanía | -73.5203, -39.6372, -70.8265, -37.5817 | -73.68, -39.79, -70.67, -37.43 | 0.59 |
| `CL-AT` | 03 | Atacama | -71.5919, -29.5350, -68.2631, -25.2858 | -71.75, -29.69, -68.11, -25.13 | 0.49 |
| `CL-BI` | 08 | Biobío | -73.9736, -38.4924, -70.9830, -36.4432 | -74.13, -38.65, -70.83, -36.29 | 0.40 |
| `CL-CO` | 04 | Coquimbo | -71.7178, -32.2825, -69.8091, -29.0366 | -71.87, -32.44, -69.65, -28.88 | 0.62 |
| `CL-LI` | 06 | Libertador General Bernardo O'Higgins | -72.0575, -35.0052, -70.0092, -33.8507 | -72.21, -35.16, -69.85, -33.70 | 0.68 |
| `CL-LL` | 10 | Los Lagos | -74.8485, -44.0671, -71.5810, -40.2361 | -75.00, -44.22, -71.43, -40.08 | 0.42 |
| `CL-LR` | 14 | Los Ríos | -73.7253, -40.6809, -71.5923, -39.2875 | -73.88, -40.84, -71.44, -39.13 | 0.65 |
| `CL-MA` | 12 | Magallanes y de la Antártica Chilena (without the Antarctic Territory) | -75.7232, -56.5378, -66.4156, -48.5941 | -75.88, -56.69, -66.26, -48.44 | 0.24 |
| `CL-ML` | 07 | Maule | -72.7857, -36.5438, -70.3117, -34.6844 | -72.94, -36.70, -70.16, -34.53 | 0.66 |
| `CL-NB` | 16 | Ñuble | -72.8847, -37.1985, -71.0070, -36.0054 | -73.04, -37.35, -70.85, -35.85 | 0.59 |
| `CL-RM` | 13 | Metropolitana de Santiago | -71.7155, -34.2910, -69.7698, -32.9219 | -71.87, -34.45, -69.61, -32.77 | 0.56 |
| `CL-TA` | 01 | Tarapacá | -70.2866, -21.6277, -68.4049, -18.9368 | -70.44, -21.78, -68.25, -18.78 | 0.72 |
| `CL-VS` | 05 | Valparaíso (mainland) | -71.8957, -33.9742, -69.9892, -32.0205 | -72.05, -34.13, -69.83, -31.87 | 0.42 |

The island boxes of `CL-VS`, from the same file, are the parts of the region west of 76° W:

| Island group | Parts | Box (west, south, east, north) | Box with 0.15° margin |
|---|---|---|---|
| Rapa Nui and Salas y Gómez | 171 | -109.4549, -27.2023, -105.3594, -26.4698 | -109.61, -27.36, -105.20, -26.31 |
| Juan Fernández | 19 | -80.8378, -33.8163, -78.7696, -33.6057 | -80.99, -33.97, -78.61, -33.45 |
| Desventuradas (San Félix, San Ambrosio) | 11 | -80.1214, -26.3510, -79.8606, -26.2731 | -80.28, -26.51, -79.71, -26.12 |

The Rapa Nui box reaches east to Salas y Gómez, an uninhabited islet 400 km away. A box for Rapa Nui alone would be much
smaller; that is part of the decision above.

**Cross-checks.**

- **OCHA's Chile COD-AB** (admin level 1, from BCN, CC BY-IGO, last modified 26 January 2026; opened on HDX) gives boxes
  within 0.07° of these in 15 of 16 regions. The exception is Magallanes, 0.56° further north at its southern edge: the
  OCHA layer leaves out the Diego Ramírez islands (about 56.5° S), which DPA 2023 includes.
- **Natural Earth 1:10m admin-1** (version 5.1.1, public domain) is within 0.21° in 12 regions, but off by 0.29° in
  Biobío and 0.43° in La Araucanía (it puts Isla Mocha, which belongs to Biobío, in La Araucanía), 0.44° in Los Lagos
  and 0.62° in Magallanes (no Diego Ramírez). So DPA 2023 is the layer to use, as IGN's was for Argentina.

## Sources, layer by layer

| Layer (file) | US source today | Proposed for Chile | Publisher | Licence | Checked |
|---|---|---|---|---|---|
| Terrain (`terrain.sqlite`) | USGS 3DEP | Copernicus DEM GLO-30, as proposed for Guyana | ESA / Airbus | Copernicus WorldDEM-30 | as in REGIONS.md |
| Terrain, islands | | DEM of Isla de Pascua (4 m) and Juan Fernández (2 m), TIFF | IDE Chile catalogue | none stated | opened (record) |
| Water (`water.sqlite`), rivers | NHD | "Hidrografía de la región de Arica a la región de Los Lagos" (2024 edition), 1:25,000, with Strahler order and DGA basin codes | IDE Chile hydrography working group | none stated | opened (record; WFS count of the 2021 edition, 122,852 features) |
| Water, lakes | NHD | Catastro de Lagos (2,067 lake and lagoon polygons, with name, type and altitude) | Dirección General de Aguas (DGA) | none stated | opened (file read) |
| Water, canals | NHD | Canales CNR (13,166 irrigation canals) | Comisión Nacional de Riego / DOH, MOP | GeoMOP terms (free, no named licence) | opened (API count) |
| Water, Aysén and Magallanes; fallback | | OSM waterways and water areas (Geofabrik's Chile extract) | OSM contributors | ODbL | opened (file headers) |
| Dams | NID | Catastro de Embalses (1,370 reservoirs, with use and, for some, wall height; "updated to December 2015") | Dirección de Obras Hidráulicas (DOH) with DGA, MOP | GeoMOP terms | opened (API count) |
| Crops (`crops.sqlite`) | USDA Cropland Data Layer | Catastro Frutícola: fruit plantation polygons by species, including berries, 94,731 polygons in 14 regions | CIREN (IDE Minagri) | **none stated** | opened (API counts) |
| Crops, open fallback | | MapBiomas Chile, Collection 2 (annual land cover) | MapBiomas Chile | CC BY 4.0 | opened (terms) |
| Buildings (`buildings.sqlite`) | Microsoft US footprints, OSM heights | Google Open Buildings v3; Microsoft Global ML Building Footprints (330 files for Chile) to fill gaps; OSM heights | Google; Microsoft; OSM contributors | CC BY 4.0 or ODbL (at the user's choice); CDLA Permissive 2.0; ODbL | opened (country lists); coverage not measured |
| Places (`places.sqlite`) | GNIS, Census gazetteers, OSM | Census 2017 cities (270), towns (289), villages (727) and hamlets (3,669); Census 2024 locality names (9,378 points) and entities (28,415); IGM place names from the 1:50,000 maps (105,440 points); OSM named places | INE; IGM; OSM contributors | "Datos de uso público" (2017); none stated (2024, IGM); ODbL | opened (API counts) |
| Roads (base map) | OSM | OSM, as today; Red Vial Chile (14,266 road segments with route number and surface, updated to about 2017) to fill rural gaps | OSM contributors; Dirección de Vialidad, MOP | ODbL; GeoMOP terms | opened (API count) |
| Addresses (`addresses/<code>.sqlite`) | Overture addresses | Overture addresses: 4,199,023 Chilean rows from INE, distributed by AddressForAll (also in OpenAddresses) | Overture Maps Foundation / INE | CC BY 4.0 as Overture lists it (see "Licence notes") | opened; counted |
| Addresses, street ranges | | Maestro de Calles 2018: 395,480 street segments with fields for left and right door-number ranges, in 64 comunas | INE and IDE Chile's street working group | "Datos de uso público" | opened (API counts) |
| Points of interest (`poi` rows) | OSM | OSM, plus the health, school, emergency and energy lists below | | | below |

### Help and resource points

| Kind | Proposed source | Publisher | Licence | Checked |
|---|---|---|---|---|
| Health | Establecimientos de Salud: 5,837 establishments, 5,411 with coordinates, 827 with an emergency service; types include rural health posts (1,186), CESFAM (607), SAPU (272) and hospitals (234); address split into street type, name and number | Ministerio de Salud (DEIS) | **CC0** | opened (file read) |
| Pharmacies | Farmacias en Chile: 1,925 pharmacies, 1,805 with coordinates | Ministerio de Salud | CC BY | opened (service read) |
| Fire stations | "BOMBEROS" layer of SENAPRED's Visor Chile Preparado: 1,418 fire companies with name, address and phone | SENAPRED | **none stated** | opened (count, fields) |
| Police | "CARABINEROS" layer of the same viewer: 883 stations | SENAPRED | **none stated** | opened (count, fields) |
| Schools | Directorio Oficial de Establecimientos Educacionales 2026: 12,004 schools in operation, 11,966 with coordinates, which MINEDUC calls "reference only" | Ministerio de Educación | **none stated** | opened (file read) |
| Fuel | "Estación de Servicio" layer of IDE Energía: 1,793 stations with the fuels each sells; source CNE, updated 1 April 2026 | Ministerio de Energía | none stated on the service (the catalogue record linking it says cc-by) | opened (count, fields) |
| Power | Substations (1,217), transmission lines (1,128, from the Coordinador Eléctrico Nacional) and power plants, same service | Ministerio de Energía | as above | opened (counts) |
| Rural drinking water | Agua Potable Rural systems: 2,213 rural water committees and cooperatives, 2,119 with coordinates, data as of December 2020 | Ministerio de Obras Públicas | **CC BY-NC** (`cc-nc`) | opened (file read) |
| Drinking water taps | OSM `amenity=drinking_water` (274) and `man_made=water_tap` (44) | OSM contributors | ODbL | counted (OSM data of 15 July 2026, on an Overpass mirror) |
| Tsunami meeting points | SENAPRED: 1,544 meeting points, 2,842 evacuation routes, 523 safety lines and 354 areas to evacuate, in the 15 coastal regions; last edited 29 October 2026 | SENAPRED | **none stated** | opened (counts, fields) |
| Volcano meeting points | SENAPRED: 184 meeting points, 260 evacuation routes, 3,499 volcanic hazard polygons, 104 active volcanoes | SENAPRED | **none stated** | opened (counts, fields) |
| Shelters, PDI stations, airfields | No national open list found; OSM has 849 `emergency=assembly_point` and 385 `aeroway=aerodrome` | OSM contributors | ODbL | counted (as above) |

### Hazards

Chile's map needs something the US map does not lead with: tsunami and volcano information. These sources were found.

- **SHOA tsunami flood charts (CITSU).** The navy's hydrographic service publishes the charts of how far a tsunami would
  reach, from Arica to Puerto Williams, as PDF and KMZ. SHOA's page refused automated reading (HTTP 403), so the
  licence is **not verified**. Copies of the charts on ArcGIS Online carry conflicting notices: two say "all rights
  reserved, no part ... may be reproduced ... without SHOA's prior written permission" (citing the copyright law,
  Ley 17.336), two say "Dato abierto", and SHOA's own 2015 entry on datos.gob.cl is `cc-nc`. They should be treated
  as not redistributable until SHOA confirms.
- **SENAPRED's tsunami and volcano layers** (table above) cover the same need with meeting points and evacuation areas,
  and are current. They state no licence. Their 104 active volcanoes and SERNAGEOMIN's 87 below were not reconciled.
- **SERNAGEOMIN's volcano ranking 2023** (opened, PDF): 87 active volcanic systems with coordinates and risk scores. The
  top three are Villarrica, Calbuco and Llaima. No licence is stated. SERNAGEOMIN's map server (hazard maps and its
  landslide catalogue) could not be reached (connection timed out); **not verified**.
- No national open flood layer was found.

Notes:

- **Terrain.** No official open national elevation model like Argentina's MDE-Ar was found. CIREN offers 12.5 m
  regional mosaics reprocessed from the Alaska Satellite Facility's ALOS PALSAR product, with no licence on the
  records; ASF's terms were not checked. Copernicus GLO-30 is the simpler choice.
- **Water.** The official 1:25,000 river network stops at Los Lagos. Aysén and Magallanes, a third of the country and
  most of its fjords and glaciers, would come from OSM or from BCN's older "Red hidrográfica" (free use with credit;
  opened).
- **Crops.** CIREN's Catastro Frutícola is a much closer match to what `tools/build_crops.py` keeps (orchards,
  vineyards, berries) than anything found for Argentina: a polygon inventory of fruit plantations by species, such as
  "ARANDANO AMERICANO". But it states no licence, and each polygon carries the property's tax roll number (`rolpredi`),
  which a pack should drop. The CC BY version on datos.gob.cl (ODEPA) is a table by comuna with no geometry. Wine
  vineyards are a separate SAG survey, found only as reports (search only). MapBiomas Chile is CC BY 4.0; whether its
  classes separate orchards and vineyards was not checked, and its GeoTIFF downloads were "temporarily suspended".
- **Addresses.** Unlike Argentina, Chile has address points. See "How addresses are written".
- **Health.** MINSAL's list is the best-licensed layer found (CC0), current to November 2026, and marks which
  establishments have an emergency service. That is the field a person needs most on a bad day.
- **SENAPRED's layers** are the richest emergency data found, and they are the same layers people in Chile already see
  in the government's "Chile Preparado" viewer. They are public on ArcGIS Online, but the four items checked have an
  empty licence field. Under the rule REGIONS-AR.md uses ("a dataset with no stated licence is treated here as not
  yet usable"), they need SENAPRED's written permission.

## Licence notes and attribution

- **CC0** (MINSAL health establishments). No credit required; credit is still good practice.
- **datos.gob.cl.** Its terms of use (Resolución Exenta Nº 469 of 2024; opened) make CC0 the default, with PDDL, CC BY
  4.0 and ODC-By also allowed. Each record still carries its own licence, and many older (2015) geodata records are
  `cc-nc`, which the portal titles "Creative Commons Non-Commercial (Any)" and links to CC BY-NC 2.0. The licence must
  be read record by record.
- **CC BY-NC** (`cc-nc`: rural drinking water systems; SHOA's 2015 entry). Non-commercial. The same question as IGN's
  terms in REGIONS-AR.md ("free and at no cost, commercial use only in derivative works"): fine for free packs, but a
  pack holding it could not be sold, even by someone else.
- **CC BY 4.0** (MapBiomas Chile, Google Open Buildings): credit the publisher, link the licence, say if changed.
- **ODbL** (OSM, and Microsoft footprints if taken through Overture's buildings theme): as for the US map.
- **CDLA Permissive 2.0** (Microsoft footprints downloaded directly from its dataset list): a pack that shares them
  must make the text of the licence available with them.
- **INE.** INE's open-data terms put its site's content under **CC BY-SA 4.0** (opened). Share-alike would bind any
  database built from it. INE's 2017 census layers say only "Datos de uso público", and its 2024 layers state nothing.
  Which of these applies to each layer is a question for INE; the JSON assigns CC BY-SA 4.0 to no layer yet.
- **INE addresses through Overture.** Overture lists them as "© Instituto Nacional de Estadísticas. Available under CC
  BY 4.0. Distributed by AddressForAll." AddressForAll's own record (opened) shows how that came about: INE did not
  publish the file, AddressForAll obtained it through a request under the Transparency Law, and INE later answered,
  in AddressForAll's translation, that the data "are public and can be used for any purposes ... You only need to cite
  the source as: INE CHILE". AddressForAll's own record calls the licence "Implied CC-BY", and OpenAddresses records
  it as "CHILE GOVERMENT TRANSPARENCY LAW" (sic). It looks usable with the credit "INE Chile", but it rests on a
  letter, not a published licence, and the maintainers should know that.
- **BCN** (opened): free use, credit "Biblioteca del Congreso Nacional de Chile"; referential only.
- **IDE Chile and GeoMOP.** IDE Chile's catalogue asks users to cite the providing institution, and its footer says "all
  rights reserved". GeoMOP says its data is free of charge. Neither names a licence.
- **No licence stated** (needs the publisher's permission before use): SENAPRED's layers, CIREN's fruit survey and DEMs,
  MINEDUC's school directory, SERNAGEOMIN's ranking, DGA's lakes, IGM's place names and IDE Energía's service.
- **CC BY-IGO** (OCHA's boundaries, used only as a cross-check): credit OCHA and its source, BCN.
- **DIFROL and maps of Chile's borders.** This is the most important legal point for Chile, comparable to IGN's terms
  for Argentina. The DPA 2023 metadata (opened) says that, under DFL Nº 5 of 1967, DS Nº 566 of 1970 and DFL Nº 83 of
  1979, every publication whose circulation DIFROL authorises must carry a fixed legend, and that maps that show
  Chile's borders do not commit the Chilean state. In a separate sentence, which cites no law, it adds that "the
  publications and products derived from it must likewise be reviewed and validated by DIFROL".
  The documents disagree on which resolution the legend cites: the metadata says Nº 87 of 2023, the description file
  in the same archive says Nº 87 of 2019, and the IDE Chile record says Nº 50 of 2019. The archive itself states no
  licence, while datos.gob.cl lists IDE Chile's DPA 2023 download in a `cc-by` catalogue record
  (`categoria-geoespacial-limites-y-fronteras`). Computing a box from the layer is arguably not publishing a map, but
  showing Chile's borders in the app may be. This is a question for the maintainers and, likely, for DIFROL. Lastbook's
  world base map already draws country outlines (`web/world-context.json`), and the map credits Natural Earth
  (`MAP_CREDIT` in `packaging/build_packs.py`).

## How addresses are written

- **Order.** Street, then number, then the rest (apartment, floor, block), then comuna and region: "Avenida Palena 1084,
  Depto. 505, 9180794 Estación Central" (UPU addressing sheet for Chile, 2017; opened). As in Argentina, the number
  comes *after* the street, the opposite of the US order the parser expects.
- **Street words.** *Avenida* (*Av.*, *Avda.*), *Calle*, *Pasaje* (*Psje.*, very common in housing estates),
  *Camino*, *Ruta*, *Carretera*. Villa and población names are part of the address but not of the street. Rural
  addresses often have no number: "S/N" (sin número), "Km 15", "Parcela 31", "Lote 3", "Sitio 14". Street names often
  hold dates ("21 de Mayo", "10 de Julio"), which people also write in words.
- **Postal code.** Seven digits, written before the comuna: three for the delivery area (usually a comuna) and four for
  one side of a block, as in `8720019 QUILICURA`. Where a comuna has no block-level codes, its code ends in `0000`
  (UPU sheet; opened). Correos de Chile offers a look-up page only; no open postcode file was found.
- **What Overture has.** 4,199,023 rows in release 2026-10-21.0 (counted with DuckDB on 17 November 2026), in all 16
  regions but only 311 of the 346 comunas, and none on Rapa Nui or Juan Fernández. 3,988,122 have both a number and a
  street, which is what `tools/build_addresses.py` keeps. None has a postcode. Street names are in capitals, mostly
  without a street word. The region is in `address_levels[1]` ("METROPOLITANA DE SANTIAGO", "DE VALPARAÍSO") and the
  comuna in `address_levels[2]`. Per region, from 1,593,107 in Metropolitana to 24,715 in Aysén (in the JSON).
- **What INE's street file adds.** The Maestro de Calles 2018 has 395,480 street segments; 277,295 carry a
  door-number range on at least one side, and 162,601 on both. But it covers only 64 comunas, and 186,561 of its
  segments (47%) are in Metropolitana. It could complement Overture by interpolation, as REGIONS-AR.md proposes for
  Argentina's street blocks, but not replace it.
- **What the current code does with that.**
  - `tools/build_addresses.py` selects `country = 'US'` only, so today it would take no Chilean rows. Once that filter
    changes, taking the first two letters of the region name (`state.upper()[:2]`) would give `DE` (Delaware) for 15
    regions, because their names start with "DE" or "DEL", and `ME` (Maine) for Metropolitana. Chile needs the
    region mapped to `CL-..` by name or CUT code.
  - `engine/address_search.py` treats a query as an address only when it starts with a number, so "Avenida Palena
    1084", "S/N" and "Parcela 31" are not looked up as addresses at all. It reads a postcode only as five digits
    (`\d{5}`), knows English street words only, and in "38 B" takes the "B" as part of the street.
  - The normaliser replaces letters outside a to z with spaces instead of folding them, so "Ñuble" becomes "uble" and
    "Peñalolén" becomes three words, "pe alol n". That is worth fixing for every language, not only Spanish.

## Still undecided

Each of these needs the maintainers' decision before any code changes. The first three are shared with REGIONS.md and
REGIONS-AR.md.

1. **Codes in setup.** Whether hyphenated codes such as `CL-RM` are acceptable as a manifest `id`, in `map-set.json`
   and in `Lastbook-Map-<id>.zip`, and how setup lists 16 Chilean regions.
2. **The box rule**, as in REGIONS.md, plus one question new with Chile: whether a region may have **more than one
   box** (Valparaíso's mainland and its three island groups), or whether Rapa Nui gets its own map.
3. **Disputed and undemarcated boundaries**: the Chilean Antarctic Territory, and the undemarcated stretch of the
   Southern Patagonian Ice Field.
4. **DIFROL's rule** on maps that show Chile's borders: whether a map pack that draws them needs DIFROL's review, and
   where the legend would go. This may need a question to DIFROL itself.
5. **Layers with no stated licence**, chiefly SENAPRED's tsunami and volcano layers and CIREN's fruit survey: whether
   to ask the publishers for written permission, and who asks.
6. **Non-commercial and share-alike licences**: CC BY-NC (rural water systems) and INE's CC BY-SA 4.0, as for IGN's
   terms in REGIONS-AR.md.
7. **Address search** for Chile: street-first order, seven-digit postcodes, Spanish street words, numbers such as
   "S/N" and "Parcela 31", and folding ñ and accents.
8. **New point and area kinds**: tsunami meeting points and areas to evacuate, volcano hazard areas, rural water
   systems, and health establishments with an emergency service, and how they map to the kinds `web/map.js` already
   draws.

## What was checked, and what was not

- Opened or downloaded on 17 November 2026: the DPA 2023 archive from SUBDERE (region shapefile and its metadata,
  description and change documents); OCHA's Chile COD-AB on HDX; Natural Earth admin-1 5.1.1; BCN's map library and its
  region file; IDE Chile catalogue records for DPA 2023, the hydrography, the island DEMs and CIREN's DEMs; DGA's lake
  file; MINSAL's health establishment file; MINEDUC's 2026 school directory; MapBiomas Chile's terms; Google's Open
  Buildings country list; Microsoft's dataset list; Overture's attribution page; AddressForAll's Chile record and
  OpenAddresses' Chile source; the UPU addressing sheet; SERNAGEOMIN's 2023 ranking; datos.gob.cl's terms of use; INE's
  open-data terms.
- Read through public APIs on 17 November 2026: datos.gob.cl's CKAN API (licences and file lists), IDE Chile's WFS
  (river count), MOP's ArcGIS services (canals, reservoirs, roads), CIREN's ArcGIS service (fruit survey), INE's ArcGIS
  services (census places, Maestro de Calles), IGM's ArcGIS services (place names), IDE Energía's service (fuel and
  power), MINSAL's pharmacy service, and SENAPRED's ArcGIS layers and item records.
- Counted on 17 November 2026: Overture's Chilean addresses (DuckDB on release 2026-10-21.0); OSM tags on an Overpass
  mirror whose data was dated 15 July 2026.
- Computed on 17 November 2026: the 16 boxes and the three island boxes, from DPA 2023, cross-checked against OCHA and
  Natural Earth.
- Seen only in search results from the publishers' own sites: SAG's vineyard survey, SERNAGEOMIN's hazard map shop and
  map services.
- Not verified: the ISO 3166-2:CL codes against the ISO site; SHOA's own pages (403) and the CITSU licence;
  SERNAGEOMIN's map server (unreachable); DIFROL's own site; whether CIREN, DGA, IGM and INE publish terms for the
  layers above somewhere other than the records read; ASF's ALOS PALSAR terms; MapBiomas Chile's classes; building
  coverage measured in buildings; national lists of shelters, PDI stations and airfields; CNE's fuel API (needs a
  token); and OSM address coverage (the Overpass query timed out, as it did for Argentina).
