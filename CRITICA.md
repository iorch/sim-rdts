# Crítica honesta — al estilo Feynman y Satoshi

> "El primer principio es que no debes engañarte a ti mismo, y tú eres la persona más fácil de engañar." — Richard Feynman

Una simulación que confirma lo que ya esperábamos merece más desconfianza, no menos. Esta es una crítica deliberada de nuestro propio trabajo: primero al estilo de Feynman (¿en qué nos podríamos estar engañando?) y después al estilo de Satoshi (¿los incentivos son de verdad los que decimos?).

## Parte 1 — Feynman: ¿nos estamos engañando?

**Cada bloque de Core lleva datos.** Corrimos con la fracción de spam fijada en uno: todos los bloques de Core cargan datos que RDTS invalida, así que todos son susceptibles de quedar huérfanos. Eso convierte cada número de frecuencia en una **cota superior**, no en un valor típico. Si en la realidad solo una fracción de los bloques de Core lleva datos ofensivos, la frecuencia de reemplazo baja aproximadamente en esa proporción, y el umbral de incentivo del 30% se corre hacia arriba. Presentar el peor caso como el caso normal sería engañarnos.

**regtest no es la red real.** En regtest la dificultad es fija, los bloques salen al instante, no hay latencia de propagación ni mercado de comisiones, y "cadena más larga" significa "más bloques", no "más trabajo acumulado". En la red real la dificultad se ajusta, las carreras de bloques tienen latencia física y el valor de un bloque incluye sus comisiones. La lógica cualitativa se traslada; **los números concretos no**.

**Pocas muestras y cadenas cortas.** Cada punto son 10 a 20 corridas de 45 bloques (unas 7.5 horas de red simulada). Las probabilidades de la cola (ese 10% suelto entre 65% y 75% de hashpower) son en buena medida **ruido estadístico**, y los intervalos de confianza son anchos. Las cifras "por día" son extrapolaciones de corridas cortas suponiendo estacionariedad.

**El "~57%" es una elección, no una ley.** El cruce depende del umbral con que definimos "fork persistente" (6 bloques) y del largo de la corrida. Cambiá cualquiera de los dos y el número se mueve. Lo honesto es decir "algo por encima del 50%", no fingir una constante universal.

**¿Probamos lo que creemos?** Forzamos RDTS activo desde el bloque cero y forzamos el spam con `generateblock`, saltándonos la política de mempool. Eso prueba correctamente el **rechazo de consenso**, pero **esquiva por completo la activación**: en la realidad RDTS debe alcanzar antes su umbral de señalización, y una minoría no puede activarlo. Toda la historia de "una minoría impone un costo" presupone que RDTS ya está activo — lo cual, por señalización, requeriría casi la mayoría. Esa circularidad la simulación no la aborda.

## Parte 2 — Satoshi: ¿los incentivos son los que decimos?

**El modelo de minero es ingenuo.** Modelamos a los mineros como bandos fijos que minan honestamente sobre su punta. Un minero Core que pierde bloques por reorganización tiene una respuesta más barata que señalar RDTS: **simplemente dejar de incluir los datos**. Confundimos "incentivo a dejar de hacer spam" con "incentivo a imponer el softfork a los demás" — son cosas distintas, y la racional inmediata es la primera.

**¿Dónde están las comisiones?** El incentivo real de un minero es `ganancia esperada incluyendo datos` frente a `ganancia esperada sin datos` = comisiones de esas transacciones contra el riesgo de orfandad. La simulación **no tiene mercado de comisiones**, así que mide solo un lado de la balanza (el riesgo de orfandad) y no puede concluir el incentivo neto. Si los datos pagan comisiones altas, puede convenir incluirlos aunque a veces se orfanen.

**Sin comportamiento estratégico.** No hay minería egoísta, retención de bloques ni manejo del momento de anuncio. La elección de minero uniforme e independiente ignora la liberación estratégica de bloques que domina las carreras de reorganización reales.

**Mundo binario.** Hay solo dos bandos. La red real tiene también mineros con política propia y una mayoría que "sigue la cadena más larga" sin militar en ningún lado. El corte limpio Core-contra-Knots es una simplificación.

**Consenso a medias.** BIP-110 exime los UTXOs creados antes de la activación. No lo modelamos, así que probablemente **sobreestimamos** cuántas transacciones serían realmente rechazables tras un flag-day real.

## Lo que sí sobrevive a la crítica

Para ser justos: el **mecanismo** es real y su dirección es correcta. El enforcement asimétrico produce divisiones gobernadas por el hashpower; el número de nodos es irrelevante frente al hashpower; y el trabajo desperdiciado hace pico cerca del empate. Esos hallazgos **cualitativos** son robustos. Lo que no es robusto son los **números** — los umbrales exactos y las frecuencias.

## Qué habría que medir para creerles a los números

- **Barrer la fracción de bloques con datos** (100%, 50%, 20%, 10%) y ver cómo se mueve el umbral de incentivo.
- **Agregar un modelo de comisiones** y computar la ganancia neta esperada, no solo el riesgo de orfandad.
- **Modelar la activación por señalización** (el umbral de BIP9), en vez de forzarla.
- **Corridas más largas** (144 bloques o más = un día) y más repeticiones, para estrechar los intervalos de confianza.
- **Usar trabajo acumulado con dificultad ajustable**, no conteo de bloques.
- **Modelar la respuesta "dejar de incluir datos"** como estrategia alternativa a "señalar RDTS".

---

En el espíritu de Satoshi: lo que importa no es que las cadenas *puedan* partirse, sino qué le *conviene* a cada minero. Y ese cálculo, aquí, está hecho a medias — falta el lado de las comisiones. Tratá estos resultados como un mapa del mecanismo, no como una predicción de la red real.
