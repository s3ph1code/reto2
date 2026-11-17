# Diseño · Reto 2: asistente con memoria de tres niveles, RAG y servidor MCP

- **Fecha:** 2026-11-17
- **Autor:** Kevin Cifuentes
- **Curso:** Inteligencia Artificial, semestre 5
- **Repositorio:** https://github.com/s3ph1code/reto2 (rama `main`)

---

## 1. Intención y por qué

El reto se entregó como dos tutoriales, sin enunciado ni rúbrica:

- `Tutorial_MCP_23_Oct.md`: montar servidores MCP en VS Code (el `memory` oficial en Node y uno
  propio en Python con `uv` + `FastMCP`), consumidos por Copilot Chat en modo Agente.
- `Tutorial_Memoria_RAG.md`: dotar de memoria a un asistente con tres niveles (corto, medio y
  largo plazo) usando ChromaDB, `sentence-transformers` y un LLM.

Un repositorio de referencia de otros compañeros del curso
(`Jo-Ssua/Reto_2_Inteligencia_Artificial`, consultado solo como referencia, sin copiar código)
muestra que el nivel esperado **no es replicar los tutoriales** sino extenderlos: añadieron un
segundo servidor MCP de invención propia, un RAG sobre un PDF, evaluación con RAGAS y trazas en
LangSmith. Eso coincide con la sección «Próximos pasos» del tutorial de RAG, que propone
exactamente memoria de documentos (punto 4) y evaluación (punto 5).

De ahí la intención: **un solo asistente que integre las dos mitades del reto** —la memoria de
tres niveles con RAG y un servidor MCP propio— sobre un dominio verificable, con evidencia
medible de que funciona.

## 2. Objetivos

1. Implementar los tres niveles de memoria del tutorial, con sus mecanismos completos: ventana
   deslizante, resumen progresivo con caducidad, hechos atómicos con deduplicación, puntuación
   combinada (similitud / importancia / recencia), refuerzo y olvido.
2. Añadir una cuarta colección de **documentos**: ingesta de un PDF propio, chunking, RAG con
   respuesta citada por artículo.
3. Exponer todo eso como **servidor MCP propio** (stdio, `FastMCP`), funcionando dentro de
   VS Code con Copilot Chat en modo Agente.
4. Cubrir también los pasos del tutorial de MCP que son de configuración: servidor `memory`
   oficial vía `npx`, `.vscode/mcp.json`, `.github/copilot-instructions.md`, y un servidor de
   terceros vía `uvx`. Con bitácora y capturas como evidencia.
5. **Medir** la calidad del RAG con RAGAS (`faithfulness`, `answer_relevancy`,
   `context_precision`, `context_recall`) sobre un conjunto propio de preguntas con respuesta de
   referencia, y guardar los resultados en el repositorio.
6. Que todo sea reproducible por un tercero desde el README, con herramientas gratuitas.

## 3. No objetivos

- Interfaz web o gráfica. El asistente es de consola, más el servidor MCP.
- Multiusuario con autenticación. Se deja previsto el metadato `usuario`, sin implementar login.
- LangSmith u otro servicio de trazas en la nube: las trazas son un archivo local JSONL.
- Fine-tuning, agentes múltiples, o reescribir el protocolo MCP a mano (se usa el SDK oficial).
- Búsqueda híbrida BM25 y resolución automática de contradicciones (puntos 2 y 3 de «Próximos
  pasos»): quedan mencionados como trabajo futuro en el README.

## 4. Anti objetivos

Cosas que harían fracasar el reto aunque el código funcione:

- **Que se parezca al repositorio de los compañeros.** Ni código, ni estructura, ni corpus, ni
  herramientas. La referencia solo sirvió para calibrar el alcance.
- **Que solo corra con una clave de pago.** Debe funcionar con una clave gratuita y degradar de
  forma honesta (modo simulado) cuando no hay clave.
- **Que la atribución del repositorio no sea solo de Kevin Cifuentes.** Sin coautores en los
  commits ni menciones a herramientas de IA en el historial.
- **Que el asistente se presente como asesor legal.** El corpus es una ley; el README y el propio
  prompt del sistema deben dejar claro que es un ejercicio académico y que las respuestas se
  verifican contra el texto citado.
- **Entregar métricas sin la conversación que las produjo.** Las evidencias (CSV, trazas,
  capturas) van versionadas en el repositorio.

## 5. Restricciones

| Restricción | Consecuencia en el diseño |
|---|---|
| Sin clave de Anthropic (no tiene capa gratuita) | `llm.py` se escribe con una interfaz de proveedor; se usa Google AI Studio (Gemini) como principal y Groq como alternativa, ambos sin tarjeta de crédito. Se mantiene la firma `llamar_llm(sistema, mensajes, max_tokens)` del tutorial. |
| El identificador del modelo es inestable (hay avisos de deprecación de `gemini-2.5-flash` y las fuentes se contradicen sobre qué sigue gratis) | El modelo se lee de `.env` (`MODELO_LLM`). Un subcomando `modelos` lista los que la clave tiene disponibles. Ningún identificador queda escrito en el código. |
| Capa gratuita con límite de peticiones por minuto | La evaluación RAGAS limita el número de preguntas, espacia las llamadas y guarda resultados parciales para poder reanudar. |
| La Ley 769 de 2002 está reformada varias veces (Ley 2251 y Ley 2283 de 2022, entre otras) | El corpus se versiona: `corpus/FUENTE.md` registra URL, entidad, fecha de descarga y vigencia conocida. Las multas no se leen como cifras del texto sino que se calculan desde múltiplos de SMLDV con el salario mínimo del año como parámetro. |
| Windows 11 con PowerShell | Los comandos del README se dan en PowerShell y en Bash. Nada de rutas al estilo `.venv/bin/python`. |
| Primera ejecución descarga ~470 MB (modelo de embeddings) | Documentado en el README; los embeddings son locales y no consumen API. |
| Español en todo el proyecto | Nombres de módulos, funciones, prompts, documentación y commits en español, como en los tutoriales. |
| Nada de secretos en el repositorio | `.env` ignorado, `.env.example` versionado, y `datos/` (Chroma y trazas con contenido de conversaciones) ignorado. |
| El SMLMV de 2026 está jurídicamente inestable: el Decreto 1469 de 2025 lo fijó en $1.750.905, el Consejo de Estado suspendió provisionalmente sus efectos y el Decreto 0159 de 2026 lo fijó de forma transitoria | Razón de más para que el salario sea parámetro de `.env` y no una cifra en el código. `.env.example` trae $1.750.905 etiquetado con su decreto y su fecha; `calcular_multa` **imprime siempre qué salario usó y de qué norma viene**, para que la cifra sea auditable y no una afirmación del asistente. |
| Python 3.11.9 es el intérprete instalado | Se exige `>=3.11`. Se evita a propósito Python 3.14, que en el repositorio de referencia obligó a un módulo de compatibilidad solo para que RAGAS funcionara. |
| No está confirmado que el plan gratuito de GitHub Copilot habilite servidores MCP (las fuentes se contradicen) | El entregable no puede depender de Copilot. El cliente MCP de respaldo es el **MCP Inspector** del paso 9 del tutorial, que corre con `uv run mcp dev` y no necesita cuenta. La bitácora documenta el cliente que se usó realmente. |

## 6. Enfoques considerados

### A. Tres subproyectos separados

Tres carpetas independientes, cada una proyecto `uv` propio: `proyecto-mcp/` (configuración del
servidor oficial), `mi-servidor/` (servidor MCP propio de notas) y `memoria-rag/` (las tres
memorias). Es la forma del repositorio de referencia.

- **A favor:** mapea uno a uno con los tutoriales, trivial de contrastar con la guía.
- **En contra:** el servidor MCP y la memoria quedan como dos tareas sin relación; `llm.py` y
  `almacen.py` duplicados en dos proyectos; el servidor propio se queda en un `notas.json` de
  juguete que no demuestra nada que la memoria de tres niveles no haga mejor.

### B. Un proyecto, dos puntos de entrada — **elegido**

Un único proyecto `uv` con el paquete `asistente/`: una sola configuración, un solo `llm.py`, una
sola base vectorial y un solo `gestor` que coordina las memorias. Encima, dos formas de usarlo:

1. `asistente chat`: el chat de consola del tutorial de RAG.
2. `asistente mcp`: un servidor MCP por stdio que expone esa misma memoria y ese mismo RAG como
   herramientas para Copilot en VS Code.

- **A favor:** el servidor MCP propio pasa a ser algo con sustancia (memoria persistente con RAG
  para Copilot) en lugar de un bloc de notas; cero duplicación; una sola historia que contar en
  la presentación.
- **En contra:** exige diseñar la frontera entre el gestor y las herramientas MCP, y obliga a
  documentar aparte los pasos del tutorial de MCP que son pura configuración.

### C. Replicar los dos tutoriales literalmente

Descartada. Los compañeros ya fijaron un techo más alto y el propio tutorial señala el RAG de
documentos y la evaluación como los pasos siguientes; entregar menos deja el trabajo por debajo
del nivel del curso.

**Decisión (Kevin, en conversación):** enfoque B.

## 7. El dominio: asistente de tránsito colombiano

Decisión mía, sobre la que Kevin dio vía libre, con el corpus intercambiable por si cambia de
idea.

- **Corpus:** Código Nacional de Tránsito Terrestre (Ley 769 de 2002), PDF público alojado por
  entidades del Estado (RUNT, ANI, Cancillería). Se escoge una copia, se registra su procedencia
  y se deja un comando para indexar cualquier otro PDF.
- **Por qué este corpus:** son artículos numerados, así que cada respuesta se puede citar y
  verificar contra el texto. Eso es exactamente lo que miden `faithfulness` y
  `context_precision`, y permite escribir respuestas de referencia para `context_recall` sin
  inventarlas.
- **Por qué este dominio luce las tres memorias:** el asistente recuerda datos duraderos del
  usuario (tipo de vehículo, ciudad, si es conductor nuevo) y con eso responde distinto a la
  misma pregunta. Es una demostración visible del largo plazo, no un detalle de laboratorio.
- **Por qué habilita una herramienta determinista:** las sanciones se expresan en múltiplos de
  SMLDV, no en pesos. Calcularlas es aritmética con un parámetro anual: algo que un LLM hace mal
  y una herramienta MCP hace bien. Es el mejor argumento de por qué existe MCP.

## 8. Arquitectura

```text
                        ┌─────────────────────────────────────────┐
  asistente chat  ────► │                                         │
  (consola)             │              GestorMemoria              │
                        │                                         │
  Copilot Chat          │  corto  ·  medio  ·  largo  ·  RAG doc  │
  (VS Code, Agente)     │                                         │
        │               └──────────────────┬──────────────────────┘
        │  stdio                           │
        └──► asistente mcp  ───────────────┘        ┌──────────────┐
             (FastMCP)                              │  ChromaDB    │
                                                    │  hechos      │
             llm.py ──► Gemini / Groq / simulado    │  sesiones    │
             multas.py ──► cálculo determinista     │  documentos  │
             trazas.py ──► datos/trazas.jsonl       └──────────────┘
```

### 8.1 Estructura de archivos

```text
reto2/
├── README.md                      # portada: qué es, cómo correrlo, resultados
├── .env.example
├── .gitignore
├── pyproject.toml                 # proyecto uv único
├── .vscode/mcp.json               # memory (npx), asistente (propio), fetch (uvx)
├── .github/copilot-instructions.md
├── corpus/
│   └── FUENTE.md                  # URL, entidad, fecha de descarga, vigencia
├── docs/
│   ├── superpowers/specs/         # este documento
│   ├── bitacora-mcp.md            # pasos de configuración del tutorial 1
│   ├── decisiones.md              # parámetros elegidos y por qué
│   └── capturas/                  # evidencia en VS Code
├── src/asistente/
│   ├── config.py                  # .env, rutas, parámetros en un solo sitio
│   ├── llm.py                     # proveedor + modo simulado
│   ├── almacen.py                 # cliente Chroma + embeddings locales
│   ├── memoria_corto.py           # ventana deslizante
│   ├── memoria_medio.py           # resumen progresivo + caducidad
│   ├── memoria_largo.py           # hechos: dedup, puntuación, refuerzo, olvido
│   ├── documentos.py              # extracción, chunking, ingesta del PDF
│   ├── rag.py                     # recuperación + respuesta citada
│   ├── multas.py                  # SMLDV -> pesos (determinista, sin LLM)
│   ├── gestor.py                  # orquesta las cuatro memorias
│   ├── trazas.py                  # registro JSONL por turno
│   ├── chat.py                    # entrada 1: consola
│   ├── servidor_mcp.py            # entrada 2: FastMCP por stdio
│   └── cli.py                     # subcomandos: chat, mcp, indexar, inspeccionar, modelos, evaluar
├── evaluacion/
│   ├── preguntas.json             # preguntas + respuesta de referencia + artículo
│   ├── evaluar.py                 # RAGAS 4 métricas -> CSV + resumen md
│   └── resultados/                # CSV y resumen versionados (evidencia)
├── tests/                         # pytest de las partes deterministas
└── datos/                         # ignorado: chroma/, trazas.jsonl
```

### 8.2 Decisiones de implementación

**Memorias.** Se respetan los mecanismos y los parámetros por defecto del tutorial
(`max_mensajes=10`, `max_caracteres=8000`, `dias_vigencia=14`, `distancia_max=0.6`,
`umbral_duplicado=0.15`, `k=5`, pesos 0.6/0.25/0.15, corte 0.35, `extraer_cada=6`),
centralizados en `config.py` para poder ajustarlos sin tocar la lógica. La expulsión por pares y
el mínimo de dos mensajes en la ventana se conservan tal cual: existen para no romper la
alternancia usuario/asistente que exigen los LLM.

**Cuarta colección, `documentos`.** Separada de `hechos` y `sesiones` porque su ciclo de vida es
distinto: no caduca, no se refuerza y no se extrae de la conversación. Chunking por caracteres
con solape, respetando límites de artículo cuando el texto lo permite; cada chunk guarda como
metadatos el número de artículo, la página y el nombre del documento, que es lo que permite
citar.

**`rag.py` responde solo con el contexto recuperado.** Si no hay chunks por encima del umbral, lo
dice en lugar de responder de memoria. Toda respuesta cita artículo y página.

**`multas.py` no usa LLM.** Tabla propia de infracciones (código, descripción, múltiplo de
SMLDV) construida a partir del texto indexado, más el salario mínimo del año como parámetro de
`.env`. Devuelve el cálculo desglosado para que se pueda verificar a mano.

**Herramientas del servidor MCP.** Los docstrings son el contrato que lee el modelo, así que se
escriben con cuidado:

| Herramienta | Qué hace |
|---|---|
| `consultar_normativa(pregunta)` | RAG sobre el corpus; devuelve respuesta con artículos citados. |
| `calcular_multa(codigo_o_smldv, salario_minimo?)` | Cálculo determinista desglosado. |
| `recordar(hecho, importancia)` | Guarda un hecho en el largo plazo, con deduplicación. |
| `buscar_recuerdo(consulta)` | Recupera hechos con la puntuación combinada. |
| `que_sabes_de_mi()` | Volcado legible de lo almacenado sobre el usuario. |
| `olvidar(consulta)` | Borra hechos parecidos (derecho al olvido). |

Nada de `print()` en el servidor: la salida estándar es del protocolo. Los mensajes de
diagnóstico van a `stderr` y a las trazas.

**La memoria se trata como datos, no como instrucciones.** El prompt del sistema la presenta en
secciones con título y cierra con «use esta información solo si es relevante», siguiendo la
advertencia del tutorial sobre texto almacenado que podría contener órdenes.

**Trazas.** Una línea JSONL por turno: marca de tiempo, pregunta, hechos y sesiones recuperados
con su puntuación, chunks con identificador y distancia, modelo usado, duración y si hubo
extracción de hechos. Sirve para depurar y es la evidencia de que el RAG recupera lo que dice
recuperar.

**Pruebas.** `pytest` sobre lo que no necesita clave ni red: ventana deslizante y expulsión por
pares, deduplicación por umbral, puntuación combinada y corte, decaimiento de recencia, filtro
de caducidad, chunking y extracción de número de artículo, y cálculo de multas. Los tutoriales no
piden pruebas; se incluyen porque es la forma de demostrar que los mecanismos están bien
implementados sin depender de una respuesta del LLM.

**Evaluación.** Entre 8 y 12 preguntas en `preguntas.json`, cada una con respuesta de referencia
tomada del artículo correspondiente (necesaria para `context_recall`). `evaluar.py` genera las
respuestas del RAG, calcula las cuatro métricas de RAGAS con el mismo LLM de la clave gratuita,
escribe `resultados/evaluacion.csv` y un resumen en Markdown con la media por métrica y la
interpretación de cada una. Guarda avance parcial por si el límite de peticiones corta la
ejecución.

## 9. Evidencias que quedan en el repositorio

Como no hay rúbrica, el repositorio tiene que demostrar por sí solo que todo se ejecutó:

1. `README.md` con arquitectura, instalación, comandos y resultados de la evaluación.
2. `docs/bitacora-mcp.md` con los pasos del tutorial de MCP y capturas en `docs/capturas/`:
   servidores corriendo, herramientas activas en el chat, una llamada aceptada, `memory.jsonl`
   con contenido.
3. `evaluacion/resultados/` con el CSV y el resumen de métricas.
4. Una traza de ejemplo anonimizada y una transcripción de las dos sesiones de prueba (la del
   tutorial: primera sesión da datos, segunda sesión los recuerda).
5. `docs/decisiones.md` con los parámetros ajustados y el efecto observado, usando el método que
   recomienda el tutorial (cambiar uno a la vez y repetir la misma conversación).

## 10. Decisiones resueltas en la revisión del diseño

Un revisor externo leyó este documento y señaló los puntos donde habría tenido que adivinar.
Estas son las decisiones tomadas, todas mías salvo donde se indica:

**10.1 Qué texto de la ley es el autoritativo.** El PDF indexado, y nada más. El asistente
responde «según el texto indexado, artículo X» y el README declara la fecha y la procedencia de
esa copia. Las respuestas de referencia de `preguntas.json` se escriben **leyendo el PDF
indexado**, no la ley vigente consolidada: si se mezclan, `context_recall` y `faithfulness`
dejan de medir el RAG y empiezan a medir el desfase del corpus. Las leyes reformatorias (2251 y
2283 de 2022) **no se indexan**; quedan declaradas como limitación conocida en el README y como
trabajo futuro, junto con la observación de que una respuesta de RAG vale lo que valga la fecha
de su corpus. La tabla de `multas.py` se construye desde el mismo PDF indexado, con el multiplo
de SMLDV y el artículo de origen anotados fila por fila.

**10.2 Cuándo se usa el RAG y cuándo no.** No todos los turnos pasan por el RAG. El gestor decide
por umbral de distancia: si el mejor fragmento recuperado no supera el umbral, el turno se
responde de forma conversacional, con las tres memorias pero sin citas. La regla «solo responde
con el contexto recuperado» rige la ruta de normativa (`consultar_normativa` y las preguntas de
ley), no la charla. Sin esto, un turno como «me llamo Kevin y tengo una moto en Medellín» caería
en la ruta de rechazo y la demostración de memoria parecería rota.

**10.3 Qué mide la evaluación.** `evaluar.py` llama a la **ruta de RAG desnuda**, sin memoria
inyectada en el prompt. Las métricas deben medir calidad de recuperación; si se les suma la
memoria del usuario, `faithfulness` empieza a medir otra cosa y el número deja de ser
interpretable. Queda escrito en el resumen de resultados para que nadie lo lea al revés.

**10.4 Las dos entradas no corren a la vez.** ChromaDB en modo `PersistentClient` es un SQLite de
un solo proceso: con el servidor MCP vivo dentro de VS Code y el chat de consola abierto al mismo
tiempo, aparecerían errores de bloqueo. Se documenta como requisito de uso («no ejecute `chat` y
`mcp` simultáneamente»), y el programa da un mensaje claro si detecta el bloqueo en lugar de
reventar con una traza de SQLite. Montar Chroma en modo servidor sería la solución real, pero es
complejidad que este reto no necesita.

**10.5 El medio plazo también se consolida desde MCP.** Un servidor MCP no tiene fin de turno ni
cierre garantizado, así que se añade una séptima herramienta, `cerrar_sesion()`, y además el
servidor consolida por inactividad. De lo contrario los resúmenes de sesión solo existirían en el
chat de consola y el nivel medio quedaría a medias en la mitad del entregable.

**10.6 El PDF de la ley se versiona en el repositorio.** Es norma pública colombiana y pesa pocos
megas. Sin él en el repositorio, el objetivo 6 (que un tercero reproduzca todo desde el README) y
la reproducibilidad de las métricas dependerían de que una URL estatal siga viva, y esas URL
caducan. `corpus/FUENTE.md` registra de dónde salió.

**10.7 Los commits los hago yo, sin ninguna línea de atribución** (decisión de Kevin, anterior a
esta revisión). Ni `Co-Authored-By`, ni menciones a herramientas de IA, ni en los mensajes de
commit ni en los de los pull requests. La identidad de Git de la máquina ya es la correcta.

**10.8 Orden de construcción: primero todo lo que no necesita clave.** Paquete, memorias,
ingesta, RAG, multas, servidor MCP, pruebas y README funcionan con embeddings locales y modo
simulado. La evaluación con RAGAS y la transcripción de las dos sesiones se ejecutan al final,
cuando haya clave. Así el repositorio nunca está en un estado donde falte lo que no dependía de
terceros.

## 11. Qué queda a criterio de quien implemente

- Tamaño y solape exactos de los chunks: se parte de 1000/150 caracteres y se ajusta según lo que
  muestren `context_precision` y `context_recall`.
- Estructura interna de la tabla de infracciones de `multas.py` y cuántas infracciones incluir
  (mínimo: las más consultadas, con su código del tipo `C29`).
- Biblioteca de extracción de PDF (`pypdf` como punto de partida) y cómo tratar encabezados y
  pies repetidos.
- Forma exacta del CLI (`argparse` o similar) y los nombres finales de los subcomandos.
- Redacción de los docstrings de las herramientas MCP, que es lo que determina si el modelo las
  usa en el momento correcto.
- Qué copia del PDF de la ley se indexa, entre las alojadas por entidades del Estado.
