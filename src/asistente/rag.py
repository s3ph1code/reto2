"""RAG sobre el corpus: recuperacion y respuesta citada.

Esta es la unica ruta del asistente que tiene prohibido responder de memoria:
si el corpus no contiene la respuesta, lo dice. Las conversaciones normales no
pasan por aqui (lo decide `gestor.py` por umbral de distancia).
"""

from __future__ import annotations

import re

from . import config
from .llm import llamar_llm

PROMPT_RAG = (
    "Usted responde preguntas sobre normas de transito colombianas usando "
    "UNICAMENTE los fragmentos de texto legal que se le entregan. Reglas:\n"
    "1. No use conocimiento propio. Si los fragmentos no contienen la "
    "respuesta, diga exactamente que el corpus indexado no la contiene.\n"
    "2. Cite siempre el articulo y la pagina de donde sale cada afirmacion, "
    "con el formato (articulo N, pagina P).\n"
    "3. No calcule multas en pesos: el texto legal las expresa en salarios "
    "minimos diarios. Indique el multiplo y recuerde que existe una "
    "herramienta de calculo aparte.\n"
    "4. Responda en espanol, de forma concisa.\n"
    "5. Esto es un ejercicio academico, no asesoria legal."
)

AVISO_SIN_CONTEXTO = (
    "El corpus indexado no contiene informacion para responder esa pregunta."
)


def recuperar(coleccion, pregunta: str, k: int | None = None) -> list[dict]:
    """Devuelve los fragmentos mas parecidos a la pregunta, con sus metadatos."""
    total = coleccion.count()
    if total == 0:
        return []
    tope = k or config.K_FRAGMENTOS
    resultado = coleccion.query(query_texts=[pregunta], n_results=min(tope, total))
    docs = (resultado.get("documents") or [[]])[0]
    metas = (resultado.get("metadatas") or [[]])[0]
    dists = (resultado.get("distances") or [[]])[0]
    ids = (resultado.get("ids") or [[]])[0]
    fragmentos = []
    for id_, doc, meta, dist in zip(ids, docs, metas, dists):
        meta = meta or {}
        fragmentos.append(
            {
                "id": id_,
                "texto": doc,
                "articulo": meta.get("articulo", ""),
                "pagina": meta.get("pagina", 0),
                "documento": meta.get("documento", ""),
                "distancia": round(float(dist), 4),
            }
        )
    return fragmentos


# Vocabulario que delata una pregunta de normativa aunque venga muy corta.
PALABRAS_NORMATIVA = {
    "articulo",
    "alcoholemia",
    "ley",
    "codigo",
    "norma",
    "multa",
    "multas",
    "comparendo",
    "sancion",
    "infraccion",
    "smldv",
    "licencia",
    "soat",
    "seguro",
    "tecnomecanica",
    "tecnico-mecanica",
    "revision",
    "matricula",
    "placa",
    "transito",
    "velocidad",
    "estacionar",
    "parquear",
    "embriaguez",
    "casco",
    "cinturon",
    "peaton",
    "carril",
    "semaforo",
    "senal",
    "grua",
    "inmovilizacion",
}

LARGO_MINIMO = 15


def _normalizar(texto: str) -> str:
    tildes = str.maketrans("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN")
    return texto.translate(tildes).lower()


def tiene_senal_normativa(texto: str) -> bool:
    """Indica si el texto menciona vocabulario propio de la normativa."""
    palabras = set(re.findall(r"[a-z\-]+", _normalizar(texto)))
    return bool(palabras & PALABRAS_NORMATIVA)


def es_relevante(fragmentos: list[dict]) -> bool:
    """Indica si hay algun fragmento utilizable para una consulta explicita.

    Se aplica cuando el usuario ya pidio normativa (por ejemplo al llamar a la
    herramienta `consultar_normativa`), asi que el criterio es amplio.
    """
    if not fragmentos:
        return False
    return fragmentos[0]["distancia"] <= config.DISTANCIA_CON_SENAL


def decidir_ruta(texto: str, fragmentos: list[dict]) -> bool:
    """Decide si un turno de conversacion debe responderse con el corpus.

    La distancia por si sola no basta: las frases muy cortas producen
    embeddings inestables y caen en cualquier lado. "Gracias!" quedaba a 0.649
    (dentro del umbral, pero no es una pregunta legal) y "Necesito el SOAT?" a
    0.806 (fuera del umbral, pero si lo es). De ahi las tres senales:

    1. un turno muy corto sin vocabulario legal es charla, sin mirar distancias;
    2. si menciona vocabulario legal, se acepta una distancia mas holgada;
    3. si no, se exige el umbral estricto medido en docs/decisiones.md.
    """
    if not fragmentos:
        return False
    distancia = fragmentos[0]["distancia"]
    senal = tiene_senal_normativa(texto)
    if len(texto.strip()) < LARGO_MINIMO and not senal:
        return False
    if senal:
        return distancia <= config.DISTANCIA_CON_SENAL
    return distancia <= config.DISTANCIA_MAX_DOCUMENTOS


def formatear_contexto(fragmentos: list[dict]) -> str:
    bloques = []
    for fragmento in fragmentos:
        cabecera = (
            f"[articulo {fragmento['articulo'] or 'sin numero'}, "
            f"pagina {fragmento['pagina']}]"
        )
        bloques.append(f"{cabecera}\n{fragmento['texto']}")
    return "\n\n---\n\n".join(bloques)


def citas(fragmentos: list[dict]) -> list[str]:
    """Lista legible de las fuentes usadas, sin repetir articulos."""
    vistas, salida = set(), []
    for fragmento in fragmentos:
        clave = (fragmento["articulo"], fragmento["pagina"])
        if clave in vistas:
            continue
        vistas.add(clave)
        salida.append(
            f"articulo {fragmento['articulo'] or '?'}, pagina {fragmento['pagina']} "
            f"({fragmento['documento']})"
        )
    return salida


def responder(
    coleccion, pregunta: str, k: int | None = None, fragmentos: list[dict] | None = None
) -> dict:
    """Responde una pregunta de normativa citando el corpus.

    Acepta fragmentos ya recuperados para no consultar la base dos veces cuando
    el gestor ya decidio la ruta con ellos.
    """
    if fragmentos is None:
        fragmentos = recuperar(coleccion, pregunta, k)
    if not es_relevante(fragmentos):
        return {
            "respuesta": AVISO_SIN_CONTEXTO,
            "fragmentos": fragmentos,
            "fuentes": [],
            "con_contexto": False,
        }
    contenido = (
        f"Fragmentos del corpus:\n\n{formatear_contexto(fragmentos)}\n\n"
        f"Pregunta: {pregunta}"
    )
    respuesta = llamar_llm(PROMPT_RAG, [{"role": "user", "content": contenido}])
    return {
        "respuesta": respuesta,
        "fragmentos": fragmentos,
        "fuentes": citas(fragmentos),
        "con_contexto": True,
    }
