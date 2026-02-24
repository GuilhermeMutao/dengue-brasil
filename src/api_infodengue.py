"""
Módulo de acesso à API do InfoDengue (Fiocruz / FGV).

Fornece funções cacheadas para buscar dados epidemiológicos de dengue
por município, por estado (agregado) e para todo o Brasil (via capitais).
"""

from __future__ import annotations

import time
from typing import Optional

import pandas as pd
import requests
import streamlit as st

from src.constants import (
    DOENCA_PADRAO,
    ESTADOS,
    INFODENGUE_BASE_URL,
    UF_PARA_REGIAO,
)

# ---------------------------------------------------------------------------
_TIMEOUT = 30
_DELAY_ENTRE_REQUISICOES = 0.15  # segundos entre chamadas consecutivas


# =====================================================================
# Nível mais baixo: consulta por município
# =====================================================================

@st.cache_data(
    ttl=3_600,
    show_spinner=False,
)
def buscar_dados_municipio(
    geocode: int,
    ey_start: int,
    ey_end: int,
    ew_start: int = 1,
    ew_end: int = 52,
    disease: str = DOENCA_PADRAO,
) -> pd.DataFrame:
    """Busca dados do InfoDengue para UM município (geocode).

    Retorna DataFrame com colunas:
        se, data_iniSE, casos_est, casos_est_min, casos_est_max,
        casos, p_rt1, p_inc100k, Localidade_id, nivel, id, versao_modelo,
        Rt, pop, tempmin, tempmed, tempmax, umidmin, umidmed, umidmax,
        receptession, transmissao, nivel_inc, notif_accum_year
    """
    params = {
        "geocode": geocode,
        "disease": disease,
        "format": "json",
        "ew_start": ew_start,
        "ew_end": ew_end,
        "ey_start": ey_start,
        "ey_end": ey_end,
    }

    try:
        resp = requests.get(INFODENGUE_BASE_URL, params=params, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError):
        return pd.DataFrame()

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    # Padronizar nomes de colunas
    rename_map = {
        "data_iniSE": "data",
        "SE": "se",
        "casos_est": "casos_est",
        "casos": "casos",
        "Rt": "rt",
        "p_rt1": "p_rt1",
        "p_inc100k": "inc",
        "nivel": "nivel",
        "tempmin": "tmin",
        "tempmed": "tmed",
        "tempmax": "tmax",
        "umidmin": "umid_min",
        "umidmed": "umid_med",
        "umidmax": "umid_max",
        "pop": "populacao",
        "Localidade_id": "geocode",
        "notif_accum_year": "casos_acum_ano",
    }
    # Renomear apenas colunas existentes
    cols_existentes = {k: v for k, v in rename_map.items() if k in df.columns}
    df = df.rename(columns=cols_existentes)

    # Garantir coluna geocode
    if "geocode" not in df.columns:
        df["geocode"] = geocode

    # Converter data
    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], errors="coerce")

    # Converter se para int
    if "se" in df.columns:
        df["se"] = pd.to_numeric(df["se"], errors="coerce").astype("Int64")

    return df


# =====================================================================
# Nível intermediário: consulta por estado (agrega municípios)
# =====================================================================

@st.cache_data(
    ttl=3_600,
    show_spinner="Buscando dados do estado…",
)
def buscar_dados_estado_capitais(
    sigla_uf: str,
    ey_start: int,
    ey_end: int,
) -> pd.DataFrame:
    """Busca dados da CAPITAL do estado como proxy rápido.

    Para visão nacional, consultar apenas capitais é ~200× mais rápido
    do que iterar sobre todos os municípios de cada UF.
    """
    info = ESTADOS.get(sigla_uf)
    if not info:
        return pd.DataFrame()

    df = buscar_dados_municipio(
        geocode=info["capital_geocode"],
        ey_start=ey_start,
        ey_end=ey_end,
    )

    if df.empty:
        return df

    df["sigla_uf"] = sigla_uf
    df["nome_uf"] = info["nome"]
    df["regiao"] = UF_PARA_REGIAO.get(sigla_uf, "")
    return df


@st.cache_data(
    ttl=3_600,
    show_spinner="Buscando dados dos municípios… (pode demorar)",
)
def buscar_dados_municipios_uf(
    sigla_uf: str,
    geocodes: list[int],
    ey_start: int,
    ey_end: int,
    max_municipios: Optional[int] = None,
) -> pd.DataFrame:
    """Busca dados do InfoDengue para uma lista de municípios.

    Itera sobre os geocodes com delay para evitar rate-limiting.
    Se max_municipios for definido, limita a quantidade de consultas.
    """
    if max_municipios:
        geocodes = geocodes[:max_municipios]

    frames: list[pd.DataFrame] = []
    total = len(geocodes)

    progress_bar = st.progress(0, text=f"Carregando municípios de {sigla_uf}…")

    for i, gc in enumerate(geocodes):
        try:
            df = buscar_dados_municipio(gc, ey_start, ey_end)
            if not df.empty:
                frames.append(df)
        except Exception:
            pass

        progress_bar.progress(
            (i + 1) / total,
            text=f"Carregando municípios de {sigla_uf}… ({i + 1}/{total})",
        )

        if i < total - 1:
            time.sleep(_DELAY_ENTRE_REQUISICOES)

    progress_bar.empty()

    if not frames:
        return pd.DataFrame()

    result = pd.concat(frames, ignore_index=True)
    result["sigla_uf"] = sigla_uf
    result["nome_uf"] = ESTADOS.get(sigla_uf, {}).get("nome", sigla_uf)
    result["regiao"] = UF_PARA_REGIAO.get(sigla_uf, "")
    return result


# =====================================================================
# Nível nacional: agrega dados de todas as capitais
# =====================================================================

@st.cache_data(
    ttl=3_600,
    show_spinner="Carregando dados nacionais (27 capitais)…",
)
def buscar_dados_brasil_capitais(
    ey_start: int,
    ey_end: int,
) -> pd.DataFrame:
    """Busca dados de TODAS as 27 capitais e consolida.

    Retorna DataFrame com colunas extras: sigla_uf, nome_uf, regiao.
    """
    frames: list[pd.DataFrame] = []

    for sigla in sorted(ESTADOS.keys()):
        df = buscar_dados_estado_capitais(sigla, ey_start, ey_end)
        if not df.empty:
            frames.append(df)
        time.sleep(_DELAY_ENTRE_REQUISICOES)

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


# =====================================================================
# Agregação por semana epidemiológica (nível nacional)
# =====================================================================

def agregar_nacional_por_semana(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega dados de todas as capitais por semana epidemiológica.

    Soma casos/casos_est; média ponderada de incidência e Rt.
    """
    if df.empty:
        return df

    agg_dict: dict = {
        "casos": "sum",
        "casos_est": "sum",
    }
    if "data" in df.columns:
        agg_dict["data"] = "first"
    if "inc" in df.columns:
        agg_dict["inc"] = "mean"
    if "rt" in df.columns:
        agg_dict["rt"] = "mean"
    if "nivel" in df.columns:
        agg_dict["nivel"] = "max"

    cols_presentes = [c for c in agg_dict if c in df.columns]
    agg_filtrado = {k: v for k, v in agg_dict.items() if k in cols_presentes}

    if "se" not in df.columns:
        return df

    resultado = df.groupby("se", as_index=False).agg(agg_filtrado)
    return resultado.sort_values("se").reset_index(drop=True)


def agregar_por_uf_semana(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega dados por UF e semana epidemiológica."""
    if df.empty or "sigla_uf" not in df.columns or "se" not in df.columns:
        return df

    agg_dict: dict = {"casos": "sum", "casos_est": "sum"}
    if "data" in df.columns:
        agg_dict["data"] = "first"
    if "inc" in df.columns:
        agg_dict["inc"] = "mean"
    if "rt" in df.columns:
        agg_dict["rt"] = "mean"
    if "nivel" in df.columns:
        agg_dict["nivel"] = "max"
    if "nome_uf" in df.columns:
        agg_dict["nome_uf"] = "first"
    if "regiao" in df.columns:
        agg_dict["regiao"] = "first"

    agg_filtrado = {k: v for k, v in agg_dict.items() if k in df.columns}

    resultado = df.groupby(["sigla_uf", "se"], as_index=False).agg(agg_filtrado)
    return resultado.sort_values(["sigla_uf", "se"]).reset_index(drop=True)


def resumo_por_uf(df: pd.DataFrame) -> pd.DataFrame:
    """Gera resumo total por UF (soma de casos no período inteiro).

    Útil para o mapa coroplético de estados.
    """
    if df.empty or "sigla_uf" not in df.columns:
        return df

    agg_dict: dict = {"casos": "sum", "casos_est": "sum"}
    if "inc" in df.columns:
        agg_dict["inc"] = "mean"
    if "rt" in df.columns:
        agg_dict["rt"] = "mean"
    if "nivel" in df.columns:
        agg_dict["nivel"] = lambda x: x.mode().iloc[0] if not x.mode().empty else 1
    if "nome_uf" in df.columns:
        agg_dict["nome_uf"] = "first"
    if "regiao" in df.columns:
        agg_dict["regiao"] = "first"
    if "populacao" in df.columns:
        agg_dict["populacao"] = "first"

    agg_filtrado = {k: v for k, v in agg_dict.items() if k in df.columns}

    resultado = df.groupby("sigla_uf", as_index=False).agg(agg_filtrado)
    return resultado.sort_values("casos", ascending=False).reset_index(drop=True)
