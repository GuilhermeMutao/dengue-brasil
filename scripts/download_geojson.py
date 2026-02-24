"""
Script para pré-download de dados geográficos do IBGE.

Execute uma vez antes do deploy para garantir que os dados
estejam disponíveis offline:

    python scripts/download_geojson.py

Baixa:
- GeoJSON dos estados brasileiros (para mapa coroplético)
- Lista completa de municípios com geocodes (CSV)
"""

import json
import os
import sys
from pathlib import Path

import requests

# Adicionar raiz do projeto ao path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.constants import ESTADOS, IBGE_LOCALIDADES_URL, IBGE_MALHAS_URL

DATA_DIR = PROJECT_ROOT / "data"
GEOJSON_DIR = DATA_DIR / "geojson"
TIMEOUT = 60


def download_geojson_estados():
    """Baixa GeoJSON dos 27 estados brasileiros."""
    print("📥 Baixando GeoJSON dos estados…")
    url = (
        f"{IBGE_MALHAS_URL}/paises/BR"
        "?intrarregiao=UF"
        "&formato=application/vnd.geo+json"
        "&qualidade=intermediaria"
    )

    resp = requests.get(url, timeout=TIMEOUT)
    resp.raise_for_status()
    geojson = resp.json()

    os.makedirs(GEOJSON_DIR, exist_ok=True)
    filepath = GEOJSON_DIR / "brasil_estados.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False)

    n_features = len(geojson.get("features", []))
    size_mb = filepath.stat().st_size / (1024 * 1024)
    print(f"   ✅ Salvo: {filepath}")
    print(f"   → {n_features} features, {size_mb:.2f} MB")


def download_municipios_csv():
    """Baixa lista de todos os municípios do IBGE em CSV."""
    print("\n📥 Baixando lista de municípios…")

    url = f"{IBGE_LOCALIDADES_URL}/municipios?orderBy=nome"
    resp = requests.get(url, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    rows = []
    for m in data:
        # A estrutura pode variar: microrregiao → mesorregiao → UF
        # ou região-imediata → região-intermediária → UF
        uf_info = {}
        micro = m.get("microrregiao")
        if micro:
            meso = micro.get("mesorregiao")
            if meso:
                uf_info = meso.get("UF", {}) or {}
        if not uf_info:
            ri = m.get("regiao-imediata")
            if ri:
                rint = ri.get("regiao-intermediaria")
                if rint:
                    uf_info = rint.get("UF", {}) or {}
        if not uf_info:
            # Fallback: extrair do geocode (2 primeiros dígitos)
            gc = str(m.get("id", ""))
            uf_info = {"id": gc[:2], "sigla": "", "nome": ""}

        rows.append({
            "geocode": m["id"],
            "nome": m["nome"],
            "cod_uf": uf_info.get("id", ""),
            "sigla_uf": uf_info.get("sigla", ""),
            "nome_uf": uf_info.get("nome", ""),
        })

    # Salvar como CSV
    import csv

    filepath = DATA_DIR / "municipios_ibge.csv"
    os.makedirs(DATA_DIR, exist_ok=True)

    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["geocode", "nome", "cod_uf", "sigla_uf", "nome_uf"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"   ✅ Salvo: {filepath}")
    print(f"   → {len(rows)} municípios")


def main():
    print("=" * 60)
    print("  Dashboard Dengue Brasil — Download de Dados Geográficos")
    print("=" * 60)

    download_geojson_estados()
    download_municipios_csv()

    print("\n" + "=" * 60)
    print("  ✅ Download completo!")
    print("=" * 60)


if __name__ == "__main__":
    main()
