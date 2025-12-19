import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import base64
import os

# =============================================================================
# CONFIGURACAO DA PAGINA
# =============================================================================
st.set_page_config(
    page_title="LIA Dashboard - Ciclo 1",
    page_icon="logo_lia.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =============================================================================
# PALETA OFICIAL LIA - Visual Caloroso (Laranja Dominante)
# =============================================================================
LIA_COLORS = {
    "primary": "#F47C3C",           # Laranja principal LIA
    "primary_light": "#F89B5C",     # Laranja claro
    "secondary": "#FB7185",         # Rosa/coral
    "coral": "#FECACA",             # Coral claro para backgrounds
    "gradient_start": "#F97316",    # Inicio gradiente
    "gradient_mid": "#FB7185",      # Meio gradiente
    "gradient_end": "#FECDD3",      # Fim gradiente (rosa suave)
    "bg_card": "#FFFFFF",           # Cards brancos
    "bg_card_alt": "#F8F8F8",       # Cards cinza claro
    "bg_dark": "#0E0E0E",           # Preto base (apenas contraste)
    "text_primary": "#1A1A1A",      # Texto principal escuro
    "text_secondary": "#555555",    # Texto secundario
    "text_muted": "#888888",        # Texto discreto
    "success": "#16A34A",           # Verde para variacao positiva
    "border": "#E5E5E5",            # Bordas suaves
}

# =============================================================================
# CARREGAR LOGO DA CORUJA
# =============================================================================
def get_logo_base64():
    """Carrega o logo da coruja em base64 para uso no HTML"""
    logo_path = os.path.join(os.path.dirname(__file__), "logo_lia.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

logo_base64 = get_logo_base64()

# =============================================================================
# DATA PROVIDER - Camada de abstracao para dados
# =============================================================================
class DataProvider:
    """Camada de abstracao para integracao com Meta Ads e GA4"""

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

    def get_cycle_status(self, period, meta_data, creative_data):
        """Gera status do ciclo com insights"""
        insights = []

        # CTR
        delta_ctr = meta_data["delta_ctr"]
        if abs(delta_ctr) < 0.5:
            insights.append("CTR estavel")
        elif delta_ctr > 0:
            insights.append("CTR em alta")
        else:
            insights.append("CTR em queda")

        # CPC
        delta_cpc = meta_data["delta_cpc"]
        if delta_cpc < 0:
            insights.append("CPC controlado")
        else:
            insights.append("CPC em observacao")

        # Criativo lider
        if len(creative_data) > 0:
            insights.append("Criativo lider ja identificado")

        # Fase
        is_learning = period in ["today", "yesterday"]
        phase = "Fase de Aprendizado (ate 48h)" if is_learning else "Otimizacao ativa"

        return {
            "insights": insights,
            "phase": phase,
            "is_learning": is_learning
        }


# Inicializar provider
data_provider = DataProvider(mode="mock")

# =============================================================================
# CSS - VISUAL CALOROSO LIA (LARANJA DOMINANTE, CARDS CLAROS)
# =============================================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

*, *::before, *::after {{ box-sizing: border-box; }}

/* Fundo principal: Gradiente LIA (igual landing) */
html, body, [data-testid="stAppViewContainer"], .stApp {{
    background: linear-gradient(135deg, {LIA_COLORS["gradient_start"]} 0%, {LIA_COLORS["gradient_mid"]} 50%, {LIA_COLORS["gradient_end"]} 100%) !important;
    min-height: 100vh;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}}

/* Esconder sidebar */
[data-testid="stSidebar"], section[data-testid="stSidebar"],
button[kind="header"], [data-testid="collapsedControl"] {{
    display: none !important;
}}

.main .block-container {{
    padding: 20px 32px !important;
    max-width: 1300px !important;
    margin: 0 auto;
}}

h1, h2, h3, h4, h5, h6, p, span, div, label {{
    font-family: 'Inter', sans-serif !important;
}}

/* ============ HEADER COM GRADIENTE ============ */
.lia-header {{
    background: linear-gradient(135deg, {LIA_COLORS["primary"]} 0%, {LIA_COLORS["secondary"]} 100%);
    border-radius: 16px;
    padding: 24px 32px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 8px 32px rgba(244, 124, 60, 0.3);
}}

.lia-header-left {{
    display: flex;
    align-items: center;
    gap: 16px;
}}

.lia-logo {{
    width: 56px;
    height: 56px;
    border-radius: 14px;
    background: white;
    padding: 4px;
}}

.lia-brand {{
    display: flex;
    flex-direction: column;
}}

.lia-brand-name {{
    font-size: 26px;
    font-weight: 700;
    color: white;
    letter-spacing: -0.5px;
    text-shadow: 0 2px 4px rgba(0,0,0,0.1);
}}

.lia-brand-tagline {{
    font-size: 14px;
    color: rgba(255,255,255,0.9);
    margin-top: 2px;
}}

.lia-cycle-badge {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 18px;
    background: rgba(255,255,255,0.2);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 10px;
    font-size: 14px;
    font-weight: 600;
    color: white;
}}

/* ============ CARDS CLAROS ============ */
.card {{
    background: {LIA_COLORS["bg_card"]};
    border-radius: 14px;
    padding: 20px 24px;
    margin-bottom: 20px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    border: 1px solid {LIA_COLORS["border"]};
}}

.card-alt {{
    background: {LIA_COLORS["bg_card_alt"]};
}}

/* ============ STATUS DO CICLO (COM CORUJA) ============ */
.status-card {{
    background: {LIA_COLORS["bg_card"]};
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 24px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.08);
    display: flex;
    align-items: flex-start;
    gap: 20px;
    border-left: 4px solid {LIA_COLORS["primary"]};
}}

.status-owl {{
    width: 52px;
    height: 52px;
    flex-shrink: 0;
}}

.status-content {{
    flex: 1;
}}

.status-title {{
    font-size: 13px;
    font-weight: 600;
    color: {LIA_COLORS["text_muted"]};
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
}}

.status-text {{
    font-size: 15px;
    color: {LIA_COLORS["text_primary"]};
    line-height: 1.6;
    margin-bottom: 12px;
}}

.status-badge {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    background: {LIA_COLORS["primary"]};
    color: white;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
}}

/* ============ SECTION TITLES ============ */
.section-title {{
    font-size: 17px;
    font-weight: 700;
    color: {LIA_COLORS["text_primary"]};
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 10px;
}}

.section-title-icon {{
    width: 24px;
    height: 24px;
    background: {LIA_COLORS["primary"]};
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 12px;
}}

/* ============ KPIs EM CARDS CLAROS ============ */
.kpi-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 24px;
}}

.kpi-card {{
    background: {LIA_COLORS["bg_card"]};
    border-radius: 12px;
    padding: 18px 20px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    border: 1px solid {LIA_COLORS["border"]};
}}

.kpi-label {{
    font-size: 11px;
    font-weight: 600;
    color: {LIA_COLORS["text_muted"]};
    text-transform: uppercase;
    letter-spacing: 0.3px;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 6px;
}}

.kpi-icon {{
    color: {LIA_COLORS["primary"]};
}}

.kpi-value {{
    font-size: 26px;
    font-weight: 700;
    color: {LIA_COLORS["text_primary"]};
    margin-bottom: 4px;
}}

.kpi-delta {{
    font-size: 12px;
    font-weight: 500;
}}

.kpi-delta.positive {{
    color: {LIA_COLORS["success"]};
}}

.kpi-delta.negative {{
    color: #DC2626;
}}

/* Override Streamlit metrics */
[data-testid="stMetricValue"] {{
    color: {LIA_COLORS["text_primary"]} !important;
    font-size: 26px !important;
    font-weight: 700 !important;
}}

[data-testid="stMetricLabel"] {{
    color: {LIA_COLORS["text_muted"]} !important;
    font-size: 11px !important;
    text-transform: uppercase !important;
}}

[data-testid="stMetricDelta"] {{
    font-size: 12px !important;
}}

[data-testid="stMetricDelta"] svg {{
    display: none !important;
}}

/* ============ BADGES ============ */
.badge-row {{
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 16px;
}}

.badge {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 14px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 500;
}}

.badge-orange {{
    background: {LIA_COLORS["primary"]}15;
    color: {LIA_COLORS["primary"]};
    border: 1px solid {LIA_COLORS["primary"]}30;
}}

.badge-green {{
    background: {LIA_COLORS["success"]}15;
    color: {LIA_COLORS["success"]};
    border: 1px solid {LIA_COLORS["success"]}30;
}}

/* ============ TABELA COM HEADER LARANJA ============ */
.table-card {{
    background: {LIA_COLORS["bg_card"]};
    border-radius: 14px;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    margin-bottom: 24px;
}}

.table-header {{
    background: linear-gradient(90deg, {LIA_COLORS["primary"]}20, {LIA_COLORS["secondary"]}10);
    padding: 14px 20px;
    border-bottom: 1px solid {LIA_COLORS["border"]};
}}

.table-header-title {{
    font-size: 15px;
    font-weight: 600;
    color: {LIA_COLORS["text_primary"]};
}}

.stDataFrame {{
    background: transparent !important;
}}

[data-testid="stDataFrame"] > div {{
    background: {LIA_COLORS["bg_card"]} !important;
    border-radius: 0 0 14px 14px !important;
}}

/* ============ ESCOPO DO CICLO (CORAL CLARO) ============ */
.scope-card {{
    background: {LIA_COLORS["coral"]};
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 12px;
    border: 1px solid {LIA_COLORS["secondary"]}30;
}}

.scope-icon {{
    font-size: 20px;
}}

.scope-text {{
    font-size: 13px;
    color: {LIA_COLORS["text_primary"]};
    line-height: 1.5;
}}

.scope-text strong {{
    font-weight: 600;
}}

/* ============ FILTROS ============ */
.stSelectbox > div > div {{
    background: {LIA_COLORS["bg_card"]} !important;
    border: 1px solid {LIA_COLORS["border"]} !important;
    border-radius: 10px !important;
}}

.stSelectbox label {{
    color: {LIA_COLORS["text_secondary"]} !important;
    font-size: 12px !important;
    font-weight: 500 !important;
}}

/* ============ GRAFICOS ============ */
.chart-card {{
    background: {LIA_COLORS["bg_card"]};
    border-radius: 14px;
    padding: 20px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}}

.js-plotly-plot .plotly .modebar {{ display: none !important; }}

/* ============ FOOTER ============ */
.dash-footer {{
    text-align: center;
    padding: 24px 0;
    color: white;
    font-size: 13px;
    margin-top: 20px;
    text-shadow: 0 1px 2px rgba(0,0,0,0.1);
}}

.dash-footer a {{
    color: white;
    text-decoration: underline;
}}

/* ============ RESPONSIVE ============ */
@media (max-width: 768px) {{
    .kpi-grid {{
        grid-template-columns: repeat(2, 1fr);
    }}
    .lia-header {{
        flex-direction: column;
        gap: 16px;
        text-align: center;
    }}
}}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# HEADER COM GRADIENTE LARANJA
# =============================================================================
logo_img = f'<img src="data:image/png;base64,{logo_base64}" class="lia-logo" alt="LIA">' if logo_base64 else '<div class="lia-logo" style="background: white; border-radius: 14px;"></div>'

st.markdown(f'''
<div class="lia-header">
    <div class="lia-header-left">
        {logo_img}
        <div class="lia-brand">
            <span class="lia-brand-name">LIA Dashboard - Ciclo 1</span>
            <span class="lia-brand-tagline">Performance de midia ate clique na landing</span>
        </div>
    </div>
    <div class="lia-cycle-badge">Ciclo 1 - Trafego</div>
</div>
''', unsafe_allow_html=True)

# =============================================================================
# FILTROS (em card claro)
# =============================================================================
st.markdown('<div class="card">', unsafe_allow_html=True)
filter_cols = st.columns([1.5, 1, 1, 1.5])
with filter_cols[0]:
    periodo = st.selectbox("Periodo", ["Hoje", "Ontem", "Ultimos 7 dias", "Ultimos 14 dias"], index=2, key="filter_periodo")
with filter_cols[1]:
    fonte = st.selectbox("Fonte", ["Meta", "GA4", "Ambos"], index=0, key="filter_fonte")
with filter_cols[2]:
    nivel = st.selectbox("Nivel", ["Campanha", "Conjunto", "Criativo"], index=0, key="filter_nivel")
with filter_cols[3]:
    campanha = st.selectbox("Campanha", ["Todas", "LIA_Awareness_BR", "LIA_Trafego_BR"], index=0, key="filter_campanha")
st.markdown('</div>', unsafe_allow_html=True)

# Mapear periodo
period_map = {"Hoje": "today", "Ontem": "yesterday", "Ultimos 7 dias": "7d", "Ultimos 14 dias": "14d"}
selected_period = period_map.get(periodo, "7d")

# Obter dados
meta_data = data_provider.get_meta_metrics(period=selected_period)
ga4_data = data_provider.get_ga4_metrics(period=selected_period)
creative_data = data_provider.get_creative_performance()
trends_data = data_provider.get_daily_trends(period=selected_period)
cycle_status = data_provider.get_cycle_status(selected_period, meta_data, creative_data)

# =============================================================================
# BLOCO 1 - STATUS DO CICLO (COM CORUJA)
# =============================================================================
owl_img = f'<img src="data:image/png;base64,{logo_base64}" class="status-owl" alt="LIA">' if logo_base64 else ''
insights_text = ".<br>".join(cycle_status["insights"]) + "."

st.markdown(f'''
<div class="status-card">
    {owl_img}
    <div class="status-content">
        <div class="status-title">Status do Ciclo 1</div>
        <div class="status-text">
            {insights_text}<br>
            Campanha em fase de aprendizado.
        </div>
        <div class="status-badge">{cycle_status["phase"]}</div>
    </div>
</div>
''', unsafe_allow_html=True)

# =============================================================================
# BLOCO 2 - KPIs PRINCIPAIS (Cards Claros)
# =============================================================================
st.markdown('<div class="section-title"><div class="section-title-icon">$</div> KPIs Principais</div>', unsafe_allow_html=True)

st.markdown('<div class="card">', unsafe_allow_html=True)
kpi_row1 = st.columns(4)
with kpi_row1[0]:
    st.metric("Investimento", f"R$ {meta_data['investimento']:,.2f}", f"{meta_data['delta_investimento']:+.1f}%")
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
    st.metric("CPC Link", f"R$ {meta_data['cpc_link']:.2f}", f"{meta_data['delta_cpc']:+.1f}%", delta_color="inverse")
with kpi_row2[3]:
    st.metric("CPM", f"R$ {meta_data['cpm']:.2f}", f"{meta_data['delta_cpm']:+.1f}%", delta_color="inverse")
st.markdown('</div>', unsafe_allow_html=True)

# =============================================================================
# BLOCO 3 - PERFORMANCE POR CRIATIVO
# =============================================================================
st.markdown('<div class="section-title"><div class="section-title-icon">*</div> Performance por Criativo</div>', unsafe_allow_html=True)

if len(creative_data) > 0:
    best_ctr_idx = creative_data["CTR"].idxmax()
    best_cpc_idx = creative_data["CPC"].idxmin()
    best_ctr_name = creative_data.loc[best_ctr_idx, "Criativo"][:25]
    best_cpc_name = creative_data.loc[best_cpc_idx, "Criativo"][:25]

    st.markdown(f'''
    <div class="badge-row">
        <div class="badge badge-orange">Melhor CTR: {best_ctr_name}... ({creative_data.loc[best_ctr_idx, "CTR"]:.2f}%)</div>
        <div class="badge badge-green">Menor CPC: {best_cpc_name}... (R$ {creative_data.loc[best_cpc_idx, "CPC"]:.2f})</div>
    </div>
    ''', unsafe_allow_html=True)

    # Tabela com header laranja
    st.markdown('<div class="table-card">', unsafe_allow_html=True)
    st.markdown('<div class="table-header"><span class="table-header-title">Criativos Ativos</span></div>', unsafe_allow_html=True)

    # Ordenar por Cliques (padrao)
    creative_sorted = creative_data.sort_values("Cliques", ascending=False)

    st.dataframe(
        creative_sorted.style.format({
            "Investimento": "R$ {:.2f}",
            "Impressoes": "{:,.0f}",
            "Cliques": "{:,.0f}",
            "CTR": "{:.2f}%",
            "CPC": "R$ {:.2f}",
            "CPM": "R$ {:.2f}"
        }),
        use_container_width=True,
        hide_index=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

# =============================================================================
# BLOCO 4 - ESCOPO DO CICLO (Coral Claro)
# =============================================================================
st.markdown(f'''
<div class="scope-card">
    <span class="scope-icon">i</span>
    <span class="scope-text"><strong>Ciclo 1 analisa midia ate clique/sessao.</strong> Conversoes finais entram em ciclos posteriores.</span>
</div>
''', unsafe_allow_html=True)

# =============================================================================
# TENDENCIA TEMPORAL (em cards claros)
# =============================================================================
st.markdown('<div class="section-title"><div class="section-title-icon">~</div> Tendencia Temporal</div>', unsafe_allow_html=True)

chart_cols = st.columns(3)

with chart_cols[0]:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    fig_clicks = go.Figure()
    fig_clicks.add_trace(go.Scatter(
        x=trends_data["Data"], y=trends_data["Cliques"],
        mode="lines+markers",
        line=dict(color=LIA_COLORS["primary"], width=3),
        marker=dict(size=8, color=LIA_COLORS["primary"]),
        fill="tozeroy", fillcolor="rgba(244,124,60,0.15)"
    ))
    fig_clicks.update_layout(
        title=dict(text="Cliques/Dia", font=dict(size=14, color=LIA_COLORS["text_primary"])),
        height=200, margin=dict(l=0, r=0, t=40, b=0),
        paper_bgcolor="transparent", plot_bgcolor="transparent",
        xaxis=dict(showgrid=False, tickfont=dict(size=10, color=LIA_COLORS["text_muted"])),
        yaxis=dict(showgrid=True, gridcolor="#E5E5E5", tickfont=dict(size=10, color=LIA_COLORS["text_muted"])),
        showlegend=False
    )
    st.plotly_chart(fig_clicks, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with chart_cols[1]:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    fig_ctr = go.Figure()
    fig_ctr.add_trace(go.Scatter(
        x=trends_data["Data"], y=trends_data["CTR"],
        mode="lines+markers",
        line=dict(color=LIA_COLORS["secondary"], width=3),
        marker=dict(size=8, color=LIA_COLORS["secondary"]),
        fill="tozeroy", fillcolor="rgba(251,113,133,0.15)"
    ))
    fig_ctr.update_layout(
        title=dict(text="CTR/Dia (%)", font=dict(size=14, color=LIA_COLORS["text_primary"])),
        height=200, margin=dict(l=0, r=0, t=40, b=0),
        paper_bgcolor="transparent", plot_bgcolor="transparent",
        xaxis=dict(showgrid=False, tickfont=dict(size=10, color=LIA_COLORS["text_muted"])),
        yaxis=dict(showgrid=True, gridcolor="#E5E5E5", tickfont=dict(size=10, color=LIA_COLORS["text_muted"])),
        showlegend=False
    )
    st.plotly_chart(fig_ctr, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with chart_cols[2]:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    fig_cpc = go.Figure()
    fig_cpc.add_trace(go.Scatter(
        x=trends_data["Data"], y=trends_data["CPC"],
        mode="lines+markers",
        line=dict(color=LIA_COLORS["success"], width=3),
        marker=dict(size=8, color=LIA_COLORS["success"]),
        fill="tozeroy", fillcolor="rgba(22,163,74,0.15)"
    ))
    fig_cpc.update_layout(
        title=dict(text="CPC/Dia (R$)", font=dict(size=14, color=LIA_COLORS["text_primary"])),
        height=200, margin=dict(l=0, r=0, t=40, b=0),
        paper_bgcolor="transparent", plot_bgcolor="transparent",
        xaxis=dict(showgrid=False, tickfont=dict(size=10, color=LIA_COLORS["text_muted"])),
        yaxis=dict(showgrid=True, gridcolor="#E5E5E5", tickfont=dict(size=10, color=LIA_COLORS["text_muted"])),
        showlegend=False
    )
    st.plotly_chart(fig_cpc, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =============================================================================
# LANDING PAGE (GA4)
# =============================================================================
st.markdown('<div class="section-title"><div class="section-title-icon">@</div> Landing Page (GA4)</div>', unsafe_allow_html=True)

st.markdown('<div class="card">', unsafe_allow_html=True)
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
st.markdown('</div>', unsafe_allow_html=True)

# Tabela Origem/Midia
st.markdown('<div class="table-card">', unsafe_allow_html=True)
st.markdown('<div class="table-header"><span class="table-header-title">Origem/Midia (foco em paid social)</span></div>', unsafe_allow_html=True)
source_data = data_provider.get_source_medium()
st.dataframe(source_data, use_container_width=True, hide_index=True)
st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown(f'''
<div class="dash-footer">
    Dashboard Ciclo 1 - <a href="https://applia.ai" target="_blank">LIA App</a> - Atualizado em tempo real
</div>
''', unsafe_allow_html=True)
