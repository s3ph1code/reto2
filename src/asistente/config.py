"""Configuracion central: rutas, parametros y variables de entorno.

Todos los parametros ajustables del asistente viven aqui, para poder cambiarlos
sin tocar la logica. Los valores por defecto son los del tutorial del reto.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parents[2]
load_dotenv(RAIZ / ".env")


def _entero(nombre: str, defecto: int) -> int:
    try:
        return int(os.environ.get(nombre, defecto))
    except ValueError:
        return defecto


def _decimal(nombre: str, defecto: float) -> float:
    try:
        return float(os.environ.get(nombre, defecto))
    except ValueError:
        return defecto


# ---------------------------------------------------------------- rutas
DIR_DATOS = RAIZ / "datos"
DIR_CHROMA = DIR_DATOS / "chroma"
ARCHIVO_TRAZAS = DIR_DATOS / "trazas.jsonl"
DIR_CORPUS = RAIZ / "corpus"
DIR_EVALUACION = RAIZ / "evaluacion"

# ------------------------------------------------------------------ LLM
# El identificador del modelo NO se escribe en el codigo: los nombres cambian y
# se deprecan. Se lee del entorno y `asistente modelos` lista los disponibles.
PROVEEDOR_LLM = os.environ.get("PROVEEDOR_LLM", "gemini").strip().lower()
MODELO_LLM = os.environ.get("MODELO_LLM", "gemini-2.5-flash").strip()
CLAVE_GEMINI = os.environ.get("GEMINI_API_KEY", "").strip()
CLAVE_GROQ = os.environ.get("GROQ_API_KEY", "").strip()
MAX_TOKENS = _entero("MAX_TOKENS", 1024)

# ---------------------------------------------------------- embeddings
# Modelo multilingue: entiende espanol. Es local y no consume API.
MODELO_EMBEDDINGS = os.environ.get(
    "MODELO_EMBEDDINGS", "paraphrase-multilingual-MiniLM-L12-v2"
).strip()

# ------------------------------------------------- memoria corto plazo
MAX_MENSAJES = _entero("MAX_MENSAJES", 10)
MAX_CARACTERES = _entero("MAX_CARACTERES", 8000)

# ------------------------------------------------- memoria medio plazo
DIAS_VIGENCIA = _entero("DIAS_VIGENCIA", 14)
DISTANCIA_MAX_SESIONES = _decimal("DISTANCIA_MAX_SESIONES", 0.6)
K_SESIONES = _entero("K_SESIONES", 3)

# ------------------------------------------------- memoria largo plazo
UMBRAL_DUPLICADO = _decimal("UMBRAL_DUPLICADO", 0.15)
K_HECHOS = _entero("K_HECHOS", 5)
CANDIDATOS_HECHOS = _entero("CANDIDATOS_HECHOS", 15)
PESO_SIMILITUD = _decimal("PESO_SIMILITUD", 0.60)
PESO_IMPORTANCIA = _decimal("PESO_IMPORTANCIA", 0.25)
PESO_RECENCIA = _decimal("PESO_RECENCIA", 0.15)
CORTE_PUNTUACION = _decimal("CORTE_PUNTUACION", 0.35)
VIDA_MEDIA_DIAS = _decimal("VIDA_MEDIA_DIAS", 30.0)
EXTRAER_CADA = _entero("EXTRAER_CADA", 6)

# ------------------------------------------------- documentos (RAG)
TAMANO_FRAGMENTO = _entero("TAMANO_FRAGMENTO", 1000)
SOLAPE_FRAGMENTO = _entero("SOLAPE_FRAGMENTO", 150)
K_FRAGMENTOS = _entero("K_FRAGMENTOS", 4)
# Por encima de esta distancia se considera que el corpus no tiene nada que
# decir sobre la pregunta, y el turno se responde como conversacion normal.
# El valor 0.65 no es una corazonada: se midio la distancia del mejor fragmento
# en preguntas de normativa (0.20 a 0.61) y en turnos de charla (0.71 a 0.84).
# Ver docs/decisiones.md.
DISTANCIA_MAX_DOCUMENTOS = _decimal("DISTANCIA_MAX_DOCUMENTOS", 0.65)
# Umbral mas holgado para cuando el turno menciona vocabulario de normativa
# ("SOAT", "multa", "licencia"...) o cuando el usuario pide normativa de forma
# explicita. Las frases cortas dan distancias altas aunque sean pertinentes.
DISTANCIA_CON_SENAL = _decimal("DISTANCIA_CON_SENAL", 0.90)

# --------------------------------------------------------------- multas
# El salario minimo es un parametro, nunca una cifra en el codigo: en 2026 el
# Decreto 1469 de 2025 lo fijo en 1.750.905, el Consejo de Estado suspendio
# provisionalmente sus efectos y el Decreto 0159 de 2026 lo fijo de forma
# transitoria. Toda multa calculada debe decir de donde sale su salario.
SMLMV = _decimal("SMLMV", 1_750_905.0)
FUENTE_SMLMV = os.environ.get(
    "FUENTE_SMLMV",
    "Decreto 1469 de 2025 (suspendido provisionalmente por el Consejo de Estado; "
    "verifique el valor vigente antes de citar la cifra)",
).strip()

# ------------------------------------------------------------ colecciones
COL_HECHOS = "hechos"
COL_SESIONES = "sesiones"
COL_DOCUMENTOS = "documentos"
