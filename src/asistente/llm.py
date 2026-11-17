"""Conexion con el modelo de lenguaje.

Toda llamada al LLM pasa por aqui, para poder cambiar de proveedor sin tocar el
resto del codigo. Se habla con la API por HTTP con la libreria estandar: asi el
proyecto no depende de la version de ningun SDK.

Proveedores soportados:

- `gemini`: Google AI Studio. Clave gratuita en https://aistudio.google.com/apikey
- `groq`:   Groq Cloud. Clave gratuita en https://console.groq.com
- sin clave: modo simulado, que devuelve una respuesta falsa pero permite
  probar la memoria a corto plazo y el almacen sin gastar API.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from . import config

TIEMPO_ESPERA = 60


class ErrorLLM(RuntimeError):
    """Fallo al hablar con el proveedor del modelo."""


def hay_clave() -> bool:
    """Indica si hay credenciales para llamar a un modelo real."""
    return bool(_clave())


def proveedor() -> str:
    return config.PROVEEDOR_LLM


def _clave() -> str:
    if config.PROVEEDOR_LLM == "groq":
        return config.CLAVE_GROQ
    return config.CLAVE_GEMINI


def _peticion(url: str, cuerpo: dict | None, cabeceras: dict[str, str]) -> dict:
    datos = json.dumps(cuerpo).encode("utf-8") if cuerpo is not None else None
    peticion = urllib.request.Request(url, data=datos, headers=cabeceras)
    try:
        with urllib.request.urlopen(peticion, timeout=TIEMPO_ESPERA) as respuesta:
            return json.loads(respuesta.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detalle = error.read().decode("utf-8", "replace")[:400]
        raise ErrorLLM(f"HTTP {error.code} del proveedor: {detalle}") from error
    except urllib.error.URLError as error:
        raise ErrorLLM(f"No se pudo contactar al proveedor: {error.reason}") from error


def _texto_plano(contenido: Any) -> str:
    """Normaliza el contenido de un mensaje a texto."""
    if isinstance(contenido, str):
        return contenido
    if isinstance(contenido, list):
        piezas = []
        for item in contenido:
            if isinstance(item, dict):
                piezas.append(str(item.get("text", item)))
            else:
                piezas.append(str(item))
        return " ".join(piezas)
    return str(contenido)


def _llamar_gemini(sistema: str, mensajes: list[dict], max_tokens: int) -> str:
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{config.MODELO_LLM}:generateContent"
    )
    contenidos = [
        {
            "role": "model" if m.get("role") == "assistant" else "user",
            "parts": [{"text": _texto_plano(m.get("content", ""))}],
        }
        for m in mensajes
    ]
    cuerpo = {
        "contents": contenidos,
        "generationConfig": {"maxOutputTokens": max_tokens},
    }
    if sistema:
        cuerpo["system_instruction"] = {"parts": [{"text": sistema}]}

    respuesta = _peticion(
        url,
        cuerpo,
        {
            "Content-Type": "application/json",
            "x-goog-api-key": config.CLAVE_GEMINI,
        },
    )
    candidatos = respuesta.get("candidates") or []
    if not candidatos:
        raise ErrorLLM(f"El modelo no devolvio candidatos: {str(respuesta)[:300]}")
    partes = candidatos[0].get("content", {}).get("parts") or []
    return "".join(p.get("text", "") for p in partes).strip()


def _llamar_groq(sistema: str, mensajes: list[dict], max_tokens: int) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    lista = []
    if sistema:
        lista.append({"role": "system", "content": sistema})
    for m in mensajes:
        lista.append(
            {"role": m.get("role", "user"), "content": _texto_plano(m.get("content", ""))}
        )
    respuesta = _peticion(
        url,
        {"model": config.MODELO_LLM, "messages": lista, "max_tokens": max_tokens},
        {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.CLAVE_GROQ}",
        },
    )
    opciones = respuesta.get("choices") or []
    if not opciones:
        raise ErrorLLM(f"El modelo no devolvio respuesta: {str(respuesta)[:300]}")
    return (opciones[0].get("message", {}).get("content") or "").strip()


def llamar_llm(sistema: str, mensajes: list[dict], max_tokens: int | None = None) -> str:
    """Envia un prompt de sistema y una lista de mensajes, y devuelve el texto.

    `mensajes` tiene la forma [{"role": "user" | "assistant", "content": "..."}].
    """
    if not mensajes:
        raise ValueError("La lista de mensajes no puede estar vacia.")
    tope = max_tokens or config.MAX_TOKENS

    if not hay_clave():
        ultimo = _texto_plano(mensajes[-1].get("content", ""))
        return "[respuesta simulada, sin clave de API] " + ultimo[:200]

    if config.PROVEEDOR_LLM == "groq":
        return _llamar_groq(sistema, mensajes, tope)
    return _llamar_gemini(sistema, mensajes, tope)


def modelos_disponibles() -> list[str]:
    """Lista los modelos que la clave configurada puede usar."""
    if not hay_clave():
        return []
    if config.PROVEEDOR_LLM == "groq":
        respuesta = _peticion(
            "https://api.groq.com/openai/v1/models",
            None,
            {"Authorization": f"Bearer {config.CLAVE_GROQ}"},
        )
        return sorted(m.get("id", "") for m in respuesta.get("data", []))
    respuesta = _peticion(
        "https://generativelanguage.googleapis.com/v1beta/models",
        None,
        {"x-goog-api-key": config.CLAVE_GEMINI},
    )
    nombres = []
    for modelo in respuesta.get("models", []):
        if "generateContent" in (modelo.get("supportedGenerationMethods") or []):
            nombres.append(modelo.get("name", "").replace("models/", ""))
    return sorted(nombres)
