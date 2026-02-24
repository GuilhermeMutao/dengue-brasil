"""
Página: Visão Geral — KPIs nacionais e resumo epidemiológico.
"""

import streamlit as st
import pandas as pd

from src.api_infodengue import (
    buscar_dados_brasil_capitais,
    agregar_nacional_por_semana,
    resumo_por_uf,
)
from src.api_ibge import carregar_geojson_estados, obter_feature_id_key_estados
from src.data_processing import (
    limpar_dados,
    filtrar_por_periodo,
    filtrar_por_regiao,
    filtrar_por_nivel_alerta,
    adicionar_info_uf,
    adicionar_metricas_populacionais,
    calcular_kpis,
    preparar_dados_mapa_estados,
    extrair_ano_semana,
)
from src.charts import (
    mapa_coropletico_estados,
    serie_temporal,
    barras_agrupadas_regiao,
    gauge_nivel_alerta,
)
from src.constants import (
    ANO_MINIMO,
    ANO_MAXIMO,
    LABELS_NIVEL_ALERTA,
    CORES_NIVEL_ALERTA,
    LISTA_REGIOES,
    METRICAS,
    METRICAS_MAPA,
    POPULACAO_BRASIL,
)

# ---------------------------------------------------------------------------
# Sidebar — Filtros
# ---------------------------------------------------------------------------
with st.sidebar:
    st.subheader("⚙️ Filtros")

    ano_range = st.slider(
        "Período (anos)",
        min_value=ANO_MINIMO,
        max_value=ANO_MAXIMO,
        value=(2020, ANO_MAXIMO),
        step=1,
        help="Selecione o intervalo de anos para análise.",
    )
    ano_inicio, ano_fim = ano_range

    # Filtro por macrorregião
    regioes_sel = st.multiselect(
        "Macrorregiões",
        options=LISTA_REGIOES,
        default=[],
        help="Deixe vazio para todas as regiões.",
        key="vg_regioes",
    )

    # Filtro por nível de alerta
    niveis_sel = st.multiselect(
        "Nível de Alerta",
        options=[1, 2, 3, 4],
        format_func=lambda n: LABELS_NIVEL_ALERTA.get(n, str(n)),
        default=[],
        help="Filtrar estados pelo nível de alerta predominante.",
        key="vg_niveis",
    )

    # Métrica para o mapa
    metrica_mapa = st.selectbox(
        "Métrica do Mapa",
        options=METRICAS_MAPA,
        format_func=lambda m: METRICAS.get(m, m),
        index=0,
        key="vg_metrica_mapa",
    )

    # Escala logarítmica
    log_scale = st.toggle(
        "Escala logarítmica no mapa",
        value=False,
        help="Suaviza dominância de estados com valores muito altos (ex: SP).",
        key="vg_log_scale",
    )

# ---------------------------------------------------------------------------
# Título
# ---------------------------------------------------------------------------
_doenca = st.session_state.get("doenca", "dengue")
_nomes_doenca = {"dengue": "Dengue", "chikungunya": "Chikungunya", "zika": "Zika"}
_nome_doenca = _nomes_doenca.get(_doenca, "Dengue")

st.title(f"🦟 Visão Geral — {_nome_doenca} no Brasil")
st.markdown(
    f"Panorama nacional com base nos dados das **27 capitais estaduais** "
    f"(*proxy* para visão por estado). Fonte: [InfoDengue](https://info.dengue.mat.br)."
)
st.divider()

# ---------------------------------------------------------------------------
# Carregar e processar dados
# ---------------------------------------------------------------------------
with st.spinner("Buscando dados das capitais brasileiras…"):
    df_bruto = buscar_dados_brasil_capitais(ey_start=ano_inicio, ey_end=ano_fim, disease=_doenca)

if df_bruto.empty:
    st.error("⚠️ Não foi possível obter dados da API InfoDengue. Tente novamente mais tarde.")
    st.stop()

# Limpeza e enriquecimento
df = limpar_dados(df_bruto)
df = adicionar_info_uf(df)
df = filtrar_por_periodo(df, ano_inicio, ano_fim)

# Agregações (antes de filtros de região/nível para KPIs nacionais)
df_nacional = agregar_nacional_por_semana(df)
kpis = calcular_kpis(df_nacional)

# Aplicar filtros opcionais
if regioes_sel:
    df = filtrar_por_regiao(df, regioes_sel)
if niveis_sel:
    df = filtrar_por_nivel_alerta(df, niveis_sel)

if df.empty:
    st.warning("Nenhum dado encontrado com os filtros aplicados.")
    st.stop()

# Resumo por UF com métricas populacionais
df_resumo_uf = resumo_por_uf(df)
df_resumo_uf = adicionar_info_uf(df_resumo_uf)
df_resumo_uf = adicionar_metricas_populacionais(df_resumo_uf)

# ---------------------------------------------------------------------------
# Cards KPI — Linha 1: Contadores
# ---------------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total de Casos (Capitais)",
        value=f"{kpis['total_casos']:,.0f}",
        help="Soma dos casos notificados das capitais no período.",
    )

with col2:
    st.metric(
        label="Casos Estimados",
        value=f"{kpis['total_casos_est']:,.0f}",
        help="Soma dos casos estimados pelo nowcasting do InfoDengue.",
    )

with col3:
    st.metric(
        label="Última Semana Epi.",
        value=f"{kpis['casos_ultima_semana']:,.0f}",
        delta=f"{kpis['variacao_semanal']:+.1f}%",
        delta_color="inverse",
        help=f"Casos na SE {kpis['ultima_semana']} e variação semanal.",
    )

with col4:
    nivel = kpis["nivel_predominante"]
    cor = CORES_NIVEL_ALERTA.get(nivel, "#999")
    label = LABELS_NIVEL_ALERTA.get(nivel, "—")
    st.metric(
        label="Nível de Alerta Predominante",
        value=label.split("—")[0].strip(),
        help=f"{label}. Baseado na moda do nível de alerta.",
    )

# Cards KPI — Linha 2: Indicadores adicionais
col5, col6, col7, col8 = st.columns(4)

with col5:
    st.metric(
        label="Incidência Média (por 100k)",
        value=f"{kpis['media_incidencia']:.1f}",
        help="Média aritmética da incidência por 100 mil hab. no período.",
    )

with col6:
    # Rt com indicador de tendência
    rt_val = kpis['media_rt']
    rt_delta = "↑ Expansão" if rt_val > 1 else "↓ Retração"
    st.metric(
        label="Rt Médio",
        value=f"{rt_val:.2f}",
        delta=rt_delta,
        delta_color="inverse" if rt_val > 1 else "normal",
        help="Número reprodutivo médio. Rt > 1 indica tendência de crescimento.",
    )

with col7:
    # Probabilidade de Rt > 1
    p_rt1_val = float(df_nacional["p_rt1"].mean()) if "p_rt1" in df_nacional.columns else None
    if p_rt1_val is not None:
        st.metric(
            label="P(Rt > 1)",
            value=f"{p_rt1_val:.1%}",
            help="Probabilidade média de Rt > 1 no período. Valores altos indicam risco de expansão.",
        )
    else:
        pop_filtrada = int(df_resumo_uf["populacao"].sum()) if "populacao" in df_resumo_uf.columns else POPULACAO_BRASIL
        st.metric(
            label="População Coberta",
            value=f"{pop_filtrada:,.0f}",
            help="Soma da população estimada dos estados filtrados (IBGE 2024).",
        )

with col8:
    if not df_resumo_uf.empty and "casos_por_100k" in df_resumo_uf.columns:
        top_pc = df_resumo_uf.nlargest(1, "casos_por_100k").iloc[0]
        st.metric(
            label="Maior Incid. per Capita",
            value=f"{top_pc['sigla_uf']}",
            delta=f"{top_pc['casos_por_100k']:.0f}/100k",
            delta_color="off",
            help=f"{top_pc.get('nome_uf', '')} — {top_pc['casos_por_100k']:.1f} casos por 100 mil hab.",
        )
    else:
        st.metric(label="Maior Incid. per Capita", value="—")

# Gauge de nível de alerta
with st.container():
    col_gauge, col_info = st.columns([1, 2])
    with col_gauge:
        nivel = kpis["nivel_predominante"]
        fig_gauge = gauge_nivel_alerta(nivel, titulo="Nível de Alerta Nacional")
        st.plotly_chart(fig_gauge, use_container_width=True)
    with col_info:
        st.markdown(
            f"**Nível predominante**: {LABELS_NIVEL_ALERTA.get(nivel, '—')}\n\n"
            f"Baseado na moda do nível de alerta das 27 capitais no período "
            f"{ano_inicio}–{ano_fim}. O nível de alerta do InfoDengue considera "
            f"incidência, Rt e tendência dos casos."
        )

st.divider()

# ---------------------------------------------------------------------------
# Mapa coroplético + Barras por região (lado a lado)
# ---------------------------------------------------------------------------
col_mapa, col_barras = st.columns([3, 2])

with col_mapa:
    st.subheader(f"📍 {METRICAS.get(metrica_mapa, metrica_mapa)} por Estado")
    try:
        geojson = carregar_geojson_estados()
        feature_key = obter_feature_id_key_estados(geojson)
        df_mapa = preparar_dados_mapa_estados(df_resumo_uf)

        fig_mapa = mapa_coropletico_estados(
            df=df_mapa,
            geojson=geojson,
            feature_id_key=feature_key,
            metrica=metrica_mapa,
            titulo="",
            log_scale=log_scale,
        )
        st.plotly_chart(fig_mapa, use_container_width=True)
    except Exception as e:
        st.warning(f"Não foi possível carregar o mapa: {e}")

with col_barras:
    st.subheader("📊 Casos por Região")
    fig_regiao = barras_agrupadas_regiao(
        df_resumo_uf,
        coluna_y="casos",
        titulo="",
    )
    st.plotly_chart(fig_regiao, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# Série temporal nacional
# ---------------------------------------------------------------------------
st.subheader("📈 Evolução Temporal — Total Nacional (Capitais)")

if not df_nacional.empty:
    fig_serie = serie_temporal(
        df_nacional,
        coluna_y="casos",
        titulo="",
    )
    st.plotly_chart(fig_serie, use_container_width=True)
else:
    st.info("Sem dados suficientes para a série temporal.")

# ---------------------------------------------------------------------------
# Tabela ranking de estados — Tabs Absoluto vs. Per Capita
# ---------------------------------------------------------------------------
st.subheader("🏆 Ranking de Capitais")

if not df_resumo_uf.empty:
    tab_abs, tab_pc = st.tabs(["📊 Por Volume (Absoluto)", "👤 Per Capita (por 100k hab.)"])

    colunas_base = [
        "sigla_uf", "nome_uf", "regiao", "populacao",
        "casos", "casos_est", "casos_por_100k", "pct_nacional",
        "inc", "taxa_est_notif", "nivel",
    ]
    colunas_existentes = [c for c in colunas_base if c in df_resumo_uf.columns]

    max_pct = float(df_resumo_uf["pct_nacional"].max()) if "pct_nacional" in df_resumo_uf.columns and not df_resumo_uf["pct_nacional"].empty else 100.0

    column_config_base = {
        "sigla_uf": st.column_config.TextColumn("UF", width="small"),
        "nome_uf": st.column_config.TextColumn("Estado", width="medium"),
        "regiao": st.column_config.TextColumn("Região", width="medium"),
        "populacao": st.column_config.NumberColumn("População", format="%d"),
        "casos": st.column_config.NumberColumn("Casos Notif.", format="%d"),
        "casos_est": st.column_config.NumberColumn("Casos Estim.", format="%d"),
        "casos_por_100k": st.column_config.NumberColumn("Casos/100k", format="%.1f"),
        "pct_nacional": st.column_config.ProgressColumn(
            "% Nacional", format="%.1f%%", min_value=0, max_value=max_pct,
        ),
        "inc": st.column_config.NumberColumn("Incidência Média", format="%.2f"),
        "taxa_est_notif": st.column_config.NumberColumn("Razão Est/Notif", format="%.2f"),
        "nivel": st.column_config.NumberColumn(
            "Nível Alerta", format="%d",
            help="1=Verde, 2=Amarelo, 3=Laranja, 4=Vermelho",
        ),
    }

    with tab_abs:
        tabela_abs = df_resumo_uf[colunas_existentes].sort_values("casos", ascending=False)
        st.dataframe(
            tabela_abs, column_config=column_config_base,
            hide_index=True, use_container_width=True, height=450,
        )
        csv_abs = tabela_abs.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Baixar ranking absoluto (CSV)",
            data=csv_abs,
            file_name=f"ranking_absoluto_{ano_inicio}_{ano_fim}.csv",
            mime="text/csv",
            key="dl_rank_abs",
        )

    with tab_pc:
        if "casos_por_100k" in df_resumo_uf.columns:
            tabela_pc = df_resumo_uf[colunas_existentes].sort_values("casos_por_100k", ascending=False)
            st.dataframe(
                tabela_pc, column_config=column_config_base,
                hide_index=True, use_container_width=True, height=450,
            )
            csv_pc = tabela_pc.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Baixar ranking per capita (CSV)",
                data=csv_pc,
                file_name=f"ranking_percapita_{ano_inicio}_{ano_fim}.csv",
                mime="text/csv",
                key="dl_rank_pc",
            )
        else:
            st.info("Dados per capita não disponíveis.")
