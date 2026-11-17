# Bitacora: los pasos del tutorial de MCP

Que se ejecuto, con que resultado, y que queda pendiente de hacer a mano.
Fecha: 2026-11-17.

## Pasos 1 y 2: Node.js y uv

Ya estaban instalados en la maquina. Versiones comprobadas:

```text
node -v   ->  v24.18.0
npx -v    ->  11.16.0
uv --version -> uv 0.13.6
python --version -> Python 3.11.9
```

Node se necesita para el servidor `memory` oficial (se ejecuta con `npx`) y para
el MCP Inspector del paso 9, que corre sobre Node por debajo.

## Paso 3: VS Code

VS Code esta instalado, pero **la extension GitHub Copilot Chat no lo esta** y no
hay sesion de GitHub iniciada. Instalarla, iniciar sesion y aceptar las llamadas
a herramientas son pasos de interfaz grafica que hay que hacer a mano.

Ademas, no esta confirmado que el plan gratuito de Copilot habilite servidores
MCP: las fuentes publicas se contradicen. Por eso el entregable **no depende de
Copilot**: el cliente MCP de referencia de este proyecto es el MCP Inspector del
paso 9, que no necesita cuenta ni extension.

## Paso 4: estructura del proyecto

En lugar de las tres carpetas del tutorial (`proyecto-mcp`, `mi-servidor`,
`memoria-rag`) se uso un solo proyecto `uv` con dos puntos de entrada, para que
el servidor MCP y la memoria de tres niveles sean la misma pieza. El motivo esta
en el documento de diseno, seccion 6.

Lo que si se conserva del tutorial: `.vscode/mcp.json` y
`.github/copilot-instructions.md` en la raiz del repositorio.

## Paso 5: servidor de memoria oficial

Configurado en `.vscode/mcp.json`:

```json
"memory": {
  "type": "stdio",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-memory"],
  "env": { "MEMORY_FILE_PATH": "${workspaceFolder}/datos/memory.jsonl" }
}
```

El archivo apunta a `datos/`, que esta en `.gitignore`: tal como advierte el
tutorial, `memory.jsonl` es texto plano en disco y no debe subirse a Git.

## Paso 6: probar la memoria oficial

Pendiente de hacer a mano, porque requiere Copilot Chat en modo Agente. Pasos:

1. Abrir esta carpeta en VS Code.
2. `Ctrl+Shift+P` -> **MCP: List Servers** -> `memory` -> **Start**.
3. En el chat en modo **Agent**, con el icono de herramientas comprobar que las
   de `memory` estan activas.
4. Pedir: «usa el mcp memory. Recuerda que me llamo Kevin, vivo en Medellin y
   manejo una moto».
5. Aceptar la llamada a `create_entities`.
6. Abrir `datos/memory.jsonl` y comprobar que los datos estan ahi.
7. Abrir un chat nuevo y preguntar «¿Qué sabes de mí? Revisa tu memoria».

Capturas a guardar en `docs/capturas/`: el servidor en **Running**, el selector
de herramientas, la llamada aceptada y el contenido de `memory.jsonl`.

## Pasos 7 y 8: servidor MCP propio

Construido en `src/asistente/servidor_mcp.py` con `FastMCP`, siete herramientas
y stdio. Registrado en `.vscode/mcp.json`:

```json
"asistente-transito": {
  "type": "stdio",
  "command": "uv",
  "args": ["--directory", "${workspaceFolder}", "run", "asistente", "mcp"]
}
```

**Comprobado:** el servidor carga y registra sus siete herramientas. Se verifico
programaticamente, pidiendole al propio servidor su lista de herramientas:

```text
HERRAMIENTAS MCP: 7
  - consultar_normativa: Responde una pregunta sobre el Codigo Nacional de Transito colombiano.
  - calcular_multa: Calcula en pesos colombianos una multa de transito.
  - recordar: Guarda en la memoria a largo plazo un hecho duradero sobre el usuario.
  - buscar_recuerdo: Busca en la memoria a largo plazo los hechos relevantes para una consulta.
  - que_sabes_de_mi: Enumera todo lo que el asistente tiene guardado sobre el usuario.
  - olvidar: Borra de la memoria a largo plazo los hechos parecidos a un texto.
  - cerrar_sesion: Consolida la memoria al terminar una conversacion.
```

Dos detalles del tutorial que se respetaron:

- **Nada de `print()`** en el servidor: la salida estandar es del protocolo. El
  aviso de inicializacion va a `stderr`.
- Los **docstrings** son la descripcion que lee el modelo para decidir cuando
  usar cada herramienta, asi que estan escritos como contrato, indicando cuando
  usarla y cuando no (por ejemplo, `calcular_multa` dice explicitamente «use
  siempre esta herramienta en lugar de calcular la multa usted mismo»).

### Un tropiezo que vale documentar

La primera ejecucion fallo:

```text
ModuleNotFoundError: No module named 'mcp.server.fastmcp'.
This is mcp 2.x, where FastMCP was renamed to MCPServer
```

El SDK publicado hoy es la version 2.x y el tutorial esta escrito contra la 1.x.
Se fijo `mcp[cli]>=1.2,<2` en `pyproject.toml` a proposito, para mantener la API
del tutorial. Migrar a la 2.x queda como trabajo futuro.

## Paso 9: MCP Inspector

El Inspector es la via de depuracion que no necesita Copilot:

```bash
uv run mcp dev src/asistente/servidor_mcp.py
```

Abre una interfaz web; se pulsa **Connect**, se va a la pestana **Tools** y se
ejecuta cada herramienta con los parametros que se quieran. Si algo falla ahi,
el problema esta en el codigo y no en el cliente.

Pendiente: ejecutarlo y guardar la captura de la pestana **Tools** con las siete
herramientas listadas y el resultado de una llamada a `consultar_normativa`.

## Paso 10: servidor de terceros con uvx

Anadido al mismo `mcp.json`, como indica el tutorial:

```json
"fetch": { "type": "stdio", "command": "uvx", "args": ["mcp-server-fetch"] }
```

## Resumen del estado

| Paso | Estado |
|---|---|
| 1-2. Node y uv | hecho (ya instalados) |
| 3. VS Code | parcial: falta instalar Copilot Chat e iniciar sesion |
| 4. Estructura | hecho, con la variante justificada en el diseno |
| 5. Servidor `memory` | configurado |
| 6. Probar `memory` | pendiente, requiere interfaz grafica |
| 7-8. Servidor propio | hecho y verificado (7 herramientas) |
| 9. Inspector | comando listo, captura pendiente |
| 10. Servidor `fetch` con uvx | configurado |
