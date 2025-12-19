import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

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
        """
        Retorna métricas do Meta Ads
        Args:
            period: "today", "yesterday", "7d", "14d", "custom"
            level: "campaign", "adset", "creative"
            filters: dict com filtros adicionais
        """
        if self.mode == "mock":
            return self._get_mock_meta_metrics(period, level)
        # TODO: Implementar integração real com Meta Ads API
        return self._get_mock_meta_metrics(period, level)

    def get_ga4_metrics(self, period="7d", filters=None):
        """
        Retorna métricas do GA4
        Args:
            period: "today", "yesterday", "7d", "14d", "custom"
            filters: dict com filtros adicionais
        """
        if self.mode == "mock":
            return self._get_mock_ga4_metrics(period)
        # TODO: Implementar integração real com GA4 API
        return self._get_mock_ga4_metrics(period)

    def get_creative_performance(self, period="7d"):
        """Retorna performance por criativo"""
        if self.mode == "mock":
            return self._get_mock_creative_data()
        return self._get_mock_creative_data()

    def get_daily_trends(self, period="7d"):
        """Retorna tendências diárias para gráficos"""
        if self.mode == "mock":
            return self._get_mock_daily_trends(period)
        return self._get_mock_daily_trends(period)

    def _get_mock_meta_metrics(self, period, level):
        """Dados mock para Meta Ads"""
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
            # Variações vs período anterior
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
        """Dados mock para GA4"""
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
        """Dados mock de performance por criativo"""
        return pd.DataFrame({
            "Criativo": [
                "Video_LIA_Problema_WhatsApp_v2",
                "Static_Beneficios_App_v1",
                "Carousel_Features_3slides",
                "Video_Depoimento_Usuario",
                "Static_Promo_Download_v3"
            ],
            "Formato": ["Vídeo 15s", "Imagem", "Carrossel", "Vídeo 30s", "Imagem"],
            "Investimento": [285.00, 195.00, 165.00, 125.00, 80.00],
            "Impressões": [42000, 31000, 26000, 18000, 8000],
            "Cliques Link": [1280, 890, 620, 320, 90],
            "CTR Link": [3.05, 2.87, 2.38, 1.78, 1.12],
            "CPC Link": [0.22, 0.22, 0.27, 0.39, 0.89],
            "CPM": [6.79, 6.29, 6.35, 6.94, 10.00],
        })

    def _get_mock_daily_trends(self, period):
        """Dados mock para tendências diárias"""
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
        """Retorna dados de origem/mídia do GA4"""
        return pd.DataFrame({
            "Origem/Mídia": [
                "facebook / paid",
                "instagram / paid",
                "google / cpc",
                "(direct) / (none)",
                "google / organic"
            ],
            "Sessões": [1450, 890, 285, 145, 80],
            "Usuários": [1200, 750, 240, 95, 55],
            "Taxa Engaj.": ["72.3%", "68.9%", "58.2%", "45.1%", "62.8%"],
            "Tempo Médio": ["1m 58s", "1m 42s", "1m 15s", "0m 48s", "2m 05s"],
        })


# Inicializar provider
data_provider = DataProvider(mode="mock")

# =============================================================================
# CSS CUSTOMIZADO - Tema Dark com Inter
# =============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* Reset e Base */
*, *::before, *::after {
    box-sizing: border-box;
}

html, body, [data-testid="stAppViewContainer"], .stApp {
    background: #000 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* Esconder sidebar completamente */
[data-testid="stSidebar"] {
    display: none !important;
}

section[data-testid="stSidebar"] {
    display: none !important;
}

button[kind="header"] {
    display: none !important;
}

[data-testid="collapsedControl"] {
    display: none !important;
}

/* Container principal */
.main .block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

/* Tipografia global */
h1, h2, h3, h4, h5, h6, p, span, div, label {
    font-family: 'Inter', sans-serif !important;
}

/* ========================================
   BRANDING PANEL (Coluna Esquerda)
   ======================================== */
.branding-panel {
    background: linear-gradient(180deg, #7c3aed 0%, #4c1d95 40%, #000000 100%);
    min-height: 100vh;
    padding: 48px 32px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    position: relative;
}

.logo-container {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 32px;
}

.logo-circle {
    width: 48px;
    height: 48px;
    background: #fff;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
}

.logo-circle svg {
    width: 28px;
    height: 28px;
}

.logo-text {
    font-size: 24px;
    font-weight: 700;
    color: #fff;
    letter-spacing: -0.5px;
}

.branding-title {
    font-size: 32px;
    font-weight: 700;
    color: #fff;
    line-height: 1.2;
    margin-bottom: 12px;
}

.branding-subtitle {
    font-size: 15px;
    color: rgba(255, 255, 255, 0.7);
    line-height: 1.5;
    margin-bottom: 40px;
}

/* Steps/Pills do Ciclo */
.steps-container {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-bottom: 48px;
}

.step-pill {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 16px;
    border-radius: 12px;
    transition: all 0.2s ease;
}

.step-pill.active {
    background: #fff;
}

.step-pill.inactive {
    background: rgba(255, 255, 255, 0.1);
}

.step-number {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    font-weight: 600;
}

.step-pill.active .step-number {
    background: #000;
    color: #fff;
}

.step-pill.inactive .step-number {
    background: rgba(255, 255, 255, 0.2);
    color: rgba(255, 255, 255, 0.7);
}

.step-text {
    font-size: 14px;
    font-weight: 500;
}

.step-pill.active .step-text {
    color: #000;
}

.step-pill.inactive .step-text {
    color: rgba(255, 255, 255, 0.6);
}

.branding-footer {
    position: absolute;
    bottom: 32px;
    left: 32px;
    right: 32px;
    padding: 16px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.branding-footer-text {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.6);
    line-height: 1.5;
}

/* ========================================
   DASHBOARD PANEL (Coluna Direita)
   ======================================== */
.dashboard-panel {
    background: #000;
    padding: 32px;
    min-height: 100vh;
}

.dashboard-header {
    margin-bottom: 24px;
}

.dashboard-title {
    font-size: 24px;
    font-weight: 700;
    color: #fff;
    margin-bottom: 4px;
}

.dashboard-subtitle {
    font-size: 14px;
    color: #a3a3a3;
}

/* Barra de Filtros */
.filter-bar {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 24px;
    padding: 16px;
    background: #0f0f10;
    border: 1px solid #232323;
    border-radius: 12px;
}

/* Cards de KPI */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 32px;
}

@media (max-width: 1200px) {
    .kpi-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 768px) {
    .kpi-grid {
        grid-template-columns: 1fr;
    }
}

.kpi-card {
    background: #0f0f10;
    border: 1px solid #232323;
    border-radius: 16px;
    padding: 20px;
    transition: all 0.2s ease;
}

.kpi-card:hover {
    border-color: #3f3f46;
    transform: translateY(-2px);
}

.kpi-label {
    font-size: 12px;
    font-weight: 500;
    color: #a3a3a3;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
}

.kpi-value {
    font-size: 28px;
    font-weight: 700;
    color: #fff;
    margin-bottom: 4px;
}

.kpi-delta {
    font-size: 12px;
    font-weight: 500;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}

.kpi-delta.positive {
    color: #22c55e;
}

.kpi-delta.negative {
    color: #ef4444;
}

/* Seções */
.section-container {
    background: #0f0f10;
    border: 1px solid #232323;
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 24px;
}

.section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 20px;
}

.section-title {
    font-size: 16px;
    font-weight: 600;
    color: #fff;
}

.section-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
}

.badge-success {
    background: rgba(34, 197, 94, 0.15);
    color: #22c55e;
    border: 1px solid rgba(34, 197, 94, 0.3);
}

.badge-info {
    background: rgba(59, 130, 246, 0.15);
    color: #3b82f6;
    border: 1px solid rgba(59, 130, 246, 0.3);
}

.badge-warning {
    background: rgba(245, 158, 11, 0.15);
    color: #f59e0b;
    border: 1px solid rgba(245, 158, 11, 0.3);
}

/* Alert/Aviso */
.scope-alert {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 14px 16px;
    background: rgba(59, 130, 246, 0.08);
    border: 1px solid rgba(59, 130, 246, 0.2);
    border-radius: 12px;
    margin-bottom: 24px;
}

.scope-alert-icon {
    font-size: 18px;
    flex-shrink: 0;
}

.scope-alert-text {
    font-size: 13px;
    color: #a3a3a3;
    line-height: 1.5;
}

/* Empty State */
.empty-state {
    text-align: center;
    padding: 48px 24px;
}

.empty-state-icon {
    font-size: 48px;
    margin-bottom: 16px;
    opacity: 0.5;
}

.empty-state-title {
    font-size: 16px;
    font-weight: 600;
    color: #fff;
    margin-bottom: 8px;
}

.empty-state-text {
    font-size: 14px;
    color: #a3a3a3;
}

/* Tabelas */
.styled-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
}

.styled-table th {
    background: rgba(255, 255, 255, 0.05);
    color: #a3a3a3;
    font-size: 12px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 12px 16px;
    text-align: left;
    border-bottom: 1px solid #232323;
}

.styled-table td {
    color: #fff;
    font-size: 14px;
    padding: 14px 16px;
    border-bottom: 1px solid #232323;
}

.styled-table tr:last-child td {
    border-bottom: none;
}

.styled-table tr:hover td {
    background: rgba(255, 255, 255, 0.02);
}

/* Botões */
.btn-primary {
    background: #fff;
    color: #000;
    border: none;
    padding: 10px 20px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
}

.btn-primary:hover {
    background: #e5e5e5;
}

.btn-outline {
    background: transparent;
    color: #a3a3a3;
    border: 1px solid #3f3f46;
    padding: 10px 20px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
}

.btn-outline:hover {
    border-color: #fff;
    color: #fff;
}

/* Streamlit overrides */
.stSelectbox > div > div {
    background: #0f0f10 !important;
    border: 1px solid #232323 !important;
    border-radius: 8px !important;
}

.stSelectbox label {
    color: #a3a3a3 !important;
    font-size: 12px !important;
}

[data-testid="stMetricValue"] {
    color: #fff !important;
    font-size: 28px !important;
    font-weight: 700 !important;
}

[data-testid="stMetricLabel"] {
    color: #a3a3a3 !important;
}

[data-testid="stMetricDelta"] svg {
    display: none;
}

[data-testid="stMetricDelta"] {
    font-size: 12px !important;
}

.stDataFrame {
    background: transparent !important;
}

[data-testid="stDataFrame"] > div {
    background: transparent !important;
}

/* Gráficos Plotly */
.js-plotly-plot .plotly .modebar {
    display: none !important;
}

/* Responsivo - empilhar no mobile */
@media (max-width: 992px) {
    .branding-panel {
        min-height: auto;
        padding: 32px 24px;
    }

    .branding-footer {
        position: relative;
        bottom: auto;
        left: auto;
        right: auto;
        margin-top: 32px;
    }
}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# LAYOUT PRINCIPAL - DUAS COLUNAS
# =============================================================================

# Criar layout split
col_brand, col_dash = st.columns([0.38, 0.62], gap="small")

# =============================================================================
# COLUNA ESQUERDA - BRANDING PANEL
# =============================================================================
with col_brand:
    st.markdown("""
    <div class="branding-panel">
        <!-- Logo -->
        <div class="logo-container">
            <div class="logo-circle">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="#7c3aed" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M2 17L12 22L22 17" stroke="#7c3aed" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M2 12L12 17L22 12" stroke="#7c3aed" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <span class="logo-text">LIA</span>
        </div>

        <!-- Título -->
        <h1 class="branding-title">Ciclo 1 — Tráfego para Landing</h1>
        <p class="branding-subtitle">Medição até clique. Sem conversão final nesta fase.</p>

        <!-- Steps AIDA -->
        <div class="steps-container">
            <div class="step-pill active">
                <div class="step-number">1</div>
                <span class="step-text">Alcance</span>
            </div>
            <div class="step-pill active">
                <div class="step-number">2</div>
                <span class="step-text">Interesse</span>
            </div>
            <div class="step-pill active">
                <div class="step-number">3</div>
                <span class="step-text">Landing</span>
            </div>
            <div class="step-pill inactive">
                <div class="step-number">4</div>
                <span class="step-text">Próximos passos</span>
            </div>
        </div>

        <!-- Footer -->
        <div class="branding-footer">
            <p class="branding-footer-text">
                ⏱️ Primeiras 48h = fase de aprendizado.<br/>
                Evitar decisões precipitadas sobre criativos.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# COLUNA DIREITA - DASHBOARD OPERACIONAL
# =============================================================================
with col_dash:
    # Header do Dashboard
    st.markdown("""
    <div class="dashboard-header">
        <h1 class="dashboard-title">Dashboard Ciclo 1</h1>
        <p class="dashboard-subtitle">Performance de mídia até o clique na landing (applia.ai)</p>
    </div>
    """, unsafe_allow_html=True)

    # Barra de Filtros
    st.markdown('<div style="margin-bottom: 8px;">', unsafe_allow_html=True)
    filter_cols = st.columns([1.5, 1, 1, 1.5])

    with filter_cols[0]:
        periodo = st.selectbox(
            "Período",
            ["Hoje", "Ontem", "Últimos 7 dias", "Últimos 14 dias", "Personalizado"],
            index=2,
            key="filter_periodo"
        )

    with filter_cols[1]:
        fonte = st.selectbox(
            "Fonte",
            ["Meta", "GA4", "Ambos"],
            index=0,
            key="filter_fonte"
        )

    with filter_cols[2]:
        nivel = st.selectbox(
            "Nível",
            ["Campanha", "Conjunto", "Criativo"],
            index=0,
            key="filter_nivel"
        )

    with filter_cols[3]:
        campanha = st.selectbox(
            "Campanha",
            ["Todas", "LIA_Awareness_BR", "LIA_Trafego_BR"],
            index=0,
            key="filter_campanha"
        )

    st.markdown('</div>', unsafe_allow_html=True)

    # Mapear período para o provider
    period_map = {
        "Hoje": "today",
        "Ontem": "yesterday",
        "Últimos 7 dias": "7d",
        "Últimos 14 dias": "14d",
        "Personalizado": "7d"
    }
    selected_period = period_map.get(periodo, "7d")

    # Obter dados
    meta_data = data_provider.get_meta_metrics(period=selected_period)
    ga4_data = data_provider.get_ga4_metrics(period=selected_period)
    creative_data = data_provider.get_creative_performance()
    trends_data = data_provider.get_daily_trends(period=selected_period)

    # =============================================================================
    # KPIs PRINCIPAIS - Grid 4x2
    # =============================================================================
    st.markdown("### 📊 KPIs Principais", unsafe_allow_html=True)

    # Linha 1 de KPIs
    kpi_row1 = st.columns(4)

    with kpi_row1[0]:
        investimento = meta_data["investimento"]
        delta_inv = meta_data["delta_investimento"]
        st.metric(
            label="Investimento",
            value=f"${investimento:,.2f}",
            delta=f"{delta_inv:+.1f}%"
        )

    with kpi_row1[1]:
        impressoes = meta_data["impressoes"]
        delta_imp = meta_data["delta_impressoes"]
        st.metric(
            label="Impressões",
            value=f"{impressoes:,.0f}",
            delta=f"{delta_imp:+.1f}%"
        )

    with kpi_row1[2]:
        alcance = meta_data["alcance"]
        delta_alc = meta_data["delta_alcance"]
        st.metric(
            label="Alcance",
            value=f"{alcance:,.0f}",
            delta=f"{delta_alc:+.1f}%"
        )

    with kpi_row1[3]:
        frequencia = meta_data["frequencia"]
        delta_freq = meta_data["delta_frequencia"]
        st.metric(
            label="Frequência",
            value=f"{frequencia:.2f}",
            delta=f"{delta_freq:+.2f}"
        )

    # Linha 2 de KPIs
    kpi_row2 = st.columns(4)

    with kpi_row2[0]:
        cliques = meta_data["cliques_link"]
        delta_clq = meta_data["delta_cliques"]
        st.metric(
            label="Cliques no Link",
            value=f"{cliques:,.0f}",
            delta=f"{delta_clq:+.1f}%"
        )

    with kpi_row2[1]:
        ctr = meta_data["ctr_link"]
        delta_ctr = meta_data["delta_ctr"]
        st.metric(
            label="CTR (Link)",
            value=f"{ctr:.2f}%",
            delta=f"{delta_ctr:+.2f}pp"
        )

    with kpi_row2[2]:
        cpc = meta_data["cpc_link"]
        delta_cpc = meta_data["delta_cpc"]
        st.metric(
            label="CPC (Link)",
            value=f"${cpc:.2f}",
            delta=f"{delta_cpc:+.1f}%",
            delta_color="inverse"
        )

    with kpi_row2[3]:
        cpm = meta_data["cpm"]
        delta_cpm = meta_data["delta_cpm"]
        st.metric(
            label="CPM",
            value=f"${cpm:.2f}",
            delta=f"{delta_cpm:+.1f}%",
            delta_color="inverse"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # =============================================================================
    # PERFORMANCE POR CRIATIVO
    # =============================================================================
    st.markdown("""
    <div class="section-container">
        <div class="section-header">
            <span class="section-title">🎨 Performance por Criativo</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Identificar melhor CTR e menor CPC
    if len(creative_data) > 0:
        best_ctr_idx = creative_data["CTR Link"].idxmax()
        best_cpc_idx = creative_data["CPC Link"].idxmin()

        badge_cols = st.columns(2)
        with badge_cols[0]:
            st.markdown(f"""
            <div class="section-badge badge-success">
                🏆 Melhor CTR: <strong>{creative_data.loc[best_ctr_idx, 'Criativo'][:25]}...</strong> ({creative_data.loc[best_ctr_idx, 'CTR Link']:.2f}%)
            </div>
            """, unsafe_allow_html=True)

        with badge_cols[1]:
            st.markdown(f"""
            <div class="section-badge badge-info">
                💰 Menor CPC: <strong>{creative_data.loc[best_cpc_idx, 'Criativo'][:25]}...</strong> (${creative_data.loc[best_cpc_idx, 'CPC Link']:.2f})
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Tabela de criativos
        st.dataframe(
            creative_data.style.format({
                "Investimento": "${:.2f}",
                "Impressões": "{:,.0f}",
                "Cliques Link": "{:,.0f}",
                "CTR Link": "{:.2f}%",
                "CPC Link": "${:.2f}",
                "CPM": "${:.2f}"
            }).background_gradient(subset=["CTR Link"], cmap="Greens")
            .background_gradient(subset=["CPC Link"], cmap="Reds_r"),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">📊</div>
            <div class="empty-state-title">Ainda em aprendizado</div>
            <div class="empty-state-text">Aguarde acumular entregas para visualizar performance por criativo.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # =============================================================================
    # TENDÊNCIA TEMPORAL
    # =============================================================================
    st.markdown("### 📈 Tendência Temporal", unsafe_allow_html=True)

    chart_cols = st.columns(3)

    # Gráfico de Cliques por Dia
    with chart_cols[0]:
        fig_clicks = go.Figure()
        fig_clicks.add_trace(go.Scatter(
            x=trends_data["Data"],
            y=trends_data["Cliques"],
            mode="lines+markers",
            line=dict(color="#7c3aed", width=2),
            marker=dict(size=6, color="#7c3aed"),
            fill="tozeroy",
            fillcolor="rgba(124, 58, 237, 0.1)",
            name="Cliques"
        ))
        fig_clicks.update_layout(
            title="Cliques por Dia",
            template="plotly_dark",
            height=220,
            margin=dict(l=0, r=0, t=40, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, tickfont=dict(size=10)),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", tickfont=dict(size=10)),
            font=dict(size=12, color="#a3a3a3"),
            showlegend=False
        )
        st.plotly_chart(fig_clicks, use_container_width=True)

    # Gráfico de CTR por Dia
    with chart_cols[1]:
        fig_ctr = go.Figure()
        fig_ctr.add_trace(go.Scatter(
            x=trends_data["Data"],
            y=trends_data["CTR"],
            mode="lines+markers",
            line=dict(color="#22c55e", width=2),
            marker=dict(size=6, color="#22c55e"),
            fill="tozeroy",
            fillcolor="rgba(34, 197, 94, 0.1)",
            name="CTR"
        ))
        fig_ctr.update_layout(
            title="CTR por Dia (%)",
            template="plotly_dark",
            height=220,
            margin=dict(l=0, r=0, t=40, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, tickfont=dict(size=10)),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", tickfont=dict(size=10)),
            font=dict(size=12, color="#a3a3a3"),
            showlegend=False
        )
        st.plotly_chart(fig_ctr, use_container_width=True)

    # Gráfico de CPC por Dia
    with chart_cols[2]:
        fig_cpc = go.Figure()
        fig_cpc.add_trace(go.Scatter(
            x=trends_data["Data"],
            y=trends_data["CPC"],
            mode="lines+markers",
            line=dict(color="#f59e0b", width=2),
            marker=dict(size=6, color="#f59e0b"),
            fill="tozeroy",
            fillcolor="rgba(245, 158, 11, 0.1)",
            name="CPC"
        ))
        fig_cpc.update_layout(
            title="CPC por Dia ($)",
            template="plotly_dark",
            height=220,
            margin=dict(l=0, r=0, t=40, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, tickfont=dict(size=10)),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", tickfont=dict(size=10)),
            font=dict(size=12, color="#a3a3a3"),
            showlegend=False
        )
        st.plotly_chart(fig_cpc, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # =============================================================================
    # LANDING PAGE (GA4)
    # =============================================================================
    st.markdown("### 🌐 Landing Page (GA4)", unsafe_allow_html=True)

    # Alerta de escopo
    st.markdown("""
    <div class="scope-alert">
        <span class="scope-alert-icon">ℹ️</span>
        <span class="scope-alert-text">
            <strong>Ciclo 1 mede até clique/sessão.</strong>
            Instalações e conversões serão avaliadas nos próximos ciclos.
        </span>
    </div>
    """, unsafe_allow_html=True)

    # KPIs do GA4
    ga4_cols = st.columns(5)

    with ga4_cols[0]:
        st.metric(
            label="Sessões",
            value=f"{ga4_data['sessoes']:,.0f}",
            delta=f"{ga4_data['delta_sessoes']:+.1f}%"
        )

    with ga4_cols[1]:
        st.metric(
            label="Usuários",
            value=f"{ga4_data['usuarios']:,.0f}",
            delta=f"{ga4_data['delta_usuarios']:+.1f}%"
        )

    with ga4_cols[2]:
        st.metric(
            label="Pageviews",
            value=f"{ga4_data['pageviews']:,.0f}",
            delta=f"{ga4_data['delta_pageviews']:+.1f}%"
        )

    with ga4_cols[3]:
        st.metric(
            label="Taxa Engajamento",
            value=f"{ga4_data['taxa_engajamento']:.1f}%",
            delta=f"{ga4_data['delta_engajamento']:+.1f}%"
        )

    with ga4_cols[4]:
        st.metric(
            label="Tempo Médio",
            value=ga4_data['tempo_medio']
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabela de Origem/Mídia
    st.markdown("#### Origem/Mídia (foco em paid social)")
    source_data = data_provider.get_source_medium()
    st.dataframe(
        source_data,
        use_container_width=True,
        hide_index=True
    )

    # Footer
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align: center; padding: 24px; color: #525252; font-size: 12px;">
        Dashboard Ciclo 1 • LIA App • Atualizado em tempo real
    </div>
    """, unsafe_allow_html=True)
