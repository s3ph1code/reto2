"""Servidor MCP: la segunda entrada al asistente.

Expone por stdio la misma memoria de tres niveles y el mismo RAG que usa el chat
de consola, para que un cliente MCP (Copilot Chat en modo Agente, o el MCP
Inspector) pueda usarlos como herramientas.

Importante: nada de `print()` aqui. La salida estandar esta reservada para los
mensajes del protocolo y cualquier texto adicional rompe la comunicacion. Los
avisos van a la salida de errores.
"""

from __future__ import annotations

import sys

from mcp.server.fastmcp import FastMCP

from . import multas
from .gestor import GestorMemoria

mcp = FastMCP("asistente-transito")

_gestor: GestorMemoria | None = None


def gestor() -> GestorMemoria:
    """Crea el gestor la primera vez que se necesita.

    Se construye tarde a proposito: cargar el modelo de embeddings tarda unos
    segundos y no debe retrasar el arranque del servidor.
    """
    global _gestor
    if _gestor is None:
        print("[asistente] inicializando memoria y corpus...", file=sys.stderr)
        _gestor = GestorMemoria()
    return _gestor


@mcp.tool()
def consultar_normativa(pregunta: str) -> str:
    """Responde una pregunta sobre el Codigo Nacional de Transito colombiano.

    Busca en el corpus indexado (Ley 769 de 2002) los fragmentos mas parecidos a
    la pregunta y responde unicamente con ellos, citando articulo y pagina. Si
    el corpus no contiene la respuesta, lo dice en lugar de inventarla.
    Use esta herramienta para cualquier duda sobre normas, requisitos,
    documentos obligatorios, senales o sanciones de transito en Colombia.
    """
    resultado = gestor().consultar_normativa(pregunta)
    texto = resultado["respuesta"]
    if resultado["fuentes"]:
        texto += "\n\nFuentes: " + "; ".join(resultado["fuentes"])
    return texto


@mcp.tool()
def calcular_multa(tipo_o_smldv: str, salario_mensual: float = 0) -> str:
    """Calcula en pesos colombianos una multa de transito.

    El Codigo Nacional de Transito expresa las multas en multiplos de salario
    minimo legal diario vigente (SMLDV), no en pesos. Esta herramienta hace la
    conversion de forma exacta y devuelve el calculo desglosado con la norma de
    la que sale el salario usado.

    Parametros:
      tipo_o_smldv: el tipo de infraccion del articulo 131 ("A", "B", "C" o
        "D") o directamente un numero de SMLDV (por ejemplo "45").
      salario_mensual: salario minimo mensual en pesos. Deje 0 para usar el
        configurado en el proyecto.

    Use siempre esta herramienta en lugar de calcular la multa usted mismo.
    """
    try:
        calculo = multas.calcular(
            tipo_o_smldv, salario_mensual if salario_mensual > 0 else None
        )
    except multas.ErrorMulta as error:
        return f"No se pudo calcular: {error}\n\n{multas.tabla_tipos()}"
    return multas.formatear(calculo)


@mcp.tool()
def recordar(hecho: str, importancia: int = 5) -> str:
    """Guarda en la memoria a largo plazo un hecho duradero sobre el usuario.

    El hecho debe ser una frase corta, independiente y en tercera persona, por
    ejemplo "El usuario conduce una motocicleta en Medellin". La importancia va
    de 1 a 10 y pesa en la recuperacion posterior. Si ya existe un hecho casi
    identico, se actualiza en lugar de duplicarse.
    No guarde contrasenas, numeros de documento, placas ni datos bancarios.
    """
    identificador = gestor().largo.guardar_hecho(hecho, importancia)
    return f"Hecho guardado (id {identificador[:8]}): {hecho}"


@mcp.tool()
def buscar_recuerdo(consulta: str) -> list[str]:
    """Busca en la memoria a largo plazo los hechos relevantes para una consulta.

    Ordena los resultados combinando similitud con la consulta, importancia del
    hecho y cuan recientemente se uso, y refresca los que devuelve. Uselo al
    empezar una conversacion para recuperar contexto sobre el usuario.
    """
    return gestor().largo.recuperar(consulta)


@mcp.tool()
def que_sabes_de_mi() -> str:
    """Enumera todo lo que el asistente tiene guardado sobre el usuario.

    Devuelve los hechos de la memoria a largo plazo con su importancia, mas el
    recuento de resumenes de sesiones y de fragmentos del corpus. Sirve para que
    el usuario pueda revisar y controlar lo que se almaceno sobre el.
    """
    estado = gestor().inspeccionar()
    lineas = [
        f"Fragmentos del corpus indexados: {estado['fragmentos_corpus']}",
        f"Resumenes de sesiones guardados: {estado['sesiones']}",
        f"Hechos sobre el usuario: {len(estado['hechos'])}",
    ]
    for hecho, meta in estado["hechos"]:
        lineas.append(f"  - {hecho} [importancia {meta.get('importancia')}]")
    return "\n".join(lineas)


@mcp.tool()
def olvidar(consulta: str) -> str:
    """Borra de la memoria a largo plazo los hechos parecidos a un texto.

    Es el derecho al olvido: uselo cuando el usuario pida expresamente que se
    olvide algo o cuando un dato deje de ser cierto. El borrado es definitivo.
    """
    borrados = gestor().largo.olvidar(consulta)
    return f"Hechos borrados: {borrados}"


@mcp.tool()
def cerrar_sesion() -> str:
    """Consolida la memoria al terminar una conversacion.

    Vacia la ventana de corto plazo hacia el resumen de la sesion, extrae los
    hechos pendientes a la memoria a largo plazo y guarda el resumen con su
    fecha en la coleccion de sesiones. Llamela al final de una conversacion
    larga: un servidor MCP no tiene un cierre automatico que lo haga.
    """
    gestor().cerrar_sesion()
    return "Sesion consolidada: resumen guardado y hechos extraidos."


def ejecutar() -> None:
    """Arranca el servidor por stdio (como lo lanza VS Code)."""
    mcp.run()


if __name__ == "__main__":
    ejecutar()
