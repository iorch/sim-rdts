# sim-rdts

Simula una red de nodos Bitcoin corriendo **Core** y **Knots** en `regtest` y mide la
dinámica de la cadena cuando Knots aplica el softfork **BIP-110 / RDTS** y Core no.

**Dashboards (GitHub Pages):** https://iorch.github.io/sim-rdts/

## Qué mide

Bitcoin Knots **v29.3.knots20260508** activa el softfork **BIP-110 / RDTS** (`consensusrules=rdts`)
y rechaza **a nivel de consenso** las transacciones con datos grandes. Bitcoin Core **31.1** no lo
conoce y las mina. Cada bloque con datos que Core produce es **válido para Core e inválido para
Knots** → la cadena puede partirse. Las simulaciones miden, según el reparto de hashpower:

- **P(fork persistente)** — cuándo la cadena se parte de forma irreversible.
- **P(el softfork gana)** — cuándo Core reorganiza a la cadena limpia y descarta su spam.
- **Frecuencia de reemplazo** de la cadena de Core (incentivo económico a señalar RDTS).

### Hallazgos

- El fork es **de consenso**, no solo de relay: verificado a nivel de bloque
  (`bad-txns-vout-script-toolarge`, `Push value size limit exceeded`).
- El softfork **gana con una leve supermayoría (~55-57% de hashpower)**, no en el 50% — por una
  asimetría de captura: cuando la cadena limpia lidera, Core la adopta y le pone un bloque con
  datos encima, absorbiendo la ventaja.
- **El número de nodos no importa, solo el hashpower**: Knots con 16-30 nodos dispersos pierde
  igual por debajo del umbral (sim-2).
- **Incentivo temprano:** Core pierde **≥1 bloque/día** por reorg desde ~30% de hashpower Knots —
  mucho antes del umbral de victoria → presión a señalar RDTS (efecto cascada).

## Activación de RDTS en regtest

RDTS es un deployment versionbits (`DEPLOYMENT_REDUCED_DATA`, bit 4) que en regtest está
`NEVER_ACTIVE` por defecto. Se fuerza activo con:

```
consensusrules=rdts                              # en bitcoin.conf
-vbparams=reduced_data:-1:9223372036854775807    # start=-1 => ALWAYS_ACTIVE
```

(El nombre del deployment es `reduced_data`, no `rdts`.)

## Estructura

```
docker/   Dockerfile.{core,knots} + conf/{core,knots}.conf  (binarios verificados por SHA256)
sim/      rpc.py · spam_txs.py · orchestrator.py · montecarlo.py · sim2.py
          analyze.py · analyze2.py · incentive.py · reorg_probe.py · make_artifact*.py
results/  results.csv · sim2.csv · reorg_probe.csv · *.png · *.json · report*.html
docs/     sitio de GitHub Pages (index + sim1 + sim2)
deploy/   build_pages.py (genera docs/ desde results/)
```

## Cómo correr

```bash
# 1) imágenes Docker (descargan y verifican los binarios oficiales aarch64)
cd docker
docker build -f Dockerfile.knots -t bip110-knots:29.3 .
docker build -f Dockerfile.core  -t bip110-core:31.1  .

# 2) experimento 1 — fork vs hashpower (nodos iguales)
cd ../sim
python3 montecarlo.py --runs 10 --blocks 45
python3 analyze.py && python3 make_artifact.py

# 3) experimento 2 — hashpower concentrado
python3 sim2.py --runs 20 --blocks 45
python3 analyze2.py && python3 make_artifact2.py

# 4) frecuencia de reemplazo / incentivo
python3 reorg_probe.py --ns 6,11,16 --runs 6
python3 incentive.py

# 5) regenerar el sitio de Pages
python3 ../deploy/build_pages.py
```

## Notas / limitaciones

- **Rutas:** los scripts resuelven todo relativo al repo (`__file__`); se puede sobreescribir la
  raíz con la variable de entorno `SIM_RDTS_ROOT`.
- **Dependencia externa:** `spam_txs.py` reutiliza el *functional test framework* de Bitcoin Core
  (`test/functional/test_framework`) como librería para serializar transacciones taproot/witness.
  Apuntar a un checkout local con la variable `BITCOIN_FUNCTIONAL_TEST` (por defecto usa una ruta
  de desarrollo). Solo lo necesitan las corridas (no el análisis ni la generación del sitio).
- **`p_spam=1.0`** en las corridas: cada bloque de Core lleva datos → cota superior de la
  frecuencia de reorg. Con menos actividad de datos, los umbrales de incentivo se corren.
- Simulación en **regtest** (dificultad fija): "más largo" = "más bloques"; en mainnet sería
  "más trabajo (PoW)", pero la lógica es idéntica.

## Licencia

Ver [LICENSE](LICENSE).
