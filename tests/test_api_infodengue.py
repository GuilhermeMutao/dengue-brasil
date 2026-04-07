"""
Testes unitários para o módulo de acesso à API InfoDengue.
"""

import pandas as pd
import pytest

from src.api_infodengue import (
    agregar_nacional_por_semana,
    agregar_por_uf_semana,
    resumo_por_uf,
)


@pytest.fixture
def df_capitais():
    """DataFrame simulando dados de múltiplas capitais."""
    return pd.DataFrame({
        "se": [202401, 202401, 202402, 202402],
        "data": pd.to_datetime(["2024-01-07"] * 2 + ["2024-01-14"] * 2),
        "casos": [100, 80, 150, 120],
        "casos_est": [110, 90, 160, 130],
        "casos_est_min": [105, 85, 155, 125],
        "casos_est_max": [120, 100, 170, 140],
        "inc": [5.0, 4.0, 6.0, 5.0],
        "rt": [1.2, 1.1, 1.3, 1.0],
        "nivel": [1, 1, 2, 1],
        "sigla_uf": ["SP", "RJ", "SP", "RJ"],
        "nome_uf": ["São Paulo", "Rio de Janeiro", "São Paulo", "Rio de Janeiro"],
        "regiao": ["Sudeste", "Sudeste", "Sudeste", "Sudeste"],
    })


class TestAgregarNacionalPorSemana:
    def test_agrega_corretamente(self, df_capitais):
        resultado = agregar_nacional_por_semana(df_capitais)
        assert len(resultado) == 2  # 2 semanas
        assert resultado["casos"].iloc[0] == 180  # 100 + 80
        assert resultado["casos_est_min"].iloc[0] == 190  # 105 + 85
        assert resultado["casos_est_max"].iloc[0] == 220  # 120 + 100

    def test_agrega_colunas_numericas_como_texto(self, df_capitais):
        df = df_capitais.copy()
        df["p_rt1"] = pd.Series(["0.6", "0.8", "0.5", "0.7"], dtype="string")
        df["tmed"] = pd.Series(["25.0", "26.0", "27.0", "28.0"], dtype="string")
        df["nivel"] = pd.Series(["1", "1", "2", "1"], dtype="string")

        resultado = agregar_nacional_por_semana(df)

        assert resultado["p_rt1"].iloc[0] == pytest.approx(0.7)
        assert resultado["tmed"].iloc[0] == pytest.approx(25.5)
        assert resultado["nivel"].iloc[0] == 1

    def test_df_vazio(self):
        resultado = agregar_nacional_por_semana(pd.DataFrame())
        assert resultado.empty


class TestAgregarPorUfSemana:
    def test_agrega_por_uf(self, df_capitais):
        resultado = agregar_por_uf_semana(df_capitais)
        assert len(resultado) == 4  # 2 UFs × 2 semanas
        sp_202401 = resultado[
            (resultado["sigla_uf"] == "SP") & (resultado["se"] == 202401)
        ]
        assert sp_202401["casos_est_min"].iloc[0] == 105
        assert sp_202401["casos_est_max"].iloc[0] == 120

    def test_agrega_texto_numerico(self, df_capitais):
        df = df_capitais.copy()
        df["p_rt1"] = pd.Series(["0.6", "0.8", "0.5", "0.7"], dtype="string")
        df["tmed"] = pd.Series(["25.0", "26.0", "27.0", "28.0"], dtype="string")

        resultado = agregar_por_uf_semana(df)

        sp_202401 = resultado[
            (resultado["sigla_uf"] == "SP") & (resultado["se"] == 202401)
        ]
        assert sp_202401["p_rt1"].iloc[0] == pytest.approx(0.6)
        assert sp_202401["tmed"].iloc[0] == pytest.approx(25.0)

    def test_df_vazio(self):
        resultado = agregar_por_uf_semana(pd.DataFrame())
        assert resultado.empty


class TestResumoPorUf:
    def test_resumo(self, df_capitais):
        resultado = resumo_por_uf(df_capitais)
        assert len(resultado) == 2  # 2 UFs
        sp = resultado[resultado["sigla_uf"] == "SP"]
        assert sp["casos"].iloc[0] == 250  # 100 + 150

    def test_resumo_texto_numerico(self, df_capitais):
        df = df_capitais.copy()
        df["p_rt1"] = pd.Series(["0.6", "0.8", "0.5", "0.7"], dtype="string")
        df["tmed"] = pd.Series(["25.0", "26.0", "27.0", "28.0"], dtype="string")

        resultado = resumo_por_uf(df)

        sp = resultado[resultado["sigla_uf"] == "SP"]
        assert sp["p_rt1"].iloc[0] == pytest.approx(0.55)
        assert sp["tmed"].iloc[0] == pytest.approx(26.0)

    def test_df_vazio(self):
        resultado = resumo_por_uf(pd.DataFrame())
        assert resultado.empty
