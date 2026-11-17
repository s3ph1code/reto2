# Instrucciones del proyecto

Este repositorio incluye el servidor MCP `asistente-transito`, que da memoria
persistente y consulta de normativa. Uselo asi:

- Al inicio de cada conversacion, recupere el contexto del usuario con
  `buscar_recuerdo` (o `que_sabes_de_mi` si necesita el listado completo).
- Cuando el usuario comparta datos duraderos —vehiculo, ciudad, preferencias,
  decisiones— guardelos con `recordar`, en frases cortas y en tercera persona.
- Para cualquier duda sobre normas de transito colombianas, use
  `consultar_normativa`: responde solo con el corpus indexado y cita articulo y
  pagina. No responda de memoria propia sobre la ley.
- Para convertir una multa a pesos use siempre `calcular_multa`. No haga la
  aritmetica usted mismo.
- Al terminar una conversacion larga, llame a `cerrar_sesion` para que el
  resumen de la sesion quede guardado.
- Si el usuario pide que se olvide algo, use `olvidar`.
- No guarde contrasenas, numeros de documento, placas ni datos bancarios.

Tambien esta configurado el servidor oficial `memory` (grafo de conocimiento) y
`fetch` (lectura de paginas web), ambos en `.vscode/mcp.json`.
