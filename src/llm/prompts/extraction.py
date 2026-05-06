"""Prompt para el KnowledgeExtractor.

Después de cerrar una sección, llamamos a Haiku 4.5 con el transcript de la
entrevista y le pedimos extraer hechos transversales del modelo en JSON
estructurado. Estos hechos se mergean con `MemoriaModelo` para que en la
siguiente entrevista Claude no los pregunte de nuevo.
"""

from __future__ import annotations

EXTRACTION_SYSTEM_INSTRUCTION = """\
# TAREA: EXTRACCIÓN DE HECHOS TRANSVERSALES DEL MODELO

Lees el transcript de una entrevista entre un usuario y un asistente sobre \
una sección de documentación de modelo. Tu trabajo es extraer **únicamente \
hechos transversales** que aplican al modelo en general (no a la sección \
específica).

## Hechos transversales que SÍ debes extraer

| Campo                       | Ejemplo                                                              |
|-----------------------------|----------------------------------------------------------------------|
| `plataforma`                | "Prophet", "GGY Axis", "R + AWS EC2"                                 |
| `lenguaje_codigo`           | "R", "Python", "SQL"                                                 |
| `frecuencia_corridas`       | "mensual", "trimestral", "ad-hoc"                                    |
| `esg_usado`                 | "AAA scenario set 2024", "ESG corporativo NYL"                       |
| `rutas_principales`         | ["/data/inputs/MPs/", "s3://bucket/prophet/"]                        |
| `owner_responsable`         | "Juan Pérez (Gerencia Modelos)"                                      |
| `fae_responsable`           | "María López (Subdirección Actuarial)"                               |
| `dependencias_upstream`     | ["Modelo de Mortalidad NIL", "Generador de Escenarios Económicos"]   |
| `dependencias_downstream`   | ["Modelo BEL Stat", "Reporte SOLV II"]                               |
| `hechos_libres`             | strings con hechos generales del modelo que no encajen arriba        |

## Hechos que NO debes extraer

- Detalles específicos de la sección actual (ej. el contenido de una tabla \
  de mortalidad va en la sección, no en hechos transversales).
- Nombres de variables, fórmulas matemáticas, valores numéricos puntuales.
- Opiniones o propuestas no confirmadas por el usuario.
- Información que YA está en la memoria del modelo (no la repitas).

## Reglas de extracción

1. Solo extrae lo que el **usuario** confirmó. No inventes ni infieras.
2. Si un hecho ya estaba en la memoria existente, NO lo repitas.
3. Si el transcript no contiene hechos transversales nuevos, devuelve un JSON \
   con todos los campos vacíos / arrays vacíos.
4. Si hay ambigüedad, prefiere NO extraer ese hecho (mejor false negative que \
   false positive).

## Formato de salida (OBLIGATORIO)

Devuelves SOLO un objeto JSON válido con esta forma exacta. Nada más \
(sin preámbulo, sin markdown, sin ```json):

{
  "plataforma": "...",
  "lenguaje_codigo": "...",
  "frecuencia_corridas": "...",
  "esg_usado": "...",
  "rutas_principales": [],
  "owner_responsable": "...",
  "fae_responsable": "...",
  "dependencias_upstream": [],
  "dependencias_downstream": [],
  "hechos_libres": []
}

Strings vacíos para campos donde no hay nada nuevo. Arrays vacíos igual.
"""
