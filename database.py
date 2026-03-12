"""
database.py — Camada de integração com Supabase
"""

import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

def _get_env(key: str) -> str:
    """Lê variável de .env local ou de secrets do Streamlit Cloud."""
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


def get_client():
    """Retorna cliente Supabase autenticado."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError(
            "❌ Variáveis SUPABASE_URL e SUPABASE_KEY não configuradas.\n"
            "   Copie o arquivo .env.example para .env e preencha."
        )
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def upsert_vagas(df: pd.DataFrame) -> int:
    """
    Insere ou atualiza vagas no Supabase.
    Usa 'url' como chave de upsert para evitar duplicatas.
    Retorna o número de registros processados.
    """
    client = get_client()

    cols = ["cargo", "empresa", "linguagem", "nivel", "salario",
            "modalidade", "skills", "cidade", "url", "fonte", "coletado_em"]

    # Garante que só colunas existentes são enviadas
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
    """
    Busca vagas do Supabase com filtros opcionais.
    Fallback para CSV local se Supabase não estiver configurado.
    """
    # Fallback: sem Supabase configurado, usa CSV ou gerador
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

        result = query.limit(5000).execute()
        df = pd.DataFrame(result.data)

        if df.empty:
            print("⚠️  Supabase retornou vazio — usando fallback")
            return _fallback_data()

        return df

    except Exception as e:
        print(f"⚠️  Erro Supabase: {e} — usando fallback")
        return _fallback_data()


def fetch_all_vagas() -> pd.DataFrame:
    """Busca todas as vagas sem filtros (para cache do Streamlit)."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return _fallback_data()

    try:
        client = get_client()
        result = client.table(TABLE).select("*").limit(5000).execute()
        df = pd.DataFrame(result.data)
        return df if not df.empty else _fallback_data()
    except Exception as e:
        print(f"⚠️  Supabase indisponível: {e}")
        return _fallback_data()


def _fallback_data() -> pd.DataFrame:
    """Usa CSV local se existir, senão gera dados sintéticos."""
    import os
    if os.path.exists("vagas_reais.csv"):
        print("📂 Usando vagas_reais.csv")
        return pd.read_csv("vagas_reais.csv")
    
    print("🔧 Usando dataset sintético (rode scraper.py para dados reais)")
    from generate_data import generate_data
    return generate_data()


def get_stats() -> dict:
    """Retorna estatísticas rápidas da tabela."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return {"total": 0, "fonte": "sintético", "ultima_coleta": "N/A"}

    try:
        client = get_client()
        result = client.table(TABLE).select("coletado_em", count="exact").order("coletado_em", desc=True).limit(1).execute()
        ultima = result.data[0]["coletado_em"][:10] if result.data else "N/A"
        return {"total": result.count, "fonte": "Gupy (real)", "ultima_coleta": ultima}
    except:
        return {"total": 0, "fonte": "erro", "ultima_coleta": "N/A"}
