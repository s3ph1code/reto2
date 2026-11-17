"""Pruebas de los mecanismos deterministas de las tres memorias.

No necesitan clave de API ni red: comprueban la logica, no al modelo.
"""

from __future__ import annotations

import math

from asistente import config
from asistente.memoria_corto import MemoriaCortoPlazo
from asistente.memoria_largo import MemoriaLargoPlazo


# --------------------------------------------------- memoria a corto plazo
def test_ventana_no_expulsa_antes_del_limite():
    memoria = MemoriaCortoPlazo(max_mensajes=4, max_caracteres=10_000)
    assert memoria.agregar("user", "hola") == []
    assert memoria.agregar("assistant", "buenas") == []
    assert len(memoria.obtener()) == 2


def test_ventana_expulsa_en_pares():
    memoria = MemoriaCortoPlazo(max_mensajes=4, max_caracteres=10_000)
    todos = []
    for i in range(6):
        todos.extend(memoria.agregar("user" if i % 2 == 0 else "assistant", f"m{i}"))
    # Al superar la ventana se van los dos mas antiguos, nunca uno solo.
    assert len(todos) == 2, "se expulsa de dos en dos para no romper la alternancia"
    assert [m["content"] for m in todos] == ["m0", "m1"]
    assert len(memoria.obtener()) == 4
    assert [m["content"] for m in memoria.obtener()] == ["m2", "m3", "m4", "m5"]


def test_ventana_expulsa_por_tamano_en_caracteres():
    memoria = MemoriaCortoPlazo(max_mensajes=100, max_caracteres=50)
    memoria.agregar("user", "x" * 40)
    memoria.agregar("assistant", "y" * 40)
    expulsados = memoria.agregar("user", "z" * 40)
    assert expulsados, "un par de mensajes largos debe forzar la expulsion"


def test_ventana_nunca_queda_vacia():
    memoria = MemoriaCortoPlazo(max_mensajes=1, max_caracteres=1)
    memoria.agregar("user", "a" * 100)
    memoria.agregar("assistant", "b" * 100)
    assert len(memoria.obtener()) == 2, "siempre queda al menos el ultimo intercambio"


def test_vaciar_devuelve_todo_y_limpia():
    memoria = MemoriaCortoPlazo()
    memoria.agregar("user", "hola")
    memoria.agregar("assistant", "buenas")
    restantes = memoria.vaciar()
    assert len(restantes) == 2
    assert memoria.obtener() == []


# --------------------------------------------------- memoria a largo plazo
class ColeccionFalsa:
    """Doble de prueba de una coleccion de ChromaDB, sin embeddings ni disco."""

    def __init__(self, registros=None):
        self.registros = registros or {}
        self.actualizados = []

    def count(self):
        return len(self.registros)

    def upsert(self, ids, documents, metadatas):
        for i, doc, meta in zip(ids, documents, metadatas):
            self.registros[i] = (doc, meta)

    def update(self, ids, metadatas):
        self.actualizados.append(list(ids))
        for i, meta in zip(ids, metadatas):
            doc, _ = self.registros[i]
            self.registros[i] = (doc, meta)

    def delete(self, ids):
        for i in ids:
            self.registros.pop(i, None)

    def get(self):
        return {
            "documents": [d for d, _ in self.registros.values()],
            "metadatas": [m for _, m in self.registros.values()],
        }

    def query(self, query_texts, n_results):
        # Devuelve los registros en el orden en que se guardaron, con la
        # distancia que el propio metadato declara para la prueba.
        ids = list(self.registros.keys())[:n_results]
        return {
            "ids": [ids],
            "documents": [[self.registros[i][0] for i in ids]],
            "metadatas": [[self.registros[i][1] for i in ids]],
            "distances": [[self.registros[i][1].get("_dist", 0.5) for i in ids]],
        }


def test_puntuacion_combina_los_tres_factores():
    largo = MemoriaLargoPlazo(ColeccionFalsa())
    esperado = (
        config.PESO_SIMILITUD * 1.0
        + config.PESO_IMPORTANCIA * 1.0
        + config.PESO_RECENCIA * 1.0
    )
    assert math.isclose(largo.puntuar(1.0, 10, 0.0), esperado, rel_tol=1e-9)


def test_la_recencia_decae_con_los_dias():
    largo = MemoriaLargoPlazo(ColeccionFalsa())
    hoy = largo.puntuar(0.8, 5, 0)
    hace_un_mes = largo.puntuar(0.8, 5, 30)
    hace_tres_meses = largo.puntuar(0.8, 5, 90)
    assert hoy > hace_un_mes > hace_tres_meses


def test_la_importancia_desempata_a_igual_similitud():
    largo = MemoriaLargoPlazo(ColeccionFalsa())
    assert largo.puntuar(0.7, 9, 1) > largo.puntuar(0.7, 2, 1)


def test_un_hecho_casi_identico_reutiliza_su_identificador():
    coleccion = ColeccionFalsa()
    largo = MemoriaLargoPlazo(coleccion, umbral_duplicado=0.15)
    primero = largo.guardar_hecho("El usuario vive en Cali", 7)
    coleccion.registros[primero][1]["_dist"] = 0.05  # casi identico
    segundo = largo.guardar_hecho("El usuario reside en Cali", 7)
    assert primero == segundo, "la deduplicacion debe actualizar, no duplicar"
    assert coleccion.count() == 1


def test_un_hecho_distinto_crea_registro_nuevo():
    coleccion = ColeccionFalsa()
    largo = MemoriaLargoPlazo(coleccion, umbral_duplicado=0.15)
    primero = largo.guardar_hecho("El usuario vive en Cali", 7)
    coleccion.registros[primero][1]["_dist"] = 0.80  # muy distinto
    largo.guardar_hecho("El usuario conduce una motocicleta", 6)
    assert coleccion.count() == 2


def test_recuperar_refresca_el_ultimo_acceso():
    coleccion = ColeccionFalsa()
    largo = MemoriaLargoPlazo(coleccion)
    largo.guardar_hecho("El usuario conduce una motocicleta", 9)
    for _, meta in coleccion.registros.values():
        meta["_dist"] = 0.1
    assert largo.recuperar("que vehiculo tiene") != []
    assert coleccion.actualizados, "los hechos recuperados deben reforzarse"


def test_olvidar_borra_solo_lo_muy_parecido():
    coleccion = ColeccionFalsa()
    largo = MemoriaLargoPlazo(coleccion)
    identificador = largo.guardar_hecho("El usuario vive en Cali", 5)
    coleccion.registros[identificador][1]["_dist"] = 0.9
    assert largo.olvidar("su ciudad") == 0, "0.9 esta lejos: no se debe borrar"
    coleccion.registros[identificador][1]["_dist"] = 0.1
    assert largo.olvidar("su ciudad") == 1
    assert coleccion.count() == 0
