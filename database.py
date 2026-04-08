import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()


def _get_env(key: str) -> str:
    value = os.getenv(key, "")
    if not value:
        try:
            import streamlit as st
            value = st.secrets.get(key, "")
        except Exception:
            pass
    return value


SUPABASE_URL = _get_env("SUPABASE_URL")
SUPABASE_KEY = _get_env("SUPABASE_KEY")
TABLE = "vagas"


def _fetch_paged(query, page_size: int = 1000, max_rows: int = 20000) -> pd.DataFrame:
    all_rows = []

    for start in range(0, max_rows, page_size):
        end = start + page_size - 1
        result = query.range(start, end).execute()
        batch = result.data or []
        if not batch:
            break

        all_rows.extend(batch)
        if len(batch) < page_size:
            break

    return pd.DataFrame(all_rows)


def get_client():
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError(
            "❌ Variáveis SUPABASE_URL e SUPABASE_KEY não configuradas.\n"
            "   Copie o arquivo .env.example para .env e preencha."
        )
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def upsert_vagas(df: pd.DataFrame) -> int:
    client = get_client()

    cols = ["cargo", "empresa", "linguagem", "nivel", "salario",
            "modalidade", "skills", "cidade", "url", "fonte", "coletado_em"]

    cols_to_send = [c for c in cols if c in df.columns]
    records = df[cols_to_send].to_dict("records")

    batch_size = 200
    total = 0

    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        try:
            client.table(TABLE).upsert(batch, on_conflict="url").execute()
            total += len(batch)
            print(f"  📦 Lote {i//batch_size + 1}: {len(batch)} registros")
        except Exception as e:
            print(f"  ⚠️  Erro no lote {i//batch_size + 1}: {e}")

    return total


def fetch_vagas(
    linguagens: list[str] | None = None,
    niveis: list[str] | None = None,
    modalidades: list[str] | None = None,
    sal_min: int = 0,
    sal_max: int = 999999,
) -> pd.DataFrame:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return _fallback_data()

    try:
        client = get_client()
        query = (
            client.table(TABLE)
            .select("*")
            .gte("salario", sal_min)
            .lte("salario", sal_max)
        )

        if linguagens:
            query = query.in_("linguagem", linguagens)
        if niveis:
            query = query.in_("nivel", niveis)
        if modalidades:
            query = query.in_("modalidade", modalidades)

        df = _fetch_paged(query)

        if df.empty:
            print("⚠️  Supabase retornou vazio — usando fallback")
            return _fallback_data()

        return df

    except Exception as e:
        print(f"⚠️  Erro Supabase: {e} — usando fallback")
        return _fallback_data()


def fetch_all_vagas() -> pd.DataFrame:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return _fallback_data()

    try:
        client = get_client()
        query = client.table(TABLE).select("*")
        df = _fetch_paged(query)
        return df if not df.empty else _fallback_data()
    except Exception as e:
        print(f"⚠️  Supabase indisponível: {e}")
        return _fallback_data()


def _fallback_data() -> pd.DataFrame:
    csv_path = Path(__file__).with_name("vagas_reais.csv")

    if csv_path.exists():
        print("📂 Usando vagas_reais.csv")
        try:
            df = pd.read_csv(csv_path)
        except Exception as exc:
            print(f"⚠️  Falha ao ler {csv_path.name}: {exc}")
            return _generate_synthetic_data()

        required_cols = ["cargo", "empresa", "linguagem", "nivel", "salario", "modalidade", "skills"]
        for col in required_cols:
            if col not in df.columns:
                df[col] = "N/A" if col != "salario" else 0
        return df

    print("🔧 Usando dataset sintético (rode scraper.py para dados reais)")
    return _generate_synthetic_data()


def _generate_synthetic_data() -> pd.DataFrame:

    import random
    import numpy as np

    langs = {
        "Python":     {"base": 9000,  "growth": 1.45, "remote_pct": 0.75},
        "JavaScript": {"base": 7500,  "growth": 1.40, "remote_pct": 0.65},
        "TypeScript": {"base": 8500,  "growth": 1.42, "remote_pct": 0.70},
        "Java":       {"base": 9500,  "growth": 1.38, "remote_pct": 0.55},
        "Go":         {"base": 12000, "growth": 1.50, "remote_pct": 0.80},
        "Kotlin":     {"base": 8800,  "growth": 1.40, "remote_pct": 0.60},
        "C#":         {"base": 8200,  "growth": 1.35, "remote_pct": 0.50},
        "PHP":        {"base": 6500,  "growth": 1.30, "remote_pct": 0.55},
        "Ruby":       {"base": 10000, "growth": 1.48, "remote_pct": 0.85},
        "Swift":      {"base": 9200,  "growth": 1.42, "remote_pct": 0.65},
        "R":          {"base": 7200,  "growth": 1.35, "remote_pct": 0.45},
        "Rust":       {"base": 14000, "growth": 1.55, "remote_pct": 0.82},
    }

    levels = ["Junior", "Pleno", "Sênior", "Especialista"]
    level_multi = {"Junior": 0.55, "Pleno": 1.0, "Sênior": 1.6, "Especialista": 2.2}
    modalities = ["Remoto", "Híbrido", "Presencial"]

    skills_pool = {
        "Python": "Python, Django, FastAPI, Flask, Docker, AWS, PostgreSQL, Git, CI/CD, Linux, pandas, NumPy",
        "JavaScript": "JavaScript, React, Vue, Node.js, Next.js, Docker, AWS, MongoDB, Git, CI/CD, REST API",
        "TypeScript": "TypeScript, React, Angular, Next.js, Node.js, Docker, AWS, PostgreSQL, Git, CI/CD",
        "Java": "Java, Spring Boot, Docker, Kubernetes, AWS, PostgreSQL, MySQL, Kafka, Git, CI/CD, Microservices",
        "Go": "Go, Docker, Kubernetes, AWS, PostgreSQL, Redis, Kafka, Git, CI/CD, gRPC, Microservices",
        "Kotlin": "Kotlin, Java, Android, Docker, AWS, Firebase, Git, CI/CD, REST API, Agile",
        "C#": "C#, ASP.NET, Docker, Azure, SQL, Git, CI/CD, REST API, Microservices, Agile",
        "PHP": "PHP, Laravel, Docker, MySQL, Redis, Git, CI/CD, REST API, Linux, Vue",
        "Ruby": "Ruby, Rails, Docker, AWS, PostgreSQL, Redis, Sidekiq, Git, CI/CD, REST API",
        "Swift": "Swift, iOS, Xcode, Docker, AWS, Firebase, Git, CI/CD, REST API, Agile",
        "R": "R, Python, SQL, Power BI, Tableau, pandas, NumPy, scikit-learn, Git, Agile",
        "Rust": "Rust, Docker, Kubernetes, AWS, PostgreSQL, Redis, Git, CI/CD, Linux, gRPC",
    }

    empresas = [
        "Nubank", "iFood", "Mercado Livre", "PagSeguro", "Stone", "Itaú",
        "XP Inc.", "BTG Pactual", "Globo", "TOTVS", "Locaweb", "Zup Innovation",
        "CI&T", "ThoughtWorks", "Loft", "QuintoAndar", "Wildlife Studios",
        "Vtex", "RD Station", "Hotmart", "PicPay", "C6 Bank", "Inter",
    ]

    cargos = {
        "Junior": ["Dev Jr", "Desenvolvedor(a) Junior", "Junior Developer", "Analista Jr"],
        "Pleno": ["Dev Pleno", "Desenvolvedor(a) Pleno", "Software Engineer", "Analista Pleno"],
        "Sênior": ["Dev Sênior", "Senior Developer", "Senior Engineer", "Tech Lead"],
        "Especialista": ["Staff Engineer", "Especialista", "Principal Engineer", "Arquiteto de Software"],
    }

    rows = []
    np.random.seed(42)

    for lang, cfg in langs.items():
        n_vagas = random.randint(25, 70)
        for _ in range(n_vagas):
            nivel = random.choices(levels, weights=[0.2, 0.35, 0.30, 0.15])[0]
            base = cfg["base"] * level_multi[nivel]
            salario = int(base * random.uniform(0.85, 1.15))

            r = random.random()
            if r < cfg["remote_pct"]:
                mod = "Remoto"
            elif r < cfg["remote_pct"] + 0.15:
                mod = "Híbrido"
            else:
                mod = "Presencial"

            cargo_prefix = random.choice(cargos[nivel])
            cargo = f"{cargo_prefix} {lang}"

            all_skills = skills_pool[lang].split(", ")
            n_skills = random.randint(3, min(8, len(all_skills)))
            selected = random.sample(all_skills, n_skills)

            rows.append({
                "cargo": cargo,
                "empresa": random.choice(empresas),
                "linguagem": lang,
                "nivel": nivel,
                "salario": salario,
                "modalidade": mod,
                "skills": ", ".join(selected),
                "cidade": random.choice(["São Paulo - SP", "Rio de Janeiro - RJ", "Belo Horizonte - MG",
                                        "Curitiba - PR", "Porto Alegre - RS", "Florianópolis - SC",
                                        "Recife - PE", "Brasil"]),
                "url": f"https://techradar.demo/vaga/{lang.lower()}-{random.randint(1000,9999)}",
                "fonte": "synthetic",
                "coletado_em": "2026-03-16T00:00:00",
            })

    return pd.DataFrame(rows)


def get_stats() -> dict:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return {"total": 0, "fonte": "sintético", "ultima_coleta": "N/A"}

    try:
        client = get_client()
        result = client.table(TABLE).select("coletado_em", count="exact").order("coletado_em", desc=True).limit(1).execute()
        ultima = result.data[0]["coletado_em"][:10] if result.data else "N/A"
        return {"total": result.count, "fonte": "Gupy (real)", "ultima_coleta": ultima}
    except Exception:
        return {"total": 0, "fonte": "erro", "ultima_coleta": "N/A"}
