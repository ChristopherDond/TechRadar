import re
from collections import Counter

SKILLS_DB = [
    "Python", "JavaScript", "TypeScript", "Java", "Go", "Kotlin", "C#", "PHP",
    "Ruby", "Swift", "Rust", "Scala", "Elixir", "Dart", "R",
    "React", "Vue", "Angular", "Next.js", "Nuxt.js", "Svelte", "Flutter",
    "React Native", "Tailwind CSS",
    "Django", "FastAPI", "Flask", "Spring Boot", "Laravel", "Rails",
    "Express", "NestJS", "ASP.NET", "Gin",
    "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Terraform",
    "Jenkins", "GitHub Actions", "GitLab CI", "Datadog", "Grafana",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Kafka",
    "Elasticsearch", "DynamoDB", "RabbitMQ",
    "Git", "CI/CD", "REST API", "GraphQL", "Microservices", "gRPC",
    "Linux", "Agile", "Scrum", "SQL", "NoSQL",
    "TensorFlow", "PyTorch", "scikit-learn", "pandas", "NumPy",
    "Spark", "Airflow", "dbt", "Power BI", "Tableau",
    "Machine Learning", "Deep Learning", "MLOps",
    "OAuth", "JWT",
]


def extract_skills_from_text(text: str) -> list[str]:

    text_lower = text.lower()
    found = []
    for skill in SKILLS_DB:
        if skill.lower() in text_lower:
            found.append(skill)
    return sorted(set(found))


def analyze_resume(resume_text: str, df, target_nivel: str = "Pleno"):

    user_skills = extract_skills_from_text(resume_text)
    user_set = set(s.lower() for s in user_skills)

    df_target = df[df["nivel"] == target_nivel].copy()
    if df_target.empty:
        df_target = df.copy()

    def calc_match(skills_str):
        if not isinstance(skills_str, str):
            return 0.0
        vaga_skills = {s.strip().lower() for s in skills_str.split(",") if s.strip()}
        if not vaga_skills:
            return 0.0
        return len(user_set & vaga_skills) / len(vaga_skills)

    df_target["match"] = df_target["skills"].apply(calc_match)

    market_skills = Counter()
    for _, row in df_target.iterrows():
        if not isinstance(row["skills"], str):
            continue
        for s in row["skills"].split(","):
            s = s.strip()
            if s and s.lower() not in user_set:
                market_skills[s] += 1

    compatible = df_target[df_target["match"] >= 0.4]
    top_vagas = compatible.nlargest(10, "match")

    score = (len(compatible) / len(df_target) * 100) if len(df_target) > 0 else 0

    sal_esperado = compatible["salario"].mean() if not compatible.empty else 0
    sal_mercado = df_target["salario"].mean() if not df_target.empty else 0

    lang_compat = {}
    for lang in df_target["linguagem"].unique():
        df_lang = df_target[df_target["linguagem"] == lang]
        if not df_lang.empty:
            lang_compat[lang] = df_lang["match"].mean() * 100

    return {
        "score": score,
        "user_skills": user_skills,
        "missing_skills": market_skills.most_common(15),
        "compatible_count": len(compatible),
        "total_vagas": len(df_target),
        "sal_esperado": sal_esperado,
        "sal_mercado": sal_mercado,
        "top_vagas": top_vagas,
        "lang_compatibility": dict(sorted(lang_compat.items(), key=lambda x: -x[1])),
    }
