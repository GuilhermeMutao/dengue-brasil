"""
Módulo de acesso à API do IBGE.

Fornece funções cacheadas para obter:
- Lista de estados e municípios (API Localidades v1)
- GeoJSON de estados e municípios (API Malhas v3)
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

from src.constants import (
    ESTADOS,
    IBGE_LOCALIDADES_URL,
    IBGE_MALHAS_URL,
    UF_PARA_REGIAO,
)

# Diretório base do projeto
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_GEOJSON_DIR = _PROJECT_ROOT / "data" / "geojson"

# ---------------------------------------------------------------------------
# Timeout padrão para requisições HTTP (segundos)
# ---------------------------------------------------------------------------
_TIMEOUT = 30


# =====================================================================
# Localidades
# =====================================================================

@st.cache_data(ttl=86_400, show_spinner="Carregando lista de estados…")
def carregar_estados() -> pd.DataFrame:
    """Retorna DataFrame com todos os 27 estados brasileiros.

    Colunas: cod_uf, sigla, nome, regiao
    """
    url = f"{IBGE_LOCALIDADES_URL}/estados?orderBy=nome"
    resp = requests.get(url, timeout=_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    rows = []
    for estado in data:
        sigla = estado["sigla"]
        rows.append(
            {
                "cod_uf": estado["id"],
                "sigla": sigla,
                "nome": estado["nome"],
                "regiao": estado.get("regiao", {}).get("nome", UF_PARA_REGIAO.get(sigla, "")),
            }
        )

    return pd.DataFrame(rows).sort_values("nome").reset_index(drop=True)


@st.cache_data(ttl=86_400, show_spinner="Carregando municípios…")
def carregar_municipios(cod_uf: int) -> pd.DataFrame:
    """Retorna DataFrame com os municípios de uma UF.

    Colunas: geocode, nome, cod_uf, sigla_uf
    """
    url = f"{IBGE_LOCALIDADES_URL}/estados/{cod_uf}/municipios?orderBy=nome"
    resp = requests.get(url, timeout=_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    rows = []
    for m in data:
        # Extrair sigla da UF robustamente
        sigla_uf = ""
        micro = m.get("microrregiao")
        if micro:
            meso = micro.get("mesorregiao")
            if meso:
                uf = meso.get("UF")
                if uf:
                    sigla_uf = uf.get("sigla", "")
        if not sigla_uf:
            ri = m.get("regiao-imediata")
            if ri:
                rint = ri.get("regiao-intermediaria")
                if rint:
                    uf = rint.get("UF")
                    if uf:
                        sigla_uf = uf.get("sigla", "")

        rows.append(
            {
                "geocode": m["id"],
                "nome": m["nome"],
                "cod_uf": cod_uf,
                "sigla_uf": sigla_uf,
            }
        )

    df = pd.DataFrame(rows)
    # Garantir geocode como int (7 dígitos)
    df["geocode"] = df["geocode"].astype(int)
    return df.sort_values("nome").reset_index(drop=True)


@st.cache_data(ttl=86_400, show_spinner="Carregando todos os municípios do Brasil…")
def carregar_todos_municipios() -> pd.DataFrame:
    """Retorna DataFrame com TODOS os municípios do Brasil.

    Faz 27 chamadas (uma por UF) e concatena.
    """
    frames = []
    for sigla, info in ESTADOS.items():
        try:
            df = carregar_municipios(info["cod_uf"])
            if df["sigla_uf"].isna().all() or (df["sigla_uf"] == "").all():
                df["sigla_uf"] = sigla
            frames.append(df)
        except Exception:
            continue

    if not frames:
        return pd.DataFrame(columns=["geocode", "nome", "cod_uf", "sigla_uf"])

    return pd.concat(frames, ignore_index=True).sort_values("nome").reset_index(drop=True)


# =====================================================================
# GeoJSON
# =====================================================================

@st.cache_resource(show_spinner="Carregando mapa dos estados…")
def carregar_geojson_estados() -> dict:
    """Retorna GeoJSON dos estados brasileiros.

    Tenta carregar do arquivo local primeiro (fallback offline).
    Senão, busca da API IBGE Malhas v3.
    """
    local_path = _GEOJSON_DIR / "brasil_estados.json"

    # Fallback local
    if local_path.exists():
        with open(local_path, encoding="utf-8") as f:
            return json.load(f)

    # Buscar da API IBGE
    url = (
        f"{IBGE_MALHAS_URL}/paises/BR"
        "?intrarregiao=UF"
        "&formato=application/vnd.geo+json"
        "&qualidade=intermediaria"
    )
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    geojson = resp.json()

    # Salvar localmente como cache
    os.makedirs(_GEOJSON_DIR, exist_ok=True)
    with open(local_path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False)

    return geojson


@st.cache_resource(show_spinner="Carregando mapa dos municípios…")
def carregar_geojson_municipios(cod_uf: int) -> dict:
    """Retorna GeoJSON dos municípios de uma UF.

    Busca da API IBGE Malhas v3 e cacheia em memória.
    """
    local_path = _GEOJSON_DIR / f"municipios_{cod_uf}.json"

    if local_path.exists():
        with open(local_path, encoding="utf-8") as f:
            return json.load(f)

    url = (
        f"{IBGE_MALHAS_URL}/estados/{cod_uf}"
        "?intrarregiao=municipio"
        "&formato=application/vnd.geo+json"
        "&qualidade=minima"
    )
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    geojson = resp.json()

    # Salvar localmente
    os.makedirs(_GEOJSON_DIR, exist_ok=True)
    with open(local_path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False)

    return geojson


def obter_feature_id_key_estados(geojson: dict) -> str:
    """Detecta automaticamente a chave de identificação no GeoJSON de estados.

    Retorna algo como 'properties.codarea' ou 'properties.id'.
    """
    if not geojson.get("features"):
        return "properties.codarea"

    props = geojson["features"][0].get("properties", {})
    # Prioridade: codarea > cod_uf > id
    for key in ("codarea", "cod_uf", "CD_UF", "id"):
        if key in props:
            return f"properties.{key}"
    return "properties.codarea"


def obter_feature_id_key_municipios(geojson: dict) -> str:
    """Detecta automaticamente a chave no GeoJSON de municípios."""
    if not geojson.get("features"):
        return "properties.codarea"

    props = geojson["features"][0].get("properties", {})
    for key in ("codarea", "CD_MUN", "geocode", "id"):
        if key in props:
            return f"properties.{key}"
    return "properties.codarea"
