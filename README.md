[Leia em Português (Brasil)](README-pt-br.md)

# 📡 TechRadar — Brazilian Dev Job Market Intelligence

> Using Python to prove the market wants Python.

TechRadar is an interactive dashboard that scrapes real tech job listings in Brazil and turns them into actionable market intelligence: salary benchmarks, stack demand, skill trends, and employability insights.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-Database-3ECF8E?style=flat&logo=supabase&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-Interactive-3F4F75?style=flat&logo=plotly&logoColor=white)

---

## ✨ Features

- Salary analysis by language and level.
- Demand analysis by stack, company, and work mode.
- Skills analysis with word cloud and ranking.
- Cross-analysis with insights (salary × demand).
- Resume analyzer.
- Stack comparator.
- Market trends tab (attractiveness + percentiles + career projection).
- Persistent Job Tracker (`job_tracker.json`).
- CSV export from the current filtered dataset.
- Quick market alert and collection time series.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Dashboard | Streamlit |
| Data viz | Plotly, Matplotlib, WordCloud |
| Data processing | pandas, NumPy |
| Database | Supabase (PostgreSQL) |
| Data collection | Multi-source scraping (Gupy, Programathor, Catho) |
| Testing | pytest |

---

## 🚀 Getting Started

### 1) Clone
```bash
git clone https://github.com/your-username/techradar.git
cd techradar
```

### 2) Create and activate virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3) Install dependencies
```bash
pip install -r requirements.txt
```

### 4) Configure environment
Create `.env` from `.env.example` and set:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
```

### 5) Scrape real job data
```bash
python scraper.py
```

### 6) Run dashboard
```bash
streamlit run app.py
```
Open `http://localhost:8501`.

---

## 📁 Project Structure

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

## 🧪 Tests

```bash
pytest -q
```

---

## 🤝 Contributing

Contributions are welcome via issues and pull requests.

---

## 📄 License

MIT License.
