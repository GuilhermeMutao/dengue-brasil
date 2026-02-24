# 🦟 Dashboard Dengue Brasil

Dashboard interativo para análise e monitoramento de dados de saúde pública sobre a **Dengue no Brasil**.

Desenvolvido como Trabalho de Conclusão de Curso (TCC) da Especialização em Ciência de Dados do **IFTM — Campus Uberaba Parque Tecnológico**.

---

## 📋 Funcionalidades

| Página | Descrição |
|---|---|
| **Visão Geral** | KPIs nacionais, mapa coroplético por estado, evolução temporal e ranking |
| **Mapa Interativo** | Choropleth de estados com drill-down para municípios de um estado |
| **Série Temporal** | Evolução semanal com comparação entre estados e análise de sazonalidade |
| **Comparativo Regional** | Ranking de estados, análise por macrorregião e heatmaps |
| **Sobre** | Metodologia, tecnologias, referências e créditos |

## 🛠️ Tecnologias

- **Python 3.11+**
- **Streamlit** — Framework do dashboard web
- **Plotly** — Gráficos interativos e mapas coropléticos
- **Pandas** — Processamento e análise de dados
- **Requests** — Consumo de APIs REST

## 📊 Fontes de Dados

- **[InfoDengue](https://info.dengue.mat.br)** (Fiocruz/FGV) — Dados epidemiológicos semanais
- **[API IBGE — Localidades](https://servicodados.ibge.gov.br/api/docs/localidades)** — Estados e municípios
- **[API IBGE — Malhas](https://servicodados.ibge.gov.br/api/docs/malhas)** — GeoJSON para mapas

---

## 🚀 Como Executar

### Pré-requisitos

- Python 3.11 ou superior
- pip

### Instalação

```bash
# Clonar o repositório
git clone https://github.com/seu-usuario/dashboard-dengue-brasil.git
cd dashboard-dengue-brasil

# Criar ambiente virtual
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate   # Linux/Mac

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
docker build -t dashboard-dengue .
docker run -p 8501:8501 dashboard-dengue
```

---

## 🏗️ Estrutura do Projeto

```
├── app.py                    # Entrypoint + navegação multipágina
├── pages/
│   ├── 01_visao_geral.py     # KPIs + mapa + ranking
│   ├── 02_mapa.py            # Choropleth estados/municípios
│   ├── 03_serie_temporal.py  # Evolução temporal + sazonalidade
│   ├── 04_comparativo.py     # Ranking + heatmaps regionais
│   └── 05_sobre.py           # Metodologia e créditos
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
python -m pytest tests/ -v
```

---

## 👤 Autor

**Guilherme José Morais Mutão**  
Pós-graduação — Especialização em Ciência de Dados  
IFTM — Campus Uberaba Parque Tecnológico

**Orientador:** Prof. Dr. Ernani Viriato De Melo

---

## 📄 Licença

Este projeto é de código aberto, desenvolvido para fins acadêmicos.
"# dengue-brasil" 
