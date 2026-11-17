# Decisiones y ajuste de parametros

Las dos decisiones que mas cambiaron la calidad del asistente se tomaron
midiendo, no por intuicion. Quedan aqui documentadas con sus numeros.

---

## 1. Trocear por articulo en lugar de cada N caracteres

**Problema observado.** Con el troceado clasico (1000 caracteres con 150 de
solape) la evaluacion dio `acierto@4 = 0.333`. Al mirar el detalle, la busqueda
no estaba fallando: recuperaba fragmentos del tema correcto, pero etiquetados
con el **articulo vecino**.

| Pregunta | Articulo correcto | Articulos recuperados |
|---|---|---|
| Que seguro deben tener los vehiculos | 42 | 24, 30, 60, 50 |
| Que dice la norma sobre alcoholemia | 152 | 151, 153, 2, 130 |
| Como se otorga la licencia por primera vez | 17 | 18, 25, 19, 54 |
| Como se liquidan las multas | 131 | 137, 130, 136, 160 |

La causa: un trozo de 1000 caracteres empieza en mitad de un articulo y acaba
dentro del siguiente, y la etiqueta se quedaba con el primer numero que
aparecia en el trozo, que casi siempre era el del articulo anterior.

**Cambio.** `fragmentar()` parte primero el texto en los encabezados
`ARTICULO N` y solo subdivide los articulos mas largos que el tamano maximo. La
ley esta escrita en articulos: el troceado ahora sigue la estructura del
documento en lugar de imponerle una cuadricula.

**Resultado.**

| Metrica | Antes (cuadricula) | Despues (por articulo) |
|---|---|---|
| acierto@4 | 0.333 | **0.833** |
| precision@4 | 0.083 | **0.271** |
| MRR | 0.333 | **0.639** |
| distancia media | 0.2796 | 0.2492 |
| fragmentos | 252 | 291 |

---

## 2. El umbral que decide si un turno usa el RAG

**Problema observado.** Con el umbral inicial de 0.95, el saludo
"Hola, me llamo Kevin y manejo una moto en Medellin" se iba por la ruta de RAG y
el asistente contestaba con articulos de la ley en lugar de conversar. La
demostracion de la memoria parecia rota.

**Medicion.** Distancia del mejor fragmento recuperado, por tipo de turno:

| Turnos de charla | Distancia | Preguntas de normativa | Distancia |
|---|---|---|---|
| Hola, me llamo Kevin y manejo una moto | 0.7104 | Cual es el limite de velocidad en zona urbana | 0.2049 |
| Gracias, muy amable | 0.7245 | Donde esta prohibido estacionar | 0.2555 |
| Prefiero que me respondas corto | 0.7537 | Que equipo de carretera debo llevar | 0.4066 |
| Como estas | 0.7914 | Cuanto vale una multa tipo C | 0.4468 |
| Que sabes de mi | 0.8231 | Necesito el SOAT para transitar | 0.6064 |
| Me gusta el futbol y programar en Python | 0.8370 | | |

Los dos grupos no se solapan: la normativa llega hasta 0.6064 y la charla
empieza en 0.7104.

**Decision.** `DISTANCIA_MAX_DOCUMENTOS = 0.65`, justo en el hueco, con margen
por los dos lados. Por debajo, el turno se responde con el corpus y con citas;
por encima, como conversacion con las tres memorias.

### Pero el umbral solo no bastaba

Al probar el umbral con frases nuevas aparecieron dos fallos claros:

| Turno | Distancia | Con solo el umbral | Deberia ser |
|---|---|---|---|
| `Gracias!` | 0.649 | RAG | charla |
| `Necesito el SOAT?` | 0.806 | charla | RAG |

Las frases muy cortas producen embeddings inestables: con pocas palabras, la
distancia deja de ser informativa. "Gracias, muy amable" medio 0.7245, pero
"Gracias!" a secas cayo a 0.649 y se colaba en el corpus.

**Decision.** El enrutador (`rag.decidir_ruta`) usa tres senales en lugar de
una:

1. un turno de menos de 15 caracteres sin vocabulario legal es charla, sin
   mirar la distancia;
2. si el turno menciona vocabulario de normativa (`SOAT`, `multa`, `licencia`,
   `velocidad`, `estacionar`, `articulo`...), se acepta una distancia mas
   holgada, `DISTANCIA_CON_SENAL = 0.90`;
3. si no hay vocabulario legal, se exige el umbral estricto de 0.65.

**Resultado.** 9 de 9 turnos de prueba enrutados correctamente, y el
comportamiento quedo fijado en `tests/test_rutas.py` con las distancias reales
medidas, para que un cambio futuro de umbral no lo rompa en silencio.

Cuando el usuario llama a la herramienta `consultar_normativa` no se aplica el
enrutador: ya pidio normativa explicitamente, asi que basta el criterio amplio.

---

## 3. Se fija la version 1.x del SDK de MCP

El SDK publicado hoy es `mcp` 2.x, donde `FastMCP` paso a llamarse `MCPServer` y
la API cambio. El tutorial del reto esta escrito contra la 1.x
(`from mcp.server.fastmcp import FastMCP`), asi que `pyproject.toml` fija
`mcp[cli]>=1.2,<2` a proposito. Es una decision consciente, no un descuido:
migrar a la 2.x es trabajo futuro anotado en el README.

---

## 4. Sin llamadas al LLM en la evaluacion

Las metricas miden **recuperacion**, no redaccion: para cada pregunta se sabe
que articulo del corpus la responde y se comprueba si aparece entre los k
fragmentos recuperados. Eso tiene tres ventajas sobre evaluar la respuesta
generada: no gasta cuota de API, es reproducible por cualquiera que clone el
repositorio, y aisla el componente que de verdad se construyo aqui.

Tambien es la razon de que la evaluacion llame a la ruta de RAG desnuda, sin la
memoria del usuario en el prompt: con la memoria inyectada, las metricas dejarian
de medir la calidad de la busqueda.

---

## Parametros que se dejaron como en el tutorial

`max_mensajes=10`, `max_caracteres=8000`, `dias_vigencia=14`,
`umbral_duplicado=0.15`, `k=5` para hechos, pesos 0.60 / 0.25 / 0.15, corte de
puntuacion 0.35 y `extraer_cada=6`. No se tocaron porque no habia evidencia para
cambiarlos; todos son ajustables desde `.env` sin modificar codigo.
