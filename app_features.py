import json
import tempfile
from pathlib import Path

import pandas as pd


TRACKER_STAGES = ["🔍 Interesse", "📤 Aplicado", "💬 Entrevista", "✅ Aprovado", "❌ Recusado"]


def default_tracker_state() -> dict:
    return {stage: [] for stage in TRACKER_STAGES}


def load_tracker(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return default_tracker_state()

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return default_tracker_state()

    if not isinstance(data, dict):
        return default_tracker_state()

    state = default_tracker_state()
    for stage in TRACKER_STAGES:
        values = data.get(stage, [])
        state[stage] = values if isinstance(values, list) else []
    return state


def save_tracker(path: str, tracker: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    payload = json.dumps(tracker, ensure_ascii=False, indent=2)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        delete=False,
        dir=str(p.parent),
        prefix=p.stem + ".",
        suffix=".tmp",
    ) as tmp_file:
        tmp_file.write(payload)
        tmp_path = Path(tmp_file.name)

    tmp_path.replace(p)


def build_market_alert(df: pd.DataFrame) -> str:
    if df.empty:
        return "Sem dados para gerar alertas."

    top_lang = df["linguagem"].value_counts().idxmax()
    top_count = int(df["linguagem"].value_counts().max())

    remote_df = df[df["modalidade"] == "Remoto"]
    onsite_df = df[df["modalidade"] == "Presencial"]
    remote_avg = float(remote_df["salario"].mean()) if not remote_df.empty else 0.0
    onsite_avg = float(onsite_df["salario"].mean()) if not onsite_df.empty else 0.0

    if remote_avg and onsite_avg:
        diff = remote_avg - onsite_avg
        comp = "acima" if diff > 0 else "abaixo"
        return (
            f"🔔 Alerta rápido: {top_lang} lidera demanda ({top_count} vagas). "
            f"Salário remoto está R$ {abs(diff):,.0f} {comp} do presencial."
        )

    return f"🔔 Alerta rápido: {top_lang} lidera demanda ({top_count} vagas)."


def build_collection_timeseries(df: pd.DataFrame) -> pd.DataFrame:
    if "coletado_em" not in df.columns or df.empty:
        return pd.DataFrame(columns=["data", "vagas"])

    ts = df.copy()
    ts["coletado_em"] = pd.to_datetime(ts["coletado_em"], errors="coerce", utc=True)
    ts = ts.dropna(subset=["coletado_em"])
    if ts.empty:
        return pd.DataFrame(columns=["data", "vagas"])

    ts["data"] = ts["coletado_em"].dt.date
    out = ts.groupby("data").size().reset_index(name="vagas").sort_values("data")
    return out
