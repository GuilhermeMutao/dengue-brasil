"""
Página: Série Temporal — Evolução dos casos ao longo do tempo.
"""

import streamlit as st
import pandas as pd

from src.api_infodengue import (
    buscar_dados_brasil_capitais,
    buscar_dados_estado_capitais,
    agregar_nacional_por_semana,
    agregar_por_uf_semana,
)
from src.data_processing import (
    limpar_dados,
    filtrar_por_periodo,
    adicionar_info_uf,
    extrair_ano_semana,
    calcular_variacao_semanal,
)
from src.charts import (
    serie_temporal,
    serie_temporal_com_estimativa,
    heatmap_temporal,
)
from src.constants import ANO_MINIMO, ANO_MAXIMO, ESTADOS, LISTA_UFS, METRICAS

# ---------------------------------------------------------------------------
# Sidebar — Filtros
# ---------------------------------------------------------------------------
with st.sidebar:
    st.subheader("⚙️ Filtros da Série Temporal")

    ano_range = st.slider(
        "Período (anos)",
        min_value=ANO_MINIMO,
        max_value=ANO_MAXIMO,
        value=(2020, ANO_MAXIMO),
        step=1,
        key="serie_periodo",
    )
    ano_inicio, ano_fim = ano_range

    # Modo de visualização
    modo = st.radio(
        "Visualizar",
        ["Brasil (agregado)", "Comparar estados"],
        index=0,
        key="serie_modo",
    )

    ufs_selecionadas: list[str] = []
    if modo == "Comparar estados":
        ufs_selecionadas = st.multiselect(
            "Selecione estados (até 5)",
            options=LISTA_UFS,
            default=["SP", "RJ", "MG"],
            max_selections=5,
            format_func=lambda s: f"{s} — {ESTADOS[s]['nome']}",
            key="serie_ufs",
        )

    # Métrica
    metricas_serie = ["casos", "casos_est", "inc", "rt"]
    metrica = st.selectbox(
        "Métrica",
        options=metricas_serie,
        format_func=lambda m: METRICAS.get(m, m),
        index=0,
        key="serie_metrica",
    )

# ---------------------------------------------------------------------------
# Título
# ---------------------------------------------------------------------------
st.title("📈 Série Temporal")
st.markdown(
    "Acompanhe a evolução dos casos de dengue ao longo das semanas "
    "epidemiológicas. Compare estados ou analise a tendência nacional."
)
st.divider()

# ---------------------------------------------------------------------------
# Modo: Brasil agregado
# ---------------------------------------------------------------------------
if modo == "Brasil (agregado)":
    with st.spinner("Buscando dados nacionais…"):
        df_bruto = buscar_dados_brasil_capitais(ey_start=ano_inicio, ey_end=ano_fim)

    if df_bruto.empty:
        st.error("⚠️ Não foi possível obter dados. Tente novamente.")
        st.stop()

    df = limpar_dados(df_bruto)
    df = filtrar_por_periodo(df, ano_inicio, ano_fim)
    df_nacional = agregar_nacional_por_semana(df)

    # Tabs: Série simples | Notificados vs Estimados | Heatmap
    tab1, tab2, tab3 = st.tabs([
        "📊 Série Temporal",
        "🔍 Notificados vs. Estimados",
        "🌡️ Mapa de Calor Sazonal",
    ])

    with tab1:
        fig = serie_temporal(
            df_nacional,
            coluna_y=metrica,
            titulo=f"{METRICAS.get(metrica, metrica)} — Brasil ({ano_inicio}–{ano_fim})",
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        fig_est = serie_temporal_com_estimativa(
            df_nacional,
            titulo=f"Casos Notificados vs. Estimados — Brasil ({ano_inicio}–{ano_fim})",
        )
        st.plotly_chart(fig_est, use_container_width=True)

    with tab3:
        df_heat = extrair_ano_semana(df_nacional)
        fig_heat = heatmap_temporal(
            df_heat,
            coluna_valor="casos" if metrica not in df_heat.columns else metrica,
            titulo=f"Sazonalidade — {METRICAS.get(metrica, metrica)} por Semana e Ano",
        )
        st.plotly_chart(fig_heat, use_container_width=True)

    # Dados brutos
    with st.expander("📋 Ver dados brutos"):
        st.dataframe(df_nacional, hide_index=True, use_container_width=True)

# ---------------------------------------------------------------------------
# Modo: Comparar estados
# ---------------------------------------------------------------------------
else:
    if not ufs_selecionadas:
        st.info("Selecione pelo menos um estado na barra lateral.")
        st.stop()

    with st.spinner(f"Buscando dados de {len(ufs_selecionadas)} estados…"):
        frames = []
        for uf in ufs_selecionadas:
            df_uf = buscar_dados_estado_capitais(uf, ey_start=ano_inicio, ey_end=ano_fim)
            if not df_uf.empty:
                frames.append(df_uf)

    if not frames:
        st.error("Nenhum dado retornado para os estados selecionados.")
        st.stop()

    df_todos = pd.concat(frames, ignore_index=True)
    df_todos = limpar_dados(df_todos)
    df_todos = filtrar_por_periodo(df_todos, ano_inicio, ano_fim)
    df_todos = adicionar_info_uf(df_todos)

    # Agregar por UF e semana
    df_uf_semana = agregar_por_uf_semana(df_todos)

    # Tabs
    tab1, tab2 = st.tabs(["📊 Comparativo", "🌡️ Mapa de Calor"])

    with tab1:
        fig = serie_temporal(
            df_uf_semana,
            coluna_y=metrica,
            coluna_grupo="sigla_uf",
            titulo=f"{METRICAS.get(metrica, metrica)} — Comparativo ({ano_inicio}–{ano_fim})",
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        # Heatmap por estado
        from src.charts import heatmap_estados

        fig_hm = heatmap_estados(
            df_uf_semana,
            coluna_valor="casos" if metrica not in df_uf_semana.columns else metrica,
            titulo=f"Intensidade por Estado e Semana ({ano_inicio}–{ano_fim})",
        )
        st.plotly_chart(fig_hm, use_container_width=True)

    with st.expander("📋 Ver dados brutos"):
        st.dataframe(df_uf_semana, hide_index=True, use_container_width=True)
