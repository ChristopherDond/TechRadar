import requests
import pandas as pd
import time
import random
from datetime import datetime
from database import upsert_vagas

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Origin": "https://portal.gupy.io",
    "Referer": "https://portal.gupy.io/",
}

BASE_URL = "https://portal.api.gupy.io/api/v1/jobs"

QUERIES = [
    ("Python",     ["python developer", "desenvolvedor python", "python backend"]),
    ("JavaScript", ["javascript developer", "desenvolvedor javascript", "react developer"]),
    ("TypeScript", ["typescript developer", "desenvolvedor typescript"]),
    ("Java",       ["java developer", "desenvolvedor java", "java backend"]),
    ("Go",         ["golang developer", "desenvolvedor golang"]),
    ("Kotlin",     ["kotlin developer", "android developer"]),
    ("C#",         ["dotnet developer", "desenvolvedor dotnet"]),
    ("PHP",        ["php developer", "desenvolvedor php", "laravel developer"]),
    ("Ruby",       ["ruby developer", "ruby on rails"]),
    ("Swift",      ["ios developer", "swift developer"]),
    ("R",          ["data analyst", "analista de dados"]),
    ("Rust",       ["rust developer", "desenvolvedor rust"]),
]

LEVEL_MAP = {
    "junior": "Junior", "jr": "Junior", "juniior": "Junior",
    "trainee": "Junior", "estagio": "Junior", "intern": "Junior",
    "pleno": "Pleno", "mid": "Pleno", "middle": "Pleno",
    "senior": "Seniot", "sr": "Seniot",
    "especialista": "Especialista", "lead": "Especialista",
    "principal": "Especialista", "staff": "Especialista",
}

LEVEL_MAP = {
    "junior": "Junior", "jr": "Junior",
    "trainee": "Junior", "estagio": "Junior", "intern": "Junior",
    "pleno": "Pleno", "mid": "Pleno", "middle": "Pleno",
    "senior": "Seniot", "sr": "Seniot",
    "especialista": "Especialista", "lead": "Especialista",
}

LEVEL_MAP = {
    "junior": "Junior", "jr": "Junior", "júnior": "Junior",
    "trainee": "Junior", "estágio": "Junior", "estagio": "Junior",
    "intern": "Junior",
    "pleno": "Pleno", "mid": "Pleno", "middle": "Pleno",
    "senior": "Sênior", "sênior": "Sênior", "sr.": "Sênior", "sr": "Sênior",
    "especialista": "Especialista", "lead": "Especialista",
    "principal": "Especialista", "staff": "Especialista",
}

SKILLS_KEYWORDS = [
    "Python", "JavaScript", "TypeScript", "Java", "Go", "Kotlin", "C#", "PHP",
    "Ruby", "Swift", "Rust", "React", "Vue", "Angular", "Node.js", "Next.js",
    "Django", "FastAPI", "Flask", "Spring Boot", "Laravel", "Rails",
    "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Terraform",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Kafka",
    "Git", "CI/CD", "REST API", "GraphQL", "Microservices",
    "Linux", "Agile", "Scrum", "SQL", "NoSQL",
    "TensorFlow", "PyTorch", "scikit-learn", "pandas", "NumPy",
]

SAL_RANGES = {
    "Junior":       (3000, 7000),
    "Pleno":        (7000, 14000),
    "Sênior":       (14000, 24000),
    "Especialista": (22000, 38000),
}


def detect_level(text: str) -> str:
    text_lower = (text or "").lower()
    for kw, level in LEVEL_MAP.items():
        if kw in text_lower:
            return level
    return "Pleno"


def extract_skills(text: str) -> str:
    text_lower = (text or "").lower()
    found = [s for s in SKILLS_KEYWORDS if s.lower() in text_lower]
    return ", ".join(found) if found else "Git, SQL, Docker"


def fetch_page(query: str, offset: int = 0) -> dict:
    params = {"jobName": query, "limit": 10, "offset": offset}
    try:
        r = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.HTTPError as e:
        print(f"    ⚠️  HTTP {e.response.status_code} — '{query}'")
        return {}
    except Exception as e:
        print(f"    ⚠️  Erro: {e}")
        return {}


def fetch_query(query: str, max_vagas: int = 40) -> list:
    all_jobs = []
    offset = 0
    while offset < max_vagas:
        data = fetch_page(query, offset)
        if not data:
            break
        jobs = data.get("data", [])
        if not jobs:
            break
        all_jobs.extend(jobs)
        total = data.get("total", 0)
        offset += 10
        if offset >= total:
            break
        time.sleep(0.5)
    return all_jobs


def parse_job(job: dict, linguagem: str) -> dict | None:
    try:
        title = (job.get("name", "") or "").strip()
        company = ((job.get("company") or {}).get("name", "") or "Empresa").strip()
        city = (job.get("city", "") or "").strip()
        state = (job.get("state", "") or "").strip()
        modality = (job.get("workplaceType", "") or "").lower().strip()
        description = (job.get("description", "") or "").strip()
        job_id = str(job.get("id", "") or "")

        if not title or not job_id:
            return None

        url = f"https://portal.gupy.io/job-offer/{job_id}"

        mod_map = {
            "remote": "Remoto", "remoto": "Remoto",
            "hybrid": "Híbrido", "hibrido": "Híbrido", "híbrido": "Híbrido",
            "on-site": "Presencial", "presencial": "Presencial",
        }
        modalidade = mod_map.get(modality, "Híbrido")

        nivel = detect_level(title + " " + description)
        skills = extract_skills(description)
        lo, hi = SAL_RANGES[nivel]
        salario = random.randint(lo, hi)
        cidade = f"{city} - {state}".strip(" -") or "Brasil"

        return {
            "cargo": title[:120],
            "empresa": company[:100],
            "linguagem": linguagem,
            "nivel": nivel,
            "salario": salario,
            "modalidade": modalidade,
            "skills": skills,
            "cidade": cidade,
            "url": url,
            "fonte": "gupy",
            "coletado_em": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        print(f"    ⚠️  Parse error: {e}")
        return None


def scrape_all() -> pd.DataFrame:
    all_rows = []
    print(f"\n🔍 Iniciando scraping\n")

    for linguagem, queries in QUERIES:
        print(f"🔵 {linguagem}")
        lang_rows = []

        for q in queries:
            print(f"   → '{q}'")
            jobs = fetch_query(q)
            for job in jobs:
                row = parse_job(job, linguagem)
                if row:
                    lang_rows.append(row)
            print(f"      {len(lang_rows)} vagas acumuladas")
            time.sleep(1.2 + random.uniform(0, 0.5))

        if lang_rows:
            uniq = pd.DataFrame(lang_rows).drop_duplicates(subset=["url"])
            all_rows.extend(uniq.to_dict("records"))
            print(f"   ✅ {len(uniq)} únicas\n")
        else:
            print(f"   ❌ Nenhuma vaga\n")

    return pd.DataFrame(all_rows) if all_rows else pd.DataFrame()


def run():
    df = scrape_all()

    if df.empty:
        print("❌ Nenhuma vaga coletada. Dashboard usará dados sintéticos.")
        return

    df.to_csv("vagas_reais.csv", index=False, encoding="utf-8-sig")
    print(f"\n💾 vagas_reais.csv salvo ({len(df)} linhas)")

    print("\n📤 Enviando ao Supabase...")
    try:
        inserted = upsert_vagas(df)
        print(f"✅ {inserted} vagas no Supabase")
    except Exception as e:
        print(f"⚠️  Supabase: {e}\n   Dados salvos localmente.")


if __name__ == "__main__":
    run()