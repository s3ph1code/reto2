"""Memoria de documentos: ingesta del corpus para el RAG.

Extrae el texto de un PDF (o de un .md/.txt), lo divide en fragmentos con
solape y los guarda como embeddings en la coleccion `documentos`.

Cada fragmento conserva como metadatos el documento, la pagina y el numero de
articulo al que pertenece. Esos metadatos son los que permiten que el asistente
cite la fuente en lugar de afirmar cosas sin respaldo.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from . import config

# "ARTICULO 131", "ARTÍCULO 131o.", "Articulo 131."
PATRON_ARTICULO = re.compile(r"ART[IÍ]CULO\s+(\d+)", re.IGNORECASE)


def extraer_texto(ruta: Path) -> list[tuple[int, str]]:
    """Devuelve una lista de (numero_de_pagina, texto) del documento."""
    if not ruta.exists():
        raise FileNotFoundError(f"No existe el documento: {ruta}")
    if ruta.suffix.lower() == ".pdf":
        from pypdf import PdfReader

        lector = PdfReader(str(ruta))
        paginas = []
        for numero, pagina in enumerate(lector.pages, start=1):
            texto = pagina.extract_text() or ""
            paginas.append((numero, texto))
        return paginas
    return [(1, ruta.read_text(encoding="utf-8", errors="replace"))]


def limpiar(texto: str) -> str:
    """Normaliza espacios y saltos de linea sueltos del PDF."""
    texto = texto.replace("\r", "\n")
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def fragmentar(
    paginas: list[tuple[int, str]],
    tamano: int | None = None,
    solape: int | None = None,
) -> list[dict]:
    """Divide el documento en fragmentos, anotando pagina y articulo.

    El troceo sigue la estructura del documento, no una cuadricula de
    caracteres: primero se parte el texto en los encabezados de articulo, y solo
    los articulos mas largos que `tamano` se subdividen con solape.

    Trocear cada N caracteres sin mirar los encabezados mezclaba el final de un
    articulo con el principio del siguiente, y la etiqueta quedaba con el
    articulo equivocado: la busqueda acertaba el tema pero la cita apuntaba al
    articulo vecino.
    """
    largo = tamano or config.TAMANO_FRAGMENTO
    paso = largo - (solape if solape is not None else config.SOLAPE_FRAGMENTO)
    if paso <= 0:
        raise ValueError("El solape no puede ser mayor o igual que el tamano.")

    # Un solo texto continuo, guardando donde empieza cada pagina para poder
    # decir en que pagina cae cada fragmento.
    piezas, inicios = [], []
    posicion = 0
    for numero_pagina, texto in paginas:
        limpio = limpiar(texto)
        if not limpio:
            continue
        inicios.append((posicion, numero_pagina))
        piezas.append(limpio)
        posicion += len(limpio) + 1
    if not piezas:
        return []
    completo = "\n".join(piezas)

    def pagina_de(indice: int) -> int:
        actual = inicios[0][1]
        for comienzo, numero in inicios:
            if comienzo <= indice:
                actual = numero
            else:
                break
        return actual

    # Cada encabezado de articulo abre un segmento que llega hasta el siguiente.
    encabezados = list(PATRON_ARTICULO.finditer(completo))
    segmentos: list[tuple[str, int, str]] = []  # (texto, indice, articulo)
    if not encabezados:
        segmentos.append((completo, 0, ""))
    else:
        if encabezados[0].start() > 0:
            segmentos.append((completo[: encabezados[0].start()], 0, ""))
        for orden, encabezado in enumerate(encabezados):
            inicio = encabezado.start()
            fin = (
                encabezados[orden + 1].start()
                if orden + 1 < len(encabezados)
                else len(completo)
            )
            segmentos.append((completo[inicio:fin], inicio, encabezado.group(1)))

    fragmentos: list[dict] = []
    for texto_segmento, indice, articulo in segmentos:
        if len(texto_segmento) <= largo:
            fragmentos.append(
                {
                    "texto": texto_segmento.strip(),
                    "pagina": pagina_de(indice),
                    "articulo": articulo,
                }
            )
            continue
        desplazamiento = 0
        while desplazamiento < len(texto_segmento):
            trozo = texto_segmento[desplazamiento : desplazamiento + largo]
            fragmentos.append(
                {
                    "texto": trozo.strip(),
                    "pagina": pagina_de(indice + desplazamiento),
                    "articulo": articulo,
                }
            )
            desplazamiento += paso

    return [f for f in fragmentos if len(f["texto"]) > 50]


def indexar(coleccion, ruta: Path, etiqueta: str | None = None) -> int:
    """Ingesta un documento completo en la coleccion. Devuelve los fragmentos."""
    nombre = etiqueta or ruta.name
    paginas = extraer_texto(ruta)
    fragmentos = fragmentar(paginas)
    if not fragmentos:
        return 0

    ids, textos, metadatos = [], [], []
    for indice, fragmento in enumerate(fragmentos):
        firma = hashlib.sha1(
            f"{nombre}|{indice}|{fragmento['texto'][:80]}".encode("utf-8")
        ).hexdigest()[:16]
        ids.append(f"{firma}")
        textos.append(fragmento["texto"])
        metadatos.append(
            {
                "documento": nombre,
                "pagina": int(fragmento["pagina"]),
                "articulo": str(fragmento["articulo"]),
            }
        )

    # En lotes: ChromaDB no acepta inserciones ilimitadas de una sola vez.
    for comienzo in range(0, len(ids), 200):
        fin = comienzo + 200
        coleccion.upsert(
            ids=ids[comienzo:fin],
            documents=textos[comienzo:fin],
            metadatas=metadatos[comienzo:fin],
        )
    return len(ids)


def documentos_del_corpus() -> list[Path]:
    """Lista los documentos indexables que hay en la carpeta `corpus/`."""
    if not config.DIR_CORPUS.exists():
        return []
    validos = {".pdf", ".md", ".txt"}
    return sorted(
        p
        for p in config.DIR_CORPUS.iterdir()
        if p.is_file() and p.suffix.lower() in validos and p.name != "FUENTE.md"
    )
