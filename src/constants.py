"""
Constantes globais do Dashboard Dengue Brasil.

Mapeamentos de UFs, regiões, geocodes de capitais, paleta de cores
e configurações padrão da aplicação.
"""

# ---------------------------------------------------------------------------
# Configurações da aplicação
# ---------------------------------------------------------------------------
APP_TITLE = "Dashboard Dengue Brasil"
APP_ICON = "🦟"
APP_LAYOUT = "wide"

ANO_MINIMO = 2010
ANO_MAXIMO = 2025
DOENCA_PADRAO = "dengue"

# ---------------------------------------------------------------------------
# Informações dos 27 estados brasileiros (sigla, nome, código IBGE do estado
# e geocode IBGE da capital — usado como proxy para consultas rápidas)
# ---------------------------------------------------------------------------
ESTADOS: dict[str, dict] = {
    "AC": {"nome": "Acre", "cod_uf": 12, "capital_geocode": 1200401, "capital": "Rio Branco"},
    "AL": {"nome": "Alagoas", "cod_uf": 27, "capital_geocode": 2704302, "capital": "Maceió"},
    "AM": {"nome": "Amazonas", "cod_uf": 13, "capital_geocode": 1302603, "capital": "Manaus"},
    "AP": {"nome": "Amapá", "cod_uf": 16, "capital_geocode": 1600303, "capital": "Macapá"},
    "BA": {"nome": "Bahia", "cod_uf": 29, "capital_geocode": 2927408, "capital": "Salvador"},
    "CE": {"nome": "Ceará", "cod_uf": 23, "capital_geocode": 2304400, "capital": "Fortaleza"},
    "DF": {"nome": "Distrito Federal", "cod_uf": 53, "capital_geocode": 5300108, "capital": "Brasília"},
    "ES": {"nome": "Espírito Santo", "cod_uf": 32, "capital_geocode": 3205309, "capital": "Vitória"},
    "GO": {"nome": "Goiás", "cod_uf": 52, "capital_geocode": 5208707, "capital": "Goiânia"},
    "MA": {"nome": "Maranhão", "cod_uf": 21, "capital_geocode": 2111300, "capital": "São Luís"},
    "MG": {"nome": "Minas Gerais", "cod_uf": 31, "capital_geocode": 3106200, "capital": "Belo Horizonte"},
    "MS": {"nome": "Mato Grosso do Sul", "cod_uf": 50, "capital_geocode": 5002704, "capital": "Campo Grande"},
    "MT": {"nome": "Mato Grosso", "cod_uf": 51, "capital_geocode": 5103403, "capital": "Cuiabá"},
    "PA": {"nome": "Pará", "cod_uf": 15, "capital_geocode": 1501402, "capital": "Belém"},
    "PB": {"nome": "Paraíba", "cod_uf": 25, "capital_geocode": 2507507, "capital": "João Pessoa"},
    "PE": {"nome": "Pernambuco", "cod_uf": 26, "capital_geocode": 2611606, "capital": "Recife"},
    "PI": {"nome": "Piauí", "cod_uf": 22, "capital_geocode": 2211001, "capital": "Teresina"},
    "PR": {"nome": "Paraná", "cod_uf": 41, "capital_geocode": 4106902, "capital": "Curitiba"},
    "RJ": {"nome": "Rio de Janeiro", "cod_uf": 33, "capital_geocode": 3304557, "capital": "Rio de Janeiro"},
    "RN": {"nome": "Rio Grande do Norte", "cod_uf": 24, "capital_geocode": 2408102, "capital": "Natal"},
    "RO": {"nome": "Rondônia", "cod_uf": 11, "capital_geocode": 1100205, "capital": "Porto Velho"},
    "RR": {"nome": "Roraima", "cod_uf": 14, "capital_geocode": 1400100, "capital": "Boa Vista"},
    "RS": {"nome": "Rio Grande do Sul", "cod_uf": 43, "capital_geocode": 4314902, "capital": "Porto Alegre"},
    "SC": {"nome": "Santa Catarina", "cod_uf": 42, "capital_geocode": 4205407, "capital": "Florianópolis"},
    "SE": {"nome": "Sergipe", "cod_uf": 28, "capital_geocode": 2800308, "capital": "Aracaju"},
    "SP": {"nome": "São Paulo", "cod_uf": 35, "capital_geocode": 3550308, "capital": "São Paulo"},
    "TO": {"nome": "Tocantins", "cod_uf": 17, "capital_geocode": 1721000, "capital": "Palmas"},
}

# ---------------------------------------------------------------------------
# Macrorregiões do Brasil
# ---------------------------------------------------------------------------
REGIOES: dict[str, list[str]] = {
    "Norte": ["AC", "AM", "AP", "PA", "RO", "RR", "TO"],
    "Nordeste": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
    "Sudeste": ["ES", "MG", "RJ", "SP"],
    "Sul": ["PR", "RS", "SC"],
    "Centro-Oeste": ["DF", "GO", "MS", "MT"],
}

# Mapeamento inverso: sigla → região
UF_PARA_REGIAO: dict[str, str] = {}
for regiao, ufs in REGIOES.items():
    for uf in ufs:
        UF_PARA_REGIAO[uf] = regiao

# ---------------------------------------------------------------------------
# Mapeamento cod_uf → sigla  (útil para merge com GeoJSON do IBGE)
# ---------------------------------------------------------------------------
COD_UF_PARA_SIGLA: dict[int, str] = {
    info["cod_uf"]: sigla for sigla, info in ESTADOS.items()
}
SIGLA_PARA_COD_UF: dict[str, int] = {
    sigla: info["cod_uf"] for sigla, info in ESTADOS.items()
}

# ---------------------------------------------------------------------------
# Paleta de cores para os níveis de alerta do InfoDengue
# ---------------------------------------------------------------------------
CORES_NIVEL_ALERTA: dict[int, str] = {
    1: "#2ECC71",   # Verde — Baixo
    2: "#F1C40F",   # Amarelo — Atenção
    3: "#E67E22",   # Laranja — Alerta
    4: "#E74C3C",   # Vermelho — Emergência
}

LABELS_NIVEL_ALERTA: dict[int, str] = {
    1: "Verde — Baixo",
    2: "Amarelo — Atenção",
    3: "Laranja — Alerta",
    4: "Vermelho — Emergência",
}

# ---------------------------------------------------------------------------
# Paleta de cores customizadas para o dashboard
# ---------------------------------------------------------------------------
COR_PRIMARIA = "#E63946"       # Vermelho acentuado
COR_SECUNDARIA = "#457B9D"     # Azul aço
COR_DESTAQUE = "#1D3557"       # Azul escuro
COR_FUNDO = "#F1FAEE"          # Verde-água claro
COR_SUCESSO = "#2ECC71"        # Verde
COR_AVISO = "#F39C12"          # Laranja

# Escalas contínuas para Plotly
ESCALA_CALOR = "YlOrRd"        # Amarelo → Laranja → Vermelho
ESCALA_SEQUENCIAL = "Reds"     # Para mapas de incidência

# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------
INFODENGUE_BASE_URL = "https://info.dengue.mat.br/api/alertcity"
IBGE_LOCALIDADES_URL = "https://servicodados.ibge.gov.br/api/v1/localidades"
IBGE_MALHAS_URL = "https://servicodados.ibge.gov.br/api/v3/malhas"

# ---------------------------------------------------------------------------
# Nomes amigáveis das métricas
# ---------------------------------------------------------------------------
METRICAS: dict[str, str] = {
    "casos": "Casos Notificados",
    "casos_est": "Casos Estimados",
    "inc": "Taxa de Incidência",
    "rt": "Número Reprodutivo (Rt)",
    "nivel": "Nível de Alerta",
}

# ---------------------------------------------------------------------------
# Lista ordenada de siglas para exibição
# ---------------------------------------------------------------------------
LISTA_UFS: list[str] = sorted(ESTADOS.keys())
LISTA_UFS_NOMES: list[str] = [f"{s} — {ESTADOS[s]['nome']}" for s in LISTA_UFS]
