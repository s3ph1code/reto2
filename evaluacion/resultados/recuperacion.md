# Resultados de la evaluacion de recuperacion

- Fecha: 2026-11-17 12:48
- Corpus: `ley-769-2002-cnt.pdf` (291 fragmentos)
- Fragmentos recuperados por pregunta (k): 4
- Preguntas: 12

## Medias

| Metrica | Valor | Que significa |
|---|---|---|
| acierto@4 | 0.833 | proporcion de preguntas en las que el articulo correcto aparece entre los k fragmentos |
| precision@4 | 0.271 | que parte de los fragmentos recuperados pertenece al articulo correcto |
| MRR | 0.639 | 1/posicion del primer fragmento correcto; 1.0 es acertar siempre de primero |
| distancia media | 0.2492 | distancia coseno del mejor fragmento (0 = identico) |

## Detalle por pregunta

| Pregunta | Art. esperado | Art. recuperados | Acierto | Precision | MRR | Dist. |
|---|---|---|---|---|---|---|
| Que equipo de carretera debe portar todo vehiculo para transitar? | 30 | 60, 68, 30, 68 | 1 | 0.25 | 0.333 | 0.2356 |
| Que seguro deben tener los vehiculos para poder circular en Colombia? | 42 | 24, 25, 60, 41 | 0 | 0.0 | 0.0 | 0.3214 |
| Cuanto tiempo vale la licencia de conduccion de un vehiculo particular? | 22 | 122, 22, 24, 47 | 1 | 0.25 | 0.5 | 0.2259 |
| En que casos debo bajar la velocidad a treinta kilometros por hora? | 74 | 74, 108, 106, 107 | 1 | 0.25 | 1.0 | 0.2198 |
| Donde esta prohibido estacionar el carro? | 76 | 76, 127, 76, 69 | 1 | 0.5 | 1.0 | 0.2206 |
| Como se liquidan las multas de transito? | 131 | 140, 131, 93, 134 | 1 | 0.25 | 0.5 | 0.2178 |
| Que exige la revision tecnico-mecanica y de gases? | 28 | 53, 52, 51, 122 | 0 | 0.0 | 0.0 | 0.2634 |
| Como se otorga la licencia de conduccion por primera vez? | 17 | 17, 19, 24, 22 | 1 | 0.25 | 1.0 | 0.1649 |
| Ante quien se matricula un vehiculo? | 39 | 46, 2, 39, 37 | 1 | 0.25 | 0.333 | 0.3376 |
| Que dice la norma sobre el grado de alcoholemia? | 152 | 152, 152, 150, 131 | 1 | 0.5 | 1.0 | 0.3616 |
| Como se deben usar los carriles en una via de un solo sentido? | 68 | 68, 68, 60, 94 | 1 | 0.5 | 1.0 | 0.2143 |
| Cual es el limite de velocidad en zonas urbanas? | 106 | 106, 74, 120, 108 | 1 | 0.25 | 1.0 | 0.2074 |

## Como leer esto

Se evalua la ruta de RAG desnuda, sin memoria del usuario en el prompt:
lo que se mide es la calidad de la recuperacion, no la del modelo. Las
metricas no necesitan clave de API ni llamadas al LLM, asi que son
reproducibles por cualquiera que clone el repositorio e indexe el corpus.

El articulo esperado de cada pregunta se tomo leyendo el PDF indexado, no
la ley consolidada vigente. Una respuesta de RAG vale lo que valga la
fecha de su corpus.
