"""
Página: Comparativo Regional — Barras, ranking e heatmaps regionais.
"""

import streamlit as st
import pandas as pd

from src.api_infodengue import (
    buscar_dados_brasil_capitais,
    resumo_por_uf,
)
from src.data_processing import (
    limpar_dados,
    filtrar_por_periodo,
    adicionar_info_uf,
    top_n_localidades,
    extrair_ano_semana,
)
from src.charts import (
    barras_comparativo,
    barras_agrupadas_regiao,
    heatmap_estados,
    heatmap_temporal,
)
from src.constants import ANO_MINIMO, ANO_MAXIMO, METRICAS

# ---------------------------------------------------------------------------
# Sidebar — Filtros
# ---------------------------------------------------------------------------
with st.sidebar:
    st.subheader("⚙️ Filtros do Comparativo")

    ano_range = st.slider(
        "Período (anos)",
        min_value=ANO_MINIMO,
        max_value=ANO_MAXIMO,
        value=(2020, ANO_MAXIMO),
        step=1,
        key="comp_periodo",
    )
    ano_inicio, ano_fim = ano_range

    metrica = st.selectbox(
        "Métrica de comparação",
        options=["casos", "casos_est", "inc"],
        format_func=lambda m: METRICAS.get(m, m),
        index=0,
        key="comp_metrica",
    )

    top_n = st.slider(
        "Quantidade no ranking",
        min_value=5,
        max_value=27,
        value=15,
        step=1,
        key="comp_top_n",
    )

# ---------------------------------------------------------------------------
# Título
# ---------------------------------------------------------------------------
st.title("📊 Comparativo Regional")
st.markdown(
    "Compare estados e regiões do Brasil em relação aos indicadores de dengue. "
    "Os dados são baseados nas capitais estaduais como proxy."
)
st.divider()

# ---------------------------------------------------------------------------
# Carregar dados
# ---------------------------------------------------------------------------
with st.spinner("Carregando dados para comparação…"):
    df_bruto = buscar_dados_brasil_capitais(ey_start=ano_inicio, ey_end=ano_fim)

if df_bruto.empty:
    st.error("⚠️ Não foi possível obter dados. Tente novamente.")
    st.stop()

df = limpar_dados(df_bruto)
df = adicionar_info_uf(df)
df = filtrar_por_periodo(df, ano_inicio, ano_fim)
df_resumo = resumo_por_uf(df)

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "🏆 Ranking por Estado",
    "🌎 Por Região",
    "🌡️ Heatmap Estados × Semana",
    "📅 Sazonalidade",
])

# -- Tab 1: Ranking de estados
with tab1:
    st.subheader(f"Top {top_n} Estados — {METRICAS.get(metrica, metrica)}")

    fig_rank = barras_comparativo(
        df=df_resumo,
        coluna_x="sigla_uf",
        coluna_y=metrica,
        titulo="",
        horizontal=True,
        top_n=top_n,
    )
    st.plotly_chart(fig_rank, use_container_width=True)

    with st.expander("📋 Ver tabela completa"):
        cols_tabela = [c for c in ["sigla_uf", "nome_uf", "regiao", "casos", "casos_est", "inc"] if c in df_resumo.columns]
        st.dataframe(
            df_resumo[cols_tabela].sort_values(metrica, ascending=False),
            hide_index=True,
            use_container_width=True,
        )

# -- Tab 2: Por região
with tab2:
    st.subheader(f"{METRICAS.get(metrica, metrica)} por Macrorregião")

    col1, col2 = st.columns(2)

    with col1:
        fig_regiao = barras_agrupadas_regiao(
            df_resumo,
            coluna_y=metrica,
            titulo="",
        )
        st.plotly_chart(fig_regiao, use_container_width=True)

    with col2:
        # Tabela por região
        if "regiao" in df_resumo.columns:
            df_reg = (
                df_resumo.groupby("regiao", as_index=False)
                .agg({metrica: "sum", "sigla_uf": "count"})
                .rename(columns={"sigla_uf": "qtd_estados"})
                .sort_values(metrica, ascending=False)
            )
            st.dataframe(
                df_reg,
                column_config={
                    "regiao": "Região",
                    metrica: st.column_config.NumberColumn(
                        METRICAS.get(metrica, metrica),
                        format="%d" if metrica != "inc" else "%.2f",
                    ),
                    "qtd_estados": "Nº Estados",
                },
                hide_index=True,
                use_container_width=True,
            )

# -- Tab 3: Heatmap estados × semana
with tab3:
    st.subheader("Intensidade por Estado e Semana Epidemiológica")

    # Precisamos dos dados por UF e SE (não agregados)
    from src.api_infodengue import agregar_por_uf_semana

    df_uf_se = agregar_por_uf_semana(df)

    fig_heat = heatmap_estados(
        df_uf_se,
        coluna_valor="casos" if metrica not in df_uf_se.columns else metrica,
        titulo="",
    )
    st.plotly_chart(fig_heat, use_container_width=True)

# -- Tab 4: Sazonalidade
with tab4:
    st.subheader("Padrão Sazonal — Casos por Semana e Ano")

    from src.api_infodengue import agregar_nacional_por_semana

    df_nacional = agregar_nacional_por_semana(df)
    df_nacional = extrair_ano_semana(df_nacional)

    fig_sazonal = heatmap_temporal(
        df_nacional,
        coluna_valor="casos" if metrica not in df_nacional.columns else metrica,
        titulo="",
    )
    st.plotly_chart(fig_sazonal, use_container_width=True)

    st.info(
        "💡 **Como interpretar**: Linhas mais escuras indicam maior incidência. "
        "Observe as colunas (semanas) com picos recorrentes — essas representam "
        "o período sazonal da dengue (geralmente entre as semanas 1–20, "
        "correspondentes ao verão e outono)."
    )
