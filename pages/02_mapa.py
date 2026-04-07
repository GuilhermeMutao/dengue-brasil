"""
Página: Mapa Interativo — Choropleth de estados e municípios.
"""

import streamlit as st
import pandas as pd

from src.api_infodengue import (
    buscar_dados_brasil_top_municipios,
    buscar_dados_municipios_uf,
    resumo_por_uf,
)
from src.api_ibge import (
    carregar_geojson_estados,
    carregar_geojson_municipios,
    carregar_municipios,
    obter_feature_id_key_estados,
    obter_feature_id_key_municipios,
)
from src.data_processing import (
    limpar_dados,
    filtrar_por_periodo,
    filtrar_por_regiao,
    adicionar_info_uf,
    adicionar_metricas_populacionais,
    preparar_dados_mapa_estados,
    preparar_dados_mapa_municipios,
)
from src.charts import mapa_coropletico_estados, mapa_coropletico_municipios
from streamlit_folium import st_folium
from src.constants import (
    ANO_MINIMO,
    ANO_MAXIMO,
    ESTADOS,
    LISTA_UFS,
    LISTA_REGIOES,
    METRICAS,
    METRICAS_MAPA,
    LABELS_NIVEL_ALERTA,
    mensagem_sem_dados_doenca,
    obter_nome_doenca,
    obter_prefixo_doenca,
)

# ---------------------------------------------------------------------------
# Sidebar — Filtros
# ---------------------------------------------------------------------------
with st.sidebar:
    st.subheader("⚙️ Filtros do Mapa")

    ano_range = st.slider(
        "Período (anos)",
        min_value=ANO_MINIMO,
        max_value=ANO_MAXIMO,
        value=(2020, ANO_MAXIMO),
        step=1,
        key="mapa_periodo",
    )
    ano_inicio, ano_fim = ano_range

    # Nível geográfico
    nivel_geo = st.radio(
        "Nível geográfico",
        options=["Brasil (Estados)", "Estado (Municípios)"],
        index=0,
        key="mapa_nivel_geo",
    )

    uf_selecionada = None
    if nivel_geo == "Estado (Municípios)":
        uf_selecionada = st.selectbox(
            "Selecione o estado",
            options=LISTA_UFS,
            format_func=lambda s: f"{s} — {ESTADOS[s]['nome']}",
            key="mapa_uf",
        )

    # Filtro por macrorregião (somente nível Brasil)
    regioes_sel = []
    if nivel_geo == "Brasil (Estados)":
        regioes_sel = st.multiselect(
            "Filtrar por Macrorregião",
            options=LISTA_REGIOES,
            default=[],
            help="Deixe vazio para todas as regiões.",
            key="mapa_regioes",
        )

    # Métrica
    metrica = st.selectbox(
        "Métrica para colorir o mapa",
        options=METRICAS_MAPA,
        format_func=lambda m: METRICAS.get(m, m),
        index=0,
        key="mapa_metrica",
    )

    # Escala logarítmica
    log_scale = st.toggle(
        "Escala logarítmica",
        value=False,
        help="Suaviza a dominância de regiões com valores extremos.",
        key="mapa_log_scale",
    )

# ---------------------------------------------------------------------------
# Título
# ---------------------------------------------------------------------------
_doenca = st.session_state.get("doenca", "dengue")
_nome_doenca = obter_nome_doenca(_doenca)
_prefixo_doenca = obter_prefixo_doenca(_doenca)

st.title(f"🗺️ Mapa Interativo — {_nome_doenca}")
st.markdown(
    f"Explore a distribuição geográfica da arbovirose selecionada: **{_nome_doenca}**. "
    "Selecione **Brasil** para visão por estados ou um **estado específico** "
    "para ver os municípios."
)
st.divider()

# ---------------------------------------------------------------------------
# Nível Brasil (estados)
# ---------------------------------------------------------------------------
if nivel_geo == "Brasil (Estados)":
    with st.spinner("Carregando dados nacionais…"):
        df_bruto = buscar_dados_brasil_top_municipios(ey_start=ano_inicio, ey_end=ano_fim, disease=_doenca)

    if df_bruto.empty:
        st.error(mensagem_sem_dados_doenca(_doenca))
        st.stop()

    df = limpar_dados(df_bruto)
    df = adicionar_info_uf(df)
    df = filtrar_por_periodo(df, ano_inicio, ano_fim)

    # Aplicar filtro de região
    if regioes_sel:
        df = filtrar_por_regiao(df, regioes_sel)

    if df.empty:
        st.warning("Nenhum dado encontrado com os filtros aplicados.")
        st.stop()

    df_resumo = resumo_por_uf(df)
    df_resumo = adicionar_info_uf(df_resumo)
    df_resumo = adicionar_metricas_populacionais(df_resumo)
    df_mapa = preparar_dados_mapa_estados(df_resumo)

    # Painel de resumo rápido acima do mapa
    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1:
        total_casos = int(df_resumo["casos"].sum()) if "casos" in df_resumo.columns else 0
        st.metric("Total de Casos", f"{total_casos:,.0f}")
    with kpi2:
        if "casos_por_100k" in df_resumo.columns and not df_resumo.empty:
            top = df_resumo.nlargest(1, "casos_por_100k").iloc[0]
            st.metric("Maior Incidência per Capita", f"{top['sigla_uf']} — {top['casos_por_100k']:.0f}/100k")
        else:
            st.metric("Maior Incidência per Capita", "—")
    with kpi3:
        if "casos" in df_resumo.columns and not df_resumo.empty:
            top_abs = df_resumo.nlargest(1, "casos").iloc[0]
            st.metric("Estado Mais Afetado", f"{top_abs['sigla_uf']} — {int(top_abs['casos']):,} casos")
        else:
            st.metric("Estado Mais Afetado", "—")

    st.divider()

    try:
        geojson = carregar_geojson_estados()
        feature_key = obter_feature_id_key_estados(geojson)

        fig = mapa_coropletico_estados(
            df=df_mapa,
            geojson=geojson,
            feature_id_key=feature_key,
            metrica=metrica,
            titulo=f"{METRICAS.get(metrica, metrica)} por Estado ({ano_inicio}–{ano_fim})",
            log_scale=log_scale,
        )
        st_folium(fig, use_container_width=True, height=600, returned_objects=[])
    except Exception as e:
        st.error(f"Erro ao renderizar mapa: {e}")

    # Tabela resumo abaixo do mapa
    with st.expander("📋 Ver dados em tabela", expanded=False):
        if not df_resumo.empty:
            cols = [c for c in [
                "sigla_uf", "nome_uf", "regiao", "populacao",
                "casos", "casos_est", "casos_por_100k", "pct_nacional",
                "inc", "taxa_est_notif", "nivel",
            ] if c in df_resumo.columns]

            sort_col = metrica if metrica in df_resumo.columns else "casos"
            st.dataframe(
                df_resumo[cols].sort_values(sort_col, ascending=False),
                column_config={
                    "populacao": st.column_config.NumberColumn("População", format="%d"),
                    "casos": st.column_config.NumberColumn("Casos Notif.", format="%d"),
                    "casos_est": st.column_config.NumberColumn("Casos Estim.", format="%d"),
                    "casos_por_100k": st.column_config.NumberColumn("Casos/100k", format="%.1f"),
                    "pct_nacional": st.column_config.NumberColumn("% Nacional", format="%.2f%%"),
                    "taxa_est_notif": st.column_config.NumberColumn("Razão Est/Notif", format="%.2f"),
                    "inc": st.column_config.NumberColumn("Incidência", format="%.2f"),
                    "nivel": st.column_config.NumberColumn("Nível", format="%d"),
                },
                hide_index=True,
                use_container_width=True,
            )
            csv_estados = df_resumo[cols].sort_values(sort_col, ascending=False).to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Baixar dados por estado (CSV)",
                data=csv_estados,
                file_name=f"{_prefixo_doenca}_estados_{ano_inicio}_{ano_fim}.csv",
                mime="text/csv",
                key="dl_mapa_estados",
            )

# ---------------------------------------------------------------------------
# Nível Estado (municípios)
# ---------------------------------------------------------------------------
else:
    if not uf_selecionada:
        st.info("Selecione um estado na barra lateral.")
        st.stop()

    info_uf = ESTADOS[uf_selecionada]

    st.subheader(f"📍 {info_uf['nome']} ({uf_selecionada})")
    st.caption(
        "⏳ O carregamento de municípios pode demorar dependendo "
        "da quantidade de municípios do estado."
    )

    # Carregar municípios
    with st.spinner("Obtendo lista de municípios…"):
        df_municipios = carregar_municipios(info_uf["cod_uf"])

    if df_municipios.empty:
        st.error("Não foi possível obter a lista de municípios.")
        st.stop()

    geocodes = df_municipios["geocode"].tolist()
    total_munic = len(geocodes)

    # Limitar quantidade se muitos municípios
    limite = st.sidebar.slider(
        "Máx. de municípios a consultar",
        min_value=10,
        max_value=min(total_munic, 200),
        value=min(total_munic, 50),
        step=10,
        key="mapa_limite_munic",
        help=f"O estado tem {total_munic} municípios. Consultar todos pode demorar.",
    )

    with st.spinner(f"Buscando dados de {limite} municípios…"):
        df_munic_dados = buscar_dados_municipios_uf(
            sigla_uf=uf_selecionada,
            geocodes=geocodes,
            ey_start=ano_inicio,
            ey_end=ano_fim,
            max_municipios=limite,
            disease=_doenca,
        )

    if df_munic_dados.empty:
        st.warning(mensagem_sem_dados_doenca(_doenca))
        st.stop()

    df_munic_dados = limpar_dados(df_munic_dados)
    df_munic_dados = filtrar_por_periodo(df_munic_dados, ano_inicio, ano_fim)
    df_mapa_munic = preparar_dados_mapa_municipios(df_munic_dados)

    # Merge nomes dos municípios
    if "geocode" in df_mapa_munic.columns:
        nomes = df_municipios[["geocode", "nome"]].copy()
        nomes["geocode"] = nomes["geocode"].astype(df_mapa_munic["geocode"].dtype)
        df_mapa_munic = df_mapa_munic.merge(nomes, on="geocode", how="left")

    # KPIs resumo do estado
    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1:
        total = int(df_mapa_munic["casos"].sum()) if "casos" in df_mapa_munic.columns else 0
        st.metric("Total de Casos", f"{total:,}")
    with kpi2:
        munic_dados = len(df_mapa_munic)
        st.metric("Municípios com Dados", f"{munic_dados}/{total_munic}")
    with kpi3:
        if "nivel" in df_mapa_munic.columns and not df_mapa_munic.empty:
            nivel_max = int(df_mapa_munic["nivel"].max())
            label_nivel = LABELS_NIVEL_ALERTA.get(nivel_max, "—")
            st.metric("Nível Máximo de Alerta", label_nivel.split("—")[0].strip())
        else:
            st.metric("Nível Máximo de Alerta", "—")

    st.divider()

    try:
        geojson_munic = carregar_geojson_municipios(info_uf["cod_uf"])
        feature_key_munic = obter_feature_id_key_municipios(geojson_munic)

        centros_uf = {
            "AC": {"lat": -9.0, "lon": -70.8}, "AL": {"lat": -9.5, "lon": -36.5},
            "AM": {"lat": -3.4, "lon": -65.0}, "AP": {"lat": 1.4, "lon": -51.8},
            "BA": {"lat": -12.6, "lon": -41.7}, "CE": {"lat": -5.5, "lon": -39.3},
            "DF": {"lat": -15.8, "lon": -47.9}, "ES": {"lat": -19.2, "lon": -40.3},
            "GO": {"lat": -15.9, "lon": -49.3}, "MA": {"lat": -5.4, "lon": -45.4},
            "MG": {"lat": -18.5, "lon": -44.6}, "MS": {"lat": -20.8, "lon": -54.8},
            "MT": {"lat": -12.7, "lon": -56.1}, "PA": {"lat": -3.2, "lon": -52.0},
            "PB": {"lat": -7.1, "lon": -36.6}, "PE": {"lat": -8.3, "lon": -37.9},
            "PI": {"lat": -7.7, "lon": -42.7}, "PR": {"lat": -24.9, "lon": -51.6},
            "RJ": {"lat": -22.2, "lon": -42.5}, "RN": {"lat": -5.6, "lon": -36.4},
            "RO": {"lat": -11.2, "lon": -62.8}, "RR": {"lat": 2.1, "lon": -61.4},
            "RS": {"lat": -29.8, "lon": -53.3}, "SC": {"lat": -27.2, "lon": -50.3},
            "SE": {"lat": -10.6, "lon": -37.4}, "SP": {"lat": -22.3, "lon": -49.1},
            "TO": {"lat": -10.2, "lon": -48.3},
        }
        centro = centros_uf.get(uf_selecionada, {"lat": -14.2, "lon": -51.9})

        # Para métricas populacionais no nível de município, usar apenas métricas básicas
        metrica_munic = metrica if metrica in ("casos", "casos_est", "inc") else "casos"

        fig = mapa_coropletico_municipios(
            df=df_mapa_munic,
            geojson=geojson_munic,
            feature_id_key=feature_key_munic,
            metrica=metrica_munic,
            titulo=f"{METRICAS.get(metrica_munic, metrica_munic)} — {info_uf['nome']} ({ano_inicio}–{ano_fim})",
            center=centro,
            zoom=6,
            log_scale=log_scale,
        )
        st_folium(fig, use_container_width=True, height=600, returned_objects=[])
    except Exception as e:
        st.error(f"Erro ao renderizar mapa de municípios: {e}")

    # Tabela dos municípios
    with st.expander("📋 Ver dados dos municípios", expanded=False):
        cols_munic = [c for c in [
            "nome", "geocode", "casos", "casos_est", "inc", "nivel",
        ] if c in df_mapa_munic.columns]
        if cols_munic:
            df_munic_show = df_mapa_munic[cols_munic].sort_values(
                "casos" if "casos" in cols_munic else cols_munic[0],
                ascending=False,
            )
            st.dataframe(
                df_munic_show,
                column_config={
                    "nome": "Município",
                    "geocode": "Geocode",
                    "casos": st.column_config.NumberColumn("Casos", format="%d"),
                    "casos_est": st.column_config.NumberColumn("Casos Est.", format="%d"),
                    "inc": st.column_config.NumberColumn("Incidência", format="%.2f"),
                    "nivel": st.column_config.NumberColumn("Nível", format="%d"),
                },
                hide_index=True,
                use_container_width=True,
            )
            csv_munic = df_munic_show.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Baixar dados dos municípios (CSV)",
                data=csv_munic,
                file_name=f"{_prefixo_doenca}_{uf_selecionada}_municipios_{ano_inicio}_{ano_fim}.csv",
                mime="text/csv",
                key="dl_mapa_munic",
            )
