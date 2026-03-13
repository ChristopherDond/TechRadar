# 📡 TechRadar — Brazilian Dev Job Market Intelligence

> Using Python to prove the market wants Python.

TechRadar is an interactive dashboard that scrapes real tech job listings in Brazil and turns them into actionable market intelligence — salary benchmarks, trending technologies, in-demand skills, and personalized employability insights.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-Database-3ECF8E?style=flat&logo=supabase&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-Interactive-3F4F75?style=flat&logo=plotly&logoColor=white)

---

## ✨ Features

### 📊 Salary Analysis
Average and median salary by language, box plots by level (Junior → Specialist), and a salary growth curve across career levels.

### 🔥 Market Demand
Tech stack rankings by number of openings, work modality breakdown (Remote / Hybrid / On-site), and top hiring companies.

### ☁️ Skills Word Cloud
Visual representation of the most requested skills overall and filtered by each language.

### 🔬 Cross Analysis
Heatmap of average salary by language × level, a bubble chart comparing demand vs. salary vs. dispersion, and auto-generated insights.

### 🎯 Employability Score
Select your current skills and get your compatibility percentage with real job openings, your expected salary range, and a ranked list of skills to learn next.

### ⚔️ Stack Comparator
Compare any two languages side by side — salaries across levels, job openings, remote distribution, exclusive vs. shared skills, and an automatic verdict on whether switching stacks is worth it financially.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Dashboard | Streamlit |
| Data viz | Plotly, Matplotlib, WordCloud |
| Data processing | pandas, NumPy |
| Database | Supabase (PostgreSQL) |
| Data collection | Gupy API (real job listings) |
| Hosting | Streamlit Cloud |

---

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/your-username/techradar.git
cd techradar
```

### 2. Create and activate virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
cp .env.example .env
```
Fill in your Supabase credentials in the `.env` file:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
```

### 5. Set up the database
Run `schema.sql` in your Supabase SQL Editor to create the table, indexes, and RLS policies.

### 6. Scrape real job data
```bash
python scraper.py
```
This will collect listings from 12 tech stacks via the Gupy API, save a local backup to `vagas_reais.csv`, and push everything to Supabase.

> **No Supabase?** No problem — the dashboard automatically falls back to a synthetic dataset so you can run it right away.

### 7. Run the dashboard
```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## ☁️ Deployment (Streamlit Cloud)

1. Push the project to a public GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Select your repo, branch `main`, and file `app.py`
4. Go to **Advanced settings → Secrets** and add:
```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-service-role-key"
```
5. Click **Deploy** — your public URL will be live in ~2 minutes.

---

## 📁 Project Structure

```
techradar/
├── app.py              # Main Streamlit dashboard (6 tabs)
├── scraper.py          # Gupy API scraper
├── database.py         # Supabase integration layer
├── generate_data.py    # Synthetic data fallback
├── schema.sql          # Supabase table + indexes + RLS
├── requirements.txt
├── .env.example
├── .gitignore
└── .streamlit/
    └── secrets.toml.example
```

---

## 💡 The Metalanguage Concept

The core idea behind TechRadar is **metalanguage**: Python being used to prove that the market demands Python.

After scraping and analyzing hundreds of real job listings, the data consistently confirms — Python ranks as the most demanded language and among the best paying ones in the Brazilian tech market.

---

## 🤝 Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.

---

## 📄 License

MIT License — feel free to use, modify, and distribute.