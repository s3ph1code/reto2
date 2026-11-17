# Procedencia del corpus

| Dato | Valor |
|---|---|
| Documento | Ley 769 de 2002 — Codigo Nacional de Transito Terrestre |
| Archivo | `ley-769-2002-cnt.pdf` |
| Origen | RUNT (Registro Unico Nacional de Transito), entidad del Estado colombiano |
| URL | https://www.runt.gov.co/sites/default/files/normas/Ley%20769%20de%202002%20%28C%C3%B3digo%20Nacional%20de%20Tr%C3%A1nsito%29.pdf |
| Fecha de descarga | 2026-11-17 |
| Paginas | 84 |
| Caracteres extraidos | ~183.600 |
| Articulos detectados | 181 menciones, 172 numeros distintos |

## Vigencia: lea esto antes de citar una cifra

El texto de esta copia es el de la Ley 769 de 2002 **con las notas de
modificacion que trae el propio documento** (por ejemplo, el articulo 131 indica
"Modificado por el art. 21, Ley 1383 de 2010"). La ley ha sido reformada varias
veces despues, entre otras por la **Ley 2251 de 2022** y la **Ley 2283 de
2022**, que **no estan indexadas** en este proyecto.

Por eso el asistente responde siempre "segun el texto indexado, articulo N" y
nunca "segun la ley vigente". Es una limitacion conocida y deliberada: deja a la
vista que **una respuesta de RAG vale lo que valga la fecha de su corpus**.

## El salario minimo no sale del corpus

Las multas del articulo 131 se expresan en multiplos de salario minimo legal
diario vigente (SMLDV), no en pesos. El valor del salario es un parametro de
`.env` (`SMLMV`), no una cifra del texto, y toda multa calculada imprime de que
norma sale.

Para 2026 la cifra esta en disputa judicial: el Decreto 1469 de 2025 la fijo en
$1.750.905, el Consejo de Estado suspendio provisionalmente sus efectos y el
Decreto 0159 de 2026 la fijo de forma transitoria. Verifique el valor vigente
antes de usar una multa calculada para algo que no sea este ejercicio.

## Cambiar el corpus

El corpus es intercambiable. Ponga cualquier `.pdf`, `.md` o `.txt` en esta
carpeta y ejecute:

```bash
uv run asistente indexar
```

Si cambia el corpus, actualice tambien `evaluacion/preguntas.json`: los
articulos esperados de la evaluacion pertenecen a este documento.
