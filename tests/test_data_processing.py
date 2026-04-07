"""
Testes unitários para o módulo de processamento de dados.
"""

import pandas as pd
import numpy as np
import pytest

from src.data_processing import (
    limpar_dados,
    filtrar_por_periodo,
    filtrar_por_uf,
    adicionar_info_uf,
    extrair_ano_semana,
    calcular_variacao_semanal,
    calcular_kpis,
    preparar_dados_mapa_estados,
    preparar_dados_mapa_municipios,
    top_n_localidades,
    semana_epi_para_data,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def df_basico():
    """DataFrame com dados básicos do InfoDengue."""
    return pd.DataFrame({
        "se": [202401, 202402, 202403, 202404, 202405],
        "data": pd.to_datetime(["2024-01-07", "2024-01-14", "2024-01-21", "2024-01-28", "2024-02-04"]),
        "casos": [100, 150, 200, 180, 220],
        "casos_est": [110.0, 160.0, 210.0, 190.0, 230.0],
        "inc": [5.2, 7.8, 10.4, 9.3, 11.5],
        "rt": [1.2, 1.3, 1.1, 0.9, 1.4],
        "nivel": [1, 2, 2, 2, 3],
        "geocode": [3550308, 3550308, 3550308, 3550308, 3550308],
        "sigla_uf": ["SP", "SP", "SP", "SP", "SP"],
    })


@pytest.fixture
def df_multi_uf():
    """DataFrame com dados de múltiplas UFs."""
    return pd.DataFrame({
        "se": [202401, 202401, 202401, 202402, 202402, 202402],
        "data": pd.to_datetime(["2024-01-07"] * 3 + ["2024-01-14"] * 3),
        "casos": [100, 80, 200, 150, 120, 250],
        "casos_est": [110, 90, 220, 160, 130, 270],
        "inc": [5.0, 4.0, 8.0, 6.0, 5.0, 9.0],
        "nivel": [1, 1, 2, 2, 1, 3],
        "sigla_uf": ["SP", "RJ", "MG", "SP", "RJ", "MG"],
        "geocode": [3550308, 3304557, 3106200, 3550308, 3304557, 3106200],
    })


# ---------------------------------------------------------------------------
# Testes: limpar_dados
# ---------------------------------------------------------------------------

class TestLimparDados:
    def test_remove_casos_est_nulos(self):
        df = pd.DataFrame({
            "casos": [10, 20, 30],
            "casos_est": [11.0, None, 33.0],
            "nivel": [1, 2, 3],
        })
        resultado = limpar_dados(df)
        assert len(resultado) == 2

    def test_valida_nivel_alerta(self):
        df = pd.DataFrame({
            "casos": [10, 20],
            "casos_est": [11.0, 22.0],
            "nivel": [5, -1],
        })
        resultado = limpar_dados(df)
        assert (resultado["nivel"] == 1).all()

    def test_converte_data(self):
        df = pd.DataFrame({
            "data": ["2024-01-01", "2024-02-01"],
            "casos": [10, 20],
            "casos_est": [11.0, 22.0],
        })
        resultado = limpar_dados(df)
        assert pd.api.types.is_datetime64_any_dtype(resultado["data"])

    def test_converte_indicadores_e_clima(self):
        df = pd.DataFrame({
            "casos": ["10", "20"],
            "casos_est": ["11.0", "22.0"],
            "p_rt1": pd.Series(["0.8", "0.9"], dtype="string"),
            "tmed": pd.Series(["25.5", "26.5"], dtype="string"),
            "umid_med": pd.Series(["75", "80"], dtype="string"),
        })

        resultado = limpar_dados(df)

        assert pd.api.types.is_numeric_dtype(resultado["p_rt1"])
        assert pd.api.types.is_numeric_dtype(resultado["tmed"])
        assert pd.api.types.is_numeric_dtype(resultado["umid_med"])

    def test_df_vazio(self):
        df = pd.DataFrame()
        resultado = limpar_dados(df)
        assert resultado.empty


# ---------------------------------------------------------------------------
# Testes: filtrar_por_periodo
# ---------------------------------------------------------------------------

class TestFiltrarPorPeriodo:
    def test_filtra_por_ano(self, df_basico):
        resultado = filtrar_por_periodo(df_basico, 2024, 2024)
        assert len(resultado) == 5

    def test_filtra_excluindo(self, df_basico):
        resultado = filtrar_por_periodo(df_basico, 2025, 2025)
        assert len(resultado) == 0

    def test_df_vazio(self):
        df = pd.DataFrame()
        resultado = filtrar_por_periodo(df, 2024, 2024)
        assert resultado.empty


# ---------------------------------------------------------------------------
# Testes: filtrar_por_uf
# ---------------------------------------------------------------------------

class TestFiltrarPorUf:
    def test_filtra_uf(self, df_multi_uf):
        resultado = filtrar_por_uf(df_multi_uf, "SP")
        assert len(resultado) == 2
        assert (resultado["sigla_uf"] == "SP").all()

    def test_uf_inexistente(self, df_multi_uf):
        resultado = filtrar_por_uf(df_multi_uf, "XX")
        assert len(resultado) == 0


# ---------------------------------------------------------------------------
# Testes: adicionar_info_uf
# ---------------------------------------------------------------------------

class TestAdicionarInfoUf:
    def test_adiciona_nome_e_regiao(self, df_basico):
        resultado = adicionar_info_uf(df_basico)
        assert "nome_uf" in resultado.columns
        assert "regiao" in resultado.columns
        assert resultado["nome_uf"].iloc[0] == "São Paulo"
        assert resultado["regiao"].iloc[0] == "Sudeste"


# ---------------------------------------------------------------------------
# Testes: extrair_ano_semana
# ---------------------------------------------------------------------------

class TestExtrairAnoSemana:
    def test_extrai_corretamente(self, df_basico):
        resultado = extrair_ano_semana(df_basico)
        assert "ano" in resultado.columns
        assert "semana" in resultado.columns
        assert resultado["ano"].iloc[0] == 2024
        assert resultado["semana"].iloc[0] == 1


# ---------------------------------------------------------------------------
# Testes: calcular_kpis
# ---------------------------------------------------------------------------

class TestCalcularKpis:
    def test_kpis_basicos(self, df_basico):
        kpis = calcular_kpis(df_basico)
        assert kpis["total_casos"] == 850
        assert kpis["total_casos_est"] == 900
        assert isinstance(kpis["media_incidencia"], float)
        assert isinstance(kpis["media_rt"], float)
        assert kpis["nivel_predominante"] == 2

    def test_variacao_semanal(self, df_basico):
        kpis = calcular_kpis(df_basico)
        # Último: 220, penúltimo: 180 → variação = (220-180)/180 * 100 ≈ 22.2%
        assert abs(kpis["variacao_semanal"] - 22.2) < 0.2

    def test_df_vazio(self):
        kpis = calcular_kpis(pd.DataFrame())
        assert kpis["total_casos"] == 0


# ---------------------------------------------------------------------------
# Testes: preparar_dados_mapa
# ---------------------------------------------------------------------------

class TestPrepararDadosMapa:
    def test_mapa_estados(self, df_multi_uf):
        from src.api_infodengue import resumo_por_uf

        resumo = resumo_por_uf(df_multi_uf)
        resultado = preparar_dados_mapa_estados(resumo)
        assert "codarea" in resultado.columns

    def test_mapa_municipios(self, df_basico):
        resultado = preparar_dados_mapa_municipios(df_basico)
        assert "codarea" in resultado.columns
        assert len(resultado) == 1  # Um município


# ---------------------------------------------------------------------------
# Testes: top_n_localidades
# ---------------------------------------------------------------------------

class TestTopNLocalidades:
    def test_top_2(self, df_multi_uf):
        resultado = top_n_localidades(
            df_multi_uf, coluna_grupo="sigla_uf", coluna_metrica="casos", n=2
        )
        assert len(resultado) == 2
        assert resultado.iloc[0]["sigla_uf"] == "MG"  # MG tem mais casos


# ---------------------------------------------------------------------------
# Testes: semana_epi_para_data
# ---------------------------------------------------------------------------

class TestSemanaEpiParaData:
    def test_converte_se(self):
        data = semana_epi_para_data(202401)
        # SE 1/2024 começa no domingo 31/12/2023 (comportamento correto)
        assert data.year in (2023, 2024)
        assert data.month in (12, 1)

    def test_converte_se_meio_ano(self):
        data = semana_epi_para_data(202426)
        assert data.year == 2024
        assert data.month in (6, 7)
