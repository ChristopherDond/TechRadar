from database import _fallback_data
from market_trends import calculate_market_trends
from resume_analyzer import extract_skills_from_text
from app_features import build_market_alert, build_collection_timeseries
from scraper import (
    normalize_level,
    normalize_modalidade,
    normalize_skills,
    deduplicate_rows,
)

def test_fallback_data_nao_vazio():
    df = _fallback_data()
    assert len(df) > 0

def test_fallback_colunas():
    df = _fallback_data()
    for col in ["cargo", "empresa", "linguagem", "nivel", "salario"]:
        assert col in df.columns

def test_extract_skills():
    skills = extract_skills_from_text("Experiência com Python, Docker e AWS")
    assert "Python" in skills
    assert "Docker" in skills

def test_market_trends():
    df = _fallback_data()
    trends = calculate_market_trends(df)
    assert len(trends) > 0
    assert all("attractiveness" in v for v in trends.values())


def test_normalizacao_scraper():
    assert normalize_level("seniot") == "Sênior"
    assert normalize_modalidade("remote") == "Remoto"
    assert normalize_skills("Python, Docker, Python") == "Python, Docker"


def test_deduplicacao_scraper():
    rows = [
        {"cargo": "Dev", "empresa": "Acme", "linguagem": "Python", "nivel": "Pleno", "salario": 10000, "modalidade": "Remoto", "skills": "Python", "cidade": "Brasil", "url": "https://x/v1", "fonte": "gupy", "coletado_em": "2026-03-22T00:00:00Z"},
        {"cargo": "Dev", "empresa": "Acme", "linguagem": "Python", "nivel": "Pleno", "salario": 10000, "modalidade": "remoto", "skills": "Python", "cidade": "Brasil", "url": "https://x/v1", "fonte": "gupy", "coletado_em": "2026-03-22T00:00:00Z"},
    ]
    assert len(deduplicate_rows(rows)) == 1


def test_market_alert_and_timeseries():
    df = _fallback_data()
    alert = build_market_alert(df)
    assert "Alerta rápido" in alert

    ts = build_collection_timeseries(df)
    assert not ts.empty
    assert "vagas" in ts.columns
