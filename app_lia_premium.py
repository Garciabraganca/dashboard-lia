import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import base64
import os
import logging

# Configurar logging (apenas backend, nunca frontend)
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

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
# PALETA OFICIAL LIA
# =============================================================================
LIA = {
    "primary": "#F47C3C",
    "primary_light": "#FFE7D6",
    "secondary": "#FB7185",
    "coral": "#FECACA",
    "gradient_start": "#F97316",
    "gradient_mid": "#FB7185",
    "gradient_end": "#FECDD3",
    "white": "#FFFFFF",
    "bg_card": "#FFFFFF",
    "bg_zebra": "#FAFAFA",
    "text_dark": "#1A1A1A",
    "text_secondary": "#555555",
    "text_muted": "#888888",
    "success": "#16A34A",
    "error": "#DC2626",
    "border": "#E5E5E5",
    "shadow": "rgba(0,0,0,0.08)",
}

# =============================================================================
# CARREGAR LOGO DA CORUJA
# =============================================================================
def get_logo_base64():
    try:
        logo_path = os.path.join(os.path.dirname(__file__), "logo_lia.png")
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except Exception as e:
        logger.error(f"Erro ao carregar logo: {e}")
    return None

logo_base64 = get_logo_base64()

# =============================================================================
# DATA PROVIDER COM TRATAMENTO DE ERROS
# =============================================================================
class DataProvider:
    def __init__(self, mode="mock"):
        self.mode = mode
        self.error_state = False
        self.error_message = ""

    def _safe_execute(self, func, default=None):
        """Executa funcao com tratamento de erro"""
        try:
            return func()
        except Exception as e:
            logger.error(f"DataProvider error: {e}")
            self.error_state = True
            self.error_message = str(e)
            return default

    def get_meta_metrics(self, period="7d", level="campaign", filters=None):
        return self._safe_execute(
            lambda: self._get_mock_meta_metrics(period, level),
            default=self._empty_meta_metrics()
        )

    def get_ga4_metrics(self, period="7d", filters=None):
        return self._safe_execute(
            lambda: self._get_mock_ga4_metrics(period),
            default=self._empty_ga4_metrics()
        )

    def get_creative_performance(self, period="7d"):
        return self._safe_execute(
            lambda: self._get_mock_creative_data(),
            default=pd.DataFrame()
        )

    def get_daily_trends(self, period="7d"):
        return self._safe_execute(
            lambda: self._get_mock_daily_trends(period),
            default=pd.DataFrame({"Data": [], "Cliques": [], "CTR": [], "CPC": []})
        )

    def get_source_medium(self):
        return self._safe_execute(
            lambda: self._get_mock_source_medium(),
            default=pd.DataFrame()
        )

    def _empty_meta_metrics(self):
        return {
            "investimento": 0, "impressoes": 0, "alcance": 0, "frequencia": 0,
            "cliques_link": 0, "ctr_link": 0, "cpc_link": 0, "cpm": 0,
            "delta_investimento": 0, "delta_impressoes": 0, "delta_alcance": 0,
            "delta_frequencia": 0, "delta_cliques": 0, "delta_ctr": 0,
            "delta_cpc": 0, "delta_cpm": 0,
        }

    def _empty_ga4_metrics(self):
        return {
            "sessoes": 0, "usuarios": 0, "pageviews": 0,
            "taxa_engajamento": 0, "tempo_medio": "0m 0s",
            "delta_sessoes": 0, "delta_usuarios": 0,
            "delta_pageviews": 0, "delta_engajamento": 0,
        }

    def _get_mock_meta_metrics(self, period, level):
        multiplier = {"today": 0.14, "yesterday": 0.14, "7d": 1, "14d": 2}.get(period, 1)
        base = {
            "investimento": 850.00, "impressoes": 125000, "alcance": 89000,
            "frequencia": 1.40, "cliques_link": 3200, "ctr_link": 2.56,
            "cpc_link": 0.27, "cpm": 6.80,
            "delta_investimento": 12.5, "delta_impressoes": 18.3,
            "delta_alcance": 15.2, "delta_frequencia": 0.05,
            "delta_cliques": 22.1, "delta_ctr": 0.3,
            "delta_cpc": -8.5, "delta_cpm": -5.2,
        }
        return {k: v * multiplier if isinstance(v, (int, float)) and not k.startswith("delta") else v
                for k, v in base.items()}

    def _get_mock_ga4_metrics(self, period):
        multiplier = {"today": 0.14, "yesterday": 0.14, "7d": 1, "14d": 2}.get(period, 1)
        return {
            "sessoes": int(2850 * multiplier), "usuarios": int(2340 * multiplier),
            "pageviews": int(4200 * multiplier), "taxa_engajamento": 68.5,
            "tempo_medio": "1m 42s", "delta_sessoes": 15.8, "delta_usuarios": 12.3,
            "delta_pageviews": 18.9, "delta_engajamento": 3.2,
        }

    def _get_mock_creative_data(self):
        return pd.DataFrame({
            "Criativo": [
                "Video_LIA_Problema_WhatsApp_v2", "Static_Beneficios_App_v1",
                "Carousel_Features_3slides", "Video_Depoimento_Usuario",
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
        return pd.DataFrame({
            "Data": dates,
            "Cliques": [380, 420, 395, 450, 480, 510, 565][:days],
            "CTR": [2.3, 2.4, 2.35, 2.5, 2.55, 2.6, 2.75][:days],
            "CPC": [0.30, 0.28, 0.29, 0.27, 0.26, 0.25, 0.24][:days],
        })

    def _get_mock_source_medium(self):
        return pd.DataFrame({
            "Origem / Midia": ["facebook / paid", "instagram / paid", "google / cpc", "(direct) / (none)", "google / organic"],
            "Sessoes": [1450, 890, 285, 145, 80],
            "Usuarios": [1200, 750, 240, 95, 55],
            "Engajamento": ["72.3%", "68.9%", "58.2%", "45.1%", "62.8%"],
            "Tempo Medio": ["1m 58s", "1m 42s", "1m 15s", "0m 48s", "2m 05s"],
        })

    def get_cycle_status(self, period, meta_data, creative_data):
        try:
            insights = []
            delta_ctr = meta_data.get("delta_ctr", 0)
            delta_cpc = meta_data.get("delta_cpc", 0)

            if abs(delta_ctr) < 0.5:
                insights.append("CTR estavel")
            elif delta_ctr > 0:
                insights.append("CTR em alta")
            else:
                insights.append("CTR em queda")

            if delta_cpc < 0:
                insights.append("CPC controlado")
            else:
                insights.append("CPC em observacao")

            if len(creative_data) > 0:
                insights.append("Criativo lider identificado")

            is_learning = period in ["today", "yesterday"]
            phase = "Fase de Aprendizado (ate 48h)" if is_learning else "Otimizacao ativa"

            return {"insights": insights, "phase": phase, "is_learning": is_learning}
        except Exception as e:
            logger.error(f"Erro em get_cycle_status: {e}")
            return {"insights": ["Coletando dados..."], "phase": "Processando", "is_learning": True}


# Inicializar provider
data_provider = DataProvider(mode="mock")

# =============================================================================
# COMPONENTE: CARD DE ERRO AMIGAVEL
# =============================================================================
def render_error_card(title="Estamos ajustando os dados", message="Algumas metricas estao temporariamente indisponiveis. Nossa equipe ja esta verificando."):
    owl_img = f'<img src="data:image/png;base64,{logo_base64}" style="width:48px;height:48px;margin-bottom:12px;">' if logo_base64 else ''
    st.markdown(f'''
    <div style="background:{LIA["white"]};border-radius:16px;padding:32px;text-align:center;border:1px solid {LIA["border"]};margin:16px 0;">
        {owl_img}
        <h3 style="color:{LIA["text_dark"]};font-size:18px;margin:0 0 8px 0;">{title}</h3>
        <p style="color:{LIA["text_secondary"]};font-size:14px;margin:0 0 16px 0;">{message}</p>
        <button onclick="window.location.reload()" style="background:{LIA["primary"]};color:white;border:none;padding:10px 24px;border-radius:8px;font-size:14px;cursor:pointer;">
            Recarregar dados
        </button>
    </div>
    ''', unsafe_allow_html=True)

# =============================================================================
# CSS - CONTRASTE CORRIGIDO (CONTEUDO SOBRE FUNDO BRANCO)
# =============================================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

*, *::before, *::after {{ box-sizing: border-box; }}

/* Fundo: Gradiente LIA (emocional) */
html, body, [data-testid="stAppViewContainer"], .stApp {{
    background: linear-gradient(135deg, {LIA["gradient_start"]} 0%, {LIA["gradient_mid"]} 50%, {LIA["gradient_end"]} 100%) !important;
    min-height: 100vh;
    font-family: 'Inter', -apple-system, sans-serif !important;
}}

[data-testid="stSidebar"], section[data-testid="stSidebar"],
button[kind="header"], [data-testid="collapsedControl"] {{
    display: none !important;
}}

.main .block-container {{
    padding: 20px !important;
    max-width: 1200px !important;
    margin: 0 auto;
}}

/* ========== CAMADA DE CONTEUDO CENTRAL (BRANCA) ========== */
.content-layer {{
    background: {LIA["white"]};
    border-radius: 20px;
    padding: 28px 32px;
    box-shadow: 0 8px 40px {LIA["shadow"]};
    margin-top: 16px;
}}

/* ========== HEADER (sobre gradiente, texto branco OK) ========== */
.lia-header {{
    background: linear-gradient(135deg, {LIA["primary"]} 0%, {LIA["secondary"]} 100%);
    border-radius: 16px;
    padding: 20px 28px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 4px 20px rgba(244,124,60,0.3);
    margin-bottom: 0;
}}

.lia-header-left {{
    display: flex;
    align-items: center;
    gap: 14px;
}}

.lia-logo {{
    width: 50px;
    height: 50px;
    border-radius: 12px;
    background: white;
    padding: 4px;
}}

.lia-brand-name {{
    font-size: 22px;
    font-weight: 700;
    color: white;
}}

.lia-brand-tagline {{
    font-size: 13px;
    color: rgba(255,255,255,0.9);
}}

.lia-cycle-badge {{
    padding: 8px 16px;
    background: rgba(255,255,255,0.2);
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
    color: white;
}}

/* ========== TITULOS DE SECAO ========== */
.section-title {{
    font-size: 16px;
    font-weight: 700;
    color: {LIA["text_dark"]};
    margin: 24px 0 16px 0;
    display: flex;
    align-items: center;
    gap: 10px;
}}

.section-icon {{
    width: 24px;
    height: 24px;
    background: {LIA["primary"]};
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 12px;
    font-weight: bold;
}}

/* ========== STATUS DO CICLO (COM CORUJA) ========== */
.status-card {{
    background: {LIA["white"]};
    border-radius: 14px;
    padding: 20px;
    display: flex;
    align-items: flex-start;
    gap: 16px;
    border-left: 4px solid {LIA["primary"]};
    border: 1px solid {LIA["border"]};
    margin-bottom: 20px;
}}

.status-owl {{
    width: 48px;
    height: 48px;
    flex-shrink: 0;
}}

.status-title {{
    font-size: 12px;
    font-weight: 600;
    color: {LIA["text_muted"]};
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
}}

.status-text {{
    font-size: 14px;
    color: {LIA["text_dark"]};
    line-height: 1.5;
    margin-bottom: 10px;
}}

.status-badge {{
    display: inline-block;
    padding: 6px 12px;
    background: {LIA["primary"]};
    color: white;
    border-radius: 16px;
    font-size: 11px;
    font-weight: 600;
}}

/* ========== KPIs EM CARDS BRANCOS INDIVIDUAIS ========== */
.kpi-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-bottom: 20px;
}}

.kpi-card {{
    background: {LIA["white"]};
    border-radius: 12px;
    padding: 16px 18px;
    border: 1px solid {LIA["border"]};
}}

.kpi-label {{
    font-size: 11px;
    font-weight: 600;
    color: {LIA["text_muted"]};
    text-transform: uppercase;
    margin-bottom: 6px;
}}

.kpi-value {{
    font-size: 24px;
    font-weight: 700;
    color: {LIA["text_dark"]};
    margin-bottom: 4px;
}}

.kpi-delta {{
    font-size: 12px;
    font-weight: 500;
}}

.kpi-delta.positive {{ color: {LIA["success"]}; }}
.kpi-delta.negative {{ color: {LIA["error"]}; }}

/* Override Streamlit metrics para funcionar em cards brancos */
[data-testid="stMetricValue"] {{
    color: {LIA["text_dark"]} !important;
    font-size: 24px !important;
    font-weight: 700 !important;
}}

[data-testid="stMetricLabel"] {{
    color: {LIA["text_muted"]} !important;
    font-size: 11px !important;
    text-transform: uppercase !important;
}}

[data-testid="stMetricDelta"] {{
    font-size: 12px !important;
}}

[data-testid="stMetricDelta"] svg {{ display: none !important; }}

/* ========== BADGES ========== */
.badge-row {{
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 14px;
}}

.badge {{
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 500;
}}

.badge-orange {{
    background: {LIA["primary_light"]};
    color: {LIA["primary"]};
    border: 1px solid {LIA["primary"]}40;
}}

.badge-green {{
    background: #DCFCE7;
    color: {LIA["success"]};
    border: 1px solid {LIA["success"]}40;
}}

/* ========== TABELA COM HEADER LARANJA CLARO ========== */
.table-container {{
    background: {LIA["white"]};
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid {LIA["border"]};
    margin-bottom: 20px;
}}

.table-header {{
    background: {LIA["primary_light"]};
    padding: 12px 18px;
    border-bottom: 1px solid {LIA["border"]};
}}

.table-header-title {{
    font-size: 14px;
    font-weight: 600;
    color: {LIA["text_dark"]};
}}

.stDataFrame {{
    background: transparent !important;
}}

[data-testid="stDataFrame"] > div {{
    background: {LIA["white"]} !important;
}}

/* ========== CARD DE ESCOPO (CORAL CLARO) ========== */
.scope-card {{
    background: {LIA["coral"]};
    border-radius: 10px;
    padding: 14px 18px;
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 20px;
}}

.scope-text {{
    font-size: 13px;
    color: {LIA["text_dark"]};
}}

/* ========== GRAFICOS EM CARDS ========== */
.chart-card {{
    background: {LIA["white"]};
    border-radius: 12px;
    padding: 16px;
    border: 1px solid {LIA["border"]};
    margin-bottom: 16px;
}}

.js-plotly-plot .plotly .modebar {{ display: none !important; }}

/* ========== FILTROS ========== */
.stSelectbox > div > div {{
    background: {LIA["white"]} !important;
    border: 1px solid {LIA["border"]} !important;
    border-radius: 8px !important;
}}

.stSelectbox label {{
    color: {LIA["text_secondary"]} !important;
    font-size: 12px !important;
}}

/* ========== FOOTER ========== */
.footer {{
    text-align: center;
    padding: 20px 0 0 0;
    color: {LIA["text_muted"]};
    font-size: 12px;
    border-top: 1px solid {LIA["border"]};
    margin-top: 24px;
}}

.footer a {{
    color: {LIA["primary"]};
    text-decoration: none;
}}

/* Responsivo */
@media (max-width: 768px) {{
    .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }}
    .lia-header {{ flex-direction: column; gap: 12px; text-align: center; }}
}}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# HEADER (sobre gradiente - texto branco OK)
# =============================================================================
logo_img = f'<img src="data:image/png;base64,{logo_base64}" class="lia-logo" alt="LIA">' if logo_base64 else '<div class="lia-logo"></div>'

st.markdown(f'''
<div class="lia-header">
    <div class="lia-header-left">
        {logo_img}
        <div>
            <div class="lia-brand-name">LIA Dashboard - Ciclo 1</div>
            <div class="lia-brand-tagline">Performance de midia ate clique na landing</div>
        </div>
    </div>
    <div class="lia-cycle-badge">Ciclo 1 - Trafego</div>
</div>
''', unsafe_allow_html=True)

# =============================================================================
# CAMADA DE CONTEUDO CENTRAL (FUNDO BRANCO)
# =============================================================================
st.markdown('<div class="content-layer">', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# FILTROS
# -----------------------------------------------------------------------------
filter_cols = st.columns([1.5, 1, 1, 1.5])
with filter_cols[0]:
    periodo = st.selectbox("Periodo", ["Hoje", "Ontem", "Ultimos 7 dias", "Ultimos 14 dias"], index=2, key="periodo")
with filter_cols[1]:
    fonte = st.selectbox("Fonte", ["Meta", "GA4", "Ambos"], index=0, key="fonte")
with filter_cols[2]:
    nivel = st.selectbox("Nivel", ["Campanha", "Conjunto", "Criativo"], index=0, key="nivel")
with filter_cols[3]:
    campanha = st.selectbox("Campanha", ["Todas", "LIA_Awareness_BR", "LIA_Trafego_BR"], index=0, key="campanha")

period_map = {"Hoje": "today", "Ontem": "yesterday", "Ultimos 7 dias": "7d", "Ultimos 14 dias": "14d"}
selected_period = period_map.get(periodo, "7d")

# -----------------------------------------------------------------------------
# CARREGAR DADOS (com tratamento de erro)
# -----------------------------------------------------------------------------
try:
    meta_data = data_provider.get_meta_metrics(period=selected_period)
    ga4_data = data_provider.get_ga4_metrics(period=selected_period)
    creative_data = data_provider.get_creative_performance()
    trends_data = data_provider.get_daily_trends(period=selected_period)
    cycle_status = data_provider.get_cycle_status(selected_period, meta_data, creative_data)
    has_error = data_provider.error_state
except Exception as e:
    logger.error(f"Erro ao carregar dados: {e}")
    has_error = True
    meta_data = data_provider._empty_meta_metrics()
    ga4_data = data_provider._empty_ga4_metrics()
    creative_data = pd.DataFrame()
    trends_data = pd.DataFrame({"Data": [], "Cliques": [], "CTR": [], "CPC": []})
    cycle_status = {"insights": ["Processando..."], "phase": "Carregando", "is_learning": True}

# Se houver erro, mostrar card amigavel
if has_error:
    render_error_card()

# -----------------------------------------------------------------------------
# STATUS DO CICLO (COM CORUJA)
# -----------------------------------------------------------------------------
owl_img = f'<img src="data:image/png;base64,{logo_base64}" class="status-owl">' if logo_base64 else ''
insights_text = ". ".join(cycle_status["insights"]) + "."

st.markdown(f'''
<div class="status-card">
    {owl_img}
    <div style="flex:1;">
        <div class="status-title">Status do Ciclo 1</div>
        <div class="status-text">{insights_text} Campanha em fase de aprendizado.</div>
        <div class="status-badge">{cycle_status["phase"]}</div>
    </div>
</div>
''', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# KPIs PRINCIPAIS (em cards brancos)
# -----------------------------------------------------------------------------
st.markdown('<div class="section-title"><div class="section-icon">$</div> KPIs Principais</div>', unsafe_allow_html=True)

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

# -----------------------------------------------------------------------------
# PERFORMANCE POR CRIATIVO
# -----------------------------------------------------------------------------
st.markdown('<div class="section-title"><div class="section-icon">*</div> Performance por Criativo</div>', unsafe_allow_html=True)

if len(creative_data) > 0:
    try:
        best_ctr_idx = creative_data["CTR"].idxmax()
        best_cpc_idx = creative_data["CPC"].idxmin()
        best_ctr_name = creative_data.loc[best_ctr_idx, "Criativo"][:22]
        best_cpc_name = creative_data.loc[best_cpc_idx, "Criativo"][:22]

        st.markdown(f'''
        <div class="badge-row">
            <div class="badge badge-orange">Melhor CTR: {best_ctr_name}... ({creative_data.loc[best_ctr_idx, "CTR"]:.2f}%)</div>
            <div class="badge badge-green">Menor CPC: {best_cpc_name}... (R$ {creative_data.loc[best_cpc_idx, "CPC"]:.2f})</div>
        </div>
        ''', unsafe_allow_html=True)

        st.markdown('<div class="table-container">', unsafe_allow_html=True)
        st.markdown('<div class="table-header"><span class="table-header-title">Criativos Ativos</span></div>', unsafe_allow_html=True)

        creative_sorted = creative_data.sort_values("Cliques", ascending=False)
        st.dataframe(
            creative_sorted.style.format({
                "Investimento": "R$ {:.2f}", "Impressoes": "{:,.0f}",
                "Cliques": "{:,.0f}", "CTR": "{:.2f}%",
                "CPC": "R$ {:.2f}", "CPM": "R$ {:.2f}"
            }),
            use_container_width=True, hide_index=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Erro ao renderizar tabela de criativos: {e}")
        render_error_card("Dados de criativos indisponiveis", "Estamos processando as informacoes de criativos.")
else:
    st.markdown(f'''
    <div style="background:{LIA["bg_zebra"]};border-radius:12px;padding:32px;text-align:center;border:1px dashed {LIA["border"]};">
        <p style="color:{LIA["text_muted"]};margin:0;">Nenhum criativo ativo no periodo selecionado.</p>
    </div>
    ''', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# ESCOPO DO CICLO
# -----------------------------------------------------------------------------
st.markdown(f'''
<div class="scope-card">
    <span style="font-size:18px;">i</span>
    <span class="scope-text"><strong>Ciclo 1 analisa midia ate clique/sessao.</strong> Conversoes finais entram em ciclos posteriores.</span>
</div>
''', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TENDENCIA TEMPORAL
# -----------------------------------------------------------------------------
st.markdown('<div class="section-title"><div class="section-icon">~</div> Tendencia Temporal</div>', unsafe_allow_html=True)

if len(trends_data) > 0:
    try:
        chart_cols = st.columns(3)

        with chart_cols[0]:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(
                x=trends_data["Data"], y=trends_data["Cliques"],
                mode="lines+markers", line=dict(color=LIA["primary"], width=2),
                marker=dict(size=6, color=LIA["primary"]),
                fill="tozeroy", fillcolor="rgba(244,124,60,0.1)"
            ))
            fig1.update_layout(
                title=dict(text="Cliques/Dia", font=dict(size=13, color=LIA["text_dark"])),
                height=180, margin=dict(l=0, r=0, t=35, b=0),
                paper_bgcolor="transparent", plot_bgcolor="transparent",
                xaxis=dict(showgrid=False, tickfont=dict(size=9, color=LIA["text_muted"])),
                yaxis=dict(showgrid=True, gridcolor="#F0F0F0", tickfont=dict(size=9, color=LIA["text_muted"])),
                showlegend=False
            )
            st.plotly_chart(fig1, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with chart_cols[1]:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=trends_data["Data"], y=trends_data["CTR"],
                mode="lines+markers", line=dict(color=LIA["secondary"], width=2),
                marker=dict(size=6, color=LIA["secondary"]),
                fill="tozeroy", fillcolor="rgba(251,113,133,0.1)"
            ))
            fig2.update_layout(
                title=dict(text="CTR/Dia (%)", font=dict(size=13, color=LIA["text_dark"])),
                height=180, margin=dict(l=0, r=0, t=35, b=0),
                paper_bgcolor="transparent", plot_bgcolor="transparent",
                xaxis=dict(showgrid=False, tickfont=dict(size=9, color=LIA["text_muted"])),
                yaxis=dict(showgrid=True, gridcolor="#F0F0F0", tickfont=dict(size=9, color=LIA["text_muted"])),
                showlegend=False
            )
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with chart_cols[2]:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(
                x=trends_data["Data"], y=trends_data["CPC"],
                mode="lines+markers", line=dict(color=LIA["success"], width=2),
                marker=dict(size=6, color=LIA["success"]),
                fill="tozeroy", fillcolor="rgba(22,163,74,0.1)"
            ))
            fig3.update_layout(
                title=dict(text="CPC/Dia (R$)", font=dict(size=13, color=LIA["text_dark"])),
                height=180, margin=dict(l=0, r=0, t=35, b=0),
                paper_bgcolor="transparent", plot_bgcolor="transparent",
                xaxis=dict(showgrid=False, tickfont=dict(size=9, color=LIA["text_muted"])),
                yaxis=dict(showgrid=True, gridcolor="#F0F0F0", tickfont=dict(size=9, color=LIA["text_muted"])),
                showlegend=False
            )
            st.plotly_chart(fig3, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Erro ao renderizar graficos: {e}")
        render_error_card("Graficos indisponiveis", "Estamos processando os dados de tendencia.")

# -----------------------------------------------------------------------------
# LANDING PAGE (GA4)
# -----------------------------------------------------------------------------
st.markdown('<div class="section-title"><div class="section-icon">@</div> Landing Page (GA4)</div>', unsafe_allow_html=True)

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

# Tabela Origem/Midia
try:
    source_data = data_provider.get_source_medium()
    if len(source_data) > 0:
        st.markdown('<div class="table-container">', unsafe_allow_html=True)
        st.markdown('<div class="table-header"><span class="table-header-title">Origem/Midia (foco em paid social)</span></div>', unsafe_allow_html=True)
        st.dataframe(source_data, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)
except Exception as e:
    logger.error(f"Erro ao renderizar tabela de origem/midia: {e}")

# Footer
st.markdown(f'''
<div class="footer">
    Dashboard Ciclo 1 - <a href="https://applia.ai" target="_blank">LIA App</a> - Atualizado em tempo real
</div>
''', unsafe_allow_html=True)

# Fechar camada de conteudo
st.markdown('</div>', unsafe_allow_html=True)
