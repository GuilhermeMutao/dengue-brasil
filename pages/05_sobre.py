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
## Desenvolvimento de um Dashboard Interativo para Análise e Monitoramento de Dados de Saúde Pública: Um Estudo de Caso sobre a Dengue no Brasil

Este dashboard foi desenvolvido como **Trabalho de Conclusão de Curso (TCC)** da
Pós-graduação — Especialização em Ciência de Dados do **Instituto Federal de Educação,
Ciência e Tecnologia do Triângulo Mineiro (IFTM) — Campus Uberaba Parque Tecnológico**.

---

### 🎯 Objetivo

Desenvolver um dashboard interativo para a visualização e análise de dados históricos
e atuais sobre a Dengue no Brasil, facilitando o monitoramento da doença e a geração
de *insights* por parte de seus usuários.

---

### 📊 Metodologia

A abordagem da pesquisa é **quantitativa**, baseada na análise de **dados secundários**
públicos. O projeto se caracteriza como pesquisa aplicada com desenvolvimento de um
produto tecnológico.

**Fonte de dados principal:**
- **[InfoDengue](https://info.dengue.mat.br)** — Sistema de monitoramento de arboviroses
  da Fiocruz e FGV. Fornece dados semanais por município com estimativas de casos,
  nível de alerta, número reprodutivo (Rt) e taxa de incidência.

**Fontes complementares:**
- **[API IBGE — Localidades](https://servicodados.ibge.gov.br/api/docs/localidades)** —
  Lista de estados e municípios com geocódigos.
- **[API IBGE — Malhas](https://servicodados.ibge.gov.br/api/docs/malhas)** —
  GeoJSON para mapas coropléticos.

**Pipeline de dados:**

```
API InfoDengue → Coleta (requests) → Limpeza (Pandas) → Visualização (Plotly) → Dashboard (Streamlit)
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
│   ├── 03_serie_temporal ← Evolução temporal + sazonalidade
│   ├── 04_comparativo    ← Ranking + heatmaps regionais
│   └── 05_sobre          ← Esta página
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

### ⚠️ Limitações

- A qualidade da análise depende diretamente da qualidade dos dados públicos,
  que podem apresentar **subnotificação** ou atrasos.
- Para a visão nacional, os dados são baseados nas **27 capitais estaduais** como
  proxy para cada estado (trade-off entre velocidade e abrangência).
- O projeto **não inclui modelo preditivo**, focando em análise descritiva e visual.
- Não são correlacionados dados climáticos ou socioeconômicos
  (escopo para trabalhos futuros).

---

### 👤 Autor

**Guilherme José Morais Mutão**

Pós-graduação — Especialização em Ciência de Dados  
IFTM — Campus Uberaba Parque Tecnológico

**Orientador:** Prof. Dr. Ernani Viriato De Melo

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

st.caption("Dashboard Dengue Brasil · IFTM · 2025")
