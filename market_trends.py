import pandas as pd
import numpy as np

def calculate_market_trends(df: pd.DataFrame) -> dict:

    trends = {}

    for lang in df["linguagem"].unique():
        df_lang = df[df["linguagem"] == lang]
        n_vagas = len(df_lang)
        sal_medio = df_lang["salario"].mean()
        sal_mediana = df_lang["salario"].median()
        remote_pct = (df_lang["modalidade"] == "Remoto").mean() * 100
        n_empresas = df_lang["empresa"].nunique()

        demand_score = min(n_vagas / df["linguagem"].value_counts().max() * 100, 100)
        salary_score = min(sal_medio / df["salario"].max() * 100, 100)
        remote_score = remote_pct

        attractiveness = (demand_score * 0.4 + salary_score * 0.35 + remote_score * 0.25)

        from collections import Counter
        skills = Counter()
        for s_str in df_lang["skills"].dropna():
            for s in s_str.split(","):
                s = s.strip()
                if s and s != lang:
                    skills[s] += 1

        trends[lang] = {
            "vagas": n_vagas,
            "sal_medio": sal_medio,
            "sal_mediana": sal_mediana,
            "remote_pct": remote_pct,
            "n_empresas": n_empresas,
            "attractiveness": attractiveness,
            "demand_score": demand_score,
            "salary_score": salary_score,
            "remote_score": remote_score,
            "top_skills": skills.most_common(8),
        }

    return trends


def get_salary_percentiles(df: pd.DataFrame, lang: str) -> dict:

    data = df[df["linguagem"] == lang]["salario"]
    if data.empty:
        return {}
    return {
        "p10": np.percentile(data, 10),
        "p25": np.percentile(data, 25),
        "p50": np.percentile(data, 50),
        "p75": np.percentile(data, 75),
        "p90": np.percentile(data, 90),
        "mean": data.mean(),
        "std": data.std(),
    }


def generate_career_projection(df: pd.DataFrame, lang: str) -> list[dict]:

    levels = ["Junior", "Pleno", "Sênior", "Especialista"]
    projections = []

    for level in levels:
        subset = df[(df["linguagem"] == lang) & (df["nivel"] == level)]
        if not subset.empty:
            projections.append({
                "nivel": level,
                "sal_medio": subset["salario"].mean(),
                "sal_min": subset["salario"].min(),
                "sal_max": subset["salario"].max(),
                "vagas": len(subset),
            })

    return projections