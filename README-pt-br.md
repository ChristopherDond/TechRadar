[Read in English](README.md)

# 📡 TechRadar — Inteligência de Mercado Dev no Brasil

> Usando Python para provar que o mercado quer Python.

O TechRadar é um dashboard interativo que coleta vagas reais de tecnologia no Brasil e transforma os dados em inteligência prática: faixas salariais, demanda por stack, tendências de skills e insights de empregabilidade.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-Database-3ECF8E?style=flat&logo=supabase&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-Interactive-3F4F75?style=flat&logo=plotly&logoColor=white)

---

## ✨ Funcionalidades

- Análise salarial por linguagem e nível.
- Análise de demanda por stack, empresa e modalidade.
- Análise de skills com nuvem de palavras e ranking.
- Análise cruzada com insights automáticos (salário × demanda).
- Analisador de currículo.
- Comparador de stacks.
- Aba de tendências (atratividade + percentis + projeção de carreira).
- Job Tracker persistente (`job_tracker.json`).
- Exportação CSV dos dados filtrados.
- Alerta rápido de mercado e série temporal de coleta.

---

## 🛠️ Stack Técnica

| Camada | Tecnologia |
|---|---|
| Dashboard | Streamlit |
| Visualização | Plotly, Matplotlib, WordCloud |
| Processamento de dados | pandas, NumPy |
| Banco de dados | Supabase (PostgreSQL) |
| Coleta de dados | Scraping multi-fonte (Gupy, Programathor, Catho) |
| Testes | pytest |

---

## 🚀 Como executar

### 1) Clonar
```bash
git clone https://github.com/your-username/techradar.git
cd techradar
```

### 2) Criar e ativar ambiente virtual
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3) Instalar dependências
```bash
pip install -r requirements.txt
```

### 4) Configurar ambiente
Crie `.env` a partir de `.env.example` e defina:
```env
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-service-role-key
```

### 5) Coletar vagas reais
```bash
python scraper.py
```

### 6) Rodar dashboard
```bash
streamlit run app.py
```
Abra `http://localhost:8501`.

---

## 📁 Estrutura do projeto

```text
techradar/
├── app.py
├── app_features.py
├── new_tabs.py
├── scraper.py
├── database.py
├── market_trends.py
├── resume_analyzer.py
├── vagas_reais.csv
├── requirements.txt
├── .env.example
└── tests/
```

---

## 🧪 Testes

```bash
pytest -q
```

---

## 🤝 Contribuindo

Contribuições são bem-vindas via issues e pull requests.

---

## 📄 Licença

MIT License.
