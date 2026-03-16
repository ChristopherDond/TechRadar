import pytest
import pandas as pd

from scraper import extract_salary, detect_level, extract_skills


class TestExtractSalary:

    def test_range_brl(self):
        text = "Salário: R$ 5.000,00 a R$ 10.000,00"
        result = extract_salary(text, "Pleno")
        assert 5000 <= result <= 10000

    def test_single_value(self):
        text = "Remuneração: R$ 8.500"
        result = extract_salary(text, "Pleno")
        assert 7000 <= result <= 9000

    def test_no_salary_uses_fallback(self):
        text = "Vaga para desenvolvedor Python com experiência"
        result = extract_salary(text, "Sênior")

        assert 15000 <= result <= 21000

    def test_empty_text(self):
        result = extract_salary("", "Junior")
        assert result > 0

    def test_ignores_tiny_values(self):
        text = "R$ 50 de vale refeição e R$ 12.000 salário"
        result = extract_salary(text, "Pleno")
        assert result >= 500


class TestDetectLevel:

    def test_junior(self):
        assert detect_level("Desenvolvedor Junior Python") == "Junior"

    def test_senior(self):
        assert detect_level("Senior Backend Developer") == "Sênior"

    def test_senior_accent(self):
        assert detect_level("Desenvolvedor Sênior") == "Sênior"

    def test_pleno(self):
        assert detect_level("Dev Pleno Java") == "Pleno"

    def test_specialist(self):
        assert detect_level("Tech Lead de Engenharia") == "Especialista"

    def test_default_pleno(self):
        assert detect_level("Desenvolvedor de Software") == "Pleno"

    def test_trainee_is_junior(self):
        assert detect_level("Trainee de Tecnologia") == "Junior"


class TestExtractSkills:

    def test_basic_extraction(self):
        text = "Experiência com Python, Django, Docker e AWS"
        skills = extract_skills(text)
        assert "Python" in skills
        assert "Django" in skills
        assert "Docker" in skills

    def test_empty_text(self):
        result = extract_skills("")
        assert result == "Git, SQL"

    def test_case_insensitive(self):
        text = "experiência com python e docker"
        skills = extract_skills(text)
        assert "Python" in skills
        assert "Docker" in skills

from resume_analyzer import extract_skills_from_text, analyze_resume


class TestResumeAnalyzer:

    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame([
            {"linguagem": "Python", "nivel": "Pleno", "salario": 10000,
             "modalidade": "Remoto", "skills": "Python, Django, Docker, AWS",
             "cargo": "Dev Python", "empresa": "TechCo"},
            {"linguagem": "Java", "nivel": "Pleno", "salario": 12000,
             "modalidade": "Híbrido", "skills": "Java, Spring Boot, Docker, Kubernetes",
             "cargo": "Dev Java", "empresa": "BigCorp"},
            {"linguagem": "Python", "nivel": "Pleno", "salario": 11000,
             "modalidade": "Remoto", "skills": "Python, FastAPI, PostgreSQL, Git",
             "cargo": "Backend Dev", "empresa": "StartupX"},
        ])

    def test_extract_skills_from_text(self):
        text = "Tenho 3 anos de experiência com Python, Django, Docker e AWS"
        skills = extract_skills_from_text(text)
        assert "Python" in skills
        assert "Django" in skills

    def test_analyze_resume_returns_score(self, sample_df):
        resume = "Desenvolvedor Python com experiência em Django, Docker, AWS e Git"
        result = analyze_resume(resume, sample_df, "Pleno")
        assert "score" in result
        assert "user_skills" in result
        assert "missing_skills" in result
        assert result["score"] >= 0

    def test_empty_resume(self, sample_df):
        result = analyze_resume("", sample_df, "Pleno")
        assert result["score"] == 0 or len(result["user_skills"]) == 0

from market_trends import calculate_market_trends, get_salary_percentiles, generate_career_projection


class TestMarketTrends:

    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame([
            {"linguagem": "Python", "nivel": "Junior", "salario": 5000,
             "modalidade": "Remoto", "skills": "Python, Git", "empresa": "A"},
            {"linguagem": "Python", "nivel": "Pleno", "salario": 10000,
             "modalidade": "Remoto", "skills": "Python, Django", "empresa": "B"},
            {"linguagem": "Python", "nivel": "Sênior", "salario": 18000,
             "modalidade": "Híbrido", "skills": "Python, Docker", "empresa": "C"},
            {"linguagem": "Java", "nivel": "Pleno", "salario": 11000,
             "modalidade": "Presencial", "skills": "Java, Spring Boot", "empresa": "D"},
        ])

    def test_calculate_trends(self, sample_df):
        trends = calculate_market_trends(sample_df)
        assert "Python" in trends
        assert "Java" in trends
        assert trends["Python"]["vagas"] == 3
        assert trends["Python"]["attractiveness"] > 0

    def test_salary_percentiles(self, sample_df):
        perc = get_salary_percentiles(sample_df, "Python")
        assert perc["p50"] > 0
        assert perc["p10"] <= perc["p90"]

    def test_career_projection(self, sample_df):
        proj = generate_career_projection(sample_df, "Python")
        assert len(proj) >= 1
        assert all("sal_medio" in p for p in proj)

    def test_empty_language(self, sample_df):
        perc = get_salary_percentiles(sample_df, "Rust")
        assert perc == {}
