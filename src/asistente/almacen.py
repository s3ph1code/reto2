"""Almacen vectorial compartido por las memorias de medio y largo plazo y por
el RAG de documentos.

Cada memoria usa su propia coleccion dentro de la misma base de ChromaDB:

- `hechos`:      memoria a largo plazo
- `sesiones`:    memoria a medio plazo
- `documentos`:  fragmentos del corpus (Codigo Nacional de Transito)
"""

from __future__ import annotations

import sys

import chromadb
from chromadb.utils import embedding_functions

from . import config

_FUNCION_EMB = None


class ErrorAlmacen(RuntimeError):
    """La base vectorial no se pudo abrir o esta bloqueada por otro proceso."""


def crear_cliente(ruta: str | None = None) -> "chromadb.ClientAPI":
    """Abre (o crea) la base vectorial persistente en disco.

    ChromaDB en modo persistente es un SQLite de un solo proceso: no ejecute el
    chat de consola y el servidor MCP al mismo tiempo sobre la misma carpeta.
    """
    destino = ruta or str(config.DIR_CHROMA)
    config.DIR_CHROMA.mkdir(parents=True, exist_ok=True)
    try:
        return chromadb.PersistentClient(path=destino)
    except Exception as error:  # noqa: BLE001 - se reempaqueta con un mensaje util
        raise ErrorAlmacen(
            "No se pudo abrir la base vectorial en "
            f"{destino}. Si tiene el servidor MCP corriendo en VS Code, deten"
            "galo antes de usar el chat de consola (ChromaDB no admite dos "
            f"procesos sobre la misma carpeta). Detalle: {error}"
        ) from error


def funcion_embeddings():
    """Modelo de embeddings local (no consume API).

    Usa el multilingue del tutorial, que funciona bien en espanol. Si
    `sentence-transformers` no esta disponible, cae al modelo que trae ChromaDB
    para que el proyecto siga siendo ejecutable, avisando por la salida de
    errores.
    """
    global _FUNCION_EMB
    if _FUNCION_EMB is not None:
        return _FUNCION_EMB
    try:
        _FUNCION_EMB = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=config.MODELO_EMBEDDINGS
        )
    except Exception as error:  # noqa: BLE001
        print(
            f"[aviso] No se pudo cargar {config.MODELO_EMBEDDINGS} ({error}). "
            "Se usa el modelo por defecto de ChromaDB, de menor calidad en espanol.",
            file=sys.stderr,
        )
        _FUNCION_EMB = embedding_functions.DefaultEmbeddingFunction()
    return _FUNCION_EMB


def obtener_coleccion(cliente, nombre: str, funcion_emb=None):
    """Devuelve una coleccion que mide la similitud con la distancia coseno."""
    return cliente.get_or_create_collection(
        name=nombre,
        embedding_function=funcion_emb or funcion_embeddings(),
        metadata={"hnsw:space": "cosine"},
    )
