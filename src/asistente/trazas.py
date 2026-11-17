"""Registro de trazas: una linea JSON por turno de conversacion.

Sirve para depurar y, sobre todo, como evidencia: permite comprobar que el RAG
recupero de verdad los fragmentos que dice haber usado, con sus distancias.
"""

from __future__ import annotations

import json
import time
from typing import Any

from . import config


def registrar(evento: str, datos: dict[str, Any]) -> None:
    """Anade un evento al archivo de trazas. Nunca interrumpe la conversacion."""
    linea = {"momento": time.strftime("%Y-%m-%dT%H:%M:%S"), "evento": evento}
    linea.update(datos)
    try:
        config.DIR_DATOS.mkdir(parents=True, exist_ok=True)
        with open(config.ARCHIVO_TRAZAS, "a", encoding="utf-8") as archivo:
            archivo.write(json.dumps(linea, ensure_ascii=False) + "\n")
    except OSError:
        pass


def leer(limite: int = 20) -> list[dict]:
    """Devuelve las ultimas trazas registradas."""
    if not config.ARCHIVO_TRAZAS.exists():
        return []
    lineas = config.ARCHIVO_TRAZAS.read_text(encoding="utf-8").strip().splitlines()
    salida = []
    for linea in lineas[-limite:]:
        try:
            salida.append(json.loads(linea))
        except json.JSONDecodeError:
            continue
    return salida
