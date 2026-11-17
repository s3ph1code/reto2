"""Pruebas del troceado de documentos y del calculo de multas.

El calculo de multas es la parte del asistente que debe ser exacta siempre: de
ahi que se pruebe contra los multiplos del articulo 131 del corpus.
"""

from __future__ import annotations

import pytest

from asistente import multas
from asistente.documentos import PATRON_ARTICULO, fragmentar, limpiar


# --------------------------------------------------------------- documentos
def test_limpiar_normaliza_espacios_y_saltos():
    assert limpiar("hola   mundo") == "hola mundo"
    assert limpiar("a\n\n\n\n\nb") == "a\n\nb"
    assert limpiar("  texto  ") == "texto"


def test_el_patron_reconoce_las_formas_del_pdf():
    assert PATRON_ARTICULO.findall("ARTICULO 131. MULTAS") == ["131"]
    assert PATRON_ARTICULO.findall("ARTÍCULO   131. MULTAS") == ["131"]
    assert PATRON_ARTICULO.findall("Articulo 42. SEGUROS") == ["42"]


def test_fragmentar_trocea_con_solape():
    texto = "A" * 2500
    fragmentos = fragmentar([(1, texto)], tamano=1000, solape=200)
    assert len(fragmentos) >= 3
    assert all(len(f["texto"]) <= 1000 for f in fragmentos)
    assert all(f["pagina"] == 1 for f in fragmentos)


def test_el_numero_de_articulo_se_arrastra_entre_fragmentos():
    texto = "ARTICULO 30. EQUIPOS. " + ("contenido del articulo treinta. " * 80)
    fragmentos = fragmentar([(7, texto)], tamano=500, solape=50)
    assert len(fragmentos) > 1
    assert all(f["articulo"] == "30" for f in fragmentos), (
        "un fragmento sin encabezado sigue perteneciendo al ultimo articulo visto"
    )
    assert fragmentos[0]["pagina"] == 7


def test_se_descartan_los_fragmentos_minusculos():
    fragmentos = fragmentar([(1, "corto")], tamano=1000, solape=100)
    assert fragmentos == []


def test_el_solape_no_puede_igualar_al_tamano():
    with pytest.raises(ValueError):
        fragmentar([(1, "x" * 100)], tamano=100, solape=100)


# ------------------------------------------------------------------ multas
def test_los_cuatro_tipos_del_articulo_131():
    # Multiplos verificados en el texto del PDF indexado.
    assert multas.TIPOS["A"]["smldv"] == 4
    assert multas.TIPOS["B"]["smldv"] == 8
    assert multas.TIPOS["C"]["smldv"] == 15
    assert multas.TIPOS["D"]["smldv"] == 30


def test_un_smldv_es_el_salario_entre_treinta():
    assert multas.valor_smldv(1_500_000) == 50_000


def test_calculo_de_una_multa_tipo_c():
    calculo = multas.calcular("C", salario_mensual=1_500_000)
    assert calculo["multiplo_smldv"] == 15
    assert calculo["valor_smldv"] == 50_000
    assert calculo["total"] == 750_000
    assert calculo["articulo"] == "131"


def test_acepta_un_multiplo_directo_de_smldv():
    calculo = multas.calcular(45, salario_mensual=1_500_000)
    assert calculo["total"] == 45 * 50_000
    assert calculo["tipo"] == ""


def test_el_tipo_no_distingue_mayusculas():
    assert multas.calcular("d", 1_500_000)["total"] == multas.calcular("D", 1_500_000)["total"]


def test_una_infraccion_desconocida_falla_con_mensaje_claro():
    with pytest.raises(multas.ErrorMulta):
        multas.calcular("Z")
    with pytest.raises(multas.ErrorMulta):
        multas.calcular(-5)


def test_el_salario_debe_ser_positivo():
    with pytest.raises(multas.ErrorMulta):
        multas.valor_smldv(0)


def test_el_texto_de_la_multa_declara_su_fuente():
    texto = multas.formatear(multas.calcular("B", 1_500_000))
    assert "articulo 131" in texto
    assert "Fuente del salario" in texto, (
        "una multa sin la norma de su salario no es verificable"
    )
