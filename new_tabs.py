import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
from resume_analyzer import analyze_resume
from market_trends import (
    calculate_market_trends,
    get_salary_percentiles,
    generate_career_projection,
)


def render_trends_tab(df, PLOTLY_LAYOUT):

    st.markdown("#### 📈 Tendências do Mercado Tech")
    st.markdown(
        "<p style='color:#64748b'>Radar de atratividade, percentis salariais "
        "e projeção de carreira por stack.</p>",
        unsafe_allow_html=True,
    )

    trends = calculate_market_trends(df)

    st.markdown("##### 🎯 Radar de Atratividade")
    trend_df = pd.DataFrame([
        {
            "Linguagem": lang,
            "Demanda": v["demand_score"],
            "Salário": v["salary_score"],
            "Remoto": v["remote_score"],
            "Score": v["attractiveness"],
            "Vagas": v["vagas"],
        }
        for lang, v in trends.items()
    ]).sort_values("Score", ascending=False)

    fig_trend = px.bar(
        trend_df, x="Linguagem", y="Score", color="Score",
        color_continuous_scale=[[0, "#1e2d45"], [0.5, "#7c3aed"], [1, "#00d4ff"]],
        text=trend_df["Score"].apply(lambda x: f"{x:.0f}"),
    )
    fig_trend.update_layout(
        **PLOTLY_LAYOUT, height=380, coloraxis_showscale=False,
        xaxis_title="", yaxis_title="Score de Atratividade",
    )
    fig_trend.update_traces(
        textposition="outside",
        textfont=dict(family="JetBrains Mono", size=11),
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    tc1, tc2, tc3 = st.columns(3)
    top3 = trend_df.head(3)
    cols_iter = [tc1, tc2, tc3]
    colors_top = ["#00d4ff", "#7c3aed", "#10b981"]
    for idx, (_, row) in enumerate(top3.iterrows()):
        if idx < 3:
            with cols_iter[idx]:
                c = colors_top[idx]
                st.markdown(f"""
                <div class="card" style="border-color:{c}44">
                    <div style="font-size:1.6rem;font-weight:700;color:{c};
                                font-family:'JetBrains Mono'">{row['Linguagem']}</div>
                    <div style="color:#64748b;font-size:0.8rem;margin-top:4px">
                        Demanda: {row['Demanda']:.0f} · Salário: {row['Salário']:.0f}
                        · Remoto: {row['Remoto']:.0f}%
                    </div>
                    <div style="color:#94a3b8;font-size:0.85rem;margin-top:8px">
                        {row['Vagas']} vagas disponíveis
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("##### 💰 Percentis Salariais por Stack")
    sel_lang = st.selectbox(
        "Selecione a linguagem:",
        sorted(df["linguagem"].unique()),
        key="perc_lang",
    )
    perc = get_salary_percentiles(df, sel_lang)

    if perc:
        perc_cols = st.columns(5)
        labels = [
            ("P10", perc["p10"]), ("P25", perc["p25"]),
            ("Mediana", perc["p50"]), ("P75", perc["p75"]),
            ("P90", perc["p90"]),
        ]
        for i, (label, val) in enumerate(labels):
            with perc_cols[i]:
                st.metric(label, f"R$ {val:,.0f}")

    st.markdown("##### 🚀 Projeção de Carreira")
    proj = generate_career_projection(df, sel_lang)
    if proj:
        proj_df = pd.DataFrame(proj)
        fig_proj = go.Figure()
        fig_proj.add_trace(go.Bar(
            x=proj_df["nivel"], y=proj_df["sal_medio"],
            marker=dict(
                color=proj_df["sal_medio"],
                colorscale=[[0, "#1e2d45"], [0.5, "#7c3aed"], [1, "#00d4ff"]],
            ),
            text=[f"R$ {v:,.0f}" for v in proj_df["sal_medio"]],
            textposition="outside",
            textfont=dict(family="JetBrains Mono", size=11),
        ))
        fig_proj.add_trace(go.Scatter(
            x=proj_df["nivel"], y=proj_df["sal_max"],
            mode="markers", name="Teto",
            marker=dict(symbol="triangle-up", size=10, color="#10b981"),
        ))
        fig_proj.add_trace(go.Scatter(
            x=proj_df["nivel"], y=proj_df["sal_min"],
            mode="markers", name="Piso",
            marker=dict(symbol="triangle-down", size=10, color="#ef4444"),
        ))
        fig_proj.update_layout(
            **PLOTLY_LAYOUT, height=350,
            xaxis_title="Nível", yaxis_title="Salário (R$)",
            showlegend=True,
        )
        st.plotly_chart(fig_proj, use_container_width=True)


def render_resume_tab(df_full, PLOTLY_LAYOUT):

    st.markdown("#### 📄 Analisar Currículo")
    st.markdown(
        "<p style='color:#64748b'>Cole o texto do seu currículo e descubra "
        "sua compatibilidade com o mercado, skills que faltam e vagas ideais.</p>",
        unsafe_allow_html=True,
    )

    rc1, rc2 = st.columns([2, 3])

    with rc1:
        st.markdown("##### 📝 Seu Currículo")
        resume_text = st.text_area(
            "Cole o conteúdo do seu currículo aqui",
            height=300,
            placeholder="Desenvolvedor Python com 3 anos de experiência em "
                        "Django, FastAPI, Docker, AWS...",
        )
        target_nivel = st.selectbox(
            "Nível alvo",
            ["Junior", "Pleno", "Sênior", "Especialista"],
            index=1, key="resume_nivel",
        )
        analyze_btn = st.button("🔍 Analisar Currículo", type="primary")

    with rc2:
        if analyze_btn and resume_text.strip():
            result = analyze_resume(resume_text, df_full, target_nivel)

            cor = (
                "#10b981" if result["score"] >= 60
                else "#f59e0b" if result["score"] >= 30
                else "#ef4444"
            )
            st.markdown(f"""
            <div style="background:#111827;border:1px solid #1e2d45;
                        border-radius:14px;padding:24px;text-align:center;
                        margin-bottom:16px">
                <div style="font-size:0.8rem;color:#64748b;text-transform:uppercase;
                            letter-spacing:0.1em">Compatibilidade com o Mercado</div>
                <div style="font-size:4rem;font-weight:700;color:{cor};
                            font-family:'JetBrains Mono',monospace;line-height:1.1">
                    {result["score"]:.0f}%
                </div>
                <div style="color:#94a3b8;font-size:0.9rem">
                    {result["compatible_count"]} de {result["total_vagas"]} vagas como {target_nivel}
                </div>
            </div>
            """, unsafe_allow_html=True)

            rm1, rm2 = st.columns(2)
            with rm1:
                sal = result["sal_esperado"]
                st.metric(
                    "💰 Salário Esperado",
                    f"R$ {sal:,.0f}" if sal else "N/A",
                )
            with rm2:
                st.metric("🎯 Skills Detectadas", f"{len(result['user_skills'])}")

            if result["user_skills"]:
                st.markdown("##### ✅ Skills no Currículo")
                skills_html = " ".join(
                    f"<span class='tag' style='color:#10b981;"
                    f"border-color:#10b98144'>{s}</span>"
                    for s in result["user_skills"]
                )
                st.markdown(skills_html, unsafe_allow_html=True)

            if result["missing_skills"]:
                st.markdown("##### 📚 Skills para Aprender")
                falta_df = pd.DataFrame(
                    result["missing_skills"], columns=["Skill", "Vagas"],
                )
                fig_f = px.bar(
                    falta_df, x="Vagas", y="Skill", orientation="h",
                    color="Vagas",
                    color_continuous_scale=[[0, "#1e2d45"], [1, "#f59e0b"]],
                    text="Vagas",
                )
                fig_f.update_layout(
                    **PLOTLY_LAYOUT, height=320, showlegend=False,
                    coloraxis_showscale=False,
                    yaxis={"categoryorder": "total ascending"},
                    margin=dict(l=10, r=10, t=10, b=10),
                )
                fig_f.update_traces(
                    textposition="inside",
                    textfont=dict(family="JetBrains Mono", size=10),
                )
                st.plotly_chart(fig_f, use_container_width=True)

            if result["lang_compatibility"]:
                st.markdown("##### 🎯 Compatibilidade por Stack")
                lc_items = list(result["lang_compatibility"].items())[:8]
                lc_df = pd.DataFrame([
                    {"Stack": k, "Compat": v} for k, v in lc_items
                ])
                fig_lc = px.bar(
                    lc_df, x="Stack", y="Compat", color="Compat",
                    color_continuous_scale=[[0, "#1e2d45"], [1, "#10b981"]],
                    text=lc_df["Compat"].apply(lambda x: f"{x:.0f}%"),
                )
                fig_lc.update_layout(
                    **PLOTLY_LAYOUT, height=280,
                    coloraxis_showscale=False,
                    xaxis_title="", yaxis_title="% Compatibilidade",
                )
                fig_lc.update_traces(
                    textposition="outside",
                    textfont=dict(family="JetBrains Mono", size=11),
                )
                st.plotly_chart(fig_lc, use_container_width=True)

        elif analyze_btn:
            st.warning("Cole o texto do seu currículo para analisar.")
        else:
            st.markdown("""
            <div class="insight-box" style="text-align:center;padding:40px">
                <div style="font-size:2.5rem">📄</div>
                <div style="color:#94a3b8;margin-top:8px">
                    Cole seu currículo ao lado e clique em
                    <b>Analisar Currículo</b>
                </div>
                <div style="color:#64748b;font-size:0.8rem;margin-top:12px">
                    💡 Dica: quanto mais detalhado o texto, melhor a análise
                </div>
            </div>
            """, unsafe_allow_html=True)


def render_tracker_tab():

    st.markdown("#### 📋 Job Tracker")
    st.markdown(
        "<p style='color:#64748b'>Acompanhe suas candidaturas. "
        "Adicione vagas e mova entre os estágios.</p>",
        unsafe_allow_html=True,
    )

    if "job_tracker" not in st.session_state:
        st.session_state.job_tracker = {
            "🔍 Interesse": [],
            "📤 Aplicado": [],
            "💬 Entrevista": [],
            "✅ Aprovado": [],
            "❌ Recusado": [],
        }

    st.markdown("##### ➕ Adicionar Vaga")
    jt1, jt2, jt3, jt4 = st.columns([3, 2, 2, 1])
    with jt1:
        new_cargo = st.text_input(
            "Cargo", placeholder="Dev Python Pleno", key="jt_cargo",
        )
    with jt2:
        new_empresa = st.text_input(
            "Empresa", placeholder="Nubank", key="jt_empresa",
        )
    with jt3:
        new_salario = st.text_input(
            "Salário", placeholder="R$ 12.000", key="jt_salario",
        )
    with jt4:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("Adicionar", key="jt_add"):
            if new_cargo:
                st.session_state.job_tracker["🔍 Interesse"].append({
                    "cargo": new_cargo,
                    "empresa": new_empresa or "—",
                    "salario": new_salario or "—",
                })
                st.rerun()

    st.markdown("---")

    stages = list(st.session_state.job_tracker.keys())
    stage_colors = ["#00d4ff", "#7c3aed", "#f59e0b", "#10b981", "#ef4444"]
    kanban_cols = st.columns(5)

    for idx, stage in enumerate(stages):
        with kanban_cols[idx]:
            color = stage_colors[idx]
            jobs = st.session_state.job_tracker[stage]
            st.markdown(f"""
            <div style="background:#111827;border:1px solid {color}44;
                        border-radius:10px;padding:12px;min-height:120px">
                <div style="font-size:0.85rem;font-weight:600;color:{color};
                            margin-bottom:10px;text-align:center">
                    {stage} ({len(jobs)})
                </div>
            </div>
            """, unsafe_allow_html=True)

            for i, job in enumerate(jobs):
                st.markdown(f"""
                <div class="card" style="padding:10px;margin-top:6px;
                            border-color:{color}33">
                    <div style="font-size:0.85rem;font-weight:600;
                                color:#e2e8f0">{job['cargo']}</div>
                    <div style="font-size:0.75rem;color:#64748b">
                        {job['empresa']} · {job['salario']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                move_cols = st.columns(2)
                if idx > 0:
                    with move_cols[0]:
                        if st.button("◀", key=f"prev_{stage}_{i}",
                                     help=f"Mover para {stages[idx-1]}"):
                            item = st.session_state.job_tracker[stage].pop(i)
                            st.session_state.job_tracker[stages[idx-1]].append(item)
                            st.rerun()
                if idx < len(stages) - 1:
                    with move_cols[1]:
                        if st.button("▶", key=f"next_{stage}_{i}",
                                     help=f"Mover para {stages[idx+1]}"):
                            item = st.session_state.job_tracker[stage].pop(i)
                            st.session_state.job_tracker[stages[idx+1]].append(item)
                            st.rerun()

    total_tracked = sum(len(v) for v in st.session_state.job_tracker.values())
    if total_tracked > 0:
        st.markdown("---")
        st1, st2, st3, st4 = st.columns(4)
        with st1:
            st.metric("Total Rastreadas", total_tracked)
        with st2:
            applied = len(st.session_state.job_tracker["📤 Aplicado"])
            st.metric("Aplicações", applied)
        with st3:
            interview = len(st.session_state.job_tracker["💬 Entrevista"])
            st.metric("Entrevistas", interview)
        with st4:
            approved = len(st.session_state.job_tracker["✅ Aprovado"])
            rate = (approved / total_tracked * 100) if total_tracked > 0 else 0
            st.metric("Taxa Sucesso", f"{rate:.0f}%")

        if st.button("🗑️ Limpar Tracker", key="clear_tracker"):
            for key in st.session_state.job_tracker:
                st.session_state.job_tracker[key] = []
            st.rerun()
