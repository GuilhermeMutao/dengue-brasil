"""
Constantes globais do Dashboard Arboviroses Brasil.

Mapeamentos de UFs, regiões, geocodes de capitais, paleta de cores
e configurações padrão da aplicação.
"""

from datetime import datetime as _dt

# ---------------------------------------------------------------------------
# Configurações da aplicação
# ---------------------------------------------------------------------------
APP_TITLE = "Dashboard Arboviroses Brasil"
APP_ICON = "🦟"
APP_LAYOUT = "wide"

ANO_MINIMO = 2010
ANO_MAXIMO = _dt.now().year
DOENCA_PADRAO = "dengue"

# ---------------------------------------------------------------------------
# Doenças monitoradas
# ---------------------------------------------------------------------------
DOENCAS: dict[str, dict[str, str]] = {
    "dengue": {"nome": "Dengue", "icone": "🦟", "prefixo": "dengue"},
    "chikungunya": {"nome": "Chikungunya", "icone": "🤒", "prefixo": "chikungunya"},
    "zika": {"nome": "Zika", "icone": "🧬", "prefixo": "zika"},
}

NOMES_DOENCA: dict[str, str] = {codigo: info["nome"] for codigo, info in DOENCAS.items()}
ICONES_DOENCA: dict[str, str] = {codigo: info["icone"] for codigo, info in DOENCAS.items()}
PREFIXOS_ARQUIVO_DOENCA: dict[str, str] = {
    codigo: info["prefixo"] for codigo, info in DOENCAS.items()
}
LABELS_DOENCA: dict[str, str] = {
    codigo: f"{info['icone']} {info['nome']}" for codigo, info in DOENCAS.items()
}


def obter_nome_doenca(doenca: str | None) -> str:
    """Retorna o nome amigável da doença com fallback seguro."""
    return NOMES_DOENCA.get(doenca or DOENCA_PADRAO, NOMES_DOENCA[DOENCA_PADRAO])


def obter_icone_doenca(doenca: str | None) -> str:
    """Retorna o ícone da doença com fallback seguro."""
    return ICONES_DOENCA.get(doenca or DOENCA_PADRAO, ICONES_DOENCA[DOENCA_PADRAO])


def obter_prefixo_doenca(doenca: str | None) -> str:
    """Retorna o prefixo de arquivos exportados com fallback seguro."""
    return PREFIXOS_ARQUIVO_DOENCA.get(
        doenca or DOENCA_PADRAO,
        PREFIXOS_ARQUIVO_DOENCA[DOENCA_PADRAO],
    )


def mensagem_sem_dados_doenca(doenca: str | None) -> str:
    """Mensagem padronizada para cenários sem retorno da API InfoDengue."""
    nome = obter_nome_doenca(doenca)
    return (
        f"⚠️ Não foi possível obter dados de {nome} para o período selecionado. "
        "Algumas arboviroses podem ter disponibilidade limitada na API InfoDengue "
        "para determinados municípios, estados ou anos."
    )

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
    "inc": "Incidência (por 100 mil hab.)",
    "casos_por_100k": "Casos por 100 mil hab.",
    "pct_nacional": "% do Total Nacional",
    "rt": "Número Reprodutivo (Rt)",
    "nivel": "Nível de Alerta",
    "taxa_est_notif": "Razão Estimado / Notificado",
    "diferenca_est_notif": "Diferença Estimado - Notificado",
    "pct_ajuste_estimativa": "% de Ajuste da Estimativa",
    "faixa_incerteza": "Faixa de Incerteza",
    "incerteza_pct": "% de Incerteza",
    "populacao": "População Estimada",
}

# Métricas disponíveis para mapas e filtros
METRICAS_MAPA: list[str] = [
    "casos", "casos_est", "inc", "casos_por_100k", "pct_nacional", "taxa_est_notif",
]

# Leituras alternativas para heatmaps de sazonalidade.
ESCALAS_HEATMAP_SAZONAL: dict[str, str] = {
    "relativa_ano": "Relativa ao pico do ano",
    "log": "Logarítmica",
    "percentil_95": "Corte por percentil 95",
    "absoluta": "Absoluta",
}

# ---------------------------------------------------------------------------
# População estimada dos estados (IBGE 2024)
# ---------------------------------------------------------------------------
POPULACAO_ESTADOS: dict[str, int] = {
    "AC": 936_000,
    "AL": 3_360_000,
    "AM": 4_287_000,
    "AP": 901_000,
    "BA": 14_986_000,
    "CE": 9_240_000,
    "DF": 3_095_000,
    "ES": 4_109_000,
    "GO": 7_206_000,
    "MA": 7_154_000,
    "MG": 21_412_000,
    "MS": 2_866_000,
    "MT": 3_784_000,
    "PA": 8_777_000,
    "PB": 4_059_000,
    "PE": 9_674_000,
    "PI": 3_289_000,
    "PR": 11_597_000,
    "RJ": 17_503_000,
    "RN": 3_560_000,
    "RO": 1_815_000,
    "RR": 715_000,
    "RS": 11_473_000,
    "SC": 7_610_000,
    "SE": 2_348_000,
    "SP": 46_650_000,
    "TO": 1_607_000,
}

# ---------------------------------------------------------------------------
# Top 5 municípios mais populosos por estado (geocodes IBGE)
# Usado para obter nível de alerta representativo do estado, não apenas capital
# Fonte: IBGE Estimativas Populacionais 2024
# ---------------------------------------------------------------------------
TOP_MUNICIPIOS_POR_UF: dict[str, list[int]] = {
    "AC": [1200401, 1200302, 1200336, 1200013, 1200179],  # Rio Branco, Cruzeiro do Sul, Sena Madureira, Acrelândia, Feijó
    "AL": [2704302, 2700300, 2706307, 2701407, 2704906],  # Maceió, Arapiraca, Palmeira dos Índios, Penedo, Rio Largo
    "AM": [1302603, 1303403, 1301902, 1304062, 1302504],  # Manaus, Parintins, Itacoatiara, Manacapuru, Maués
    "AP": [1600303, 1600600, 1600154, 1600105, 1600204],  # Macapá, Santana, Laranjal do Jari, Amapá, Calçoene
    "BA": [2927408, 2910800, 2930709, 2919553, 2905701],  # Salvador, Feira de Santana, Vitória da Conquista, Lauro de Freitas, Camaçari
    "CE": [2304400, 2307304, 2303709, 2305233, 2309607],  # Fortaleza, Juazeiro do Norte, Caucaia, Maracanaú, Sobral
    "DF": [5300108],  # Brasília (DF = município único)
    "ES": [3205309, 3205002, 3201308, 3205200, 3201209],  # Vitória, Serra, Cariacica, Vila Velha, Cachoeiro de Itapemirim
    "GO": [5208707, 5201405, 5200050, 5209903, 5219753],  # Goiânia, Aparecida de Goiânia, Águas Lindas de Goiás, Luziânia, Trindade
    "MA": [2111300, 2105302, 2102002, 2104305, 2109106],  # São Luís, Imperatriz, Caxias, Codó, Paço do Lumiar
    "MG": [3106200, 3106705, 3118601, 3170206, 3136702],  # Belo Horizonte, Betim, Contagem, Uberlândia, Juiz de Fora
    "MS": [5002704, 5003702, 5002505, 5006309, 5007109],  # Campo Grande, Dourados, Corumbá, Ponta Porã, Três Lagoas
    "MT": [5103403, 5108402, 5106224, 5103700, 5107602],  # Cuiabá, Rondonópolis, Sinop, Várzea Grande, Tangará da Serra
    "PA": [1501402, 1500800, 1504422, 1505536, 1502400],  # Belém, Ananindeua, Marabá, Parauapebas, Castanhal
    "PB": [2507507, 2504009, 2513901, 2503704, 2509602],  # João Pessoa, Campina Grande, Santa Rita, Cabedelo, Patos
    "PE": [2611606, 2607901, 2609600, 2604106, 2610707],  # Recife, Jaboatão dos Guararapes, Olinda, Cabo de Santo Agostinho, Paulista
    "PI": [2211001, 2207702, 2202208, 2205003, 2203503],  # Teresina, Parnaíba, Campo Maior, Floriano, Corrente
    "PR": [4106902, 4113700, 4104808, 4115200, 4108304],  # Curitiba, Londrina, Cascavel, Maringá, Foz do Iguaçu
    "RJ": [3304557, 3302858, 3301009, 3303302, 3303500],  # Rio de Janeiro, Duque de Caxias, Belford Roxo, Niterói, Nova Iguaçu
    "RN": [2408102, 2407104, 2410004, 2408003, 2404002],  # Natal, Mossoró, Parnamirim, Macaíba, Ceará-Mirim
    "RO": [1100205, 1100304, 1100114, 1100023, 1101005],  # Porto Velho, Ji-Paraná, Cacoal, Ariquemes, Vilhena
    "RR": [1400100, 1400027, 1400050, 1400159, 1400175],  # Boa Vista, Caracaraí, Alto Alegre, Cantá, Pacaraima
    "RS": [4314902, 4303905, 4309209, 4304606, 4307708],  # Porto Alegre, Caxias do Sul, Gravataí, Canoas, Esteio
    "SC": [4205407, 4209102, 4204202, 4208203, 4211306],  # Florianópolis, Joinville, Criciúma, Itajaí, Lages
    "SE": [2800308, 2804102, 2803609, 2802700, 2802106],  # Aracaju, Lagarto, Itabaiana, Estância, Capela
    "SP": [3550308, 3518800, 3509502, 3547809, 3534401],  # São Paulo, Guarulhos, Campinas, Santo André, Osasco
    "TO": [1721000, 1702109, 1710508, 1716109, 1718204],  # Palmas, Araguaína, Gurupi, Porto Nacional, Paraíso do Tocantins
}

# ---------------------------------------------------------------------------
# Lista ordenada de siglas para exibição
# ---------------------------------------------------------------------------
LISTA_UFS: list[str] = sorted(ESTADOS.keys())
LISTA_UFS_NOMES: list[str] = [f"{s} — {ESTADOS[s]['nome']}" for s in LISTA_UFS]

# Total da população brasileira estimada
POPULACAO_BRASIL: int = sum(POPULACAO_ESTADOS.values())

# Lista de regiões para filtro
LISTA_REGIOES: list[str] = sorted(REGIOES.keys())
