from database import _fallback_data
from market_trends import calculate_market_trends
from resume_analyzer import extract_skills_from_text

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