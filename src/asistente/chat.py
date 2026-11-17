"""Chat de consola: la primera de las dos entradas al asistente."""

from __future__ import annotations

from . import multas
from .gestor import GestorMemoria
from .llm import hay_clave, proveedor

AYUDA = """Comandos:
  salir                      cierra la sesion y consolida la memoria
  /memoria                   muestra lo que el asistente recuerda
  /olvida <texto>            borra los hechos parecidos a ese texto
  /multa <A|B|C|D|numero>    calcula una multa (herramienta determinista)
  /ayuda                     vuelve a mostrar esta lista
"""


def ejecutar() -> None:
    if not hay_clave():
        print(
            "[aviso] No hay clave de API configurada: el asistente responde en "
            "modo simulado.\n        Copie .env.example a .env y anada su clave "
            "para respuestas reales.\n"
        )
    else:
        print(f"[modelo] proveedor: {proveedor()}\n")

    gestor = GestorMemoria()
    print("Asistente de transito con memoria. Escriba 'salir' para terminar.")
    print(AYUDA)

    while True:
        try:
            texto = input("Usted: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            gestor.cerrar_sesion()
            print("Sesion guardada. Hasta pronto.")
            return

        if not texto:
            continue
        if texto.lower() in {"salir", "exit", "quit"}:
            gestor.cerrar_sesion()
            print("Sesion guardada. Hasta pronto.")
            return
        if texto.lower() in {"/ayuda", "ayuda", "/help"}:
            print(AYUDA)
            continue
        if texto.lower() == "/memoria":
            estado = gestor.inspeccionar()
            print(f"\nFragmentos del corpus: {estado['fragmentos_corpus']}")
            print(f"Resumenes de sesiones: {estado['sesiones']}")
            print(f"Mensajes en la ventana: {estado['mensajes_en_ventana']}")
            if estado["resumen_sesion"]:
                print(f"Resumen de esta sesion: {estado['resumen_sesion']}")
            print(f"Hechos ({len(estado['hechos'])}):")
            for hecho, meta in estado["hechos"]:
                print(f"  - {hecho}  [importancia {meta.get('importancia')}]")
            print()
            continue
        if texto.lower().startswith("/olvida"):
            consulta = texto[len("/olvida") :].strip()
            if not consulta:
                print("Indique que debe olvidar: /olvida mi ciudad\n")
                continue
            borrados = gestor.largo.olvidar(consulta)
            print(f"Hechos borrados: {borrados}\n")
            continue
        if texto.lower().startswith("/multa"):
            argumento = texto[len("/multa") :].strip()
            if not argumento:
                print(multas.tabla_tipos() + "\n")
                continue
            try:
                print("\n" + multas.formatear(multas.calcular(argumento)) + "\n")
            except multas.ErrorMulta as error:
                print(f"{error}\n")
            continue

        print(f"Asistente: {gestor.conversar(texto)}\n")
