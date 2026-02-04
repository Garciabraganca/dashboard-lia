import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import base64
import json
import html
import os
import logging
import textwrap

# Importar integrações
from config import Config
from ga_integration import GA4Integration
from meta_integration import MetaAdsIntegration

# Importar AIAgent para análise de IA
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
# PALETA OFICIAL LIA - NEON DUSK THEME
# =============================================================================
LIA = {
    # Cores principais Neon Dusk
    "primary": "#00D4FF",           # Cyan vibrante
    "primary_dark": "#00A8CC",      # Cyan escuro para hover
    "primary_light": "#E0F7FF",     # Cyan bem claro para backgrounds
    "secondary": "#0EA5E9",         # Azul céu
    "accent": "#06B6D4",            # Teal accent

    # Gradiente Neon Dusk
    "gradient_start": "#020024",    # Azul escuro profundo
    "gradient_mid": "#090979",      # Azul médio
    "gradient_end": "#00D4FF",      # Cyan vibrante

    # Backgrounds
    "bg_dark": "#020024",           # Fundo escuro principal
    "bg_card": "rgba(2, 0, 36, 0.85)",  # Card escuro semi-transparente
    "bg_card_solid": "#0A0A2E",     # Card escuro sólido
    "bg_glass": "rgba(0, 212, 255, 0.08)", # Glass effect com cyan
    "bg_hover": "rgba(0, 212, 255, 0.15)", # Hover state

    # Texto - alto contraste
    "text_light": "#FFFFFF",        # Texto principal (branco)
    "text_primary": "#F0F9FF",      # Texto primário (off-white)
    "text_secondary": "#94A3B8",    # Texto secundário (cinza claro)
    "text_muted": "#64748B",        # Texto muted (cinza médio)
    "text_dark": "#1E293B",         # Texto escuro (para fundos claros)

    # Status colors
    "success": "#10B981",           # Verde esmeralda
    "success_light": "#D1FAE5",     # Verde claro
    "error": "#EF4444",             # Vermelho
    "error_light": "#FEE2E2",       # Vermelho claro
    "warning": "#F59E0B",           # Amarelo/laranja
    "warning_light": "#FEF3C7",     # Amarelo claro

    # Bordas e sombras
    "border": "rgba(0, 212, 255, 0.2)",  # Borda cyan sutil
    "border_light": "rgba(255, 255, 255, 0.1)", # Borda clara
    "shadow": "rgba(0, 0, 0, 0.3)",      # Sombra
    "glow": "rgba(0, 212, 255, 0.4)",    # Glow cyan
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
            "last_7d": "last_7d",
            "last_14d": "last_14d",
            "last_30d": "last_30d",
            "custom": "custom"
        }
        return mapping.get(period, "last_7d")

    def get_meta_metrics(self, period="7d", level="campaign", filters=None, campaign_filter=None, custom_start=None, custom_end=None):
        # Tentar dados reais primeiro
        if self.meta_client and self.mode != "mock":
            try:
                api_period = self._period_to_api_format(period)

                # Primeiro busca COM filtro de campanha
                insights = self.meta_client.get_ad_insights(date_range=api_period, campaign_name_filter=campaign_filter, custom_start=custom_start, custom_end=custom_end)

                if not insights.empty:
                    result = self._process_meta_insights(insights)

                    # Buscar métricas agregadas para Alcance e Frequência corretos
                    aggregated = self.meta_client.get_aggregated_insights(
                        date_range=api_period,
                        campaign_name_filter=campaign_filter,
                        custom_start=custom_start,
                        custom_end=custom_end
                    )
                    if aggregated:
                        result["alcance"] = aggregated.get("reach", result["alcance"])
                        result["frequencia"] = aggregated.get("frequency", result["frequencia"])

                    result["_data_source"] = "real"
                    result["_filter_applied"] = campaign_filter
                    return result

                # Se não encontrou com filtro, tenta SEM filtro para ver se há dados
                if campaign_filter:
                    logger.info(f"Meta: No data found for filter '{campaign_filter}', trying without filter")
                    insights_no_filter = self.meta_client.get_ad_insights(date_range=api_period, campaign_name_filter=None, custom_start=custom_start, custom_end=custom_end)

                    if not insights_no_filter.empty:
                        # Há dados mas não com o filtro especificado
                        result = self._process_meta_insights(insights_no_filter)

                        # Buscar métricas agregadas para Alcance e Frequência corretos
                        aggregated = self.meta_client.get_aggregated_insights(
                            date_range=api_period,
                            campaign_name_filter=None,
                            custom_start=custom_start,
                            custom_end=custom_end
                        )
                        if aggregated:
                            result["alcance"] = aggregated.get("reach", result["alcance"])
                            result["frequencia"] = aggregated.get("frequency", result["frequencia"])

                        result["_data_source"] = "real_no_filter"
                        result["_filter_applied"] = None
                        result["_requested_filter"] = campaign_filter
                        # Log das campanhas disponíveis para debug
                        if 'campaign_name' in insights_no_filter.columns:
                            available = insights_no_filter['campaign_name'].unique().tolist()
                            logger.info(f"Meta: Available campaigns: {available}")
                            result["_available_campaigns"] = available
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
        import math

        def safe_sum(col):
            """Soma segura que trata NaN"""
            if col not in df.columns:
                return 0
            val = df[col].sum()
            return 0 if (pd.isna(val) or math.isnan(val)) else val

        def safe_int(val):
            """Conversão segura para int"""
            if pd.isna(val) or (isinstance(val, float) and math.isnan(val)):
                return 0
            return int(val)

        def safe_div(numerator, denominator):
            """Divisão segura que retorna 0 se divisor for 0"""
            if denominator == 0:
                return 0
            return numerator / denominator

        def sum_actions(action_types):
            """Soma ações do Meta Ads que correspondem aos tipos informados."""
            if 'actions' not in df.columns:
                return 0

            total = 0
            for actions in df['actions'].dropna():
                parsed_actions = []
                if isinstance(actions, str):
                    try:
                        parsed_actions = json.loads(actions)
                    except json.JSONDecodeError:
                        continue
                elif isinstance(actions, dict):
                    parsed_actions = [actions]
                elif isinstance(actions, list):
                    parsed_actions = actions
                else:
                    continue

                for action in parsed_actions:
                    if not isinstance(action, dict):
                        continue
                    action_type = action.get('action_type')
                    if action_type in action_types:
                        try:
                            total += float(action.get('value', 0))
                        except (TypeError, ValueError):
                            continue

            return int(total)

        try:
            # Agregar métricas básicas
            total_spend = safe_sum('spend')
            total_impressions = safe_int(safe_sum('impressions'))
            total_clicks = safe_int(safe_sum('clicks'))

            # Calcular métricas derivadas corretamente a partir dos totais
            # CTR = (clicks / impressions) * 100
            ctr = safe_div(total_clicks, total_impressions) * 100
            # CPC = spend / clicks
            cpc = safe_div(total_spend, total_clicks)
            # CPM = (spend / impressions) * 1000
            cpm = safe_div(total_spend, total_impressions) * 1000

            # Nota: Alcance e Frequência serão sobrescritos pelo get_aggregated_insights
            # pois não podem ser somados (são métricas de usuários únicos)
            sdk_install_actions = {
                "app_install",
                "mobile_app_install",
                "omni_app_install",
                "app_install_event",
                "mobile_app_install_event",
            }
            return {
                "investimento": total_spend,
                "impressoes": total_impressions,
                "alcance": safe_int(safe_sum('reach')),  # Será sobrescrito por aggregated
                "frequencia": 0,  # Será sobrescrito por aggregated
                "cliques_link": total_clicks,
                "instalacoes_sdk": sum_actions(sdk_install_actions),
                "ctr_link": round(ctr, 2),
                "cpc_link": round(cpc, 2),
                "cpm": round(cpm, 2),
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

                if metrics:
                    sessions = metrics.get('sessoes', 0)
                    users = metrics.get('usuarios', 0)
                    pageviews = metrics.get('pageviews', 0)

                    # Log para diagnóstico
                    logger.info(f"GA4 metrics retrieved - sessions: {sessions}, users: {users}, pageviews: {pageviews}, filter: {campaign_filter}")

                    # Verificar se há dados significativos (não apenas sessions)
                    has_meaningful_data = sessions > 0 or users > 0 or pageviews > 0

                    if has_meaningful_data:
                        # Adicionar deltas (por enquanto zerados)
                        metrics['delta_sessoes'] = 0
                        metrics['delta_usuarios'] = 0
                        metrics['delta_pageviews'] = 0
                        metrics['delta_engajamento'] = 0
                        metrics['_campaign_filter'] = campaign_filter

                        # Indicar se dados são completos ou parciais
                        if sessions > 0:
                            metrics['_data_source'] = 'real'
                        else:
                            # Dados parciais: há pageviews/users mas não sessions
                            metrics['_data_source'] = 'partial'
                            logger.warning(f"GA4 partial data: sessions=0 but users={users}, pageviews={pageviews}")
                        return metrics

                # GA4 conectado mas sem dados para este filtro
                return {**self._empty_metrics(), "_data_source": "no_data", "_campaign_filter": campaign_filter}

            except Exception as e:
                logger.error(f"Erro ao obter dados reais do GA4: {e}")

        # Fallback para mock
        metrics = self._get_mock_ga4_metrics()
        metrics["_data_source"] = "mock"
        return metrics

    def get_source_medium(self, period="7d", custom_start=None, custom_end=None, campaign_filter=None):
        if self.ga4_client and self.mode != "mock":
            try:
                api_period = self._period_to_api_format(period)
                df = self.ga4_client.get_sessions_data(date_range=api_period, custom_start=custom_start, custom_end=custom_end)
                if not df.empty:
                    # Agrupar por source_medium
                    summary = df.groupby('source_medium').agg({
                        'sessions': 'sum',
                        'users': 'sum',
                        'engagement_rate': 'mean',
                        'pageviews': 'sum'
                    }).reset_index()
                    summary = summary.sort_values('sessions', ascending=False)
                    summary.columns = ["Origem / Midia", "Sessoes", "Usuarios", "Engajamento", "Pageviews"]
                    # Formatar engajamento
                    summary["Engajamento"] = summary["Engajamento"].apply(lambda x: f"{x*100:.1f}%")
                    return summary
            except Exception as e:
                logger.error(f"Erro ao obter source/medium real: {e}")

        return self._get_mock_source_medium()

    def get_events_data(self, period="7d", custom_start=None, custom_end=None, campaign_filter=None):
        if self.ga4_client and self.mode != "mock":
            try:
                api_period = self._period_to_api_format(period)
                df = self.ga4_client.get_events_data(date_range=api_period, custom_start=custom_start, custom_end=custom_end, campaign_filter=campaign_filter)
                if not df.empty:
                    # Renomear colunas para o dashboard
                    df = df.rename(columns={
                        'event_name': 'Nome do Evento',
                        'event_count': 'Contagem de Eventos',
                        'total_users': 'Total de Usuarios',
                        'events_per_user': 'Eventos por Usuario'
                    })
                    # Formatar colunas com percentuais
                    df['Contagem de Eventos'] = df.apply(lambda x: f"{x['Contagem de Eventos']:,} ({x['event_count_pct']:.2f}%)".replace(',', '.'), axis=1)
                    df['Total de Usuarios'] = df.apply(lambda x: f"{x['Total de Usuarios']:,} ({x['users_pct']:.2f}%)".replace(',', '.'), axis=1)
                    df['Eventos por Usuario'] = df['Eventos por Usuario'].apply(lambda x: f"{x:.2f}".replace('.', ','))

                    return df[['Nome do Evento', 'Contagem de Eventos', 'Total de Usuarios', 'Eventos por Usuario']]
            except Exception as e:
                logger.error(f"Erro ao obter eventos reais: {e}")

        return self._get_mock_events_data()

    def get_creative_data(self, period="7d", custom_start=None, custom_end=None, campaign_filter=None):
        if self.meta_client and self.mode != "mock":
            try:
                api_period = self._period_to_api_format(period)

                # Primeiro tenta com filtro de campanha
                df = self.meta_client.get_creative_insights(date_range=api_period, campaign_name_filter=campaign_filter, custom_start=custom_start, custom_end=custom_end)

                # Se não encontrou com filtro, tenta sem filtro
                if df.empty and campaign_filter:
                    logger.info(f"Creative: No data with filter '{campaign_filter}', trying without filter")
                    df = self.meta_client.get_creative_insights(date_range=api_period, campaign_name_filter=None, custom_start=custom_start, custom_end=custom_end)

                if not df.empty:
                    # Renomear e selecionar colunas
                    df = df.rename(columns={
                        'ad_name': 'Criativo',
                        'spend': 'Investimento',
                        'impressions': 'Impressoes',
                        'clicks': 'Cliques',
                        'ctr': 'CTR',
                        'cpc': 'CPC',
                        'cpm': 'CPM'
                    })
                    # Adicionar coluna de formato (Meta API não retorna diretamente de forma simples, vamos inferir ou deixar fixo)
                    df['Formato'] = df['Criativo'].apply(lambda x: "Video" if "video" in str(x).lower() else "Imagem")
                    return df[['Criativo', 'Formato', 'Investimento', 'Impressoes', 'Cliques', 'CTR', 'CPC', 'CPM']]
            except Exception as e:
                logger.error(f"Erro ao obter criativos reais: {e}")

        # Retorna DataFrame vazio em vez de mock data para não mostrar dados falsos
        return pd.DataFrame()

    def get_daily_trends(self, period="7d", custom_start=None, custom_end=None, campaign_filter=None):
        """Retorna dados de tendência diária (cliques, CTR, CPC)"""
        if self.meta_client and self.mode != "mock":
            try:
                api_period = self._period_to_api_format(period)

                # Primeiro tenta com filtro de campanha
                df = self.meta_client.get_ad_insights(
                    date_range=api_period,
                    campaign_name_filter=campaign_filter,
                    custom_start=custom_start,
                    custom_end=custom_end
                )

                # Se não encontrou com filtro, tenta sem filtro
                if df.empty and campaign_filter:
                    logger.info(f"Trends: No data with filter '{campaign_filter}', trying without filter")
                    df = self.meta_client.get_ad_insights(
                        date_range=api_period,
                        campaign_name_filter=None,
                        custom_start=custom_start,
                        custom_end=custom_end
                    )

                if not df.empty and 'date_start' in df.columns:
                    # Agrupar por data para obter totais diários
                    df['Data'] = pd.to_datetime(df['date_start']).dt.strftime('%d/%m')
                    df['_sort_key'] = pd.to_datetime(df['date_start'])

                    # Agregar corretamente: CTR e CPC são métricas derivadas
                    # CTR = clicks / impressions * 100
                    # CPC = spend / clicks
                    daily = df.groupby(['Data', '_sort_key'], sort=False).agg({
                        'clicks': 'sum',
                        'impressions': 'sum',
                        'spend': 'sum'
                    }).reset_index()

                    # Calcular métricas derivadas corretamente
                    daily['Cliques'] = daily['clicks']
                    daily['CTR'] = (daily['clicks'] / daily['impressions'] * 100).fillna(0)
                    daily['CPC'] = (daily['spend'] / daily['clicks']).fillna(0)

                    # Ordenar por data cronologicamente
                    daily = daily.sort_values('_sort_key').drop(columns=['_sort_key', 'clicks', 'impressions', 'spend'])
                    return daily
            except Exception as e:
                logger.error(f"Erro ao obter tendências reais: {e}")

        # Retorna DataFrame vazio se não há dados reais
        return pd.DataFrame()

    def _empty_meta_metrics(self):
        return {
            "investimento": 0, "impressoes": 0, "alcance": 0, "frequencia": 0,
            "cliques_link": 0, "instalacoes_sdk": 0, "ctr_link": 0, "cpc_link": 0, "cpm": 0,
            "delta_investimento": 0, "delta_impressoes": 0, "delta_alcance": 0,
            "delta_frequencia": 0, "delta_cliques": 0, "delta_ctr": 0,
            "delta_cpc": 0, "delta_cpm": 0,
        }

    def _empty_metrics(self):
        return {
            'sessoes': 0, 'usuarios': 0, 'pageviews': 0,
            'taxa_engajamento': 0, 'tempo_medio': "0m 0s",
            'delta_sessoes': 0, 'delta_usuarios': 0, 'delta_pageviews': 0, 'delta_engajamento': 0
        }

    def _get_mock_meta_metrics(self, period, level):
        return {
            "investimento": 1250.50, "impressoes": 85400, "alcance": 42100, "frequencia": 2.03,
            "cliques_link": 2450, "instalacoes_sdk": 320, "ctr_link": 2.87, "cpc_link": 0.51, "cpm": 14.64,
            "delta_investimento": 12.5, "delta_impressoes": -5.2, "delta_alcance": 3.1,
            "delta_frequencia": 0.5, "delta_cliques": 15.8, "delta_ctr": 0.45,
            "delta_cpc": -8.2, "delta_cpm": 2.3,
        }

    def _get_mock_ga4_metrics(self):
        return {
            "sessoes": 3240, "usuarios": 2850, "pageviews": 6120,
            "taxa_engajamento": 68.5, "tempo_medio": "1m 42s",
            "delta_sessoes": 15.2, "delta_usuarios": 12.4,
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

    def _get_mock_daily_trends(self, period, custom_start=None, custom_end=None):
        import random
        random.seed(42)

        # Calcular dias baseado no período ou datas personalizadas
        if period == "custom" and custom_start and custom_end:
            start_date = datetime.strptime(custom_start, "%Y-%m-%d")
            end_date = datetime.strptime(custom_end, "%Y-%m-%d")
            days = (end_date - start_date).days + 1
            dates = [(start_date + timedelta(days=i)).strftime("%d/%m") for i in range(days)]
        else:
            # Mapeamento correto dos períodos do dashboard
            days = {"today": 1, "yesterday": 1, "last_7d": 7, "last_14d": 14, "last_30d": 30}.get(period, 7)
            dates = [(datetime.now() - timedelta(days=i)).strftime("%d/%m") for i in range(days-1, -1, -1)]

        # Gerar dados mock para o número correto de dias
        base_cliques = [380, 420, 395, 450, 480, 510, 565, 520, 490, 530, 560, 580, 540, 500]
        base_ctr = [2.3, 2.4, 2.35, 2.5, 2.55, 2.6, 2.75, 2.65, 2.58, 2.7, 2.8, 2.85, 2.72, 2.62]
        base_cpc = [0.30, 0.28, 0.29, 0.27, 0.26, 0.25, 0.24, 0.25, 0.26, 0.24, 0.23, 0.22, 0.24, 0.25]

        # Estender dados se necessário
        while len(base_cliques) < days:
            base_cliques.extend([random.randint(380, 600) for _ in range(7)])
            base_ctr.extend([round(random.uniform(2.2, 2.9), 2) for _ in range(7)])
            base_cpc.extend([round(random.uniform(0.22, 0.32), 2) for _ in range(7)])

        return pd.DataFrame({
            "Data": dates,
            "Cliques": base_cliques[:days],
            "CTR": base_ctr[:days],
            "CPC": base_cpc[:days],
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
                "user_engagement", "scroll_50", "primary_cta_click"
            ],
            "Contagem de Eventos": [
                "2.050 (33,19%)", "1.992 (32,25%)", "1.958 (31,70%)", "78 (1,26%)",
                "78 (1,26%)", "17 (0,28%)", "3 (0,05%)"
            ],
            "Total de Usuarios": [
                "1.968 (100%)", "1.968 (100%)", "1.958 (99,49%)", "68 (3,46%)",
                "38 (1,93%)", "14 (0,71%)", "3 (0,15%)"
            ],
            "Eventos por Usuario": ["1,04", "1,01", "1,00", "1,15", "2,05", "1,21", "1,00"]
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
    owl_img = f'<img src="data:image/png;base64,{logo_base64}" style="width:48px;height:48px;margin-bottom:12px;filter:drop-shadow(0 0 10px rgba(0,212,255,0.5));">' if logo_base64 else ''
    st.markdown(f'''
    <div style="background:rgba(2,0,36,0.85);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);border-radius:20px;padding:32px;text-align:center;border:1px solid {LIA["border"]};margin:16px 0;box-shadow:0 20px 40px rgba(0,0,0,0.4);">
        {owl_img}
        <h3 style="color:{LIA["text_light"]};font-size:18px;margin:0 0 8px 0;">{title}</h3>
        <p style="color:{LIA["text_secondary"]};font-size:14px;margin:0 0 16px 0;">{message}</p>
        <button onclick="window.location.reload()" style="background:linear-gradient(135deg,{LIA["primary"]},{LIA["secondary"]});color:{LIA["bg_dark"]};border:none;padding:10px 24px;border-radius:8px;font-size:14px;cursor:pointer;font-weight:600;box-shadow:0 8px 20px rgba(0,212,255,0.3);">
            Recarregar dados
        </button>
    </div>
    ''', unsafe_allow_html=True)

# =============================================================================
# CSS - NEON DUSK THEME (CONTRASTE PROFISSIONAL)
# =============================================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

*, *::before, *::after {{ box-sizing: border-box; }}

/* Fundo: Gradiente Neon Dusk (escuro para cyan) */
html, body, [data-testid="stAppViewContainer"], .stApp {{
    background: linear-gradient(135deg, {LIA["gradient_start"]} 0%, {LIA["gradient_mid"]} 40%, {LIA["gradient_end"]} 100%) !important;
    min-height: 100vh;
    font-family: 'Inter', -apple-system, sans-serif !important;
}}

/* Ajuste para melhor transição do gradiente */
[data-testid="stAppViewContainer"]::before {{
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: radial-gradient(ellipse at 30% 0%, rgba(0, 212, 255, 0.15) 0%, transparent 50%),
                radial-gradient(ellipse at 70% 100%, rgba(0, 212, 255, 0.1) 0%, transparent 40%);
    pointer-events: none;
    z-index: 0;
}}

[data-testid="stSidebar"], section[data-testid="stSidebar"],
button[kind="header"], [data-testid="collapsedControl"] {{
    display: none !important;
}}

.main .block-container {{
    padding: 20px !important;
    max-width: 1200px !important;
    margin: 0 auto;
    position: relative;
    z-index: 1;
}}

/* ========== CARTOES GLASSMORPHISM ESCUROS ========== */
.glass-card {{
    background: rgba(2, 0, 36, 0.75);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid {LIA["border"]};
    border-radius: 20px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4),
                0 0 60px rgba(0, 212, 255, 0.05);
    padding: 24px;
}}

.content-layer {{
    display: flex;
    flex-direction: column;
    gap: 18px;
    margin-top: 16px;
}}

/* ========== HEADER (glass escuro com glow) ========== */
.lia-header {{
    background: rgba(2, 0, 36, 0.85);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-radius: 20px;
    padding: 20px 28px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border: 1px solid {LIA["border"]};
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4),
                0 0 30px rgba(0, 212, 255, 0.1);
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
    background: linear-gradient(135deg, {LIA["primary"]} 0%, {LIA["secondary"]} 100%);
    backdrop-filter: blur(12px);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 8px 20px rgba(0, 212, 255, 0.3);
}}

.lia-logo img {{
    width: 32px;
    height: 32px;
    filter: brightness(0) invert(1);
}}

.lia-title-group {{
    display: flex;
    flex-direction: column;
}}

.lia-main-title {{
    font-size: 20px;
    font-weight: 800;
    color: {LIA["text_light"]};
    letter-spacing: -0.5px;
    margin: 0;
    line-height: 1.2;
    text-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
}}

.lia-subtitle {{
    font-size: 12px;
    color: {LIA["primary"]};
    font-weight: 500;
    margin: 0;
}}

/* ========== STATUS CARD ========== */
.status-card {{
    background: rgba(2, 0, 36, 0.8);
    border-radius: 16px;
    padding: 12px 20px;
    display: flex;
    align-items: center;
    gap: 12px;
    border: 1px solid {LIA["border"]};
    box-shadow: 0 10px 20px rgba(0,0,0,0.3);
}}

.status-owl {{
    width: 28px;
    height: 28px;
    filter: drop-shadow(0 0 8px rgba(0, 212, 255, 0.5));
}}

.status-text {{
    font-size: 13px;
    color: {LIA["text_primary"]};
    font-weight: 500;
}}

/* ========== KPI GRID & CARDS ========== */
.section-title {{
    font-size: 15px;
    font-weight: 700;
    color: {LIA["text_light"]};
    margin-bottom: 18px;
    display: flex;
    align-items: center;
    gap: 8px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

.section-icon {{
    width: 24px;
    height: 24px;
    background: linear-gradient(135deg, {LIA["primary"]} 0%, {LIA["secondary"]} 100%);
    color: {LIA["bg_dark"]};
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 800;
    box-shadow: 0 4px 12px rgba(0, 212, 255, 0.3);
}}

.kpi-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    gap: 12px;
}}

.kpi-card {{
    position: relative;
    perspective: 1000px;
    height: 150px;
    display: block;
}}

.kpi-card input {{
    position: absolute;
    opacity: 0;
    pointer-events: none;
}}

.kpi-inner {{
    position: relative;
    width: 100%;
    height: 100%;
}}

.kpi-front,
.kpi-back {{
    position: absolute;
    inset: 0;
    backface-visibility: hidden;
    background: rgba(2, 0, 36, 0.8);
    border-radius: 16px;
    padding: 16px;
    border: 1px solid {LIA["border"]};
    transition: transform 0.6s ease, background 0.2s ease, box-shadow 0.2s ease;
    cursor: pointer;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}}

.kpi-front {{
    transform: rotateY(0deg);
}}

.kpi-back {{
    transform: rotateY(180deg);
}}

.kpi-card input:checked ~ .kpi-inner .kpi-back {{
    transform: rotateY(0deg);
}}

.kpi-card input:checked ~ .kpi-inner .kpi-front {{
    transform: rotateY(-180deg);
}}

.kpi-card:hover .kpi-front,
.kpi-card:hover .kpi-back {{
    background: rgba(2, 0, 36, 0.95);
    border-color: {LIA["primary"]};
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4),
                0 0 20px rgba(0, 212, 255, 0.15);
}}

.kpi-top {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    margin-bottom: 10px;
}}

.kpi-icon {{
    font-size: 16px;
    filter: drop-shadow(0 0 6px rgba(0, 212, 255, 0.4));
}}

.kpi-label {{
    font-size: 11px;
    font-weight: 600;
    color: {LIA["text_secondary"]};
    text-transform: uppercase;
    letter-spacing: 0.3px;
    margin: 0;
}}

.kpi-value {{
    font-size: 20px;
    font-weight: 800;
    color: {LIA["text_light"]};
    margin-bottom: 6px;
    text-shadow: 0 0 20px rgba(0, 212, 255, 0.2);
}}

.kpi-delta {{
    font-size: 11px;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 2px;
}}

.kpi-back p {{
    margin: 12px 0 0 0;
    font-size: 12px;
    color: {LIA["text_secondary"]};
}}

.delta-up {{ color: {LIA["success"]}; text-shadow: 0 0 10px rgba(16, 185, 129, 0.4); }}
.delta-down {{ color: {LIA["error"]}; text-shadow: 0 0 10px rgba(239, 68, 68, 0.4); }}
.delta-neutral {{ color: {LIA["text_muted"]}; }}

/* ========== BADGES ========== */
.badge-row {{
    display: flex;
    gap: 8px;
    margin-bottom: 16px;
}}

.badge {{
    padding: 6px 12px;
    border-radius: 100px;
    font-size: 11px;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 6px;
}}

.badge-orange, .badge-cyan {{
    background: rgba(0, 212, 255, 0.15);
    color: {LIA["primary"]};
    border: 1px solid rgba(0, 212, 255, 0.3);
    box-shadow: 0 0 10px rgba(0, 212, 255, 0.1);
}}

.badge-green {{
    background: rgba(16, 185, 129, 0.15);
    color: {LIA["success"]};
    border: 1px solid rgba(16, 185, 129, 0.3);
    box-shadow: 0 0 10px rgba(16, 185, 129, 0.1);
}}

/* ========== TABELA COM HEADER GLASS ESCURO ========== */
.table-container {{
    background: rgba(2, 0, 36, 0.8);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-radius: 20px;
    overflow: hidden;
    border: 1px solid {LIA["border"]};
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
    margin-bottom: 12px;
}}

.table-header {{
    background: rgba(0, 212, 255, 0.1);
    padding: 14px 18px;
    border-bottom: 1px solid {LIA["border"]};
}}

.table-header-title {{
    font-size: 14px;
    font-weight: 600;
    color: {LIA["text_light"]};
}}

.stDataFrame {{
    background: transparent !important;
}}

[data-testid="stDataFrame"] > div {{
    background: transparent !important;
}}

.lia-html-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
    text-align: left;
}}

.lia-html-table :is(th, td) {{
    padding: 12px 16px;
    white-space: nowrap;
    vertical-align: middle;
}}

.lia-html-table thead th {{
    background: rgba(0, 212, 255, 0.12);
    border-bottom: 1px solid {LIA["border"]};
    color: {LIA["primary"]};
    font-weight: 600;
    text-transform: capitalize;
    letter-spacing: 0.02em;
}}

.lia-html-table tbody td {{
    border-bottom: 1px solid rgba(0, 212, 255, 0.1);
    color: {LIA["text_primary"]};
    opacity: 0.78;
    transition: opacity 0.3s ease, background 0.3s ease;
}}

.lia-html-table tbody tr:nth-child(odd) {{
    background: rgba(1, 13, 37, 0.35);
}}

.lia-html-table tbody tr:hover td {{
    opacity: 1;
}}

.lia-html-table tbody tr:last-child td {{
    border-bottom: 0;
}}

.lia-html-table tbody td:nth-child(n + 2) {{
    text-align: right;
    font-variant-numeric: tabular-nums;
}}

.event-tooltip-wrapper {{
    position: relative;
    display: inline-flex;
    align-items: center;
    gap: 6px;
}}

.event-btn {{
    background: transparent;
    border: none;
    padding: 0;
    font-size: 14px;
    font-weight: 600;
    color: {LIA["text_light"]};
    cursor: default;
    display: inline-flex;
    align-items: center;
    gap: 6px;
}}

.tooltip-icon {{
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: linear-gradient(135deg, {LIA["primary"]} 0%, {LIA["secondary"]} 100%);
    color: {LIA["bg_dark"]};
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 700;
    box-shadow: 0 0 8px rgba(0, 212, 255, 0.4);
}}

.tooltip-popup {{
    position: absolute;
    left: 0;
    bottom: calc(100% + 8px);
    background: rgba(2, 0, 36, 0.95);
    color: {LIA["text_light"]};
    padding: 8px 10px;
    border-radius: 8px;
    font-size: 12px;
    line-height: 1.4;
    min-width: 160px;
    max-width: 240px;
    opacity: 0;
    pointer-events: none;
    transform: translateY(4px);
    transition: opacity 0.2s ease, transform 0.2s ease;
    z-index: 10;
    border: 1px solid {LIA["border"]};
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}}

.event-tooltip-wrapper:hover .tooltip-popup,
.event-tooltip-wrapper:focus-within .tooltip-popup {{
    opacity: 1;
    pointer-events: auto;
    transform: translateY(0);
}}

/* ========== CARD DE ESCOPO ========== */
.scope-card {{
    background: rgba(2, 0, 36, 0.8);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-radius: 20px;
    padding: 16px 20px;
    display: flex;
    align-items: center;
    gap: 12px;
    border: 1px solid {LIA["border"]};
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
    margin-bottom: 12px;
}}

.scope-text {{
    font-size: 13px;
    color: {LIA["text_primary"]};
}}

/* ========== GRAFICOS EM CARDS ========== */
.chart-card {{
    background: rgba(2, 0, 36, 0.8);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-radius: 20px;
    padding: 18px;
    border: 1px solid {LIA["border"]};
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
    margin-bottom: 12px;
}}

.trend-toggle [data-baseweb="tab-list"] {{
    gap: 8px;
    background: rgba(0, 212, 255, 0.05);
    border-radius: 12px;
    padding: 4px;
}}

.trend-toggle [data-baseweb="tab"] {{
    background: transparent;
    border-radius: 8px;
    padding: 6px 14px;
    color: {LIA["text_secondary"]};
    font-size: 13px;
    font-weight: 600;
}}

.trend-toggle [aria-selected="true"] {{
    background: linear-gradient(135deg, {LIA["primary"]} 0%, {LIA["secondary"]} 100%);
    color: {LIA["bg_dark"]};
    box-shadow: 0 8px 16px rgba(0, 212, 255, 0.3);
}}

.js-plotly-plot .plotly .modebar {{ display: none !important; }}

/* ========== FILTROS ========== */
.filter-card {{
    background: rgba(2, 0, 36, 0.8);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid {LIA["border"]};
    border-radius: 20px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
    padding: 18px 18px 10px 18px;
}}

.stSelectbox > div > div {{
    background: rgba(2, 0, 36, 0.9) !important;
    border: 1px solid {LIA["border"]} !important;
    border-radius: 12px !important;
    box-shadow: 0 10px 24px rgba(0, 0, 0, 0.3);
    color: {LIA["text_light"]} !important;
}}

.stSelectbox > div > div:hover {{
    border-color: {LIA["primary"]} !important;
    box-shadow: 0 0 15px rgba(0, 212, 255, 0.2);
}}

.stSelectbox label {{
    color: {LIA["text_secondary"]} !important;
    font-size: 12px !important;
}}

.stSelectbox [data-baseweb="select"] span {{
    color: {LIA["text_light"]} !important;
}}

/* ========== AGENTE DE IA ========== */
.ai-agent-card {{
    background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(14, 165, 233, 0.1) 100%);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 2px solid {LIA["primary"]};
    border-radius: 20px;
    padding: 24px;
    margin-bottom: 16px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4),
                0 0 40px rgba(0, 212, 255, 0.15);
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
    background: linear-gradient(135deg, {LIA["primary"]} 0%, {LIA["secondary"]} 100%);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    box-shadow: 0 8px 20px rgba(0, 212, 255, 0.4);
}}

.ai-agent-title {{
    font-size: 16px;
    font-weight: 700;
    color: {LIA["text_light"]};
    text-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
}}

.ai-agent-subtitle {{
    font-size: 12px;
    color: {LIA["primary"]};
}}

.ai-agent-content {{
    background: rgba(2, 0, 36, 0.6);
    border-radius: 12px;
    padding: 16px;
    font-size: 14px;
    line-height: 1.6;
    color: {LIA["text_primary"]};
    border: 1px solid {LIA["border"]};
}}

.ai-agent-content h1, .ai-agent-content h2, .ai-agent-content h3 {{
    font-size: 14px;
    font-weight: 700;
    margin: 12px 0 8px 0;
    color: {LIA["primary"]};
}}

.ai-agent-content p {{
    margin: 8px 0;
}}

.ai-agent-content ul, .ai-agent-content ol {{
    margin: 8px 0;
    padding-left: 20px;
    color: {LIA["text_primary"]};
}}

/* ========== FOOTER ========== */
.footer {{
    text-align: center;
    padding: 8px 0 0 0;
    color: {LIA["text_secondary"]};
    font-size: 12px;
    border-top: none;
    margin-top: 8px;
}}

/* ========== STREAMLIT GLOBAL OVERRIDES ========== */
.stButton > button {{
    background: linear-gradient(135deg, {LIA["primary"]} 0%, {LIA["secondary"]} 100%) !important;
    color: {LIA["bg_dark"]} !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 10px 20px !important;
    font-weight: 600 !important;
    box-shadow: 0 8px 20px rgba(0, 212, 255, 0.3) !important;
    transition: all 0.3s ease !important;
}}

.stButton > button:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 12px 28px rgba(0, 212, 255, 0.4) !important;
}}

/* Date input styling */
.stDateInput > div > div {{
    background: rgba(2, 0, 36, 0.9) !important;
    border: 1px solid {LIA["border"]} !important;
    border-radius: 12px !important;
    color: {LIA["text_light"]} !important;
}}

.stDateInput label {{
    color: {LIA["text_secondary"]} !important;
}}

/* Metric styling */
[data-testid="stMetricValue"] {{
    color: {LIA["text_light"]} !important;
}}

[data-testid="stMetricDelta"] {{
    color: {LIA["success"]} !important;
}}

/* Text elements */
.stMarkdown p, .stMarkdown li {{
    color: {LIA["text_primary"]};
}}

/* Expander styling */
.streamlit-expanderHeader {{
    background: rgba(2, 0, 36, 0.8) !important;
    border: 1px solid {LIA["border"]} !important;
    border-radius: 12px !important;
    color: {LIA["text_light"]} !important;
}}

/* Scrollbar styling */
::-webkit-scrollbar {{
    width: 8px;
    height: 8px;
}}

::-webkit-scrollbar-track {{
    background: rgba(2, 0, 36, 0.5);
    border-radius: 4px;
}}

::-webkit-scrollbar-thumb {{
    background: {LIA["primary"]};
    border-radius: 4px;
}}

::-webkit-scrollbar-thumb:hover {{
    background: {LIA["primary_dark"]};
}}

/* Link styling */
a {{
    color: {LIA["primary"]} !important;
    text-decoration: none;
}}

a:hover {{
    text-decoration: underline;
    text-shadow: 0 0 10px rgba(0, 212, 255, 0.4);
}}

/* Loading spinner */
.stSpinner > div {{
    border-top-color: {LIA["primary"]} !important;
}}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# BARRA SUPERIOR (HEADER)
# =============================================================================
logo_img = f'<img src="data:image/png;base64,{logo_base64}">' if logo_base64 else '🦉'

st.markdown(f'''
<div class="lia-header">
    <div class="lia-header-left">
        <div class="lia-logo">{logo_img}</div>
        <div class="lia-title-group">
            <h1 class="lia-main-title">LIA Dashboard</h1>
            <p class="lia-subtitle">Inteligência em Performance</p>
        </div>
    </div>
</div>
''', unsafe_allow_html=True)

if "show_integration_settings" not in st.session_state:
    st.session_state.show_integration_settings = False

if st.button("⚙️ Configurações de integração", key="toggle_integration_settings", use_container_width=True):
    st.session_state.show_integration_settings = not st.session_state.show_integration_settings

# =============================================================================
# FILTROS E CONTROLES
# =============================================================================
st.markdown('<div class="content-layer">', unsafe_allow_html=True)

filter_cols = st.columns([2, 2, 1])

with filter_cols[0]:
    st.markdown('<div class="filter-card">', unsafe_allow_html=True)
    campanha = st.selectbox(
        "Campanha",
        ["Ciclo 2", "Ciclo 1", "Todas"],
        index=0
    )
    st.markdown('</div>', unsafe_allow_html=True)

with filter_cols[1]:
    st.markdown('<div class="filter-card">', unsafe_allow_html=True)
    periodos = {
        "Hoje": "today",
        "Ontem": "yesterday",
        "Últimos 7 dias": "last_7d",
        "Últimos 14 dias": "last_14d",
        "Últimos 30 dias": "last_30d",
        "Personalizado": "custom"
    }
    selected_label = st.selectbox("Período", list(periodos.keys()), index=2)
    selected_period = periodos[selected_label]
    st.markdown('</div>', unsafe_allow_html=True)

# Datas personalizadas (se selecionado)
custom_start_str, custom_end_str = None, None
if selected_period == "custom":
    with filter_cols[2]:
        st.markdown('<div class="filter-card">', unsafe_allow_html=True)
        d = st.date_input("Intervalo", [datetime.now() - timedelta(days=7), datetime.now()])
        if len(d) == 2:
            custom_start_str = d[0].strftime("%Y-%m-%d")
            custom_end_str = d[1].strftime("%Y-%m-%d")
        st.markdown('</div>', unsafe_allow_html=True)

# Mapear filtro de campanha para as APIs
# Meta usa o nome da campanha como aparece no dropdown (ex: "Ciclo 2" match "LIA | Ciclo 2 | ...")
meta_campaign_filter = None if campanha == "Todas" else campanha

# Mapear nome da campanha para filtro de UTM (GA4)
# Os UTMs reais usam "ciclo1" e "ciclo2" (sem espaço), ex: lia_ciclo2_conversao
utm_filter_map = {
    "Ciclo 2": "ciclo2",
    "Ciclo 1": "ciclo1",
    "Todas": None
}
ga4_campaign_filter = utm_filter_map.get(campanha, None)

# Feedback visual do filtro de campanha selecionado
if campanha == "Todas":
    st.markdown('''
    <div class="scope-card">
        <span style="font-size:18px;">i</span>
        <span class="scope-text">Exibindo dados de: <strong>Todos os ciclos</strong></span>
    </div>
    ''', unsafe_allow_html=True)
else:
    st.markdown(f'''
    <div class="scope-card">
        <span style="font-size:18px;">i</span>
        <span class="scope-text">Filtrando por campanha: <strong>{campanha}</strong></span>
    </div>
    ''', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# CARREGAR DADOS (com tratamento de erro)
# -----------------------------------------------------------------------------
cycle_status = {"insights": ["Processando..."], "phase": "Carregando", "is_learning": True}
try:
    with st.spinner("Sincronizando dados..."):
        meta_data = data_provider.get_meta_metrics(
            period=selected_period,
            campaign_filter=meta_campaign_filter,
            custom_start=custom_start_str,
            custom_end=custom_end_str,
        )
        ga4_data = data_provider.get_ga4_metrics(
            period=selected_period,
            custom_start=custom_start_str,
            custom_end=custom_end_str,
            campaign_filter=ga4_campaign_filter,
        )
        creative_data = data_provider.get_creative_data(
            period=selected_period,
            campaign_filter=meta_campaign_filter,
            custom_start=custom_start_str,
            custom_end=custom_end_str,
        )
        trends_data = data_provider.get_daily_trends(
            period=selected_period,
            custom_start=custom_start_str,
            custom_end=custom_end_str,
            campaign_filter=meta_campaign_filter,
        )
        cycle_status = data_provider.get_cycle_status(selected_period, meta_data, creative_data)
except Exception as e:
    import streamlit as st
    st.error(f"Erro ao carregar dados do módulo Premium: {e}")
    meta_data = {
        "investimento": 0, "impressoes": 0, "alcance": 0, "frequencia": 0,
        "cliques_link": 0, "ctr_link": 0, "cpc_link": 0, "cpm": 0,
        "delta_investimento": 0, "delta_impressoes": 0, "delta_alcance": 0,
        "delta_frequencia": 0, "delta_cliques": 0, "delta_ctr": 0,
        "delta_cpc": 0, "delta_cpm": 0, "_data_source": "error"
    }
    ga4_data = {
        "sessoes": 0, "usuarios": 0, "pageviews": 0,
        "taxa_engajamento": 0, "tempo_medio": "0m 0s",
        "delta_sessoes": 0, "delta_usuarios": 0, "delta_pageviews": 0,
        "delta_engajamento": 0, "_data_source": "error"
    }
    creative_data = {}
    trends_data = []

# -----------------------------------------------------------------------------
# STATUS DO CICLO (COM CORUJA)
# -----------------------------------------------------------------------------
try:
    owl_img = f'<img src="data:image/png;base64,{logo_base64}" class="status-owl">' if logo_base64 else ''
except Exception as e:
    import streamlit as st
    st.error(f"Erro interno no módulo Premium: {e}")
    owl_img = ''
insights_text = ". ".join(cycle_status["insights"]) + "."
campaign_objective_map = {
    "Ciclo 2": "Conversão na landing page",
    "Ciclo 1": "Reconhecimento de marca",
    "Todas": "Múltiplos objetivos",
}
campaign_objective = campaign_objective_map.get(campanha, "Conversão na landing page")
status_line = f"{insights_text} Objetivo da campanha: {campaign_objective}. {cycle_status['phase']}."

st.markdown(f'''
<div class="status-card">
    {owl_img}
    <div class="status-text">{status_line}</div>
</div>
''', unsafe_allow_html=True)

if st.session_state.show_integration_settings:
    # Indicador de fonte de dados e diagnóstico de conexão
    data_source = meta_data.get("_data_source", "unknown")
    if data_source == "real":
        st.success(f"✅ Conectado ao Meta Ads - Filtro: {meta_data.get('_filter_applied', 'Nenhum')}")
    elif data_source == "real_no_filter":
        st.warning(f"⚠️ Meta Ads: Sem dados para '{meta_data.get('_requested_filter')}'. Mostrando total da conta.")
        if "_available_campaigns" in meta_data:
            st.info(f"Campanhas encontradas: {', '.join(meta_data['_available_campaigns'])}")
    else:
        st.info("💡 Usando dados de demonstração. Verifique as credenciais no Streamlit Secrets.")

# =============================================================================
# SEÇÃO DE ANÁLISE COM IA (PRIMEIRA DOBRA)
# =============================================================================
st.markdown('<div class="section-title"><div class="section-icon">🤖</div> Análise com IA</div>', unsafe_allow_html=True)

# Verificar se a API key está disponível
if Config.validate_openai_credentials():
    # Determinar o ciclo baseado na campanha selecionada
    cycle = campanha if campanha in ["Ciclo 1", "Ciclo 2"] else "Todos os Ciclos"

    # Botão para gerar análise
    if st.button("🔮 Gerar Análise com IA", key="btn_ai_analysis", use_container_width=True):
        with st.spinner("Analisando dados com IA..."):
            try:
                # Inicializar o agente de IA
                ai_agent = AIAgent(api_key=Config.get_openai_api_key())

                # Preparar dados para análise
                analysis_meta_data = {
                    "investimento": meta_data.get("investimento", 0),
                    "impressoes": meta_data.get("impressoes", 0),
                    "alcance": meta_data.get("alcance", 0),
                    "frequencia": meta_data.get("frequencia", 0),
                    "cliques_link": meta_data.get("cliques_link", 0),
                    "ctr_link": meta_data.get("ctr_link", 0),
                    "cpc_link": meta_data.get("cpc_link", 0),
                    "cpm": meta_data.get("cpm", 0),
                    "delta_ctr": meta_data.get("delta_ctr", 0),
                    "delta_cpc": meta_data.get("delta_cpc", 0),
                    "delta_cliques": meta_data.get("delta_cliques", 0),
                }

                analysis_ga4_data = {
                    "sessoes": ga4_data.get("sessoes", 0),
                    "usuarios": ga4_data.get("usuarios", 0),
                    "pageviews": ga4_data.get("pageviews", 0),
                    "taxa_engajamento": ga4_data.get("taxa_engajamento", 0),
                    "tempo_medio": ga4_data.get("tempo_medio", "N/A"),
                }

                # Gerar análise
                analysis = ai_agent.analyze(
                    meta_data=analysis_meta_data,
                    ga4_data=analysis_ga4_data,
                    creative_data=creative_data,
                    source_data=data_provider.get_source_medium(period=selected_period, custom_start=custom_start_str, custom_end=custom_end_str, campaign_filter=ga4_campaign_filter),
                    events_data=data_provider.get_events_data(period=selected_period, custom_start=custom_start_str, custom_end=custom_end_str, campaign_filter=ga4_campaign_filter),
                    period=selected_period,
                    cycle=cycle
                )

                # Salvar análise no session state
                st.session_state['ai_analysis'] = analysis
                st.session_state['ai_analysis_cycle'] = cycle

            except Exception as e:
                logger.error(f"Erro ao gerar análise de IA: {e}")
                st.error(f"Erro ao gerar análise: {str(e)}")

    # Exibir análise salva se existir
    if 'ai_analysis' in st.session_state:
        analysis_cycle = st.session_state.get('ai_analysis_cycle', 'Ciclo 2')
        st.markdown(f'''
        <div class="ai-agent-card">
            <div class="ai-agent-header">
                <div class="ai-agent-icon">🦉</div>
                <div>
                    <div class="ai-agent-title">LIA - Análise Inteligente</div>
                    <div class="ai-agent-subtitle">Análise do {analysis_cycle} • Powered by GPT-4</div>
                </div>
            </div>
            <div class="ai-agent-content">
                {st.session_state['ai_analysis']}
            </div>
        </div>
        ''', unsafe_allow_html=True)
else:
    st.markdown(f'''
    <div class="glass-card" style="padding: 20px; text-align: center;">
        <p style="color: {LIA["text_muted"]}; margin: 0;">
            🔒 Configure a chave da API OpenAI no Streamlit Secrets para habilitar a análise com IA.
        </p>
    </div>
    ''', unsafe_allow_html=True)

# =============================================================================
# CAMADA DE CONTEUDO CENTRAL
# =============================================================================

# -----------------------------------------------------------------------------
# META ADS (KPIs)
# -----------------------------------------------------------------------------
def build_kpi_card(icon, label, value, delta, suffix="%", invert=False, precision=1):
    delta_class = "delta-neutral"
    delta_text = "stable"

    if delta is not None and delta != 0:
        is_positive = delta > 0
        # Se invert=True, positivo é ruim (ex: CPC subindo)
        is_good = not is_positive if invert else is_positive
        delta_class = "delta-up" if is_good else "delta-down"
        icon_delta = "↑" if is_positive else "↓"
        delta_text = f"{icon_delta} {abs(delta):.{precision}f}{suffix}"

    card_id = "kpi-" + "".join(
        char.lower() if char.isalnum() else "-" for char in str(label)
    ).strip("-")

    return textwrap.dedent(f"""
    <label class="kpi-card" id="{card_id}">
        <input type="checkbox" />
        <div class="kpi-inner">
            <div class="kpi-front">
                <div class="kpi-top">
                    <div style="display:flex;align-items:center;gap:8px;">
                        <div class="kpi-icon">{icon}</div>
                        <div class="kpi-label">{label}</div>
                    </div>
                    <span style="font-size:16px;color:{LIA["text_muted"]};">⋯</span>
                </div>
                <div class="kpi-value">{value}</div>
                <div class="kpi-delta {delta_class}">{delta_text}</div>
            </div>
            <div class="kpi-back">
                <div class="kpi-top">
                    <div class="kpi-label">{label}</div>
                    <span style="font-size:14px;color:{LIA["text_muted"]};">✕</span>
                </div>
                <h3 style="margin:0;font-size:18px;color:{LIA["text_dark"]};">{value}</h3>
                <p>Variação: <span class="{delta_class}">{delta_text}</span></p>
            </div>
        </div>
    </label>
    """).strip()

kpi_cards = [
    {"icon": "💰", "label": "Investimento", "value": f"$ {meta_data.get('investimento', 0):,.2f}", "delta": meta_data.get('delta_investimento', 0), "suffix": "%"},
    {"icon": "👀", "label": "Impressoes", "value": f"{meta_data.get('impressoes', 0):,.0f}", "delta": meta_data.get('delta_impressoes', 0), "suffix": "%"},
    {"icon": "📡", "label": "Alcance", "value": f"{meta_data.get('alcance', 0):,.0f}", "delta": meta_data.get('delta_alcance', 0), "suffix": "%"},
    {"icon": "🔁", "label": "Frequência", "value": f"{meta_data.get('frequencia', 0):.2f}", "delta": meta_data.get('delta_frequencia', 0), "suffix": "", "precision": 2},
    {"icon": "🖱️", "label": "Cliques Link", "value": f"{meta_data.get('cliques_link', 0):,.0f}", "delta": meta_data.get('delta_cliques', 0), "suffix": "%"},
    {"icon": "🎯", "label": "CTR Link", "value": f"{meta_data.get('ctr_link', 0):.2f}%", "delta": meta_data.get('delta_ctr', 0), "suffix": "pp", "precision": 2},
    {"icon": "💡", "label": "CPC Link", "value": f"$ {meta_data.get('cpc_link', 0):.2f}", "delta": meta_data.get('delta_cpc', 0), "suffix": "%", "invert": True},
    {"icon": "📊", "label": "CPM", "value": f"$ {meta_data.get('cpm', 0):.2f}", "delta": meta_data.get('delta_cpm', 0), "suffix": "%", "invert": True},
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
  <div class="section-title"><div class="section-icon">$</div> KPIs Principais (Meta Ads)</div>
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
        best_ctr_name = str(creative_data.loc[best_ctr_idx, "Criativo"])[:22]

        st.markdown(f'''
        <div class="badge-row">
            <div class="badge badge-orange">Criativo campeão: {best_ctr_name}... ({creative_data.loc[best_ctr_idx, "CTR"]:.2f}% CTR)</div>
        </div>
        ''', unsafe_allow_html=True)

        st.markdown('<div class="table-container">', unsafe_allow_html=True)
        st.markdown('<div class="table-header"><span class="table-header-title">Performance por Criativo</span></div>', unsafe_allow_html=True)

        # Mostrar todos os criativos, ordenados por CTR (campeão primeiro)
        creative_display = creative_data.sort_values('CTR', ascending=False)
        creative_formatters = {
            "Investimento": lambda value: f"$ {value:,.2f}",
            "Impressoes": lambda value: f"{value:,.0f}",
            "Cliques": lambda value: f"{value:,.0f}",
            "CTR": lambda value: f"{value:.2f}%",
            "CPC": lambda value: f"$ {value:,.2f}",
            "CPM": lambda value: f"$ {value:,.2f}",
        }
        columns = list(creative_display.columns)
        header_cells = "".join(f"<th>{html.escape(str(col))}</th>" for col in columns)
        body_rows = []
        for _, row in creative_display.iterrows():
            row_cells = []
            for col in columns:
                value = row[col]
                if col in creative_formatters and pd.notna(value):
                    formatted = creative_formatters[col](value)
                else:
                    formatted = "" if pd.isna(value) else str(value)
                row_cells.append(f"<td>{html.escape(formatted)}</td>")
            body_rows.append("<tr>" + "".join(row_cells) + "</tr>")
        creative_table_html = f"""<table class="lia-html-table"><thead><tr>{header_cells}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"""
        st.markdown(creative_table_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Erro ao renderizar tabela de criativos: {e}")
        render_error_card("Dados de criativos indisponiveis", "Estamos processando as informacoes de criativos.")
else:
    st.markdown(f'''
    <div style="background:rgba(2,0,36,0.8);border-radius:16px;padding:32px;text-align:center;border:1px dashed {LIA["border"]};backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);">
        <p style="color:{LIA["text_secondary"]};margin:0;">Nenhum dado de criativo encontrado no periodo selecionado.</p>
    </div>
    ''', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# ESCOPO DO CICLO
# -----------------------------------------------------------------------------
st.markdown(f'''
<div class="scope-card">
    <span style="font-size:18px;color:{LIA["primary"]};">i</span>
    <span class="scope-text"><strong>Ciclo 2 analisa midia e conversoes na landing page.</strong> Acompanhamento completo do funil de conversao.</span>
</div>
''', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TENDENCIA TEMPORAL
# -----------------------------------------------------------------------------
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title"><div class="section-icon">~</div> Tendencia Temporal</div>', unsafe_allow_html=True)

if isinstance(trends_data, pd.DataFrame) and not trends_data.empty and "Data" in trends_data.columns:
    try:
        st.markdown('<div class="chart-card trend-toggle">', unsafe_allow_html=True)
        st.markdown('<div class="section-title"><div class="section-icon">~</div> Tendência de Cliques</div>', unsafe_allow_html=True)

        trend_tabs = st.tabs(["Diário", "Semanal"])
        trend_daily = trends_data.copy()
        trend_daily["__date"] = pd.to_datetime(trend_daily["Data"], dayfirst=True, errors="coerce")
        current_year = datetime.now().year
        trend_daily["__date"] = trend_daily["__date"].apply(
            lambda value: value.replace(year=current_year) if pd.notna(value) else value
        )

        with trend_tabs[0]:
            fig_daily = go.Figure()
            fig_daily.add_trace(go.Scatter(
                x=trend_daily["Data"],
                y=trend_daily["Cliques"],
                mode="lines",
                line=dict(color=LIA["primary"], width=3, shape="spline"),
                fill="tozeroy",
                fillcolor="rgba(0,212,255,0.2)"
            ))
            fig_daily.update_layout(
                height=260,
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False, tickfont=dict(size=11, color=LIA["text_secondary"]), tickcolor=LIA["text_secondary"]),
                yaxis=dict(showgrid=True, gridcolor="rgba(0,212,255,0.1)", tickfont=dict(size=11, color=LIA["text_secondary"])),
                showlegend=False
            )
            st.plotly_chart(fig_daily, use_container_width=True)

        with trend_tabs[1]:
            weekly = trend_daily.dropna(subset=["__date"]).set_index("__date").resample("W-MON")["Cliques"].sum().reset_index()
            weekly["Label"] = weekly["__date"].dt.strftime("Sem %d/%m")
            if weekly.empty:
                st.markdown(f'''
                <div style="background:rgba(2,0,36,0.8);border-radius:16px;padding:24px;text-align:center;border:1px dashed {LIA["border"]};">
                    <p style="color:{LIA["text_secondary"]};margin:0;">Sem dados suficientes para consolidar as semanas.</p>
                </div>
                ''', unsafe_allow_html=True)
            else:
                fig_weekly = go.Figure()
                fig_weekly.add_trace(go.Scatter(
                    x=weekly["Label"],
                    y=weekly["Cliques"],
                    mode="lines",
                    line=dict(color=LIA["secondary"], width=3, shape="spline"),
                    fill="tozeroy",
                    fillcolor="rgba(14,165,233,0.2)"
                ))
                fig_weekly.update_layout(
                    height=260,
                    margin=dict(l=10, r=10, t=10, b=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=False, tickfont=dict(size=11, color=LIA["text_secondary"])),
                    yaxis=dict(showgrid=True, gridcolor="rgba(0,212,255,0.1)", tickfont=dict(size=11, color=LIA["text_secondary"])),
                    showlegend=False
                )
                st.plotly_chart(fig_weekly, use_container_width=True)

        st.markdown('</div>', unsafe_allow_html=True)

        chart_cols = st.columns(3)

        with chart_cols[0]:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(
                x=trends_data["Data"],
                y=trends_data["Cliques"],
                mode="lines+markers",
                line=dict(color=LIA["primary"], width=2, shape='spline'),
                marker=dict(size=6, color=LIA["primary"]),
                fill="tozeroy",
                fillcolor="rgba(0,212,255,0.15)"
            ))
            fig1.update_layout(
                title=dict(text="Cliques/Dia", font=dict(size=14, color=LIA["text_light"], family="Inter")),
                height=220, margin=dict(l=10, r=10, t=40, b=30),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False, tickfont=dict(size=11, color=LIA["text_secondary"]), showline=True, linecolor="rgba(0,212,255,0.2)"),
                yaxis=dict(showgrid=True, gridcolor="rgba(0,212,255,0.1)", tickfont=dict(size=11, color=LIA["text_secondary"]), showline=True, linecolor="rgba(0,212,255,0.2)"),
                showlegend=False
            )
            st.plotly_chart(fig1, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with chart_cols[1]:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=trends_data["Data"],
                y=trends_data["CTR"],
                mode="lines+markers",
                line=dict(color=LIA["secondary"], width=2, shape='spline'),
                marker=dict(size=6, color=LIA["secondary"]),
                fill="tozeroy",
                fillcolor="rgba(14,165,233,0.15)"
            ))
            fig2.update_layout(
                title=dict(text="CTR/Dia (%)", font=dict(size=14, color=LIA["text_light"], family="Inter")),
                height=220, margin=dict(l=10, r=10, t=40, b=30),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False, tickfont=dict(size=11, color=LIA["text_secondary"]), showline=True, linecolor="rgba(0,212,255,0.2)"),
                yaxis=dict(showgrid=True, gridcolor="rgba(0,212,255,0.1)", tickfont=dict(size=11, color=LIA["text_secondary"]), showline=True, linecolor="rgba(0,212,255,0.2)"),
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
                marker=dict(size=10, color=LIA["success"], line=dict(width=2, color=LIA["bg_dark"])),
                fill="tozeroy", fillcolor="rgba(16,185,129,0.2)"
            ))
            fig3.update_layout(
                title=dict(text="CPC/Dia ($)", font=dict(size=14, color=LIA["text_light"], family="Inter")),
                height=220, margin=dict(l=10, r=10, t=40, b=30),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False, tickfont=dict(size=11, color=LIA["text_secondary"]), showline=True, linecolor="rgba(0,212,255,0.2)"),
                yaxis=dict(showgrid=True, gridcolor="rgba(0,212,255,0.1)", tickfont=dict(size=11, color=LIA["text_secondary"]), showline=True, linecolor="rgba(0,212,255,0.2)"),
                showlegend=False
            )
            st.plotly_chart(fig3, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Erro ao renderizar graficos: {e}")
        render_error_card("Graficos indisponiveis", "Estamos processando os dados de tendencia.")
else:
    st.markdown(f'''
    <div style="background:rgba(2,0,36,0.8);border-radius:16px;padding:32px;text-align:center;border:1px dashed {LIA["border"]};backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);">
        <p style="color:{LIA["text_secondary"]};margin:0;">Sem dados de tendência temporal para o período e campanha selecionados.</p>
    </div>
    ''', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# FUNIL DE CONVERSÃO SIMPLES (Impressões -> Cliques -> Loja -> Instalações)
# -----------------------------------------------------------------------------
cols = st.columns([3, 2])

with cols[0]:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title"><div class="section-icon">~</div> Tendência de Cliques e CTR</div>', unsafe_allow_html=True)
    if isinstance(trends_data, pd.DataFrame) and not trends_data.empty and "Data" in trends_data.columns:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=trends_data["Data"], y=trends_data["Cliques"], name="Cliques", mode="lines+markers", line=dict(color=LIA["primary"], width=3, shape='spline'), marker=dict(size=8, color=LIA["primary"]), fill="tozeroy", fillcolor="rgba(0,212,255,0.15)"))
        fig.add_trace(go.Scatter(x=trends_data["Data"], y=trends_data["CTR"], name="CTR %", yaxis="y2", mode="lines+markers", line=dict(color=LIA["success"], width=3, shape='spline'), marker=dict(size=8, color=LIA["success"])))
        fig.update_layout(
            yaxis2=dict(overlaying="y", side="right", range=[0, trends_data["CTR"].max() * 1.2] if trends_data["CTR"].max() > 0 else [0, 5], tickfont=dict(color=LIA["text_secondary"]), gridcolor="rgba(0,212,255,0.1)"),
            yaxis=dict(tickfont=dict(color=LIA["text_secondary"]), gridcolor="rgba(0,212,255,0.1)"),
            xaxis=dict(tickfont=dict(color=LIA["text_secondary"])),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color=LIA["text_light"])),
            height=350, margin=dict(l=0, r=0, t=30, b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown(f'''
        <div style="background:rgba(2,0,36,0.8);border-radius:16px;padding:32px;text-align:center;border:1px dashed {LIA["border"]};">
            <p style="color:{LIA["text_secondary"]};margin:0;">Sem dados de tendência para o período selecionado.</p>
        </div>
        ''', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with cols[1]:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title"><div class="section-icon">V</div> Funil de Conversão</div>', unsafe_allow_html=True)

    # Buscar dados de eventos para o funil
    events_data_for_funnel = data_provider.get_events_data(period=selected_period, custom_start=custom_start_str, custom_end=custom_end_str, campaign_filter=ga4_campaign_filter)
    cta_count = 0
    if isinstance(events_data_for_funnel, pd.DataFrame) and not events_data_for_funnel.empty:
        cta_row = events_data_for_funnel[events_data_for_funnel['Nome do Evento'] == 'primary_cta_click']
        if not cta_row.empty:
            try:
                raw_val = cta_row.iloc[0]['Contagem de Eventos']
                if isinstance(raw_val, (int, float)):
                    cta_count = int(raw_val)
                else:
                    raw_str = str(raw_val)
                    num_part = raw_str.split('(')[0].strip().split()[0] if '(' in raw_str else raw_str.split()[0]
                    cta_count = int(num_part.replace('.', '').replace(',', ''))
            except (ValueError, IndexError, TypeError) as e:
                logger.warning(f"Erro ao parsear cta_count: {e}")
                cta_count = 0

    instalacoes = int(meta_data.get("instalacoes_sdk", 0) or 0)
    funnel_labels = ["Impressões", "Cliques no link", "Cliques na loja", "Instalações (SDK Meta)"]
    funnel_values = [
        int(meta_data.get('impressoes', 0) or 0),
        int(meta_data.get('cliques_link', 0) or 0),
        int(cta_count or 0),
        int(instalacoes or 0)
    ]

    funnel_df = pd.DataFrame({"Etapa": funnel_labels, "Valor": funnel_values})
    fig_funnel = go.Figure(go.Funnel(
        y=funnel_df['Etapa'],
        x=funnel_df['Valor'],
        textposition="inside",
        textinfo="value+percent initial",
        marker=dict(
            color=[LIA["primary"], LIA["secondary"], LIA["accent"], LIA["success"]],
            line=dict(width=2, color=LIA["bg_dark"])
        ),
        textfont=dict(color=LIA["bg_dark"], size=12, family="Inter")
    ))
    fig_funnel.update_layout(
        height=350,
        margin=dict(l=40, r=40, t=40, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=LIA["text_light"])
    )
    st.plotly_chart(fig_funnel, use_container_width=True)
    st.caption("**Cliques na loja** = evento GA4 `primary_cta_click` | **Instalações** = eventos do SDK da Meta")
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
elif ga4_source == "partial":
    st.warning(f"⚠️ Dados parciais do GA4 (pageviews/usuarios sem sessoes) - Filtro: {ga4_filter if ga4_filter else 'Todas as campanhas'}. Verifique se o gtag.js esta configurado corretamente.")
elif ga4_source == "no_data":
    st.warning(f"⚠️ GA4 conectado, mas sem dados para campanha '{ga4_filter}'. Aguarde as UTMs serem processadas (ate 24-48h).")
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
        source_data = data_provider.get_source_medium(period=selected_period, custom_start=custom_start_str, custom_end=custom_end_str, campaign_filter=ga4_campaign_filter)
        if len(source_data) > 0 and "Origem / Midia" in source_data.columns:
            source_data = source_data[source_data["Origem / Midia"].str.contains("paid", case=False, na=False)]
        if len(source_data) > 0:
            st.markdown('<div class="table-container">', unsafe_allow_html=True)
            st.markdown('<div class="table-header"><span class="table-header-title">Origem/Midia (foco em paid social)</span></div>', unsafe_allow_html=True)

            source_html = '<table class="lia-html-table"><thead><tr>'
            for col in source_data.columns:
                source_html += f'<th>{col}</th>'
            source_html += '</tr></thead><tbody>'

            for _, row in source_data.iterrows():
                source_html += '<tr>'
                for col in source_data.columns:
                    source_html += f'<td>{row[col]}</td>'
                source_html += '</tr>'
            source_html += '</tbody></table>'

            st.markdown(source_html, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'''
            <div style="background:rgba(2,0,36,0.8);border-radius:16px;padding:20px;text-align:center;border:1px dashed {LIA["border"]};backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);">
                <p style="color:{LIA["text_secondary"]};margin:0;">Nenhuma origem de tráfego paga encontrada no período.</p>
            </div>
            ''', unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Erro ao renderizar tabela de origem/midia: {e}")

with table_cols[1]:
    # Tabela de Eventos do GA4 com Tooltips CSS
    try:
        events_data = data_provider.get_events_data(period=selected_period, custom_start=custom_start_str, custom_end=custom_end_str, campaign_filter=ga4_campaign_filter)
        if len(events_data) > 0:
            event_tooltips = {
                "page_view": "Total de visualizações da página.",
                "session_start": "Total de acessos à landing page originados das campanhas.",
                "first_visit": "Quantidade de pessoas únicas que visitaram a landing page.",
                "scroll": "Indica que o usuário rolou a página.",
                "scroll_25": "Indica até onde o usuário rolou a página (nível de leitura).",
                "scroll_50": "Indica até onde o usuário rolou a página (nível de leitura).",
                "scroll_75": "Indica até onde o usuário rolou a página (nível de leitura).",
                "landing_visit": "Usuários que realmente carregaram e visualizaram a landing page.",
                "user_engagement": "Percentual de usuários que tiveram alguma interação relevante na página.",
                "primary_cta_click": "Clique no botão principal de ação (ex: 'Baixar agora').",
                "cta_baixe_agora_click": "Clique no botão principal de ação (ex: 'Baixar agora').",
                "cta_click_store": "Clique no botão que direciona para a loja do app (App Store ou Google Play). Indica intenção clara de instalação.",
                "click": "Clique genérico em algum elemento da página.",
                "store_click": "Clique no botão que direciona para a loja do app (App Store ou Google Play). Indica intenção clara de instalação.",
                "install": "Instalações do app (evento dependente da integração do SDK dentro do app).",
            }
            columns = list(events_data.columns)
            header_html = "".join(f"<th>{html.escape(str(col))}</th>" for col in columns)
            body_rows = []
            for _, row in events_data.iterrows():
                cells = []
                for col in columns:
                    value = "" if pd.isna(row[col]) else str(row[col])
                    tooltip_attr = ""
                    if col == "Nome do Evento":
                        tooltip = event_tooltips.get(str(row[col]).strip(), "")
                        if tooltip:
                            tooltip_attr = f' title="{html.escape(tooltip)}"'
                    cells.append(f"<td{tooltip_attr}>{html.escape(value)}</td>")
                body_rows.append("<tr>" + "".join(cells) + "</tr>")
            events_table_html = f"""
            <table class="lia-html-table">
                <thead><tr>{header_html}</tr></thead>
                <tbody>{''.join(body_rows)}</tbody>
            </table>
            """
            st.markdown('<div class="table-container">', unsafe_allow_html=True)
            st.markdown('<div class="table-header"><span class="table-header-title">Eventos do Google Analytics</span></div>', unsafe_allow_html=True)
            st.markdown(events_table_html, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Erro ao renderizar tabela de eventos: {e}")

st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown('''
<div class="footer glass-card">
    Dashboard Ciclo 2 - <a href="https://applia.ai" target="_blank">LIA App</a> - Atualizado em tempo real
</div>
''', unsafe_allow_html=True)

# Fechar camada de conteudo
st.markdown('</div>', unsafe_allow_html=True)
