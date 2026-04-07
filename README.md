# 🦟 Dashboard Arboviroses Brasil

Dashboard interativo para análise e monitoramento de dados de saúde pública sobre **Dengue, Chikungunya e Zika** no Brasil.

Desenvolvido como Trabalho de Conclusão de Curso (TCC) da Especialização em Ciência de Dados do **IFTM — Campus Uberaba Parque Tecnológico**.

---

## 📋 Funcionalidades

| Página | Descrição |
|---|---|
| **Visão Geral** | KPIs nacionais, mapa coroplético por estado, evolução temporal e ranking |
| **Mapa Interativo** | Choropleth de estados com drill-down para municípios de um estado |
| **Série Temporal** | Evolução semanal, notificados vs. estimados, curva epidêmica e sazonalidade |
| **Comparativo Regional** | Ranking de estados, análise por macrorregião e heatmaps |
| **Análise Climática** | Correlação exploratória entre temperatura/umidade e casos |
| **Sobre** | Metodologia, tecnologias, referências, limitações e créditos |

## 📊 Escopo Dos Dados

- O seletor global permite alternar entre **Dengue**, **Chikungunya** e **Zika**.
- A visão nacional usa os **principais municípios por UF** (até 5 municípios por estado), não todos os municípios do Brasil.
- Esse recorte melhora a representatividade em relação a usar apenas capitais e mantém o tempo de carregamento viável para um dashboard interativo.
- Os totais devem ser lidos como um painel comparativo dos municípios consultados, não como o total oficial nacional.
- Algumas combinações de doença, município e período podem retornar poucos dados ou nenhum dado, conforme disponibilidade da API InfoDengue.

## 🛠️ Tecnologias

- **Python 3.11+**
- **Streamlit** — Framework do dashboard web
- **Plotly** — Gráficos interativos e mapas coropléticos
- **Pandas** — Processamento e análise de dados
- **Requests** — Consumo de APIs REST
- **NumPy** — Operações numéricas

## 📊 Fontes De Dados

- **[InfoDengue](https://info.dengue.mat.br)** (Fiocruz/FGV) — Dados epidemiológicos semanais, estimativas, alertas e variáveis climáticas
- **[API IBGE — Localidades](https://servicodados.ibge.gov.br/api/docs/localidades)** — Estados e municípios
- **[API IBGE — Malhas](https://servicodados.ibge.gov.br/api/docs/malhas)** — GeoJSON para mapas
- **População Estimada (IBGE 2024)** — Referência para métricas per capita

---

## 🚀 Como Executar

### Pré-requisitos

- Python 3.11 ou superior
- pip

### Instalação

```bash
# Clonar o repositório
git clone https://github.com/seu-usuario/dashboard-arboviroses-brasil.git
cd dashboard-arboviroses-brasil

# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente virtual no Windows
.venv\Scripts\activate

# Ativar ambiente virtual no Linux/Mac
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### Pré-download de dados geográficos (opcional)

```bash
python scripts/download_geojson.py
```

### Executar

```bash
streamlit run app.py
```

Acesse **http://localhost:8501** no navegador.

### Docker

```bash
docker build -t dashboard-arboviroses .
docker run -p 8501:8501 dashboard-arboviroses
```

---

## 🏗️ Estrutura Do Projeto

```text
├── app.py                    # Entrypoint + navegação multipágina
├── pages/
│   ├── 01_visao_geral.py     # KPIs + mapa + ranking
│   ├── 02_mapa.py            # Choropleth estados/municípios
│   ├── 03_serie_temporal.py  # Evolução temporal + sazonalidade
│   ├── 04_comparativo.py     # Ranking + heatmaps regionais
│   ├── 05_sobre.py           # Metodologia e créditos
│   └── 06_clima.py           # Análise climática
├── src/
│   ├── api_ibge.py           # Acesso à API do IBGE
│   ├── api_infodengue.py     # Acesso à API do InfoDengue
│   ├── data_processing.py    # Limpeza e transformação
│   ├── charts.py             # Gráficos Plotly
│   └── constants.py          # Configurações e mapeamentos
├── data/
│   └── geojson/              # GeoJSON offline (fallback)
├── tests/                    # Testes unitários
├── scripts/                  # Scripts auxiliares
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## 📝 Testes

```bash
python -m pytest -q
```

---

## 👤 Autor

**Guilherme José Morais Mutão**  
Pós-graduação — Especialização em Ciência de Dados  
IFTM — Campus Uberaba Parque Tecnológico

**Orientador:** Prof. Camilo de Lelis Tosta Paula

---

## 📄 Licença

Este projeto é de código aberto, desenvolvido para fins acadêmicos.
