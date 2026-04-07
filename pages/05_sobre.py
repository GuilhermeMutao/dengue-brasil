"""
Página: Sobre o Projeto — Metodologia, créditos e referências.
"""

import streamlit as st

st.title("ℹ️ Sobre o Projeto")

st.divider()

# ---------------------------------------------------------------------------
# Descrição
# ---------------------------------------------------------------------------
st.markdown("""
## Desenvolvimento de um Dashboard Interativo para Análise e Monitoramento de Dados de Saúde Pública: Um Estudo de Caso sobre Arboviroses no Brasil

Este dashboard foi desenvolvido como **Trabalho de Conclusão de Curso (TCC)** da
Pós-graduação — Especialização em Ciência de Dados do **Instituto Federal de Educação,
Ciência e Tecnologia do Triângulo Mineiro (IFTM) — Campus Uberaba Parque Tecnológico**.

---

### 🎯 Objetivo

Desenvolver um dashboard interativo para a visualização e análise de dados históricos
e atuais sobre **arboviroses** (Dengue, Chikungunya e Zika) no Brasil, facilitando o
monitoramento das doenças e a geração de *insights* por parte de seus usuários.

---

### 📊 Metodologia

A abordagem da pesquisa é **quantitativa**, baseada na análise de **dados secundários**
públicos. O projeto se caracteriza como pesquisa aplicada com desenvolvimento de um
produto tecnológico.

**Fontes de dados:**
- **[InfoDengue](https://info.dengue.mat.br)** — Sistema de monitoramento de arboviroses
  da Fiocruz e FGV. Fornece dados semanais por município para Dengue, Chikungunya e
  Zika, incluindo casos notificados, casos estimados por nowcasting, intervalo de
  incerteza, nível de alerta, número reprodutivo (Rt), incidência e variáveis climáticas.
- **[API IBGE — Localidades](https://servicodados.ibge.gov.br/api/docs/localidades)** —
  lista de estados e municípios com geocódigos usados nas consultas.
- **[API IBGE — Malhas](https://servicodados.ibge.gov.br/api/docs/malhas)** —
  GeoJSON para mapas coropléticos.
- **População Estimada (IBGE 2024)** — referência populacional para métricas per capita.

**Recorte e agregação:**
- A visão nacional usa os **principais municípios por UF** (até 5 municípios por estado)
  como recorte de análise. Essa escolha melhora a cobertura em relação a usar apenas
  capitais e mantém o tempo de carregamento viável para um dashboard interativo.
- O recorte não representa todos os municípios do Brasil. Portanto, os totais devem ser
  interpretados como um painel comparativo dos municípios consultados, não como o total
  oficial nacional.
- Nas páginas com drill-down municipal, o usuário pode consultar uma amostra maior de
  municípios do estado, limitada por desempenho e disponibilidade da API.

**Casos notificados vs. estimados:**
- Casos notificados são os registros já recebidos.
- Casos estimados usam nowcasting da InfoDengue para reduzir o impacto de atrasos de
  notificação, principalmente nas semanas epidemiológicas mais recentes.
- Quando disponíveis, `casos_est_min` e `casos_est_max` são exibidos como faixa de
  incerteza, indicando a cautela necessária na leitura da tendência.

**Pipeline de dados:**

```
API InfoDengue → Coleta (requests) → Limpeza (Pandas) → Análise → Visualização (Plotly) → Dashboard (Streamlit)
```

---

### 🛠️ Tecnologias Utilizadas

| Tecnologia | Versão | Uso |
|---|---|---|
| **Python** | 3.11+ | Linguagem principal |
| **Streamlit** | ≥ 1.40 | Framework do dashboard web |
| **Plotly** | ≥ 5.24 | Gráficos interativos e mapas |
| **Pandas** | ≥ 2.2 | Processamento e análise de dados |
| **Requests** | ≥ 2.32 | Consumo de APIs REST |
| **NumPy** | ≥ 1.26 | Operações numéricas |

---

### 📐 Arquitetura da Aplicação

```
app.py                    ← Entrypoint + navegação multipágina
├── pages/
│   ├── 01_visao_geral    ← KPIs nacionais + mapa + ranking
│   ├── 02_mapa           ← Choropleth estados/municípios
│   ├── 03_serie_temporal ← Evolução temporal + curva epidêmica + média móvel
│   ├── 04_comparativo    ← Ranking + heatmaps regionais
│   ├── 05_sobre          ← Esta página
│   └── 06_clima          ← Análise de correlação climática
├── src/
│   ├── api_ibge          ← Acesso à API do IBGE
│   ├── api_infodengue    ← Acesso à API do InfoDengue
│   ├── data_processing   ← Limpeza e transformação
│   ├── charts            ← Criação de gráficos Plotly
│   └── constants         ← Configurações e mapeamentos
└── data/
    └── geojson/          ← GeoJSON offline (fallback)
```

---

### ✨ Funcionalidades

| Funcionalidade | Descrição |
|---|---|
| **Multi-doença** | Suporte a Dengue, Chikungunya e Zika via seletor global |
| **Visão Geral** | 8+ KPIs nacionais, gauge de nível de alerta, P(Rt > 1) |
| **Mapa Interativo** | Choropleth por estados e drill-down para municípios |
| **Série Temporal** | Evolução de casos com média móvel, variação semanal |
| **Curva Epidêmica** | Sobreposição anual (SE 1–52) para comparação entre anos |
| **Comparativo Regional** | Rankings absolutos e per capita, heatmaps |
| **Análise Climática** | Correlação temperatura/umidade × casos (Pearson) |
| **Métricas populacionais** | Casos por 100k hab., % nacional, razão est./notif. |
| **Exportação** | Download de dados em CSV em todas as páginas |

---

### ⚠️ Limitações

- A qualidade da análise depende diretamente da qualidade dos dados públicos,
  que podem apresentar **subnotificação** ou atrasos.
- A visão nacional usa os **principais municípios por UF**, não todos os municípios do
  Brasil. Isso é um trade-off entre representatividade, tempo de resposta e uso responsável
  da API.
- Algumas combinações de doença, município e período podem retornar poucos dados ou
  nenhum dado, especialmente para doenças com menor disponibilidade histórica em
  determinados locais.
- O projeto **não inclui modelo preditivo**, focando em análise descritiva e visual
  (escopo para trabalhos futuros).
- A correlação climática apresentada é **exploratória** e não implica causalidade.

---

### 👤 Autor

**Guilherme José Morais Mutão**

Pós-graduação — Especialização em Ciência de Dados
IFTM — Campus Uberaba Parque Tecnológico

**Orientador:** Prof. Camilo de Lelis Tosta Paula

---

### 📚 Referências Bibliográficas

1. BRASIL. Ministério da Saúde. Secretaria de Vigilância em Saúde. *Monitoramento dos
   casos de arboviroses urbanas transmitidas pelo Aedes Aegypti (dengue, chikungunya e zika)*.
   Boletim Epidemiológico, v. 54, n. 1, p. 1-75, 2023.

2. CAIRO, Alberto. *The Truthful Art: Data, Charts, and Maps for Communication*.
   San Francisco: New Riders, 2016.

3. FEW, Stephen. *Information Dashboard Design: Displaying Data for At-a-Glance
   Monitoring*. 2. ed. Burlingame: Analytics Press, 2013.

4. FUNDAÇÃO OSWALDO CRUZ (FIOCRUZ). *InfoDengue: Sistema de Alerta de
   Arboviroses*. Rio de Janeiro, 2025. Disponível em: https://info.dengue.mat.br.

5. MCKINNEY, Wes. *Python para Análise de Dados: Tratamento de Dados com Pandas,
   NumPy e IPython*. 2. ed. São Paulo: Novatec Editora, 2018.

6. TEIXEIRA, Maurício G. et al. Dengue: trinta anos de história no Brasil.
   *Ciência & Saúde Coletiva*, v. 20, n. 3, p. 671-674, 2015.

---
""")

st.caption("Dashboard Arboviroses Brasil · IFTM · 2025")
