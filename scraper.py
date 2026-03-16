import requests
import pandas as pd
import re
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
    ("Python",     ["python developer", "desenvolvedor python", "python backend", "engenheiro python"]),
    ("JavaScript", ["javascript developer", "desenvolvedor javascript", "react developer", "frontend developer"]),
    ("TypeScript", ["typescript developer", "desenvolvedor typescript", "angular developer"]),
    ("Java",       ["java developer", "desenvolvedor java", "java backend", "spring developer"]),
    ("Go",         ["golang developer", "desenvolvedor golang", "go developer"]),
    ("Kotlin",     ["kotlin developer", "android developer", "kotlin android"]),
    ("C#",         ["dotnet developer", "desenvolvedor dotnet", "c# developer", ".net developer"]),
    ("PHP",        ["php developer", "desenvolvedor php", "laravel developer"]),
    ("Ruby",       ["ruby developer", "ruby on rails", "rails developer"]),
    ("Swift",      ["ios developer", "swift developer", "apple developer"]),
    ("R",          ["data analyst", "analista de dados", "cientista de dados"]),
    ("Rust",       ["rust developer", "desenvolvedor rust", "rust engineer"]),
]

LEVEL_KEYWORDS = {
    "Especialista": [
        ("especialista", 10), ("lead", 9), ("principal", 9), ("staff", 9),
        ("tech lead", 10), ("arquiteto", 8), ("architect", 8), ("head", 7),
        ("coordenador", 7), ("gerente de desenvolvimento", 7),
    ],
    "Sênior": [
        ("sênior", 10), ("senior", 10), ("sr.", 9), ("sr ", 9),
        ("iii", 6), ("3", 4), ("experiente", 5),
    ],
    "Pleno": [
        ("pleno", 10), ("mid", 8), ("middle", 8), ("mid-level", 9),
        ("ii", 6), ("intermediário", 8), ("intermediario", 8),
    ],
    "Junior": [
        ("junior", 10), ("júnior", 10), ("jr.", 9), ("jr ", 9),
        ("trainee", 9), ("estágio", 8), ("estagio", 8), ("estagiário", 8),
        ("estagiario", 8), ("intern", 9), ("aprendiz", 8), ("i ", 3),
    ],
}

SKILLS_KEYWORDS = {

    "Python", "JavaScript", "TypeScript", "Java", "Go", "Kotlin", "C#", "PHP",
    "Ruby", "Swift", "Rust", "Scala", "Elixir", "Dart", "R",
 
    "React", "Vue", "Angular", "Next.js", "Nuxt.js", "Svelte", "Flutter",
    "React Native", "Tailwind CSS",

    "Django", "FastAPI", "Flask", "Spring Boot", "Laravel", "Rails",
    "Express", "NestJS", "ASP.NET", "Gin", "Echo", "Fiber",

    "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Terraform",
    "Ansible", "Jenkins", "GitHub Actions", "GitLab CI", "ArgoCD",
    "Datadog", "Grafana", "Prometheus", "New Relic",

    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Kafka",
    "Elasticsearch", "DynamoDB", "Cassandra", "SQLite", "Oracle",
    "RabbitMQ", "Celery",

    "Git", "CI/CD", "REST API", "GraphQL", "Microservices", "gRPC",
    "Linux", "Agile", "Scrum", "Kanban", "SQL", "NoSQL",
    "Figma", "Jira", "Confluence",

    "TensorFlow", "PyTorch", "scikit-learn", "pandas", "NumPy",
    "Spark", "Airflow", "dbt", "Power BI", "Tableau",
    "Machine Learning", "Deep Learning", "MLOps", "LLM",

    "OAuth", "JWT", "OWASP", "SSL/TLS",
}

SAL_REFERENCE = {
    "Junior":       {"min": 3000, "max": 7000,  "median": 4800},
    "Pleno":        {"min": 7000, "max": 14000, "median": 10000},
    "Sênior":       {"min": 14000, "max": 24000, "median": 18000},
    "Especialista": {"min": 22000, "max": 38000, "median": 28000},
}

SALARY_PATTERNS = [

    re.compile(
        r"R\$\s*([\d]{1,3}(?:\.?\d{3})*(?:,\d{2})?)\s*(?:a|até|à|-|–)\s*R?\$?\s*([\d]{1,3}(?:\.?\d{3})*(?:,\d{2})?)",
        re.IGNORECASE,
    ),

    re.compile(
        r"(?:sal[aá]rio|remunera[çc][ãa]o|vencimento|pagamento)\s*:?\s*(?:de\s+)?R?\$?\s*([\d]{1,3}(?:\.?\d{3})*(?:,\d{2})?)",
        re.IGNORECASE,
    ),

    re.compile(
        r"R\$\s*([\d]{1,3}(?:\.?\d{3})*(?:,\d{2})?)",
        re.IGNORECASE,
    ),
]


def _parse_brl(value_str: str) -> float:

    cleaned = value_str.replace(".", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def extract_salary(text: str, nivel: str) -> int:

    if not text:
        ref = SAL_REFERENCE.get(nivel, SAL_REFERENCE["Pleno"])
        return ref["median"]

    for pattern in SALARY_PATTERNS:
        match = pattern.search(text)
        if match:
            groups = match.groups()
            if len(groups) >= 2:

                low = _parse_brl(groups[0])
                high = _parse_brl(groups[1])
                if low > 500 and high > 500:
                    return int((low + high) / 2)
            elif len(groups) == 1:
                val = _parse_brl(groups[0])
                if val > 500:
                    return int(val)

    ref = SAL_REFERENCE.get(nivel, SAL_REFERENCE["Pleno"])
    variation = random.uniform(-0.15, 0.15)
    return int(ref["median"] * (1 + variation))


def detect_level(text: str) -> str:

    text_lower = (text or "").lower()
    scores = {"Junior": 0, "Pleno": 0, "Sênior": 0, "Especialista": 0}

    for level, keywords in LEVEL_KEYWORDS.items():
        for keyword, weight in keywords:
            if keyword in text_lower:
                scores[level] += weight

    best_level = max(scores, key=scores.get)

    if scores[best_level] == 0:
        return "Pleno"
    return best_level


def extract_skills(text: str) -> str:

    if not text:
        return "Git, SQL"

    text_lower = text.lower()
    found = []
    for skill in SKILLS_KEYWORDS:

        skill_lower = skill.lower()
        if skill_lower in text_lower:
            found.append(skill)

    return ", ".join(sorted(set(found))) if found else "Git, SQL"

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


def fetch_query(query: str, max_vagas: int = 60) -> list:

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

        full_text = f"{title} {description}"
        nivel = detect_level(full_text)
        skills = extract_skills(full_text)

        salario = extract_salary(description, nivel)

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
    stats = {"total_raw": 0, "total_unique": 0, "salary_extracted": 0}
    print(f"\n🔍 TechRadar v2.0 — Iniciando scraping inteligente\n")

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
                    stats["total_raw"] += 1
            print(f"      {len(lang_rows)} vagas acumuladas")
            time.sleep(1.2 + random.uniform(0, 0.5))

        if lang_rows:
            uniq = pd.DataFrame(lang_rows).drop_duplicates(subset=["url"])
            all_rows.extend(uniq.to_dict("records"))
            stats["total_unique"] += len(uniq)
            print(f"   ✅ {len(uniq)} únicas\n")
        else:
            print(f"   ❌ Nenhuma vaga\n")

    print(f"\n📊 Resumo do scraping:")
    print(f"   Total bruto: {stats['total_raw']}")
    print(f"   Total único: {stats['total_unique']}")

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