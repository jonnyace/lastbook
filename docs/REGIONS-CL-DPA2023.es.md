# Mapas detallados para Chile: una propuesta

> **Investigación complementaria del PR #140 (cd7d26c).** Este texto en español corresponde al estudio DPA 2023 en [inglés](REGIONS-CL-DPA2023.md), no a una traducción de la [propuesta de Chile ya existente](REGIONS-CL.md). No reemplaza sus rectángulos ni decide cuáles se usarán. La propuesta existente conserva cinco rectángulos separados para las islas de Valparaíso y un límite sur de −56.60° para Magallanes; este estudio usa tres grupos de islas y −56.5378° según DPA 2023. Las comprobaciones y los cálculos que siguen son los comunicados por el autor; no se recalcularon durante esta integración. No se entrega ningún mapa.

> Versión en español de [REGIONS-CL-DPA2023.md](REGIONS-CL-DPA2023.md). Si las dos difieren, vale la versión en inglés, que es la que se
> discute en el repositorio.

Esta es una propuesta para discutir, no una decisión. Responde, para Chile, las preguntas que [MAPS.md](MAPS.md) pide
contestar antes de que la cobertura vaya más allá de Estados Unidos: qué fuente abierta reemplaza a cada lista federal,
con qué licencia, qué es un "estado" acá y cómo se escriben las direcciones. Sigue la forma de [REGIONS.md](REGIONS.md)
y de [REGIONS-AR.md](REGIONS-AR.md), y busca alimentar la misma discusión de diseño (issues #23, #25 y #31). La versión
legible por máquina es [regions-cl-dpa2023-proposed.json](regions-cl-dpa2023-proposed.json).

Nada de esto cambia la app, el motor ni una compilación. Ningún código lee el JSON, y nada de esto se distribuye: las
compilaciones empaquetan solo `web/` y `content/`.

**Cómo se verificó.** La investigación se hizo el 17 de noviembre de 2026. Cada fuente lleva una de tres marcas, como en
REGIONS-AR.md:

- **abierta**: se abrió y se leyó la página del conjunto de datos, del registro o de la licencia, también a través de
  una API pública (el servicio se indica en el JSON); "contada" es un conteo leído de la misma forma;
- **solo búsqueda**: el dato se vio en un resultado de búsqueda del sitio del propio publicador, pero no se abrió la
  página;
- **sin verificar**: no se pudo llegar a la página o leerla; la fila dice qué falta.

Chile no tiene una página única como las "Capas SIG" del IGN argentino. Las capas están repartidas entre IDE Chile
(`geoportal.cl`), el Ministerio de Obras Públicas (GeoMOP: Vialidad, DOH, DGA), IDE Minagri (CIREN, CONAF, ODEPA), los
servicios ArcGIS del INE, la Biblioteca del Congreso Nacional (BCN), el MINSAL, el MINEDUC y SENAPRED. Pocas declaran
una licencia, y ese es el hallazgo principal de esta propuesta.

## Qué es una región

Chile tiene 16 regiones (Ñuble, la más nueva, se creó en 2018). La propuesta es un mapa por región, al mismo nivel que
un estado de Estados Unidos.

### Códigos

La norma ISO 3166-2:CL le da a cada región dos letras después de `CL-`: `CL-RM` Metropolitana, `CL-VS` Valparaíso,
`CL-BI` Biobío, y así. Se cotejaron con el archivo admin-1 de Natural Earth (`iso_3166_2`), no con el sitio de ISO, como
también aclara REGIONS.md para sus códigos.

- El prefijo importa tanto como para Argentina. Tres de las partes de dos letras ya son códigos de Estados Unidos en
  `STATE_CODES` (`engine/address_search.py`): `AR` (La Araucanía y Arkansas), `CO` (Coquimbo y Colorado) y `MA`
  (Magallanes y Massachusetts). Las demás no chocan hoy, pero nada impide que choquen mañana.
- Las fuentes chilenas usan el código CUT de región (Código Único Territorial), dos dígitos de `01` (Tarapacá) a `16`
  (Ñuble), no las letras ISO. Todas las capas oficiales de abajo traen el CUT, así que el JSON guarda los dos. El CUT
  conserva el cero inicial; una fuente que lo guarda como número (`1101` para la comuna `01101`) lo pierde.

### Tres lugares que necesitan una decisión

- **Las islas de Valparaíso.** `CL-VS` incluye Rapa Nui (Isla de Pascua) y Salas y Gómez, a 3.700 km en el Pacífico, y
  los archipiélagos de Juan Fernández y de las Desventuradas. Un solo rectángulo que las incluya a todas abarcaría 40
  grados de longitud de océano, y la capa de relieve se corta por rectángulo. La propuesta le da a `CL-VS` un rectángulo
  para el continente y tres rectángulos pequeños para los grupos de islas (abajo), así que una región puede tener más de
  un rectángulo. La otra opción es que Rapa Nui tenga su propio mapa; ISO no tiene un código para ella.
- **El Territorio Chileno Antártico.** Por ley, Magallanes incluye la comuna Antártica (CUT `12202`). La capa oficial de
  límites la deja afuera ("no incluye el Territorio Antártico Chileno"), y el rectángulo de abajo también. La
  reclamación se superpone con las de Argentina y el Reino Unido y queda congelada por el Tratado Antártico, así que,
  como `AR-V`, entra en la decisión sobre límites en disputa (punto 6 de REGIONS.md).
- **El Campo de Hielo Patagónico Sur.** Un tramo del límite con Argentina, a lo largo de Magallanes y justo al sur del
  extremo austral de Aysén, no está demarcado. El archivo de regiones de la BCN lo muestra como un polígono aparte, "Zona
  sin demarcar" (codregion 0, 3.937 km²; abierta), con extensión -73.64, -49.81, -72.87, -49.17 (punto decimal, como
  en las tablas). Puntos repartidos sobre ella no caen en el polígono de Aysén ni en el de Magallanes de la capa
  oficial de 2023, así que esa capa también la deja afuera. La zona queda entera dentro del rectángulo con margen de
  `CL-MA` y en parte dentro del de `CL-AI`.

### Rectángulos

Los rectángulos se calcularon con la **capa oficial de límites, "División Política Administrativa 2023" (DPA 2023)**,
publicada por la SUBDERE con el Instituto Geográfico Militar (IGM), la DIFROL y el INE, a través del grupo de trabajo
DPA de IDE Chile (SIRGAS-Chile, EPSG:5360, escala 1:50.000). El archivo se descargó de la SUBDERE
(`ide.subdere.gov.cl/descargas/SHP/Limite_DPA_03082023.rar`) y su shapefile `REGIONES_v1` se leyó el 17 de noviembre de
2026. Tiene 16 elementos, uno por región, con `CUT_REG`, `REGION` y `SUPERFICIE`. Cada rectángulo es la extensión de
todos los vértices de las partes de la región al este de 76° O (todas, salvo las islas de Valparaíso en el Pacífico),
menos/más 0,15° y redondeado hacia afuera a 0,01°, el
mismo margen que usa `map_sets.state` para los estados de Estados Unidos. SIRGAS-Chile y WGS 84 difieren mucho menos que
ese redondeo.

La última columna es nueva para Chile: la superficie de la región (`SUPERFICIE`, km²) dividida por la superficie de su
rectángulo sin margen. Chile es largo y angosto, y su límite corre en diagonal por la cordillera, así que los
rectángulos traen mucho mar y mucho territorio de Argentina y Bolivia. En Magallanes, cerca de una cuarta parte del
rectángulo es la región. En Valparaíso la superficie incluye sus islas (unos 275 km²), así que su proporción queda un
poco alta.

En la tabla, los números van en el formato del archivo (punto decimal), igual que en la versión en inglés.

| Código | CUT | Nombre | Rectángulo (oeste, sur, este, norte) | Rectángulo con margen de 0,15° | Parte del rectángulo |
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
| `CL-MA` | 12 | Magallanes y de la Antártica Chilena (sin el Territorio Antártico) | -75.7232, -56.5378, -66.4156, -48.5941 | -75.88, -56.69, -66.26, -48.44 | 0.24 |
| `CL-ML` | 07 | Maule | -72.7857, -36.5438, -70.3117, -34.6844 | -72.94, -36.70, -70.16, -34.53 | 0.66 |
| `CL-NB` | 16 | Ñuble | -72.8847, -37.1985, -71.0070, -36.0054 | -73.04, -37.35, -70.85, -35.85 | 0.59 |
| `CL-RM` | 13 | Metropolitana de Santiago | -71.7155, -34.2910, -69.7698, -32.9219 | -71.87, -34.45, -69.61, -32.77 | 0.56 |
| `CL-TA` | 01 | Tarapacá | -70.2866, -21.6277, -68.4049, -18.9368 | -70.44, -21.78, -68.25, -18.78 | 0.72 |
| `CL-VS` | 05 | Valparaíso (continente) | -71.8957, -33.9742, -69.9892, -32.0205 | -72.05, -34.13, -69.83, -31.87 | 0.42 |

Los rectángulos de las islas de `CL-VS`, del mismo archivo, son las partes de la región al oeste de 76° O:

| Grupo de islas | Partes | Rectángulo (oeste, sur, este, norte) | Rectángulo con margen de 0,15° |
|---|---|---|---|
| Rapa Nui y Salas y Gómez | 171 | -109.4549, -27.2023, -105.3594, -26.4698 | -109.61, -27.36, -105.20, -26.31 |
| Juan Fernández | 19 | -80.8378, -33.8163, -78.7696, -33.6057 | -80.99, -33.97, -78.61, -33.45 |
| Desventuradas (San Félix, San Ambrosio) | 11 | -80.1214, -26.3510, -79.8606, -26.2731 | -80.28, -26.51, -79.71, -26.12 |

El rectángulo de Rapa Nui llega al este hasta Salas y Gómez, un islote deshabitado a 400 km. Un rectángulo solo para
Rapa Nui sería mucho más chico; eso es parte de la decisión de arriba.

**Controles cruzados.**

- **El COD-AB de Chile de OCHA** (nivel admin 1, a partir de la BCN, CC BY-IGO, última modificación el 26 de enero de
  2026; abierta en HDX) da rectángulos a menos de 0,07° de estos en 15 de las 16 regiones. La excepción es Magallanes,
  0,56° más al norte en su borde sur: la capa de OCHA deja afuera las islas Diego Ramírez (cerca de 56,5° S), que la DPA
  2023 sí incluye.
- **Natural Earth admin-1 1:10m** (versión 5.1.1, dominio público) queda a menos de 0,21° en 12 regiones, pero con 0,29°
  de diferencia en Biobío y 0,43° en La Araucanía (pone la Isla Mocha, que pertenece al Biobío, en La Araucanía), 0,44°
  en Los Lagos y 0,62° en Magallanes (sin Diego Ramírez). Así que la DPA 2023 es la capa que hay que usar, como lo fue
  la del IGN para Argentina.

## Fuentes, capa por capa

| Capa (archivo) | Fuente de EE.UU. hoy | Propuesta para Chile | Publicador | Licencia | Verificado |
|---|---|---|---|---|---|
| Relieve (`terrain.sqlite`) | USGS 3DEP | Copernicus DEM GLO-30, como se propuso para Guyana | ESA / Airbus | Copernicus WorldDEM-30 | como en REGIONS.md |
| Relieve, islas | | DEM de Isla de Pascua (4 m) y Juan Fernández (2 m), TIFF | catálogo de IDE Chile | no declarada | abierta (registro) |
| Agua (`water.sqlite`), ríos | NHD | "Hidrografía de la región de Arica a la región de Los Lagos" (edición 2024), 1:25.000, con orden de Strahler y códigos de cuenca de la DGA | grupo de trabajo de hidrografía de IDE Chile | no declarada | abierta (registro; conteo WFS de la edición 2021, 122.852 elementos) |
| Agua, lagos | NHD | Catastro de Lagos (2.067 polígonos de lagos y lagunas, con nombre, tipo y altitud) | Dirección General de Aguas (DGA) | no declarada | abierta (archivo leído) |
| Agua, canales | NHD | Canales CNR (13.166 canales de riego) | Comisión Nacional de Riego / DOH, MOP | términos de GeoMOP (gratis, sin licencia con nombre) | abierta (conteo por API) |
| Agua, Aysén y Magallanes; respaldo | | cursos y superficies de agua de OSM (extracto de Chile de Geofabrik) | colaboradores de OSM | ODbL | abierta (encabezados del archivo) |
| Embalses | NID | Catastro de Embalses (1.370 embalses, con uso y, para algunos, altura del muro; "actualizado a diciembre de 2015") | Dirección de Obras Hidráulicas (DOH) con la DGA, MOP | términos de GeoMOP | abierta (conteo por API) |
| Cultivos (`crops.sqlite`) | USDA Cropland Data Layer | Catastro Frutícola: polígonos de plantaciones frutales por especie, berries incluidos, 94.731 polígonos en 14 regiones | CIREN (IDE Minagri) | **no declarada** | abierta (conteos por API) |
| Cultivos, respaldo abierto | | MapBiomas Chile, Colección 2 (cobertura anual del suelo) | MapBiomas Chile | CC BY 4.0 | abierta (términos) |
| Edificios (`buildings.sqlite`) | huellas de Microsoft para EE.UU., alturas de OSM | Google Open Buildings v3; Microsoft Global ML Building Footprints (330 archivos para Chile) para llenar vacíos; alturas de OSM | Google; Microsoft; colaboradores de OSM | CC BY 4.0 u ODbL (a elección del usuario); CDLA Permissive 2.0; ODbL | abierta (listas de países); cobertura no medida |
| Lugares (`places.sqlite`) | GNIS, nomencladores del Censo, OSM | Censo 2017: ciudades (270), pueblos (289), aldeas (727) y caseríos (3.669); Censo 2024: topónimos de localidad (9.378 puntos) y entidades (28.415); topónimos del IGM de las cartas 1:50.000 (105.440 puntos); lugares con nombre de OSM | INE; IGM; colaboradores de OSM | "Datos de uso público" (2017); no declarada (2024, IGM); ODbL | abierta (conteos por API) |
| Caminos (mapa base) | OSM | OSM, como hoy; Red Vial Chile (14.266 tramos con rol y carpeta, actualizada cerca de 2017) para llenar vacíos rurales | colaboradores de OSM; Dirección de Vialidad, MOP | ODbL; términos de GeoMOP | abierta (conteo por API) |
| Direcciones (`addresses/<code>.sqlite`) | direcciones de Overture | direcciones de Overture: 4.199.023 filas chilenas del INE, distribuidas por AddressForAll (también en OpenAddresses) | Overture Maps Foundation / INE | CC BY 4.0 según Overture (ver "Notas sobre licencias") | abierta; contada |
| Direcciones, rangos por calle | | Maestro de Calles 2018: 395.480 tramos de calle con campos para rangos de numeración a cada lado, en 64 comunas | INE y el grupo de trabajo de ejes viales de IDE Chile | "Datos de uso público" | abierta (conteos por API) |
| Puntos de interés (filas `poi`) | OSM | OSM, más las listas de salud, educación, emergencia y energía de abajo | | | abajo |

### Puntos de ayuda y recursos

| Tipo | Fuente propuesta | Publicador | Licencia | Verificado |
|---|---|---|---|---|
| Salud | Establecimientos de Salud: 5.837 establecimientos, 5.411 con coordenadas, 827 con servicio de urgencia; incluye postas de salud rural (1.186), CESFAM (607), SAPU (272) y hospitales (234); la dirección viene separada en tipo de vía, nombre y número | Ministerio de Salud (DEIS) | **CC0** | abierta (archivo leído) |
| Farmacias | Farmacias en Chile: 1.925 farmacias, 1.805 con coordenadas | Ministerio de Salud | CC BY | abierta (servicio leído) |
| Bomberos | capa "BOMBEROS" del Visor Chile Preparado de SENAPRED: 1.418 compañías con nombre, dirección y teléfono | SENAPRED | **no declarada** | abierta (conteo, campos) |
| Policía | capa "CARABINEROS" del mismo visor: 883 unidades | SENAPRED | **no declarada** | abierta (conteo, campos) |
| Colegios | Directorio Oficial de Establecimientos Educacionales 2026: 12.004 establecimientos en funcionamiento, 11.966 con coordenadas, que el MINEDUC califica de "solo referenciales" | Ministerio de Educación | **no declarada** | abierta (archivo leído) |
| Combustible | capa "Estación de Servicio" de IDE Energía: 1.793 estaciones con los combustibles que vende cada una; fuente CNE, actualizada el 1 de abril de 2026 | Ministerio de Energía | no declarada en el servicio (el registro de catálogo que lo enlaza dice cc-by) | abierta (conteo, campos) |
| Energía | subestaciones (1.217), líneas de transmisión (1.128, del Coordinador Eléctrico Nacional) y centrales, mismo servicio | Ministerio de Energía | igual que arriba | abierta (conteos) |
| Agua potable rural | Sistemas de Agua Potable Rural: 2.213 comités y cooperativas, 2.119 con coordenadas, datos a diciembre de 2020 | Ministerio de Obras Públicas | **CC BY-NC** (`cc-nc`) | abierta (archivo leído) |
| Llaves de agua | OSM `amenity=drinking_water` (274) y `man_made=water_tap` (44) | colaboradores de OSM | ODbL | contada (datos OSM del 15 de julio de 2026, en un espejo de Overpass) |
| Puntos de encuentro por tsunami | SENAPRED: 1.544 puntos de encuentro, 2.842 vías de evacuación, 523 líneas de seguridad y 354 áreas a evacuar, en las 15 regiones costeras; última edición el 29 de octubre de 2026 | SENAPRED | **no declarada** | abierta (conteos, campos) |
| Puntos de encuentro por volcán | SENAPRED: 184 puntos de encuentro, 260 vías de evacuación, 3.499 polígonos de peligro volcánico, 104 volcanes activos | SENAPRED | **no declarada** | abierta (conteos, campos) |
| Albergues, cuarteles de la PDI, aeródromos | no se encontró una lista nacional abierta; OSM tiene 849 `emergency=assembly_point` y 385 `aeroway=aerodrome` | colaboradores de OSM | ODbL | contada (igual que arriba) |

### Amenazas

El mapa de Chile necesita algo que el de Estados Unidos no pone al frente: información de tsunamis y volcanes. Se
encontraron estas fuentes.

- **Cartas de Inundación por Tsunami del SHOA (CITSU).** El servicio hidrográfico de la Armada publica las cartas de
  hasta dónde llegaría un tsunami, de Arica a Puerto Williams, en PDF y KMZ. La página del SHOA rechazó la lectura
  automática (HTTP 403), así que la licencia está **sin verificar**. Las copias de las cartas en ArcGIS Online traen
  avisos que se contradicen: dos dicen "todos los derechos reservados. Ninguna parte ... puede ser reproducida ... sin
  el permiso previo y por escrito del SHOA" (citando la ley de propiedad intelectual, Ley 17.336), dos dicen "Dato
  abierto", y el registro del propio SHOA de 2015 en datos.gob.cl es `cc-nc`. Hay que tratarlas como no redistribuibles
  hasta que el SHOA lo confirme.
- **Las capas de tsunami y volcanes de SENAPRED** (tabla de arriba) cubren la misma necesidad con puntos de encuentro y
  áreas de evacuación, y están al día. No declaran licencia. No se conciliaron sus 104 volcanes activos con los 87 del
  SERNAGEOMIN.
- **El ranking de volcanes 2023 del SERNAGEOMIN** (abierta, PDF): 87 sistemas volcánicos activos con coordenadas y
  puntajes de riesgo. Los tres primeros son Villarrica, Calbuco y Llaima. No declara licencia. El servidor de mapas del
  SERNAGEOMIN (mapas de peligro y su catastro de remociones en masa) no respondió (tiempo de conexión agotado); **sin
  verificar**.
- No se encontró una capa nacional abierta de inundaciones.

Notas:

- **Relieve.** No se encontró un modelo de elevación nacional oficial y abierto como el MDE-Ar argentino. El CIREN
  ofrece mosaicos regionales de 12,5 m reprocesados del producto ALOS PALSAR del Alaska Satellite Facility, sin licencia
  en los registros; no se revisaron los términos del ASF. Copernicus GLO-30 es la opción más simple.
- **Agua.** La red hidrográfica oficial 1:25.000 llega solo hasta Los Lagos. Aysén y Magallanes, un tercio del país y la
  mayor parte de sus fiordos y glaciares, vendrían de OSM o de la "Red hidrográfica" más antigua de la BCN (uso libre
  citando la fuente; abierta).
- **Cultivos.** El Catastro Frutícola del CIREN se parece mucho más a lo que conserva `tools/build_crops.py` (huertos,
  viñas, berries) que cualquier cosa encontrada para Argentina: un inventario de polígonos de plantaciones frutales por
  especie, como "ARANDANO AMERICANO". Pero no declara licencia, y cada polígono trae el rol del predio (`rolpredi`), que
  un paquete debería quitar. La versión CC BY en datos.gob.cl (ODEPA) es una tabla por comuna sin geometría. Las viñas
  para vino son un catastro aparte del SAG, encontrado solo como informes (solo búsqueda). MapBiomas Chile es CC BY 4.0;
  no se revisó si sus clases separan huertos y viñas, y sus descargas GeoTIFF estaban "temporalmente suspendidas".
- **Direcciones.** A diferencia de Argentina, Chile tiene puntos de dirección. Ver "Cómo se escriben las direcciones".
- **Salud.** La lista del MINSAL es la capa con mejor licencia que se encontró (CC0), está al día a noviembre de 2026 y
  marca qué establecimientos tienen servicio de urgencia. Ese es el dato que más necesita una persona en un mal día.
- **Las capas de SENAPRED** son los datos de emergencia más completos que se encontraron, y son las mismas que la gente
  en Chile ya ve en el visor "Chile Preparado" del gobierno. Son públicas en ArcGIS Online, pero los cuatro ítems
  revisados tienen el campo de licencia vacío. Con la regla que usa REGIONS-AR.md ("un conjunto de datos sin licencia
  declarada se trata acá como todavía no utilizable"), necesitan un permiso escrito de SENAPRED.

## Notas sobre licencias y atribución

- **CC0** (establecimientos de salud del MINSAL). No exige atribución; citar igual es buena práctica.
- **datos.gob.cl.** Sus términos de uso (Resolución Exenta Nº 469 de 2024; abierta) ponen CC0 por defecto, y permiten
  también PDDL, CC BY 4.0 y ODC-By. Aun así, cada registro trae su propia licencia, y muchos registros geográficos
  antiguos (2015) son `cc-nc`, que el portal titula "Creative Commons Non-Commercial (Any)" y enlaza a CC BY-NC 2.0.
  Hay que leer la licencia registro por registro.
- **CC BY-NC** (`cc-nc`: sistemas de agua potable rural; el registro del SHOA de 2015). No comercial. Es la misma
  pregunta que los términos del IGN en REGIONS-AR.md ("libre y gratuita, uso comercial solo en obras derivadas"):
  sirve para paquetes gratuitos, pero un paquete que la contenga no se podría vender, ni siquiera por un tercero.
- **CC BY 4.0** (MapBiomas Chile, Google Open Buildings): citar al publicador, enlazar la licencia y decir si se
  modificó.
- **ODbL** (OSM, y huellas de Microsoft si se toman del tema de edificios de Overture): igual que para el mapa de
  Estados Unidos.
- **CDLA Permissive 2.0** (huellas de Microsoft descargadas directamente de su lista de archivos): un paquete que las
  comparta debe poner a disposición el texto de la licencia junto con ellas.
- **INE.** Los términos de datos abiertos del INE ponen el contenido de su sitio bajo **CC BY-SA 4.0** (abierta). El
  "compartir igual" obligaría a cualquier base de datos construida con él. Las capas del Censo 2017 dicen solo "Datos
  de uso público", y las de 2024 no dicen nada. Cuál de estas aplica a cada capa es una pregunta para el INE; el
  JSON todavía no asigna CC BY-SA 4.0 a ninguna capa.
- **Direcciones del INE vía Overture.** Overture las lista como "© Instituto Nacional de Estadísticas. Available under
  CC BY 4.0. Distributed by AddressForAll." El registro de AddressForAll (abierta) muestra cómo se llegó a eso: el INE
  no publicó el archivo, AddressForAll lo obtuvo con una solicitud por Ley de Transparencia, y el INE respondió después,
  según la traducción al inglés de AddressForAll, que los datos son públicos, que se pueden usar para cualquier fin y
  que basta con citar la fuente como "INE CHILE". El propio registro de AddressForAll califica la licencia como
  "Implied CC-BY", y OpenAddresses la registra como "CHILE GOVERMENT TRANSPARENCY LAW" (sic). Parece utilizable citando
  "INE Chile", pero descansa en una respuesta, no en una licencia publicada, y los mantenedores deberían saberlo.
- **BCN** (abierta): uso libre, citando "Biblioteca del Congreso Nacional de Chile"; solo referencial.
- **IDE Chile y GeoMOP.** El catálogo de IDE Chile pide citar a la institución proveedora, y su pie de página dice
  "todos los derechos reservados". GeoMOP dice que sus datos no tienen costo. Ninguno nombra una licencia.
- **Sin licencia declarada** (necesitan permiso del publicador antes de usarse): las capas de SENAPRED, el catastro
  frutícola y los DEM del CIREN, el directorio de colegios del MINEDUC, el ranking del SERNAGEOMIN, los lagos de la DGA,
  los topónimos del IGM y el servicio de IDE Energía.
- **CC BY-IGO** (límites de OCHA, usados solo como control cruzado): citar a OCHA y a su fuente, la BCN.
- **La DIFROL y los mapas de los límites de Chile.** Es el punto legal más importante para Chile, comparable a los
  términos del IGN para Argentina. El metadato de la DPA 2023 (abierta) dice que, según el DFL Nº 5 de 1967, el DS Nº
  566 de 1970 y el DFL Nº 83 de 1979, toda publicación cuya circulación autorice la DIFROL debe llevar una leyenda fija,
  y que los mapas que muestran los límites de Chile no comprometen al Estado de Chile. En una frase aparte, que no cita
  ninguna ley, agrega que "las publicaciones y productos derivados de ella deben ser revisados y validados de igual
  manera por DIFROL". Los documentos no coinciden en qué resolución cita la leyenda: el metadato dice Nº 87 de 2023, el
  archivo de descripción del mismo archivo comprimido dice Nº 87 de 2019, y el registro de IDE Chile dice Nº 50 de 2019.
  El archivo comprimido en sí no declara licencia, mientras que datos.gob.cl lista la descarga de la DPA 2023 de IDE
  Chile en un registro de catálogo `cc-by` (`categoria-geoespacial-limites-y-fronteras`). Podría decirse que calcular un
  rectángulo a partir de la capa no es publicar un mapa, pero mostrar los límites de Chile en la app podría serlo. Es
  una pregunta para los mantenedores y, probablemente, para la propia DIFROL. El mapa base del mundo de Lastbook ya
  dibuja los contornos de los países (`web/world-context.json`), y el mapa cita a Natural Earth (`MAP_CREDIT` en
  `packaging/build_packs.py`).

## Cómo se escriben las direcciones

- **Orden.** Calle, luego número, luego el resto (departamento, piso, block), luego comuna y región: "Avenida Palena
  1084, Depto. 505, 9180794 Estación Central" (hoja de direccionamiento de la UPU para Chile, 2017; abierta). Como en
  Argentina, el número va *después* de la calle, al revés del orden de Estados Unidos que espera el analizador.
- **Palabras de calle.** *Avenida* (*Av.*, *Avda.*), *Calle*, *Pasaje* (*Psje.*, muy común en villas y poblaciones),
  *Camino*, *Ruta*, *Carretera*. El nombre de la villa o población es parte de la dirección pero no de la calle. Las
  direcciones rurales muchas veces no tienen número: "S/N" (sin número), "Km 15", "Parcela 31", "Lote 3", "Sitio 14".
  Muchos nombres de calle son fechas ("21 de Mayo", "10 de Julio"), que la gente también escribe con palabras.
- **Código postal.** Siete dígitos, que se escriben antes de la comuna: tres para el sector de reparto (normalmente una
  comuna) y cuatro para un lado de una cuadra, como en `8720019 QUILICURA`. Donde una comuna no tiene códigos por
  cuadra, su código termina en `0000` (hoja de la UPU; abierta). Correos de Chile ofrece solo una página de consulta; no
  se encontró un archivo abierto de códigos postales.
- **Qué tiene Overture.** 4.199.023 filas en la versión 2026-10-21.0 (contadas con DuckDB el 17 de noviembre de 2026),
  en las 16 regiones pero solo en 311 de las 346 comunas, y ninguna en Rapa Nui ni en Juan Fernández. 3.988.122 tienen
  número y calle, que es lo que conserva `tools/build_addresses.py`. Ninguna tiene código postal. Los nombres de calle
  van en mayúsculas, casi siempre sin la palabra de calle. La región está en `address_levels[1]` ("METROPOLITANA DE
  SANTIAGO", "DE VALPARAÍSO") y la comuna en `address_levels[2]`. Por región, van de 1.593.107 en la Metropolitana a
  24.715 en Aysén (en el JSON).
- **Qué agrega el archivo de calles del INE.** El Maestro de Calles 2018 tiene 395.480 tramos de calle; 277.295 traen un
  rango de numeración en al menos un lado, y 162.601 en ambos. Pero cubre solo 64 comunas, y 186.561 de sus tramos (47%)
  están en la Metropolitana. Podría complementar a Overture por interpolación, como propone REGIONS-AR.md para las
  cuadras de Argentina, pero no reemplazarlo.
- **Qué hace el código actual con eso.**
  - `tools/build_addresses.py` selecciona solo `country = 'US'`, así que hoy no tomaría ninguna fila chilena. Si se
    cambia ese filtro, tomar las dos primeras letras del nombre de la región (`state.upper()[:2]`) daría `DE` (Delaware)
    para 15 regiones, porque sus nombres empiezan con "DE" o "DEL", y `ME` (Maine) para la Metropolitana. Chile necesita
    que la región se traduzca a `CL-..` por nombre o por código CUT.
  - `engine/address_search.py` trata una consulta como dirección solo si empieza con un número, así que "Avenida Palena
    1084", "S/N" y "Parcela 31" no se buscan como direcciones. Lee un código postal solo como cinco dígitos (`\d{5}`),
    conoce solo palabras de calle en inglés, y en "38 B" toma la "B" como parte de la calle.
  - El normalizador reemplaza por espacios las letras fuera de la a a la z en vez de convertirlas, así que "Ñuble" queda
    como "uble" y "Peñalolén" queda en tres palabras, "pe alol n". Vale la pena arreglarlo para todos los idiomas, no
    solo para el español.

## Pendiente de decisión

Cada uno de estos puntos necesita la decisión de los mantenedores antes de cambiar código. Los tres primeros son
compartidos con REGIONS.md y REGIONS-AR.md.

1. **Códigos en el setup.** Si los códigos con guion como `CL-RM` son aceptables como `id` del manifiesto, en
   `map-set.json` y en `Lastbook-Map-<id>.zip`, y cómo lista el setup las 16 regiones chilenas.
2. **La regla del rectángulo**, como en REGIONS.md, más una pregunta nueva con Chile: si una región puede tener **más de
   un rectángulo** (el continente de Valparaíso y sus tres grupos de islas), o si Rapa Nui tiene su propio mapa.
3. **Límites en disputa y sin demarcar**: el Territorio Chileno Antártico y el tramo sin demarcar del Campo de Hielo
   Patagónico Sur.
4. **La regla de la DIFROL** sobre mapas que muestran los límites de Chile: si un paquete de mapas que los dibuja
   necesita revisión de la DIFROL, y dónde iría la leyenda. Puede requerir una consulta a la propia DIFROL.
5. **Capas sin licencia declarada**, sobre todo las de tsunami y volcanes de SENAPRED y el catastro frutícola del CIREN:
   si se pide permiso escrito a los publicadores, y quién lo pide.
6. **Licencias no comerciales y de "compartir igual"**: CC BY-NC (agua potable rural) y CC BY-SA 4.0 del INE, como
   los términos del IGN en REGIONS-AR.md.
7. **Búsqueda de direcciones** para Chile: calle antes del número, códigos postales de siete dígitos, palabras de calle
   en español, números como "S/N" y "Parcela 31", y convertir la ñ y los acentos.
8. **Nuevos tipos de puntos y áreas**: puntos de encuentro y áreas a evacuar por tsunami, áreas de peligro volcánico,
   sistemas de agua potable rural y establecimientos de salud con urgencia, y cómo se relacionan con los tipos que ya
   dibuja `web/map.js`.

## Qué se verificó y qué no

- Abierto o descargado el 17 de noviembre de 2026: el paquete DPA 2023 de la SUBDERE (shapefile de regiones y sus
  documentos de metadato, descripción y cambios); el COD-AB de Chile de OCHA en HDX; Natural Earth admin-1 5.1.1; la
  mapoteca de la BCN y su archivo de regiones; los registros del catálogo de IDE Chile de la DPA 2023, la hidrografía,
  los DEM de las islas y los DEM del CIREN; el archivo de lagos de la DGA; el archivo de establecimientos de salud del
  MINSAL; el directorio de colegios 2026 del MINEDUC; los términos de MapBiomas Chile; la lista de países de Google Open
  Buildings; la lista de archivos de Microsoft; la página de atribución de Overture; el registro de Chile de
  AddressForAll y la fuente de Chile de OpenAddresses; la hoja de direccionamiento de la UPU; el ranking 2023 del
  SERNAGEOMIN; los términos de uso de datos.gob.cl; los términos de datos abiertos del INE.
- Leído con APIs públicas el 17 de noviembre de 2026: la API CKAN de datos.gob.cl (licencias y listas de archivos), el
  WFS de IDE Chile (conteo de ríos), los servicios ArcGIS del MOP (canales, embalses, caminos), el servicio ArcGIS del
  CIREN (catastro frutícola), los servicios ArcGIS del INE (lugares censales, Maestro de Calles), los servicios ArcGIS
  del IGM (topónimos), el servicio de IDE Energía (combustible y energía), el servicio de farmacias del MINSAL, y las
  capas e ítems ArcGIS de SENAPRED.
- Contado el 17 de noviembre de 2026: las direcciones chilenas de Overture (DuckDB sobre la versión 2026-10-21.0); las
  etiquetas de OSM en un espejo de Overpass con datos del 15 de julio de 2026.
- Calculado el 17 de noviembre de 2026: los 16 rectángulos y los tres de las islas, a partir de la DPA 2023, cotejados
  con OCHA y Natural Earth.
- Visto solo en resultados de búsqueda de los sitios de los propios publicadores: el catastro vitícola del SAG, la
  tienda de mapas de peligro y los servicios de mapas del SERNAGEOMIN.
- Sin verificar: los códigos ISO 3166-2:CL contra el sitio de ISO; las páginas del propio SHOA (403) y la licencia de
  las CITSU; el servidor de mapas del SERNAGEOMIN (sin respuesta); el sitio de la propia DIFROL; si el CIREN, la DGA, el
  IGM y el INE publican términos para esas capas en otro lugar que los registros leídos; los términos de ALOS PALSAR del
  ASF; las clases de MapBiomas Chile; la cobertura de edificios medida en edificios; listas nacionales de albergues,
  cuarteles de la PDI y aeródromos; la API de combustibles de la CNE (requiere token); y la cobertura de direcciones en
  OSM (la consulta a Overpass se agotó, como pasó para Argentina).
