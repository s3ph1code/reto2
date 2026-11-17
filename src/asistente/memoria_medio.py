"""Memoria a medio plazo: resumen de la sesion actual y de las sesiones recientes.

Tiene dos partes:

1. Un resumen progresivo de la sesion en curso, que crece integrando los
   mensajes que expulsa la ventana de corto plazo.
2. Los resumenes de sesiones anteriores, guardados en la base vectorial con su
   fecha y recuperados con RAG, pero solo si son recientes.
"""

from __future__ import annotations

import time
import uuid

from . import config
from .llm import ErrorLLM, llamar_llm

PROMPT_RESUMEN = (
    "Usted mantiene un resumen breve de una conversacion. Integre los mensajes "
    "nuevos en el resumen existente. Conserve decisiones, tareas pendientes, "
    "datos concretos y preferencias. Elimine saludos y repeticiones. "
    "Maximo 150 palabras."
)


def formatear(mensajes: list[dict]) -> str:
    return "\n".join(f"{m['role']}: {m['content']}" for m in mensajes)


class MemoriaMedioPlazo:
    def __init__(self, coleccion, dias_vigencia: int | None = None):
        self.coleccion = coleccion
        self.dias_vigencia = dias_vigencia or config.DIAS_VIGENCIA
        self.resumen_sesion = ""
        self.id_sesion = str(uuid.uuid4())

    def incorporar(self, mensajes: list[dict]) -> None:
        """Resumen progresivo: integra los mensajes que salen del corto plazo."""
        if not mensajes:
            return
        contenido = (
            f"Resumen actual:\n{self.resumen_sesion or '(vacio)'}\n\n"
            f"Mensajes nuevos:\n{formatear(mensajes)}"
        )
        try:
            self.resumen_sesion = llamar_llm(
                PROMPT_RESUMEN, [{"role": "user", "content": contenido}]
            )
        except ErrorLLM:
            # Si el proveedor falla, se conserva el resumen anterior: perder una
            # actualizacion del resumen es preferible a romper la conversacion.
            pass

    def cerrar_sesion(self) -> bool:
        """Guarda el resumen de la sesion en la base vectorial, con su fecha."""
        if not self.resumen_sesion:
            return False
        self.coleccion.add(
            ids=[self.id_sesion],
            documents=[self.resumen_sesion],
            metadatas=[{"timestamp": time.time(), "tipo": "resumen_sesion"}],
        )
        self.resumen_sesion = ""
        self.id_sesion = str(uuid.uuid4())
        return True

    def recuperar(
        self, consulta: str, k: int | None = None, distancia_max: float | None = None
    ) -> list[str]:
        """RAG con filtro temporal: solo resumenes de los ultimos N dias."""
        total = self.coleccion.count()
        if total == 0:
            return []
        tope = k or config.K_SESIONES
        corte = distancia_max if distancia_max is not None else config.DISTANCIA_MAX_SESIONES
        limite = time.time() - self.dias_vigencia * 86400
        resultado = self.coleccion.query(
            query_texts=[consulta],
            n_results=min(tope, total),
            where={"timestamp": {"$gte": limite}},
        )
        documentos = resultado.get("documents") or [[]]
        distancias = resultado.get("distances") or [[]]
        if not documentos[0]:
            return []
        return [
            doc
            for doc, dist in zip(documentos[0], distancias[0])
            if dist <= corte
        ]

    def purgar_caducados(self) -> None:
        """Borra los resumenes que superan el periodo de vigencia."""
        limite = time.time() - self.dias_vigencia * 86400
        self.coleccion.delete(where={"timestamp": {"$lt": limite}})
