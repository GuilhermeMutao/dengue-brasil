"""
Dashboard Arboviroses Brasil — Entrypoint.

Aplicação web interativa para análise e monitoramento de dados de
arboviroses (dengue, chikungunya, zika) no Brasil, desenvolvida como
Trabalho de Conclusão de Curso da Especialização em Ciência de Dados
do IFTM — Campus Uberaba Parque Tecnológico.

Autor: Guilherme José Morais Mutão
Orientador: Prof.
Camilo de Lelis Tosta Paula
Ano: 2025
"""

import streamlit as st

from src.constants import (
    APP_ICON,
    APP_LAYOUT,
    APP_TITLE,
    LABELS_DOENCA,
    obter_icone_doenca,
    obter_nome_doenca,
)

# ---------------------------------------------------------------------------
# Configuração da página (deve ser a PRIMEIRA chamada Streamlit)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout=APP_LAYOUT,
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Definição das páginas
# ---------------------------------------------------------------------------
visao_geral = st.Page(
    "pages/01_visao_geral.py",
    title="Visão Geral",
    icon=":material/dashboard:",
    default=True,
)
mapa = st.Page(
    "pages/02_mapa.py",
    title="Mapa Interativo",
    icon=":material/map:",
)
serie_temporal = st.Page(
    "pages/03_serie_temporal.py",
    title="Série Temporal",
    icon=":material/timeline:",
)
comparativo = st.Page(
    "pages/04_comparativo.py",
    title="Comparativo Regional",
    icon=":material/bar_chart:",
)
clima = st.Page(
    "pages/06_clima.py",
    title="Análise Climática",
    icon=":material/thermostat:",
)
sobre = st.Page(
    "pages/05_sobre.py",
    title="Sobre o Projeto",
    icon=":material/info:",
)

# ---------------------------------------------------------------------------
# Navegação
# ---------------------------------------------------------------------------
pg = st.navigation(
    {
        "Dashboard": [visao_geral, mapa],
        "Análises": [serie_temporal, comparativo, clima],
        "Informações": [sobre],
    }
)

# ---------------------------------------------------------------------------
# Sidebar global
# ---------------------------------------------------------------------------
with st.sidebar:
    doenca_sel = st.selectbox(
        "Doença",
        options=list(LABELS_DOENCA.keys()),
        format_func=lambda d: LABELS_DOENCA[d],
        index=0,
        key="doenca_global",
        help="Selecione a arbovirose para análise. Todas as páginas usarão esta seleção.",
    )
    st.session_state["doenca"] = doenca_sel

    icone = obter_icone_doenca(doenca_sel)
    nome = obter_nome_doenca(doenca_sel)
    st.markdown(f"### {icone} Dashboard {nome} Brasil")
    st.caption(
        f"Análise e monitoramento de dados de saúde pública · "
        f"{nome} no Brasil"
    )
    st.divider()

# ---------------------------------------------------------------------------
# Executar página selecionada
# ---------------------------------------------------------------------------
pg.run()
