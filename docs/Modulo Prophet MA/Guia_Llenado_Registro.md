# Guía de Llenado — Registro de Modelos Prophet

## Propósito

Este archivo Excel es el insumo para DocuMente al generar la Ficha Técnica de un modelo Prophet. Sube el Excel en la pantalla "Iniciar Ficha Prophet" y el sistema detectará automáticamente los modelos disponibles.

---

## Hojas requeridas

El archivo debe tener exactamente estas 4 hojas (los nombres deben coincidir):

| Hoja | Obligatoria | Descripción |
|---|---|---|
| `Descripcion_General` | Sí | Una fila por modelo: datos básicos, frecuencia, reportes, problema que ataca |
| `Detalle Runs` | Sí | Una fila por corrida: número, descripción, tiempo, outputs, precedente, responsable |
| `Variables criticas` | Sí | Una fila por variable: nombre, fórmula, corrida, frecuencia, responsable |
| `Conocimiento_Tecnico` | Sí | Matriz personas × capacidades × nivel |

> Si falta una hoja, las secciones correspondientes quedarán vacías en la ficha — el import no fallará.

---

## Hoja: Descripcion_General

Columnas obligatorias:

| Columna | Descripción | Ejemplo |
|---|---|---|
| Area | Área del modelo | Rentabilidad |
| Proceso | Nombre del modelo (identificador) | VNB |
| Encargado | Dueño principal del modelo | Francisco Carmona |
| Descripcion | Descripción breve del modelo | Modelo de valor nuevo de negocio |
| Frecuencia de actualización | Con qué periodicidad se corre | Trimestral |

Columnas opcionales: `Corridas`, `Contabilidad`, `Periodo de actualización`, `Reporta`, `Insumo`, `Área encargada`, `Tiempo de ejecución`, `Qué problema ataca`.

---

## Hoja: Detalle Runs

Columnas obligatorias:

| Columna | Descripción | Ejemplo |
|---|---|---|
| # corrida | Número de la corrida | 33 |
| Detalle | Descripción breve de la corrida | IL UDI y USD |
| Es ALM? | Si la corrida es tipo ALM | No / Sí |
| Tiempo de ejecución | Tiempo aproximado de ejecución | 45 min |
| Responsable | Quién ejecuta esta corrida | Francisco Carmona |

Columnas opcionales: `Corrida Precedente`, `Outputs Principales`, `Variables críticas`, `Inputs`, `Área a quien se pide`, `Frecuencia de actualización`, `Qué se actualiza en el modelo`.

---

## Hoja: Variables criticas

Columnas obligatorias:

| Columna | Descripción | Ejemplo |
|---|---|---|
| Corrida | Número de corrida a la que pertenece | 33 |
| Nombre | Nombre de la variable en Prophet | PROF_SOLVM |
| Descripción | Qué representa la variable | Solvency margin profit |
| Fórmula | Fórmula o lógica de cálculo | PREM_INC - DEATH_OUTGO |
| Responsable de la info | Quién provee o mantiene la variable | Francisco Carmona |

Columnas opcionales: `Variables precedentes`, `Same_as`, `Frecuencia de actualización`, `Documentación`, `Variables dependientes`.

---

## Hoja: Conocimiento_Tecnico

Estructura de matriz:
- **Columna A:** nombre de la persona
- **Columnas B en adelante:** una columna por capacidad Prophet

Niveles válidos:
- `NO CONOCE`
- `BÁSICO`
- `INTERMEDIO`
- `AVANZADO`

> Usa exactamente estos valores. El sistema los mapea a la Matriz de Conocimiento Técnico de la ficha.

---

## Tolerancia a variaciones

DocuMente usa IA para mapear las columnas de tu Excel al schema esperado. Esto significa que:

- Los nombres de columnas pueden tener pequeñas variaciones (ej. "Encargado" ≈ "Responsable")
- Las hojas pueden tener columnas adicionales — se ignorarán
- El orden de columnas no importa

Sin embargo, **los nombres de las hojas deben ser exactos** para que el sistema las encuentre automáticamente.

---

## ¿Qué pasa si falta información?

| Situación | Comportamiento |
|---|---|
| Hoja faltante | Sección correspondiente queda vacía, el resto se importa |
| Columna faltante | Campo queda vacío, se puede completar manualmente en la app |
| Fila incompleta | Se importa con los campos disponibles |

Después del import, puedes editar cada sección directamente en DocuMente.

---

## Flujo recomendado

1. Descarga este template y complétalo con los datos de tu modelo.
2. En DocuMente, ve a **"Iniciar Ficha Prophet"**.
3. Sube el Excel — el sistema detectará los modelos disponibles.
4. Selecciona el modelo a documentar y haz click en **"Importar ficha"**.
5. Revisa las secciones importadas y completa las que quedaron vacías.
6. Exporta la Ficha Prophet a `.docx` desde el dashboard.
