import pandas as pd

import database
from database import _fallback_data
from market_trends import calculate_market_trends
from resume_analyzer import extract_skills_from_text
from skill_catalog import SKILLS_CATALOG
from app_features import (
    build_market_alert,
    build_collection_timeseries,
    default_tracker_state,
    load_tracker,
    save_tracker,
)
import scraper
from scraper import (
    normalize_level,
    normalize_modalidade,
    normalize_skills,
    deduplicate_rows,
)

def test_fallback_data_nao_vazio():
    df = _fallback_data()
    assert len(df) > 0


def test_fallback_data_prefere_csv_local(tmp_path, monkeypatch):
    csv_path = tmp_path / "vagas_reais.csv"
    pd.DataFrame([
        {
            "cargo": "Dev Python",
            "empresa": "Acme",
            "linguagem": "Python",
            "nivel": "Pleno",
            "salario": 12000,
            "modalidade": "Remoto",
            "skills": "Python, Docker",
        }
    ]).to_csv(csv_path, index=False)

    monkeypatch.setattr(database, "SUPABASE_URL", "")
    monkeypatch.setattr(database, "SUPABASE_KEY", "")
    monkeypatch.setattr(database, "__file__", str(tmp_path / "database.py"))

    df = database._fallback_data()
    assert len(df) == 1
    assert df.iloc[0]["empresa"] == "Acme"


def test_fallback_colunas():
    df = _fallback_data()
    for col in ["cargo", "empresa", "linguagem", "nivel", "salario"]:
        assert col in df.columns

def test_extract_skills():
    skills = extract_skills_from_text("Experiência com Python, Docker e AWS")
    assert "Python" in skills
    assert "Docker" in skills


def test_catalogo_skills_compartilhado():
    assert "Ansible" in SKILLS_CATALOG
    assert "OAuth" in SKILLS_CATALOG

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


def test_tracker_roundtrip_and_corruption(tmp_path):
    tracker_path = tmp_path / "job_tracker.json"

    tracker = default_tracker_state()
    tracker["🔍 Interesse"].append({"cargo": "Dev", "empresa": "Acme", "salario": "R$ 12.000"})
    save_tracker(tracker_path, tracker)

    loaded = load_tracker(tracker_path)
    assert loaded["🔍 Interesse"][0]["cargo"] == "Dev"

    tracker_path.write_text("{invalid json", encoding="utf-8")
    assert load_tracker(tracker_path) == default_tracker_state()


def test_scrape_all_mapeia_catho(monkeypatch):
    fake_row = {
        "cargo": "Dev Python",
        "empresa": "Acme",
        "linguagem": "Python",
        "nivel": "Pleno",
        "salario": 12000,
        "modalidade": "Remoto",
        "skills": "Python, Docker",
        "cidade": "Brasil",
        "url": "https://example.com/vaga/1",
        "fonte": "catho",
        "coletado_em": "2026-04-08T00:00:00Z",
    }

    monkeypatch.setattr(scraper, "scrape_catho", lambda max_pages=3: [fake_row])
    df = scraper.scrape_all(["catho"])

    assert len(df) == 1
    assert df.iloc[0]["fonte"] == "catho"


def test_scrape_all_preserva_alias_indeed(monkeypatch):
    fake_row = {
        "cargo": "Dev Python",
        "empresa": "Acme",
        "linguagem": "Python",
        "nivel": "Pleno",
        "salario": 12000,
        "modalidade": "Remoto",
        "skills": "Python, Docker",
        "cidade": "Brasil",
        "url": "https://example.com/vaga/2",
        "fonte": "indeed",
        "coletado_em": "2026-04-08T00:00:00Z",
    }

    monkeypatch.setattr(scraper, "scrape_catho", lambda max_pages=3: [fake_row])
    df = scraper.scrape_all(["indeed"])

    assert len(df) == 1
    assert df.iloc[0]["fonte"] == "indeed"


def test_fetch_paged_concatena_paginas():
    class FakeResult:
        def __init__(self, data):
            self.data = data

    class FakeQuery:
        def __init__(self, pages):
            self.pages = pages
            self.call = 0

        def range(self, start, end):
            return self

        def execute(self):
            if self.call < len(self.pages):
                data = self.pages[self.call]
            else:
                data = []
            self.call += 1
            return FakeResult(data)

    pages = [
        [{"id": 1}, {"id": 2}],
        [{"id": 3}],
    ]
    df = database._fetch_paged(FakeQuery(pages), page_size=2, max_rows=10)
    assert len(df) == 3
