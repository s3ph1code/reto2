"""Memoria a corto plazo: los ultimos mensajes de la conversacion.

Es una ventana deslizante. Los mensajes que salen por un extremo no se tiran:
se devuelven para que la memoria a medio plazo los resuma.
"""

from __future__ import annotations

from . import config


class MemoriaCortoPlazo:
    def __init__(self, max_mensajes: int | None = None, max_caracteres: int | None = None):
        self.max_mensajes = max_mensajes or config.MAX_MENSAJES
        self.max_caracteres = max_caracteres or config.MAX_CARACTERES
        self.mensajes: list[dict] = []

    def _tamano(self) -> int:
        return sum(len(m["content"]) for m in self.mensajes)

    def agregar(self, rol: str, contenido: str) -> list[dict]:
        """Anade un mensaje y devuelve los que salen de la ventana.

        Se expulsan de dos en dos (pregunta y respuesta) para no romper la
        alternancia usuario/asistente que exigen los modelos, y nunca se vacia
        por completo: siempre queda al menos el ultimo intercambio.
        """
        self.mensajes.append({"role": rol, "content": contenido})
        expulsados: list[dict] = []
        while (
            len(self.mensajes) > self.max_mensajes
            or self._tamano() > self.max_caracteres
        ) and len(self.mensajes) > 2:
            expulsados.extend(self.mensajes[:2])
            self.mensajes = self.mensajes[2:]
        return expulsados

    def obtener(self) -> list[dict]:
        return list(self.mensajes)

    def vaciar(self) -> list[dict]:
        """Devuelve todo lo que queda y deja la ventana limpia (fin de sesion)."""
        restantes, self.mensajes = self.mensajes, []
        return restantes
