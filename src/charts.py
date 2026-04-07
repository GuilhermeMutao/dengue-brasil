"""
Módulo de criação de gráficos Plotly para o Dashboard Arboviroses Brasil.

Cada função retorna um objeto plotly.graph_objects.Figure pronto
para ser exibido via st.plotly_chart().
Mapas coropléticos usam Folium (retornam folium.Map).
"""

from __future__ import annotations

from typing import Optional

import branca.colormap as cm
import folium
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
# Mapas coropléticos (Folium)
# =====================================================================

def mapa_coropletico_estados(
    df: pd.DataFrame,
    geojson: dict,
    feature_id_key: str = "properties.codarea",
    metrica: str = "casos",
    titulo: str = "Casos por Estado",
    log_scale: bool = False,
) -> folium.Map:
    """Cria mapa coroplético dos estados brasileiros com Folium.

    Retorna um objeto folium.Map para exibição via st_folium.
    """
    m = folium.Map(
        location=[-14.2, -51.9],
        zoom_start=4,
        tiles="CartoDB positron",
        control_scale=True,
    )

    if df.empty or "codarea" not in df.columns:
        return m

    plot_df = df.copy()

    # Fallback se a métrica não existir
    if metrica not in plot_df.columns:
        metrica = "casos" if "casos" in plot_df.columns else plot_df.select_dtypes(include="number").columns[0]

    label_metrica = METRICAS.get(metrica, metrica.title())

    # Escala logarítmica
    col_cor = metrica
    if log_scale and metrica in plot_df.columns:
        plot_df["_log_metrica"] = np.log1p(plot_df[metrica].fillna(0))
        col_cor = "_log_metrica"

    # Colormap
    vmin = float(plot_df[col_cor].min()) if not plot_df[col_cor].isna().all() else 0
    vmax = float(plot_df[col_cor].max()) if not plot_df[col_cor].isna().all() else 1
    if vmin == vmax:
        vmax = vmin + 1

    colormap = cm.LinearColormap(
        colors=["#FFFFB2", "#FED976", "#FEB24C", "#FD8D3C", "#FC4E2A", "#E31A1C", "#B10026"],
        vmin=vmin,
        vmax=vmax,
        caption=label_metrica + (" (log)" if log_scale else ""),
    )

    # Indexar dados por codarea
    dados_por_codarea = {}
    for _, row in plot_df.iterrows():
        dados_por_codarea[str(row["codarea"])] = row

    def style_function(feature):
        codarea = str(feature["properties"].get("codarea", ""))
        row = dados_por_codarea.get(codarea)
        if row is not None and pd.notna(row.get(col_cor)):
            valor = float(row[col_cor])
            cor = colormap(valor)
        else:
            cor = "#cccccc"
        return {
            "fillColor": cor,
            "color": "#333333",
            "weight": 1,
            "fillOpacity": 0.7,
        }

    def highlight_function(feature):
        return {
            "weight": 3,
            "color": "#000000",
            "fillOpacity": 0.85,
        }

    # Construir tooltip fields
    tooltip_fields = ["codarea"]
    tooltip_aliases = ["Código:"]
    for col, alias in [
        ("sigla_uf", "UF:"), ("nome_uf", "Estado:"), ("casos", "Casos:"),
        ("casos_est", "Casos Est.:"), ("casos_por_100k", "Casos/100k:"),
        ("inc", "Incidência:"), ("nivel", "Nível Alerta:"),
    ]:
        if col in plot_df.columns:
            tooltip_fields.append(col)
            tooltip_aliases.append(alias)

    # Injetar dados no GeoJSON para tooltip
    geojson_enriquecido = _enriquecer_geojson(geojson, plot_df, tooltip_fields)

    folium.GeoJson(
        geojson_enriquecido,
        name=titulo,
        style_function=style_function,
        highlight_function=highlight_function,
        tooltip=folium.GeoJsonTooltip(
            fields=tooltip_fields,
            aliases=tooltip_aliases,
            localize=True,
            sticky=True,
            style="font-size: 13px;",
        ),
    ).add_to(m)

    colormap.add_to(m)
    m.fit_bounds(m.get_bounds())

    return m


def _enriquecer_geojson(
    geojson: dict,
    df: pd.DataFrame,
    campos: list[str],
) -> dict:
    """Injeta dados do DataFrame nas properties do GeoJSON para tooltips."""
    import copy
    geo = copy.deepcopy(geojson)
    dados_map = {}
    for _, row in df.iterrows():
        dados_map[str(row.get("codarea", ""))] = row

    for feature in geo.get("features", []):
        codarea = str(feature["properties"].get("codarea", ""))
        row = dados_map.get(codarea)
        for campo in campos:
            if campo == "codarea":
                continue
            if row is not None and campo in row.index:
                val = row[campo]
                if isinstance(val, (np.integer, np.int64)):
                    val = int(val)
                elif isinstance(val, (np.floating, np.float64)):
                    val = round(float(val), 2)
                elif pd.isna(val):
                    val = "—"
                feature["properties"][campo] = val
            else:
                feature["properties"][campo] = "—"

    return geo


def mapa_coropletico_municipios(
    df: pd.DataFrame,
    geojson: dict,
    feature_id_key: str = "properties.codarea",
    metrica: str = "casos",
    titulo: str = "Casos por Município",
    center: Optional[dict] = None,
    zoom: int = 6,
    log_scale: bool = False,
) -> folium.Map:
    """Cria mapa coroplético de municípios com Folium.

    Retorna um objeto folium.Map para exibição via st_folium.
    """
    if center is None:
        center = {"lat": -14.2, "lon": -51.9}

    m = folium.Map(
        location=[center["lat"], center["lon"]],
        zoom_start=zoom,
        tiles="CartoDB positron",
        control_scale=True,
    )

    if df.empty or "codarea" not in df.columns:
        return m

    label_metrica = METRICAS.get(metrica, metrica.title())
    plot_df = df.copy()

    col_cor = metrica
    if log_scale and metrica in plot_df.columns:
        plot_df["_log_metrica"] = np.log1p(plot_df[metrica].fillna(0))
        col_cor = "_log_metrica"

    vmin = float(plot_df[col_cor].min()) if not plot_df[col_cor].isna().all() else 0
    vmax = float(plot_df[col_cor].max()) if not plot_df[col_cor].isna().all() else 1
    if vmin == vmax:
        vmax = vmin + 1

    colormap = cm.LinearColormap(
        colors=["#FFFFB2", "#FED976", "#FEB24C", "#FD8D3C", "#FC4E2A", "#E31A1C", "#B10026"],
        vmin=vmin,
        vmax=vmax,
        caption=label_metrica + (" (log)" if log_scale else ""),
    )

    dados_por_codarea = {}
    for _, row in plot_df.iterrows():
        dados_por_codarea[str(row["codarea"])] = row

    def style_function(feature):
        codarea = str(feature["properties"].get("codarea", ""))
        row = dados_por_codarea.get(codarea)
        if row is not None and pd.notna(row.get(col_cor)):
            cor = colormap(float(row[col_cor]))
        else:
            cor = "#cccccc"
        return {
            "fillColor": cor,
            "color": "#666666",
            "weight": 0.5,
            "fillOpacity": 0.7,
        }

    def highlight_function(feature):
        return {"weight": 2, "color": "#000000", "fillOpacity": 0.85}

    tooltip_fields = ["codarea"]
    tooltip_aliases = ["Geocode:"]
    for col, alias in [
        ("nome", "Município:"), ("casos", "Casos:"),
        ("casos_est", "Casos Est.:"), ("inc", "Incidência:"),
        ("nivel", "Nível Alerta:"),
    ]:
        if col in plot_df.columns:
            tooltip_fields.append(col)
            tooltip_aliases.append(alias)

    geojson_enriquecido = _enriquecer_geojson(geojson, plot_df, tooltip_fields)

    folium.GeoJson(
        geojson_enriquecido,
        name=titulo,
        style_function=style_function,
        highlight_function=highlight_function,
        tooltip=folium.GeoJsonTooltip(
            fields=tooltip_fields,
            aliases=tooltip_aliases,
            localize=True,
            sticky=True,
            style="font-size: 13px;",
        ),
    ).add_to(m)

    colormap.add_to(m)
    return m


# =====================================================================
# Séries temporais
# =====================================================================

def serie_temporal(
    df: pd.DataFrame,
    coluna_y: str = "casos",
    coluna_grupo: Optional[str] = None,
    titulo: str = "Evolução Temporal dos Casos",
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
        tickformat="%d/%m/%Y" if coluna_x == "data" else None,
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
    """Gráfico analítico com casos notificados, estimados e ajuste."""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Sem dados disponíveis", showarrow=False, font=dict(size=20))
        return _aplicar_layout(fig, titulo)

    coluna_x = "data" if "data" in df.columns else "se"
    df_sorted = df.sort_values(coluna_x).copy()

    for col in [
        "casos",
        "casos_est",
        "casos_est_min",
        "casos_est_max",
        "diferenca_est_notif",
        "pct_ajuste_estimativa",
    ]:
        if col in df_sorted.columns:
            df_sorted[col] = pd.to_numeric(df_sorted[col], errors="coerce")

    if (
        "diferenca_est_notif" not in df_sorted.columns
        and "casos" in df_sorted.columns
        and "casos_est" in df_sorted.columns
    ):
        df_sorted["diferenca_est_notif"] = df_sorted["casos_est"] - df_sorted["casos"]

    if (
        "pct_ajuste_estimativa" not in df_sorted.columns
        and "diferenca_est_notif" in df_sorted.columns
        and "casos" in df_sorted.columns
    ):
        df_sorted["pct_ajuste_estimativa"] = 0.0
        casos_validos = df_sorted["casos"] > 0
        df_sorted.loc[casos_validos, "pct_ajuste_estimativa"] = (
            df_sorted.loc[casos_validos, "diferenca_est_notif"]
            / df_sorted.loc[casos_validos, "casos"]
        ) * 100

    hover_df = pd.DataFrame(index=df_sorted.index)
    hover_df["se"] = df_sorted["se"] if "se" in df_sorted.columns else df_sorted[coluna_x]
    hover_df["notificados"] = df_sorted["casos"] if "casos" in df_sorted.columns else np.nan
    hover_df["estimados"] = df_sorted["casos_est"] if "casos_est" in df_sorted.columns else np.nan
    hover_df["ajuste"] = df_sorted["diferenca_est_notif"] if "diferenca_est_notif" in df_sorted.columns else np.nan
    hover_df["ajuste_pct"] = df_sorted["pct_ajuste_estimativa"] if "pct_ajuste_estimativa" in df_sorted.columns else np.nan
    hover_df["limite_min"] = df_sorted["casos_est_min"] if "casos_est_min" in df_sorted.columns else np.nan
    hover_df["limite_max"] = df_sorted["casos_est_max"] if "casos_est_max" in df_sorted.columns else np.nan
    customdata = hover_df.to_numpy()

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.72, 0.28],
        vertical_spacing=0.08,
        subplot_titles=(
            "Casos por semana epidemiológica",
            "Ajuste da estimativa (estimados - notificados)",
        ),
    )

    # Área de incerteza (se disponível)
    if "casos_est_min" in df_sorted.columns and "casos_est_max" in df_sorted.columns:
        fig.add_trace(
            go.Scatter(
                x=df_sorted[coluna_x],
                y=df_sorted["casos_est_max"],
                mode="lines",
                line=dict(color="rgba(230,57,70,0)", width=0),
                hoverinfo="skip",
                showlegend=False,
                name="Limite Superior",
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=df_sorted[coluna_x],
                y=df_sorted["casos_est_min"],
                mode="lines",
                fill="tonexty",
                fillcolor="rgba(230, 57, 70, 0.15)",
                line=dict(color="rgba(230,57,70,0)", width=0),
                hoverinfo="skip",
                showlegend=True,
                name="Intervalo de Incerteza",
            ),
            row=1,
            col=1,
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
                customdata=customdata,
                hovertemplate=(
                    "SE: %{customdata[0]}<br>"
                    "Notificados: %{y:,.0f}<br>"
                    "Estimados: %{customdata[2]:,.0f}<br>"
                    "Ajuste: %{customdata[3]:+,.0f} (%{customdata[4]:+.1f}%)"
                    "<extra></extra>"
                ),
            ),
            row=1,
            col=1,
        )

    # Casos estimados por último para não ficar escondido sob a linha azul.
    if "casos_est" in df_sorted.columns:
        fig.add_trace(
            go.Scatter(
                x=df_sorted[coluna_x],
                y=df_sorted["casos_est"],
                mode="lines",
                name="Casos Estimados",
                line=dict(color=COR_PRIMARIA, width=3, dash="dash"),
                customdata=customdata,
                hovertemplate=(
                    "SE: %{customdata[0]}<br>"
                    "Estimados: %{y:,.0f}<br>"
                    "Notificados: %{customdata[1]:,.0f}<br>"
                    "Ajuste: %{customdata[3]:+,.0f} (%{customdata[4]:+.1f}%)<br>"
                    "Intervalo: %{customdata[5]:,.0f} - %{customdata[6]:,.0f}"
                    "<extra></extra>"
                ),
            ),
            row=1,
            col=1,
        )

    if "diferenca_est_notif" in df_sorted.columns:
        cores_barra = np.where(
            df_sorted["diferenca_est_notif"] >= 0,
            "rgba(230, 57, 70, 0.75)",
            "rgba(69, 123, 157, 0.75)",
        )
        fig.add_trace(
            go.Bar(
                x=df_sorted[coluna_x],
                y=df_sorted["diferenca_est_notif"],
                name="Diferença Estimada - Notificada",
                marker_color=cores_barra,
                customdata=customdata,
                hovertemplate=(
                    "SE: %{customdata[0]}<br>"
                    "Diferença: %{y:+,.0f}<br>"
                    "Ajuste: %{customdata[4]:+.1f}%"
                    "<extra></extra>"
                ),
            ),
            row=2,
            col=1,
        )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(0,0,0,0.05)",
        tickformat="%d/%m/%Y" if coluna_x == "data" else None,
        row=1,
        col=1,
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(0,0,0,0.05)",
        tickformat="%d/%m/%Y" if coluna_x == "data" else None,
        row=2,
        col=1,
    )
    fig.update_yaxes(
        title_text="Casos",
        showgrid=True,
        gridcolor="rgba(0,0,0,0.05)",
        row=1,
        col=1,
    )
    fig.update_yaxes(
        title_text="Ajuste",
        showgrid=True,
        zeroline=True,
        zerolinecolor="rgba(0,0,0,0.35)",
        gridcolor="rgba(0,0,0,0.05)",
        row=2,
        col=1,
    )
    fig.update_layout(hovermode="x unified", height=650)

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
    titulo: str = "Casos por Região",
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
    escala: str = "absoluta",
    percentil_clip: float = 95.0,
) -> go.Figure:
    """Heatmap com eixo X = semana epidemiológica e eixo Y = ano.

    Requer colunas 'ano' e 'semana' (usar extrair_ano_semana antes).
    A escala pode realçar padrões sazonais quando anos epidêmicos dominam a cor.
    """
    if df.empty or "ano" not in df.columns or "semana" not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="Sem dados disponíveis", showarrow=False, font=dict(size=20))
        return _aplicar_layout(fig, titulo)

    if coluna_valor not in df.columns:
        fig = go.Figure()
        fig.add_annotation(
            text=f"Coluna '{coluna_valor}' não disponível",
            showarrow=False,
            font=dict(size=20),
        )
        return _aplicar_layout(fig, titulo)

    label_valor = METRICAS.get(coluna_valor, coluna_valor.title())

    pivot = df.pivot_table(
        values=coluna_valor,
        index="ano",
        columns="semana",
        aggfunc="sum",
        fill_value=0,
    )
    pivot = pivot.sort_index().sort_index(axis=1).astype(float)

    valores = pivot.to_numpy(dtype=float)
    valores_validos = valores[np.isfinite(valores)]
    valores_positivos = valores_validos[valores_validos > 0]
    referencia_percentil = valores_positivos if valores_positivos.size else valores_validos

    escala = escala if escala in {"absoluta", "percentil_95", "log", "relativa_ano"} else "absoluta"
    pivot_visual = pivot.copy()
    label_cor = label_valor
    label_visual = label_valor
    hover_extra = ""
    zmin = None
    zmax = None

    if escala == "percentil_95" and referencia_percentil.size:
        limite = float(np.nanpercentile(referencia_percentil, percentil_clip))
        pivot_visual = pivot.clip(upper=limite)
        label_cor = f"{label_valor} (cor limitada no P{percentil_clip:g})"
        label_visual = "Valor usado na cor"
        hover_extra = f"<br>Limite da escala: {limite:,.0f}"
    elif escala == "log":
        pivot_visual = np.log10(pivot + 1)
        label_cor = f"{label_valor} (log10)"
        label_visual = "log10(valor + 1)"
        hover_extra = "<br>Escala logarítmica para reduzir efeito de picos extremos"
    elif escala == "relativa_ano":
        max_por_ano = pivot.max(axis=1).replace(0, np.nan)
        pivot_visual = pivot.div(max_por_ano, axis=0).fillna(0) * 100
        label_cor = "% do Pico do Ano"
        label_visual = "% do pico anual"
        hover_extra = "<br>Escala relativa ao maior valor do próprio ano"
        zmin = 0
        zmax = 100

    fmt_original = ",.0f" if coluna_valor in {"casos", "casos_est", "casos_est_min", "casos_est_max"} else ",.2f"
    fmt_visual = ".1f" if escala == "relativa_ano" else ".2f"
    if escala in {"absoluta", "percentil_95"} and coluna_valor in {"casos", "casos_est", "casos_est_min", "casos_est_max"}:
        fmt_visual = ",.0f"

    hovertemplate = (
        "Ano: %{y}<br>"
        "Semana Epidemiológica: %{x}<br>"
        f"{label_valor}: %{{customdata[0]:{fmt_original}}}"
    )
    if escala != "absoluta":
        hovertemplate += f"<br>{label_visual}: %{{z:{fmt_visual}}}{hover_extra}"
    hovertemplate += "<extra></extra>"

    fig = go.Figure(
        data=go.Heatmap(
            z=pivot_visual.to_numpy(dtype=float),
            x=pivot_visual.columns.tolist(),
            y=pivot_visual.index.tolist(),
            customdata=np.dstack([pivot.to_numpy(dtype=float)]),
            colorscale=ESCALA_CALOR,
            zmin=zmin,
            zmax=zmax,
            colorbar=dict(title=dict(text=label_cor, font=dict(size=12))),
            hovertemplate=hovertemplate,
        )
    )

    fig.update_xaxes(title_text="Semana Epidemiológica")
    fig.update_yaxes(title_text="Ano", type="category")

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
        xaxis=dict(tickformat="%d/%m/%Y") if coluna_x == "data" else {},
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
