import requests
import pandas as pd
import re
import time
import random
import sys
from datetime import datetime
from bs4 import BeautifulSoup
from database import upsert_vagas

HEADERS_JSON = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Origin": "https://portal.gupy.io",
    "Referer": "https://portal.gupy.io/",
}

HEADERS_HTML = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.7",
}

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
    ("Swift",      ["ios developer", "swift developer"]),
    ("R",          ["data analyst", "analista de dados", "cientista de dados"]),
    ("Rust",       ["rust developer", "desenvolvedor rust"]),
]

QUERIES_SHORT = [
    ("Python",     ["python", "django", "fastapi"]),
    ("JavaScript", ["react", "javascript", "node.js"]),
    ("TypeScript", ["typescript", "angular"]),
    ("Java",       ["java", "spring boot"]),
    ("Go",         ["golang"]),
    ("Kotlin",     ["kotlin", "android"]),
    ("C#",         [".net", "c#"]),
    ("PHP",        ["php", "laravel"]),
    ("Ruby",       ["ruby on rails"]),
    ("Swift",      ["ios developer"]),
    ("R",          ["data analyst"]),
    ("Rust",       ["rust developer"]),
]

LEVEL_KEYWORDS = {
    "Especialista": [
        ("especialista", 10), ("lead", 9), ("principal", 9), ("staff", 9),
        ("tech lead", 10), ("arquiteto", 8), ("architect", 8), ("head", 7),
    ],
    "Seniot": [
        ("seniot", 10), ("senior", 10), ("sr.", 9), ("sr ", 9), ("experiente", 5),
    ],
    "Pleno": [
        ("pleno", 10), ("mid", 8), ("middle", 8), ("mid-level", 9),
        ("intermediario", 8),
    ],
    "Junior": [
        ("junior", 10), ("jr.", 9), ("jr ", 9),
        ("trainee", 9), ("estagio", 8), ("intern", 9), ("aprendiz", 8),
    ],
}

LEVEL_KEYWORDS = {
    "Especialista": [
        ("especialista", 10), ("lead", 9), ("principal", 9), ("staff", 9),
        ("tech lead", 10), ("arquiteto", 8), ("head", 7),
    ],
    "Sênior": [
        ("sênior", 10), ("senior", 10), ("sr.", 9), ("sr ", 9), ("experiente", 5),
    ],
    "Pleno": [
        ("pleno", 10), ("mid", 8), ("middle", 8), ("mid-level", 9),
        ("intermediário", 8), ("intermediario", 8),
    ],
    "Junior": [
        ("junior", 10), ("júnior", 10), ("jr.", 9), ("jr ", 9),
        ("trainee", 9), ("estágio", 8), ("estagio", 8), ("intern", 9),
    ],
}

SKILLS_KEYWORDS = {
    "Python", "JavaScript", "TypeScript", "Java", "Go", "Kotlin", "C#", "PHP",
    "Ruby", "Swift", "Rust", "Scala", "Elixir", "Dart", "R",
    "React", "Vue", "Angular", "Next.js", "Nuxt.js", "Svelte", "Flutter",
    "React Native", "Tailwind CSS",
    "Django", "FastAPI", "Flask", "Spring Boot", "Laravel", "Rails",
    "Express", "NestJS", "ASP.NET", "Gin",
    "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Terraform",
    "Ansible", "Jenkins", "GitHub Actions", "GitLab CI",
    "Datadog", "Grafana", "Prometheus",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Kafka",
    "Elasticsearch", "DynamoDB", "Cassandra", "RabbitMQ", "Celery",
    "Git", "CI/CD", "REST API", "GraphQL", "Microservices", "gRPC",
    "Linux", "Agile", "Scrum", "SQL", "NoSQL",
    "TensorFlow", "PyTorch", "scikit-learn", "pandas", "NumPy",
    "Spark", "Airflow", "dbt", "Power BI", "Tableau",
    "Machine Learning", "Deep Learning", "MLOps",
}

SAL_REFERENCE = {
    "Junior":       {"median": 4800},
    "Pleno":        {"median": 10000},
    "Sênior":       {"median": 18000},
    "Especialista": {"median": 28000},
}

SALARY_PATTERNS = [
    re.compile(r"R\$\s*([\d]{1,3}(?:\.?\d{3})*(?:,\d{2})?)\s*(?:a|ate|ate|-|)\s*R?\$?\s*([\d]{1,3}(?:\.?\d{3})*(?:,\d{2})?)", re.IGNORECASE),
    re.compile(r"(?:salario|remuneracao)\s*:?\s*R?\$?\s*([\d]{1,3}(?:\.?\d{3})*(?:,\d{2})?)", re.IGNORECASE),
    re.compile(r"R\$\s*([\d]{1,3}(?:\.?\d{3})*(?:,\d{2})?)", re.IGNORECASE),
]


def _parse_brl(s):
    try:
        return float(s.replace(".", "").replace(",", "."))
    except Exception:
        return 0.0


def extract_salary(text, nivel):
    if text:
        for pattern in SALARY_PATTERNS:
            m = pattern.search(text)
            if m:
                g = m.groups()
                if len(g) >= 2:
                    lo, hi = _parse_brl(g[0]), _parse_brl(g[1])
                    if lo > 500 and hi > 500:
                        return int((lo + hi) / 2)
                elif len(g) == 1:
                    v = _parse_brl(g[0])
                    if v > 500:
                        return int(v)
    median = SAL_REFERENCE.get(nivel, SAL_REFERENCE["Pleno"])["median"]
    return int(median * random.uniform(0.85, 1.15))


def detect_level(text):
    text_lower = (text or "").lower()
    scores = {lvl: 0 for lvl in LEVEL_KEYWORDS}
    for level, keywords in LEVEL_KEYWORDS.items():
        for keyword, weight in keywords:
            if keyword in text_lower:
                scores[level] += weight
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Pleno"


def extract_skills(text):
    if not text:
        return "Git, SQL"
    text_lower = text.lower()
    found = [s for s in SKILLS_KEYWORDS if s.lower() in text_lower]
    return ", ".join(sorted(set(found))) if found else "Git, SQL"


def _row(cargo, empresa, linguagem, nivel, salario, modalidade, skills, cidade, url, fonte):
    return {
        "cargo": str(cargo)[:120],
        "empresa": str(empresa)[:100],
        "linguagem": linguagem,
        "nivel": nivel,
        "salario": salario,
        "modalidade": modalidade,
        "skills": skills,
        "cidade": str(cidade)[:100],
        "url": str(url),
        "fonte": fonte,
        "coletado_em": datetime.utcnow().isoformat(),
    }

def _gupy_page(query, offset=0):
    try:
        r = requests.get(
            "https://portal.api.gupy.io/api/v1/jobs",
            params={"jobName": query, "limit": 10, "offset": offset},
            headers=HEADERS_JSON, timeout=15
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"    gupy err: {e}")
        return {}


def _gupy_query(query, max_vagas=60):
    jobs, offset = [], 0
    while offset < max_vagas:
        data = _gupy_page(query, offset)
        if not data:
            break
        page = data.get("data", [])
        if not page:
            break
        jobs.extend(page)
        offset += 10
        if offset >= data.get("total", 0):
            break
        time.sleep(0.5)
    return jobs


def _gupy_parse(job, linguagem):
    try:
        title = (job.get("name", "") or "").strip()
        company = ((job.get("company") or {}).get("name", "") or "Empresa").strip()
        city = (job.get("city", "") or "").strip()
        state = (job.get("state", "") or "").strip()
        modality = (job.get("workplaceType", "") or "").lower()
        description = (job.get("description", "") or "").strip()
        job_id = str(job.get("id", "") or "")
        if not title or not job_id:
            return None
        mod_map = {
            "remote": "Remoto", "remoto": "Remoto",
            "hybrid": "Híbrido", "hibrido": "Híbrido",
            "on-site": "Presencial", "presencial": "Presencial",
        }
        full_text = f"{title} {description}"
        nivel = detect_level(full_text)
        return _row(title, company, linguagem, nivel,
                    extract_salary(description, nivel),
                    mod_map.get(modality, "Híbrido"),
                    extract_skills(full_text),
                    f"{city} - {state}".strip(" -") or "Brasil",
                    f"https://portal.gupy.io/job-offer/{job_id}",
                    "gupy")
    except Exception as e:
        print(f"    gupy parse: {e}")
        return None


def scrape_gupy():
    rows = []
    print("\n🟣 GUPY")
    for linguagem, queries in QUERIES:
        print(f"  🔵 {linguagem}")
        lang = []
        for q in queries:
            print(f"     → '{q}'")
            for job in _gupy_query(q):
                row = _gupy_parse(job, linguagem)
                if row:
                    lang.append(row)
            time.sleep(1.2 + random.uniform(0, 0.5))
        if lang:
            uniq = pd.DataFrame(lang).drop_duplicates(subset=["url"])
            rows.extend(uniq.to_dict("records"))
            print(f"     ✅ {len(uniq)} únicas")
        else:
            print(f"     ❌ Nenhuma")
    return rows

PT_BASE = "https://programathor.com.br"

PT_SLUGS = [
    ("Python",     ["/jobs-python", "/jobs-django", "/jobs-fastapi"]),
    ("JavaScript", ["/jobs-javascript", "/jobs-react", "/jobs-nodejs"]),
    ("TypeScript", ["/jobs-typescript"]),
    ("Java",       ["/jobs-java", "/jobs-spring"]),
    ("Go",         ["/jobs-go", "/jobs-golang"]),
    ("Kotlin",     ["/jobs-kotlin", "/jobs-android"]),
    ("C#",         ["/jobs-dotnet", "/jobs-csharp"]),
    ("PHP",        ["/jobs-php", "/jobs-laravel"]),
    ("Ruby",       ["/jobs-ruby"]),
    ("Swift",      ["/jobs-ios", "/jobs-swift"]),
    ("R",          ["/jobs-data-science"]),
    ("Rust",       ["/jobs-rust"]),
]


def _pt_fetch(slug, page=1):
    try:
        r = requests.get(f"{PT_BASE}{slug}?page={page}", headers=HEADERS_HTML, timeout=15)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        print(f"    programathor err ({slug}): {e}")
        return None


def _pt_parse(card, linguagem):
    try:
        title_el = card.select_one("h2, h3, .job-title, [class*='title']")
        title = title_el.get_text(strip=True) if title_el else ""

        company_el = card.select_one("[class*='company'], [class*='empresa']")
        company = company_el.get_text(strip=True) if company_el else "Empresa"

        link_el = card.select_one("a[href]")
        href = link_el["href"] if link_el else ""
        url = href if href.startswith("http") else f"{PT_BASE}{href}"

        if not title or not url or url == PT_BASE:
            return None

        location_el = card.select_one("[class*='location'], [class*='cidade']")
        loc = (location_el.get_text(strip=True) if location_el else "").lower()
        if "remot" in loc:
            mod = "Remoto"
        elif "hibrid" in loc or "híbrid" in loc:
            mod = "Híbrido"
        else:
            mod = "Presencial"

        full_text = card.get_text(" ", strip=True)
        nivel = detect_level(full_text)
        return _row(title, company, linguagem, nivel,
                    extract_salary(full_text, nivel), mod,
                    extract_skills(full_text),
                    loc[:80] or "Brasil", url, "programathor")
    except Exception as e:
        print(f"    programathor parse: {e}")
        return None


def scrape_programathor(max_pages=3):
    rows = []
    print("\n🟠 PROGRAMATHOR")
    for linguagem, slugs in PT_SLUGS:
        print(f"  🔵 {linguagem}")
        lang = []
        for slug in slugs:
            for page in range(1, max_pages + 1):
                soup = _pt_fetch(slug, page)
                if not soup:
                    break
                cards = (
                    soup.select(".job-card")
                    or soup.select("[class*='job-item']")
                    or soup.select("article")
                    or soup.select(".list-jobs li")
                )
                if not cards:
                    break
                for card in cards:
                    row = _pt_parse(card, linguagem)
                    if row:
                        lang.append(row)
                time.sleep(1.0 + random.uniform(0, 0.5))
        if lang:
            uniq = pd.DataFrame(lang).drop_duplicates(subset=["url"])
            rows.extend(uniq.to_dict("records"))
            print(f"     ✅ {len(uniq)} únicas")
        else:
            print(f"     ❌ Nenhuma")
    return rows

INDEED_BASE = "https://br.indeed.com"


def _indeed_fetch(query, start=0):
    try:
        r = requests.get(
            f"{INDEED_BASE}/jobs",
            params={"q": query, "l": "Brasil", "start": start},
            headers=HEADERS_HTML, timeout=15
        )
        r.raise_for_status()
        return BeautifulSoup(r.text, "lxml")
    except Exception as e:
        print(f"    indeed err ('{query}'): {e}")
        return None


def _indeed_parse(card, linguagem):
    try:
        title_el = (
            card.select_one("[class*='jobTitle'] a")
            or card.select_one("h2 a")
            or card.select_one(".title a")
        )
        if not title_el:
            return None
        title = title_el.get_text(strip=True)

        href = title_el.get("href", "")
        url = href if href.startswith("http") else f"{INDEED_BASE}{href}"

        company_el = card.select_one("[class*='companyName'], .company")
        company = company_el.get_text(strip=True) if company_el else "Empresa"

        loc_el = card.select_one("[class*='companyLocation'], .location")
        loc = (loc_el.get_text(strip=True) if loc_el else "").lower()

        if "remot" in loc or "home office" in loc:
            mod = "Remoto"
        elif "híbrid" in loc or "hibrid" in loc:
            mod = "Híbrido"
        else:
            mod = "Presencial"

        snippet_el = card.select_one("[class*='snippet'], .summary")
        snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""
        full_text = f"{title} {snippet}"

        nivel = detect_level(full_text)
        return _row(title, company, linguagem, nivel,
                    extract_salary(full_text, nivel), mod,
                    extract_skills(full_text),
                    loc[:80] or "Brasil", url, "indeed")
    except Exception as e:
        print(f"    indeed parse: {e}")
        return None


def scrape_indeed(max_pages=3):
    rows = []
    print("\n🟡 CATHO")
    for linguagem, queries in QUERIES_SHORT:
        print(f"  🔵 {linguagem}")
        lang = []
        for q in queries:
            print(f"     → '{q}'")
            try:
                url = f"https://www.catho.com.br/vagas/{q.replace(' ', '-')}/"
                r = requests.get(url, headers=HEADERS_HTML, timeout=15)
                if r.status_code != 200:
                    continue
                soup = BeautifulSoup(r.text, "html.parser")
                cards = (
                    soup.select("[class*='JobCard']")
                    or soup.select("[class*='job-card']")
                    or soup.select("article")
                )
                for card in cards:
                    title_el = card.select_one("h2, h3, [class*='title']")
                    title = title_el.get_text(strip=True) if title_el else ""
                    company_el = card.select_one("[class*='company'], [class*='empresa']")
                    company = company_el.get_text(strip=True) if company_el else "Empresa"
                    link_el = card.select_one("a[href]")
                    href = link_el["href"] if link_el else ""
                    url_vaga = href if href.startswith("http") else f"https://www.catho.com.br{href}"
                    if not title or not href:
                        continue
                    full_text = card.get_text(" ", strip=True)
                    nivel = detect_level(full_text)
                    lang.append(_row(title, company, linguagem, nivel,
                                     extract_salary(full_text, nivel),
                                     "Híbrido", extract_skills(full_text),
                                     "Brasil", url_vaga, "catho"))
                time.sleep(1.5 + random.uniform(0, 0.5))
            except Exception as e:
                print(f"    catho err: {e}")
        if lang:
            uniq = pd.DataFrame(lang).drop_duplicates(subset=["url"])
            rows.extend(uniq.to_dict("records"))
            print(f"     ✅ {len(uniq)} únicas")
        else:
            print(f"     ❌ Nenhuma")
    return rows

def scrape_all(sources=None):
    if sources is None:
        sources = ["gupy", "programathor", "indeed"]

    source_map = {
        "gupy":         scrape_gupy,
        "programathor": scrape_programathor,
        "indeed":       scrape_indeed,
    }

    print(f"\n🔍 TechRadar — Multi-source scraper")
    print(f"   Fontes: {', '.join(sources)}\n")

    all_rows = []
    for source in sources:
        if source not in source_map:
            print(f"⚠️  Fonte desconhecida: {source}")
            continue
        try:
            result = source_map[source]()
            all_rows.extend(result)
            print(f"   → {source}: {len(result)} vagas")
        except Exception as e:
            print(f"   ❌ Erro em {source}: {e}")

    if not all_rows:
        return pd.DataFrame()

    df = pd.DataFrame(all_rows).drop_duplicates(subset=["url"]).reset_index(drop=True)

    print(f"\n📊 Total consolidado: {len(df)} vagas únicas")
    for fonte, count in df["fonte"].value_counts().items():
        print(f"   · {fonte}: {count}")

    return df


def run():
    sources = None
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg == "--source" and i + 1 < len(args):
            sources = [args[i + 1]]
        elif arg.startswith("--source="):
            sources = [arg.split("=", 1)[1]]

    df = scrape_all(sources)

    if df.empty:
        print("\n❌ Nenhuma vaga coletada.")
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