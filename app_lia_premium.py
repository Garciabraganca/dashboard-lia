import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# =============================================================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================================================
st.set_page_config(
    page_title="LIA • Ciclo 1 Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =============================================================================
# DATA PROVIDER - Camada de abstração para dados
# =============================================================================
class DataProvider:
    """Camada de abstração para integração com Meta Ads e GA4"""

    def __init__(self, mode="mock"):
        self.mode = mode

    def get_meta_metrics(self, period="7d", level="campaign", filters=None):
        if self.mode == "mock":
            return self._get_mock_meta_metrics(period, level)
        return self._get_mock_meta_metrics(period, level)

    def get_ga4_metrics(self, period="7d", filters=None):
        if self.mode == "mock":
            return self._get_mock_ga4_metrics(period)
        return self._get_mock_ga4_metrics(period)

    def get_creative_performance(self, period="7d"):
        if self.mode == "mock":
            return self._get_mock_creative_data()
        return self._get_mock_creative_data()

    def get_daily_trends(self, period="7d"):
        if self.mode == "mock":
            return self._get_mock_daily_trends(period)
        return self._get_mock_daily_trends(period)

    def _get_mock_meta_metrics(self, period, level):
        multiplier = {"today": 0.14, "yesterday": 0.14, "7d": 1, "14d": 2}.get(period, 1)
        base_metrics = {
            "investimento": 850.00,
            "impressoes": 125000,
            "alcance": 89000,
            "frequencia": 1.40,
            "cliques_link": 3200,
            "ctr_link": 2.56,
            "cpc_link": 0.27,
            "cpm": 6.80,
            "delta_investimento": 12.5,
            "delta_impressoes": 18.3,
            "delta_alcance": 15.2,
            "delta_frequencia": 0.05,
            "delta_cliques": 22.1,
            "delta_ctr": 0.3,
            "delta_cpc": -8.5,
            "delta_cpm": -5.2,
        }
        return {k: v * multiplier if isinstance(v, (int, float)) and not k.startswith("delta") else v
                for k, v in base_metrics.items()}

    def _get_mock_ga4_metrics(self, period):
        multiplier = {"today": 0.14, "yesterday": 0.14, "7d": 1, "14d": 2}.get(period, 1)
        return {
            "sessoes": int(2850 * multiplier),
            "usuarios": int(2340 * multiplier),
            "pageviews": int(4200 * multiplier),
            "taxa_engajamento": 68.5,
            "tempo_medio": "1m 42s",
            "delta_sessoes": 15.8,
            "delta_usuarios": 12.3,
            "delta_pageviews": 18.9,
            "delta_engajamento": 3.2,
        }

    def _get_mock_creative_data(self):
        return pd.DataFrame({
            "Criativo": [
                "Video_LIA_Problema_WhatsApp_v2",
                "Static_Beneficios_App_v1",
                "Carousel_Features_3slides",
                "Video_Depoimento_Usuario",
                "Static_Promo_Download_v3"
            ],
            "Formato": ["Video 15s", "Imagem", "Carrossel", "Video 30s", "Imagem"],
            "Investimento": [285.00, 195.00, 165.00, 125.00, 80.00],
            "Impressoes": [42000, 31000, 26000, 18000, 8000],
            "Cliques": [1280, 890, 620, 320, 90],
            "CTR": [3.05, 2.87, 2.38, 1.78, 1.12],
            "CPC": [0.22, 0.22, 0.27, 0.39, 0.89],
            "CPM": [6.79, 6.29, 6.35, 6.94, 10.00],
        })

    def _get_mock_daily_trends(self, period):
        days = {"today": 1, "yesterday": 1, "7d": 7, "14d": 14}.get(period, 7)
        dates = [(datetime.now() - timedelta(days=i)).strftime("%d/%m") for i in range(days-1, -1, -1)]
        import random
        random.seed(42)
        base_clicks = [380, 420, 395, 450, 480, 510, 565][:days]
        base_ctr = [2.3, 2.4, 2.35, 2.5, 2.55, 2.6, 2.75][:days]
        base_cpc = [0.30, 0.28, 0.29, 0.27, 0.26, 0.25, 0.24][:days]
        return pd.DataFrame({
            "Data": dates,
            "Cliques": base_clicks + [random.randint(400, 550) for _ in range(max(0, days-7))],
            "CTR": base_ctr + [round(random.uniform(2.3, 2.8), 2) for _ in range(max(0, days-7))],
            "CPC": base_cpc + [round(random.uniform(0.22, 0.32), 2) for _ in range(max(0, days-7))],
        })

    def get_source_medium(self):
        return pd.DataFrame({
            "Origem / Midia": ["facebook / paid", "instagram / paid", "google / cpc", "(direct) / (none)", "google / organic"],
            "Sessoes": [1450, 890, 285, 145, 80],
            "Usuarios": [1200, 750, 240, 95, 55],
            "Engajamento": ["72.3%", "68.9%", "58.2%", "45.1%", "62.8%"],
            "Tempo Medio": ["1m 58s", "1m 42s", "1m 15s", "0m 48s", "2m 05s"],
        })

    def get_executive_summary(self, period, meta_data, creative_data):
        """Gera resumo executivo dinâmico baseado nos dados"""
        insights = []

        # Verificar fase de aprendizado
        is_learning = period in ["today", "yesterday"] or meta_data["investimento"] < 20
        if is_learning:
            insights.append("Em aprendizado")

        # Analisar CTR
        ctr = meta_data["ctr_link"]
        delta_ctr = meta_data["delta_ctr"]
        if abs(delta_ctr) < 0.5:
            insights.append("CTR estavel")
        elif delta_ctr > 0:
            insights.append("CTR em alta")
        else:
            insights.append("CTR em queda")

        # Analisar CPC
        delta_cpc = meta_data["delta_cpc"]
        if delta_cpc < 0:
            insights.append("CPC controlado")
        elif delta_cpc > 10:
            insights.append("CPC subindo")
        else:
            insights.append("CPC estavel")

        # Criativo lider
        if len(creative_data) > 0:
            best_ctr_idx = creative_data["CTR"].idxmax()
            best_creative = creative_data.loc[best_ctr_idx, "Criativo"]
            # Abreviar nome
            short_name = best_creative.split("_")[0] + "_" + best_creative.split("_")[1] if "_" in best_creative else best_creative[:15]
            insights.append(f"Lider: {short_name}")

        return " | ".join(insights)


# Inicializar provider
data_provider = DataProvider(mode="mock")

# =============================================================================
# CSS CUSTOMIZADO - Tema Dark com Inter
# =============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"], .stApp {
    background: #000 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* Esconder sidebar */
[data-testid="stSidebar"], section[data-testid="stSidebar"],
button[kind="header"], [data-testid="collapsedControl"] {
    display: none !important;
}

.main .block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

h1, h2, h3, h4, h5, h6, p, span, div, label {
    font-family: 'Inter', sans-serif !important;
}

/* Branding Panel */
.brand-wrapper {
    background: linear-gradient(180deg, #7c3aed 0%, #4c1d95 40%, #000000 100%);
    min-height: 100vh;
    padding: 40px 28px;
    border-radius: 0;
}

.brand-logo {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 28px;
}

.brand-logo-circle {
    width: 44px;
    height: 44px;
    background: #fff;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
}

.brand-logo-text {
    font-size: 22px;
    font-weight: 700;
    color: #fff;
}

.brand-title {
    font-size: 26px;
    font-weight: 700;
    color: #fff;
    line-height: 1.25;
    margin-bottom: 8px;
}

.brand-subtitle {
    font-size: 14px;
    color: rgba(255,255,255,0.7);
    margin-bottom: 24px;
    line-height: 1.5;
}

.brand-block {
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 12px;
}

.brand-block-label {
    font-size: 11px;
    font-weight: 600;
    color: rgba(255,255,255,0.5);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
}

.brand-block-text {
    font-size: 13px;
    color: #fff;
    line-height: 1.4;
}

.brand-steps {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin: 24px 0;
}

.brand-step {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    border-radius: 10px;
    font-size: 13px;
    font-weight: 500;
}

.brand-step.active {
    background: #fff;
    color: #000;
}

.brand-step.inactive {
    background: rgba(255,255,255,0.1);
    color: rgba(255,255,255,0.6);
}

.brand-step-num {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 600;
}

.brand-step.active .brand-step-num {
    background: #000;
    color: #fff;
}

.brand-step.inactive .brand-step-num {
    background: rgba(255,255,255,0.2);
    color: rgba(255,255,255,0.7);
}

.brand-footer {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 10px;
    padding: 14px;
    margin-top: 24px;
}

.brand-footer-text {
    font-size: 11px;
    color: rgba(255,255,255,0.5);
    line-height: 1.5;
}

/* Dashboard Panel */
.dash-header {
    margin-bottom: 16px;
}

.dash-title {
    font-size: 22px;
    font-weight: 700;
    color: #fff;
    margin-bottom: 2px;
}

.dash-subtitle {
    font-size: 13px;
    color: #737373;
}

/* Executive Summary */
.exec-summary {
    background: #0f0f10;
    border: 1px solid #232323;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 20px;
}

.exec-label {
    font-size: 11px;
    font-weight: 600;
    color: #525252;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
}

.exec-text {
    font-size: 14px;
    color: #e5e5e5;
    font-weight: 500;
}

/* KPIs - Deltas mais discretos */
[data-testid="stMetricValue"] {
    color: #fff !important;
    font-size: 24px !important;
    font-weight: 700 !important;
}

[data-testid="stMetricLabel"] {
    color: #737373 !important;
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.3px !important;
}

[data-testid="stMetricDelta"] {
    font-size: 11px !important;
    opacity: 0.7 !important;
}

[data-testid="stMetricDelta"] svg {
    display: none !important;
}

/* Seções */
.section-title-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
}

.section-title {
    font-size: 15px;
    font-weight: 600;
    color: #fff;
}

/* Badges */
.badge-row {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 14px;
}

.badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 500;
}

.badge-green {
    background: rgba(34,197,94,0.12);
    color: #4ade80;
    border: 1px solid rgba(34,197,94,0.25);
}

.badge-blue {
    background: rgba(59,130,246,0.12);
    color: #60a5fa;
    border: 1px solid rgba(59,130,246,0.25);
}

/* Alerta de escopo */
.scope-note {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 16px;
    background: rgba(59,130,246,0.06);
    border: 1px solid rgba(59,130,246,0.15);
    border-radius: 10px;
    margin-bottom: 16px;
}

.scope-note-text {
    font-size: 12px;
    color: #a3a3a3;
}

.scope-note-text strong {
    color: #d4d4d4;
}

/* Empty State */
.empty-box {
    text-align: center;
    padding: 40px 20px;
    background: #0a0a0a;
    border: 1px dashed #262626;
    border-radius: 12px;
}

.empty-box-title {
    font-size: 14px;
    font-weight: 600;
    color: #a3a3a3;
    margin-bottom: 6px;
}

.empty-box-text {
    font-size: 12px;
    color: #525252;
}

/* Tabelas */
.stDataFrame { background: transparent !important; }
[data-testid="stDataFrame"] > div { background: transparent !important; }

/* Gráficos */
.js-plotly-plot .plotly .modebar { display: none !important; }

/* Streamlit overrides */
.stSelectbox > div > div {
    background: #0f0f10 !important;
    border: 1px solid #262626 !important;
    border-radius: 8px !important;
}

.stSelectbox label {
    color: #737373 !important;
    font-size: 11px !important;
}

/* Footer */
.dash-footer {
    text-align: center;
    padding: 20px;
    color: #404040;
    font-size: 11px;
}

/* Responsivo */
@media (max-width: 992px) {
    .brand-wrapper {
        min-height: auto;
        padding: 24px 20px;
    }
}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# LAYOUT PRINCIPAL - DUAS COLUNAS
# =============================================================================
col_brand, col_dash = st.columns([0.38, 0.62], gap="small")

# =============================================================================
# COLUNA ESQUERDA - BRANDING PANEL
# =============================================================================
with col_brand:
    # Container com gradiente
    st.markdown('<div class="brand-wrapper">', unsafe_allow_html=True)

    # Logo
    st.markdown('''
    <div class="brand-logo">
        <div class="brand-logo-circle">◆</div>
        <span class="brand-logo-text">LIA</span>
    </div>
    ''', unsafe_allow_html=True)

    # Título
    st.markdown('<div class="brand-title">Ciclo 1 — Trafego para Landing</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-subtitle">Medicao ate clique/sessao. Sem conversao final nesta fase.</div>', unsafe_allow_html=True)

    # Bloco Objetivo
    st.markdown('''
    <div class="brand-block">
        <div class="brand-block-label">Objetivo</div>
        <div class="brand-block-text">Gerar alcance qualificado e cliques para a landing.</div>
    </div>
    ''', unsafe_allow_html=True)

    # Bloco Status
    st.markdown('''
    <div class="brand-block">
        <div class="brand-block-label">Status</div>
        <div class="brand-block-text">Em aprendizado nas primeiras 48h.</div>
    </div>
    ''', unsafe_allow_html=True)

    # Steps
    st.markdown('''
    <div class="brand-steps">
        <div class="brand-step active">
            <div class="brand-step-num">1</div>
            <span>Alcance</span>
        </div>
        <div class="brand-step active">
            <div class="brand-step-num">2</div>
            <span>Interesse</span>
        </div>
        <div class="brand-step active">
            <div class="brand-step-num">3</div>
            <span>Landing</span>
        </div>
        <div class="brand-step inactive">
            <div class="brand-step-num">4</div>
            <span>Proximos passos</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # Footer
    st.markdown('''
    <div class="brand-footer">
        <div class="brand-footer-text">
            Evitar decisoes precipitadas antes de acumular volume.
        </div>
    </div>
    ''', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# =============================================================================
# COLUNA DIREITA - DASHBOARD OPERACIONAL
# =============================================================================
with col_dash:
    # Header
    st.markdown('''
    <div class="dash-header">
        <div class="dash-title">Dashboard Ciclo 1</div>
        <div class="dash-subtitle">Performance de midia ate o clique na landing (applia.ai)</div>
    </div>
    ''', unsafe_allow_html=True)

    # Barra de Filtros
    filter_cols = st.columns([1.5, 1, 1, 1.5])
    with filter_cols[0]:
        periodo = st.selectbox("Periodo", ["Hoje", "Ontem", "Ultimos 7 dias", "Ultimos 14 dias", "Personalizado"], index=2, key="filter_periodo")
    with filter_cols[1]:
        fonte = st.selectbox("Fonte", ["Meta", "GA4", "Ambos"], index=0, key="filter_fonte")
    with filter_cols[2]:
        nivel = st.selectbox("Nivel", ["Campanha", "Conjunto", "Criativo"], index=0, key="filter_nivel")
    with filter_cols[3]:
        campanha = st.selectbox("Campanha", ["Todas", "LIA_Awareness_BR", "LIA_Trafego_BR"], index=0, key="filter_campanha")

    # Mapear período
    period_map = {"Hoje": "today", "Ontem": "yesterday", "Ultimos 7 dias": "7d", "Ultimos 14 dias": "14d", "Personalizado": "7d"}
    selected_period = period_map.get(periodo, "7d")

    # Obter dados
    meta_data = data_provider.get_meta_metrics(period=selected_period)
    ga4_data = data_provider.get_ga4_metrics(period=selected_period)
    creative_data = data_provider.get_creative_performance()
    trends_data = data_provider.get_daily_trends(period=selected_period)

    # =============================================================================
    # RESUMO EXECUTIVO
    # =============================================================================
    exec_summary = data_provider.get_executive_summary(selected_period, meta_data, creative_data)
    st.markdown(f'''
    <div class="exec-summary">
        <div class="exec-label">Status do Ciclo 1</div>
        <div class="exec-text">{exec_summary}</div>
    </div>
    ''', unsafe_allow_html=True)

    # =============================================================================
    # KPIs PRINCIPAIS
    # =============================================================================
    st.markdown('<div class="section-title">KPIs Principais</div>', unsafe_allow_html=True)

    kpi_row1 = st.columns(4)
    with kpi_row1[0]:
        st.metric("Investimento", f"${meta_data['investimento']:,.2f}", f"{meta_data['delta_investimento']:+.1f}%")
    with kpi_row1[1]:
        st.metric("Impressoes", f"{meta_data['impressoes']:,.0f}", f"{meta_data['delta_impressoes']:+.1f}%")
    with kpi_row1[2]:
        st.metric("Alcance", f"{meta_data['alcance']:,.0f}", f"{meta_data['delta_alcance']:+.1f}%")
    with kpi_row1[3]:
        st.metric("Frequencia", f"{meta_data['frequencia']:.2f}", f"{meta_data['delta_frequencia']:+.2f}")

    kpi_row2 = st.columns(4)
    with kpi_row2[0]:
        st.metric("Cliques Link", f"{meta_data['cliques_link']:,.0f}", f"{meta_data['delta_cliques']:+.1f}%")
    with kpi_row2[1]:
        st.metric("CTR Link", f"{meta_data['ctr_link']:.2f}%", f"{meta_data['delta_ctr']:+.2f}pp")
    with kpi_row2[2]:
        st.metric("CPC Link", f"${meta_data['cpc_link']:.2f}", f"{meta_data['delta_cpc']:+.1f}%", delta_color="inverse")
    with kpi_row2[3]:
        st.metric("CPM", f"${meta_data['cpm']:.2f}", f"{meta_data['delta_cpm']:+.1f}%", delta_color="inverse")

    st.markdown("<br>", unsafe_allow_html=True)

    # =============================================================================
    # PERFORMANCE POR CRIATIVO
    # =============================================================================
    st.markdown('<div class="section-title">Performance por Criativo</div>', unsafe_allow_html=True)

    if len(creative_data) > 0:
        best_ctr_idx = creative_data["CTR"].idxmax()
        best_cpc_idx = creative_data["CPC"].idxmin()
        best_ctr_name = creative_data.loc[best_ctr_idx, "Criativo"][:20]
        best_cpc_name = creative_data.loc[best_cpc_idx, "Criativo"][:20]

        st.markdown(f'''
        <div class="badge-row">
            <div class="badge badge-green">Melhor CTR: {best_ctr_name}... ({creative_data.loc[best_ctr_idx, "CTR"]:.2f}%)</div>
            <div class="badge badge-blue">Menor CPC: {best_cpc_name}... (${creative_data.loc[best_cpc_idx, "CPC"]:.2f})</div>
        </div>
        ''', unsafe_allow_html=True)

        # Tabela simples sem gradiente forte
        st.dataframe(
            creative_data.style.format({
                "Investimento": "${:.2f}",
                "Impressoes": "{:,.0f}",
                "Cliques": "{:,.0f}",
                "CTR": "{:.2f}%",
                "CPC": "${:.2f}",
                "CPM": "${:.2f}"
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.markdown('''
        <div class="empty-box">
            <div class="empty-box-title">Ainda em aprendizado</div>
            <div class="empty-box-text">Volte apos acumular entrega (impressoes/cliques).</div>
        </div>
        ''', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # =============================================================================
    # TENDÊNCIA TEMPORAL
    # =============================================================================
    st.markdown('<div class="section-title">Tendencia Temporal</div>', unsafe_allow_html=True)

    chart_cols = st.columns(3)

    with chart_cols[0]:
        fig_clicks = go.Figure()
        fig_clicks.add_trace(go.Scatter(
            x=trends_data["Data"], y=trends_data["Cliques"],
            mode="lines+markers", line=dict(color="#7c3aed", width=2),
            marker=dict(size=5, color="#7c3aed"),
            fill="tozeroy", fillcolor="rgba(124,58,237,0.08)"
        ))
        fig_clicks.update_layout(
            title="Cliques/Dia", template="plotly_dark", height=200,
            margin=dict(l=0, r=0, t=35, b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, tickfont=dict(size=9, color="#525252")),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)", tickfont=dict(size=9, color="#525252")),
            font=dict(size=11, color="#737373"), showlegend=False
        )
        st.plotly_chart(fig_clicks, use_container_width=True)

    with chart_cols[1]:
        fig_ctr = go.Figure()
        fig_ctr.add_trace(go.Scatter(
            x=trends_data["Data"], y=trends_data["CTR"],
            mode="lines+markers", line=dict(color="#22c55e", width=2),
            marker=dict(size=5, color="#22c55e"),
            fill="tozeroy", fillcolor="rgba(34,197,94,0.08)"
        ))
        fig_ctr.update_layout(
            title="CTR/Dia (%)", template="plotly_dark", height=200,
            margin=dict(l=0, r=0, t=35, b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, tickfont=dict(size=9, color="#525252")),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)", tickfont=dict(size=9, color="#525252")),
            font=dict(size=11, color="#737373"), showlegend=False
        )
        st.plotly_chart(fig_ctr, use_container_width=True)

    with chart_cols[2]:
        fig_cpc = go.Figure()
        fig_cpc.add_trace(go.Scatter(
            x=trends_data["Data"], y=trends_data["CPC"],
            mode="lines+markers", line=dict(color="#f59e0b", width=2),
            marker=dict(size=5, color="#f59e0b"),
            fill="tozeroy", fillcolor="rgba(245,158,11,0.08)"
        ))
        fig_cpc.update_layout(
            title="CPC/Dia ($)", template="plotly_dark", height=200,
            margin=dict(l=0, r=0, t=35, b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, tickfont=dict(size=9, color="#525252")),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)", tickfont=dict(size=9, color="#525252")),
            font=dict(size=11, color="#737373"), showlegend=False
        )
        st.plotly_chart(fig_cpc, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # =============================================================================
    # LANDING PAGE (GA4)
    # =============================================================================
    st.markdown('<div class="section-title">Landing Page (GA4)</div>', unsafe_allow_html=True)

    st.markdown('''
    <div class="scope-note">
        <span>ℹ️</span>
        <span class="scope-note-text"><strong>Ciclo 1 mede ate clique/sessao.</strong> Instalacoes e conversoes serao avaliadas nos proximos ciclos.</span>
    </div>
    ''', unsafe_allow_html=True)

    ga4_cols = st.columns(5)
    with ga4_cols[0]:
        st.metric("Sessoes", f"{ga4_data['sessoes']:,.0f}", f"{ga4_data['delta_sessoes']:+.1f}%")
    with ga4_cols[1]:
        st.metric("Usuarios", f"{ga4_data['usuarios']:,.0f}", f"{ga4_data['delta_usuarios']:+.1f}%")
    with ga4_cols[2]:
        st.metric("Pageviews", f"{ga4_data['pageviews']:,.0f}", f"{ga4_data['delta_pageviews']:+.1f}%")
    with ga4_cols[3]:
        st.metric("Engajamento", f"{ga4_data['taxa_engajamento']:.1f}%", f"{ga4_data['delta_engajamento']:+.1f}%")
    with ga4_cols[4]:
        st.metric("Tempo Medio", ga4_data['tempo_medio'])

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabela Origem/Mídia
    st.markdown("**Origem/Midia (foco em paid social)**")
    source_data = data_provider.get_source_medium()
    st.dataframe(source_data, use_container_width=True, hide_index=True)

    # Footer
    st.markdown('<div class="dash-footer">Dashboard Ciclo 1 • LIA App • Atualizado em tempo real</div>', unsafe_allow_html=True)
