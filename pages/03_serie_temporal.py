"""
Página: Série Temporal — Evolução dos casos ao longo do tempo.
"""

import streamlit as st
import pandas as pd

from src.api_infodengue import (
    buscar_dados_brasil_top_municipios,
    buscar_dados_estado_top_municipios,
    agregar_nacional_por_semana,
    agregar_por_uf_semana,
)
from src.data_processing import (
    limpar_dados,
    filtrar_por_periodo,
    adicionar_info_uf,
    extrair_ano_semana,
    calcular_variacao_semanal,
    adicionar_metricas_estimativa,
)
from src.charts import (
    serie_temporal,
    serie_temporal_com_estimativa,
    serie_curva_epidemica,
    heatmap_temporal,
    heatmap_estados,
)
from src.constants import (
    ANO_MINIMO,
    ANO_MAXIMO,
    ESTADOS,
    ESCALAS_HEATMAP_SAZONAL,
    LISTA_UFS,
    METRICAS,
    mensagem_sem_dados_doenca,
    obter_nome_doenca,
    obter_prefixo_doenca,
)

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

    # Média móvel
    media_movel = st.toggle(
        "Média móvel (4 semanas)",
        value=False,
        help="Exibe linha suavizada com média móvel de 4 semanas.",
        key="serie_media_movel",
    )

# ---------------------------------------------------------------------------
# Título
# ---------------------------------------------------------------------------
_doenca = st.session_state.get("doenca", "dengue")
_nome_doenca = obter_nome_doenca(_doenca)
_prefixo_doenca = obter_prefixo_doenca(_doenca)

st.title("📈 Série Temporal")
st.markdown(
    f"Acompanhe a evolução dos casos de **{_nome_doenca}** ao longo das semanas "
    "epidemiológicas. Compare estados ou analise a tendência nacional."
)
st.divider()

# ---------------------------------------------------------------------------
# Modo: Brasil agregado
# ---------------------------------------------------------------------------
if modo == "Brasil (agregado)":
    with st.spinner("Buscando dados nacionais…"):
        df_bruto = buscar_dados_brasil_top_municipios(
            ey_start=ano_inicio,
            ey_end=ano_fim,
            disease=_doenca,
        )

    if df_bruto.empty:
        st.error(mensagem_sem_dados_doenca(_doenca))
        st.stop()

    df = limpar_dados(df_bruto)
    df = filtrar_por_periodo(df, ano_inicio, ano_fim)
    df_nacional = agregar_nacional_por_semana(df)
    df_nacional = adicionar_metricas_estimativa(df_nacional)

    # Calcular variação semanal
    df_nacional = calcular_variacao_semanal(df_nacional, coluna=metrica)

    # Média móvel
    if media_movel and metrica in df_nacional.columns:
        df_nacional[f"{metrica}_mm4"] = (
            df_nacional[metrica].rolling(4, min_periods=1).mean()
        )

    # KPIs de variação
    if f"{metrica}_var_pct" in df_nacional.columns:
        ultimas = df_nacional.dropna(subset=[f"{metrica}_var_pct"]).tail(4)
        if not ultimas.empty:
            kpi1, kpi2, kpi3 = st.columns(3)
            with kpi1:
                ult_var = ultimas[f"{metrica}_var_pct"].iloc[-1]
                st.metric(
                    "Variação Última Semana",
                    f"{ult_var:+.1f}%",
                    delta=f"{'↑' if ult_var > 0 else '↓'} {'aumento' if ult_var > 0 else 'redução'}",
                    delta_color="inverse",
                )
            with kpi2:
                media_var = ultimas[f"{metrica}_var_pct"].mean()
                st.metric(
                    "Variação Média (4 sem.)",
                    f"{media_var:+.1f}%",
                    help="Média da variação percentual das últimas 4 semanas.",
                )
            with kpi3:
                total = int(df_nacional[metrica].sum()) if metrica in df_nacional.columns else 0
                st.metric(
                    f"Total {METRICAS.get(metrica, metrica)}",
                    f"{total:,}",
                )
            st.divider()

    # Tabs: Série simples | Notificados vs Estimados | Curva Epidêmica | Heatmap
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Série Temporal",
        "🔍 Notificados vs. Estimados",
        "🔄 Curva Epidêmica Anual",
        "🌡️ Mapa de Calor Sazonal",
    ])

    with tab1:
        import plotly.graph_objects as go

        fig = serie_temporal(
            df_nacional,
            coluna_y=metrica,
            titulo=f"{METRICAS.get(metrica, metrica)} — Brasil ({ano_inicio}–{ano_fim})",
        )

        # Adicionar média móvel se ativada
        if media_movel and f"{metrica}_mm4" in df_nacional.columns:
            coluna_x = "data" if "data" in df_nacional.columns else "se"
            df_sorted = df_nacional.sort_values(coluna_x)
            fig.add_trace(
                go.Scatter(
                    x=df_sorted[coluna_x],
                    y=df_sorted[f"{metrica}_mm4"],
                    mode="lines",
                    name="Média Móvel (4 sem.)",
                    line=dict(color="#F39C12", width=3, dash="dash"),
                )
            )

        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        total_notificado = float(df_nacional["casos"].sum()) if "casos" in df_nacional.columns else 0.0
        total_estimado = float(df_nacional["casos_est"].sum()) if "casos_est" in df_nacional.columns else 0.0
        ajuste_total = total_estimado - total_notificado
        ajuste_total_pct = (ajuste_total / total_notificado) * 100 if total_notificado > 0 else 0.0
        ultimas_4 = df_nacional.tail(4)
        ajuste_4 = float(ultimas_4["diferenca_est_notif"].sum()) if "diferenca_est_notif" in ultimas_4.columns else 0.0
        notificados_4 = float(ultimas_4["casos"].sum()) if "casos" in ultimas_4.columns else 0.0
        ajuste_4_pct = (ajuste_4 / notificados_4) * 100 if notificados_4 > 0 else 0.0

        card1, card2, card3, card4 = st.columns(4)
        with card1:
            st.metric(
                "Total Notificado",
                f"{total_notificado:,.0f}",
                help="Soma dos casos já notificados no período selecionado.",
            )
        with card2:
            st.metric(
                "Total Estimado",
                f"{total_estimado:,.0f}",
                help="Soma dos casos estimados pelo nowcasting do InfoDengue.",
            )
        with card3:
            st.metric(
                "Ajuste Total",
                f"{ajuste_total:+,.0f}",
                delta=f"{ajuste_total_pct:+.1f}%",
                delta_color="inverse",
                help="Diferença entre casos estimados e notificados no período.",
            )
        with card4:
            st.metric(
                "Ajuste 4 Semanas",
                f"{ajuste_4:+,.0f}",
                delta=f"{ajuste_4_pct:+.1f}%",
                delta_color="inverse",
                help="Diferença acumulada nas últimas 4 semanas da série filtrada.",
            )

        st.info(
            "**Como interpretar:** os casos notificados são registros já recebidos; "
            "os casos estimados usam nowcasting para compensar atrasos de notificação, "
            "especialmente nas semanas mais recentes. A banda vermelha mostra a faixa "
            "de incerteza da estimativa; quanto mais larga, maior a cautela ao tirar "
            "conclusões sobre a tendência."
        )

        fig_est = serie_temporal_com_estimativa(
            df_nacional,
            titulo=f"Casos Notificados vs. Estimados — {_nome_doenca} Brasil ({ano_inicio}–{ano_fim})",
        )
        st.plotly_chart(fig_est, use_container_width=True)

    with tab3:
        st.markdown(
            "**Sobreposição anual**: cada linha representa um ano, alinhada pela "
            "semana epidemiológica (1–52). Permite comparar a intensidade da "
            "epidemia entre anos."
        )
        fig_curva = serie_curva_epidemica(
            df_nacional,
            coluna_valor=metrica,
            titulo=f"Curva Epidêmica — {METRICAS.get(metrica, metrica)} ({ano_inicio}–{ano_fim})",
        )
        st.plotly_chart(fig_curva, use_container_width=True)

    with tab4:
        df_heat = extrair_ano_semana(df_nacional)
        metrica_heat = "casos" if metrica not in df_heat.columns else metrica
        default_heat = "relativa_ano" if metrica_heat in {"casos", "casos_est", "inc"} else "absoluta"
        escala_heat = st.radio(
            "Escala de cores",
            options=list(ESCALAS_HEATMAP_SAZONAL.keys()),
            index=list(ESCALAS_HEATMAP_SAZONAL.keys()).index(default_heat),
            format_func=lambda e: ESCALAS_HEATMAP_SAZONAL[e],
            horizontal=True,
            key="serie_heatmap_escala",
            help=(
                "Use a escala relativa para comparar o formato sazonal entre anos. "
                "Use a absoluta para comparar magnitude real."
            ),
        )
        st.caption(
            "Dica: a escala relativa ao pico do ano evita que a epidemia de 2024 "
            "apague padrões menores em anos como 2023 e 2025."
        )
        fig_heat = heatmap_temporal(
            df_heat,
            coluna_valor=metrica_heat,
            titulo=f"Sazonalidade — {METRICAS.get(metrica_heat, metrica_heat)} por Semana e Ano",
            escala=escala_heat,
        )
        st.plotly_chart(fig_heat, use_container_width=True)
        st.info(
            "💡 **Como interpretar**: na escala relativa, a cor mostra o quanto cada "
            "semana representa do pico daquele mesmo ano. Ela é ideal para comparar "
            "o formato sazonal entre anos. Na escala absoluta, a cor mostra o volume "
            "real e anos epidêmicos podem dominar a visualização."
        )

    # Dados brutos com download
    with st.expander("📋 Ver dados brutos"):
        st.dataframe(df_nacional, hide_index=True, use_container_width=True)
        csv = df_nacional.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Baixar série temporal (CSV)",
            data=csv,
            file_name=f"{_prefixo_doenca}_serie_brasil_{ano_inicio}_{ano_fim}.csv",
            mime="text/csv",
            key="dl_serie_br",
        )

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
            df_uf = buscar_dados_estado_top_municipios(uf, ey_start=ano_inicio, ey_end=ano_fim, disease=_doenca)
            if not df_uf.empty:
                frames.append(df_uf)

    if not frames:
        st.error(mensagem_sem_dados_doenca(_doenca))
        st.stop()

    df_todos = pd.concat(frames, ignore_index=True)
    df_todos = limpar_dados(df_todos)
    df_todos = filtrar_por_periodo(df_todos, ano_inicio, ano_fim)
    df_todos = adicionar_info_uf(df_todos)

    # Agregar por UF e semana
    df_uf_semana = agregar_por_uf_semana(df_todos)

    # Tabs
    tab1, tab2, tab3 = st.tabs([
        "📊 Comparativo",
        "🔄 Curva Epidêmica",
        "🌡️ Mapa de Calor",
    ])

    with tab1:
        fig = serie_temporal(
            df_uf_semana,
            coluna_y=metrica,
            coluna_grupo="sigla_uf",
            titulo=f"{METRICAS.get(metrica, metrica)} — Comparativo ({ano_inicio}–{ano_fim})",
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        uf_curva = st.selectbox(
            "Estado para curva epidêmica",
            options=ufs_selecionadas,
            format_func=lambda s: f"{s} — {ESTADOS[s]['nome']}",
            key="serie_curva_uf",
        )
        df_curva_uf = df_uf_semana[df_uf_semana["sigla_uf"] == uf_curva]
        fig_curva = serie_curva_epidemica(
            df_curva_uf,
            coluna_valor=metrica,
            titulo=f"Curva Epidêmica — {ESTADOS[uf_curva]['nome']} ({ano_inicio}–{ano_fim})",
        )
        st.plotly_chart(fig_curva, use_container_width=True)

    with tab3:
        fig_hm = heatmap_estados(
            df_uf_semana,
            coluna_valor="casos" if metrica not in df_uf_semana.columns else metrica,
            titulo=f"Intensidade por Estado e Semana ({ano_inicio}–{ano_fim})",
        )
        st.plotly_chart(fig_hm, use_container_width=True)

    with st.expander("📋 Ver dados brutos"):
        st.dataframe(df_uf_semana, hide_index=True, use_container_width=True)
        csv = df_uf_semana.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Baixar comparativo (CSV)",
            data=csv,
            file_name=f"{_prefixo_doenca}_comparativo_{ano_inicio}_{ano_fim}.csv",
            mime="text/csv",
            key="dl_serie_comp",
        )
