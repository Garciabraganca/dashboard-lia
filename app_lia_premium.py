import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import base64
import os
import logging
import textwrap

# Importar integrações
from config import Config
from ga_integration import GA4Integration
from meta_integration import MetaAdsIntegration

# Importar AIAgent
from ai_agent import AIAgent

# Configurar logging (apenas backend, nunca frontend)
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURACAO DA PAGINA
# =============================================================================
st.set_page_config(
    page_title="LIA Dashboard - Ciclo 2",
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
    def __init__(self, mode="auto"):
        self.mode = mode
        self.error_state = False
        self.error_message = ""
        self.meta_client = None
        self.ga4_client = None
        self._init_clients()

    def _init_clients(self):
        """Inicializa clientes das APIs se credenciais estiverem disponíveis"""
        try:
            # Inicializar Meta Ads
            if Config.validate_meta_credentials():
                self.meta_client = MetaAdsIntegration(
                    access_token=Config.get_meta_access_token(),
                    ad_account_id=Config.get_meta_ad_account_id()
                )
                logger.info("Meta Ads client initialized")
        except Exception as e:
            logger.error(f"Erro ao inicializar Meta client: {e}")
            self.meta_client = None

        try:
            # Inicializar GA4
            if Config.validate_ga4_credentials():
                self.ga4_client = GA4Integration(
                    credentials_json=Config.get_ga4_credentials(),
                    property_id=Config.get_ga4_property_id()
                )
                logger.info("GA4 client initialized")
        except Exception as e:
            logger.error(f"Erro ao inicializar GA4 client: {e}")
            self.ga4_client = None

    def _safe_execute(self, func, default=None):
        """Executa funcao com tratamento de erro"""
        try:
            return func()
        except Exception as e:
            logger.error(f"DataProvider error: {e}")
            self.error_state = True
            self.error_message = str(e)
            return default

    def _period_to_api_format(self, period):
        """Converte período do dashboard para formato da API"""
        mapping = {
            "today": "today",
            "yesterday": "yesterday",
            "7d": "last_7d",
            "14d": "last_14d",
            "30d": "last_30d",
            "custom": "custom"
        }
        return mapping.get(period, "last_7d")

    def get_meta_metrics(self, period="7d", level="campaign", filters=None, campaign_filter=None, custom_start=None, custom_end=None):
        # Tentar dados reais primeiro
        if self.meta_client and self.mode != "mock":
            try:
                api_period = self._period_to_api_format(period)
                insights = self.meta_client.get_ad_insights(date_range=api_period, campaign_name_filter=campaign_filter, custom_start=custom_start, custom_end=custom_end)
                if not insights.empty:
                    result = self._process_meta_insights(insights)
                    result["_data_source"] = "real"
                    return result
            except Exception as e:
                logger.error(f"Erro ao obter dados reais do Meta: {e}")

        # Fallback para mock
        result = self._safe_execute(
            lambda: self._get_mock_meta_metrics(period, level),
            default=self._empty_meta_metrics()
        )
        result["_data_source"] = "mock"
        return result

    def _process_meta_insights(self, df):
        """Processa insights do Meta para formato do dashboard"""
        try:
            return {
                "investimento": df['spend'].sum() if 'spend' in df.columns else 0,
                "impressoes": int(df['impressions'].sum()) if 'impressions' in df.columns else 0,
                "alcance": int(df['reach'].sum()) if 'reach' in df.columns else 0,
                "frequencia": df['frequency'].mean() if 'frequency' in df.columns else 0,
                "cliques_link": int(df['clicks'].sum()) if 'clicks' in df.columns else 0,
                "ctr_link": df['ctr'].mean() if 'ctr' in df.columns else 0,
                "cpc_link": df['cpc'].mean() if 'cpc' in df.columns else 0,
                "cpm": df['cpm'].mean() if 'cpm' in df.columns else 0,
                "delta_investimento": 0,
                "delta_impressoes": 0,
                "delta_alcance": 0,
                "delta_frequencia": 0,
                "delta_cliques": 0,
                "delta_ctr": 0,
                "delta_cpc": 0,
                "delta_cpm": 0,
            }
        except Exception as e:
            logger.error(f"Erro ao processar insights Meta: {e}")
            return self._empty_meta_metrics()

    def get_ga4_metrics(self, period="7d", filters=None, custom_start=None, custom_end=None, campaign_filter=None):
        # Tentar dados reais primeiro
        if self.ga4_client and self.mode != "mock":
            try:
                api_period = self._period_to_api_format(period)
                metrics = self.ga4_client.get_aggregated_metrics(date_range=api_period, custom_start=custom_start, custom_end=custom_end, campaign_filter=campaign_filter)
                if metrics and metrics.get('sessoes', 0) > 0:
                    # Adicionar deltas (por enquanto zerados)
                    metrics['delta_sessoes'] = 0
                    metrics['delta_usuarios'] = 0
                    metrics['delta_pageviews'] = 0
                    metrics['delta_engajamento'] = 0
                    metrics['_data_source'] = 'real'
                    metrics['_campaign_filter'] = campaign_filter
                    return metrics
                else:
                    # GA4 conectado mas sem dados para este filtro
                    result = self._get_mock_ga4_metrics(period)
                    result['_data_source'] = 'no_data'
                    result['_campaign_filter'] = campaign_filter
                    return result
            except Exception as e:
                logger.error(f"Erro ao obter dados reais do GA4: {e}")

        # Fallback para mock
        result = self._safe_execute(
            lambda: self._get_mock_ga4_metrics(period),
            default=self._empty_ga4_metrics()
        )
        result['_data_source'] = 'mock'
        return result

    def get_creative_performance(self, period="7d", campaign_filter=None, custom_start=None, custom_end=None):
        # Tentar dados reais primeiro
        if self.meta_client and self.mode != "mock":
            try:
                api_period = self._period_to_api_format(period)
                df = self.meta_client.get_creative_insights(date_range=api_period, campaign_name_filter=campaign_filter, custom_start=custom_start, custom_end=custom_end)
                if not df.empty:
                    # Formatar para o dashboard
                    result = pd.DataFrame({
                        "Criativo": df['ad_name'] if 'ad_name' in df.columns else [],
                        "Formato": "Anúncio",  # API não retorna formato diretamente
                        "Investimento": df['spend'] if 'spend' in df.columns else 0,
                        "Impressoes": df['impressions'].astype(int) if 'impressions' in df.columns else 0,
                        "Cliques": df['clicks'].astype(int) if 'clicks' in df.columns else 0,
                        "CTR": df['ctr'] if 'ctr' in df.columns else 0,
                        "CPC": df['cpc'] if 'cpc' in df.columns else 0,
                        "CPM": df['cpm'] if 'cpm' in df.columns else 0,
                    })
                    return result
            except Exception as e:
                logger.error(f"Erro ao obter criativos reais: {e}")

        # Fallback para mock
        return self._safe_execute(
            lambda: self._get_mock_creative_data(),
            default=pd.DataFrame()
        )

    def get_daily_trends(self, period="7d"):
        return self._safe_execute(
            lambda: self._get_mock_daily_trends(period),
            default=pd.DataFrame({"Data": [], "Cliques": [], "CTR": [], "CPC": []})
        )

    def get_source_medium(self, period="7d", custom_start=None, custom_end=None, campaign_filter=None):
        # Tentar dados reais primeiro
        if self.ga4_client and self.mode != "mock":
            try:
                api_period = self._period_to_api_format(period)
                source_data = self.ga4_client.get_source_medium_data(date_range=api_period, custom_start=custom_start, custom_end=custom_end, campaign_filter=campaign_filter)
                if not source_data.empty:
                    return source_data
            except Exception as e:
                logger.error(f"Erro ao obter source/medium do GA4: {e}")

        # Fallback para mock
        return self._safe_execute(
            lambda: self._get_mock_source_medium(),
            default=pd.DataFrame()
        )

    def get_events_data(self, period="7d", custom_start=None, custom_end=None, campaign_filter=None):
        """Obtém dados de eventos do GA4"""
        # Tentar dados reais primeiro
        if self.ga4_client and self.mode != "mock":
            try:
                api_period = self._period_to_api_format(period)
                events_data = self.ga4_client.get_events_data(date_range=api_period, custom_start=custom_start, custom_end=custom_end, campaign_filter=campaign_filter)
                if not events_data.empty:
                    # Formatar para exibição na tabela
                    formatted_df = pd.DataFrame({
                        'Nome do Evento': events_data['event_name'],
                        'Contagem de Eventos': events_data.apply(
                            lambda row: f"{row['event_count']:,} ({row['event_count_pct']:.2f}%)", axis=1
                        ),
                        'Total de Usuarios': events_data.apply(
                            lambda row: f"{row['total_users']:,} ({row['users_pct']:.2f}%)", axis=1
                        ),
                        'Eventos por Usuario': events_data['events_per_user'].apply(lambda x: f"{x:.2f}"),
                        'Receita Total': events_data['event_value'].apply(lambda x: f"R$ {x:,.2f}")
                    })
                    return formatted_df
            except Exception as e:
                logger.error(f"Erro ao obter eventos do GA4: {e}")

        # Fallback para mock
        return self._safe_execute(
            lambda: self._get_mock_events_data(),
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
        multiplier = {"today": 0.14, "yesterday": 0.14, "7d": 1, "14d": 2, "30d": 4.3, "custom": 1}.get(period, 1)
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
        multiplier = {"today": 0.14, "yesterday": 0.14, "7d": 1, "14d": 2, "30d": 4.3, "custom": 1}.get(period, 1)
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
        days = {"today": 1, "yesterday": 1, "7d": 7, "14d": 14, "30d": 30, "custom": 7}.get(period, 7)
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

    def _get_mock_events_data(self):
        """Retorna dados mock de eventos do GA4"""
        return pd.DataFrame({
            "Nome do Evento": [
                "page_view", "session_start", "first_visit", "scroll",
                "user_engagement", "scroll_50", "cta_baixe_agora_click"
            ],
            "Contagem de Eventos": [
                "2.050 (33,19%)", "1.992 (32,25%)", "1.958 (31,70%)", "78 (1,26%)",
                "78 (1,26%)", "17 (0,28%)", "3 (0,05%)"
            ],
            "Total de Usuarios": [
                "1.968 (100%)", "1.968 (100%)", "1.958 (99,49%)", "68 (3,46%)",
                "38 (1,93%)", "14 (0,71%)", "3 (0,15%)"
            ],
            "Eventos por Usuario": ["1,04", "1,01", "1,00", "1,15", "2,05", "1,21", "1,00"],
            "Receita Total": ["R$ 0,00", "R$ 0,00", "R$ 0,00", "R$ 0,00", "R$ 0,00", "R$ 0,00", "R$ 0,00"]
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
data_provider = DataProvider(mode="auto")

# =============================================================================
# COMPONENTE: CARD DE ERRO AMIGAVEL
# =============================================================================
def render_error_card(title="Estamos ajustando os dados", message="Algumas metricas estao temporariamente indisponiveis. Nossa equipe ja esta verificando."):
    owl_img = f'<img src="data:image/png;base64,{logo_base64}" style="width:48px;height:48px;margin-bottom:12px;">' if logo_base64 else ''
    st.markdown(f'''
    <div style="background:rgba(255,255,255,0.65);backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);border-radius:20px;padding:32px;text-align:center;border:1px solid rgba(255,255,255,0.35);margin:16px 0;box-shadow:0 20px 40px rgba(0,0,0,0.12);">
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

/* ========== CARTOES GLASSMORPHISM ========== */
.glass-card {{
    background: rgba(255, 255, 255, 0.65);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border: 1px solid rgba(255, 255, 255, 0.35);
    border-radius: 20px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.12);
    padding: 24px;
}}

.content-layer {{
    display: flex;
    flex-direction: column;
    gap: 18px;
    margin-top: 16px;
}}

/* ========== HEADER (em glass) ========== */
.lia-header {{
    background: rgba(255, 255, 255, 0.65);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border-radius: 20px;
    padding: 20px 28px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border: 1px solid rgba(255, 255, 255, 0.35);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.12);
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
    background: rgba(255,255,255,0.85);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    padding: 4px;
    border: 1px solid rgba(255, 255, 255, 0.35);
    box-shadow: 0 12px 24px rgba(0,0,0,0.12);
}}

.lia-brand-name {{
    font-size: 22px;
    font-weight: 700;
    color: {LIA["text_dark"]};
}}

.lia-brand-tagline {{
    font-size: 13px;
    color: {LIA["text_secondary"]};
}}

.lia-cycle-badge {{
    padding: 8px 16px;
    background: rgba(255,255,255,0.75);
    border: 1px solid rgba(255,255,255,0.35);
    border-radius: 12px;
    font-size: 13px;
    font-weight: 600;
    color: {LIA["text_dark"]};
}}

/* ========== TITULOS DE SECAO ========== */
.section-title {{
    font-size: 16px;
    font-weight: 700;
    color: {LIA["text_dark"]};
    margin: 0 0 14px 0;
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
    background: rgba(255, 255, 255, 0.65);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border-radius: 20px;
    padding: 24px;
    display: flex;
    align-items: flex-start;
    gap: 16px;
    border: 1px solid rgba(255, 255, 255, 0.35);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.12);
    margin-bottom: 4px;
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

/* ========== KPIs EM CARDS GLASS ========== */
.kpi-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-bottom: 8px;
}}

.ga4-grid {{
    grid-template-columns: repeat(5, 1fr);
}}

.kpi-card {{
    background: rgba(255, 255, 255, 0.65);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border: 1px solid rgba(255, 255, 255, 0.35);
    border-radius: 20px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.12);
    padding: 20px 22px;
}}

.kpi-top {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}}

.kpi-icon {{
    width: 28px;
    height: 28px;
    border-radius: 10px;
    background: linear-gradient(135deg, {LIA["primary"]}, {LIA["secondary"]});
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 14px;
    box-shadow: 0 10px 20px rgba(0,0,0,0.12);
}}

.kpi-label {{
    font-size: 11px;
    font-weight: 600;
    color: {LIA["text_secondary"]};
    text-transform: uppercase;
    letter-spacing: 0.3px;
}}

.kpi-value {{
    font-size: 26px;
    font-weight: 800;
    color: #000000;
    margin-bottom: 6px;
}}

.kpi-delta {{
    font-size: 12px;
    font-weight: 700;
}}

.kpi-delta.positive {{ color: {LIA["success"]}; }}
.kpi-delta.negative {{ color: {LIA["error"]}; }}
.kpi-delta.neutral {{ color: {LIA["text_secondary"]}; }}

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

/* ========== TABELA COM HEADER GLASS ========== */
.table-container {{
    background: rgba(255, 255, 255, 0.65);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border-radius: 20px;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.35);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.12);
    margin-bottom: 12px;
}}

.table-header {{
    background: rgba(255,255,255,0.75);
    padding: 14px 18px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.35);
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
    background: transparent !important;
}}

/* ========== CARD DE ESCOPO ========== */
.scope-card {{
    background: rgba(255, 255, 255, 0.65);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border-radius: 20px;
    padding: 16px 20px;
    display: flex;
    align-items: center;
    gap: 12px;
    border: 1px solid rgba(255, 255, 255, 0.35);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.12);
    margin-bottom: 12px;
}}

.scope-text {{
    font-size: 13px;
    color: {LIA["text_dark"]};
}}

/* ========== GRAFICOS EM CARDS ========== */
.chart-card {{
    background: rgba(255, 255, 255, 0.65);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border-radius: 20px;
    padding: 18px;
    border: 1px solid rgba(255, 255, 255, 0.35);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.12);
    margin-bottom: 12px;
}}

.js-plotly-plot .plotly .modebar {{ display: none !important; }}

/* ========== FILTROS ========== */
.filter-card {{
    background: rgba(255, 255, 255, 0.65);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border: 1px solid rgba(255, 255, 255, 0.35);
    border-radius: 20px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.12);
    padding: 18px 18px 10px 18px;
}}

.stSelectbox > div > div {{
    background: rgba(255, 255, 255, 0.8) !important;
    border: 1px solid rgba(255, 255, 255, 0.35) !important;
    border-radius: 12px !important;
    box-shadow: 0 10px 24px rgba(0, 0, 0, 0.06);
}}

.stSelectbox label {{
    color: {LIA["text_secondary"]} !important;
    font-size: 12px !important;
}}

/* ========== AGENTE DE IA ========== */
.ai-agent-card {{
    background: linear-gradient(135deg, rgba(244,124,60,0.1) 0%, rgba(251,113,133,0.1) 100%);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border: 2px solid {LIA["primary"]};
    border-radius: 20px;
    padding: 24px;
    margin-bottom: 16px;
    box-shadow: 0 20px 40px rgba(244,124,60,0.15);
}}

.ai-agent-header {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
}}

.ai-agent-icon {{
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, {LIA["primary"]}, {LIA["secondary"]});
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
}}

.ai-agent-title {{
    font-size: 16px;
    font-weight: 700;
    color: {LIA["text_dark"]};
}}

.ai-agent-subtitle {{
    font-size: 12px;
    color: {LIA["text_secondary"]};
}}

.ai-agent-content {{
    background: rgba(255,255,255,0.8);
    border-radius: 12px;
    padding: 16px;
    font-size: 14px;
    line-height: 1.6;
    color: {LIA["text_dark"]};
}}

.ai-agent-content h1, .ai-agent-content h2, .ai-agent-content h3 {{
    font-size: 14px;
    font-weight: 700;
    margin: 12px 0 8px 0;
    color: {LIA["text_dark"]};
}}

.ai-agent-content p {{
    margin: 8px 0;
}}

.ai-agent-content ul, .ai-agent-content ol {{
    margin: 8px 0;
    padding-left: 20px;
}}

/* ========== FOOTER ========== */
.footer {{
    text-align: center;
    padding: 8px 0 0 0;
    color: {LIA["text_muted"]};
    font-size: 12px;
    border-top: none;
    margin-top: 8px;
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
            <div class="lia-brand-name">LIA Dashboard - Ciclo 2</div>
            <div class="lia-brand-tagline">Performance de midia e conversoes na landing</div>
        </div>
    </div>
    <div class="lia-cycle-badge">Ciclo 2 - Conversao</div>
</div>
''', unsafe_allow_html=True)

# =============================================================================
# CAMADA DE CONTEUDO CENTRAL
# =============================================================================
st.markdown('<div class="content-layer">', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# FILTROS
# -----------------------------------------------------------------------------
st.markdown('<div class="filter-card">', unsafe_allow_html=True)
filter_cols = st.columns([1.5, 1, 1, 1.5])
with filter_cols[0]:
    periodo = st.selectbox("Periodo", ["Hoje", "Ontem", "Ultimos 7 dias", "Ultimos 14 dias", "Ultimos 30 dias", "Personalizado"], index=2, key="periodo")
with filter_cols[1]:
    fonte = st.selectbox("Fonte", ["Meta", "GA4", "Ambos"], index=0, key="fonte")
with filter_cols[2]:
    nivel = st.selectbox("Nivel", ["Campanha", "Conjunto", "Criativo"], index=0, key="nivel")
with filter_cols[3]:
    campanha = st.selectbox("Campanha", ["Ciclo 2", "Ciclo 1", "Todas"], index=0, key="campanha")

# Campos de data personalizada
custom_start_date = None
custom_end_date = None
if periodo == "Personalizado":
    date_cols = st.columns(2)
    with date_cols[0]:
        custom_start_date = st.date_input("Data Inicio", value=datetime.now() - timedelta(days=7), key="custom_start")
    with date_cols[1]:
        custom_end_date = st.date_input("Data Fim", value=datetime.now(), key="custom_end")

st.markdown('</div>', unsafe_allow_html=True)

period_map = {"Hoje": "today", "Ontem": "yesterday", "Ultimos 7 dias": "7d", "Ultimos 14 dias": "14d", "Ultimos 30 dias": "30d", "Personalizado": "custom"}
selected_period = period_map.get(periodo, "7d")

# Converter datas para string se personalizado
custom_start_str = custom_start_date.strftime("%Y-%m-%d") if custom_start_date else None
custom_end_str = custom_end_date.strftime("%Y-%m-%d") if custom_end_date else None

# Mapear nome da campanha para filtro
campaign_filter = campanha if campanha != "Todas" else None

# -----------------------------------------------------------------------------
# CARREGAR DADOS (com tratamento de erro)
# -----------------------------------------------------------------------------
try:
    meta_data = data_provider.get_meta_metrics(period=selected_period, campaign_filter=campaign_filter, custom_start=custom_start_str, custom_end=custom_end_str)
    ga4_data = data_provider.get_ga4_metrics(period=selected_period, custom_start=custom_start_str, custom_end=custom_end_str, campaign_filter=campaign_filter)
    creative_data = data_provider.get_creative_performance(period=selected_period, campaign_filter=campaign_filter, custom_start=custom_start_str, custom_end=custom_end_str)
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
status_line = f"{insights_text} {cycle_status['phase']}."

st.markdown(f'''
<div class="status-card">
    {owl_img}
    <div style="flex:1;">
        <div class="status-title">Status do Ciclo 2</div>
        <div class="status-text">{status_line}</div>
        <div class="status-badge">{cycle_status["phase"]}</div>
    </div>
</div>
''', unsafe_allow_html=True)

# Indicador de fonte de dados e diagnóstico de conexão
data_source = meta_data.get("_data_source", "unknown")
if data_source == "mock":
    st.warning("⚠️ Usando dados de demonstração. Verifique as credenciais META_ACCESS_TOKEN no Streamlit Secrets.")
elif data_source == "real":
    st.success("✅ Conectado à API Meta Ads - dados reais")

# Expander com diagnóstico detalhado da conexão
with st.expander("🔧 Diagnóstico de Conexão Meta Ads"):
    if data_provider.meta_client:
        connection_status = data_provider.meta_client.verify_connection()
        if connection_status["connected"]:
            st.success(f"✅ {connection_status['message']}")
            info = connection_status["account_info"]
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**ID da Conta:** {info.get('id', 'N/A')}")
                st.markdown(f"**Nome:** {info.get('name', 'N/A')}")
                st.markdown(f"**Empresa:** {info.get('business_name', 'N/A')}")
            with col2:
                st.markdown(f"**Status:** {info.get('status', 'N/A')}")
                st.markdown(f"**Moeda:** {info.get('currency', 'N/A')}")
                st.markdown(f"**Timezone:** {info.get('timezone', 'N/A')}")
        else:
            st.error(f"❌ {connection_status['message']}")
            if connection_status["error_code"]:
                st.code(f"Código: {connection_status['error_code']}\nDetalhes: {connection_status['error_details']}")
    else:
        st.error("❌ Cliente Meta Ads não inicializado")
        st.info("Verifique se META_ACCESS_TOKEN está configurado no Streamlit Secrets.")

# -----------------------------------------------------------------------------
# AGENTE DE IA - ANALISE INTELIGENTE
# -----------------------------------------------------------------------------
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown('''
<div class="ai-agent-header">
    <div class="ai-agent-icon">🤖</div>
    <div>
        <div class="ai-agent-title">LIA - Assistente de Marketing IA</div>
        <div class="ai-agent-subtitle">Analise inteligente dos seus dados em tempo real</div>
    </div>
</div>
''', unsafe_allow_html=True)

# Verificar se a chave da API está configurada e o módulo está disponível
openai_api_key = Config.get_openai_api_key()

if openai_api_key:
    # Botão para gerar análise
    if st.button("🔍 Gerar Analise com IA", key="ai_analyze_btn", use_container_width=True):
        with st.spinner("🤖 LIA está analisando seus dados..."):
            try:
                # Inicializar agente
                ai_agent = AIAgent(api_key=openai_api_key, model="gpt-4o-mini")

                # Obter dados extras para análise
                source_data_for_ai = data_provider.get_source_medium(period=selected_period, custom_start=custom_start_str, custom_end=custom_end_str, campaign_filter=campaign_filter)
                events_data_for_ai = data_provider.get_events_data(period=selected_period, custom_start=custom_start_str, custom_end=custom_end_str, campaign_filter=campaign_filter)

                # Gerar análise
                analysis = ai_agent.analyze(
                    meta_data=meta_data,
                    ga4_data=ga4_data,
                    creative_data=creative_data,
                    source_data=source_data_for_ai,
                    events_data=events_data_for_ai,
                    period=selected_period
                )

                # Salvar no session state para persistir
                st.session_state['ai_analysis'] = analysis
                st.session_state['ai_analysis_period'] = periodo

            except Exception as e:
                logger.error(f"Erro na análise de IA: {e}")
                st.error(f"❌ Erro ao gerar análise: {str(e)}")

    # Mostrar análise salva
    if 'ai_analysis' in st.session_state:
        st.markdown(f'''
        <div class="ai-agent-content">
            {st.session_state['ai_analysis']}
        </div>
        <p style="font-size:11px;color:#888;margin-top:8px;text-align:right;">
            Analise gerada para: {st.session_state.get('ai_analysis_period', 'N/A')}
        </p>
        ''', unsafe_allow_html=True)
else:
    st.info("💡 Configure a chave OPENAI_API_KEY nos Streamlit Secrets para ativar a análise com IA")

st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# KPIs PRINCIPAIS (em cards brancos)
# -----------------------------------------------------------------------------
def build_kpi_card(icon, label, value, delta, suffix="%", invert=False, precision=1):
    if delta is None:
        delta_class = "neutral"
        delta_text = "—"
    else:
        is_positive = delta < 0 if invert else delta >= 0
        delta_class = "positive" if is_positive else "negative"
        delta_text = f"{delta:+.{precision}f}{suffix}"
    return textwrap.dedent(f"""
    <div class="kpi-card">
        <div class="kpi-top">
            <div class="kpi-icon">{icon}</div>
            <div class="kpi-label">{label}</div>
        </div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-delta {delta_class}">{delta_text}</div>
    </div>
    """).strip()

kpi_cards = [
    {"icon": "💰", "label": "Investimento", "value": f"$ {meta_data['investimento']:,.2f}", "delta": meta_data['delta_investimento'], "suffix": "%"},
    {"icon": "👀", "label": "Impressoes", "value": f"{meta_data['impressoes']:,.0f}", "delta": meta_data['delta_impressoes'], "suffix": "%"},
    {"icon": "📡", "label": "Alcance", "value": f"{meta_data['alcance']:,.0f}", "delta": meta_data['delta_alcance'], "suffix": "%"},
    {"icon": "🔁", "label": "Frequencia", "value": f"{meta_data['frequencia']:.2f}", "delta": meta_data['delta_frequencia'], "suffix": "", "precision": 2},
    {"icon": "🖱️", "label": "Cliques Link", "value": f"{meta_data['cliques_link']:,.0f}", "delta": meta_data['delta_cliques'], "suffix": "%"},
    {"icon": "🎯", "label": "CTR Link", "value": f"{meta_data['ctr_link']:.2f}%", "delta": meta_data['delta_ctr'], "suffix": "pp", "precision": 2},
    {"icon": "💡", "label": "CPC Link", "value": f"$ {meta_data['cpc_link']:.2f}", "delta": meta_data['delta_cpc'], "suffix": "%", "invert": True},
    {"icon": "📊", "label": "CPM", "value": f"$ {meta_data['cpm']:.2f}", "delta": meta_data['delta_cpm'], "suffix": "%", "invert": True},
]

kpi_cards_html = "\n".join(
    build_kpi_card(
        card["icon"],
        card["label"],
        card["value"],
        card["delta"],
        suffix=card.get("suffix", "%"),
        invert=card.get("invert", False),
        precision=card.get("precision", 1),
    )
    for card in kpi_cards
)

kpi_section = textwrap.dedent(f"""
<div class="glass-card">
  <div class="section-title"><div class="section-icon">$</div> KPIs Principais</div>
  <div class="kpi-grid">
{kpi_cards_html}
  </div>
</div>
""")

st.markdown(kpi_section, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# PERFORMANCE POR CRIATIVO
# -----------------------------------------------------------------------------
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
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
            <div class="badge badge-green">Menor CPC: {best_cpc_name}... ($ {creative_data.loc[best_cpc_idx, "CPC"]:.2f})</div>
        </div>
        ''', unsafe_allow_html=True)

        st.markdown('<div class="table-container">', unsafe_allow_html=True)
        st.markdown('<div class="table-header"><span class="table-header-title">Criativos Ativos</span></div>', unsafe_allow_html=True)

        creative_sorted = creative_data.sort_values("Cliques", ascending=False)
        st.dataframe(
            creative_sorted.style.format({
                "Investimento": "$ {:.2f}", "Impressoes": "{:,.0f}",
                "Cliques": "{:,.0f}", "CTR": "{:.2f}%",
                "CPC": "$ {:.2f}", "CPM": "$ {:.2f}"
            }),
            use_container_width=True, hide_index=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Erro ao renderizar tabela de criativos: {e}")
        render_error_card("Dados de criativos indisponiveis", "Estamos processando as informacoes de criativos.")
else:
    st.markdown(f'''
    <div style="background:rgba(255,255,255,0.6);border-radius:16px;padding:32px;text-align:center;border:1px dashed rgba(255,255,255,0.35);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);">
        <p style="color:{LIA["text_muted"]};margin:0;">Nenhum criativo ativo no periodo selecionado.</p>
    </div>
    ''', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# ESCOPO DO CICLO
# -----------------------------------------------------------------------------
st.markdown(f'''
<div class="scope-card">
    <span style="font-size:18px;">i</span>
    <span class="scope-text"><strong>Ciclo 2 analisa midia e conversoes na landing page.</strong> Acompanhamento completo do funil de conversao.</span>
</div>
''', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TENDENCIA TEMPORAL
# -----------------------------------------------------------------------------
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title"><div class="section-icon">~</div> Tendencia Temporal</div>', unsafe_allow_html=True)

if len(trends_data) > 0:
    try:
        chart_cols = st.columns(3)

        with chart_cols[0]:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(
                x=trends_data["Data"], y=trends_data["Cliques"],
                mode="lines+markers", line=dict(color=LIA["primary"], width=3),
                marker=dict(size=10, color=LIA["primary"], line=dict(width=2, color="white")),
                fill="tozeroy", fillcolor="rgba(244,124,60,0.25)"
            ))
            fig1.update_layout(
                title=dict(text="Cliques/Dia", font=dict(size=14, color=LIA["text_dark"], family="Inter")),
                height=220, margin=dict(l=10, r=10, t=40, b=30),
                paper_bgcolor="rgba(255,255,255,0.5)", plot_bgcolor="rgba(255,255,255,0.8)",
                xaxis=dict(showgrid=False, tickfont=dict(size=11, color=LIA["text_dark"]), showline=True, linecolor="#E0E0E0"),
                yaxis=dict(showgrid=True, gridcolor="#E0E0E0", tickfont=dict(size=11, color=LIA["text_dark"]), showline=True, linecolor="#E0E0E0"),
                showlegend=False
            )
            st.plotly_chart(fig1, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with chart_cols[1]:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=trends_data["Data"], y=trends_data["CTR"],
                mode="lines+markers", line=dict(color=LIA["secondary"], width=3),
                marker=dict(size=10, color=LIA["secondary"], line=dict(width=2, color="white")),
                fill="tozeroy", fillcolor="rgba(251,113,133,0.25)"
            ))
            fig2.update_layout(
                title=dict(text="CTR/Dia (%)", font=dict(size=14, color=LIA["text_dark"], family="Inter")),
                height=220, margin=dict(l=10, r=10, t=40, b=30),
                paper_bgcolor="rgba(255,255,255,0.5)", plot_bgcolor="rgba(255,255,255,0.8)",
                xaxis=dict(showgrid=False, tickfont=dict(size=11, color=LIA["text_dark"]), showline=True, linecolor="#E0E0E0"),
                yaxis=dict(showgrid=True, gridcolor="#E0E0E0", tickfont=dict(size=11, color=LIA["text_dark"]), showline=True, linecolor="#E0E0E0"),
                showlegend=False
            )
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with chart_cols[2]:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(
                x=trends_data["Data"], y=trends_data["CPC"],
                mode="lines+markers", line=dict(color=LIA["success"], width=3),
                marker=dict(size=10, color=LIA["success"], line=dict(width=2, color="white")),
                fill="tozeroy", fillcolor="rgba(22,163,74,0.25)"
            ))
            fig3.update_layout(
                title=dict(text="CPC/Dia ($)", font=dict(size=14, color=LIA["text_dark"], family="Inter")),
                height=220, margin=dict(l=10, r=10, t=40, b=30),
                paper_bgcolor="rgba(255,255,255,0.5)", plot_bgcolor="rgba(255,255,255,0.8)",
                xaxis=dict(showgrid=False, tickfont=dict(size=11, color=LIA["text_dark"]), showline=True, linecolor="#E0E0E0"),
                yaxis=dict(showgrid=True, gridcolor="#E0E0E0", tickfont=dict(size=11, color=LIA["text_dark"]), showline=True, linecolor="#E0E0E0"),
                showlegend=False
            )
            st.plotly_chart(fig3, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Erro ao renderizar graficos: {e}")
        render_error_card("Graficos indisponiveis", "Estamos processando os dados de tendencia.")

st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# LANDING PAGE (GA4)
# -----------------------------------------------------------------------------
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title"><div class="section-icon">@</div> Landing Page (GA4)</div>', unsafe_allow_html=True)

# Indicador de fonte de dados GA4
ga4_source = ga4_data.get("_data_source", "unknown")
ga4_filter = ga4_data.get("_campaign_filter", None)
if ga4_source == "real":
    st.success(f"✅ Dados reais do GA4 - Filtro: {ga4_filter if ga4_filter else 'Todas as campanhas'}")
elif ga4_source == "no_data":
    st.warning(f"⚠️ GA4 conectado, mas sem sessoes para campanha '{ga4_filter}'. Aguarde as UTMs serem processadas (ate 24-48h).")
elif ga4_source == "mock":
    st.info("💡 Usando dados de demonstracao. Verifique as credenciais GA4 no Streamlit Secrets.")

ga4_cards = [
    {"icon": "🌐", "label": "Sessoes", "value": f"{ga4_data['sessoes']:,.0f}", "delta": ga4_data['delta_sessoes']},
    {"icon": "👥", "label": "Usuarios", "value": f"{ga4_data['usuarios']:,.0f}", "delta": ga4_data['delta_usuarios']},
    {"icon": "📄", "label": "Pageviews", "value": f"{ga4_data['pageviews']:,.0f}", "delta": ga4_data['delta_pageviews']},
    {"icon": "⚡", "label": "Engajamento", "value": f"{ga4_data['taxa_engajamento']:.1f}%", "delta": ga4_data['delta_engajamento']},
    {"icon": "⏱️", "label": "Tempo Medio", "value": ga4_data['tempo_medio'], "delta": None, "suffix": ""},
]

ga4_cards_html = "\n".join(
    build_kpi_card(
        card["icon"],
        card["label"],
        card["value"],
        card.get("delta"),
        suffix=card.get("suffix", "%"),
        invert=card.get("invert", False),
        precision=card.get("precision", 1),
    )
    for card in ga4_cards
)

ga4_section = textwrap.dedent(f"""
<div class="kpi-grid ga4-grid">
{ga4_cards_html}
</div>
""")

st.markdown(ga4_section, unsafe_allow_html=True)

# Tabelas lado a lado: Origem/Midia e Eventos
table_cols = st.columns(2)

with table_cols[0]:
    # Tabela Origem/Midia
    try:
        source_data = data_provider.get_source_medium(period=selected_period, custom_start=custom_start_str, custom_end=custom_end_str, campaign_filter=campaign_filter)
        if len(source_data) > 0:
            st.markdown('<div class="table-container">', unsafe_allow_html=True)
            st.markdown('<div class="table-header"><span class="table-header-title">Origem/Midia (foco em paid social)</span></div>', unsafe_allow_html=True)
            st.dataframe(source_data, use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Erro ao renderizar tabela de origem/midia: {e}")

with table_cols[1]:
    # Tabela de Eventos do GA4
    try:
        events_data = data_provider.get_events_data(period=selected_period, custom_start=custom_start_str, custom_end=custom_end_str, campaign_filter=campaign_filter)
        if len(events_data) > 0:
            st.markdown('<div class="table-container">', unsafe_allow_html=True)
            st.markdown('<div class="table-header"><span class="table-header-title">Eventos do GA4</span></div>', unsafe_allow_html=True)
            st.dataframe(events_data, use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Erro ao renderizar tabela de eventos: {e}")

st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown(f'''
<div class="footer glass-card">
    Dashboard Ciclo 2 - <a href="https://applia.ai" target="_blank">LIA App</a> - Atualizado em tempo real
</div>
''', unsafe_allow_html=True)

# Fechar camada de conteudo
st.markdown('</div>', unsafe_allow_html=True)
