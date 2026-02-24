"""
Módulo de criação de gráficos Plotly para o Dashboard Dengue Brasil.

Cada função retorna um objeto plotly.graph_objects.Figure pronto
para ser exibido via st.plotly_chart().
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.constants import (
    CORES_NIVEL_ALERTA,
    COR_DESTAQUE,
    COR_PRIMARIA,
    COR_SECUNDARIA,
    ESCALA_CALOR,
    ESCALA_SEQUENCIAL,
    LABELS_NIVEL_ALERTA,
    METRICAS,
    POPULACAO_ESTADOS,
)

# ---------------------------------------------------------------------------
# Configurações comuns de layout
# ---------------------------------------------------------------------------
_LAYOUT_PADRAO = dict(
    font=dict(family="Inter, sans-serif", size=13),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=20, r=20, t=50, b=20),
    hoverlabel=dict(bgcolor="white", font_size=13),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)


def _aplicar_layout(fig: go.Figure, title: str = "") -> go.Figure:
    """Aplica layout padrão ao gráfico."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color=COR_DESTAQUE)),
        **_LAYOUT_PADRAO,
    )
    return fig


# =====================================================================
# Mapas coropléticos
# =====================================================================

def mapa_coropletico_estados(
    df: pd.DataFrame,
    geojson: dict,
    feature_id_key: str = "properties.codarea",
    metrica: str = "casos",
    titulo: str = "Casos de Dengue por Estado",
    log_scale: bool = False,
) -> go.Figure:
    """Cria mapa coroplético dos estados brasileiros.

    Parâmetros:
        df: DataFrame com colunas 'codarea' (str) e a métrica desejada.
        geojson: GeoJSON dos estados (IBGE Malhas v3).
        feature_id_key: Chave no GeoJSON para matching (ex: 'properties.codarea').
        metrica: Coluna do df a ser colorida.
        titulo: Título do mapa.
        log_scale: Se True, aplica escala logarítmica nas cores.
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Sem dados disponíveis", showarrow=False, font=dict(size=20))
        return _aplicar_layout(fig, titulo)

    label_metrica = METRICAS.get(metrica, metrica.title())

    # Garantir coluna codarea
    if "codarea" not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="Dados sem codarea", showarrow=False)
        return _aplicar_layout(fig, titulo)

    plot_df = df.copy()

    # Fallback se a métrica não existir no DataFrame
    if metrica not in plot_df.columns:
        metrica = "casos" if "casos" in plot_df.columns else plot_df.select_dtypes(include="number").columns[0]
        label_metrica = METRICAS.get(metrica, metrica.title())

    # Escala logarítmica: criar coluna auxiliar para cor
    col_cor = metrica
    if log_scale and metrica in plot_df.columns:
        plot_df["_log_metrica"] = np.log1p(plot_df[metrica].fillna(0))
        col_cor = "_log_metrica"

    # Construir customdata para hover rico
    hover_cols = []
    customdata_cols = []
    for c in ["sigla_uf", "nome_uf", "populacao", "casos", "casos_est",
              "inc", "casos_por_100k", "pct_nacional", "nivel"]:
        if c in plot_df.columns:
            hover_cols.append(c)
            customdata_cols.append(c)

    # Hover name
    hover_name = "sigla_uf" if "sigla_uf" in plot_df.columns else "codarea"

    fig = px.choropleth(
        plot_df,
        geojson=geojson,
        locations="codarea",
        featureidkey=feature_id_key,
        color=col_cor,
        hover_name=hover_name,
        custom_data=customdata_cols if customdata_cols else None,
        color_continuous_scale=ESCALA_CALOR,
        labels={col_cor: label_metrica + (" (log)" if log_scale else "")},
    )

    # Hover template rico
    if customdata_cols:
        ht_parts = ["<b>%{hovertext}</b>"]
        for i, c in enumerate(customdata_cols):
            lbl = METRICAS.get(c, c.replace("_", " ").title())
            if c in ("casos", "casos_est", "populacao"):
                ht_parts.append(f"{lbl}: %{{customdata[{i}]:,.0f}}")
            elif c in ("inc", "casos_por_100k"):
                ht_parts.append(f"{lbl}: %{{customdata[{i}]:.1f}}")
            elif c == "pct_nacional":
                ht_parts.append(f"{lbl}: %{{customdata[{i}]:.2f}}%")
            elif c == "nivel":
                ht_parts.append(f"{lbl}: %{{customdata[{i}]}}")
            elif c in ("sigla_uf", "nome_uf"):
                pass  # já no hovertext
            else:
                ht_parts.append(f"{lbl}: %{{customdata[{i}]}}")
        ht_parts.append("<extra></extra>")
        fig.update_traces(hovertemplate="<br>".join(ht_parts))

    fig.update_geos(
        fitbounds="locations",
        visible=False,
        showframe=False,
        showcoastlines=False,
    )

    fig.update_layout(
        height=600,
        margin=dict(l=0, r=0, t=40, b=0),
        coloraxis_colorbar=dict(
            title=dict(text=label_metrica, font=dict(size=12)),
            thickness=15,
            len=0.7,
        ),
    )

    return _aplicar_layout(fig, titulo)


def mapa_coropletico_municipios(
    df: pd.DataFrame,
    geojson: dict,
    feature_id_key: str = "properties.codarea",
    metrica: str = "casos",
    titulo: str = "Casos de Dengue por Município",
    center: Optional[dict] = None,
    zoom: int = 5,
    log_scale: bool = False,
) -> go.Figure:
    """Cria mapa coroplético de municípios usando Mapbox (open-street-map).

    Parâmetros:
        df: DataFrame com 'codarea' (str) e a métrica.
        geojson: GeoJSON dos municípios da UF.
        feature_id_key: Chave no GeoJSON.
        metrica: Coluna a colorir.
        titulo: Título.
        center: Dict com lat/lon do centro do mapa.
        zoom: Zoom inicial.
        log_scale: Se True, aplica escala logarítmica.
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Sem dados disponíveis", showarrow=False, font=dict(size=20))
        return _aplicar_layout(fig, titulo)

    label_metrica = METRICAS.get(metrica, metrica.title())

    if center is None:
        center = {"lat": -14.2, "lon": -51.9}

    plot_df = df.copy()
    col_cor = metrica
    if log_scale and metrica in plot_df.columns:
        plot_df["_log_metrica"] = np.log1p(plot_df[metrica].fillna(0))
        col_cor = "_log_metrica"

    # Hover name
    hover_name = "nome" if "nome" in plot_df.columns else "codarea"

    fig = px.choropleth_mapbox(
        plot_df,
        geojson=geojson,
        locations="codarea",
        featureidkey=feature_id_key,
        color=col_cor,
        hover_name=hover_name,
        color_continuous_scale=ESCALA_CALOR,
        mapbox_style="open-street-map",
        zoom=zoom,
        center=center,
        opacity=0.7,
        labels={col_cor: label_metrica + (" (log)" if log_scale else "")},
    )

    fig.update_layout(
        margin=dict(l=0, r=0, t=50, b=0),
        coloraxis_colorbar=dict(
            title=dict(text=label_metrica, font=dict(size=12)),
            thickness=15,
            len=0.7,
        ),
    )

    return _aplicar_layout(fig, titulo)


# =====================================================================
# Séries temporais
# =====================================================================

def serie_temporal(
    df: pd.DataFrame,
    coluna_y: str = "casos",
    coluna_grupo: Optional[str] = None,
    titulo: str = "Evolução Temporal dos Casos de Dengue",
) -> go.Figure:
    """Cria gráfico de linha com evolução temporal.

    Se coluna_grupo for definida, cria uma série por grupo (ex: por UF).
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Sem dados disponíveis", showarrow=False, font=dict(size=20))
        return _aplicar_layout(fig, titulo)

    label_y = METRICAS.get(coluna_y, coluna_y.title())

    # Determinar coluna X
    coluna_x = "data" if "data" in df.columns else "se"

    if coluna_grupo and coluna_grupo in df.columns:
        fig = px.line(
            df.sort_values([coluna_grupo, coluna_x]),
            x=coluna_x,
            y=coluna_y,
            color=coluna_grupo,
            labels={coluna_y: label_y, coluna_x: "Data"},
            hover_data=["se"] if "se" in df.columns else None,
        )
    else:
        fig = px.line(
            df.sort_values(coluna_x),
            x=coluna_x,
            y=coluna_y,
            labels={coluna_y: label_y, coluna_x: "Data"},
            hover_data=["se"] if "se" in df.columns else None,
        )
        fig.update_traces(line=dict(color=COR_PRIMARIA, width=2.5))

    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(0,0,0,0.05)",
    )
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(0,0,0,0.05)",
    )

    return _aplicar_layout(fig, titulo)


def serie_temporal_com_estimativa(
    df: pd.DataFrame,
    titulo: str = "Casos Notificados vs. Estimados",
) -> go.Figure:
    """Gráfico de linha com casos reais e banda de estimativa.

    Mostra casos notificados como linha sólida e casos estimados como
    linha tracejada, com banda de confiança se disponível.
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Sem dados disponíveis", showarrow=False, font=dict(size=20))
        return _aplicar_layout(fig, titulo)

    coluna_x = "data" if "data" in df.columns else "se"
    df_sorted = df.sort_values(coluna_x)

    fig = go.Figure()

    # Área de confiança (se disponível)
    if "casos_est_min" in df_sorted.columns and "casos_est_max" in df_sorted.columns:
        fig.add_trace(
            go.Scatter(
                x=pd.concat([df_sorted[coluna_x], df_sorted[coluna_x][::-1]]),
                y=pd.concat([df_sorted["casos_est_max"], df_sorted["casos_est_min"][::-1]]),
                fill="toself",
                fillcolor="rgba(230, 57, 70, 0.15)",
                line=dict(color="rgba(255,255,255,0)"),
                hoverinfo="skip",
                showlegend=True,
                name="Intervalo de Confiança",
            )
        )

    # Casos estimados
    if "casos_est" in df_sorted.columns:
        fig.add_trace(
            go.Scatter(
                x=df_sorted[coluna_x],
                y=df_sorted["casos_est"],
                mode="lines",
                name="Casos Estimados",
                line=dict(color=COR_PRIMARIA, width=2, dash="dash"),
            )
        )

    # Casos notificados
    if "casos" in df_sorted.columns:
        fig.add_trace(
            go.Scatter(
                x=df_sorted[coluna_x],
                y=df_sorted["casos"],
                mode="lines",
                name="Casos Notificados",
                line=dict(color=COR_SECUNDARIA, width=2.5),
            )
        )

    fig.update_xaxes(showgrid=True, gridcolor="rgba(0,0,0,0.05)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(0,0,0,0.05)")

    return _aplicar_layout(fig, titulo)


# =====================================================================
# Gráficos de barras
# =====================================================================

def barras_comparativo(
    df: pd.DataFrame,
    coluna_x: str = "sigla_uf",
    coluna_y: str = "casos",
    titulo: str = "Comparativo de Casos por Estado",
    horizontal: bool = True,
    top_n: Optional[int] = None,
    cor: Optional[str] = None,
) -> go.Figure:
    """Cria gráfico de barras comparativo (horizontal ou vertical).

    Se top_n, mostra apenas os N maiores.
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Sem dados disponíveis", showarrow=False, font=dict(size=20))
        return _aplicar_layout(fig, titulo)

    label_y = METRICAS.get(coluna_y, coluna_y.title())

    plot_df = df.copy()
    if top_n:
        plot_df = plot_df.nlargest(top_n, coluna_y)

    # Ordenar
    plot_df = plot_df.sort_values(coluna_y, ascending=horizontal)

    if horizontal:
        fig = px.bar(
            plot_df,
            x=coluna_y,
            y=coluna_x,
            orientation="h",
            labels={coluna_y: label_y, coluna_x: ""},
            text=coluna_y,
            color=coluna_y if not cor else None,
            color_continuous_scale=ESCALA_CALOR if not cor else None,
        )
    else:
        fig = px.bar(
            plot_df,
            x=coluna_x,
            y=coluna_y,
            labels={coluna_y: label_y, coluna_x: ""},
            text=coluna_y,
            color=coluna_y if not cor else None,
            color_continuous_scale=ESCALA_CALOR if not cor else None,
        )

    if cor:
        fig.update_traces(marker_color=cor)

    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig.update_layout(showlegend=False)

    return _aplicar_layout(fig, titulo)


def barras_agrupadas_regiao(
    df: pd.DataFrame,
    coluna_y: str = "casos",
    titulo: str = "Casos de Dengue por Região",
) -> go.Figure:
    """Barras agrupadas por macrorregião."""
    if df.empty or "regiao" not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="Sem dados disponíveis", showarrow=False, font=dict(size=20))
        return _aplicar_layout(fig, titulo)

    label_y = METRICAS.get(coluna_y, coluna_y.title())

    regiao_df = (
        df.groupby("regiao", as_index=False)[coluna_y]
        .sum()
        .sort_values(coluna_y, ascending=False)
    )

    cores_regiao = {
        "Norte": "#2ECC71",
        "Nordeste": "#E74C3C",
        "Sudeste": "#3498DB",
        "Sul": "#9B59B6",
        "Centro-Oeste": "#F39C12",
    }

    fig = px.bar(
        regiao_df,
        x="regiao",
        y=coluna_y,
        color="regiao",
        color_discrete_map=cores_regiao,
        labels={coluna_y: label_y, "regiao": "Região"},
        text=coluna_y,
    )

    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig.update_layout(showlegend=False)

    return _aplicar_layout(fig, titulo)


# =====================================================================
# Heatmaps
# =====================================================================

def heatmap_temporal(
    df: pd.DataFrame,
    coluna_valor: str = "casos",
    titulo: str = "Mapa de Calor — Casos por Semana e Ano",
) -> go.Figure:
    """Heatmap com eixo X = semana epidemiológica e eixo Y = ano.

    Requer colunas 'ano' e 'semana' (usar extrair_ano_semana antes).
    """
    if df.empty or "ano" not in df.columns or "semana" not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="Sem dados disponíveis", showarrow=False, font=dict(size=20))
        return _aplicar_layout(fig, titulo)

    label_valor = METRICAS.get(coluna_valor, coluna_valor.title())

    pivot = df.pivot_table(
        values=coluna_valor,
        index="ano",
        columns="semana",
        aggfunc="sum",
        fill_value=0,
    )

    fig = px.imshow(
        pivot,
        labels=dict(x="Semana Epidemiológica", y="Ano", color=label_valor),
        color_continuous_scale=ESCALA_CALOR,
        aspect="auto",
    )

    fig.update_layout(
        coloraxis_colorbar=dict(title=dict(text=label_valor, font=dict(size=12))),
    )

    return _aplicar_layout(fig, titulo)


def heatmap_estados(
    df: pd.DataFrame,
    coluna_valor: str = "casos",
    titulo: str = "Mapa de Calor — Casos por Estado e Semana",
) -> go.Figure:
    """Heatmap com eixo X = semana epi e eixo Y = estado."""
    if df.empty or "sigla_uf" not in df.columns or "se" not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="Sem dados disponíveis", showarrow=False, font=dict(size=20))
        return _aplicar_layout(fig, titulo)

    label_valor = METRICAS.get(coluna_valor, coluna_valor.title())

    pivot = df.pivot_table(
        values=coluna_valor,
        index="sigla_uf",
        columns="se",
        aggfunc="sum",
        fill_value=0,
    )

    fig = px.imshow(
        pivot,
        labels=dict(x="Semana Epidemiológica", y="Estado", color=label_valor),
        color_continuous_scale=ESCALA_CALOR,
        aspect="auto",
    )

    fig.update_layout(
        coloraxis_colorbar=dict(title=dict(text=label_valor, font=dict(size=12))),
    )

    return _aplicar_layout(fig, titulo)


# =====================================================================
# Indicadores (KPI / Gauge)
# =====================================================================

def gauge_nivel_alerta(
    nivel: int,
    titulo: str = "Nível de Alerta",
) -> go.Figure:
    """Gauge indicator para o nível de alerta do InfoDengue (1-4)."""
    cor = CORES_NIVEL_ALERTA.get(nivel, "#999999")
    label = LABELS_NIVEL_ALERTA.get(nivel, "Desconhecido")

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=nivel,
            title=dict(text=titulo, font=dict(size=16)),
            number=dict(suffix=f"  ({label})", font=dict(size=20)),
            gauge=dict(
                axis=dict(range=[0, 4], tickvals=[1, 2, 3, 4]),
                bar=dict(color=cor),
                steps=[
                    dict(range=[0, 1], color="#d5f5e3"),
                    dict(range=[1, 2], color="#fcf3cf"),
                    dict(range=[2, 3], color="#fdebd0"),
                    dict(range=[3, 4], color="#fadbd8"),
                ],
                threshold=dict(
                    line=dict(color="black", width=2),
                    thickness=0.75,
                    value=nivel,
                ),
            ),
        )
    )

    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=60, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
    )

    return fig


# =====================================================================
# Gráficos climáticos
# =====================================================================

def grafico_clima_dual_axis(
    df: pd.DataFrame,
    coluna_casos: str = "casos",
    coluna_temp: str = "tmed",
    titulo: str = "Casos × Temperatura Média",
) -> go.Figure:
    """Gráfico de linhas com eixo Y duplo: casos (esquerdo) e temperatura (direito)."""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Sem dados disponíveis", showarrow=False, font=dict(size=20))
        return _aplicar_layout(fig, titulo)

    coluna_x = "data" if "data" in df.columns else "se"
    df_s = df.sort_values(coluna_x)

    fig = go.Figure()

    # Casos
    fig.add_trace(
        go.Scatter(
            x=df_s[coluna_x], y=df_s[coluna_casos],
            name="Casos Notificados", mode="lines",
            line=dict(color=COR_PRIMARIA, width=2),
            yaxis="y",
        )
    )

    # Temperatura / Umidade
    label_clima = {
        "tmin": "Temp. Mínima (°C)", "tmed": "Temp. Média (°C)", "tmax": "Temp. Máxima (°C)",
        "umid_min": "Umid. Mínima (%)", "umid_med": "Umid. Média (%)", "umid_max": "Umid. Máxima (%)",
    }.get(coluna_temp, coluna_temp)

    if coluna_temp in df_s.columns:
        fig.add_trace(
            go.Scatter(
                x=df_s[coluna_x], y=df_s[coluna_temp],
                name=label_clima, mode="lines",
                line=dict(color=COR_SECUNDARIA, width=2, dash="dot"),
                yaxis="y2",
            )
        )

    fig.update_layout(
        yaxis=dict(title="Casos Notificados", side="left", showgrid=True, gridcolor="rgba(0,0,0,0.05)"),
        yaxis2=dict(title=label_clima, side="right", overlaying="y", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )

    return _aplicar_layout(fig, titulo)


def scatter_correlacao(
    df: pd.DataFrame,
    coluna_x: str = "tmed",
    coluna_y: str = "casos",
    titulo: str = "Correlação: Temperatura × Casos",
) -> go.Figure:
    """Scatter plot com linha de tendência (OLS) para análise de correlação."""
    if df.empty or coluna_x not in df.columns or coluna_y not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="Sem dados disponíveis", showarrow=False, font=dict(size=20))
        return _aplicar_layout(fig, titulo)

    label_x_map = {
        "tmin": "Temp. Mínima (°C)", "tmed": "Temp. Média (°C)", "tmax": "Temp. Máxima (°C)",
        "umid_min": "Umid. Mínima (%)", "umid_med": "Umid. Média (%)", "umid_max": "Umid. Máxima (%)",
    }
    label_y = METRICAS.get(coluna_y, coluna_y.title())
    label_x = label_x_map.get(coluna_x, coluna_x)

    fig = px.scatter(
        df.dropna(subset=[coluna_x, coluna_y]),
        x=coluna_x, y=coluna_y,
        trendline="ols",
        labels={coluna_x: label_x, coluna_y: label_y},
        opacity=0.5,
    )
    fig.update_traces(marker=dict(color=COR_PRIMARIA, size=5))

    return _aplicar_layout(fig, titulo)


def serie_curva_epidemica(
    df: pd.DataFrame,
    coluna_valor: str = "casos",
    titulo: str = "Curva Epidêmica — Sobreposição Anual",
) -> go.Figure:
    """Gráfico com sobreposição de curvas anuais (SE 1–52 no eixo X, uma série por ano)."""
    if df.empty or "se" not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="Sem dados disponíveis", showarrow=False, font=dict(size=20))
        return _aplicar_layout(fig, titulo)

    df_t = df.copy()
    se_str = df_t["se"].astype(str)
    df_t["ano"] = se_str.str[:4].astype(int)
    df_t["semana"] = se_str.str[4:].astype(int)

    label_y = METRICAS.get(coluna_valor, coluna_valor.title())

    fig = px.line(
        df_t.sort_values(["ano", "semana"]),
        x="semana", y=coluna_valor, color="ano",
        labels={"semana": "Semana Epidemiológica", coluna_valor: label_y, "ano": "Ano"},
    )
    fig.update_xaxes(dtick=4, range=[1, 52])
    fig.update_layout(hovermode="x unified")
    return _aplicar_layout(fig, titulo)


def indicador_simples(
    valor: float,
    titulo: str = "",
    sufixo: str = "",
    referencia: Optional[float] = None,
) -> go.Figure:
    """Indicador numérico simples com referência opcional."""
    fig = go.Figure(
        go.Indicator(
            mode="number+delta" if referencia is not None else "number",
            value=valor,
            title=dict(text=titulo, font=dict(size=14)),
            number=dict(suffix=sufixo, font=dict(size=28, color=COR_DESTAQUE)),
            delta=dict(
                reference=referencia,
                relative=True,
                valueformat=".1%",
                increasing=dict(color="#E74C3C"),
                decreasing=dict(color="#2ECC71"),
            )
            if referencia is not None
            else None,
        )
    )

    fig.update_layout(
        height=150,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
    )

    return fig
