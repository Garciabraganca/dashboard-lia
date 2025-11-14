import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from tour_guide import render_tour_guide

st.set_page_config(
    page_title="App LIA • Dashboard AIDA",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

render_tour_guide()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
/* Forçar background preto e texto branco em tudo */
[data-testid="stSidebar"] {background: #000000 !important; border-right: 2px solid rgba(255, 255, 255, 0.2);}
[data-testid="stSidebar"] * {color: #ffffff !important;}
[data-testid="stSidebar"] h3 {font-size: 1.3rem; font-weight: 600;}
[data-testid="stSidebar"] h2 {font-size: 1.1rem;}
[data-testid="stSidebar"] p, [data-testid="stSidebar"] li {line-height: 1.6;}
body, .stApp {background: #000000 !important; color: #ffffff !important; font-family: 'Inter', sans-serif;}
/* Forçar todos os textos para branco */
* {color: #ffffff !important;}
h1, h2, h3, h4, h5, h6, p, span, div, label, input, textarea, select {color: #ffffff !important;}
.lia-header {background: rgba(255, 255, 255, 0.05); border-radius: 20px; padding: 2rem; margin-bottom: 2rem; border: 1px solid rgba(255, 255, 255, 0.2);}
.lia-title {font-size: 2.5rem; font-weight: 700; color: #ffffff !important; margin-bottom: 0.5rem;}
.lia-subtitle {font-size: 1rem; color: #ffffff !important; line-height: 1.6;}
.lia-subtitle strong {color: #ffffff !important;}
.lia-kpi-card {background: rgba(255, 255, 255, 0.05); border-radius: 16px; padding: 1.5rem; border: 1px solid rgba(255, 255, 255, 0.2); transition: all 0.3s ease; position: relative; overflow: hidden;}
.lia-kpi-card::before {content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: #ffffff;}
.lia-kpi-card:hover {transform: translateY(-5px); border-color: rgba(255, 255, 255, 0.4);}
.lia-kpi-label {font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; color: #ffffff !important; margin-bottom: 0.5rem; font-weight: 600;}
.lia-kpi-value {font-size: 2rem; font-weight: 700; color: #ffffff !important; margin-bottom: 0.3rem;}
.lia-kpi-helper {font-size: 0.8rem; color: #ffffff !important;}
.lia-kpi-badge {display: inline-block; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.75rem; font-weight: 600; margin-top: 0.5rem;}
.badge-success {background: rgba(255, 255, 255, 0.1); color: #ffffff !important; border: 1px solid rgba(255, 255, 255, 0.3);}
.badge-warning {background: rgba(255, 255, 255, 0.1); color: #ffffff !important; border: 1px solid rgba(255, 255, 255, 0.3);}
.badge-info {background: rgba(255, 255, 255, 0.1); color: #ffffff !important; border: 1px solid rgba(255, 255, 255, 0.3);}
.lia-section-header {display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 2px solid rgba(255, 255, 255, 0.2);}
.lia-section-icon {font-size: 1.8rem; color: #ffffff !important;}
.lia-section-title {font-size: 1.5rem; font-weight: 700; color: #ffffff !important; margin: 0;}
.lia-section-caption {font-size: 0.95rem; color: #ffffff !important; line-height: 1.6; margin-bottom: 1.5rem; padding: 1rem; background: rgba(255, 255, 255, 0.05); border-left: 3px solid #ffffff; border-radius: 4px;}
.lia-section-caption strong {color: #ffffff !important;}
.section-divider {height: 3px; background: #ffffff; margin: 3rem 0; border-radius: 2px;}
.funnel-stage {background: rgba(255, 255, 255, 0.05); border: 2px solid rgba(255, 255, 255, 0.3); border-radius: 12px; padding: 1rem; margin: 0.5rem 0; text-align: center; transition: all 0.3s ease;}
.funnel-stage:hover {background: rgba(255, 255, 255, 0.1); transform: scale(1.02);}
.funnel-value {font-size: 1.5rem; font-weight: 700; color: #ffffff !important;}
.funnel-label {font-size: 0.9rem; color: #ffffff !important; margin-top: 0.25rem;}
.funnel-conversion {font-size: 0.75rem; color: #ffffff !important; font-weight: 600; margin-top: 0.5rem;}
.lia-alert {background: rgba(255, 255, 255, 0.05); border-left: 4px solid #ffffff; border-radius: 8px; padding: 1rem 1.5rem; margin: 1.5rem 0; color: #ffffff !important;}
.lia-alert-title {font-weight: 600; color: #ffffff !important; margin-bottom: 0.5rem; font-size: 1.1rem;}
.lia-alert strong {color: #ffffff !important;}
.case-real-section {background: rgba(255, 255, 255, 0.05); border: 2px solid rgba(255, 255, 255, 0.2); border-radius: 20px; padding: 2rem; margin: 2rem 0;}
.projecao-section {background: rgba(255, 255, 255, 0.05); border: 2px solid rgba(255, 255, 255, 0.2); border-radius: 20px; padding: 2rem; margin: 2rem 0;}
/* Streamlit components específicos */
[data-testid="stMetricValue"] {color: #ffffff !important;}
[data-testid="stMetricLabel"] {color: #ffffff !important;}
[data-testid="stMetricDelta"] {color: #ffffff !important;}
[data-testid="stMarkdownContainer"] {color: #ffffff !important;}
[data-testid="stMarkdownContainer"] * {color: #ffffff !important;}
/* Tabelas */
.dataframe {color: #ffffff !important; background: rgba(255, 255, 255, 0.05) !important;}
.dataframe th {color: #ffffff !important; background: rgba(255, 255, 255, 0.1) !important;}
.dataframe td {color: #ffffff !important;}
/* Success/Info messages */
.stSuccess, .stInfo, .stWarning {background: rgba(255, 255, 255, 0.05) !important;}
.stSuccess *, .stInfo *, .stWarning * {color: #ffffff !important;}
@media (max-width: 768px) {
    .lia-title {font-size: 1.8rem;}
    .lia-kpi-value {font-size: 1.5rem;}
}
</style>
""", unsafe_allow_html=True)

# DADOS - CASE REAL BRADESCO
df_case = pd.DataFrame({"Período": ["01–30 Set", "15 Out – 13 Nov"], "Investimento (R$)": [2250.00, 3930.09], "Leads": [90, 206], "CPL (R$)": [25.00, 19.08], "Impressões": [185000, 352000], "Alcance": [128000, 245000]})
total_invest = df_case["Investimento (R$)"].sum()
total_leads = df_case["Leads"].sum()
overall_cpl = total_invest / total_leads
growth_leads_pct = (df_case.loc[1, "Leads"] - df_case.loc[0, "Leads"]) / df_case.loc[0, "Leads"] * 100
improv_cpl_pct = (df_case.loc[0, "CPL (R$)"] - df_case.loc[1, "CPL (R$)"]) / df_case.loc[0, "CPL (R$)"] * 100

stages = ["Impressões", "Cliques", "Visitas LP", "Cliques CTA", "Instalações"]
values = [100_000, 3_000, 900, 300, 120]
conversions = [(values[i] / values[i-1] * 100) if values[i-1] else 0 for i in range(1, len(values))]
df_week = pd.DataFrame({"Semana": ["S1", "S2", "S3", "S4", "S5"], "Instalações": [10, 18, 24, 28, 40]})
df_creatives = pd.DataFrame({"Criativo": ["🚨 Dor do WhatsApp", "💊 Feature Remédios", "💰 Feature Despesas"], "CPM (R$)": [8.50, 7.90, 9.20], "CPC (R$)": [0.85, 0.73, 0.92], "CTR (%)": [1.3, 1.5, 1.1], "Cliques": [1200, 1450, 980]})
df_lp = pd.DataFrame({"Métrica": ["Visitas", "Duração Média", "Taxa de Rejeição", "Cliques no CTA"], "Valor": ["900", "2m 34s", "45%", "300"], "Status": ["✅ Bom", "✅ Ótimo", "⚠️ Médio", "✅ Bom"]})
df_remarketing = pd.DataFrame({"Público": ["Visitantes LP", "Clicaram CTA", "E-mails Coletados"], "Tamanho": [900, 300, 245], "CTR (%)": [3.2, 4.5, 2.8], "Conversão": [15, 22, 12]})
df_installs = pd.DataFrame({"Plataforma": ["Google Play", "App Store"], "Instalações": [75, 45], "CPI (R$)": [12.50, 18.30]})
df_lookalike = pd.DataFrame({"Lookalike": ["Warm (Engajou)", "Cold (Lançamento)", "Retargeting (Abandonou)"], "Instalações": [45, 52, 23], "CPI (R$)": [12.50, 18.00, 10.20]})
df_actions = pd.DataFrame({"Ação": ["📊 Criar variações do criativo vencedor", "🎯 Expandir lookalike 3% do público warm", "🔄 Ativar retargeting visitantes LP", "🧪 A/B test na headline da LP", "💰 Escalar budget em +30%"], "Impacto Esperado": ["Alto", "Médio", "Médio", "Médio", "Alto"], "Prazo": ["Imediato", "1 semana", "Imediato", "2 semanas", "Gradual"]})

# HEADER
with st.container():
    st.markdown('<div id="intro" class="lia-header"><div class="lia-title">📊 Dashboard AIDA Completo</div><div class="lia-subtitle"><strong>Gestão de Tráfego & Performance</strong><br/>Metodologia AIDA + Cases Reais Comprovados</div></div>', unsafe_allow_html=True)

# METODOLOGIA AIDA
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
with st.container():
    st.markdown('<div id="metodologia_aida" class="lia-section-header"><span class="lia-section-icon">💡</span><h2 class="lia-section-title">Como Aplicamos a Metodologia AIDA</h2></div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <div style="font-size: 2.5rem; margin-bottom: 1.5rem;">📊</div>
        <h3 style="color: #f1f5f9; margin-bottom: 1rem;">O Framework AIDA</h3>
        <div style="font-size: 1.3rem; color: #818cf8; margin-bottom: 2rem;">
            <strong>A</strong>tenção → <strong>I</strong>nteresse → <strong>D</strong>esejo → <strong>A</strong>ção
        </div>
        <p style="color: #cbd5e1; font-size: 1.1rem; line-height: 1.8; max-width: 800px; margin: 0 auto;">
            Esta é a estrutura que usamos em <strong>TODAS</strong> as nossas campanhas:
        </p>
        <div style="display: flex; justify-content: center; gap: 2rem; margin-top: 1.5rem; flex-wrap: wrap;">
            <div style="color: #cbd5e1;">✅ Segmentação precisa</div>
            <div style="color: #cbd5e1;">✅ Criativos testados</div>
            <div style="color: #cbd5e1;">✅ LPs otimizadas</div>
            <div style="color: #cbd5e1;">✅ Conversão maximizada</div>
        </div>
        <p style="color: #4ade80; font-size: 1.1rem; margin-top: 1.5rem;"><strong>Resultado:</strong> Campanhas previsíveis e escaláveis.</p>
    </div>
    """, unsafe_allow_html=True)

# PROJEÇÃO APP LIA
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
with st.container():
    st.markdown('<div id="projecao_lia" class="projecao-section">', unsafe_allow_html=True)
    st.markdown('<div class="lia-section-header"><span class="lia-section-icon">📱</span><h2 class="lia-section-title">EXEMPLO DE APLICAÇÃO • Projeção App LIA</h2></div><div class="lia-section-caption"><strong>⚠️ IMPORTANTE:</strong> Os dados abaixo são projeções baseadas no <strong>briefing do App LIA</strong>.<br/>Esta seção demonstra <strong>como o framework AIDA seria aplicado</strong> em uma campanha de app mobile.</div>', unsafe_allow_html=True)
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: st.markdown('<div class="lia-kpi-card"><div class="lia-kpi-label">⭐ North Star</div><div class="lia-kpi-value">120</div><div class="lia-kpi-helper">Instalações projetadas</div><span class="lia-kpi-badge badge-info">Meta inicial</span></div>', unsafe_allow_html=True)
    with col2: st.markdown('<div class="lia-kpi-card"><div class="lia-kpi-label">💰 CPI Projetado</div><div class="lia-kpi-value">R$ 15,00</div><div class="lia-kpi-helper">Custo por instalação</div><span class="lia-kpi-badge badge-warning">Estimativa</span></div>', unsafe_allow_html=True)
    with col3: st.markdown('<div class="lia-kpi-card"><div class="lia-kpi-label">📈 Crescimento</div><div class="lia-kpi-value">+43%</div><div class="lia-kpi-helper">Semana a semana</div><span class="lia-kpi-badge badge-info">Projeção</span></div>', unsafe_allow_html=True)
    with col4: st.markdown('<div class="lia-kpi-card"><div class="lia-kpi-label">💵 Budget</div><div class="lia-kpi-value">R$ 1.800</div><div class="lia-kpi-helper">Investimento inicial</div><span class="lia-kpi-badge badge-info">5 semanas</span></div>', unsafe_allow_html=True)
    with col5: st.markdown('<div class="lia-kpi-card"><div class="lia-kpi-label">📊 ROI</div><div class="lia-kpi-value">A definir</div><div class="lia-kpi-helper">Após LTV conhecido</div><span class="lia-kpi-badge badge-warning">Análise futura</span></div>', unsafe_allow_html=True)
    
    st.markdown("#### 📈 Projeção de Crescimento Semanal")
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(x=df_week["Semana"], y=df_week["Instalações"], mode="lines+markers", line=dict(color="#818cf8", width=3), marker=dict(size=12, color="#c084fc"), fill="tozeroy", fillcolor="rgba(129, 140, 248, 0.2)", name="Instalações"))
    fig_line.update_layout(template="plotly_dark", height=350, margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis=dict(showgrid=False, title="Semana"), yaxis=dict(showgrid=True, gridcolor="rgba(148, 163, 184, 0.1)", title="Instalações"), font=dict(size=12, color="#cbd5e1"))
    st.plotly_chart(fig_line)
    st.markdown('</div>', unsafe_allow_html=True)

# FUNIL AIDA
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
with st.container():
    st.markdown('<div id="funil_aida" class="lia-section-header"><span class="lia-section-icon">🪜</span><h2 class="lia-section-title">Estrutura Completa do Funil AIDA</h2></div><div class="lia-section-caption">Visão macro das 4 etapas: <strong>Atenção</strong> → <strong>Interesse</strong> → <strong>Desejo</strong> → <strong>Ação</strong></div>', unsafe_allow_html=True)
    col_f1, col_f2 = st.columns([3, 2])
    with col_f1:
        df_funnel = pd.DataFrame({"Etapa": stages, "Quantidade": values})
        fig_funnel = go.Figure(go.Funnel(y=df_funnel["Etapa"], x=df_funnel["Quantidade"], textinfo="value+percent initial", marker=dict(color=["#818cf8", "#a78bfa", "#c084fc", "#e879f9", "#f0abfc"])))
        fig_funnel.update_layout(template="plotly_dark", height=450, margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(size=13, color="#cbd5e1"))
        st.plotly_chart(fig_funnel)
    with col_f2:
        st.markdown("#### 📊 Taxa de Conversão")
        for i in range(1, len(stages)):
            conv = conversions[i-1]
            st.markdown(f'<div class="funnel-stage"><div class="funnel-label">{stages[i-1]} → {stages[i]}</div><div class="funnel-value">{conv:.1f}%</div><div class="funnel-conversion">✓ Taxa de conversão</div></div>', unsafe_allow_html=True)

# 4 ETAPAS DETALHADAS
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
with st.container():
    st.markdown('<div id="etapa_atencao" class="lia-section-header"><span class="lia-section-icon">👁️</span><h2 class="lia-section-title">1. ATENÇÃO • Impressões & Alcance</h2></div>', unsafe_allow_html=True)
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        st.metric("📊 Impressões", "100.000", "+23%")
        st.caption("Total de exibições do anúncio")
        st.metric("👥 Alcance", "75.000", "+18%")
        st.caption("Pessoas únicas alcançadas")
    with col_a2:
        st.metric("💰 CPM", "R$ 8,20", "-12%")
        st.caption("Custo por mil impressões")
        st.metric("📈 Frequência", "1,33", "")
        st.caption("Vezes que cada pessoa viu")

with st.container():
    st.markdown('<div id="etapa_interesse" class="lia-section-header"><span class="lia-section-icon">🖱️</span><h2 class="lia-section-title">2. INTERESSE • Cliques & Engajamento</h2></div>', unsafe_allow_html=True)
    col_i1, col_i2 = st.columns([2, 3])
    with col_i1:
        st.metric("🖱️ Cliques", "3.000", "+15%")
        st.metric("📊 CTR", "3,0%", "+8%")
        st.metric("💵 CPC", "R$ 0,80", "-18%")
    with col_i2:
        fig_creative = px.bar(df_creatives, x="Criativo", y="Cliques", text="Cliques", title="Performance por Criativo", template="plotly_dark", color="CTR (%)", color_continuous_scale="Purples")
        fig_creative.update_traces(textposition="outside")
        fig_creative.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
        st.plotly_chart(fig_creative)
    st.dataframe(df_creatives.style.format({"CPM (R$)": "R$ {:.2f}", "CPC (R$)": "R$ {:.2f}", "CTR (%)": "{:.1f}%"}), hide_index=True)

with st.container():
    st.markdown('<div id="etapa_desejo" class="lia-section-header"><span class="lia-section-icon">🎯</span><h2 class="lia-section-title">3. DESEJO • Landing Page</h2></div>', unsafe_allow_html=True)
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.metric("🌐 Visitas LP", "900", "+12%")
        st.metric("⏱️ Tempo Médio", "2m 34s", "+20%")
    with col_d2:
        st.metric("🚪 Taxa Rejeição", "45%", "-5%")
        st.metric("🖱️ Cliques CTA", "300", "+18%")
    st.dataframe(df_lp, hide_index=True)

with st.container():
    st.markdown('<div id="etapa_acao" class="lia-section-header"><span class="lia-section-icon">📲</span><h2 class="lia-section-title">4. AÇÃO • Instalações</h2></div>', unsafe_allow_html=True)
    col_ac1, col_ac2 = st.columns([2, 3])
    with col_ac1:
        st.metric("📲 Instalações", "120", "+40%")
        st.metric("💰 CPI", "R$ 15,00", "-25%")
        st.metric("📊 Taxa Conversão", "40%", "+12%")
    with col_ac2:
        fig_install = px.pie(df_installs, names="Plataforma", values="Instalações", title="Distribuição de Instalações", template="plotly_dark", color_discrete_sequence=["#818cf8", "#c084fc"])
        fig_install.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_install)
    st.dataframe(df_installs.style.format({"CPI (R$)": "R$ {:.2f}"}), hide_index=True)

# REMARKETING E LOOKALIKE
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
with st.container():
    st.markdown('<div id="remarketing" class="lia-section-header"><span class="lia-section-icon">🔄</span><h2 class="lia-section-title">Remarketing • Reengajamento</h2></div>', unsafe_allow_html=True)
    st.dataframe(df_remarketing.style.format({"CTR (%)": "{:.1f}%"}), hide_index=True)

with st.container():
    st.markdown('<div id="lookalike" class="lia-section-header"><span class="lia-section-icon">🎯</span><h2 class="lia-section-title">Lookalike • Expansão</h2></div>', unsafe_allow_html=True)
    st.dataframe(df_lookalike.style.format({"CPI (R$)": "R$ {:.2f}"}), hide_index=True)

# PRÓXIMOS PASSOS
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
with st.container():
    st.markdown('<div id="proximos_passos" class="lia-section-header"><span class="lia-section-icon">🚀</span><h2 class="lia-section-title">Próximos Passos • Plano de Ação</h2></div>', unsafe_allow_html=True)
    st.dataframe(df_actions, hide_index=True)

# CASE REAL
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
with st.container():
    st.markdown('<div id="case_real" class="case-real-section">', unsafe_allow_html=True)
    st.markdown('<div class="lia-section-header"><span class="lia-section-icon">✅</span><h2 class="lia-section-title">CASE REAL DE SUCESSO • Campanha Bradesco</h2></div><div class="lia-section-caption"><strong>📍 Cliente:</strong> Grupo Garcia Seguradoras<br/><strong>📢 Campanha:</strong> Bradesco - Captação de Profissionais<br/><strong>🎯 Objetivo:</strong> Recrutamento via Meta Ads<br/><strong>📅 Período:</strong> Setembro - Novembro 2024<br/><strong>✅ Status:</strong> Campanha finalizada com sucesso</div>', unsafe_allow_html=True)

    st.markdown("###")
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.markdown(f'<div class="lia-kpi-card"><div class="lia-kpi-label">💵 Investimento Total</div><div class="lia-kpi-value">R$ {total_invest:,.2f}</div><div class="lia-kpi-helper">Soma dos dois períodos</div><span class="lia-kpi-badge badge-info">Mídia Meta Ads</span></div>', unsafe_allow_html=True)
    with k2: st.markdown(f'<div class="lia-kpi-card"><div class="lia-kpi-label">👥 Leads Gerados</div><div class="lia-kpi-value">{int(total_leads)}</div><div class="lia-kpi-helper">Candidatos qualificados</div><span class="lia-kpi-badge badge-success">+{growth_leads_pct:.0f}% crescimento</span></div>', unsafe_allow_html=True)
    with k3: st.markdown(f'<div class="lia-kpi-card"><div class="lia-kpi-label">🎯 CPL Médio</div><div class="lia-kpi-value">R$ {overall_cpl:,.2f}</div><div class="lia-kpi-helper">Custo por lead consolidado</div><span class="lia-kpi-badge badge-success">Otimizado</span></div>', unsafe_allow_html=True)
    with k4: st.markdown(f'<div class="lia-kpi-card"><div class="lia-kpi-label">📉 Redução de CPL</div><div class="lia-kpi-value">-{improv_cpl_pct:.1f}%</div><div class="lia-kpi-helper">2º ciclo vs 1º ciclo</div><span class="lia-kpi-badge badge-success">Eficiência++</span></div>', unsafe_allow_html=True)

    st.markdown("###")
    c1, c2 = st.columns(2)
    with c1:
        fig_case_leads = px.bar(df_case, x="Período", y="Leads", text="Leads", title="👥 Evolução de Leads Gerados", template="plotly_dark")
        fig_case_leads.update_traces(textposition="outside", marker_color=["#818cf8", "#c084fc"])
        fig_case_leads.update_layout(height=350, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#cbd5e1"))
        st.plotly_chart(fig_case_leads)
    with c2:
        fig_case_cpl = px.bar(df_case, x="Período", y="CPL (R$)", text="CPL (R$)", title="💰 Evolução do Custo por Lead", template="plotly_dark")
        fig_case_cpl.update_traces(texttemplate="R$ %{text:.2f}", textposition="outside", marker_color=["#f97316", "#22c55e"])
        fig_case_cpl.update_layout(height=350, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#cbd5e1"))
        st.plotly_chart(fig_case_cpl)

    st.markdown("#### 📊 Métricas Completas do Case")
    st.dataframe(df_case.style.format({"Investimento (R$)": "R$ {:.2f}", "CPL (R$)": "R$ {:.2f}", "Impressões": "{:,.0f}", "Alcance": "{:,.0f}"}), hide_index=True)
    st.markdown('<div class="lia-alert"><div class="lia-alert-title">🎯 Principais Resultados e Aprendizados</div><strong>✅ Escalabilidade Comprovada:</strong> O segundo ciclo gerou mais de <strong>2x mais leads</strong> que o primeiro.<br/><strong>✅ Otimização Efetiva:</strong> CPL caiu <strong>23,7%</strong> com ajustes de segmentação e criativos.<br/><strong>✅ Volume com Qualidade:</strong> Alcance quase dobrou mantendo taxa de conversão estável.<br/><strong>✅ ROI Positivo:</strong> Cliente aprovou continuidade da parceria para novas vagas.</div>', unsafe_allow_html=True)

    # Botão para baixar mais cases
    st.markdown("###")
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        st.markdown("""
        <a href="https://drive.google.com/file/d/1ulmViwENe9wvzXgAxDgMLMomlN5yhIxn/view?usp=sharing" target="_blank">
            <button style="
                width: 100%;
                background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
                color: white;
                padding: 1rem 2rem;
                font-size: 1.1rem;
                font-weight: 600;
                border: none;
                border-radius: 12px;
                cursor: pointer;
                box-shadow: 0 8px 24px rgba(34, 197, 94, 0.4);
                transition: all 0.3s ease;
            " onmouseover="this.style.transform='translateY(-3px)'; this.style.boxShadow='0 12px 32px rgba(34, 197, 94, 0.5)';" onmouseout="this.style.transform='translateY(0px)'; this.style.boxShadow='0 8px 24px rgba(34, 197, 94, 0.4)';">
                📥 Baixar Mais Cases de Sucesso
            </button>
        </a>
        """, unsafe_allow_html=True)
        st.caption("Acesse nossa biblioteca completa de casos reais comprovados")

    st.markdown('</div>', unsafe_allow_html=True)

# FOOTER
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
st.markdown("---")
st.success("✅ Dashboard completo com Case Real Bradesco + Framework AIDA aplicável!")
