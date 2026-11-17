"""Evaluacion de la recuperacion del RAG.

Mide lo unico que se puede medir sin opinar: si el buscador trae el fragmento
correcto. Para cada pregunta del conjunto de evaluacion se conoce el articulo
del Codigo que la responde, y se comprueba si aparece entre los k fragmentos
recuperados.

Metricas, todas calculadas en local y sin gastar una sola llamada al LLM:

- `acierto@k`  : el articulo esperado aparece entre los k recuperados (0 o 1).
- `precision@k`: que proporcion de los k fragmentos pertenece al articulo correcto.
- `MRR`        : 1 dividido por la posicion del primer fragmento correcto.
- `distancia`  : distancia coseno del mejor fragmento, para ver cuan cerca quedo.

Nota importante para interpretar los numeros: se evalua la ruta de RAG desnuda,
sin memoria del usuario inyectada en el prompt. Si se mezclara la memoria, las
metricas dejarian de medir la calidad de la recuperacion.
"""

from __future__ import annotations

import csv
import json
import statistics
import time

from . import config, rag
from .almacen import crear_cliente, obtener_coleccion


def cargar_preguntas() -> dict:
    ruta = config.DIR_EVALUACION / "preguntas.json"
    if not ruta.exists():
        raise FileNotFoundError(f"No existe el conjunto de evaluacion: {ruta}")
    return json.loads(ruta.read_text(encoding="utf-8"))


def evaluar_una(coleccion, pregunta: str, esperado: str, k: int) -> dict:
    fragmentos = rag.recuperar(coleccion, pregunta, k)
    articulos = [str(f["articulo"]) for f in fragmentos]
    aciertos = [a == str(esperado) for a in articulos]
    posicion = aciertos.index(True) + 1 if any(aciertos) else 0
    return {
        "pregunta": pregunta,
        "articulo_esperado": esperado,
        "articulos_recuperados": ", ".join(articulos) or "-",
        "acierto": int(any(aciertos)),
        "precision": round(sum(aciertos) / len(aciertos), 3) if aciertos else 0.0,
        "mrr": round(1 / posicion, 3) if posicion else 0.0,
        "distancia_mejor": fragmentos[0]["distancia"] if fragmentos else None,
        "pagina_mejor": fragmentos[0]["pagina"] if fragmentos else None,
    }


def ejecutar(k: int | None = None) -> int:
    tope = k or config.K_FRAGMENTOS
    datos = cargar_preguntas()
    coleccion = obtener_coleccion(crear_cliente(), config.COL_DOCUMENTOS)
    total_fragmentos = coleccion.count()
    if total_fragmentos == 0:
        print("La coleccion de documentos esta vacia. Ejecute: uv run asistente indexar")
        return 1

    print(f"Corpus: {total_fragmentos} fragmentos | k = {tope}\n")
    filas = []
    for item in datos["preguntas"]:
        fila = evaluar_una(coleccion, item["pregunta"], item["articulo_esperado"], tope)
        filas.append(fila)
        marca = "OK " if fila["acierto"] else "   "
        print(
            f"{marca} art. {fila['articulo_esperado']:>3} esperado | "
            f"recuperados: {fila['articulos_recuperados']:<22} | "
            f"dist {fila['distancia_mejor']} | {fila['pregunta'][:48]}"
        )

    resumen = {
        "preguntas": len(filas),
        "k": tope,
        "acierto@k": round(statistics.fmean(f["acierto"] for f in filas), 3),
        "precision@k": round(statistics.fmean(f["precision"] for f in filas), 3),
        "mrr": round(statistics.fmean(f["mrr"] for f in filas), 3),
        "distancia_media": round(
            statistics.fmean(
                f["distancia_mejor"] for f in filas if f["distancia_mejor"] is not None
            ),
            4,
        ),
        "fragmentos_corpus": total_fragmentos,
        "corpus": datos.get("corpus", ""),
        "momento": time.strftime("%Y-%m-%d %H:%M"),
    }

    print("\nResumen")
    print(f"  acierto@{tope}   : {resumen['acierto@k']}")
    print(f"  precision@{tope} : {resumen['precision@k']}")
    print(f"  MRR            : {resumen['mrr']}")
    print(f"  distancia media: {resumen['distancia_media']}")

    destino = config.DIR_EVALUACION / "resultados"
    destino.mkdir(parents=True, exist_ok=True)

    archivo_csv = destino / "recuperacion.csv"
    with open(archivo_csv, "w", encoding="utf-8", newline="") as salida:
        escritor = csv.DictWriter(salida, fieldnames=list(filas[0].keys()))
        escritor.writeheader()
        escritor.writerows(filas)

    archivo_md = destino / "recuperacion.md"
    lineas = [
        "# Resultados de la evaluacion de recuperacion",
        "",
        f"- Fecha: {resumen['momento']}",
        f"- Corpus: `{resumen['corpus']}` ({total_fragmentos} fragmentos)",
        f"- Fragmentos recuperados por pregunta (k): {tope}",
        f"- Preguntas: {resumen['preguntas']}",
        "",
        "## Medias",
        "",
        "| Metrica | Valor | Que significa |",
        "|---|---|---|",
        f"| acierto@{tope} | {resumen['acierto@k']} | proporcion de preguntas en las que el articulo correcto aparece entre los k fragmentos |",
        f"| precision@{tope} | {resumen['precision@k']} | que parte de los fragmentos recuperados pertenece al articulo correcto |",
        f"| MRR | {resumen['mrr']} | 1/posicion del primer fragmento correcto; 1.0 es acertar siempre de primero |",
        f"| distancia media | {resumen['distancia_media']} | distancia coseno del mejor fragmento (0 = identico) |",
        "",
        "## Detalle por pregunta",
        "",
        "| Pregunta | Art. esperado | Art. recuperados | Acierto | Precision | MRR | Dist. |",
        "|---|---|---|---|---|---|---|",
    ]
    for fila in filas:
        lineas.append(
            f"| {fila['pregunta']} | {fila['articulo_esperado']} | "
            f"{fila['articulos_recuperados']} | {fila['acierto']} | "
            f"{fila['precision']} | {fila['mrr']} | {fila['distancia_mejor']} |"
        )
    lineas += [
        "",
        "## Como leer esto",
        "",
        "Se evalua la ruta de RAG desnuda, sin memoria del usuario en el prompt:",
        "lo que se mide es la calidad de la recuperacion, no la del modelo. Las",
        "metricas no necesitan clave de API ni llamadas al LLM, asi que son",
        "reproducibles por cualquiera que clone el repositorio e indexe el corpus.",
        "",
        "El articulo esperado de cada pregunta se tomo leyendo el PDF indexado, no",
        "la ley consolidada vigente. Una respuesta de RAG vale lo que valga la",
        "fecha de su corpus.",
    ]
    archivo_md.write_text("\n".join(lineas) + "\n", encoding="utf-8")

    print(f"\nGuardado en:\n  {archivo_csv}\n  {archivo_md}")
    return 0
