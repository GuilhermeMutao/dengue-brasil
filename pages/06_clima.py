"""
Página: Análise Climática — Correlação entre arboviroses e variáveis ambientais.
"""

import streamlit as st
import pandas as pd
import numpy as np

from src.api_infodengue import (
    buscar_dados_brasil_top_municipios,
    agregar_nacional_por_semana,
)
from src.data_processing import (
    limpar_dados,
    filtrar_por_periodo,
    extrair_ano_semana,
)
from src.charts import grafico_clima_dual_axis, heatmap_temporal, scatter_correlacao
from src.constants import (
    ANO_MINIMO,
    ANO_MAXIMO,
    ESCALAS_HEATMAP_SAZONAL,
    METRICAS,
    mensagem_sem_dados_doenca,
    obter_nome_doenca,
    obter_prefixo_doenca,
)

# ---------------------------------------------------------------------------
# Sidebar — Filtros
# ---------------------------------------------------------------------------
with st.sidebar:
    st.subheader("⚙️ Filtros Climáticos")

    ano_range = st.slider(
        "Período (anos)",
        min_value=ANO_MINIMO,
        max_value=ANO_MAXIMO,
        value=(2020, ANO_MAXIMO),
        step=1,
        key="clima_periodo",
    )
    ano_inicio, ano_fim = ano_range

    variavel_clima = st.selectbox(
        "Variável climática",
        options=["tmed", "tmin", "tmax", "umid_med", "umid_min", "umid_max"],
        format_func=lambda v: {
            "tmin": "Temperatura Mínima (°C)",
            "tmed": "Temperatura Média (°C)",
            "tmax": "Temperatura Máxima (°C)",
            "umid_min": "Umidade Mínima (%)",
            "umid_med": "Umidade Média (%)",
            "umid_max": "Umidade Máxima (%)",
        }.get(v, v),
        index=0,
        key="clima_variavel",
    )

# ---------------------------------------------------------------------------
# Título
# ---------------------------------------------------------------------------
_doenca = st.session_state.get("doenca", "dengue")
_nome_doenca = obter_nome_doenca(_doenca)
_prefixo_doenca = obter_prefixo_doenca(_doenca)

st.title("🌡️ Análise Climática")
st.markdown(
    "Explore a relação entre variáveis ambientais (temperatura e umidade) e a "
    f"incidência de **{_nome_doenca}**. Os dados climáticos são fornecidos pela API "
    "InfoDengue para os municípios consultados e ajudam a contextualizar padrões "
    "sazonais, sem implicar causalidade."
)
st.divider()

# ---------------------------------------------------------------------------
# Carregar dados
# ---------------------------------------------------------------------------
with st.spinner("Carregando dados nacionais…"):
    df_bruto = buscar_dados_brasil_top_municipios(ey_start=ano_inicio, ey_end=ano_fim, disease=_doenca)

if df_bruto.empty:
    st.error(mensagem_sem_dados_doenca(_doenca))
    st.stop()

df = limpar_dados(df_bruto)
df = filtrar_por_periodo(df, ano_inicio, ano_fim)
df_nacional = agregar_nacional_por_semana(df)

# Verificar disponibilidade de dados climáticos
colunas_clima = ["tmin", "tmed", "tmax", "umid_min", "umid_med", "umid_max"]
clima_disponivel = [c for c in colunas_clima if c in df_nacional.columns and df_nacional[c].notna().any()]

if not clima_disponivel:
    st.warning(
        "⚠️ Dados climáticos não disponíveis para o período selecionado. "
        "A API InfoDengue pode não incluir variáveis ambientais para todos os períodos."
    )
    st.stop()

# ---------------------------------------------------------------------------
# KPIs de correlação
# ---------------------------------------------------------------------------
st.subheader("📊 Coeficientes de Correlação (Pearson)")

cols_kpi = st.columns(len(clima_disponivel))
for i, col_clima in enumerate(clima_disponivel):
    with cols_kpi[i]:
        valid = df_nacional[["casos", col_clima]].dropna()
        if len(valid) > 2:
            corr = valid["casos"].corr(valid[col_clima])
            label_map = {
                "tmin": "Temp. Mín.", "tmed": "Temp. Méd.", "tmax": "Temp. Máx.",
                "umid_min": "Umid. Mín.", "umid_med": "Umid. Méd.", "umid_max": "Umid. Máx.",
            }
            # Interpretar força
            abs_corr = abs(corr)
            if abs_corr >= 0.7:
                forca = "Forte"
            elif abs_corr >= 0.4:
                forca = "Moderada"
            else:
                forca = "Fraca"
            st.metric(
                label=f"r ({label_map.get(col_clima, col_clima)})",
                value=f"{corr:.3f}",
                delta=forca,
                delta_color="off",
            )
        else:
            st.metric(label=col_clima, value="N/D")

st.divider()

# ---------------------------------------------------------------------------
# Tabs de visualização
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Evolução Temporal",
    "🔗 Scatter — Correlação",
    "🌡️ Sazonalidade Climática",
    "📋 Dados Brutos",
])

# -- Tab 1: Dual-axis temporal
with tab1:
    label_var = {
        "tmin": "Temperatura Mínima", "tmed": "Temperatura Média", "tmax": "Temperatura Máxima",
        "umid_min": "Umidade Mínima", "umid_med": "Umidade Média", "umid_max": "Umidade Máxima",
    }.get(variavel_clima, variavel_clima)

    fig_dual = grafico_clima_dual_axis(
        df_nacional,
        coluna_casos="casos",
        coluna_temp=variavel_clima,
        titulo=f"Casos de {_nome_doenca} × {label_var} ({ano_inicio}–{ano_fim})",
    )
    st.plotly_chart(fig_dual, use_container_width=True)

    st.info(
        "💡 **Interpretação**: Observe se os picos de casos acompanham picos de "
        "temperatura ou umidade (correlação positiva) ou se ocorrem em momentos "
        "opostos (correlação negativa). Em arboviroses transmitidas pelo Aedes, "
        "picos de casos costumam se concentrar em períodos quentes e úmidos, mas "
        "a sazonalidade deve ser analisada por doença, localidade e ano."
    )

# -- Tab 2: Scatter com tendência
with tab2:
    col_scatter1, col_scatter2 = st.columns(2)

    with col_scatter1:
        fig_scatter_temp = scatter_correlacao(
            df_nacional,
            coluna_x=variavel_clima,
            coluna_y="casos",
            titulo=f"Casos × {label_var}",
        )
        st.plotly_chart(fig_scatter_temp, use_container_width=True)

    with col_scatter2:
        # Segundo scatter com outra variável para comparação
        outra_var = "umid_med" if variavel_clima.startswith("t") else "tmed"
        if outra_var in clima_disponivel:
            label_outra = {
                "tmed": "Temperatura Média", "umid_med": "Umidade Média",
            }.get(outra_var, outra_var)
            fig_scatter2 = scatter_correlacao(
                df_nacional,
                coluna_x=outra_var,
                coluna_y="casos",
                titulo=f"Casos × {label_outra}",
            )
            st.plotly_chart(fig_scatter2, use_container_width=True)

    st.info(
        "💡 **Linha de tendência**: A reta (OLS) indica a direção geral da relação. "
        "Uma inclinação positiva sugere que valores mais altos da variável climática "
        f"estão associados a mais casos de {_nome_doenca} no recorte analisado."
    )

# -- Tab 3: Heatmap sazonalidade climática
with tab3:
    df_heat = extrair_ano_semana(df_nacional)
    if "ano" in df_heat.columns and "semana" in df_heat.columns and variavel_clima in df_heat.columns:
        import plotly.express as px
        escala_heat_casos = st.radio(
            "Escala de cores para o heatmap de casos",
            options=list(ESCALAS_HEATMAP_SAZONAL.keys()),
            index=list(ESCALAS_HEATMAP_SAZONAL.keys()).index("relativa_ano"),
            format_func=lambda e: ESCALAS_HEATMAP_SAZONAL[e],
            horizontal=True,
            key="clima_heatmap_casos_escala",
            help=(
                "Use a escala relativa para comparar sazonalidade dos casos entre anos; "
                "use a absoluta para comparar volume real."
            ),
        )
        pivot_clima = df_heat.pivot_table(
            values=variavel_clima, index="ano", columns="semana", aggfunc="mean",
        )
        fig_heat_clima = px.imshow(
            pivot_clima,
            labels=dict(x="Semana Epidemiológica", y="Ano", color=label_var),
            color_continuous_scale="RdYlBu_r" if variavel_clima.startswith("t") else "YlGnBu",
            aspect="auto",
        )
        fig_heat_clima.update_layout(
            title=dict(text=f"Sazonalidade — {label_var} por Semana e Ano", font=dict(size=18)),
            height=400,
        )
        st.plotly_chart(fig_heat_clima, use_container_width=True)

        # Heatmap de casos para comparação lado-a-lado
        fig_heat_casos = heatmap_temporal(
            df_heat,
            coluna_valor="casos",
            titulo=f"Sazonalidade — Casos de {_nome_doenca} por Semana e Ano",
            escala=escala_heat_casos,
        )
        st.plotly_chart(fig_heat_casos, use_container_width=True)

        st.info(
            "💡 **Compare os dois mapas de calor**: Observe se as regiões mais "
            "quentes/úmidas (tonalidades intensas no mapa superior) coincidem "
            "com os maiores volumes de casos (tonalidades intensas no mapa inferior). "
            "Se 2024 dominar a escala, use a leitura relativa ou logarítmica."
        )
    else:
        st.warning("Dados insuficientes para o heatmap sazonal.")

# -- Tab 4: Dados brutos
with tab4:
    cols_exibir = ["se", "data", "casos", "casos_est"] + [c for c in clima_disponivel]
    cols_exibir = [c for c in cols_exibir if c in df_nacional.columns]

    st.dataframe(
        df_nacional[cols_exibir].sort_values("se", ascending=False),
        column_config={
            "casos": st.column_config.NumberColumn("Casos", format="%d"),
            "casos_est": st.column_config.NumberColumn("Estimados", format="%d"),
            "tmin": st.column_config.NumberColumn("Temp. Mín. (°C)", format="%.1f"),
            "tmed": st.column_config.NumberColumn("Temp. Méd. (°C)", format="%.1f"),
            "tmax": st.column_config.NumberColumn("Temp. Máx. (°C)", format="%.1f"),
            "umid_min": st.column_config.NumberColumn("Umid. Mín. (%)", format="%.1f"),
            "umid_med": st.column_config.NumberColumn("Umid. Méd. (%)", format="%.1f"),
            "umid_max": st.column_config.NumberColumn("Umid. Máx. (%)", format="%.1f"),
        },
        hide_index=True,
        use_container_width=True,
    )

    # Botão de download
    csv = df_nacional[cols_exibir].to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Baixar dados climáticos (CSV)",
        data=csv,
        file_name=f"{_prefixo_doenca}_clima_{ano_inicio}_{ano_fim}.csv",
        mime="text/csv",
        key="download_clima",
    )
