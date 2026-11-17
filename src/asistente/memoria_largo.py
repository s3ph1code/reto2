"""Memoria a largo plazo: hechos duraderos recuperados con RAG.

No guarda conversaciones sino hechos atomicos: frases cortas, independientes y
en tercera persona ("El usuario conduce una motocicleta"). Guardar hechos
pequenos hace la busqueda por similitud mas precisa y permite actualizar o
borrar un dato concreto.
"""

from __future__ import annotations

import json
import math
import time
import uuid

from . import config
from .llm import ErrorLLM, llamar_llm

PROMPT_EXTRACCION = (
    "Extraiga de la conversacion los hechos que conviene recordar de forma "
    "permanente: datos del usuario, preferencias estables, decisiones y "
    "conocimientos importantes. Ignore lo trivial o temporal. NO guarde "
    "contrasenas, numeros de documento, placas, datos bancarios ni datos de "
    "salud. Responda SOLO con un JSON valido con esta forma: "
    '[{"hecho": "texto breve en tercera persona", "importancia": 1-10}]. '
    "Si no hay nada que recordar, responda []."
)


class MemoriaLargoPlazo:
    def __init__(self, coleccion, umbral_duplicado: float | None = None):
        self.coleccion = coleccion
        self.umbral_duplicado = (
            umbral_duplicado if umbral_duplicado is not None else config.UMBRAL_DUPLICADO
        )

    # ------------------------------------------------------------ guardar
    def guardar_hecho(self, hecho: str, importancia: int = 5) -> str:
        """Guarda un hecho. Si ya existe uno casi identico, lo actualiza.

        La deduplicacion reutiliza el identificador del hecho parecido y usa
        `upsert`, asi que decir dos veces lo mismo no crea dos registros.
        """
        ahora = time.time()
        id_hecho = str(uuid.uuid4())
        if self.coleccion.count() > 0:
            previo = self.coleccion.query(query_texts=[hecho], n_results=1)
            distancias = (previo.get("distances") or [[]])[0]
            identificadores = (previo.get("ids") or [[]])[0]
            if distancias and distancias[0] < self.umbral_duplicado:
                id_hecho = identificadores[0]
        self.coleccion.upsert(
            ids=[id_hecho],
            documents=[hecho],
            metadatas=[
                {"importancia": int(importancia), "creado": ahora, "ultimo_acceso": ahora}
            ],
        )
        return id_hecho

    def extraer_y_guardar(self, mensajes: list[dict]) -> list[str]:
        """Pide al LLM que extraiga hechos de la conversacion y los guarda."""
        if not mensajes:
            return []
        texto = "\n".join(f"{m['role']}: {m['content']}" for m in mensajes)
        try:
            salida = llamar_llm(PROMPT_EXTRACCION, [{"role": "user", "content": texto}])
        except ErrorLLM:
            return []
        try:
            limpio = salida.replace("```json", "").replace("```", "").strip()
            hechos = json.loads(limpio)
        except json.JSONDecodeError:
            # Es preferible perder un hecho a que el programa falle.
            return []
        if not isinstance(hechos, list):
            return []
        guardados = []
        for item in hechos:
            if isinstance(item, dict) and item.get("hecho"):
                try:
                    importancia = int(item.get("importancia", 5))
                except (TypeError, ValueError):
                    importancia = 5
                self.guardar_hecho(str(item["hecho"]), importancia)
                guardados.append(str(item["hecho"]))
        return guardados

    # ---------------------------------------------------------- recuperar
    def puntuar(self, similitud: float, importancia: float, dias: float) -> float:
        """Puntuacion combinada: similitud, importancia y recencia."""
        recencia = math.exp(-dias / config.VIDA_MEDIA_DIAS)
        return (
            config.PESO_SIMILITUD * similitud
            + config.PESO_IMPORTANCIA * (importancia / 10)
            + config.PESO_RECENCIA * recencia
        )

    def recuperar(self, consulta: str, k: int | None = None) -> list[str]:
        """Trae candidatos por similitud y los reordena con la puntuacion.

        Recuperar solo por similitud dejaria que un dato trivial pero parecido a
        la pregunta desplazara a uno importante; de ahi los tres factores.
        """
        total = self.coleccion.count()
        if total == 0:
            return []
        tope = k or config.K_HECHOS
        resultado = self.coleccion.query(
            query_texts=[consulta], n_results=min(config.CANDIDATOS_HECHOS, total)
        )
        ids = (resultado.get("ids") or [[]])[0]
        docs = (resultado.get("documents") or [[]])[0]
        metas = (resultado.get("metadatas") or [[]])[0]
        dists = (resultado.get("distances") or [[]])[0]
        ahora = time.time()
        puntuados = []
        for id_, doc, meta, dist in zip(ids, docs, metas, dists):
            meta = meta or {}
            dias = (ahora - float(meta.get("ultimo_acceso", ahora))) / 86400
            puntuacion = self.puntuar(1 - dist, float(meta.get("importancia", 5)), dias)
            puntuados.append((puntuacion, id_, doc, dict(meta)))
        # Se ordena solo por la puntuacion: incluir el resto de la tupla haria
        # que Python intentara comparar diccionarios cuando hay empates.
        puntuados.sort(key=lambda p: p[0], reverse=True)
        elegidos = [p for p in puntuados[:tope] if p[0] > config.CORTE_PUNTUACION]
        if elegidos:
            # Refuerzo: lo que se recuerda se refresca, como en la memoria humana.
            self.coleccion.update(
                ids=[p[1] for p in elegidos],
                metadatas=[{**p[3], "ultimo_acceso": ahora} for p in elegidos],
            )
        return [p[2] for p in elegidos]

    def todos(self) -> list[tuple[str, dict]]:
        """Devuelve todos los hechos con sus metadatos, para inspeccion."""
        if self.coleccion.count() == 0:
            return []
        datos = self.coleccion.get()
        return list(zip(datos.get("documents") or [], datos.get("metadatas") or []))

    def olvidar(self, consulta: str, umbral: float = 0.3) -> int:
        """Borra los hechos muy parecidos a la consulta (derecho al olvido)."""
        if self.coleccion.count() == 0:
            return 0
        resultado = self.coleccion.query(
            query_texts=[consulta], n_results=min(3, self.coleccion.count())
        )
        ids = [
            i
            for i, d in zip(
                (resultado.get("ids") or [[]])[0], (resultado.get("distances") or [[]])[0]
            )
            if d < umbral
        ]
        if ids:
            self.coleccion.delete(ids=ids)
        return len(ids)
