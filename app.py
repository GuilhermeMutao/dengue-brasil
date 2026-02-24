"""
Dashboard Dengue Brasil — Entrypoint.

Aplicação web interativa para análise e monitoramento de dados de
dengue no Brasil, desenvolvida como Trabalho de Conclusão de Curso
da Especialização em Ciência de Dados do IFTM — Campus Uberaba
Parque Tecnológico.

Autor: Guilherme José Morais Mutão
Orientador: Prof. Dr. Ernani Viriato De Melo
Ano: 2025
"""

import streamlit as st

# ---------------------------------------------------------------------------
# Configuração da página (deve ser a PRIMEIRA chamada Streamlit)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard Dengue Brasil",
    page_icon="🦟",
    layout="wide",
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
        "Análises": [serie_temporal, comparativo],
        "Informações": [sobre],
    }
)

# ---------------------------------------------------------------------------
# Sidebar global
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🦟 Dashboard Dengue Brasil")
    st.caption(
        "Análise e monitoramento de dados de saúde pública · "
        "Dengue no Brasil"
    )
    st.divider()

# ---------------------------------------------------------------------------
# Executar página selecionada
# ---------------------------------------------------------------------------
pg.run()
