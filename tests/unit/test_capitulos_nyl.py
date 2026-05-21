"""Tests para los helpers de agrupación por capítulo NYL.

Cubre `CAPITULOS_NYL` y `agrupar_secciones_por_capitulo()` en
`src/core/template_catalog.py`. Estos helpers son la base del Quick Win #4
del audit UX (dashboard agrupado por capítulo).
"""

from __future__ import annotations

from src.core.template_catalog import (
    CAPITULOS_NYL,
    TEMPLATE_MODEL_DEVELOPMENT,
    agrupar_secciones_por_capitulo,
    construir_secciones_vacias,
)


class TestCapitulosNyl:
    """La constante `CAPITULOS_NYL` define los 9 capítulos del template."""

    def test_tiene_9_capitulos(self) -> None:
        assert len(CAPITULOS_NYL) == 9

    def test_capitulos_son_strings_numericos(self) -> None:
        # Los keys son "1".."9" como strings (consistente con seccion.numero.split('.')[0])
        for k in CAPITULOS_NYL:
            assert k.isdigit()

    def test_capitulos_cubren_1_a_9(self) -> None:
        assert sorted(CAPITULOS_NYL.keys(), key=int) == [str(i) for i in range(1, 10)]

    def test_nombres_no_vacios(self) -> None:
        for nombre in CAPITULOS_NYL.values():
            assert nombre.strip(), f"Nombre vacío para capítulo: {nombre!r}"

    def test_keys_cubren_todos_los_capitulos_del_template(self) -> None:
        """Cada sección del template tiene su capítulo definido."""
        capitulos_template = {cat.numero.split(".")[0] for cat in TEMPLATE_MODEL_DEVELOPMENT}
        assert capitulos_template == set(CAPITULOS_NYL.keys())


class TestAgruparSeccionesPorCapitulo:
    """`agrupar_secciones_por_capitulo()` devuelve list[(cap_num, cap_nombre, [secciones])]."""

    def test_devuelve_9_grupos_para_template_completo(self) -> None:
        secciones = construir_secciones_vacias()
        grupos = agrupar_secciones_por_capitulo(secciones)
        assert len(grupos) == 9

    def test_ordenados_por_numero_de_capitulo(self) -> None:
        secciones = construir_secciones_vacias()
        grupos = agrupar_secciones_por_capitulo(secciones)
        numeros = [g[0] for g in grupos]
        assert numeros == [str(i) for i in range(1, 10)]

    def test_nombre_capitulo_coincide_con_constante(self) -> None:
        secciones = construir_secciones_vacias()
        grupos = agrupar_secciones_por_capitulo(secciones)
        for num, nombre, _ in grupos:
            assert nombre == CAPITULOS_NYL[num]

    def test_secciones_dentro_del_grupo_corresponden_al_capitulo(self) -> None:
        secciones = construir_secciones_vacias()
        grupos = agrupar_secciones_por_capitulo(secciones)
        for num_cap, _, secs in grupos:
            for s in secs:
                assert s.numero.split(".")[0] == num_cap

    def test_orden_de_secciones_preserva_orden_template(self) -> None:
        # Las secciones dentro de cada capítulo van en orden ascendente por numero
        secciones = construir_secciones_vacias()
        grupos = agrupar_secciones_por_capitulo(secciones)
        for _, _, secs in grupos:
            numeros = [s.numero for s in secs]
            # Validar orden (esto asume orden lexicográfico tipo "5.3.1" < "5.3.2")
            assert numeros == sorted(numeros, key=lambda n: [int(p) for p in n.split(".")])

    def test_total_de_secciones_se_preserva(self) -> None:
        secciones = construir_secciones_vacias()
        grupos = agrupar_secciones_por_capitulo(secciones)
        total = sum(len(g[2]) for g in grupos)
        assert total == len(secciones) == 28

    def test_lista_vacia_devuelve_grupos_vacios(self) -> None:
        grupos = agrupar_secciones_por_capitulo([])
        # Aunque la lista esté vacía, devolvemos los 9 capítulos del catálogo
        # con listas vacías — facilita rendering consistente del dashboard.
        assert len(grupos) == 9
        for _, _, secs in grupos:
            assert secs == []

    def test_secciones_de_capitulo_5_incluyen_subseccciones(self) -> None:
        secciones = construir_secciones_vacias()
        grupos = agrupar_secciones_por_capitulo(secciones)
        cap5 = next(g for g in grupos if g[0] == "5")
        numeros_cap5 = [s.numero for s in cap5[2]]
        # 5.1, 5.2, 5.3.1, 5.3.2, 5.3.3, 5.4, 5.5
        assert "5.3.1" in numeros_cap5
        assert "5.3.3" in numeros_cap5
        assert len(cap5[2]) == 7
