"""Linea de comandos del proyecto.

    asistente chat           chat de consola con memoria
    asistente mcp            arranca el servidor MCP por stdio
    asistente indexar        ingesta los documentos de corpus/ en la base
    asistente inspeccionar   muestra que hay guardado en la memoria
    asistente modelos        lista los modelos que permite su clave
    asistente multa A        calcula una multa (sin LLM)
    asistente evaluar        mide la calidad de la recuperacion
"""

from __future__ import annotations

import argparse
import sys

from . import config, multas, trazas


def _indexar(_args) -> int:
    from .almacen import crear_cliente, obtener_coleccion
    from .documentos import documentos_del_corpus, indexar

    archivos = documentos_del_corpus()
    if not archivos:
        print(f"No hay documentos indexables en {config.DIR_CORPUS}")
        return 1
    coleccion = obtener_coleccion(crear_cliente(), config.COL_DOCUMENTOS)
    total = 0
    for ruta in archivos:
        print(f"Indexando {ruta.name} ...")
        cantidad = indexar(coleccion, ruta)
        print(f"  {cantidad} fragmentos")
        total += cantidad
    print(f"\nListo. {total} fragmentos en la coleccion '{config.COL_DOCUMENTOS}'.")
    return 0


def _inspeccionar(_args) -> int:
    from .gestor import GestorMemoria

    estado = GestorMemoria().inspeccionar()
    print(f"Fragmentos del corpus : {estado['fragmentos_corpus']}")
    print(f"Resumenes de sesiones : {estado['sesiones']}")
    print(f"Hechos a largo plazo  : {len(estado['hechos'])}")
    for hecho, meta in estado["hechos"]:
        print(
            f"  - {hecho}\n      importancia {meta.get('importancia')}, "
            f"ultimo acceso {meta.get('ultimo_acceso')}"
        )
    ultimas = trazas.leer(5)
    if ultimas:
        print(f"\nUltimas {len(ultimas)} trazas:")
        for linea in ultimas:
            print(
                f"  [{linea.get('momento')}] {linea.get('evento')} "
                f"ruta={linea.get('ruta', '-')} "
                f"fragmentos={len(linea.get('fragmentos', []))}"
            )
    return 0


def _modelos(_args) -> int:
    from .llm import hay_clave, modelos_disponibles, proveedor

    if not hay_clave():
        print(
            "No hay clave configurada. Copie .env.example a .env y anada\n"
            "GEMINI_API_KEY (https://aistudio.google.com/apikey) o\n"
            "GROQ_API_KEY  (https://console.groq.com)."
        )
        return 1
    print(f"Proveedor: {proveedor()}")
    print(f"Modelo configurado: {config.MODELO_LLM}\n")
    nombres = modelos_disponibles()
    print(f"Modelos disponibles para su clave ({len(nombres)}):")
    for nombre in nombres:
        marca = " <- configurado" if nombre == config.MODELO_LLM else ""
        print(f"  {nombre}{marca}")
    return 0


def _multa(args) -> int:
    if not args.infraccion:
        print(multas.tabla_tipos())
        return 0
    try:
        print(multas.formatear(multas.calcular(args.infraccion, args.salario)))
    except multas.ErrorMulta as error:
        print(f"Error: {error}")
        return 1
    return 0


def _chat(_args) -> int:
    from .chat import ejecutar

    ejecutar()
    return 0


def _mcp(_args) -> int:
    from .servidor_mcp import ejecutar

    ejecutar()
    return 0


def _evaluar(args) -> int:
    from .evaluacion import ejecutar

    return ejecutar(k=args.k)


def main(argv: list[str] | None = None) -> int:
    analizador = argparse.ArgumentParser(
        prog="asistente",
        description=(
            "Asistente de transito con memoria de tres niveles, RAG sobre el "
            "Codigo Nacional de Transito y servidor MCP."
        ),
    )
    sub = analizador.add_subparsers(dest="comando")

    sub.add_parser("chat", help="chat de consola con memoria").set_defaults(func=_chat)
    sub.add_parser("mcp", help="servidor MCP por stdio").set_defaults(func=_mcp)
    sub.add_parser("indexar", help="ingesta los documentos de corpus/").set_defaults(
        func=_indexar
    )
    sub.add_parser("inspeccionar", help="muestra la memoria guardada").set_defaults(
        func=_inspeccionar
    )
    sub.add_parser("modelos", help="lista los modelos de su clave").set_defaults(
        func=_modelos
    )

    p_multa = sub.add_parser("multa", help="calcula una multa (sin LLM)")
    p_multa.add_argument("infraccion", nargs="?", help="tipo A, B, C, D o numero de SMLDV")
    p_multa.add_argument(
        "--salario", type=float, default=None, help="salario minimo mensual en pesos"
    )
    p_multa.set_defaults(func=_multa)

    p_eval = sub.add_parser("evaluar", help="mide la calidad de la recuperacion")
    p_eval.add_argument("--k", type=int, default=None, help="fragmentos por pregunta")
    p_eval.set_defaults(func=_evaluar)

    args = analizador.parse_args(argv)
    if not getattr(args, "func", None):
        analizador.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
