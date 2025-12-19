import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import base64
import os

# =============================================================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================================================
st.set_page_config(
    page_title="LIA • Dashboard Ciclo 1",
    page_icon="logo_lia.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =============================================================================
# PALETA OFICIAL LIA - Cores da Marca
# =============================================================================
# Extraídas do logo oficial da coruja LIA
LIA_COLORS = {
    "primary": "#F97316",       # Laranja principal (topo da coruja)
    "secondary": "#FB7185",     # Rosa/coral (base da coruja)
    "primary_dark": "#EA580C",  # Laranja escuro para hover/accent
    "secondary_dark": "#F43F5E", # Rosa escuro para variação
    "bg_dark": "#0A0A0A",       # Fundo principal escuro
    "bg_panel": "#111111",      # Fundo do painel
    "surface": "#171717",       # Superfície de cards
    "border": "#262626",        # Bordas sutis
    "text_primary": "#FFFFFF",  # Texto principal
    "text_secondary": "#A3A3A3", # Texto secundário
    "text_muted": "#525252",    # Texto discreto
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
# CSS CUSTOMIZADO - Tema LIA (Cores Oficiais: Laranja/Rosa)
# =============================================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

*, *::before, *::after {{ box-sizing: border-box; }}

html, body, [data-testid="stAppViewContainer"], .stApp {{
    background: {LIA_COLORS["bg_dark"]} !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}}

/* Esconder sidebar */
[data-testid="stSidebar"], section[data-testid="stSidebar"],
button[kind="header"], [data-testid="collapsedControl"] {{
    display: none !important;
}}

.main .block-container {{
    padding: 24px 40px !important;
    max-width: 1400px !important;
    margin: 0 auto;
}}

h1, h2, h3, h4, h5, h6, p, span, div, label {{
    font-family: 'Inter', sans-serif !important;
}}

/* Header com Logo LIA */
.lia-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 0 24px 0;
    border-bottom: 1px solid {LIA_COLORS["border"]};
    margin-bottom: 24px;
}}

.lia-header-left {{
    display: flex;
    align-items: center;
    gap: 16px;
}}

.lia-logo {{
    width: 48px;
    height: 48px;
    border-radius: 12px;
}}

.lia-brand {{
    display: flex;
    flex-direction: column;
}}

.lia-brand-name {{
    font-size: 24px;
    font-weight: 700;
    color: {LIA_COLORS["text_primary"]};
    letter-spacing: -0.5px;
}}

.lia-brand-tagline {{
    font-size: 13px;
    color: {LIA_COLORS["text_secondary"]};
}}

.lia-header-right {{
    display: flex;
    align-items: center;
    gap: 12px;
}}

.lia-cycle-badge {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 14px;
    background: linear-gradient(135deg, {LIA_COLORS["primary"]}22, {LIA_COLORS["secondary"]}22);
    border: 1px solid {LIA_COLORS["primary"]}44;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
    color: {LIA_COLORS["primary"]};
}}

/* Executive Summary - Cor da marca */
.exec-summary {{
    background: {LIA_COLORS["surface"]};
    border: 1px solid {LIA_COLORS["border"]};
    border-left: 3px solid {LIA_COLORS["primary"]};
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 24px;
}}

.exec-label {{
    font-size: 11px;
    font-weight: 600;
    color: {LIA_COLORS["text_muted"]};
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
}}

.exec-text {{
    font-size: 14px;
    color: {LIA_COLORS["text_primary"]};
    font-weight: 500;
}}

/* KPIs */
[data-testid="stMetricValue"] {{
    color: {LIA_COLORS["text_primary"]} !important;
    font-size: 26px !important;
    font-weight: 700 !important;
}}

[data-testid="stMetricLabel"] {{
    color: {LIA_COLORS["text_secondary"]} !important;
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.3px !important;
}}

[data-testid="stMetricDelta"] {{
    font-size: 11px !important;
    opacity: 0.8 !important;
}}

[data-testid="stMetricDelta"] svg {{
    display: none !important;
}}

/* Seções */
.section-title {{
    font-size: 16px;
    font-weight: 600;
    color: {LIA_COLORS["text_primary"]};
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}}

.section-title::before {{
    content: "";
    width: 4px;
    height: 16px;
    background: {LIA_COLORS["primary"]};
    border-radius: 2px;
}}

/* Badges - Cores da marca LIA */
.badge-row {{
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 16px;
}}

.badge {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 14px;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 500;
}}

.badge-primary {{
    background: {LIA_COLORS["primary"]}18;
    color: {LIA_COLORS["primary"]};
    border: 1px solid {LIA_COLORS["primary"]}33;
}}

.badge-secondary {{
    background: {LIA_COLORS["secondary"]}18;
    color: {LIA_COLORS["secondary"]};
    border: 1px solid {LIA_COLORS["secondary"]}33;
}}

/* Alerta de escopo - Cores da marca */
.scope-note {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 16px;
    background: {LIA_COLORS["primary"]}0A;
    border: 1px solid {LIA_COLORS["primary"]}22;
    border-radius: 10px;
    margin-bottom: 16px;
}}

.scope-note-icon {{
    color: {LIA_COLORS["primary"]};
    font-size: 16px;
}}

.scope-note-text {{
    font-size: 12px;
    color: {LIA_COLORS["text_secondary"]};
}}

.scope-note-text strong {{
    color: {LIA_COLORS["text_primary"]};
}}

/* Empty State com Coruja */
.empty-box {{
    text-align: center;
    padding: 48px 24px;
    background: {LIA_COLORS["surface"]};
    border: 1px dashed {LIA_COLORS["border"]};
    border-radius: 12px;
}}

.empty-box-owl {{
    width: 64px;
    height: 64px;
    margin: 0 auto 16px;
    opacity: 0.6;
}}

.empty-box-title {{
    font-size: 15px;
    font-weight: 600;
    color: {LIA_COLORS["text_secondary"]};
    margin-bottom: 6px;
}}

.empty-box-text {{
    font-size: 13px;
    color: {LIA_COLORS["text_muted"]};
}}

/* Tabelas */
.stDataFrame {{ background: transparent !important; }}
[data-testid="stDataFrame"] > div {{ background: transparent !important; }}

/* Gráficos */
.js-plotly-plot .plotly .modebar {{ display: none !important; }}

/* Streamlit overrides */
.stSelectbox > div > div {{
    background: {LIA_COLORS["surface"]} !important;
    border: 1px solid {LIA_COLORS["border"]} !important;
    border-radius: 8px !important;
}}

.stSelectbox label {{
    color: {LIA_COLORS["text_secondary"]} !important;
    font-size: 11px !important;
}}

/* Footer */
.dash-footer {{
    text-align: center;
    padding: 32px 0;
    color: {LIA_COLORS["text_muted"]};
    font-size: 12px;
    border-top: 1px solid {LIA_COLORS["border"]};
    margin-top: 32px;
}}

.dash-footer a {{
    color: {LIA_COLORS["primary"]};
    text-decoration: none;
}}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# HEADER COM LOGO LIA
# =============================================================================
logo_img = f'<img src="data:image/png;base64,{logo_base64}" class="lia-logo" alt="LIA">' if logo_base64 else '<div class="lia-logo" style="background: linear-gradient(135deg, #F97316, #FB7185); border-radius: 12px;"></div>'

st.markdown(f'''
<div class="lia-header">
    <div class="lia-header-left">
        {logo_img}
        <div class="lia-brand">
            <span class="lia-brand-name">LIA Dashboard</span>
            <span class="lia-brand-tagline">Performance de midia • applia.ai</span>
        </div>
    </div>
    <div class="lia-header-right">
        <div class="lia-cycle-badge">Ciclo 1 • Trafego</div>
    </div>
</div>
''', unsafe_allow_html=True)

# =============================================================================
# FILTROS
# =============================================================================
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

st.markdown("<br>", unsafe_allow_html=True)

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

st.markdown("<br>", unsafe_allow_html=True)

# =============================================================================
# PERFORMANCE POR CRIATIVO
# =============================================================================
st.markdown('<div class="section-title">Performance por Criativo</div>', unsafe_allow_html=True)

if len(creative_data) > 0:
    best_ctr_idx = creative_data["CTR"].idxmax()
    best_cpc_idx = creative_data["CPC"].idxmin()
    best_ctr_name = creative_data.loc[best_ctr_idx, "Criativo"][:25]
    best_cpc_name = creative_data.loc[best_cpc_idx, "Criativo"][:25]

    st.markdown(f'''
    <div class="badge-row">
        <div class="badge badge-primary">Melhor CTR: {best_ctr_name}... ({creative_data.loc[best_ctr_idx, "CTR"]:.2f}%)</div>
        <div class="badge badge-secondary">Menor CPC: {best_cpc_name}... (R$ {creative_data.loc[best_cpc_idx, "CPC"]:.2f})</div>
    </div>
    ''', unsafe_allow_html=True)

    # Tabela
    st.dataframe(
        creative_data.style.format({
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
else:
    owl_img = f'<img src="data:image/png;base64,{logo_base64}" class="empty-box-owl" alt="LIA">' if logo_base64 else ''
    st.markdown(f'''
    <div class="empty-box">
        {owl_img}
        <div class="empty-box-title">Ainda em aprendizado</div>
        <div class="empty-box-text">A LIA esta coletando dados. Volte apos acumular entrega (impressoes/cliques).</div>
    </div>
    ''', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# =============================================================================
# TENDÊNCIA TEMPORAL
# =============================================================================
st.markdown('<div class="section-title">Tendencia Temporal</div>', unsafe_allow_html=True)

chart_cols = st.columns(3)

# Cores da marca para gráficos
PRIMARY_COLOR = LIA_COLORS["primary"]
SECONDARY_COLOR = LIA_COLORS["secondary"]
PRIMARY_DARK = LIA_COLORS["primary_dark"]

with chart_cols[0]:
    fig_clicks = go.Figure()
    fig_clicks.add_trace(go.Scatter(
        x=trends_data["Data"], y=trends_data["Cliques"],
        mode="lines+markers", line=dict(color=PRIMARY_COLOR, width=2),
        marker=dict(size=6, color=PRIMARY_COLOR),
        fill="tozeroy", fillcolor=f"rgba(249,115,22,0.1)"
    ))
    fig_clicks.update_layout(
        title="Cliques/Dia", template="plotly_dark", height=220,
        margin=dict(l=0, r=0, t=40, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, tickfont=dict(size=10, color=LIA_COLORS["text_muted"])),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", tickfont=dict(size=10, color=LIA_COLORS["text_muted"])),
        font=dict(size=12, color=LIA_COLORS["text_secondary"]), showlegend=False
    )
    st.plotly_chart(fig_clicks, use_container_width=True)

with chart_cols[1]:
    fig_ctr = go.Figure()
    fig_ctr.add_trace(go.Scatter(
        x=trends_data["Data"], y=trends_data["CTR"],
        mode="lines+markers", line=dict(color=SECONDARY_COLOR, width=2),
        marker=dict(size=6, color=SECONDARY_COLOR),
        fill="tozeroy", fillcolor=f"rgba(251,113,133,0.1)"
    ))
    fig_ctr.update_layout(
        title="CTR/Dia (%)", template="plotly_dark", height=220,
        margin=dict(l=0, r=0, t=40, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, tickfont=dict(size=10, color=LIA_COLORS["text_muted"])),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", tickfont=dict(size=10, color=LIA_COLORS["text_muted"])),
        font=dict(size=12, color=LIA_COLORS["text_secondary"]), showlegend=False
    )
    st.plotly_chart(fig_ctr, use_container_width=True)

with chart_cols[2]:
    fig_cpc = go.Figure()
    fig_cpc.add_trace(go.Scatter(
        x=trends_data["Data"], y=trends_data["CPC"],
        mode="lines+markers", line=dict(color=PRIMARY_DARK, width=2),
        marker=dict(size=6, color=PRIMARY_DARK),
        fill="tozeroy", fillcolor=f"rgba(234,88,12,0.1)"
    ))
    fig_cpc.update_layout(
        title="CPC/Dia (R$)", template="plotly_dark", height=220,
        margin=dict(l=0, r=0, t=40, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, tickfont=dict(size=10, color=LIA_COLORS["text_muted"])),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", tickfont=dict(size=10, color=LIA_COLORS["text_muted"])),
        font=dict(size=12, color=LIA_COLORS["text_secondary"]), showlegend=False
    )
    st.plotly_chart(fig_cpc, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# =============================================================================
# LANDING PAGE (GA4)
# =============================================================================
st.markdown('<div class="section-title">Landing Page (GA4)</div>', unsafe_allow_html=True)

st.markdown(f'''
<div class="scope-note">
    <span class="scope-note-icon">i</span>
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
st.markdown(f'''
<div class="dash-footer">
    Dashboard Ciclo 1 • <a href="https://applia.ai" target="_blank">LIA App</a> • Atualizado em tempo real
</div>
''', unsafe_allow_html=True)
