from __future__ import annotations

import json
from typing import Any

EXTRAER_SECCION_PROPHET_SYSTEM = """\
# TAREA: EXTRACCIÓN DE DATOS PROPHET A SCHEMA ESTRUCTURADO

Recibes datos crudos de una hoja Excel de modelos actuariales Prophet.
Tu trabajo es identificar la información del modelo solicitado y mapearla
al schema de campos especificado.

## REGLAS

- NO INVENTES datos. Si un campo no está en los datos crudos, usa cadena vacía "".
- Sé tolerante a variaciones de nombre de columna ("Encargado" ≈ "Responsable").
- Si los datos tienen múltiples modelos, filtra solo el modelo solicitado.
- Devuelve SOLO el JSON. Sin texto, sin markdown de código.
- Si no encuentras datos: {"filas": [], "advertencias": ["No se encontraron datos para el modelo"]}

## FORMATO DE SALIDA

Para secciones tipo tabla:
{"filas": [{"campo1": "valor", ...}], "advertencias": []}

Para secciones tipo campos o texto:
{"contenido": "texto o JSON de campos", "advertencias": []}
"""


def construir_prompt_extraccion(
    nombre_modelo: str,
    nombre_seccion: str,
    schema_campos: list[str],
    datos_crudos: list[dict[str, Any]],
    tipo_contenido: str,
) -> str:
    datos_str = json.dumps(datos_crudos[:50], ensure_ascii=False, indent=2)
    return f"""\
## MODELO A EXTRAER
Nombre: {nombre_modelo}

## SECCIÓN A POBLAR
{nombre_seccion} (tipo: {tipo_contenido})
Schema esperado: {json.dumps(schema_campos)}

## DATOS CRUDOS DEL EXCEL
{datos_str}

Extrae los datos del modelo "{nombre_modelo}" según el schema. SOLO el JSON.
"""
