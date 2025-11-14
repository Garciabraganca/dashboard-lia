import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from tour_guide import render_tour_guide, TOUR_SECTIONS

# ---------------- CONFIG GERAL ----------------
st.set_page_config(
    page_title="App LIA • Dashboard AIDA",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Aviso para quem acessar pelo celular (sidebar)
st.info(
    "📱 **Se estiver no celular (iOS ou Android)**, toque no ícone ☰ no canto superior esquerdo "
    "para abrir o menu lateral e navegar pelo tour guiado."
)

# ---------------- TOUR GUIADO ----------------
render_tour_guide()

# ---------------- ESTILO GLOBAL (CSS) ----------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Crimson+Text:wght@400;600&display=swap');
    
    [data-testid="stSidebar"] {
        background: linear-gradient(135deg, #2d1810 0%, #1a0f0a 100%);
        border-right: 3px solid #8b6f47;
        box-shadow: inset 0 0 50px rgba(0,0,0,0.5);
    }
    
    [data-testid="stSidebar"] > div:first-child {
        background: linear-gradient(to bottom, 
            rgba(222, 184, 135, 0.1) 0%,
            rgba(205, 133, 63, 0.05) 50%,
            rgba(139, 111, 71, 0.1) 100%);
        padding: 1.5rem;
        transform-origin: top center;
        animation: scroll-open 0.7s ease-out;
    }

    @keyframes scroll-open {
        0% {
            transform: scaleY(0.2);
            opacity: 0;
        }
        100% {
            transform: scaleY(1);
            opacity: 1;
        }
    }
    
    [data-testid="stSidebar"] h3 {
        color: #deb887;
        font-family: 'Crimson Text', serif;
        font-size: 1.4rem;
        text-align: center;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        margin-bottom: 1rem;
    }
    
    [data-testid="stSidebar"] h2 {
        color: #f4a460;
        font-family: 'Crimson Text', serif;
        font-size: 1.3rem;
        margin-top: 1rem;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
    }
    
    [data-testid="stSidebar"] .stRadio > label {
        color: #deb887 !important;
        font-family: 'Crimson Text', serif;
        font-size: 1.1rem;
    }
    
    [data-testid="stSidebar"] [data-baseweb="radio"] {
        background: rgba(139, 111, 71, 0.2);
        border-radius: 8px;
        padding: 0.5rem;
        margin: 0.3rem 0;
        border-left: 3px solid #8b6f47;
    }
    
    [data-testid="stSidebar"] [data-baseweb="radio"]:hover {
        background: rgba(139, 111, 71, 0.4);
        border-left: 3px solid #deb887;
    }
    
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] li,
    [data-testid="stSidebar"] div {
        color: #e8dcc4 !important;
        font-family: 'Inter', sans-serif;
        line-height: 1.6;
    }
    
    [data-testid="stSidebar"] strong {
        color: #f4a460 !important;
    }
    
    [data-testid="stSidebar"] hr {
        border-color: #8b6f47;
        opacity: 0.5;
    }
    
    [data-testid="stSidebar"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 20px;
        background: linear-gradient(90deg, 
            transparent 0%, 
            rgba(139, 111, 71, 0.3) 25%,
            transparent 50%,
            rgba(139, 111, 71, 0.3) 75%,
            transparent 100%);
    }
    
    body, .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        color: #e5e7eb;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    .lia-header {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%);
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 2rem;
        border: 1px solid rgba(99, 102, 241, 0.2);
        box-shadow: 0 20px 60px rgba(99, 102, 241, 0.15);
    }
    
    .lia-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #818cf8 0%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .lia-subtitle {
        font-size: 1rem;
        color: #cbd5e1;
        line-height: 1.6;
    }
    
    .lia-kpi-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid rgba(148, 163, 184, 0.2);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .lia-kpi-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #818cf8, #c084fc);
    }
    
    .lia-kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(99, 102, 241, 0.3);
        border-color: rgba(99, 102, 241, 0.4);
    }
    
    .lia-kpi-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #94a3b8;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }
    
    .lia-kpi-value {
        font-size: 2rem;
        font-weight: 700;
        color: #f1f5f9;
        margin-bottom: 0.3rem;
    }
    
    .lia-kpi-helper {
        font-size: 0.8rem;
        color: #64748b;
    }
    
    .lia-kpi-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-top: 0.5rem;
    }
    
    .badge-success {
        background: rgba(34, 197, 94, 0.2);
        color: #4ade80;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }
    
    .badge-warning {
        background: rgba(251, 191, 36, 0.2);
        color: #fbbf24;
        border: 1px solid rgba(251, 191, 36, 0.3);
    }
    
    .badge-info {
        background: rgba(59, 130, 246, 0.2);
        color: #60a5fa;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }
    
    .lia-section-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid rgba(148, 163, 184, 0.2);
    }
    
    .lia-section-icon {
        font-size: 1.5rem;
    }
    
    .lia-section-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #f1f5f9;
        margin: 0;
    }
    
    .lia-section-caption {
        font-size: 0.875rem;
        color: #94a3b8;
        line-height: 1.5;
        margin-bottom: 1rem;
    }

    .funnel-stage {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%);
        border: 2px solid rgba(99, 102, 241, 0.3);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        text-align: center;
    }
    
    .funnel-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #818cf8;
    }
    
    .funnel-label {
        font-size: 0.875rem;
        color: #cbd5e1;
        margin-top: 0.25rem;
    }
    
    .funnel-conversion {
        font-size: 0.75rem;
        color: #4ade80;
        font-weight: 600;
        margin-top: 0.5rem;
    }

    .lia-alert {
        background: rgba(59, 130, 246, 0.1);
        border-left: 4px solid #3b82f6;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin: 1rem 0;
        color: #cbd5e1;
    }
    
    .lia-alert-title {
        font-weight: 600;
        color: #60a5fa;
        margin-bottom: 0.25rem;
    }

    @media (max-width: 768px) {
        .lia-title {
            font-size: 1.8rem;
        }
        .lia-kpi-value {
            font-size: 1.5rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------- DADOS ----------------
stages = ["Impressões", "Cliques", "Visitas LP", "Cliques CTA", "Instalações"]
values = [100_000, 3_000, 900, 300, 120]

conversions = []
for i in range(1, len(values)):
    prev = values[i - 1]
    rate = (values[i] / prev * 100) if prev else 0
    conversions.append(rate)

df_week = pd.DataFrame({
    "Semana": ["S1", "S2", "S3", "S4", "S5"],
    "Instalações": [10, 18, 24, 28, 40],
})

df_case = pd.DataFrame({
    "Período": ["01–30 Set", "15 Out – 13 Nov"],
    "Investimento (R$)": [137.65, 247.93],
    "Leads": [14, 41],
    "CPL (R$)": [9.83, 6.04],
    "Impressões": [5912, 11355],
    "Alcance": [4085, 7874],
})

total_invest = df_case["Investimento (R$)"].sum()
total_leads = df_case["Leads"].sum()
overall_cpl = total_invest / total_leads
growth_leads_pct = (df_case.loc[1, "Leads"] - df_case.loc[0, "Leads"]) / df_case.loc[0, "Leads"] * 100
improv_cpl_pct = (df_case.loc[0, "CPL (R$)"] - df_case.loc[1, "CPL (R$)"]) / df_case.loc[0, "CPL (R$)"] * 100

df_creatives = pd.DataFrame({
    "Criativo": ["🚨 Dor do WhatsApp", "💊 Feature Remédios", "💰 Feature Despesas"],
    "CPM (R$)": [8.50, 7.90, 9.20],
    "CPC (R$)": [0.85, 0.73, 0.92],
    "CTR (%)": [1.3, 1.5, 1.1],
    "Cliques": [1200, 1450, 980],
})

df_lp = pd.DataFrame({
    "Métrica": ["Visitas", "Duração Média", "Taxa de Rejeição", "Cliques no CTA"],
    "Valor": ["900", "2m 34s", "45%", "300"],
    "Status": ["✅ Bom", "✅ Ótimo", "⚠️ Médio", "✅ Bom"],
})

df_remarketing = pd.DataFrame({
    "Público": ["Visitantes LP", "Clicaram CTA", "E-mails Coletados"],
    "Tamanho": [900, 300, 245],
    "CTR (%)": [3.2, 4.5, 2.8],
    "Conversão": [15, 22, 12],
})

df_installs = pd.DataFrame({
    "Plataforma": ["Google Play", "App Store"],
    "Instalações": [75, 45],
    "CPI (R$)": [12.50, 18.30],
})

df_lookalike = pd.DataFrame({
    "Lookalike": ["Warm (Engajou)", "Cold (Lançamento)", "Retargeting (Abandonou)"],
    "Instalações": [45, 52, 23],
    "CPI (R$)": [12.50, 18.00, 10.20],
})

df_actions = pd.DataFrame({
    "Ação": [
        "📊 Criar variações do criativo vencedor (Feature Remédios)",
        "🎯 Expandir lookalike 3% do público warm",
        "🔄 Ativar retargeting de visitantes LP (últimos 7 dias)",
        "🧪 A/B test na headline da LP",
        "💰 Escalar budget em +30% no melhor segmento",
    ],
    "Impacto Esperado": ["Alto", "Médio", "Médio", "Médio", "Alto"],
    "Prazo": ["Imediato", "1 semana", "Imediato", "2 semanas", "Gradual"],
})

# ---------------- LAYOUT ----------------

with st.container():
    logo_cols = st.columns([1, 1, 2])

    with logo_cols[0]:
        try:
            st.image("lia-logo.png", use_column_width=True)
        except Exception:
            st.write("")

    with logo_cols[1]:
        try:
            st.image("logotipo-gb.png", use_column_width=True)
        except Exception:
            st.write("")

    with logo_cols[2]:
        st.markdown(
            """
            <div class="lia-header">
                <div class="lia-title">📊 App LIA • Dashboard AIDA</div>
                <div class="lia-subtitle">
                    Visão executiva das campanhas geridas pelo <strong>Grupo Garcia</strong>.<br/>
                    Estrutura completa do funil AIDA + Case real de captação de profissionais de limpeza para RH.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ---------- RESUMO EXECUTIVO ----------
with st.container():
    st.markdown(
        """
        <div class="lia-section-header">
            <span class="lia-section-icon">🎯</span>
            <h2 class="lia-section-title">Resumo Executivo – App LIA (Exemplo de Funil AIDA)</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(
        """
        <div class="lia-kpi-card">
            <div class="lia-kpi-label">⭐ North Star</div>
            <div class="lia-kpi-value">120</div>
            <div class="lia-kpi-helper">Instalações totais</div>
            <span class="lia-kpi-badge badge-success">+40% vs S4</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
        <div class="lia-kpi-card">
            <div class="lia-kpi-label">💰 CPI</div>
            <div class="lia-kpi-value">R$ 15,00</div>
            <div class="lia-kpi-helper">Custo por instalação</div>
            <span class="lia-kpi-badge badge-success">Meta: R$ 20</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        """
        <div class="lia-kpi-card">
            <div class="lia-kpi-label">📈 Crescimento</div>
            <div class="lia-kpi-value">+43%</div>
            <div class="lia-kpi-helper">vs período anterior</div>
            <span class="lia-kpi-badge badge-success">Tendência ↗️</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col4:
    st.markdown(
        """
        <div class="lia-kpi-card">
            <div class="lia-kpi-label">💵 Investimento</div>
            <div class="lia-kpi-value">R$ 1.800</div>
            <div class="lia-kpi-helper">Mídia + produção</div>
            <span class="lia-kpi-badge badge-info">Budget: R$ 5k</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col5:
    st.markdown(
        """
        <div class="lia-kpi-card">
            <div class="lia-kpi-label">📊 ROI</div>
            <div class="lia-kpi-value">A definir</div>
            <div class="lia-kpi-helper">Aguarda LTV/usuário</div>
            <span class="lia-kpi-badge badge-warning">Em análise</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------- CASE REAL ----------
with st.container():
    st.markdown(
        """
        <div class="lia-section-header">
            <span class="lia-section-icon">🧹</span>
            <h2 class="lia-section-title">Case Real – Captação de Profissionais de Limpeza</h2>
        </div>
        <div class="lia-section-caption">
            Campanha de recrutamento via Meta Ads focada em profissionais de limpeza.
        </div>
        """,
        unsafe_allow_html=True,
    )

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        st.markdown(
            f"""
            <div class="lia-kpi-card">
                <div class="lia-kpi-label">💵 Investimento Total</div>
                <div class="lia-kpi-value">R$ {total_invest:,.2f}</div>
                <div class="lia-kpi-helper">Soma dos dois períodos</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k2:
        st.markdown(
            f"""
            <div class="lia-kpi-card">
                <div class="lia-kpi-label">👥 Leads Gerados</div>
                <div class="lia-kpi-value">{int(total_leads)}</div>
                <div class="lia-kpi-helper">Candidatos interessados</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k3:
        st.markdown(
            f"""
            <div class="lia-kpi-card">
                <div class="lia-kpi-label">🎯 CPL Médio</div>
                <div class="lia-kpi-value">R$ {overall_cpl:,.2f}</div>
                <div class="lia-kpi-helper">Custo por lead consolidado</div>
                <span class="lia-kpi-badge badge-success">Otimização contínua</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k4:
        st.markdown(
            f"""
            <div class="lia-kpi-card">
                <div class="lia-kpi-label">📉 Redução de CPL</div>
                <div class="lia-kpi-value">-{improv_cpl_pct:.1f}%</div>
                <div class="lia-kpi-helper">2º ciclo vs 1º ciclo</div>
                <span class="lia-kpi-badge badge-success">Mais eficiência</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    c1, c2 = st.columns(2)

    with c1:
        fig_case_leads = px.bar(
            df_case,
            x="Período",
            y="Leads",
            text="Leads",
            title="👥 Leads por Período",
            template="plotly_dark",
        )
        fig_case_leads.update_traces(
            textposition="outside",
            marker_color=["#818cf8", "#c084fc"],
        )
        fig_case_leads.update_layout(
            height=320,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_case_leads, use_container_width=True)

    with c2:
        fig_case_cpl = px.bar(
            df_case,
            x="Período",
            y="CPL (R$)",
            text="CPL (R$)",
            title="💰 CPL por Período",
            template="plotly_dark",
        )
        fig_case_cpl.update_traces(
            texttemplate="R$ %{text:.2f}",
            textposition="outside",
            marker_color=["#f97316", "#22c55e"],
        )
        fig_case_cpl.update_layout(
            height=320,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_case_cpl, use_container_width=True)

    st.dataframe(
        df_case.style.format({
            "Investimento (R$)": "R$ {:.2f}",
            "CPL (R$)": "R$ {:.2f}",
            "Impressões": "{:,.0f}",
            "Alcance": "{:,.0f}",
        }),
        use_container_width=True,
        hide_index=True,
    )

# ---------- EVOLUÇÃO SEMANAL ----------
with st.container():
    st.markdown(
        """
        <div class="lia-section-header">
            <span class="lia-section-icon">📈</span>
            <h2 class="lia-section-title">Evolução Semanal – Instalações</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

fig_line = go.Figure()
fig_line.add_trace(go.Scatter(
    x=df_week["Semana"],
    y=df_week["Instalações"],
    mode="lines+markers",
    line=dict(color="#818cf8", width=3),
    marker=dict(size=10, color="#c084fc"),
    fill="tozeroy",
    fillcolor="rgba(129, 140, 248, 0.1)",
))

fig_line.update_layout(
    template="plotly_dark",
    height=320,
    margin=dict(l=20, r=20, t=20, b=20),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(showgrid=False),
    yaxis=dict(showgrid=True, gridcolor="rgba(148, 163, 184, 0.1)"),
    font=dict(size=12, color="#cbd5e1"),
)

st.plotly_chart(fig_line, use_container_width=True)

# ---------- FUNIL AIDA ----------
with st.container():
    st.markdown(
        """
        <div class="lia-section-header">
            <span class="lia-section-icon">🪜</span>
            <h2 class="lia-section-title">Funil AIDA • Visão Macro</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

col_f1, col_f2 = st.columns([3, 2])

with col_f1:
    df_funnel = pd.DataFrame({"Etapa": stages, "Quantidade": values})
    
    fig_funnel = go.Figure(go.Funnel(
        y=df_funnel["Etapa"],
        x=df_funnel["Quantidade"],
        textinfo="value+percent initial",
        marker=dict(
            color=["#818cf8", "#a78bfa", "#c084fc", "#e879f9", "#f0abfc"],
        ),
    ))
    
    fig_funnel.update_layout(
        template="plotly_dark",
        height=400,
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(size=12, color="#cbd5e1"),
    )
    
    st.plotly_chart(fig_funnel, use_container_width=True)

with col_f2:
    st.markdown("**📊 Taxa de Conversão por Etapa**")
    
    for i in range(1, len(stages)):
        conv = conversions[i-1]
        st.markdown(
            f"""
            <div class="funnel-stage">
                <div class="funnel-label">{stages[i-1]} → {stages[i]}</div>
                <div class="lia-kpi-value">{conv:.1f}%</div>
                <div class="funnel-conversion">✓ Conversão</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ---------- ATENÇÃO ----------
with st.container():
    st.markdown(
        """
        <div class="lia-section-header">
            <span class="lia-section-icon">👁️</span>
            <h2 class="lia-section-title">1. ATENÇÃO • Impressões & Alcance</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_a1, col_a2 = st.columns(2)

    with col_a1:
        st.metric("📊 Impressões", "100.000", "+23%")
        st.caption("Total de vezes que o anúncio foi exibido")
        
        st.metric("👥 Alcance", "75.000", "+18%")
        st.caption("Pessoas únicas que viram o anúncio")

    with col_a2:
        st.metric("💰 CPM", "R$ 8,20", "-12%")
        st.caption("Custo por mil impressões")
        
        st.metric("📈 Frequência", "1,33", "")
        st.caption("Média de vezes que cada pessoa viu")

# ---------- INTERESSE ----------
with st.container():
    st.markdown(
        """
        <div class="lia-section-header">
            <span class="lia-section-icon">🖱️</span>
            <h2 class="lia-section-title">2. INTERESSE • Cliques & Engajamento</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_i1, col_i2 = st.columns([2, 3])

    with col_i1:
        st.metric("🖱️ Cliques", "3.000", "+15%")
        st.metric("📊 CTR", "3,0%", "+8%")
        st.metric("💵 CPC", "R$ 0,80", "-18%")

    with col_i2:
        fig_creative = px.bar(
            df_creatives,
            x="Criativo",
            y="Cliques",
            text="Cliques",
            title="Cliques por Criativo",
            template="plotly_dark",
        )
        fig_creative.update_traces(textposition="outside")
        fig_creative.update_layout(
            height=300,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_creative, use_container_width=True)

# ---------- DESEJO ----------
with st.container():
    st.markdown(
        """
        <div class="lia-section-header">
            <span class="lia-section-icon">🎯</span>
            <h2 class="lia-section-title">3. DESEJO • Landing Page</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_d1, col_d2 = st.columns(2)

    with col_d1:
        st.metric("🌐 Visitas LP", "900", "+12%")
        st.metric("⏱️ Tempo Médio", "2m 34s", "+20%")

    with col_d2:
        st.metric("🚪 Taxa Rejeição", "45%", "-5%")
        st.metric("🖱️ Cliques CTA", "300", "+18%")

# ---------- AÇÃO ----------
with st.container():
    st.markdown(
        """
        <div class="lia-section-header">
            <span class="lia-section-icon">📲</span>
            <h2 class="lia-section-title">4. AÇÃO • Instalações</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_ac1, col_ac2 = st.columns([2, 3])

    with col_ac1:
        st.metric("📲 Instalações", "120", "+40%")
        st.metric("💰 CPI", "R$ 15,00", "-25%")
        st.metric("📊 Taxa Conversão", "40%", "+12%")

    with col_ac2:
        fig_install = px.pie(
            df_installs,
            names="Plataforma",
            values="Instalações",
            title="Distribuição de Instalações",
            template="plotly_dark",
        )
        fig_install.update_layout(
            height=300,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_install, use_container_width=True)

# ---------- REMARKETING ----------
with st.container():
    st.markdown(
        """
        <div class="lia-section-header">
            <span class="lia-section-icon">🔄</span>
            <h2 class="lia-section-title">Remarketing</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.dataframe(df_remarketing, use_container_width=True, hide_index=True)

# ---------- LOOKALIKE ----------
with st.container():
    st.markdown(
        """
        <div class="lia-section-header">
            <span class="lia-section-icon">🎯</span>
            <h2 class="lia-section-title">Lookalike</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.dataframe(df_lookalike, use_container_width=True, hide_index=True)

# ---------- PRÓXIMOS PASSOS ----------
with st.container():
    st.markdown(
        """
        <div class="lia-section-header">
            <span class="lia-section-icon">🚀</span>
            <h2 class="lia-section-title">Próximos Passos</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.dataframe(df_actions, use_container_width=True, hide_index=True)

# ---------- FOOTER ----------
st.markdown("---")
st.markdown("**📊 Dashboard AIDA • App LIA** | Desenvolvido por Grupo Garcia Seguradoras")
st.success("🎉 **Dashboard funcionando!** Todas as seções do funil AIDA completas!")
