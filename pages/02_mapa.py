"""
Página: Mapa Interativo — Choropleth de estados e municípios.
"""

import streamlit as st
import pandas as pd

from src.api_infodengue import (
    buscar_dados_brasil_capitais,
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
    adicionar_info_uf,
    preparar_dados_mapa_estados,
    preparar_dados_mapa_municipios,
)
from src.charts import mapa_coropletico_estados, mapa_coropletico_municipios
from src.constants import (
    ANO_MINIMO,
    ANO_MAXIMO,
    ESTADOS,
    LISTA_UFS,
    METRICAS,
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

    # Métrica
    metricas_disponiveis = ["casos", "casos_est", "inc"]
    metrica = st.selectbox(
        "Métrica para colorir o mapa",
        options=metricas_disponiveis,
        format_func=lambda m: METRICAS.get(m, m),
        index=0,
        key="mapa_metrica",
    )

# ---------------------------------------------------------------------------
# Título
# ---------------------------------------------------------------------------
st.title("🗺️ Mapa Interativo")
st.markdown(
    "Explore a distribuição geográfica da dengue. "
    "Selecione **Brasil** para visão por estados ou um **estado específico** "
    "para ver os municípios."
)
st.divider()

# ---------------------------------------------------------------------------
# Nível Brasil (estados)
# ---------------------------------------------------------------------------
if nivel_geo == "Brasil (Estados)":
    with st.spinner("Carregando dados nacionais…"):
        df_bruto = buscar_dados_brasil_capitais(ey_start=ano_inicio, ey_end=ano_fim)

    if df_bruto.empty:
        st.error("⚠️ Não foi possível obter dados. Tente novamente.")
        st.stop()

    df = limpar_dados(df_bruto)
    df = adicionar_info_uf(df)
    df = filtrar_por_periodo(df, ano_inicio, ano_fim)
    df_resumo = resumo_por_uf(df)
    df_mapa = preparar_dados_mapa_estados(df_resumo)

    try:
        geojson = carregar_geojson_estados()
        feature_key = obter_feature_id_key_estados(geojson)

        fig = mapa_coropletico_estados(
            df=df_mapa,
            geojson=geojson,
            feature_id_key=feature_key,
            metrica=metrica,
            titulo=f"{METRICAS.get(metrica, metrica)} por Estado ({ano_inicio}–{ano_fim})",
        )
        st.plotly_chart(fig, use_container_width=True, key="mapa_estados")
    except Exception as e:
        st.error(f"Erro ao renderizar mapa: {e}")

    # Tabela resumo abaixo do mapa
    with st.expander("📋 Ver dados em tabela", expanded=False):
        if not df_resumo.empty:
            cols = [c for c in ["sigla_uf", "nome_uf", "regiao", "casos", "casos_est", "inc"] if c in df_resumo.columns]
            st.dataframe(
                df_resumo[cols].sort_values("casos", ascending=False),
                hide_index=True,
                use_container_width=True,
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
        )

    if df_munic_dados.empty:
        st.warning("Nenhum dado retornado para os municípios consultados.")
        st.stop()

    df_munic_dados = limpar_dados(df_munic_dados)
    df_munic_dados = filtrar_por_periodo(df_munic_dados, ano_inicio, ano_fim)
    df_mapa_munic = preparar_dados_mapa_municipios(df_munic_dados)

    # Merge nomes dos municípios
    if "geocode" in df_mapa_munic.columns:
        nomes = df_municipios[["geocode", "nome"]].copy()
        nomes["geocode"] = nomes["geocode"].astype(df_mapa_munic["geocode"].dtype)
        df_mapa_munic = df_mapa_munic.merge(nomes, on="geocode", how="left")

    try:
        geojson_munic = carregar_geojson_municipios(info_uf["cod_uf"])
        feature_key_munic = obter_feature_id_key_municipios(geojson_munic)

        # Estimar centro do mapa
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

        fig = mapa_coropletico_municipios(
            df=df_mapa_munic,
            geojson=geojson_munic,
            feature_id_key=feature_key_munic,
            metrica=metrica,
            titulo=f"{METRICAS.get(metrica, metrica)} — {info_uf['nome']} ({ano_inicio}–{ano_fim})",
            center=centro,
            zoom=5,
        )
        st.plotly_chart(fig, use_container_width=True, key="mapa_munic")
    except Exception as e:
        st.error(f"Erro ao renderizar mapa de municípios: {e}")

    # Tabela dos municípios
    with st.expander("📋 Ver dados dos municípios", expanded=False):
        cols_munic = [c for c in ["nome", "geocode", "casos", "casos_est", "inc", "nivel"] if c in df_mapa_munic.columns]
        if cols_munic:
            st.dataframe(
                df_mapa_munic[cols_munic].sort_values(
                    "casos" if "casos" in cols_munic else cols_munic[0],
                    ascending=False,
                ),
                hide_index=True,
                use_container_width=True,
            )
