"""
Testes unitários para o módulo de gráficos.
"""

import pandas as pd
import pytest
import plotly.graph_objects as go
import folium

from src.charts import (
    mapa_coropletico_estados,
    serie_temporal,
    serie_temporal_com_estimativa,
    barras_comparativo,
    barras_agrupadas_regiao,
    heatmap_temporal,
    heatmap_estados,
    gauge_nivel_alerta,
    indicador_simples,
)


@pytest.fixture
def df_estados():
    """DataFrame simulando resumo por estado."""
    return pd.DataFrame({
        "sigla_uf": ["SP", "RJ", "MG"],
        "nome_uf": ["São Paulo", "Rio de Janeiro", "Minas Gerais"],
        "regiao": ["Sudeste", "Sudeste", "Sudeste"],
        "codarea": ["35", "33", "31"],
        "casos": [5000, 3000, 4000],
        "casos_est": [5500, 3300, 4400],
        "inc": [10.5, 8.3, 9.2],
    })


@pytest.fixture
def df_serie():
    """DataFrame simulando série temporal."""
    return pd.DataFrame({
        "se": [202401, 202402, 202403, 202404],
        "data": pd.to_datetime(["2024-01-07", "2024-01-14", "2024-01-21", "2024-01-28"]),
        "casos": [100, 150, 200, 180],
        "casos_est": [110, 160, 210, 190],
        "casos_est_min": [105, 155, 205, 185],
        "casos_est_max": [120, 170, 220, 200],
    })


@pytest.fixture
def df_heatmap():
    """DataFrame com ano e semana para heatmap."""
    return pd.DataFrame({
        "ano": [2023] * 4 + [2024] * 4,
        "semana": [1, 2, 3, 4, 1, 2, 3, 4],
        "casos": [50, 60, 80, 70, 100, 120, 150, 130],
    })


@pytest.fixture
def geojson_fake():
    """GeoJSON fake minimalista."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"codarea": "35"},
                "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
            }
        ],
    }


class TestMapaCoropleticoEstados:
    def test_retorna_folium_map(self, df_estados, geojson_fake):
        fig = mapa_coropletico_estados(df_estados, geojson_fake)
        assert isinstance(fig, folium.Map)

    def test_df_vazio(self, geojson_fake):
        fig = mapa_coropletico_estados(pd.DataFrame(), geojson_fake)
        assert isinstance(fig, folium.Map)


class TestSerieTemporal:
    def test_retorna_figure(self, df_serie):
        fig = serie_temporal(df_serie, coluna_y="casos")
        assert isinstance(fig, go.Figure)

    def test_com_grupo(self, df_serie):
        df = df_serie.copy()
        df["sigla_uf"] = "SP"
        fig = serie_temporal(df, coluna_y="casos", coluna_grupo="sigla_uf")
        assert isinstance(fig, go.Figure)

    def test_df_vazio(self):
        fig = serie_temporal(pd.DataFrame())
        assert isinstance(fig, go.Figure)


class TestSerieTemporalEstimativa:
    def test_retorna_figure(self, df_serie):
        fig = serie_temporal_com_estimativa(df_serie)
        assert isinstance(fig, go.Figure)

    def test_contem_camadas_analiticas(self, df_serie):
        fig = serie_temporal_com_estimativa(df_serie)
        nomes = [trace.name for trace in fig.data]

        assert "Casos Estimados" in nomes
        assert "Casos Notificados" in nomes
        assert "Intervalo de Incerteza" in nomes
        assert "Diferença Estimada - Notificada" in nomes


class TestBarrasComparativo:
    def test_retorna_figure(self, df_estados):
        fig = barras_comparativo(df_estados, coluna_x="sigla_uf", coluna_y="casos")
        assert isinstance(fig, go.Figure)

    def test_top_n(self, df_estados):
        fig = barras_comparativo(df_estados, coluna_x="sigla_uf", coluna_y="casos", top_n=2)
        assert isinstance(fig, go.Figure)


class TestBarrasAgrupadasRegiao:
    def test_retorna_figure(self, df_estados):
        fig = barras_agrupadas_regiao(df_estados)
        assert isinstance(fig, go.Figure)


class TestHeatmapTemporal:
    def test_retorna_figure(self, df_heatmap):
        fig = heatmap_temporal(df_heatmap)
        assert isinstance(fig, go.Figure)

    def test_df_vazio(self):
        fig = heatmap_temporal(pd.DataFrame())
        assert isinstance(fig, go.Figure)


class TestHeatmapEstados:
    def test_retorna_figure(self):
        df = pd.DataFrame({
            "sigla_uf": ["SP"] * 3 + ["RJ"] * 3,
            "se": [202401, 202402, 202403] * 2,
            "casos": [100, 150, 200, 80, 120, 160],
        })
        fig = heatmap_estados(df)
        assert isinstance(fig, go.Figure)


class TestGaugeNivelAlerta:
    def test_niveis(self):
        for nivel in [1, 2, 3, 4]:
            fig = gauge_nivel_alerta(nivel)
            assert isinstance(fig, go.Figure)


class TestIndicadorSimples:
    def test_sem_referencia(self):
        fig = indicador_simples(42, titulo="Teste")
        assert isinstance(fig, go.Figure)

    def test_com_referencia(self):
        fig = indicador_simples(42, titulo="Teste", referencia=35)
        assert isinstance(fig, go.Figure)
