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
)

# ---------------- TOUR GUIADO ----------------
render_tour_guide()

# ---------------- ESTADO DO TOUR ----------------
if 'tour_aberto' not in st.session_state:
    st.session_state.tour_aberto = False
if 'secao_tour' not in st.session_state:
    st.session_state.secao_tour = 'intro'

# ---------------- ESTILO GLOBAL (CSS) ----------------
st.markdown(
    """
    <style>
    /* Importar fonte moderna */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Crimson+Text:wght@400;600&display=swap');
    
    /* Sidebar - Estilo Pergaminho */
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
    
    /* Efeito de papel rasgado nas bordas */
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
    
    
    /* Fundo e tipografia */
    body, .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        color: #e5e7eb;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    /* Título principal */
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

    /* Container central */
    .lia-container {
        max-width: 1400px;
        margin: 0 auto;
        padding: 0 1rem;
    }

    /* Cards KPIs - Grid responsivo */
    .lia-kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1.2rem;
        margin-bottom: 2rem;
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

    /* Seções */
    .lia-section {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.6) 100%);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        border: 1px solid rgba(148, 163, 184, 0.2);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
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

    /* Funil visual */
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

    /* Tabelas */
    .dataframe {
        background: transparent !important;
    }

    /* Alertas/Avisos */
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

    /* Responsivo */
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

# ---------------- DADOS DE EXEMPLO ----------------
# Funil AIDA exemplo: 100k → 3k → 900 → 300 → 120
stages = ["Impressões", "Cliques", "Visitas LP", "Cliques CTA", "Instalações"]
values = [100_000, 3_000, 900, 300, 120]

# Conversões entre etapas
conversions = []
for i in range(1, len(values)):
    prev = values[i - 1]
    rate = (values[i] / prev * 100) if prev else 0
    conversions.append(rate)

# Evolução semanal (soma 120)
df_week = pd.DataFrame({
    "Semana": ["S1", "S2", "S3", "S4", "S5"],
    "Instalações": [10, 18, 24, 28, 40],
})

# Criativos exemplo
df_creatives = pd.DataFrame({
    "Criativo": [
        "🚨 Dor do WhatsApp",
        "💊 Feature Remédios",
        "💰 Feature Despesas",
    ],
    "CPM (R$)": [8.50, 7.90, 9.20],
    "CPC (R$)": [0.85, 0.73, 0.92],
    "CTR (%)": [1.3, 1.5, 1.1],
    "Cliques": [1200, 1450, 980],
})

# Dados LP (Interesse)
df_lp = pd.DataFrame({
    "Métrica": ["Visitas", "Duração Média", "Taxa de Rejeição", "Cliques no CTA"],
    "Valor": ["900", "2m 34s", "45%", "300"],
    "Status": ["✅ Bom", "✅ Ótimo", "⚠️ Médio", "✅ Bom"],
})

# Remarketing (Desejo)
df_remarketing = pd.DataFrame({
    "Público": ["Visitantes LP", "Clicaram CTA", "E-mails Coletados"],
    "Tamanho": [900, 300, 245],
    "CTR (%)": [3.2, 4.5, 2.8],
    "Conversão": [15, 22, 12],
})

# App Installs (Ação)
df_installs = pd.DataFrame({
    "Plataforma": ["Google Play", "App Store"],
    "Instalações": [75, 45],
    "CPI (R$)": [12.50, 18.30],
})

# ---------------- LAYOUT ----------------
st.markdown('<div class="lia-container">', unsafe_allow_html=True)

# Header
st.markdown(
    """
    <div class="lia-header">
        <div class="lia-title">📊 App LIA • Dashboard AIDA</div>
        <div class="lia-subtitle">
            Dashboard de validação H1 • Gestão de tráfego Meta Ads<br/>
            <strong>Nota:</strong> Os dados abaixo são exemplos do briefing. Serão substituídos por dados reais após início das campanhas.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- RESUMO EXECUTIVO ----------
st.markdown(
    """
    <div class="lia-section-header">
        <span class="lia-section-icon">🎯</span>
        <h2 class="lia-section-title">Resumo Executivo</h2>
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

st.markdown("<br/>", unsafe_allow_html=True)

# ---------- EVOLUÇÃO SEMANAL ----------
st.markdown('<div class="lia-section">', unsafe_allow_html=True)
st.markdown(
    """
    <div class="lia-section-header">
        <span class="lia-section-icon">📈</span>
        <h2 class="lia-section-title">Evolução Semanal</h2>
    </div>
    <div class="lia-section-caption">
        Acompanhamento do crescimento de instalações ao longo das 5 semanas de campanha.
    </div>
    """,
    unsafe_allow_html=True,
)

fig_line = go.Figure()
fig_line.add_trace(go.Scatter(
    x=df_week["Semana"],
    y=df_week["Instalações"],
    mode='lines+markers',
    line=dict(color='#818cf8', width=3),
    marker=dict(size=10, color='#c084fc'),
    fill='tozeroy',
    fillcolor='rgba(129, 140, 248, 0.1)',
))

fig_line.update_layout(
    template="plotly_dark",
    height=320,
    margin=dict(l=20, r=20, t=20, b=20),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    xaxis=dict(showgrid=False),
    yaxis=dict(showgrid=True, gridcolor='rgba(148, 163, 184, 0.1)'),
    font=dict(size=12, color='#cbd5e1'),
)

st.plotly_chart(fig_line, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# ---------- FUNIL AIDA VISUAL ----------
st.markdown('<div class="lia-section">', unsafe_allow_html=True)
st.markdown(
    """
    <div class="lia-section-header">
        <span class="lia-section-icon">🪜</span>
        <h2 class="lia-section-title">Funil AIDA • Visão Macro</h2>
    </div>
    <div class="lia-section-caption">
        Estrutura completa do funil: Impressões → Cliques → Visitas → CTA → Instalações
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
            color=['#818cf8', '#a78bfa', '#c084fc', '#e879f9', '#f0abfc'],
        ),
    ))
    
    fig_funnel.update_layout(
        template="plotly_dark",
        height=400,
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(size=12, color='#cbd5e1'),
    )
    
    st.plotly_chart(fig_funnel, use_container_width=True)

with col_f2:
    st.markdown("**📊 Taxa de Conversão por Etapa**")
    
    for i in range(1, len(stages)):
        conv = conversions[i-1]
        color = "success" if conv >= 30 else "warning" if conv >= 20 else "info"
        st.markdown(
            f"""
            <div class="funnel-stage">
                <div class="funnel-label">{stages[i-1]} → {stages[i]}</div>
                <div class="funnel-value">{conv:.1f}%</div>
                <div class="funnel-conversion">✓ Conversão</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown('</div>', unsafe_allow_html=True)

# ---------- ETAPA 1: ATENÇÃO ----------
st.markdown('<div class="lia-section">', unsafe_allow_html=True)
st.markdown(
    """
    <div class="lia-section-header">
        <span class="lia-section-icon">👀</span>
        <h2 class="lia-section-title">Etapa 1 • Atenção</h2>
    </div>
    <div class="lia-section-caption">
        <strong>Objetivo:</strong> Gerar o clique. Análise de performance dos criativos e métricas de engajamento.
    </div>
    """,
    unsafe_allow_html=True,
)

col_a1, col_a2, col_a3 = st.columns(3)

with col_a1:
    st.markdown(
        """
        <div class="lia-kpi-card">
            <div class="lia-kpi-label">👁️ Impressões</div>
            <div class="lia-kpi-value">100k</div>
            <div class="lia-kpi-helper">Alcance total</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_a2:
    st.markdown(
        """
        <div class="lia-kpi-card">
            <div class="lia-kpi-label">🖱️ CTR Médio</div>
            <div class="lia-kpi-value">1,3%</div>
            <div class="lia-kpi-helper">Taxa de clique</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_a3:
    st.markdown(
        """
        <div class="lia-kpi-card">
            <div class="lia-kpi-label">💰 CPC Médio</div>
            <div class="lia-kpi-value">R$ 0,83</div>
            <div class="lia-kpi-helper">Custo por clique</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br/>", unsafe_allow_html=True)

col_g1, col_g2 = st.columns(2)

with col_g1:
    fig_ctr = px.bar(
        df_creatives,
        x="Criativo",
        y="CTR (%)",
        text="CTR (%)",
        template="plotly_dark",
        title="📈 CTR por Criativo",
    )
    fig_ctr.update_traces(
        texttemplate='%{text:.1f}%',
        textposition='outside',
        marker_color=['#818cf8', '#c084fc', '#f0abfc'],
    )
    fig_ctr.update_layout(
        height=300,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='rgba(148, 163, 184, 0.1)'),
        font=dict(size=11, color='#cbd5e1'),
    )
    st.plotly_chart(fig_ctr, use_container_width=True)

with col_g2:
    fig_cpc = px.bar(
        df_creatives,
        x="Criativo",
        y="CPC (R$)",
        text="CPC (R$)",
        template="plotly_dark",
        title="💰 CPC por Criativo",
    )
    fig_cpc.update_traces(
        texttemplate='R$ %{text:.2f}',
        textposition='outside',
        marker_color=['#10b981', '#3b82f6', '#ef4444'],
    )
    fig_cpc.update_layout(
        height=300,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='rgba(148, 163, 184, 0.1)'),
        font=dict(size=11, color='#cbd5e1'),
    )
    st.plotly_chart(fig_cpc, use_container_width=True)

st.markdown("**📋 Performance Detalhada dos Criativos**")
st.dataframe(
    df_creatives.style.format({
        "CPM (R$)": "R$ {:.2f}",
        "CPC (R$)": "R$ {:.2f}",
        "CTR (%)": "{:.1f}%",
        "Cliques": "{:,.0f}",
    }),
    use_container_width=True,
    hide_index=True,
)

st.markdown(
    """
    <div class="lia-alert">
        <div class="lia-alert-title">💡 Insights - Atenção</div>
        • Criativo "Feature Remédios" apresenta melhor CTR (1.5%) e menor CPC (R$ 0.73)<br/>
        • Público 40-60 anos respondeu 2.3x melhor que 25-35 anos<br/>
        • Horário 19h-22h tem 45% mais engajamento
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('</div>', unsafe_allow_html=True)

# ---------- ETAPA 2: INTERESSE ----------
st.markdown('<div class="lia-section">', unsafe_allow_html=True)
st.markdown(
    """
    <div class="lia-section-header">
        <span class="lia-section-icon">🎯</span>
        <h2 class="lia-section-title">Etapa 2 • Interesse</h2>
    </div>
    <div class="lia-section-caption">
        <strong>Objetivo:</strong> Reter o usuário na Landing Page e gerar engajamento.
    </div>
    """,
    unsafe_allow_html=True,
)

col_i1, col_i2, col_i3, col_i4 = st.columns(4)

with col_i1:
    st.markdown(
        """
        <div class="lia-kpi-card">
            <div class="lia-kpi-label">🌐 Visitas LP</div>
            <div class="lia-kpi-value">900</div>
            <div class="lia-kpi-helper">Total de visitas</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_i2:
    st.markdown(
        """
        <div class="lia-kpi-card">
            <div class="lia-kpi-label">⏱️ Duração</div>
            <div class="lia-kpi-value">2m 34s</div>
            <div class="lia-kpi-helper">Tempo médio</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_i3:
    st.markdown(
        """
        <div class="lia-kpi-card">
            <div class="lia-kpi-label">📉 Rejeição</div>
            <div class="lia-kpi-value">45%</div>
            <div class="lia-kpi-helper">Bounce rate</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_i4:
    st.markdown(
        """
        <div class="lia-kpi-card">
            <div class="lia-kpi-label">🎯 Conv. LP</div>
            <div class="lia-kpi-value">33%</div>
            <div class="lia-kpi-helper">Clicaram CTA</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br/>", unsafe_allow_html=True)
st.markdown("**📊 Métricas da Landing Page**")
st.dataframe(df_lp, use_container_width=True, hide_index=True)

st.markdown(
    """
    <div class="lia-alert">
        <div class="lia-alert-title">💡 Insights - Interesse</div>
        • Duração média excelente (2m 34s) indica interesse real no produto<br/>
        • Seção "Organização de Remédios" teve maior scroll depth (78%)<br/>
        • Taxa de conversão LP→CTA de 33% está acima da média do mercado (20-25%)
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('</div>', unsafe_allow_html=True)

# ---------- ETAPA 3: DESEJO ----------
st.markdown('<div class="lia-section">', unsafe_allow_html=True)
st.markdown(
    """
    <div class="lia-section-header">
        <span class="lia-section-icon">💎</span>
        <h2 class="lia-section-title">Etapa 3 • Desejo</h2>
    </div>
    <div class="lia-section-caption">
        <strong>Objetivo:</strong> Converter intenção em ação através de remarketing e nutrição.
    </div>
    """,
    unsafe_allow_html=True,
)

col_d1, col_d2, col_d3 = st.columns(3)

with col_d1:
    st.markdown(
        """
        <div class="lia-kpi-card">
            <div class="lia-kpi-label">🎯 Cliques CTA</div>
            <div class="lia-kpi-value">300</div>
            <div class="lia-kpi-helper">Intenção de baixar</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_d2:
    st.markdown(
        """
        <div class="lia-kpi-card">
            <div class="lia-kpi-label">📧 E-mails</div>
            <div class="lia-kpi-value">245</div>
            <div class="lia-kpi-helper">Leads capturados</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_d3:
    st.markdown(
        """
        <div class="lia-kpi-card">
            <div class="lia-kpi-label">🔄 CTR Retarg.</div>
            <div class="lia-kpi-value">3,5%</div>
            <div class="lia-kpi-helper">Remarketing</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br/>", unsafe_allow_html=True)

fig_remarketing = px.bar(
    df_remarketing,
    x="Público",
    y="Conversão",
    text="Conversão",
    template="plotly_dark",
    title="🎯 Conversões por Público de Remarketing",
)
fig_remarketing.update_traces(
    texttemplate='%{text}',
    textposition='outside',
    marker_color=['#818cf8', '#c084fc', '#f0abfc'],
)
fig_remarketing.update_layout(
    height=300,
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    xaxis=dict(showgrid=False),
    yaxis=dict(showgrid=True, gridcolor='rgba(148, 163, 184, 0.1)'),
    font=dict(size=11, color='#cbd5e1'),
)
st.plotly_chart(fig_remarketing, use_container_width=True)

st.markdown("**📋 Performance dos Públicos de Remarketing**")
st.dataframe(
    df_remarketing.style.format({
        "Tamanho": "{:,.0f}",
        "CTR (%)": "{:.1f}%",
        "Conversão": "{:,.0f}",
    }),
    use_container_width=True,
    hide_index=True,
)

st.markdown(
    """
    <div class="lia-alert">
        <div class="lia-alert-title">💡 Insights - Desejo</div>
        • Remarketing para "Clicaram CTA" tem melhor performance (CTR 4.5%)<br/>
        • Sequência de e-mails com 3 disparos teve 28% de abertura<br/>
        • Carrossel de depoimentos no remarketing aumentou conversão em 35%
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('</div>', unsafe_allow_html=True)

# ---------- ETAPA 4: AÇÃO ----------
st.markdown('<div class="lia-section">', unsafe_allow_html=True)
st.markdown(
    """
    <div class="lia-section-header">
        <span class="lia-section-icon">🚀</span>
        <h2 class="lia-section-title">Etapa 4 • Ação</h2>
    </div>
    <div class="lia-section-caption">
        <strong>Objetivo:</strong> Gerar instalações efetivas e ativar usuários no app.
    </div>
    """,
    unsafe_allow_html=True,
)

col_ac1, col_ac2, col_ac3, col_ac4 = st.columns(4)

with col_ac1:
    st.markdown(
        """
        <div class="lia-kpi-card">
            <div class="lia-kpi-label">📱 Instalações</div>
            <div class="lia-kpi-value">120</div>
            <div class="lia-kpi-helper">App Store + Google</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_ac2:
    st.markdown(
        """
        <div class="lia-kpi-card">
            <div class="lia-kpi-label">💰 CPI Médio</div>
            <div class="lia-kpi-value">R$ 15,00</div>
            <div class="lia-kpi-helper">Custo por install</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_ac3:
    st.markdown(
        """
        <div class="lia-kpi-card">
            <div class="lia-kpi-label">📊 Conv. Final</div>
            <div class="lia-kpi-value">40%</div>
            <div class="lia-kpi-helper">CTA → Install</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_ac4:
    st.markdown(
        """
        <div class="lia-kpi-card">
            <div class="lia-kpi-label">✅ Onboarding</div>
            <div class="lia-kpi-value">85%</div>
            <div class="lia-kpi-helper">Completaram</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br/>", unsafe_allow_html=True)

col_p1, col_p2 = st.columns(2)

with col_p1:
    fig_installs = px.pie(
        df_installs,
        values="Instalações",
        names="Plataforma",
        template="plotly_dark",
        title="📱 Instalações por Plataforma",
        color_discrete_sequence=['#818cf8', '#c084fc'],
    )
    fig_installs.update_layout(
        height=300,
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=11, color='#cbd5e1'),
    )
    st.plotly_chart(fig_installs, use_container_width=True)

with col_p2:
    fig_cpi = px.bar(
        df_installs,
        x="Plataforma",
        y="CPI (R$)",
        text="CPI (R$)",
        template="plotly_dark",
        title="💰 CPI por Plataforma",
    )
    fig_cpi.update_traces(
        texttemplate='R$ %{text:.2f}',
        textposition='outside',
        marker_color=['#10b981', '#3b82f6'],
    )
    fig_cpi.update_layout(
        height=300,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='rgba(148, 163, 184, 0.1)'),
        font=dict(size=11, color='#cbd5e1'),
    )
    st.plotly_chart(fig_cpi, use_container_width=True)

st.markdown("**📋 Comparativo por Plataforma**")
st.dataframe(
    df_installs.style.format({
        "Instalações": "{:,.0f}",
        "CPI (R$)": "R$ {:.2f}",
    }),
    use_container_width=True,
    hide_index=True,
)

st.markdown(
    """
    <div class="lia-alert">
        <div class="lia-alert-title">💡 Insights - Ação</div>
        • Google Play tem 62.5% das instalações com CPI 32% menor que iOS<br/>
        • Taxa de onboarding de 85% indica product-market fit promissor<br/>
        • Retenção D1 (primeiro dia) está em 68%, acima da média do setor (45%)
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('</div>', unsafe_allow_html=True)

# ---------- DISTRIBUIÇÃO DE INVESTIMENTO ----------
st.markdown('<div class="lia-section">', unsafe_allow_html=True)
st.markdown(
    """
    <div class="lia-section-header">
        <span class="lia-section-icon">💵</span>
        <h2 class="lia-section-title">Distribuição de Investimento</h2>
    </div>
    """,
    unsafe_allow_html=True,
)

df_budget = pd.DataFrame({
    "Categoria": ["Tráfego / Atenção", "Remarketing / Desejo", "App Installs / Ação"],
    "Investimento (%)": [60, 20, 20],
    "Valor (R$)": [1080, 360, 360],
})

fig_budget = px.pie(
    df_budget,
    values="Investimento (%)",
    names="Categoria",
    template="plotly_dark",
    hole=0.4,
    color_discrete_sequence=['#818cf8', '#c084fc', '#f0abfc'],
)
fig_budget.update_layout(
    height=350,
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(size=12, color='#cbd5e1'),
)
st.plotly_chart(fig_budget, use_container_width=True)

st.dataframe(
    df_budget.style.format({
        "Investimento (%)": "{:.0f}%",
        "Valor (R$)": "R$ {:.2f}",
    }),
    use_container_width=True,
    hide_index=True,
)

st.markdown('</div>', unsafe_allow_html=True)

# ---------- PRÓXIMOS PASSOS ----------
st.markdown('<div class="lia-section">', unsafe_allow_html=True)
st.markdown(
    """
    <div class="lia-section-header">
        <span class="lia-section-icon">🎯</span>
        <h2 class="lia-section-title">Próximas Ações & Recomendações</h2>
    </div>
    """,
    unsafe_allow_html=True,
)

col_r1, col_r2 = st.columns(2)

with col_r1:
    st.markdown(
        """
        **🚀 Curto Prazo (Próximas 2 semanas)**
        
        ✅ Ampliar budget do criativo "Feature Remédios" (+50%)  
        ✅ Testar variação do criativo "Dor WhatsApp" com vídeo  
        ✅ Implementar teste A/B no CTA da LP  
        ✅ Criar público lookalike dos 120 instaladores  
        ✅ Otimizar horários de veiculação (19h-22h)
        """
    )

with col_r2:
    st.markdown(
        """
        **📅 Médio Prazo (Próximas 4-6 semanas)**
        
        ✅ Desenvolver sequência de e-mail marketing (5 disparos)  
        ✅ Implementar retargeting para usuários iOS (CPI alto)  
        ✅ Testar nova hipótese: "Feature Agenda"  
        ✅ Expandir para públicos semelhantes (Home Care)  
        ✅ Criar dashboard de retenção (D7, D30)
        """
    )

st.markdown('</div>', unsafe_allow_html=True)

# ---------- FOOTER ----------
st.markdown(
    """
    <div class="lia-alert">
        <div class="lia-alert-title">📌 Nota Importante</div>
        Este dashboard apresenta a estrutura completa de acompanhamento conforme briefing.<br/>
        <strong>Próximo passo:</strong> Integração com Meta Ads API e fontes de dados reais (Google Analytics, Firebase, etc.)
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('</div>', unsafe_allow_html=True)
