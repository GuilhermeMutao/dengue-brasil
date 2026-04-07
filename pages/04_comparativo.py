"""
Página: Comparativo Regional — Barras, ranking e heatmaps regionais.
"""

import streamlit as st
import pandas as pd

from src.api_infodengue import (
    buscar_dados_brasil_top_municipios,
    resumo_por_uf,
)
from src.data_processing import (
    limpar_dados,
    filtrar_por_periodo,
    filtrar_por_regiao,
    adicionar_info_uf,
    adicionar_metricas_populacionais,
    top_n_localidades,
    extrair_ano_semana,
)
from src.charts import (
    barras_comparativo,
    barras_agrupadas_regiao,
    heatmap_estados,
    heatmap_temporal,
)
from src.constants import (
    ANO_MINIMO,
    ANO_MAXIMO,
    ESCALAS_HEATMAP_SAZONAL,
    METRICAS,
    METRICAS_MAPA,
    LISTA_REGIOES,
    mensagem_sem_dados_doenca,
    obter_nome_doenca,
    obter_prefixo_doenca,
)

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

    # Métricas expandidas
    opcoes_metrica = ["casos", "casos_est", "inc", "casos_por_100k", "pct_nacional", "taxa_est_notif"]
    metrica = st.selectbox(
        "Métrica de comparação",
        options=opcoes_metrica,
        format_func=lambda m: METRICAS.get(m, m),
        index=0,
        key="comp_metrica",
    )

    # Filtro por regiões
    regioes_sel = st.multiselect(
        "Filtrar por Macrorregião",
        options=LISTA_REGIOES,
        default=[],
        help="Deixe vazio para todas.",
        key="comp_regioes",
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
_doenca = st.session_state.get("doenca", "dengue")
_nome_doenca = obter_nome_doenca(_doenca)
_prefixo_doenca = obter_prefixo_doenca(_doenca)

st.title("📊 Comparativo Regional")
st.markdown(
    f"Compare estados e regiões do Brasil em relação aos indicadores de **{_nome_doenca}**. "
    "A visão nacional agrega os **principais municípios por UF**, o que melhora a "
    "representatividade sem consultar todos os municípios do país."
)
st.divider()

# ---------------------------------------------------------------------------
# Carregar dados
# ---------------------------------------------------------------------------
with st.spinner("Carregando dados para comparação…"):
    df_bruto = buscar_dados_brasil_top_municipios(ey_start=ano_inicio, ey_end=ano_fim, disease=_doenca)

if df_bruto.empty:
    st.error(mensagem_sem_dados_doenca(_doenca))
    st.stop()

df = limpar_dados(df_bruto)
df = adicionar_info_uf(df)
df = filtrar_por_periodo(df, ano_inicio, ano_fim)

# Aplicar filtro regional
if regioes_sel:
    df = filtrar_por_regiao(df, regioes_sel)

if df.empty:
    st.warning("Nenhum dado encontrado com os filtros aplicados.")
    st.stop()

df_resumo = resumo_por_uf(df)
df_resumo = adicionar_info_uf(df_resumo)
df_resumo = adicionar_metricas_populacionais(df_resumo)

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏆 Ranking por Estado",
    "👤 Ranking Per Capita",
    "🌎 Por Região",
    "🌡️ Heatmap Estados × Semana",
    "📅 Sazonalidade",
])

# -- Tab 1: Ranking de estados (absoluto)
with tab1:
    st.subheader(f"Top {top_n} Estados — {METRICAS.get(metrica, metrica)}")

    # Para métricas calculadas (casos_por_100k, pct_nacional, taxa_est_notif),
    # usar df_resumo diretamente se a coluna existir
    metrica_rank = metrica if metrica in df_resumo.columns else "casos"

    fig_rank = barras_comparativo(
        df=df_resumo,
        coluna_x="sigla_uf",
        coluna_y=metrica_rank,
        titulo="",
        horizontal=True,
        top_n=top_n,
    )
    st.plotly_chart(fig_rank, use_container_width=True)

    with st.expander("📋 Ver tabela completa"):
        cols_tabela = [c for c in [
            "sigla_uf", "nome_uf", "regiao", "populacao",
            "casos", "casos_est", "casos_por_100k", "pct_nacional",
            "inc", "taxa_est_notif", "nivel",
        ] if c in df_resumo.columns]
        df_tab = df_resumo[cols_tabela].sort_values(metrica_rank, ascending=False)
        st.dataframe(
            df_tab,
            column_config={
                "populacao": st.column_config.NumberColumn("População", format="%d"),
                "casos": st.column_config.NumberColumn("Casos", format="%d"),
                "casos_est": st.column_config.NumberColumn("Estimados", format="%d"),
                "casos_por_100k": st.column_config.NumberColumn("Casos/100k", format="%.1f"),
                "pct_nacional": st.column_config.NumberColumn("% Nacional", format="%.2f%%"),
                "taxa_est_notif": st.column_config.NumberColumn("Razão Est/Notif", format="%.2f"),
                "inc": st.column_config.NumberColumn("Incidência", format="%.2f"),
            },
            hide_index=True,
            use_container_width=True,
        )
        csv_comp = df_tab.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Baixar ranking (CSV)",
            data=csv_comp,
            file_name=f"{_prefixo_doenca}_comparativo_ranking_{ano_inicio}_{ano_fim}.csv",
            mime="text/csv",
            key="dl_comp_rank",
        )

# -- Tab 2: Ranking per capita
with tab2:
    st.subheader(f"Top {top_n} Estados — Casos por 100 mil habitantes")

    if "casos_por_100k" in df_resumo.columns:
        fig_pc = barras_comparativo(
            df=df_resumo,
            coluna_x="sigla_uf",
            coluna_y="casos_por_100k",
            titulo="",
            horizontal=True,
            top_n=top_n,
        )
        st.plotly_chart(fig_pc, use_container_width=True)

        st.info(
            "💡 **Nota**: O ranking per capita normaliza pelo tamanho da população, "
            "evidenciando estados proporcionalmente mais afetados independente do "
            "tamanho populacional."
        )
    else:
        st.info("Métricas per capita não disponíveis.")

# -- Tab 3: Por região
with tab3:
    st.subheader(f"{METRICAS.get(metrica, metrica)} por Macrorregião")

    col1, col2 = st.columns(2)

    metrica_regiao = metrica if metrica in df_resumo.columns else "casos"

    with col1:
        fig_regiao = barras_agrupadas_regiao(
            df_resumo,
            coluna_y=metrica_regiao,
            titulo="",
        )
        st.plotly_chart(fig_regiao, use_container_width=True)

    with col2:
        if "regiao" in df_resumo.columns:
            agg_cols = {metrica_regiao: "sum", "sigla_uf": "count"}
            if "populacao" in df_resumo.columns:
                agg_cols["populacao"] = "sum"

            df_reg = (
                df_resumo.groupby("regiao", as_index=False)
                .agg(agg_cols)
                .rename(columns={"sigla_uf": "qtd_estados"})
                .sort_values(metrica_regiao, ascending=False)
            )

            col_config = {
                "regiao": "Região",
                metrica_regiao: st.column_config.NumberColumn(
                    METRICAS.get(metrica_regiao, metrica_regiao),
                    format="%d" if metrica_regiao in ("casos", "casos_est") else "%.2f",
                ),
                "qtd_estados": "Nº Estados",
            }
            if "populacao" in df_reg.columns:
                col_config["populacao"] = st.column_config.NumberColumn("População", format="%d")

            st.dataframe(
                df_reg,
                column_config=col_config,
                hide_index=True,
                use_container_width=True,
            )

# -- Tab 4: Heatmap estados × semana
with tab4:
    st.subheader("Intensidade por Estado e Semana Epidemiológica")

    from src.api_infodengue import agregar_por_uf_semana

    df_uf_se = agregar_por_uf_semana(df)

    metrica_heat = metrica if metrica in df_uf_se.columns else "casos"

    fig_heat = heatmap_estados(
        df_uf_se,
        coluna_valor=metrica_heat,
        titulo="",
    )
    st.plotly_chart(fig_heat, use_container_width=True)

# -- Tab 5: Sazonalidade
with tab5:
    st.subheader("Padrão Sazonal — Casos por Semana e Ano")

    from src.api_infodengue import agregar_nacional_por_semana

    df_nacional = agregar_nacional_por_semana(df)
    df_nacional = extrair_ano_semana(df_nacional)

    metrica_sazonal = metrica if metrica in df_nacional.columns else "casos"
    default_heat = "relativa_ano" if metrica_sazonal in {"casos", "casos_est", "inc"} else "absoluta"
    escala_heat = st.radio(
        "Escala de cores",
        options=list(ESCALAS_HEATMAP_SAZONAL.keys()),
        index=list(ESCALAS_HEATMAP_SAZONAL.keys()).index(default_heat),
        format_func=lambda e: ESCALAS_HEATMAP_SAZONAL[e],
        horizontal=True,
        key="comp_heatmap_sazonal_escala",
        help=(
            "Use a escala relativa para enxergar o padrão sazonal entre anos; "
            "use a absoluta para comparar volume real."
        ),
    )
    st.caption(
        "Dica: a escala relativa ao pico do ano reduz a dominância visual de anos "
        "epidêmicos, como 2024."
    )

    fig_sazonal = heatmap_temporal(
        df_nacional,
        coluna_valor=metrica_sazonal,
        titulo="",
        escala=escala_heat,
    )
    st.plotly_chart(fig_sazonal, use_container_width=True)

    st.info(
        "💡 **Como interpretar**: na escala relativa, cada ano é comparado com o "
        "seu próprio pico, facilitando enxergar em quais semanas a sazonalidade "
        "aparece. Na escala absoluta, as cores comparam o volume real entre anos. "
        "Em arboviroses transmitidas pelo Aedes, picos costumam se concentrar no "
        "verão e no outono, mas o padrão pode variar por doença, localidade e ano."
    )
