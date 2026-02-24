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
    adicionar_info_uf,
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
from src.constants import ANO_MINIMO, ANO_MAXIMO, LABELS_NIVEL_ALERTA, CORES_NIVEL_ALERTA

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

# ---------------------------------------------------------------------------
# Título
# ---------------------------------------------------------------------------
st.title("🦟 Visão Geral — Dengue no Brasil")
st.markdown(
    "Panorama nacional com base nos dados das **27 capitais estaduais** "
    "(*proxy* para visão por estado). Fonte: [InfoDengue](https://info.dengue.mat.br)."
)
st.divider()

# ---------------------------------------------------------------------------
# Carregar e processar dados
# ---------------------------------------------------------------------------
with st.spinner("Buscando dados das capitais brasileiras…"):
    df_bruto = buscar_dados_brasil_capitais(ey_start=ano_inicio, ey_end=ano_fim)

if df_bruto.empty:
    st.error("⚠️ Não foi possível obter dados da API InfoDengue. Tente novamente mais tarde.")
    st.stop()

# Limpeza e enriquecimento
df = limpar_dados(df_bruto)
df = adicionar_info_uf(df)
df = filtrar_por_periodo(df, ano_inicio, ano_fim)

# Agregações
df_nacional = agregar_nacional_por_semana(df)
df_resumo_uf = resumo_por_uf(df)
kpis = calcular_kpis(df_nacional)

# ---------------------------------------------------------------------------
# Cards KPI
# ---------------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total de Casos (Capitais)",
        value=f"{kpis['total_casos']:,.0f}",
        help="Soma dos casos notificados das 27 capitais no período selecionado.",
    )

with col2:
    st.metric(
        label="Casos Estimados",
        value=f"{kpis['total_casos_est']:,.0f}",
        help="Soma dos casos estimados pelo modelo nowcasting do InfoDengue.",
    )

with col3:
    st.metric(
        label="Última Semana Epi.",
        value=f"{kpis['casos_ultima_semana']:,.0f}",
        delta=f"{kpis['variacao_semanal']:+.1f}%",
        delta_color="inverse",
        help=f"Casos na semana epidemiológica {kpis['ultima_semana']} e variação em relação à semana anterior.",
    )

with col4:
    nivel = kpis["nivel_predominante"]
    cor = CORES_NIVEL_ALERTA.get(nivel, "#999")
    label = LABELS_NIVEL_ALERTA.get(nivel, "—")
    st.metric(
        label="Nível de Alerta Predominante",
        value=label.split("—")[0].strip(),
        help=f"{label}. Baseado na moda do nível de alerta nas 27 capitais.",
    )

st.divider()

# ---------------------------------------------------------------------------
# Mapa coroplético + Barras por região (lado a lado)
# ---------------------------------------------------------------------------
col_mapa, col_barras = st.columns([3, 2])

with col_mapa:
    st.subheader("📍 Mapa de Casos por Estado")
    try:
        geojson = carregar_geojson_estados()
        feature_key = obter_feature_id_key_estados(geojson)
        df_mapa = preparar_dados_mapa_estados(df_resumo_uf)

        fig_mapa = mapa_coropletico_estados(
            df=df_mapa,
            geojson=geojson,
            feature_id_key=feature_key,
            metrica="casos",
            titulo="",
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
# Tabela ranking de estados
# ---------------------------------------------------------------------------
st.subheader("🏆 Ranking de Capitais por Casos Notificados")

if not df_resumo_uf.empty:
    tabela = df_resumo_uf.copy()
    colunas_exibir = ["sigla_uf", "nome_uf", "regiao", "casos", "casos_est"]
    if "inc" in tabela.columns:
        colunas_exibir.append("inc")
    if "nivel" in tabela.columns:
        colunas_exibir.append("nivel")

    colunas_existentes = [c for c in colunas_exibir if c in tabela.columns]
    tabela = tabela[colunas_existentes].sort_values("casos", ascending=False)

    column_config = {
        "sigla_uf": st.column_config.TextColumn("UF", width="small"),
        "nome_uf": st.column_config.TextColumn("Estado", width="medium"),
        "regiao": st.column_config.TextColumn("Região", width="medium"),
        "casos": st.column_config.NumberColumn(
            "Casos Notificados",
            format="%d",
        ),
        "casos_est": st.column_config.NumberColumn(
            "Casos Estimados",
            format="%d",
        ),
        "inc": st.column_config.NumberColumn(
            "Incidência Média",
            format="%.2f",
        ),
        "nivel": st.column_config.NumberColumn(
            "Nível Alerta",
            format="%d",
            help="1=Verde, 2=Amarelo, 3=Laranja, 4=Vermelho",
        ),
    }

    st.dataframe(
        tabela,
        column_config=column_config,
        hide_index=True,
        use_container_width=True,
        height=400,
    )
