"""Pruebas del enrutador: que turnos se responden con el corpus y cuales no.

Los casos usan las distancias reales medidas contra el corpus indexado (ver
docs/decisiones.md), pero sin tocar la base vectorial: se le pasan los
fragmentos ya recuperados.
"""

from __future__ import annotations

from asistente import rag


def frags(distancia: float) -> list[dict]:
    return [{"distancia": distancia, "articulo": "76", "pagina": 42, "texto": "x"}]


# ------------------------------------------------- deteccion de vocabulario
def test_reconoce_vocabulario_de_normativa():
    assert rag.tiene_senal_normativa("Necesito el SOAT?")
    assert rag.tiene_senal_normativa("cuanto vale una multa")
    assert rag.tiene_senal_normativa("Donde puedo estacionar")


def test_reconoce_vocabulario_con_tildes():
    assert rag.tiene_senal_normativa("¿Cuál es el límite de velocidad?")
    assert rag.tiene_senal_normativa("revisión técnico-mecánica")


def test_no_ve_normativa_donde_no_hay():
    assert not rag.tiene_senal_normativa("Hola, como estas?")
    assert not rag.tiene_senal_normativa("Me gusta programar en Python")


# ------------------------------------------------------------ enrutamiento
def test_una_pregunta_de_normativa_clara_va_al_rag():
    # "Donde esta prohibido estacionar?" midio 0.256
    assert rag.decidir_ruta("Donde esta prohibido estacionar?", frags(0.256))


def test_una_pregunta_corta_con_vocabulario_legal_va_al_rag():
    # "Necesito el SOAT?" midio 0.806: fuera del umbral estricto, pero es legal
    assert rag.decidir_ruta("Necesito el SOAT?", frags(0.806))


def test_un_agradecimiento_corto_no_va_al_rag():
    # "Gracias!" midio 0.649: dentro del umbral, pero no es una pregunta legal
    assert not rag.decidir_ruta("Gracias!", frags(0.649))


def test_presentarse_no_va_al_rag():
    # El turno que hace visible la memoria a largo plazo. Midio 0.710.
    assert not rag.decidir_ruta(
        "Hola, me llamo Kevin y manejo una moto en Medellin.", frags(0.710)
    )


def test_charla_larga_sin_vocabulario_legal_no_va_al_rag():
    assert not rag.decidir_ruta("Me gusta el futbol y programar en Python", frags(0.837))


def test_sin_fragmentos_nunca_va_al_rag():
    assert not rag.decidir_ruta("Donde esta prohibido estacionar?", [])
    assert not rag.es_relevante([])


def test_una_consulta_explicita_es_mas_permisiva_que_el_enrutador():
    # Al llamar a consultar_normativa el usuario ya pidio normativa.
    assert rag.es_relevante(frags(0.806))
    assert not rag.decidir_ruta("Como estas?", frags(0.806))
