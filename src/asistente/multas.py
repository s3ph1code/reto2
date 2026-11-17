"""Calculo de multas de transito. Determinista, sin LLM.

El Codigo Nacional de Transito no expresa las multas en pesos sino en multiplos
de salario minimo legal diario vigente (SMLDV). Convertirlas a pesos es
aritmetica con un parametro anual: justo lo que un modelo de lenguaje hace mal
y una herramienta hace bien. De ahi que esta sea una herramienta MCP aparte.

Los multiplos estan tomados del articulo 131 del PDF indexado en `corpus/`
(copia publicada por el RUNT), verificados contra el texto extraido.
"""

from __future__ import annotations

from . import config

ARTICULO_FUENTE = "131"

TIPOS: dict[str, dict] = {
    "A": {
        "smldv": 4,
        "descripcion": (
            "Infracciones de conductores de vehiculos no automotores o de "
            "traccion animal (por ejemplo, transitar por andenes o no respetar "
            "las senales de transito)"
        ),
    },
    "B": {
        "smldv": 8,
        "descripcion": (
            "Infracciones como no respetar las normas de cruce, estacionar en "
            "sitio prohibido o no portar los documentos exigidos"
        ),
    },
    "C": {
        "smldv": 15,
        "descripcion": (
            "Infracciones graves como no detenerse ante una luz roja, exceso de "
            "velocidad o conducir sin licencia vigente"
        ),
    },
    "D": {
        "smldv": 30,
        "descripcion": (
            "Infracciones muy graves como conducir en estado de embriaguez, sin "
            "seguro obligatorio o sin revision tecnico-mecanica"
        ),
    },
}


class ErrorMulta(ValueError):
    """La infraccion pedida no se pudo interpretar."""


def valor_smldv(salario_mensual: float | None = None) -> float:
    """Un SMLDV es el salario minimo mensual dividido en 30 dias."""
    salario = salario_mensual if salario_mensual is not None else config.SMLMV
    if salario <= 0:
        raise ErrorMulta("El salario minimo debe ser un numero positivo.")
    return salario / 30


def calcular(tipo_o_multiplo: str | int | float, salario_mensual: float | None = None) -> dict:
    """Calcula una multa a partir del tipo (A, B, C, D) o de un multiplo de SMLDV.

    Devuelve el calculo desglosado para que se pueda verificar a mano, e incluye
    siempre de que norma sale el salario usado: la cifra de 2026 esta en disputa
    judicial y una multa sin su fuente no es verificable.
    """
    entrada = str(tipo_o_multiplo).strip().upper()
    if entrada in TIPOS:
        tipo = entrada
        multiplo = float(TIPOS[entrada]["smldv"])
        descripcion = TIPOS[entrada]["descripcion"]
    else:
        try:
            multiplo = float(entrada.replace(",", "."))
        except ValueError as error:
            raise ErrorMulta(
                f"No reconozco '{tipo_o_multiplo}'. Use un tipo (A, B, C o D) "
                "o un numero de SMLDV."
            ) from error
        if multiplo <= 0:
            raise ErrorMulta("El multiplo de SMLDV debe ser positivo.")
        tipo = ""
        descripcion = f"Infraccion liquidada en {multiplo:g} SMLDV"

    salario = salario_mensual if salario_mensual is not None else config.SMLMV
    diario = valor_smldv(salario)
    total = diario * multiplo

    return {
        "tipo": tipo,
        "descripcion": descripcion,
        "multiplo_smldv": multiplo,
        "salario_mensual": salario,
        "fuente_salario": config.FUENTE_SMLMV,
        "valor_smldv": round(diario, 2),
        "total": round(total, 2),
        "articulo": ARTICULO_FUENTE,
    }


def formatear(calculo: dict) -> str:
    """Presenta el calculo en texto legible, con su desglose y su fuente."""
    lineas = [
        f"Multa: ${calculo['total']:,.0f} COP",
        "",
        f"Tipo: {calculo['tipo'] or 'personalizado'} - {calculo['descripcion']}",
        f"Multiplo: {calculo['multiplo_smldv']:g} SMLDV "
        f"(articulo {calculo['articulo']} del Codigo Nacional de Transito)",
        f"Salario minimo mensual usado: ${calculo['salario_mensual']:,.0f} COP",
        f"Un SMLDV = ${calculo['valor_smldv']:,.2f} COP (salario / 30)",
        f"Calculo: {calculo['multiplo_smldv']:g} x ${calculo['valor_smldv']:,.2f} "
        f"= ${calculo['total']:,.0f} COP",
        "",
        f"Fuente del salario: {calculo['fuente_salario']}",
    ]
    return "\n".join(lineas)


def tabla_tipos() -> str:
    """Resumen de los cuatro tipos de multa del articulo 131."""
    filas = [f"Articulo {ARTICULO_FUENTE} del Codigo Nacional de Transito:", ""]
    for letra, datos in TIPOS.items():
        filas.append(f"  {letra}: {datos['smldv']:>2} SMLDV - {datos['descripcion']}")
    return "\n".join(filas)
