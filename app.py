import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")
from collections import Counter
import io
import base64
import json
from pathlib import Path
from database import fetch_all_vagas, get_stats
from new_tabs import render_trends_tab, render_resume_tab, render_tracker_tab
from app_features import build_market_alert, build_collection_timeseries

st.set_page_config(
    page_title="TechRadar · Mercado Dev Brasil",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap');

:root {
    --bg: #0a0e1a;
    --surface: #111827;
    --surface2: #1a2236;
    --border: #1e2d45;
    --accent: #00d4ff;
    --accent2: #7c3aed;
    --accent3: #10b981;
    --text: #e2e8f0;
    --muted: #64748b;
    --warn: #f59e0b;
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Space Grotesk', sans-serif !important;
}

[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}

[data-testid="stSidebar"] * {
    color: var(--text) !important;
}

/* Headers */
h1, h2, h3, h4 {
    font-family: 'Space Grotesk', sans-serif !important;
    color: var(--text) !important;
}

/* Metric cards */
[data-testid="metric-container"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 16px !important;
}

[data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace !important;
    color: var(--accent) !important;
    font-size: 1.8rem !important;
}

[data-testid="stMetricLabel"] {
    color: var(--muted) !important;
    font-size: 0.8rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
}

[data-testid="stMetricDelta"] {
    font-family: 'JetBrains Mono', monospace !important;
}

/* Multiselect */
[data-baseweb="select"] {
    background: var(--surface2) !important;
    border-color: var(--border) !important;
}

/* Slider */
[data-testid="stSlider"] > div > div > div {
    background: var(--accent2) !important;
}

/* Divider */
hr {
    border-color: var(--border) !important;
}

/* Tabs */
[data-baseweb="tab-list"] {
    background: var(--surface) !important;
    border-radius: 8px !important;
    gap: 4px !important;
    border: 1px solid var(--border) !important;
}

[data-baseweb="tab"] {
    background: transparent !important;
    color: var(--muted) !important;
    border-radius: 6px !important;
    font-family: 'Space Grotesk', sans-serif !important;
}

[aria-selected="true"] {
    background: var(--surface2) !important;
    color: var(--accent) !important;
}

/* Buttons */
.stButton > button {
    background: var(--surface2) !important;
    color: var(--accent) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    transition: all 0.2s !important;
}

.stButton > button:hover {
    background: var(--border) !important;
    border-color: var(--accent) !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

/* Card container */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 12px;
}

.tag {
    display: inline-block;
    background: var(--surface2);
    border: 1px solid var(--border);
    color: var(--accent);
    border-radius: 6px;
    padding: 2px 10px;
    font-size: 0.75rem;
    font-family: 'JetBrains Mono', monospace;
    margin: 2px;
}

.insight-box {
    background: linear-gradient(135deg, rgba(0,212,255,0.08) 0%, rgba(124,58,237,0.08) 100%);
    border: 1px solid rgba(0,212,255,0.2);
    border-radius: 10px;
    padding: 14px 18px;
    margin: 8px 0;
    font-size: 0.88rem;
    color: var(--text);
}
</style>
""", unsafe_allow_html=True)

PLOTLY_LAYOUT = dict(
    paper_bgcolor="#111827",
    plot_bgcolor="#0f172a",
    font=dict(family="Space Grotesk", color="#e2e8f0"),
    title_font=dict(family="Space Grotesk", size=16, color="#e2e8f0"),
    legend=dict(bgcolor="#1a2236", bordercolor="#1e2d45", borderwidth=1),
    margin=dict(l=20, r=20, t=40, b=20),
    xaxis=dict(gridcolor="#1e2d45", linecolor="#1e2d45", tickfont=dict(color="#94a3b8")),
    yaxis=dict(gridcolor="#1e2d45", linecolor="#1e2d45", tickfont=dict(color="#94a3b8")),
)

COLOR_SEQ = ["#00d4ff","#7c3aed","#10b981","#f59e0b","#ef4444","#8b5cf6","#06b6d4","#84cc16","#ec4899","#f97316","#14b8a6","#a855f7"]

@st.cache_data(show_spinner=False, ttl=3600)
def load_data():
    return fetch_all_vagas()

df_full = load_data()
db_stats = get_stats()

with st.sidebar:
    st.markdown("## 📡 TechRadar")
    fonte = db_stats.get("fonte", "sintético")
    total_db = db_stats.get("total", len(df_full))
    ultima = db_stats.get("ultima_coleta", "N/A")
    cor_fonte = "#10b981" if "real" in fonte else "#f59e0b"
    st.markdown(
        f"<span style='color:{cor_fonte};font-size:0.78rem'>● {fonte} · {total_db:,} vagas</span><br>"
        f"<span style='color:#64748b;font-size:0.74rem'>Atualizado: {ultima}</span>",
        unsafe_allow_html=True
    )
    st.markdown("---")

    st.markdown("### 🔍 Filtros")

    all_langs = sorted(df_full["linguagem"].unique())
    sel_langs = st.multiselect(
        "Linguagem",
        options=all_langs,
        default=all_langs,
        help="Filtre por linguagem principal"
    )

    all_levels = ["Junior", "Pleno", "Sênior", "Especialista"]
    sel_levels = st.multiselect(
        "Nível",
        options=all_levels,
        default=all_levels,
    )

    all_mods = sorted(df_full["modalidade"].unique())
    sel_mods = st.multiselect(
        "Modalidade",
        options=all_mods,
        default=all_mods,
    )

    sal_range = st.slider(
        "Faixa salarial (R$)",
        min_value=int(df_full["salario"].min()),
        max_value=int(df_full["salario"].max()),
        value=(int(df_full["salario"].min()), int(df_full["salario"].max())),
        step=500,
    )

    st.markdown("---")
    st.markdown("<span style='color:#64748b;font-size:0.75rem'>💡 Rode `python scraper.py` para atualizar os dados</span>", unsafe_allow_html=True)
    if st.button("🔄 Recarregar dados"):
        st.cache_data.clear()
        st.rerun()

df = df_full[
    df_full["linguagem"].isin(sel_langs) &
    df_full["nivel"].isin(sel_levels) &
    df_full["modalidade"].isin(sel_mods) &
    df_full["salario"].between(sal_range[0], sal_range[1])
].copy()

tracker_file = str(Path(__file__).with_name("job_tracker.json"))

st.markdown("""
<div style="padding: 24px 0 16px 0;">
    <h1 style="font-size:2.4rem; font-weight:700; margin:0; background: linear-gradient(90deg, #00d4ff, #7c3aed); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        📡 TechRadar
    </h1>
    <p style="color:#64748b; margin:4px 0 0 0; font-size:0.95rem;">
        Inteligência de mercado para developers — tecnologias em alta, salários e habilidades mais pedidas
    </p>
</div>
""", unsafe_allow_html=True)

if df.empty:
    st.warning("Nenhum resultado para os filtros selecionados.")
    st.stop()

alert_message = build_market_alert(df)
st.info(alert_message)

k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    st.metric("Vagas Analisadas", f"{len(df):,}", delta=f"{len(df) - len(df_full)}" if len(df) != len(df_full) else "dataset completo")

with k2:
    avg_sal = df["salario"].mean()
    full_avg = df_full["salario"].mean()
    st.metric("Salário Médio", f"R$ {avg_sal:,.0f}", delta=f"{((avg_sal/full_avg)-1)*100:+.1f}% vs total")

with k3:
    top_tech = df["linguagem"].value_counts().idxmax()
    top_count = df["linguagem"].value_counts().max()
    st.metric("Mais Demandada", top_tech, delta=f"{top_count} vagas")

with k4:
    top_sal_tech = df.groupby("linguagem")["salario"].mean().idxmax()
    top_sal_val = df.groupby("linguagem")["salario"].mean().max()
    st.metric("Melhor Remunerada", top_sal_tech, delta=f"R$ {top_sal_val:,.0f} médio")

with k5:
    remote_pct = (df["modalidade"] == "Remoto").mean() * 100
    st.metric("% Remoto", f"{remote_pct:.0f}%", delta=f"{remote_pct - (df_full['modalidade']=='Remoto').mean()*100:+.1f}pp")

st.markdown("##### 📦 Exportação")
exp1, exp2 = st.columns([1, 3])
with exp1:
    export_df = df.copy()
    export_df["coletado_em"] = export_df.get("coletado_em", "")
    csv_bytes = export_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="⬇️ Baixar CSV filtrado",
        data=csv_bytes,
        file_name="techradar_export.csv",
        mime="text/csv",
    )
with exp2:
    st.caption("Exporta os resultados atuais dos filtros para uso em Excel/BI.")

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

st.markdown("##### 🗓️ Série temporal de coleta")
ts_df = build_collection_timeseries(df_full)
if not ts_df.empty:
    fig_ts = px.line(ts_df, x="data", y="vagas", markers=True)
    fig_ts.update_layout(**PLOTLY_LAYOUT, height=250, xaxis_title="Data", yaxis_title="Vagas coletadas")
    st.plotly_chart(fig_ts, use_container_width=True)
else:
    st.caption("Sem histórico suficiente em `coletado_em` para série temporal.")

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "📊 Salários", "🔥 Demanda", "☁️ Skills", "🔬 Análise Cruzada",
    "🎯 Empregabilidade", "⚔️ Comparador",
    "📈 Tendências", "📄 Currículo", "📋 Job Tracker"
])

with tab1:
    c1, c2 = st.columns([3, 2])

    with c1:
        st.markdown("#### Média Salarial por Linguagem")

        sal_by_lang = (
            df.groupby("linguagem")["salario"]
            .agg(["mean","median","std","count"])
            .reset_index()
            .sort_values("mean", ascending=True)
        )
        sal_by_lang.columns = ["linguagem","media","mediana","desvio","vagas"]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=sal_by_lang["linguagem"],
            x=sal_by_lang["media"],
            orientation="h",
            name="Média",
            marker=dict(
                color=sal_by_lang["media"],
                colorscale=[[0,"#1e2d45"],[0.4,"#7c3aed"],[1,"#00d4ff"]],
                showscale=False,
            ),
            text=[f"R$ {v:,.0f}" for v in sal_by_lang["media"]],
            textposition="inside",
            textfont=dict(family="JetBrains Mono", size=11, color="white"),
        ))
        fig.add_trace(go.Scatter(
            y=sal_by_lang["linguagem"],
            x=sal_by_lang["mediana"],
            mode="markers",
            name="Mediana",
            marker=dict(symbol="diamond", size=10, color="#f59e0b", line=dict(color="white", width=1)),
        ))
        fig.update_layout(**PLOTLY_LAYOUT, height=420, xaxis_title="Salário (R$)", yaxis_title="", showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("#### Salário por Nível")

        level_order = ["Junior","Pleno","Sênior","Especialista"]
        df_box = df[df["nivel"].isin(level_order)].copy()
        df_box["nivel"] = pd.Categorical(df_box["nivel"], categories=level_order, ordered=True)
        df_box = df_box.sort_values("nivel")

        fig2 = px.box(
            df_box,
            x="nivel",
            y="salario",
            color="nivel",
            color_discrete_sequence=["#3b82f6","#10b981","#f59e0b","#ef4444"],
            category_orders={"nivel": level_order},
        )
        fig2.update_layout(**PLOTLY_LAYOUT, height=420, showlegend=False,
                           xaxis_title="Nível", yaxis_title="Salário (R$)")
        fig2.update_traces(marker=dict(size=4, opacity=0.6))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### Evolução Salarial por Nível e Linguagem")

    pivot = (
        df.groupby(["linguagem","nivel"])["salario"]
        .mean()
        .reset_index()
        .pivot(index="nivel", columns="linguagem", values="salario")
        .reindex(level_order)
        .dropna(axis=1)
    )

    fig3 = go.Figure()
    for i, tech in enumerate(pivot.columns):
        fig3.add_trace(go.Scatter(
            x=pivot.index,
            y=pivot[tech],
            mode="lines+markers",
            name=tech,
            line=dict(color=COLOR_SEQ[i % len(COLOR_SEQ)], width=2),
            marker=dict(size=8),
        ))
    fig3.update_layout(**PLOTLY_LAYOUT, height=350, xaxis_title="Nível", yaxis_title="Salário Médio (R$)")
    st.plotly_chart(fig3, use_container_width=True)

with tab2:
    c1, c2 = st.columns([2, 2])

    with c1:
        st.markdown("#### Vagas por Linguagem")
        counts = df["linguagem"].value_counts().reset_index()
        counts.columns = ["linguagem","vagas"]

        fig4 = px.bar(
            counts,
            x="linguagem",
            y="vagas",
            color="vagas",
            color_continuous_scale=[[0,"#1e2d45"],[1,"#00d4ff"]],
            text="vagas",
        )
        fig4.update_layout(**PLOTLY_LAYOUT, height=380, showlegend=False,
                           coloraxis_showscale=False, xaxis_title="", yaxis_title="Vagas")
        fig4.update_traces(textposition="outside", textfont=dict(family="JetBrains Mono", size=11))
        st.plotly_chart(fig4, use_container_width=True)

    with c2:
        st.markdown("#### Distribuição por Nível")
        level_counts = df["nivel"].value_counts().reindex(["Junior","Pleno","Sênior","Especialista"]).dropna()

        fig5 = go.Figure(go.Pie(
            labels=level_counts.index,
            values=level_counts.values,
            hole=0.55,
            marker=dict(colors=["#3b82f6","#10b981","#f59e0b","#ef4444"],
                        line=dict(color="#0a0e1a", width=2)),
            textfont=dict(family="Space Grotesk"),
        ))
        fig5.update_layout(**PLOTLY_LAYOUT, height=380, showlegend=True,
                           annotations=[dict(text=f"<b>{len(df)}</b><br>vagas", x=0.5, y=0.5,
                                            font=dict(size=15, family="JetBrains Mono", color="#e2e8f0"),
                                            showarrow=False)])
        st.plotly_chart(fig5, use_container_width=True)

    c3, c4 = st.columns([2, 2])

    with c3:
        st.markdown("#### Modalidade de Trabalho")
        mod_counts = df["modalidade"].value_counts()
        cols = {"Remoto":"#10b981","Híbrido":"#f59e0b","Presencial":"#ef4444"}

        fig6 = go.Figure(go.Bar(
            x=mod_counts.index,
            y=mod_counts.values,
            marker_color=[cols.get(m,"#64748b") for m in mod_counts.index],
            text=mod_counts.values,
            textposition="outside",
            textfont=dict(family="JetBrains Mono"),
        ))
        fig6.update_layout(**PLOTLY_LAYOUT, height=320, showlegend=False,
                           xaxis_title="", yaxis_title="Vagas")
        st.plotly_chart(fig6, use_container_width=True)

    with c4:
        st.markdown("#### Top Empresas Contratando")
        top_emp = df["empresa"].value_counts().head(10).reset_index()
        top_emp.columns = ["empresa","vagas"]

        fig7 = px.bar(top_emp, x="vagas", y="empresa", orientation="h",
                      color="vagas", color_continuous_scale=[[0,"#1e2d45"],[1,"#7c3aed"]],
                      text="vagas")
        fig7.update_layout(**PLOTLY_LAYOUT, height=320, showlegend=False,
                           coloraxis_showscale=False, xaxis_title="Vagas", yaxis_title="")
        fig7.update_yaxes(categoryorder="total ascending")
        fig7.update_traces(textposition="inside", textfont=dict(family="JetBrains Mono", size=10))
        st.plotly_chart(fig7, use_container_width=True)

with tab3:
    st.markdown("#### ☁️ Habilidades Mais Pedidas no Mercado")

    wc_col, stat_col = st.columns([3, 2])

    all_skills_text = " ".join(df["skills"].dropna().values)
    all_words = [s.strip() for s in all_skills_text.split(",") if s.strip()]
    skill_counter = Counter(all_words)

    with wc_col:
        wc = WordCloud(
            width=800, height=420,
            background_color="#111827",
            colormap="cool",
            max_words=80,
            font_path=None,
            prefer_horizontal=0.8,
            min_font_size=10,
            max_font_size=80,
        ).generate_from_frequencies(skill_counter)

        fig_wc, ax = plt.subplots(figsize=(10, 5))
        fig_wc.patch.set_facecolor("#111827")
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        st.pyplot(fig_wc, use_container_width=True)
        plt.close()

    with stat_col:
        st.markdown("#### Top 15 Skills")
        top_skills = pd.DataFrame(skill_counter.most_common(15), columns=["Skill","Menções"])

        fig_sk = px.bar(
            top_skills.sort_values("Menções"),
            x="Menções", y="Skill", orientation="h",
            color="Menções",
            color_continuous_scale=[[0,"#1e2d45"],[1,"#00d4ff"]],
            text="Menções",
        )
        fig_sk.update_layout(**PLOTLY_LAYOUT, height=440, showlegend=False,
                             coloraxis_showscale=False, xaxis_title="", yaxis_title="")
        fig_sk.update_traces(textposition="inside", textfont=dict(family="JetBrains Mono", size=10))
        st.plotly_chart(fig_sk, use_container_width=True)

    st.markdown("#### Skills por Linguagem")
    sel_tech_wc = st.selectbox("Selecione a linguagem:", options=sel_langs if sel_langs else all_langs)

    df_tech = df[df["linguagem"] == sel_tech_wc]
    tech_skills_text = " ".join(df_tech["skills"].dropna().values)
    tech_words = [s.strip() for s in tech_skills_text.split(",") if s.strip()]
    tech_counter = Counter(tech_words)

    if tech_counter:
        wc2 = WordCloud(
            width=1000, height=300,
            background_color="#111827",
            colormap="plasma",
            max_words=60,
            prefer_horizontal=0.75,
        ).generate_from_frequencies(tech_counter)

        fig_wc2, ax2 = plt.subplots(figsize=(12, 3.5))
        fig_wc2.patch.set_facecolor("#111827")
        ax2.imshow(wc2, interpolation="bilinear")
        ax2.axis("off")
        ax2.set_title(f"Skills mais pedidas para {sel_tech_wc}", color="#e2e8f0",
                      fontsize=13, pad=10, loc="left")
        st.pyplot(fig_wc2, use_container_width=True)
        plt.close()

with tab4:
    st.markdown("#### 🔬 Análise Multidimensional")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("##### Salário Médio · Linguagem × Nível")

        heatmap_data = (
            df.groupby(["linguagem","nivel"])["salario"]
            .mean()
            .reset_index()
            .pivot(index="linguagem", columns="nivel", values="salario")
            .reindex(columns=["Junior","Pleno","Sênior","Especialista"])
        )

        fig_heat = go.Figure(go.Heatmap(
            z=heatmap_data.values,
            x=heatmap_data.columns.tolist(),
            y=heatmap_data.index.tolist(),
            colorscale=[[0,"#1e2d45"],[0.5,"#7c3aed"],[1,"#00d4ff"]],
            text=np.vectorize(lambda v: f"R$ {v:,.0f}" if not np.isnan(v) else "")(heatmap_data.values),
            texttemplate="%{text}",
            textfont=dict(size=10, family="JetBrains Mono"),
            hoverongaps=False,
        ))
        fig_heat.update_layout(**PLOTLY_LAYOUT, height=420)
        st.plotly_chart(fig_heat, use_container_width=True)

    with c2:
        st.markdown("##### Demanda vs Salário Médio")

        bubble_data = (
            df.groupby("linguagem")
            .agg(vagas=("linguagem","count"), salario_medio=("salario","mean"), dispersao=("salario","std"))
            .reset_index()
        )

        bubble_data["dispersao"] = bubble_data["dispersao"].fillna(500).clip(lower=200)

        fig_bubble = px.scatter(
            bubble_data,
            x="vagas",
            y="salario_medio",
            size="dispersao",
            color="linguagem",
            text="linguagem",
            color_discrete_sequence=COLOR_SEQ,
            size_max=50,
        )
        fig_bubble.update_traces(textposition="top center", textfont=dict(size=10))
        fig_bubble.update_layout(**PLOTLY_LAYOUT, height=420, showlegend=False,
                                 xaxis_title="Nº de Vagas", yaxis_title="Salário Médio (R$)")
        st.plotly_chart(fig_bubble, use_container_width=True)

    st.markdown("##### 💡 Insights Automáticos")

    ic1, ic2, ic3 = st.columns(3)

    with ic1:
        best_roi = bubble_data.assign(score=lambda d: d["salario_medio"] / d["vagas"].max() * 100 + d["vagas"] / d["vagas"].max() * 100).nlargest(1,"score").iloc[0]
        st.markdown(f"""
        <div class="insight-box">
        <b>🏆 Melhor equilíbrio</b><br>
        <span style="color:#00d4ff;font-family:JetBrains Mono">{best_roi['linguagem']}</span>
        combina alta demanda ({int(best_roi['vagas'])} vagas) com bom salário médio 
        (R$ {best_roi['salario_medio']:,.0f}).
        </div>
        """, unsafe_allow_html=True)

    with ic2:
        premium = bubble_data.nlargest(1, "salario_medio").iloc[0]
        st.markdown(f"""
        <div class="insight-box">
        <b>💰 Premium Tech</b><br>
        <span style="color:#7c3aed;font-family:JetBrains Mono">{premium['linguagem']}</span>
        paga a maior média: <b>R$ {premium['salario_medio']:,.0f}</b>.
        Altamente especializada, com {int(premium['vagas'])} vagas no mercado.
        </div>
        """, unsafe_allow_html=True)

    with ic3:
        rem_sal = df[df["modalidade"]=="Remoto"]["salario"].mean()
        pres_sal = df[df["modalidade"]=="Presencial"]["salario"].mean()
        diff = rem_sal - pres_sal
        st.markdown(f"""
        <div class="insight-box">
        <b>🏠 Remoto vs Presencial</b><br>
        Trabalho remoto paga em média <b style="color:#10b981">R$ {abs(diff):,.0f} {'a mais' if diff>0 else 'a menos'}</b>
        que o presencial.<br>
        Remoto: R$ {rem_sal:,.0f} | Presencial: R$ {pres_sal:,.0f}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 📋 Tabela Detalhada")

    show_cols = ["cargo","empresa","linguagem","nivel","salario","modalidade"]
    display_df = df[show_cols].sort_values("salario", ascending=False).reset_index(drop=True)
    display_df["salario"] = display_df["salario"].apply(lambda x: f"R$ {x:,.0f}")

    st.dataframe(
        display_df,
        use_container_width=True,
        height=300,
        column_config={
            "cargo": "Cargo",
            "empresa": "Empresa",
            "linguagem": "Linguagem",
            "nivel": "Nível",
            "salario": "Salário",
            "modalidade": "Modalidade",
        }
    )

with tab5:
    st.markdown("#### 🎯 Score de Empregabilidade")
    st.markdown(
        "<p style='color:#64748b'>Selecione suas skills e veja quantas vagas você se encaixa, "
        "qual o salário esperado e o que falta aprender.</p>",
        unsafe_allow_html=True
    )

    col_input, col_result = st.columns([2, 3])

    with col_input:
        st.markdown("##### Suas informações")

        user_nivel = st.selectbox(
            "Seu nível atual",
            ["Junior", "Pleno", "Sênior", "Especialista"],
            index=1
        )

        all_skills_list = sorted({
            s.strip()
            for skills_str in df_full["skills"].dropna()
            for s in skills_str.split(",")
            if s.strip()
        })

        user_skills = st.multiselect(
            "Suas skills",
            options=all_skills_list,
            default=[],
            placeholder="Digite ou selecione suas skills..."
        )

        user_modalidade = st.multiselect(
            "Modalidade preferida",
            ["Remoto", "Híbrido", "Presencial"],
            default=["Remoto", "Híbrido", "Presencial"]
        )

        calcular = st.button("🔍 Calcular Score", type="primary")

    with col_result:
        if calcular and user_skills:
            user_set = set(s.lower() for s in user_skills)

            def match_score(skills_str: str) -> float:
                if not isinstance(skills_str, str):
                    return 0.0
                vaga_skills = {s.strip().lower() for s in skills_str.split(",")}
                if not vaga_skills:
                    return 0.0
                match = user_set & vaga_skills
                return len(match) / len(vaga_skills)

            df_score = df_full[
                (df_full["nivel"] == user_nivel) &
                (df_full["modalidade"].isin(user_modalidade))
            ].copy()

            df_score["match"] = df_score["skills"].apply(match_score)
            df_score["match_pct"] = (df_score["match"] * 100).round(1)

            vagas_compativeis = df_score[df_score["match"] >= 0.4]
            total_vagas = len(df_score)
            n_compativeis = len(vagas_compativeis)
            score_geral = (n_compativeis / total_vagas * 100) if total_vagas > 0 else 0

            sal_esperado = vagas_compativeis["salario"].mean() if not vagas_compativeis.empty else 0
            sal_nivel_geral = df_full[df_full["nivel"] == user_nivel]["salario"].mean()

            cor_score = "#10b981" if score_geral >= 60 else "#f59e0b" if score_geral >= 30 else "#ef4444"
            st.markdown(f"""
            <div style="background:#111827;border:1px solid #1e2d45;border-radius:14px;padding:24px;text-align:center;margin-bottom:16px">
                <div style="font-size:0.8rem;color:#64748b;text-transform:uppercase;letter-spacing:0.1em">Compatibilidade Geral</div>
                <div style="font-size:4rem;font-weight:700;color:{cor_score};font-family:'JetBrains Mono',monospace;line-height:1.1">
                    {score_geral:.0f}%
                </div>
                <div style="color:#94a3b8;font-size:0.9rem">
                    {n_compativeis} de {total_vagas} vagas como {user_nivel}
                </div>
            </div>
            """, unsafe_allow_html=True)

            m1, m2 = st.columns(2)
            with m1:
                st.metric("💰 Salário Esperado", f"R$ {sal_esperado:,.0f}" if sal_esperado else "N/A",
                          delta=f"{((sal_esperado/sal_nivel_geral)-1)*100:+.1f}% vs nível médio" if sal_esperado else "")
            with m2:
                st.metric("🎯 Vagas Compatíveis", f"{n_compativeis:,}",
                          delta=f"de {total_vagas:,} para {user_nivel}")

            st.markdown("##### 📚 Skills para aumentar seu score")

            todas_skills_vagas = Counter()
            for _, row in df_score.iterrows():
                if not isinstance(row["skills"], str):
                    continue
                for s in row["skills"].split(","):
                    s = s.strip()
                    if s and s.lower() not in user_set:
                        todas_skills_vagas[s] += 1

            top_faltando = todas_skills_vagas.most_common(10)

            if top_faltando:
                falta_df = pd.DataFrame(top_faltando, columns=["Skill","Vagas que pedem"])
                fig_falta = px.bar(
                    falta_df,
                    x="Vagas que pedem", y="Skill", orientation="h",
                    color="Vagas que pedem",
                    color_continuous_scale=[[0,"#1e2d45"],[1,"#f59e0b"]],
                    text="Vagas que pedem",
                )
                fig_falta.update_layout(**PLOTLY_LAYOUT, height=320, showlegend=False,
                                        coloraxis_showscale=False,
                                        yaxis={"categoryorder": "total ascending"},
                                        xaxis_title="", yaxis_title="",
                                        margin=dict(l=10, r=10, t=10, b=10))
                fig_falta.update_traces(textposition="inside", textfont=dict(family="JetBrains Mono", size=10))
                st.plotly_chart(fig_falta, use_container_width=True)

            if not vagas_compativeis.empty:
                st.markdown("##### 🏆 Suas vagas mais compatíveis")
                top_vagas = vagas_compativeis.nlargest(5, "match_pct")[
                    ["cargo","empresa","linguagem","salario","match_pct"]
                ].reset_index(drop=True)
                top_vagas["salario"] = top_vagas["salario"].apply(lambda x: f"R$ {x:,.0f}")
                top_vagas["match_pct"] = top_vagas["match_pct"].apply(lambda x: f"{x:.0f}%")
                st.dataframe(top_vagas, use_container_width=True,
                             column_config={
                                 "cargo": "Cargo", "empresa": "Empresa",
                                 "linguagem": "Linguagem", "salario": "Salário",
                                 "match_pct": "Compatibilidade",
                             })

        elif calcular and not user_skills:
            st.warning("Selecione pelo menos uma skill para calcular.")
        else:
            st.markdown("""
            <div class="insight-box" style="text-align:center;padding:40px">
                <div style="font-size:2rem">🎯</div>
                <div style="color:#94a3b8;margin-top:8px">
                    Selecione suas skills ao lado e clique em <b>Calcular Score</b>
                </div>
            </div>
            """, unsafe_allow_html=True)


with tab6:
    st.markdown("#### ⚔️ Comparador de Stacks")
    st.markdown(
        "<p style='color:#64748b'>Compare duas linguagens lado a lado — salários, demanda, "
        "skills e ganho potencial ao migrar.</p>",
        unsafe_allow_html=True
    )

    all_langs_comp = sorted(df_full["linguagem"].unique())

    ca, cb = st.columns(2)
    with ca:
        lang_a = st.selectbox("Stack A (atual)", all_langs_comp,
                              index=all_langs_comp.index("PHP") if "PHP" in all_langs_comp else 0)
    with cb:
        lang_b = st.selectbox("Stack B (objetivo)", all_langs_comp,
                              index=all_langs_comp.index("Python") if "Python" in all_langs_comp else 1)

    nivel_comp = st.select_slider(
        "Nível de comparação",
        options=["Junior", "Pleno", "Sênior", "Especialista"],
        value="Pleno"
    )

    if lang_a == lang_b:
        st.info("Selecione duas linguagens diferentes para comparar.")
    else:
        df_a = df_full[(df_full["linguagem"] == lang_a) & (df_full["nivel"] == nivel_comp)]
        df_b = df_full[(df_full["linguagem"] == lang_b) & (df_full["nivel"] == nivel_comp)]

        sal_a = df_a["salario"].mean() if not df_a.empty else 0
        sal_b = df_b["salario"].mean() if not df_b.empty else 0
        ganho = sal_b - sal_a
        ganho_anual = ganho * 12

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div style="background:#111827;border:1px solid #1e2d45;border-radius:12px;padding:20px;text-align:center">
                <div style="font-size:0.75rem;color:#64748b;text-transform:uppercase;letter-spacing:0.08em">{lang_a} · {nivel_comp}</div>
                <div style="font-size:2.2rem;font-weight:700;color:#00d4ff;font-family:'JetBrains Mono',monospace">R$ {sal_a:,.0f}</div>
                <div style="color:#64748b;font-size:0.85rem">{len(df_a)} vagas</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            cor_ganho = "#10b981" if ganho > 0 else "#ef4444"
            sinal = "+" if ganho > 0 else ""
            st.markdown(f"""
            <div style="background:#111827;border:1px solid {cor_ganho}44;border-radius:12px;padding:20px;text-align:center">
                <div style="font-size:0.75rem;color:#64748b;text-transform:uppercase;letter-spacing:0.08em">Ganho ao migrar</div>
                <div style="font-size:2.2rem;font-weight:700;color:{cor_ganho};font-family:'JetBrains Mono',monospace">
                    {sinal}R$ {abs(ganho):,.0f}
                </div>
                <div style="color:#64748b;font-size:0.85rem">{sinal}R$ {abs(ganho_anual):,.0f}/ano</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div style="background:#111827;border:1px solid #1e2d45;border-radius:12px;padding:20px;text-align:center">
                <div style="font-size:0.75rem;color:#64748b;text-transform:uppercase;letter-spacing:0.08em">{lang_b} · {nivel_comp}</div>
                <div style="font-size:2.2rem;font-weight:700;color:#7c3aed;font-family:'JetBrains Mono',monospace">R$ {sal_b:,.0f}</div>
                <div style="color:#64748b;font-size:0.85rem">{len(df_b)} vagas</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

        g1, g2 = st.columns(2)

        with g1:
            st.markdown("##### Salário por Nível")
            level_order = ["Junior", "Pleno", "Sênior", "Especialista"]
            comp_data = []
            for lvl in level_order:
                sal_a_lvl = df_full[(df_full["linguagem"]==lang_a)&(df_full["nivel"]==lvl)]["salario"].mean()
                sal_b_lvl = df_full[(df_full["linguagem"]==lang_b)&(df_full["nivel"]==lvl)]["salario"].mean()
                if not np.isnan(sal_a_lvl):
                    comp_data.append({"nivel": lvl, "linguagem": lang_a, "salario": sal_a_lvl})
                if not np.isnan(sal_b_lvl):
                    comp_data.append({"nivel": lvl, "linguagem": lang_b, "salario": sal_b_lvl})

            comp_df = pd.DataFrame(comp_data)
            fig_comp = px.line(
                comp_df, x="nivel", y="salario", color="linguagem",
                markers=True,
                color_discrete_map={lang_a: "#00d4ff", lang_b: "#7c3aed"},
                category_orders={"nivel": level_order},
            )
            fig_comp.update_layout(**PLOTLY_LAYOUT, height=300,
                                   xaxis_title="Nível", yaxis_title="Salário Médio (R$)")
            fig_comp.update_traces(line=dict(width=3), marker=dict(size=10))
            st.plotly_chart(fig_comp, use_container_width=True)

        with g2:
            st.markdown("##### Distribuição de Vagas por Modalidade")
            mod_a = df_a["modalidade"].value_counts()
            mod_b = df_b["modalidade"].value_counts()
            mods = ["Remoto", "Híbrido", "Presencial"]

            fig_mod = go.Figure(data=[
                go.Bar(name=lang_a, x=mods,
                       y=[mod_a.get(m, 0) for m in mods],
                       marker_color="#00d4ff"),
                go.Bar(name=lang_b, x=mods,
                       y=[mod_b.get(m, 0) for m in mods],
                       marker_color="#7c3aed"),
            ])
            fig_mod.update_layout(**PLOTLY_LAYOUT, height=300, barmode="group",
                                  xaxis_title="", yaxis_title="Vagas")
            st.plotly_chart(fig_mod, use_container_width=True)

        st.markdown("##### 🧬 Análise de Skills")

        skills_a = Counter(
            s.strip() for row in df_a["skills"].dropna()
            for s in row.split(",") if s.strip()
        )
        skills_b = Counter(
            s.strip() for row in df_b["skills"].dropna()
            for s in row.split(",") if s.strip()
        )

        set_a = set(skills_a.keys())
        set_b = set(skills_b.keys())
        em_comum = set_a & set_b
        so_a = set_a - set_b
        so_b = set_b - set_a

        sk1, sk2, sk3 = st.columns(3)
        with sk1:
            st.markdown(f"<b style='color:#00d4ff'>Exclusivas de {lang_a}</b>", unsafe_allow_html=True)
            for s in list(so_a)[:8]:
                st.markdown(f"<span class='tag'>{s}</span>", unsafe_allow_html=True)
        with sk2:
            st.markdown("<b style='color:#10b981'>Skills em comum</b>", unsafe_allow_html=True)
            for s in list(em_comum)[:8]:
                st.markdown(f"<span class='tag' style='color:#10b981'>{s}</span>", unsafe_allow_html=True)
        with sk3:
            st.markdown(f"<b style='color:#7c3aed'>Exclusivas de {lang_b}</b>", unsafe_allow_html=True)
            for s in list(so_b)[:8]:
                st.markdown(f"<span class='tag' style='color:#7c3aed'>{s}</span>", unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        demanda_a = len(df_full[df_full["linguagem"] == lang_a])
        demanda_b = len(df_full[df_full["linguagem"] == lang_b])
        sal_a_geral = df_full[df_full["linguagem"] == lang_a]["salario"].mean()
        sal_b_geral = df_full[df_full["linguagem"] == lang_b]["salario"].mean()

        vantagem_sal = lang_b if sal_b_geral > sal_a_geral else lang_a
        vantagem_dem = lang_b if demanda_b > demanda_a else lang_a

        if vantagem_sal == vantagem_dem:
            vencedor = vantagem_sal
            motivo = "domina tanto em salário quanto em demanda"
        elif sal_b_geral > sal_a_geral:
            vencedor = lang_b
            motivo = "paga mais, mesmo com menos vagas"
        else:
            vencedor = lang_a
            motivo = "tem mais vagas no mercado"

        st.markdown(f"""
        <div style="background:linear-gradient(135deg,rgba(0,212,255,0.08),rgba(124,58,237,0.08));
                    border:1px solid rgba(0,212,255,0.2);border-radius:12px;padding:20px;margin-top:8px">
            <b>🏆 Veredicto</b><br>
            <span style="color:#e2e8f0">
                Para o nível <b>{nivel_comp}</b>, <span style="color:#00d4ff;font-family:'JetBrains Mono',monospace"><b>{vencedor}</b></span> {motivo}.<br>
                {'Migrar traria um ganho de <b style="color:#10b981">R$ ' + f'{abs(ganho_anual):,.0f}</b> por ano.' if ganho > 0 else f'Manter <b>{lang_a}</b> pode ser mais vantajoso no curto prazo.'}
                <br><span style="color:#64748b;font-size:0.85rem">
                Vagas: {lang_a} ({demanda_a}) vs {lang_b} ({demanda_b}) · 
                Salário médio geral: {lang_a} R$ {sal_a_geral:,.0f} vs {lang_b} R$ {sal_b_geral:,.0f}
                </span>
            </span>
        </div>
        """, unsafe_allow_html=True)

with tab7:
    render_trends_tab(df, PLOTLY_LAYOUT)

with tab8:
    render_resume_tab(df_full, PLOTLY_LAYOUT)

with tab9:
    render_tracker_tab(tracker_file)
