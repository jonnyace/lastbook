# Mapas detallados para México: una propuesta

Esta es una propuesta para discusión, no una decisión. Responde, para México, las preguntas que [MAPS.md](MAPS.md)
plantea antes de que la cobertura pueda ir más allá de Estados Unidos: qué fuente abierta reemplaza cada lista federal,
bajo qué licencia, qué es un "estado" allí y cómo se escriben las direcciones. Sigue la estructura de
[REGIONS.md](REGIONS.md), [REGIONS-ES.md](REGIONS-ES.md) y [REGIONS-AR.md](REGIONS-AR.md), y busca alimentar la misma
discusión de diseño (issues #23, #25, #31 y #54). La versión legible por máquina es
[regions-mx-proposed.json](regions-mx-proposed.json).

Nada aquí cambia la aplicación, el motor ni una compilación. Ningún código lee el JSON y nada aquí se empaqueta: las
compilaciones solo empaquetan `web/` y `content/`.

**La versión inglesa [REGIONS-MX.md](REGIONS-MX.md) es la canónica.** Esta traducción al español sigue su contenido fielmente;
si hay alguna discrepancia, la versión inglesa tiene prioridad.

## Cómo se verificaron las fuentes. La investigación se hizo el 18 de noviembre de 2026, con agentes de investigación de IA
leyendo las páginas propias de los editores y una persona revisando el resultado. Las cajas (bboxes) se calcularon a partir
de los datos mismos, como se describe en cada sección. Cada fuente lleva una de tres marcas:

- **abierta** (opened): la página del conjunto de datos o de la licencia se abrió y se leyó;
- **solo búsqueda** (search only): el dato se vio en un resultado de búsqueda del sitio del editor, pero la página misma no
  se abrió;
- **no verificado** (not checked): no se pudo acceder a la página; la fila indica qué falta.

## Por qué México es un caso útil

México se parece a Estados Unidos en la forma en que organiza sus datos. En la guía de direcciones de Overture es el
tercero por número de direcciones, después de Estados Unidos (126.202.222) y Brasil (89.887.635), con 30.726.687 filas
mexicanas (conteos de la guía del editor, no un conteo hecho para esta propuesta). Un instituto nacional de
mapeo (INEGI) publica elevación, hidrografía, nombres, límites, uso del suelo y el marco geoestadístico bajo una
sola licencia, los "Términos
de Libre Uso de la Información del INEGI" (INEGI Libre Uso), que permite copia, distribución, adaptación y uso comercial
con atribución y sin compartir-igual (share-alike). Overture ya contiene un conjunto nacional de direcciones proveniente
de INEGI. Dos cosas difieren de EE. UU. y conviene decidirlas ahora, porque otros países latinoamericanos las plantearán:

- **No hay capa abierta de áreas de código postal.** SEPOMEX (el servicio postal) es propietario de las áreas de códigos
  postales pero no las publica como datos abiertos. El Marco Geoestadístico del INEGI incluye puntos de localidades, no
  áreas de códigos postales. El *código postal* (CP) de cinco dígitos adjunto a cada dirección en los datos de Overture es
  otra cosa y es lo que la búsqueda de direcciones necesita.
- **Tipos de cultivo específicos de México.** Las series de uso del suelo y vegetación del INEGI incluyen agave,
  agostadero, temporal (de secano) y otras clases que no tienen equivalente en las clases de EE. UU. en
  `tools/build_crops.py`.

## Qué es una región

México tiene 32 estados (*entidades federativas*): 31 estados y la Ciudad de México (que fue el Distrito Federal hasta
2016). La propuesta es una región por estado, 32 en total. Un estado es el nivel más cercano a un estado de EE. UU. en
tamaño y en lo que gestiona (salud, protección civil, la mayoría de los portales de datos abiertos): el más grande,
Chihuahua (aprox. 247.000 km²), es del tamaño de Idaho; el más pequeño es la Ciudad de México (aprox. 1.500 km²). El
compendio geográfico 2024 del INEGI, sobre el Marco Geoestadístico de diciembre de 2023, da a la Ciudad de México
1.494,3 km² y la ubica en el lugar 32. Tlaxcala (aprox. 4.000 km²) es el siguiente más pequeño y un poco más pequeño
que Delaware; las áreas de Chihuahua y Tlaxcala no se volvieron a abrir para este cambio.

### Códigos

ISO 3166-2:MX da a cada estado tres letras después de `MX-`: `MX-AGU` Aguascalientes, `MX-BCN` Baja California,
`MX-CMX` Ciudad de México, y así sucesivamente (no verificado contra el sitio de ISO, como las otras propuestas también
indican para sus códigos).

- Los sufijos de tres letras no colisionan con ningún código de estado de EE. UU. en `STATE_CODES`
  (`engine/address_search.py`), que son de dos letras. Un `MX` sin sufijo tampoco es un código de EE. UU.
- Un código con guion sigue siendo necesario para el `id` del manifiesto y para `Lastbook-Map-<id>.zip`, por la misma
  razón que en las otras propuestas: `carry_over()` en `engine/setup/install.py` solo conserva índices de direcciones
  llamados `[A-Z]{2}.sqlite` o `.json`, así que un índice llamado `MX-AGU.sqlite` (o `AGU.sqlite`, que tiene tres
  letras) se quedaría atrás en la biblioteca vieja sin mensaje.

### Cajas

Las cajas se calcularon a partir del Marco Geoestadístico del INEGI, capa AGEE (*Área Geoestadística Estatal*, el
límite estatal), versión de diciembre de 2023, en coordenadas geográficas (WGS84, EPSG:4326). El shapefile se descargó
a través del espejo de CONABIO (`dest23gw.zip`, que es datos del INEGI; abierto) y se leyó con `geopandas`. Cada estado
se tomó como un polígono. Se leyeron todos los vértices de cada polígono; la caja de límites se amplió luego 0.15° y se
redondeó hacia afuera a 0.01°, el mismo margen que `map_sets.state` usa para los estados de EE. UU.

Como verificación, los bordes exteriores coinciden con los puntos extremos conocidos de México: la Isla de Guadalupe
(29.09° N, 118.28° W) al noroeste, la costa de Quintana Roo (21.61° N, 86.71° W) al este, la desembocadura del río
Suchiate en Chiapas (aprox. 14.53° N) al sur, y la frontera con EE. UU. (32.72° N) al norte. Esa latitud sur es el
borde sur de Chiapas en esta tabla (14.5321° N). Las coordenadas publicadas de la desembocadura quedan junto a ella
(aprox. 14.53° N; una lista de puntos extremos da 14°32′27″ N, aprox. 14.54° N). Las Islas Revillagigedo pertenecen
a Colima. El borde oeste de la caja de ese estado, -114.76°, es la Isla Clarión (aprox. 18.36° N, 114.73° W), no
Socorro (aprox. 18.78° N, 110.98° W).

| Código | INEGI | Nombre | Caja (oeste, sur, este, norte) | Caja con margen 0.15° |
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

Notas:

- **La península de Baja California** se divide entre `MX-BCN` (norte) y `MX-BCS` (sur) en la línea de 28° N. Ambas
  son penínsulas largas y estrechas con costa a ambos lados, así que cada una debe ser su propia región.
- **La caja de Colima** se extiende lejos hacia el Pacífico porque incluye las Islas Revillagigedo (Socorro, San
  Benedicto, Clarión, Roca Partida). El borde oeste, -114.76°, es la Isla Clarión, a unos 700 km del continente, no
  Socorro. La parte continental de Colima es un estado pequeño costero alrededor de -103.5° W.
- **Ciudad de México (MX-CMX)** colinda al norte, este y oeste con el Estado de México (MX-MEX) y al sur con Morelos
  (MX-MOR), así que no está totalmente rodeada por MX-MEX. Es la región más pequeña por área (aprox. 1.500 km²), más
  pequeña que Tlaxcala. Las cajas de la Ciudad de México y del Estado de México se superponen mucho. Un índice de
  direcciones no puede cortarse leyendo los dos primeros dígitos del código postal como el código de estado del INEGI;
  esa división queda como trabajo futuro (un polígono estatal, o una tabla CP→estado cuyos derechos se comprueben).
- **Tlaxcala (MX-TLA)** colinda con Puebla (MX-PUE), Hidalgo (MX-HID) y el Estado de México (MX-MEX), así que no está
  totalmente rodeada por Puebla. Vale la misma reserva sobre el código postal.
- **Sonora y Chihuahua** son los dos estados más grandes por área; sus bordes norte llegan a la frontera con EE. UU.
  (Arizona, Nuevo México y Texas).
- **Quintana Roo** incluye Cozumel e Isla Mujeres; es la región más oriental.

## Fuentes, capa por capa

| Capa (archivo) | Fuente de EE. UU. hoy | Propuesta para México | Editor | Licencia | Verificado |
|---|---|---|---|---|---|
| Terreno (`terrain.sqlite`) | USGS 3DEP | **CEM 4.0** (~15 m, modelo digital de terreno, cobertura nacional); Copernicus DEM GLO-30 como alternativa | INEGI; ESA / Airbus | INEGI Libre Uso; licencia Copernicus | página del CEM y términos del INEGI abiertos; Copernicus como en REGIONS-ES.md |
| Agua (`water.sqlite`) | NHD | Red Hidrográfica Nacional INEGI (1:250.000, SHP); CONAGUA Ríos Principales (WMS/WFS); OSM | INEGI; CONAGUA; OSM | INEGI Libre Uso; no indicada (CONAGUA); ODbL | página de hidrografía INEGI solo búsqueda; CONAGUA solo búsqueda; OSM como en EE. UU. |
| Presas | NID | **CONAGUA Catálogo de Presas** (~210 presas con coordenadas, estado, municipio); OSM `waterway=dam` como respaldo | CONAGUA; OSM | no indicada (CONAGUA); ODbL | página del catálogo abierta; CSV no descargado (bucle de redirección); conteo de resultados de búsqueda |
| Cultivos (`crops.sqlite`) | USDA Cropland Data Layer | **INEGI Uso del suelo y vegetación** 1:250.000 serie VII (2018); ESA WorldCover 2021 como respaldo | INEGI; ESA WorldCover | INEGI Libre Uso; CC BY 4.0 | página del INEGI solo búsqueda; WorldCover como en REGIONS-AR.md |
| Edificios (`buildings.sqlite`) | Microsoft US footprints, OSM | **Google Open Buildings V3** (huellas de edificios, CC BY 4.0 / ODbL); edificios OSM para llenar huecos | Google Research; OSM | CC BY 4.0 (u ODbL); ODbL | página de Google Open Buildings abierta; OSM como en EE. UU. |
| Lugares (`places.sqlite`) | GNIS, Census, OSM | **INEGI Marco Geoestadístico** (AGEE, AGEM, localidades); OSM | INEGI; OSM | INEGI Libre Uso; ODbL | página y shapefile del INEGI abiertos (usados para el cálculo de cajas) |
| Direcciones (`addresses/<code>.sqlite`) | Overture addresses | **Overture addresses: 30.726.687 filas mexicanas**, fuente INEGI vía OpenAddresses | Overture Maps Foundation / INEGI | INEGI Libre Uso (ver página de atribución de Overture) | guía de direcciones y página de atribución de Overture abiertas |
| Puntos de interés (`poi`) | OSM | OSM, como hoy | OSM | ODbL | taginfo para México (API) leído |

Notas:

- **Terreno.** El CEM 4.0 es un modelo nacional de terreno (tierra desnuda, bare-earth) a ~15 m, construido a partir de
  ALOS PALSAR (JAXA) con relleno de huecos con LiDAR/fotogrametría. Está más cerca de los 30 m que la aplicación usa hoy
  que el Copernicus GLO-30, y es tierra desnuda (no superficie), así que evita el problema del dosel y los techos. La
  descarga es por estado o por área desde el portal de elevaciones del INEGI.
- **Presas.** El catálogo de CONAGUA lista ~210 presas con: nombre, latitud, longitud, altitud, estado, municipio, cuenca
  y región hidrológica. El CSV está en `sih.conagua.gob.mx/basedatos/Presas/0_Catalogo_de_presas.csv`, pero el sitio tiene
  un bucle de redirección que impidió la descarga directa para esta propuesta. El conteo se confirmó en resultados de
  búsqueda. El catálogo también está disponible como servicio ArcGIS REST (`sigagis.conagua.gob.mx`). La licencia no está
  indicada en la página; si los datos de CONAGUA siguen el mismo marco de "Términos de Libre Uso" que el INEGI no se confirmó.
- **Cultivos.** `tools/build_crops.py` conserva huertos, viñedos y frutillas. En México los cultivos permanentes más
  importantes son agave (para tequila y mezcal), café, caña de azúcar, cítricos y aguacate. La serie de uso del suelo y
  vegetación del INEGI (1:250.000, serie VII, 2018) incluye clases como *agostadero*, *temporal* (de secano), *agave*,
  *caña* y *cafetal*, que no tienen clase de EE. UU. Si la capa de cultivos debe crecer nuevos tipos para estos cultivos
  mexicanos es una decisión de los mantenedores, como se plantea para olivos, cítricos y frutos secos en REGIONS-ES.md.
- **Edificios.** Google Open Buildings V3 proporciona 1.800 millones de huellas de edificios en África, América Latina,
  el Caribe, el Sur de Asia y el Sudeste Asiático, incluyendo todo México. Cada huella tiene una puntuación de confianza
  [0.65–1.0], un área y un Plus Code. La licencia es CC BY 4.0 y ODbL; el usuario puede elegir cualquiera. Microsoft
  Global ML Building Footprints también cubre México y sigue como alternativa. El repositorio es público y no está
  archivado (API de GitHub, 19 de noviembre de 2026; último push el 18 de noviembre de 2026). La licencia directa de
  los datos, según el README, es CDLA-Permissive-2.0 (README abierto el mismo día; hay una entrada de actualización
  del 12 de noviembre de 2026). OSM tiene huellas de edificios en zonas urbanas pero la cobertura es más delgada en
  el México rural.
- **Lugares.** El Marco Geoestadístico del INEGI es el marco nacional: estados (AGEE, 32), municipios (AGEM, ~2.467) y
  localidades (urbanas y rurales). Se actualiza anualmente; la versión de diciembre de 2023 se usó para las cajas de esta
  propuesta, y la versión de diciembre de 2025 está disponible.

## Direcciones en Overture, según la guía del editor

Las filas mexicanas de Overture, versión `2026-11-18.0`, se leyeron desde la guía de direcciones el 18 de noviembre de 2026.
Los conteos de abajo son los del editor, no una medición hecha para esta propuesta:

- **30.726.687 direcciones**, el tercero después de Estados Unidos (126.202.222) y Brasil (89.887.635). Fuente: "INEGI,
  Censos Económicos. TÉRMINOS DE LIBRE USO DE LA INFORMACIÓN DEL INEGI. Distributed by OpenAddresses. Accessed:
  2026-11-17." (página de atribución de Overture, abierta).
- Los conteos por estado no se calcularon. Dividir por los dos primeros dígitos del código postal como si fueran el
  código de estado del INEGI pondría direcciones en el estado equivocado: Aguascalientes (INEGI 01) empieza en 20000, y
  Zacatecas (INEGI 32) en 98000. La división por estado queda como trabajo futuro, por ejemplo por polígono estatal, o
  por una tabla CP→estado cuyos derechos se comprueben. El total nacional de la guía es cerca de un cuarto del total de
  EE. UU. y mayor que el de cualquier país europeo listado allí.

## Puntos de ayuda

OSM es la fuente práctica para puntos de ayuda en México: ninguna lista nacional abierta con coordenadas se confirmó para
hospitales, farmacias, bomberos o policía. Los conteos de taginfo para el extracto de México de Geofabrik, datos hasta el
17 de noviembre de 2026 21:19 UTC (API, abierto):

| Etiqueta | Conteo | Notas |
|---|---|---|
| `amenity=pharmacy` | 7.943 | |
| `amenity=hospital` | 3.507 | |
| `amenity=clinic` | 5.117 | incluye *centros de salud* de atención primaria |
| `amenity=fire_station` | 426 | |
| `amenity=police` | 1.491 | |
| `amenity=drinking_water` | 548 | muy por debajo de los 44.411 de España |
| `man_made=water_well` | 685 | |
| `natural=spring` | 247 | no potable por defecto |
| `emergency=water_tank` | 49 | mayormente agua para combate de incendios |
| `emergency=defibrillator` | 23 | muy escaso |
| `tourism=alpine_hut` | 103 | mayormente en la Sierra Madre |
| `tourism=wilderness_hut` | 16 | |
| `amenity=shelter` | 2.139 | necesita filtro `shelter_type`; incluye paradas de autobús y techos de picnic |
| `amenity=fountain` | 3.074 | contar solo cuando `drinking_water=yes` |

Tres tipos de puntos mexicanos merecen una decisión:

- **Agua potable.** Con 548 puntos de `amenity=drinking_water`, la cobertura de OSM es escasa en México. El Sistema
  Nacional de Información del Agua (SINA) de CONAGUA tiene un servicio WMS para infraestructura de agua, pero su licencia
  y cobertura de puntos no se confirmaron.
- **Refugios de montaña.** La Sierra Madre Occidental y Oriental recorre México de norte a sur; los 103
  `tourism=alpine_hut` y 16 `tourism=wilderness_hut` son escasos. `amenity=shelter` (2.139) necesita el filtro
  `shelter_type`, como en España.
- **CENAPRED y Protección Civil.** El Centro Nacional de Prevención de Desastres (CENAPRED) y las Protecciones Civiles
  estatales publican mapas de peligros e inventarios de refugios, pero sus datos no se publican como datos abiertos con
  coordenadas y una licencia clara. Una capa de puntos de ayuda en México sería OSM con una nota de "incompleto", a
  menos que se encuentre una fuente estatal.

## Notas de licencia y atribución

Todas las licencias propuestas permiten la redistribución en una biblioteca libre sin conexión, incluyendo el uso
comercial. Lo que cada una pide:

- **INEGI Libre Uso.** Atribución: "Fuente: INEGI, *nombre del producto*" y la fecha de actualización cuando aplique (por
  ejemplo, "Fuente: INEGI, Marco Geoestadístico 2023"). Notificar a los usuarios finales de cualquier análisis o
  transformación, y no sugerir que el INEGI respalda el resultado. Sin compartir-igual (share-alike). Los términos están en
  `https://www.inegi.org.mx/contenidos/inegi/doc/terminos_info.pdf` (abierto).
- **CC BY 4.0** (Google Open Buildings, ESA WorldCover). Acreditar al editor: "Google Open Buildings" para edificios;
  "© ESA WorldCover project 2021" para WorldCover.
- **ODbL** (OSM, edificios de Overture). Acreditar "© OpenStreetMap contributors", indicar que los datos están bajo la
  ODbL, y ofrecer una base de datos construida a partir de ellos bajo la ODbL también. El mapa de EE. UU. ya lleva datos
  ODbL, así que esto no es nuevo.
- **Copernicus WorldDEM-30.** Como en REGIONS-ES.md y REGIONS.md.
- **CONAGUA.** La licencia del catálogo de presas no se confirmó. Si los datos de CONAGUA siguen el mismo marco de
  "Términos de Libre Uso" que el INEGI, o tienen sus propios términos, no se verificó. Debería confirmarse antes de una
  compilación.

## Cómo se escriben las direcciones

- **Orden.** Tipo de vía, nombre de la vía, luego el número, luego código postal y ciudad: "Av. Reforma, 123, 06600 Ciudad
  de México". El tipo va primero (*Avenida*, *Calle*, *Boulevard*, *Privada*, *Andador*, *Calzada*) y se abrevía a menudo
  (*Av.*, *C.*, *Blvd.*, *Priv.*, *And.*).
- **Código postal.** Cinco dígitos (*código postal*, CP), igual que un ZIP de EE. UU. Un CP debe permanecer como texto,
  porque hay ceros a la izquierda (por ejemplo 06600 Ciudad de México). Los dos primeros dígitos no son el código de
  estado del INEGI: Aguascalientes (INEGI 01) empieza en 20000 y Zacatecas (INEGI 32) en 98000. La división por estado
  de esos códigos es trabajo futuro.
- **Caracteres del español.** Los nombres de vías llevan acentos (á, é, í, ó, ú) y ñ. `normalize()` en
  `engine/address_search.py` y `norm()` en `tools/build_addresses.py` solo conservan `a-z` y `0-9`, así que "Reforma" pasa
  pero "Niños Héroes" se convierte en "ni os" y "Privada de la Cañada" en "privada de la ca ada". El plegado de acentos y ñ
  (á→a, ñ→n) en ambos lados arreglaría esto, como se plantea para España en REGIONS-ES.md.
- **S/N.** Muchas direcciones rurales y suburbanas no tienen número; OSM usa `S/N` (*sin número*), igual que el *S-N*
  español en las filas ES de Overture.
- **Lo que hace el código actual** (leído en este repositorio el 18 de noviembre de 2026):
  - `tools/build_addresses.py` solo conserva `country = 'US'`; necesitaría aceptar `country = 'MX'`.
  - `is_address_query()` necesita un número primero, así que "Av. Reforma 123, 06600" no se trata como dirección hoy.
  - La regla de CP de cinco dígitos encaja con México sin cambios, igual que con España.

## Por decidir

Cada uno necesita la decisión de los mantenedores antes de cualquier cambio de código:

1. **Códigos en la configuración.** Si `MX-AGU` y los demás son aceptables como `id` de manifiesto, en `map-set.json` y en
   `Lastbook-Map-<id>.zip`, y cómo agrupa la configuración 32 estados mexicanos. La misma preocupación de `carry_over()` que
   las otras propuestas aplica.
2. **La regla de la caja**, como en REGIONS.md, aquí del Marco Geoestadístico del INEGI.
3. **Códigos postales.** SEPOMEX es propietario de las áreas de códigos postales pero no las publica como datos abiertos.
4. **Nuevos tipos de cultivo**: agave, agostadero, café, caña de azúcar, aguacate.
5. **Licencia de CONAGUA.** Si la licencia del catálogo de presas se confirma como abierta.
6. **Google Open Buildings vs. edificios de Overture.** Si usar Google Open Buildings (CC BY 4.0 / ODbL) o esperar a que
   Overture incluya edificios de México.
7. **Cajas que se superponen.** La caja de la Ciudad de México se superpone con la del Estado de México, y la Ciudad
   de México también colinda con Morelos. Tlaxcala colinda con Puebla, Hidalgo y el Estado de México. Si un índice por
   región puede cortarse por polígono estatal, o por una tabla CP→estado cuyos derechos se comprueben, o si la
   superposición de cajas es aceptable. Los dos primeros dígitos del código postal no son el código de estado del
   INEGI, así que no sirven para ese corte.
8. **La línea de crédito en el mapa.** Los términos del INEGI piden atribución en la fuente de la obra.

## Qué se verificó y qué no

- Abierto el 18 de noviembre de 2026: los Términos de Libre Uso del INEGI (terminos_info.pdf); el portal de elevaciones
  CEM; la página del Marco Geoestadístico del INEGI y su shapefile (vía el espejo de CONABIO, que es datos del INEGI, en
  coordenadas geográficas WGS84); la página del catálogo de presas de CONAGUA; la página de Google Open Buildings V3; la
  guía de direcciones y la página de atribución de Overture; el taginfo de Geofabrik para México (API).
- Calculado el 18 de noviembre de 2026: las 32 cajas sin margen, a partir del shapefile AGEE del Marco Geoestadístico del
  INEGI como se describe arriba. El 19 de noviembre de 2026 los márgenes de 0.15° se recalcularon desde esos límites,
  redondeando hacia afuera (hacia abajo en oeste y sur, hacia arriba en este y norte) a 0.01°.
- Comprobado el 19 de noviembre de 2026, para la revisión: los conteos por país de la guía de direcciones de Overture
  (EE. UU., Brasil, México); el repositorio Microsoft Global ML Building Footprints (público, no archivado; licencia del
  README CDLA-Permissive-2.0); el compendio geográfico 2024 del INEGI para la Ciudad de México (1.494,3 km²; colinda con
  el Estado de México y Morelos); *Conociendo Tlaxcala* del INEGI para los límites de Tlaxcala (Hidalgo, Puebla y el
  Estado de México); coordenadas publicadas de la Isla Clarión, la Isla Socorro y la desembocadura del Suchiate. El
  archivo del catálogo de SEPOMEX no se volvió a descargar; los ejemplos 20000 de Aguascalientes y 98000 de Zacatecas se
  leyeron en los rangos por estado que publica Correos de México.
- Solo visto en resultados de búsqueda: la página de hidrografía del INEGI; los Ríos Principales de CONAGUA; las series de
  uso del suelo y vegetación del INEGI; el conteo de presas de CONAGUA (~210) de los resultados de búsqueda del CSV del
  catálogo.
- No verificado: el CSV del catálogo de presas de CONAGUA (bucle de redirección en `sih.conagua.gob.mx`); la licencia de
  CONAGUA; la tabla de códigos de uso del suelo del INEGI; la página de la colección del DEM de Copernicus (su licencia se
  leyó completa para REGIONS-ES.md); si los edificios de Overture cubren México; los códigos ISO 3166-2:MX contra el sitio
  de ISO; los conteos de direcciones de Overture por estado (necesitarían una consulta DuckDB); el formato o licencia del
  catálogo nacional de hospitales; los datasets del CENAPRED o Protección Civil con coordenadas.