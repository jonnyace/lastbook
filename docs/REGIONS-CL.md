# Detailed maps for Chile: a proposal

This is a proposal for discussion, not a decision. It answers, for Chile, the questions [MAPS.md](MAPS.md) asks before
coverage can go beyond the United States: which open source replaces each federal list, under what licence, what a
"state" is there, and how addresses are written. It follows the shape of [REGIONS.md](REGIONS.md),
[REGIONS-AR.md](REGIONS-AR.md) and [REGIONS-DE.md](REGIONS-DE.md) and is meant to feed the same design discussion
(issues #23, #25 and #31). The machine-readable version is [regions-cl-proposed.json](regions-cl-proposed.json).

Nothing here changes the app, the engine or a build. No code reads the JSON, and nothing here ships: builds package
`web/` and `content/` only.

**How things were checked.** Research was done on 17 November 2026. Each source carries one of three marks:

- **opened**: the page or file itself was opened and read;
- **search only**: the fact was seen in a search result from the publisher's site, but the page itself was not opened;
- **not checked**: the page could not be reached or read; the row says what is missing.

## Additional DPA 2023 research

[PR #140’s companion study](REGIONS-CL-DPA2023.md), its [paired Spanish text](REGIONS-CL-DPA2023.es.md), and [source metadata](regions-cl-dpa2023-proposed.json) add contributor-reported DPA 2023 extents, cross-checks and per-layer provenance. They do not replace the provisional boxes below. In particular, the existing proposal keeps five separate Valparaíso island boxes and Magallanes’s wider −56.60° southern edge; the companion groups the islands into three boxes and reports −56.5378° from DPA 2023. Choosing final build bounds still needs source-geometry checking. Neither proposal is read by the app or ships a map.

## Why Chile is a useful case

1. **Overture already carries 4,199,023 Chilean addresses** (`CL` in Overture's address theme guide, opened on
   17 November 2026), so address search has an open source on day one rather than a gap.
2. **Extreme north–south shape and Pacific islands.** Continental Chile is roughly 4,300 km long from north to south
   (`-17.5°` to `-56.0°` latitude) and only about 180 km wide on average, while Rapa Nui (Easter Island, `-109.35°`
   longitude) and the Juan Fernández archipelago sit thousands of kilometres west in the Pacific. A single country-wide
   bounding box spans `-113.22°` to `-65.51°` longitude and is mostly ocean, so Chile tests both per-region cuts and
   offshore-island boxes directly.
3. **Borders with Argentina ([REGIONS-AR.md](REGIONS-AR.md)).** Almost the whole eastern edge of Chile meets Argentina's
   Andean provinces (`AR-Y`, `AR-A`, `AR-K`, `AR-F`, `AR-J`, `AR-M`, `AR-Q`, `AR-R`, `AR-U`, `AR-Z`, `AR-V`), so the
   two proposals test cross-border margin overlap along the Andes and in Tierra del Fuego.

## What a region is

Chile is divided into **16 regions** (*regiones*), each subdivided into provinces (*provincias*, 56 in all) and communes
(*comunas*, 346 in all). The proposal is **one map set per region, 16 in all**, matching the level of US states,
Argentine provinces ([REGIONS-AR.md](REGIONS-AR.md)) and German Länder ([REGIONS-DE.md](REGIONS-DE.md)).

### Codes

ISO 3166-2:CL assigns each region a two-letter code after `CL-`: `CL-RM` (Región Metropolitana de Santiago), `CL-VS`
(Valparaíso), `CL-BI` (Biobío) and so on. Chile also uses official Roman/numeric identifiers (`I` to `XVI`, plus `RM`)
and two-digit *Código Único Territorial* (CUT) prefixes (`01` to `16`), assigned by the *Subsecretaría de Desarrollo
Regional y Administrativo* (SUBDERE) and the *Instituto Nacional de Estadísticas* (INE).

- A bare `CL` is not in `STATE_CODES` (`engine/address_search.py`; California is `CA` and Colorado is `CO`), and
  hyphenated `CL-XX` codes never collide with a two-letter US state code.
- Three two-letter suffixes on their own collide with US state codes: `MA` (Magallanes / Massachusetts), `AR`
  (La Araucanía / Arkansas) and `CO` (Coquimbo / Colorado). The `CL-` prefix must stay part of the code everywhere.

### Boxes

Geofabrik publishes Chile as a single country extract (`chile-261116.osm.pbf` is 352,124,743 bytes, about 352 MB or
336 MiB; `chile-261116-free.gpkg.zip` is 774,826,582 bytes, about 775 MB or 739 MiB, opened on 17 November 2026) with no
sub-region extracts on Geofabrik. Its clipping polygon (`chile.poly`, 132 vertices, opened) has outer bounds
`west = -113.2233, south = -58.4519, east = -65.5141, north = -17.4574` because it wraps Rapa Nui and Sala y Gómez in the
same polygon as the mainland, with a wide margin around the islands: Rapa Nui is at about `-109.35°`, so the
polygon's west edge lies nearly 4° beyond it.

The per-region boxes below are approximate, not checked against boundary polygons. For `CL-VS` (Valparaíso), the box
shown is **continental mainland only**. The offshore islands have separate provisional boxes below and in the JSON's
`CL-VS.island_boxes`; they are not inside the mainland box. For `CL-MA`, the south edge is widened to `-56.60°` to
include the Diego Ramírez group, whose southernmost islet reaches about `-56.54°`.

All boxes must be recomputed from BCN (*Biblioteca del Congreso Nacional de Chile*) or IDE Chile / INE regional
boundary polygons before a build tool cuts packs. Checking reference points is not a check of every coastline.

| Code | CUT | Name | Approximate region box, mainland only for CL-VS (west, south, east, north) | Box with 0.15° margin |
| --- | --- | --- | --- | --- |
| `CL-AP` | 15 | Arica y Parinacota | -70.38, -19.23, -68.91, -17.50 | -70.53, -19.38, -68.76, -17.35 |
| `CL-TA` | 01 | Tarapacá | -70.29, -21.64, -68.40, -18.94 | -70.44, -21.79, -68.25, -18.79 |
| `CL-AN` | 02 | Antofagasta | -70.75, -26.06, -67.00, -20.93 | -70.90, -26.21, -66.85, -20.78 |
| `CL-AT` | 03 | Atacama | -71.59, -29.54, -68.26, -25.29 | -71.74, -29.69, -68.11, -25.14 |
| `CL-CO` | 04 | Coquimbo | -71.72, -32.28, -69.81, -29.04 | -71.87, -32.43, -69.66, -28.89 |
| `CL-VS` | 05 | Valparaíso (continental) | -71.86, -33.90, -70.00, -32.02 | -72.01, -34.05, -69.85, -31.87 |
| `CL-RM` | 13 | Metropolitana de Santiago | -71.72, -34.29, -69.77, -32.92 | -71.87, -34.44, -69.62, -32.77 |
| `CL-LI` | 06 | Libertador General Bernardo O'Higgins | -72.07, -35.01, -70.01, -33.85 | -72.22, -35.16, -69.86, -33.70 |
| `CL-ML` | 07 | Maule | -72.79, -36.55, -70.32, -34.69 | -72.94, -36.70, -70.17, -34.54 |
| `CL-NB` | 16 | Ñuble | -72.90, -37.20, -71.00, -36.01 | -73.05, -37.35, -70.85, -35.86 |
| `CL-BI` | 08 | Biobío | -73.98, -38.49, -70.98, -36.44 | -74.13, -38.64, -70.83, -36.29 |
| `CL-AR` | 09 | La Araucanía | -73.53, -39.64, -70.83, -37.59 | -73.68, -39.79, -70.68, -37.44 |
| `CL-LR` | 14 | Los Ríos | -73.73, -40.68, -71.58, -39.27 | -73.88, -40.83, -71.43, -39.12 |
| `CL-LL` | 10 | Los Lagos | -74.85, -44.07, -71.58, -40.23 | -75.00, -44.22, -71.43, -40.08 |
| `CL-AI` | 11 | Aysén del General Carlos Ibáñez del Campo | -75.68, -49.16, -71.09, -43.64 | -75.83, -49.31, -70.94, -43.49 |
| `CL-MA` | 12 | Magallanes y de la Antártica Chilena (American sector, including Diego Ramírez) | -75.73, -56.60, -66.42, -48.60 | -75.88, -56.75, -66.27, -48.45 |

### Provisional offshore boxes for `CL-VS`

These broad boxes surround published island positions; they are not official bounds. The source pages were opened
on 17 November 2026. A future multi-box cut must include both the mainland `box` and every `island_boxes` entry,
not just the 16 top-level region boxes. No current build reads this proposal.

| Island or group | Provisional box (west, south, east, north) | Box with 0.15° margin | Position source |
| --- | --- | --- | --- |
| Rapa Nui | -109.50, -27.25, -109.20, -27.00 | -109.65, -27.40, -109.05, -26.85 | [Easter Island](https://en.wikipedia.org/wiki/Easter_Island) |
| Sala y Gómez | -105.39, -26.50, -105.33, -26.44 | -105.54, -26.65, -105.18, -26.29 | [Salas y Gómez](https://en.wikipedia.org/wiki/Salas_y_G%C3%B3mez) |
| Robinson Crusoe and Santa Clara | -79.08, -33.78, -78.72, -33.56 | -79.23, -33.93, -78.57, -33.41 | [Juan Fernández Islands](https://en.wikipedia.org/wiki/Juan_Fern%C3%A1ndez_Islands) |
| Alejandro Selkirk | -80.87, -33.86, -80.70, -33.69 | -81.02, -34.01, -80.55, -33.54 | [Juan Fernández Islands](https://en.wikipedia.org/wiki/Juan_Fern%C3%A1ndez_Islands) |
| Desventuradas | -80.18, -26.40, -79.84, -26.22 | -80.33, -26.55, -79.69, -26.07 | [Desventuradas Islands](https://en.wikipedia.org/wiki/Desventuradas_Islands) |

The Desventuradas box includes the reference positions of San Félix, San Ambrosio, Islote González and Roca Catedral.
The [Diego Ramírez Islands](https://en.wikipedia.org/wiki/Diego_Ram%C3%ADrez_Islands) are in `CL-MA`, not `CL-VS`;
the widened southern region box includes their reference position and Águila Islet at `56°32′15″ S`.

Three decisions are tied to the boxes:

- **`CL-RM` inside `CL-VS` and `CL-LI`.** The Santiago Metropolitan Region is landlocked between Valparaíso and
  O'Higgins, so their rectangular boxes overlap significantly around Santiago and Valparaíso.
- **Offshore islands (`CL-VS`).** Rapa Nui, Sala y Gómez, the Juan Fernández islands and the Desventuradas belong
  administratively to Valparaíso (`CL-VS`). Keeping their boxes separate avoids pulling the ocean between them and
  the mainland into one rectangle. Whether they ship in one pack or as add-ons still needs a decision.
- **Southern Patagonian Ice Field and Antarctic claims.** As noted in [REGIONS-AR.md](REGIONS-AR.md), a short section of
  the Southern Patagonian Ice Field border between `CL-AI`/`CL-MA` and `AR-Z` (Santa Cruz) is not fully demarcated, and
  `CL-MA` excludes Antarctic territorial claims south of 60° S, matching `AR-V` in [REGIONS-AR.md](REGIONS-AR.md).

## Sources, layer by layer

| Layer (file) | US source today | Proposed for Chile | Publisher | Licence | Mark |
| --- | --- | --- | --- | --- | --- |
| Roads, water, land (base map) | OSM extract | OSM extract, `chile-latest.osm.pbf` (352 MB / 336 MiB; `.gpkg.zip` is 775 MB / 739 MiB) | OSM contributors via Geofabrik | ODbL 1.0 | opened |
| Points of interest (`poi`) | OSM | OSM | OSM contributors | ODbL 1.0 | opened |
| Addresses (`addresses/<code>.sqlite`) | Overture addresses | **Overture addresses (`CL`, 4,199,023 records)** | Overture Maps Foundation, from Instituto Nacional de Estadísticas (INE), distributed by AddressForAll | CC BY 4.0; Overture's credit: "© Instituto Nacional de Estadísticas" | opened |
| Places (`places.sqlite`) | GNIS, Census, OSM | OSM named places; BCN / IDE Chile / INE administrative names (regiones, provincias, comunas, localidades) | OSM contributors; BCN / IDE Chile / INE | ODbL 1.0; CC BY 4.0 on BCN cartography (search only) | search only |
| Terrain (`terrain.sqlite`) | USGS 3DEP | Copernicus DEM GLO-30 (1 arc-second, ~30 m) | ESA / Airbus | Copernicus WorldDEM-30 licence | as in REGIONS.md |
| Water: reservoirs, lakes, rivers (`water.sqlite`) | NHD, NID | OSM `water=reservoir`, `natural=water` and `waterway=dam`; DGA (*Dirección General de Aguas*, MOP) hydrographic inventory if licence is confirmed | OSM contributors; DGA | ODbL 1.0; DGA licence not checked | opened for OSM; not checked for DGA |
| Crops (`crops.sqlite`) | USDA CDL | ESA WorldCover 2021 (land cover, 10 m) for the first build; ODEPA / CIREN fruit-orchard (*catastro frutícola*) layers if open licence is confirmed | ESA WorldCover consortium; ODEPA / CIREN | CC BY 4.0; CIREN licence not checked | as in REGIONS.md |
| Buildings (`buildings.sqlite`) | Microsoft US footprints | Overture buildings or Microsoft Global ML Building Footprints + OSM building heights | Overture; Microsoft; OSM contributors | Overture buildings and OSM heights: [ODbL 1.0](https://docs.overturemaps.org/attribution/#buildings); direct Microsoft footprints: [CDLA Permissive 2.0](https://github.com/microsoft/GlobalMLBuildingFootprints#license) | search only |

Notes:

- **Earthquake, tsunami and volcanic shelter layers.** Chile is one of the most seismically active countries in the
  world. SENAPRED (formerly ONEMI) publishes tsunami evacuation zones, safe assembly points (*puntos de encuentro*) and
  flood/volcanic hazard maps through IDE Chile and geoportals. Their reuse licence was not opened; if open, tsunami
  assembly points map cleanly to the `shelter` or `community` help layer in `web/map.js`.
- **Water scarcity and rural *APR* systems.** In central and northern Chile, rural drinking water often comes from
  *Agua Potable Rural* (APR, now *Servicios Sanitarios Rurales* under MOP/DOH) wells and tanks. Whether DGA/DOH lists
  carry an open licence was not checked.

## How addresses are written

Chilean street addresses put the **street name before the house number**, followed by optional unit, barrio, villa,
población or sector, the *comuna* (municipality), and sometimes the city. Names alone do not identify these roles.
These examples are made up, not household addresses:

```
Los Castaños 742, El Bosque, La Florida, Santiago
10 de Julio 1234, Comuna Ejemplo
Pasaje 3 1234, Comuna Ejemplo
Calle Ejemplo S/N, Sector Ejemplo, Comuna Ejemplo
```

In the first example, El Bosque is a villa in La Florida, but is also a comuna name elsewhere. Santiago can mean the
comuna, city, province or region; choosing the rightmost known comuna would wrongly select Santiago here.

Proposed search rules, to discuss before changing `engine/address_search.py`:

1. **Street and number first.** Use the first comma-separated part, with its **last number** as the house number:
   `10 de Julio 1234` and `Pasaje 3 1234` must retain the numbers in the street name. Accept `S/N` (*sin número*,
   no number) as a separate case; it must not become a made-up house number. The current parser expects a number first.
2. **Match place hints; do not classify them.** Treat the remaining parts as place hints, not as fixed barrio, comuna
   or city slots. Find candidates by street and number, then rank by how many hints match each record's comuna or
   locality. An unmatched villa name or trailing city must not force a different comuna. Where candidates still tie,
   keep the choice visible rather than guessing.
3. **Spanish street words.** Names use *Calle*, *Avenida* (*Av.* or *Avda.*), *Pasaje* (*Pje.*), *Camino*, *Paseo* or
   *Ruta*, plus words such as `de`, `del`, `la`, `los` and accents. The builder's ASCII-only `norm()` needs checking too.
4. **Seven-digit postal codes.** Chile uses 7-digit codes (for example `8320000`), often omitted in everyday addresses.
   Preserve all seven digits when given; do not require a code or assume the final place hint is the comuna.

### Address-builder limits

`tools/build_addresses.py` is US-only today; the Overture row count is not evidence that it can build a Chilean index:

- Its `country = 'US'` filter remains in place even with `--bbox`. Chile needs a country filter change.
- `left(postcode, 5)` would turn `8320000` into `83200`. Keep Chile's full postal code.
- `state.upper()[:2]` cannot preserve a `CL-XX` code or map a region name to one. Inspect actual Chilean Overture
  `address_levels` and `postal_city` values first, then map them to the full region code and comuna/locality fields.
  Those Chilean fields have **not been checked**; do not assume the US array positions have the same meaning.

These are requirements for a later design and builder change, not changes made by this documentation proposal.

## Still undecided

1. **Codes and names in setup.** As in [REGIONS.md](REGIONS.md) item 1, with `CL-AP` to `CL-MA`.
2. **Offshore islands in `CL-VS`.** Whether all five provisional island/group boxes are included in the `CL-VS` pack
   or offered as add-ons, and how a build represents multiple cuts without dropping islands.
3. **Tight region polygons.** Recomputing exact land boxes from BCN / IDE Chile official regional boundaries (with the
   0.15° margin rule) and deciding how to handle the overlap between `CL-RM` and `CL-VS`/`CL-LI`.
4. **Address search and builder.** Street-first parsing (including numeric street names and `S/N`), place-hint ranking,
   seven-digit postal codes, and mapping actual Chilean Overture fields to full region codes and comuna/locality fields.
5. **SENAPRED tsunami and emergency points.** Checking whether SENAPRED / IDE Chile evacuation points and safe zones
   carry a redistributable open licence.

## What was checked

- Opened: Geofabrik's Chile page (`chile-261116.osm.pbf` 352 MB / 336 MiB, `chile-261116-free.gpkg.zip`
  775 MB / 739 MiB, ODbL, data up to 16 November 2026), Geofabrik's `chile.poly` (132 vertices, outer box
  `-113.2233, -58.4519, -65.5141, -17.4574`), and
  Overture Maps' address guide (`CL`: 4,199,023 addresses).
- Opened for the review follow-up: the Wikipedia island pages linked above, for reference positions and the southern
  extent of Diego Ramírez. The provisional boxes surround those points; no official regional boundary file was opened.
- Opened for the maintainers' follow-up on 18 November 2026: Overture's attribution page, whose Addresses section
  credits Chile's rows to "© Instituto Nacional de Estadísticas. Available under CC BY 4.0. Distributed by
  AddressForAll." (Overture's access date 2026-10-15), and Geofabrik's `chile.poly` again (132 vertices, same bounds).
- Read: `tools/build_addresses.py`, confirming the US country filter, five-character postcode cut and two-character
  state cut. Chilean Overture address records and their administrative fields were not inspected.
- Search only: SUBDERE / INE CUT codes, BCN (*Biblioteca del Congreso Nacional*) cartography licensing, IDE Chile and
  SENAPRED geoportals.
- Not opened: DGA, DOH, CIREN/ODEPA, SENAPRED and CorreosChile terms pages, and the ISO 3166-2:CL page.
