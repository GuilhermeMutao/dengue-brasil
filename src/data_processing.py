"""
Módulo de processamento e transformação de dados.

Funções de limpeza, filtragem, agregação e cálculos derivados
para os DataFrames epidemiológicos.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from src.constants import (
    ESTADOS,
    POPULACAO_BRASIL,
    POPULACAO_ESTADOS,
    SIGLA_PARA_COD_UF,
    UF_PARA_REGIAO,
)


# =====================================================================
# Limpeza
# =====================================================================

def limpar_dados(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica limpeza padrão nos dados do InfoDengue.

    - Remove linhas com casos_est nulo
    - Valida nível de alerta (1-4)
    - Garante geocode como int
    - Converte coluna 'data' para datetime
    """
    if df.empty:
        return df

    df = df.copy()

    # Converter data
    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], errors="coerce")

    # Remover linhas sem estimativa de casos
    if "casos_est" in df.columns:
        df = df.dropna(subset=["casos_est"])

    # Validar nível de alerta
    if "nivel" in df.columns:
        df["nivel"] = pd.to_numeric(df["nivel"], errors="coerce")
        df.loc[~df["nivel"].isin([1, 2, 3, 4]), "nivel"] = 1

    # Geocode como int
    if "geocode" in df.columns:
        df["geocode"] = pd.to_numeric(df["geocode"], errors="coerce").astype("Int64")

    # Garantir que casos é numérico
    for col in ["casos", "casos_est", "inc", "rt"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df.reset_index(drop=True)


# =====================================================================
# Filtragem
# =====================================================================

def filtrar_por_periodo(
    df: pd.DataFrame,
    ano_inicio: int,
    ano_fim: int,
) -> pd.DataFrame:
    """Filtra DataFrame pelo período (usando coluna 'se' — formato YYYYWW)."""
    if df.empty:
        return df

    df = df.copy()

    if "se" in df.columns:
        df["ano_se"] = df["se"].astype(str).str[:4].astype(int)
        df = df[(df["ano_se"] >= ano_inicio) & (df["ano_se"] <= ano_fim)]
        df = df.drop(columns=["ano_se"])
    elif "data" in df.columns:
        df = df[
            (df["data"].dt.year >= ano_inicio) & (df["data"].dt.year <= ano_fim)
        ]

    return df.reset_index(drop=True)


def filtrar_por_uf(df: pd.DataFrame, sigla_uf: str) -> pd.DataFrame:
    """Filtra DataFrame por sigla de UF."""
    if df.empty or "sigla_uf" not in df.columns:
        return df
    return df[df["sigla_uf"] == sigla_uf].reset_index(drop=True)


def filtrar_por_geocode(df: pd.DataFrame, geocode: int) -> pd.DataFrame:
    """Filtra DataFrame por geocode de município."""
    if df.empty or "geocode" not in df.columns:
        return df
    return df[df["geocode"] == geocode].reset_index(drop=True)


def filtrar_por_regiao(
    df: pd.DataFrame,
    regioes: list[str],
) -> pd.DataFrame:
    """Filtra DataFrame pelas macrorregiões selecionadas."""
    if df.empty or not regioes or "regiao" not in df.columns:
        return df
    return df[df["regiao"].isin(regioes)].reset_index(drop=True)


def filtrar_por_nivel_alerta(
    df: pd.DataFrame,
    niveis: list[int],
) -> pd.DataFrame:
    """Filtra DataFrame pelos níveis de alerta selecionados."""
    if df.empty or not niveis or "nivel" not in df.columns:
        return df
    return df[df["nivel"].isin(niveis)].reset_index(drop=True)


# =====================================================================
# Enriquecimento
# =====================================================================

def adicionar_info_uf(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona colunas nome_uf, regiao, cod_uf baseado em sigla_uf."""
    if df.empty or "sigla_uf" not in df.columns:
        return df

    df = df.copy()

    if "nome_uf" not in df.columns:
        df["nome_uf"] = df["sigla_uf"].map(
            lambda s: ESTADOS.get(s, {}).get("nome", s)
        )
    if "regiao" not in df.columns:
        df["regiao"] = df["sigla_uf"].map(UF_PARA_REGIAO)
    if "cod_uf" not in df.columns:
        df["cod_uf"] = df["sigla_uf"].map(SIGLA_PARA_COD_UF)

    return df


def extrair_ano_semana(df: pd.DataFrame) -> pd.DataFrame:
    """Extrai colunas 'ano' e 'semana' a partir de 'se' (formato YYYYWW)."""
    if df.empty or "se" not in df.columns:
        return df

    df = df.copy()
    se_str = df["se"].astype(str)
    df["ano"] = se_str.str[:4].astype(int)
    df["semana"] = se_str.str[4:].astype(int)
    return df


# =====================================================================
# Métricas populacionais
# =====================================================================

def adicionar_metricas_populacionais(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona métricas normalizadas pela população ao resumo por UF.

    Colunas adicionadas:
        - populacao: população estimada do estado (IBGE 2024)
        - casos_por_100k: casos notificados por 100 mil habitantes
        - pct_nacional: % dos casos em relação ao total nacional
        - taxa_est_notif: razão entre casos estimados e notificados
    """
    if df.empty or "sigla_uf" not in df.columns:
        return df

    df = df.copy()

    # População do estado (IBGE 2024)
    df["populacao"] = df["sigla_uf"].map(POPULACAO_ESTADOS)

    # Casos por 100 mil habitantes
    if "casos" in df.columns:
        df["casos_por_100k"] = np.where(
            df["populacao"] > 0,
            (df["casos"] / df["populacao"]) * 100_000,
            0.0,
        )
        df["casos_por_100k"] = df["casos_por_100k"].round(1)

        # Percentual do total nacional
        total_nacional = df["casos"].sum()
        df["pct_nacional"] = np.where(
            total_nacional > 0,
            (df["casos"] / total_nacional) * 100,
            0.0,
        )
        df["pct_nacional"] = df["pct_nacional"].round(2)

    # Razão estimado / notificado
    if "casos" in df.columns and "casos_est" in df.columns:
        df["taxa_est_notif"] = np.where(
            df["casos"] > 0,
            df["casos_est"] / df["casos"],
            0.0,
        )
        df["taxa_est_notif"] = df["taxa_est_notif"].round(2)

    return df


# =====================================================================
# Cálculos derivados
# =====================================================================

def calcular_variacao_semanal(
    df: pd.DataFrame,
    coluna: str = "casos",
) -> pd.DataFrame:
    """Calcula variação percentual semana a semana.

    Adiciona coluna '{coluna}_var_pct'.
    """
    if df.empty or coluna not in df.columns:
        return df

    df = df.copy()
    df = df.sort_values("se")
    df[f"{coluna}_var_pct"] = df[coluna].pct_change() * 100
    return df


def top_n_localidades(
    df: pd.DataFrame,
    coluna_grupo: str = "sigla_uf",
    coluna_metrica: str = "casos",
    n: int = 10,
    ascending: bool = False,
) -> pd.DataFrame:
    """Retorna os top N locais por métrica agregada."""
    if df.empty or coluna_grupo not in df.columns or coluna_metrica not in df.columns:
        return df

    ranking = (
        df.groupby(coluna_grupo, as_index=False)[coluna_metrica]
        .sum()
        .sort_values(coluna_metrica, ascending=ascending)
        .head(n)
    )
    return ranking.reset_index(drop=True)


def calcular_kpis(df: pd.DataFrame) -> dict:
    """Calcula KPIs gerais a partir de um DataFrame epidemiológico.

    Retorna dicionário com:
        total_casos, total_casos_est, media_incidencia,
        media_rt, nivel_predominante, ultima_semana,
        casos_ultima_semana, variacao_semanal
    """
    if df.empty:
        return {
            "total_casos": 0,
            "total_casos_est": 0,
            "media_incidencia": 0.0,
            "media_rt": 0.0,
            "nivel_predominante": 1,
            "ultima_semana": "—",
            "casos_ultima_semana": 0,
            "variacao_semanal": 0.0,
        }

    total_casos = int(df["casos"].sum()) if "casos" in df.columns else 0
    total_casos_est = int(df["casos_est"].sum()) if "casos_est" in df.columns else 0
    media_inc = float(df["inc"].mean()) if "inc" in df.columns else 0.0
    media_rt = float(df["rt"].mean()) if "rt" in df.columns else 0.0

    # Nível predominante (moda)
    nivel_predominante = 1
    if "nivel" in df.columns and not df["nivel"].dropna().empty:
        moda = df["nivel"].dropna().mode()
        nivel_predominante = int(moda.iloc[0]) if not moda.empty else 1

    # Última semana
    ultima_se = "—"
    casos_ultima = 0
    variacao = 0.0

    if "se" in df.columns and not df["se"].dropna().empty:
        df_sorted = df.sort_values("se")
        ultima_se = str(df_sorted["se"].iloc[-1])

        if "casos" in df.columns:
            casos_ultima = int(df_sorted["casos"].iloc[-1])
            if len(df_sorted) >= 2:
                penultimo = df_sorted["casos"].iloc[-2]
                if penultimo > 0:
                    variacao = round(((casos_ultima - penultimo) / penultimo) * 100, 1)

    return {
        "total_casos": total_casos,
        "total_casos_est": total_casos_est,
        "media_incidencia": round(media_inc, 2),
        "media_rt": round(media_rt, 3),
        "nivel_predominante": nivel_predominante,
        "ultima_semana": ultima_se,
        "casos_ultima_semana": casos_ultima,
        "variacao_semanal": variacao,
    }


def preparar_dados_mapa_estados(
    resumo_uf: pd.DataFrame,
) -> pd.DataFrame:
    """Prepara DataFrame para o mapa coroplético de estados.

    Garante que a coluna 'codarea' é string inteira (ex: "11", "35")
    para match com o GeoJSON do IBGE (properties.codarea).
    """
    if resumo_uf.empty:
        return resumo_uf

    df = resumo_uf.copy()

    # Adicionar cod_uf se não existir
    if "cod_uf" not in df.columns and "sigla_uf" in df.columns:
        df["cod_uf"] = df["sigla_uf"].map(SIGLA_PARA_COD_UF)

    # codarea como string inteira — defesa contra float64 (NaN → "11.0")
    df["codarea"] = (
        pd.to_numeric(df["cod_uf"], errors="coerce")
        .fillna(0)
        .astype(int)
        .astype(str)
    )

    # Remover linhas com codarea inválido
    df = df[df["codarea"] != "0"]

    return df


def preparar_dados_mapa_municipios(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Prepara DataFrame para o mapa coroplético de municípios.

    Agrega por geocode e converte para string (codarea).
    """
    if df.empty or "geocode" not in df.columns:
        return df

    agg_dict: dict = {"casos": "sum", "casos_est": "sum"}
    if "inc" in df.columns:
        agg_dict["inc"] = "mean"
    if "nivel" in df.columns:
        agg_dict["nivel"] = "max"

    agg_filtrado = {k: v for k, v in agg_dict.items() if k in df.columns}

    resultado = df.groupby("geocode", as_index=False).agg(agg_filtrado)
    resultado["codarea"] = (
        pd.to_numeric(resultado["geocode"], errors="coerce")
        .fillna(0)
        .astype(int)
        .astype(str)
    )

    return resultado


def semana_epi_para_data(se: int) -> datetime:
    """Converte semana epidemiológica (formato YYYYWW) para datetime.

    A semana epidemiológica no Brasil inicia no domingo.
    """
    se_str = str(se)
    ano = int(se_str[:4])
    semana = int(se_str[4:])

    # Primeiro dia do ano
    jan1 = datetime(ano, 1, 1)
    # Encontrar o primeiro domingo do ano
    dia_semana = jan1.weekday()  # 0=segunda, 6=domingo
    # Offset para o primeiro domingo
    offset = (6 - dia_semana) % 7
    primeiro_domingo = jan1 + timedelta(days=offset)

    # Se o primeiro domingo é depois de 3 de janeiro, a SE 1 começa no ano anterior
    if offset > 3:
        primeiro_domingo -= timedelta(days=7)

    return primeiro_domingo + timedelta(weeks=semana - 1)
