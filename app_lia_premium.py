import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import base64
import html
import os
import logging
import textwrap
from dashboard_kpis import build_meta_kpi_cards_payload
from build_info import get_build_stamp

# Importar integrações
from config import Config
from ga_integration import GA4Integration
from meta_integration import MetaAdsIntegration

# Importar AIAgent para análise de IA (opcional - não quebra se não disponível)
try:
    from ai_agent import AIAgent
except Exception as e:
    print(f"AIAgent não disponível: {e}")
    AIAgent = None
from meta_funnel import ACTIVATE_APP_ACTION_TYPES, INSTALL_ACTION_TYPES, STORE_CLICK_ACTION_TYPES, collect_action_type_diagnostics, collect_all_action_types, sum_actions_by_types

# =============================================================================
# CONFIGURACAO DE LOGGING
# =============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

def _now_sp() -> str:
    """Return current time as string in America/Sao_Paulo (UTC-3) without pytz."""
    from datetime import timezone as _tz

    utc_now = datetime.now(_tz.utc)
    sp_offset = timedelta(hours=-3)
    sp_now = utc_now + sp_offset
    return sp_now.strftime("%Y-%m-%d %H:%M:%S")

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
# PALETA OFICIAL LIA - MINT / VIOLET
# =============================================================================
LIA = {
    # Cores principais LIA
    "primary": "#5CC9B6",           # Mint / Aqua Green
    "primary_dark": "#5CC9B6",      # Mantém consistência com a marca
    "primary_light": "#F7F9FC",     # Ice Gray para fundos suaves
    "secondary": "#7A5CFF",         # Soft Violet
    "accent": "#7A5CFF",            # Reforço secundário

    # Base de fundo
    "gradient_start": "#F7F9FC",
    "gradient_mid": "#F7F9FC",
    "gradient_end": "#FFFFFF",

    # Backgrounds
    "bg_dark": "#FFFFFF",           # Usado para textos sobre gradientes
    "bg_card": "#FFFFFF",           # Superfície de cartões
    "bg_card_solid": "#FFFFFF",
    "bg_glass": "rgba(92, 201, 182, 0.06)",
    "bg_hover": "rgba(92, 201, 182, 0.1)",

    # Texto
    "text_light": "#1A2B49",        # Navy para títulos
    "text_primary": "#1A2B49",
    "text_secondary": "rgba(26, 43, 73, 0.7)",
    "text_muted": "rgba(26, 43, 73, 0.55)",
    "text_dark": "#1A2B49",

    # Status colors (alinhados à marca)
    "success": "#5CC9B6",
    "success_light": "rgba(92, 201, 182, 0.2)",
    "error": "#7A5CFF",
    "error_light": "rgba(122, 92, 255, 0.2)",
    "warning": "#7A5CFF",
    "warning_light": "rgba(122, 92, 255, 0.18)",

    # Bordas e sombras
    "border": "rgba(26, 43, 73, 0.12)",
    "border_light": "rgba(26, 43, 73, 0.08)",
    "shadow": "rgba(26, 43, 73, 0.12)",
    "glow": "rgba(92, 201, 182, 0.18)",
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
        self.ga4_app_client = None
        self._init_clients()

    def _init_clients(self):
        """Inicializa clientes das APIs se credenciais estiverem disponíveis"""
        try:
            # Inicializar Meta Ads
            if Config.validate_meta_credentials():
                self.meta_client = MetaAdsIntegration(
                    access_token=Config.get_meta_access_token(),
                    ad_account_id=Config.get_meta_ad_account_id(),
                    app_id=Config.get_meta_app_id(),
                )
                logger.info("Meta Ads client initialized")
        except Exception as e:
            logger.error(f"Erro ao inicializar Meta client: {e}")
            self.meta_client = None

        try:
            # Inicializar GA4
            if Config.validate_ga4_credentials():
                creds = Config.get_ga4_credentials()
                self.ga4_client = GA4Integration(
                    credentials_json=creds,
                    property_id=Config.get_ga4_property_id()
                )
                ga4_app_property_id = Config.get_ga4_app_property_id()
                if ga4_app_property_id:
                    self.ga4_app_client = GA4Integration(
                        credentials_json=creds,
                        property_id=ga4_app_property_id,
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

    def _enrich_with_sdk_events(self, result: dict, api_period: str, custom_start, custom_end):
        """Busca eventos SDK e enriquece o resultado com dados do SDK."""
        if not self.meta_client:
            return

        if not self.meta_client.app_id:
            result["_all_sdk_events"] = {}
            result["_sdk_source"] = "no_app_id"
            result["_sdk_event_types"] = []
            result["_sdk_errors"] = ["META_APP_ID não configurado — eventos SDK não podem ser consultados"]
            result["_sdk_debug"] = {}
            return

        try:
            sdk_data = self.meta_client.get_all_sdk_events(
                date_range=api_period,
                custom_start=custom_start,
                custom_end=custom_end,
            )
            result["_all_sdk_events"] = sdk_data["events"]
            result["_sdk_source"] = sdk_data["source"]
            result["_sdk_event_types"] = list(sdk_data["events"].keys())
            result["_sdk_errors"] = sdk_data["errors"]
            result["_sdk_debug"] = sdk_data.get("_debug", {})

            # Se não encontrou install events nas actions do Ads Insights,
            # usar dados do SDK endpoint (que inclui eventos não-atribuídos)
            if result.get("instalacoes_sdk", 0) == 0:
                sdk_installs = sdk_data["install_count"]
                if sdk_installs == 0 and sdk_data["activate_count"] > 0:
                    logger.warning(
                        "Using SDK activate_app (%d) as proxy for installs",
                        sdk_data["activate_count"],
                    )
                    sdk_installs = sdk_data["activate_count"]

                if sdk_installs > 0:
                    result["instalacoes_sdk"] = sdk_installs

            endpoint_unsupported = bool(result.get("_sdk_debug", {}).get("endpoint_unsupported"))
            if result.get("instalacoes_sdk", 0) == 0 and endpoint_unsupported:
                if self.ga4_app_client:
                    ga4_installs = self.ga4_app_client.get_event_count(
                        event_name="first_open",
                        date_range=api_period,
                        custom_start=custom_start,
                        custom_end=custom_end,
                    )
                    if ga4_installs > 0:
                        result["instalacoes_sdk"] = ga4_installs
                        result["_sdk_source"] = "ga4_first_open"
                        result["_sdk_debug"]["ga4_fallback"] = {
                            "event": "first_open",
                            "value": ga4_installs,
                            "used": True,
                        }
                else:
                    msg = "Instalações indisponíveis: Meta endpoint unsupported e GA4_APP_PROPERTY_ID ausente."
                    result["_sdk_errors"].append(msg)
                    result["_sdk_debug"]["ga4_fallback"] = {"used": False, "reason": "missing_ga4_app_property_id"}

        except Exception as e:
            logger.error("Failed to fetch SDK events: %s", e)
            result["_sdk_source"] = result.get("_sdk_source", "error")
            result["_sdk_errors"] = [str(e)]
            result["_sdk_debug"] = {}

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
                        result["_debug"] = {"aggregated_insights": aggregated.get("_debug", {})}

                    # Sempre buscar eventos SDK (são totais, não por campanha)
                    self._enrich_with_sdk_events(result, api_period, custom_start, custom_end)

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
                            result["_debug"] = {"aggregated_insights": aggregated.get("_debug", {})}

                        # Sempre buscar eventos SDK (são totais, não por campanha)
                        self._enrich_with_sdk_events(result, api_period, custom_start, custom_end)

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
            actions_series = df["actions"] if "actions" in df.columns else pd.Series(dtype=object)
            found_action_types = collect_all_action_types(actions_series)
            diagnostics = collect_action_type_diagnostics(actions_series)
            store_clicks, has_store_clicks = sum_actions_by_types(actions_series, STORE_CLICK_ACTION_TYPES)
            if not has_store_clicks:
                # Fallback: try outbound_click specifically
                store_clicks, has_outbound = sum_actions_by_types(actions_series, {"outbound_click"})
                if not has_outbound:
                    # Fallback: try link_click
                    store_clicks, has_link_clicks = sum_actions_by_types(actions_series, {"link_click"})
                    if has_link_clicks:
                        logger.warning(
                            "Meta funnel: store click actions not found, "
                            "using 'link_click' as fallback"
                        )
                    else:
                        logger.warning(
                            "Meta funnel: no store click actions found. "
                            "Using total clicks as fallback."
                        )
                        store_clicks = total_clicks

            # SDK install events: check all known install action types
            instalacoes_sdk, tem_eventos_instalacao = sum_actions_by_types(actions_series, INSTALL_ACTION_TYPES)
            if not tem_eventos_instalacao:
                # Try activate_app as secondary signal for installs
                activate_count, has_activate = sum_actions_by_types(actions_series, ACTIVATE_APP_ACTION_TYPES)
                if has_activate:
                    logger.warning(
                        "Meta funnel: no install events found, but found activate_app events (%d). "
                        "Using activate_app as proxy for installs.",
                        activate_count,
                    )
                    instalacoes_sdk = activate_count
                    tem_eventos_instalacao = True
                else:
                    logger.warning(
                        "Meta funnel: no SDK install events found. "
                        "Action types in response: %s",
                        list(diagnostics.get("all_action_types", {}).keys()),
                    )

            return {
                "investimento": total_spend,
                "impressoes": total_impressions,
                "alcance": safe_int(safe_sum('reach')),  # Pode ser sobrescrito por aggregated
                "frequencia": 0,  # Será sobrescrito por aggregated; reach não é aditivo
                "cliques_link": total_clicks,
                "store_clicks_meta": store_clicks,
                "instalacoes_sdk": instalacoes_sdk,
                "instalacoes_total": 0,
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
                "_action_types_found": found_action_types,
                "_sdk_diagnostics": diagnostics,
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

    def get_landing_events_card_data(self, period="7d", custom_start=None, custom_end=None):
        """Retorna dados do card de Eventos da Landing (GA4) com fallback seguro."""
        if not self.ga4_client or self.mode == "mock":
            return {
                "status": "unavailable",
                "title": "Eventos (em desenvolvimento)",
                "message": "Integração GA4/Meta em configuração. Este bloco será ativado quando GA4_PROPERTY_ID e credenciais estiverem válidos.",
                "checklist": [
                    "Adicionar a service account como Viewer na propriedade GA4",
                    "Setar GA4_PROPERTY_ID",
                    "Validar eventos da landing page",
                ],
                "error": "Credenciais GA4 ausentes ou modo mock ativo.",
            }

        api_period = self._period_to_api_format(period)
        landing_host_filter = Config.get_landing_host_filter()
        try:
            summary = self.ga4_client.get_landing_events_summary(
                date_range=api_period,
                custom_start=custom_start,
                custom_end=custom_end,
                landing_host_filter=landing_host_filter,
                limit=100,
            )

            rows = summary.get("rows", [])
            if not rows:
                return {
                    "status": "no_data",
                    "title": "Eventos da Landing (GA4)",
                    "message": "GA4 conectado, mas sem eventos para o período selecionado.",
                    "date_range": summary.get("date_range"),
                    "landing_host_filter": landing_host_filter,
                }

            events_df = pd.DataFrame(rows)
            grouped = events_df.groupby("Evento", as_index=False).agg({
                "Contagem": "sum",
                "Usuários": "sum",
                "Conversões": "sum",
            })
            grouped = grouped.sort_values("Contagem", ascending=False).head(8)

            return {
                "status": "ok",
                "title": "Eventos da Landing (GA4)",
                "table": grouped,
                "kpi_total_events": int(summary.get("total_events", 0)),
                "kpi_total_users": int(summary.get("total_users", 0)),
                "kpi_total_conversions": float(summary.get("total_conversions", 0)),
                "key_event_totals": summary.get("key_event_totals", {}),
                "has_key_events": bool(summary.get("has_key_events", False)),
                "has_conversions": bool(summary.get("has_conversions", False)),
                "date_range": summary.get("date_range"),
                "landing_host_filter": landing_host_filter,
            }
        except Exception as e:
            logger.error("Erro ao obter Eventos da Landing (GA4): %s", e)
            return {
                "status": "error",
                "title": "Eventos (em desenvolvimento)",
                "message": "Integração GA4/Meta em configuração. Este bloco será ativado quando GA4_PROPERTY_ID e credenciais estiverem válidos.",
                "checklist": [
                    "Adicionar a service account como Viewer na propriedade GA4",
                    "Setar GA4_PROPERTY_ID",
                    "Validar eventos da landing page",
                ],
                "error": str(e),
            }

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
                        'spend': 'Valor gasto',
                        'impressions': 'Exibições',
                        'clicks': 'Cliques',
                        'ctr': 'Taxa de cliques',
                        'cpc': 'Custo por clique',
                        'cpm': 'Custo por mil'
                    })
                    # Adicionar coluna de formato (Meta API não retorna diretamente de forma simples, vamos inferir ou deixar fixo)
                    df['Formato'] = df['Criativo'].apply(lambda x: "Video" if "video" in str(x).lower() else "Imagem")
                    return df[['Criativo', 'Formato', 'Valor gasto', 'Exibições', 'Cliques', 'Taxa de cliques', 'Custo por clique', 'Custo por mil']]
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
            "cliques_link": 0, "store_clicks_meta": 0, "instalacoes_sdk": 0, "instalacoes_total": 0,
            "ctr_link": 0, "cpc_link": 0, "cpm": 0,
            "delta_investimento": 0, "delta_impressoes": 0, "delta_alcance": 0,
            "delta_frequencia": 0, "delta_cliques": 0, "delta_ctr": 0,
            "delta_cpc": 0, "delta_cpm": 0,
            "_data_source": "empty", "_filter_applied": None,
            "_requested_filter": None, "_available_campaigns": [],
            "_action_types_found": {},
            "_sdk_source": "none", "_sdk_errors": [], "_sdk_debug": {},
            "_debug": {},
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
            "cliques_link": 2450, "store_clicks_meta": 1820, "instalacoes_sdk": 320, "instalacoes_total": 0,
            "ctr_link": 2.87, "cpc_link": 0.51, "cpm": 14.64,
            "delta_investimento": 12.5, "delta_impressoes": -5.2, "delta_alcance": 3.1,
            "delta_frequencia": 0.5, "delta_cliques": 15.8, "delta_ctr": 0.45,
            "delta_cpc": -8.2, "delta_cpm": 2.3,
            "_sdk_source": "none", "_sdk_errors": [], "_sdk_debug": {},
            "_debug": {},
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
            "Valor gasto": [285.00, 195.00, 165.00, 125.00, 80.00],
            "Exibições": [42000, 31000, 26000, 18000, 8000],
            "Cliques": [1280, 890, 620, 320, 90],
            "Taxa de cliques": [3.05, 2.87, 2.38, 1.78, 1.12],
            "Custo por clique": [0.22, 0.22, 0.27, 0.39, 0.89],
            "Custo por mil": [6.79, 6.29, 6.35, 6.94, 10.00],
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
# CACHED DATA FETCHERS (TTL = 5 min, keyed by params)
# =============================================================================


def _normalize_breakdowns_for_cache(breakdowns):
    return tuple(sorted({str(b).strip() for b in (breakdowns or ()) if str(b).strip()}))

@st.cache_data(ttl=300, show_spinner=False)
def _fetch_meta_cached(period, campaign_filter, custom_start, custom_end, level, breakdowns, app_id):
    return data_provider.get_meta_metrics(
        period=period, campaign_filter=campaign_filter, level=level,
        custom_start=custom_start, custom_end=custom_end,
    )


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_ga4_cached(period, custom_start, custom_end, campaign_filter):
    return data_provider.get_ga4_metrics(
        period=period, custom_start=custom_start,
        custom_end=custom_end, campaign_filter=campaign_filter,
    )


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_creative_cached(period, campaign_filter, custom_start, custom_end):
    return data_provider.get_creative_data(
        period=period, campaign_filter=campaign_filter,
        custom_start=custom_start, custom_end=custom_end,
    )


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_trends_cached(period, campaign_filter, custom_start, custom_end):
    return data_provider.get_daily_trends(
        period=period, campaign_filter=campaign_filter,
        custom_start=custom_start, custom_end=custom_end,
    )

# =============================================================================
# COMPONENTE: CARD DE ERRO AMIGAVEL
# =============================================================================
def render_error_card(title="Estamos ajustando os dados", message="Algumas metricas estao temporariamente indisponiveis. Nossa equipe ja esta verificando."):
    owl_img = f'<img src="data:image/png;base64,{logo_base64}" style="width:48px;height:48px;margin-bottom:12px;filter:drop-shadow(0 0 10px rgba(92,201,182,0.18));">' if logo_base64 else ''
    st.markdown(f'''
    <div style="background:{LIA["bg_card"]};backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);border-radius:20px;padding:32px;text-align:center;border:1px solid {LIA["border"]};margin:16px 0;box-shadow:0 12px 24px rgba(92,201,182,0.12), 0 0 16px rgba(122,92,255,0.14);">
        {owl_img}
        <h3 style="color:{LIA["text_light"]};font-size:18px;margin:0 0 8px 0;">{title}</h3>
        <p style="color:{LIA["text_secondary"]};font-size:14px;margin:0 0 16px 0;">{message}</p>
        <button onclick="window.location.reload()" style="background:linear-gradient(135deg,{LIA["primary"]},{LIA["secondary"]});color:#FFFFFF;border:none;padding:10px 24px;border-radius:999px;font-size:14px;cursor:pointer;font-weight:600;box-shadow:0 8px 16px rgba(92,201,182,0.18), 0 0 12px rgba(122,92,255,0.14);">
            Recarregar dados
        </button>
    </div>
    ''', unsafe_allow_html=True)

# =============================================================================
# CSS - LIA MINT / VIOLET (ACESSIVEL E ELEVADO)
# =============================================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

*, *::before, *::after {{ box-sizing: border-box; }}

/* Fundo: Ice Gray com glow suave */
html, body, [data-testid="stAppViewContainer"], .stApp {{
    background: linear-gradient(
        180deg,
        rgba(255, 210, 180, 0.3) 0%,
        rgba(255, 245, 240, 0.4) 25%,
        #FFFFFF 60%
    ) !important;
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
    background: radial-gradient(ellipse at 20% 0%, rgba(92, 201, 182, 0.12) 0%, transparent 55%),
                radial-gradient(ellipse at 85% 100%, rgba(122, 92, 255, 0.1) 0%, transparent 45%);
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
    background: linear-gradient(
        120deg,
        rgba(255, 210, 180, 0.35) 0%,
        rgba(255, 170, 120, 0.35) 35%,
        rgba(255, 150, 110, 0.28) 70%,
        rgba(255, 245, 240, 0.4) 100%
    );
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid {LIA["border"]};
    border-radius: 20px;
    box-shadow: 0 12px 24px rgba(92, 201, 182, 0.12),
                0 0 16px rgba(92, 201, 182, 0.18);
    padding: 24px;
}}

.content-layer {{
    display: flex;
    flex-direction: column;
    gap: 18px;
    margin-top: 16px;
}}

.empty-state {{
    display: none !important;
}}

/* ========== HEADER (glass escuro com glow) ========== */
.lia-header {{
    background: linear-gradient(
        120deg,
        rgba(255, 210, 180, 0.35) 0%,
        rgba(255, 170, 120, 0.35) 35%,
        rgba(255, 150, 110, 0.28) 70%,
        rgba(255, 245, 240, 0.4) 100%
    );
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border-radius: 20px;
    padding: 20px 28px;
    min-height: 84px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border: 1px solid {LIA["border"]};
    box-shadow: 0 12px 24px rgba(92, 201, 182, 0.12),
                0 0 16px rgba(122, 92, 255, 0.14);
    margin-bottom: 0;
    overflow: visible;
    position: relative;
    z-index: 2;
}}

.lia-header-left {{
    display: flex;
    align-items: center;
    gap: 14px;
}}

.lia-logo {{
    width: 50px;
    height: 50px;
    border-radius: 20px;
    background: linear-gradient(135deg, {LIA["primary"]} 0%, {LIA["secondary"]} 100%);
    backdrop-filter: blur(12px);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 8px 16px rgba(92, 201, 182, 0.18),
                0 0 12px rgba(122, 92, 255, 0.14);
    position: relative;
    z-index: 3;
}}

.lia-logo img {{
    width: 32px;
    height: 32px;
    filter: none;
    mix-blend-mode: normal;
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
    text-shadow: none;
}}

.lia-subtitle {{
    font-size: 12px;
    color: {LIA["text_secondary"]};
    font-weight: 500;
    margin: 0;
}}

/* ========== STATUS CARD ========== */
.status-card {{
    background: {LIA["bg_card"]};
    border-radius: 20px;
    padding: 12px 20px;
    display: flex;
    align-items: center;
    gap: 12px;
    border: 1px solid {LIA["border"]};
    box-shadow: 0 10px 20px rgba(92, 201, 182, 0.12),
                0 0 12px rgba(92, 201, 182, 0.18);
}}

.status-owl {{
    width: 28px;
    height: 28px;
    filter: drop-shadow(0 0 8px rgba(92, 201, 182, 0.18));
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
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 800;
    box-shadow: 0 6px 12px rgba(92, 201, 182, 0.18),
                0 0 10px rgba(122, 92, 255, 0.14);
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
    background: {LIA["bg_card"]};
    border-radius: 20px;
    padding: 16px;
    border: 1px solid {LIA["border"]};
    transition: transform 0.6s ease, background 0.2s ease, box-shadow 0.2s ease;
    cursor: pointer;
    box-shadow: 0 10px 20px rgba(92, 201, 182, 0.12),
                0 0 12px rgba(92, 201, 182, 0.18);
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
    background: {LIA["bg_card"]};
    border-color: {LIA["primary"]};
    box-shadow: 0 12px 24px rgba(92, 201, 182, 0.14),
                0 0 14px rgba(92, 201, 182, 0.18);
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
    filter: drop-shadow(0 0 6px rgba(92, 201, 182, 0.18));
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
    text-shadow: none;
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

.delta-up {{ color: {LIA["success"]}; text-shadow: 0 0 10px rgba(92, 201, 182, 0.18); }}
.delta-down {{ color: {LIA["error"]}; text-shadow: 0 0 10px rgba(122, 92, 255, 0.14); }}
.delta-neutral {{ color: {LIA["text_muted"]}; }}

/* ========== BADGES ========== */
.badge-row {{
    display: flex;
    gap: 8px;
    margin-bottom: 16px;
}}

.badge {{
    padding: 6px 12px;
    border-radius: 18px;
    font-size: 11px;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 6px;
}}

.badge-orange, .badge-cyan {{
    background: rgba(92, 201, 182, 0.12);
    color: {LIA["primary"]};
    border: 1px solid rgba(92, 201, 182, 0.3);
    box-shadow: 0 0 6px rgba(92, 201, 182, 0.14);
}}

.badge-green {{
    background: rgba(92, 201, 182, 0.12);
    color: {LIA["success"]};
    border: 1px solid rgba(92, 201, 182, 0.3);
    box-shadow: 0 0 6px rgba(92, 201, 182, 0.14);
}}

/* ========== TABELA COM HEADER GLASS ESCURO ========== */
.table-container {{
    background: {LIA["bg_card"]};
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-radius: 20px;
    overflow: hidden;
    border: 1px solid {LIA["border"]};
    box-shadow: 0 12px 24px rgba(92, 201, 182, 0.12),
                0 0 16px rgba(92, 201, 182, 0.18);
    margin-bottom: 12px;
}}

.table-header {{
    background: rgba(92, 201, 182, 0.12);
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
    background: rgba(92, 201, 182, 0.12);
    border-bottom: 1px solid {LIA["border"]};
    color: {LIA["text_light"]};
    font-weight: 600;
    text-transform: capitalize;
    letter-spacing: 0.02em;
}}

.lia-html-table tbody td {{
    border-bottom: 1px solid rgba(26, 43, 73, 0.08);
    color: {LIA["text_primary"]};
    opacity: 0.88;
    transition: opacity 0.3s ease, background 0.3s ease;
}}

.lia-html-table tbody tr:nth-child(odd) {{
    background: rgba(247, 249, 252, 0.9);
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
    box-shadow: 0 0 8px rgba(92, 201, 182, 0.18);
}}

.tooltip-popup {{
    position: absolute;
    left: 0;
    bottom: calc(100% + 8px);
    background: {LIA["bg_card"]};
    color: {LIA["text_light"]};
    padding: 8px 10px;
    border-radius: 16px;
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
    box-shadow: 0 10px 20px rgba(92, 201, 182, 0.12),
                0 0 14px rgba(122, 92, 255, 0.14);
}}

.event-tooltip-wrapper:hover .tooltip-popup,
.event-tooltip-wrapper:focus-within .tooltip-popup {{
    opacity: 1;
    pointer-events: auto;
    transform: translateY(0);
}}

/* ========== CARD DE ESCOPO ========== */
.scope-card {{
    background: {LIA["bg_card"]};
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-radius: 20px;
    padding: 16px 20px;
    display: flex;
    align-items: center;
    gap: 12px;
    border: 1px solid {LIA["border"]};
    box-shadow: 0 12px 24px rgba(92, 201, 182, 0.12),
                0 0 14px rgba(92, 201, 182, 0.18);
    margin-bottom: 12px;
}}

.scope-text {{
    font-size: 13px;
    color: {LIA["text_primary"]};
}}

/* ========== GRAFICOS EM CARDS ========== */
.chart-card {{
    background: {LIA["bg_card"]};
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-radius: 20px;
    padding: 18px;
    border: 1px solid {LIA["border"]};
    box-shadow: 0 12px 24px rgba(92, 201, 182, 0.12),
                0 0 16px rgba(92, 201, 182, 0.18);
    margin-bottom: 12px;
}}

.trend-toggle [data-baseweb="tab-list"] {{
    gap: 8px;
    background: rgba(92, 201, 182, 0.1);
    border-radius: 18px;
    padding: 4px;
}}

.trend-toggle [data-baseweb="tab"] {{
    background: transparent;
    border-radius: 18px;
    padding: 6px 14px;
    color: {LIA["text_secondary"]};
    font-size: 13px;
    font-weight: 600;
}}

.trend-toggle [aria-selected="true"] {{
    background: linear-gradient(135deg, {LIA["primary"]} 0%, {LIA["secondary"]} 100%);
    color: {LIA["bg_dark"]};
    box-shadow: 0 8px 16px rgba(92, 201, 182, 0.14),
                0 0 12px rgba(122, 92, 255, 0.14);
}}

.js-plotly-plot .plotly .modebar {{ display: none !important; }}

/* ========== FILTROS ========== */
.filter-card {{
    background: {LIA["bg_card"]};
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid {LIA["border"]};
    border-radius: 20px;
    box-shadow: 0 8px 16px rgba(92, 201, 182, 0.1);
    padding: 18px 18px 10px 18px;
}}

.stSelectbox > div > div {{
    background: #FFFFFF !important;
    border: 1px solid {LIA["border"]} !important;
    border-radius: 18px !important;
    box-shadow: none;
    color: {LIA["text_light"]} !important;
}}

.stSelectbox > div > div:hover {{
    border-color: {LIA["primary"]} !important;
    box-shadow: none;
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
    background: linear-gradient(135deg, rgba(92, 201, 182, 0.12) 0%, rgba(122, 92, 255, 0.12) 100%);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid {LIA["primary"]};
    border-radius: 20px;
    padding: 24px;
    margin-bottom: 16px;
    box-shadow: 0 12px 24px rgba(92, 201, 182, 0.12),
                0 0 14px rgba(122, 92, 255, 0.14);
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
    border-radius: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    box-shadow: 0 8px 16px rgba(92, 201, 182, 0.18),
                0 0 12px rgba(122, 92, 255, 0.14);
}}

.ai-agent-title {{
    font-size: 16px;
    font-weight: 700;
    color: {LIA["text_light"]};
    text-shadow: none;
}}

.ai-agent-subtitle {{
    font-size: 12px;
    color: {LIA["text_secondary"]};
}}

.ai-agent-content {{
    background: #FFFFFF;
    border-radius: 20px;
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
    color: {LIA["text_light"]};
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
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 999px !important;
    padding: 10px 20px !important;
    font-weight: 600 !important;
    box-shadow: 0 8px 16px rgba(92, 201, 182, 0.18),
                0 0 12px rgba(122, 92, 255, 0.14) !important;
    transition: all 0.3s ease !important;
}}

.stButton > button:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 20px rgba(92, 201, 182, 0.18),
                0 0 14px rgba(122, 92, 255, 0.14) !important;
}}

.stButton > button[kind="secondary"],
.stButton > button[kind="secondary"]:hover {{
    background: #FFFFFF !important;
    color: {LIA["text_light"]} !important;
    border: 1px solid rgba(92, 201, 182, 0.18) !important;
    box-shadow: none !important;
    transform: none !important;
}}

.stButton > button[kind="tertiary"],
.stButton > button[kind="tertiary"]:hover {{
    background: transparent !important;
    color: {LIA["text_light"]} !important;
    border: none !important;
    box-shadow: none !important;
    text-decoration: underline;
    text-decoration-color: rgba(92, 201, 182, 0.6);
}}

.ai-analysis-button .stButton > button {{
    position: relative;
    overflow: hidden;
    justify-content: center;
    gap: 10px;
    height: 56px;
    font-size: 16px !important;
    letter-spacing: 0.2px;
    background: {LIA["text_light"]} !important;
    color: #FFFFFF !important;
    border-radius: 999px !important;
    border: none !important;
    box-shadow: 0 10px 18px rgba(26, 43, 73, 0.18);
}}

.ai-analysis-button .stButton > button::after {{
    content: "";
    position: absolute;
    left: 8%;
    right: 8%;
    bottom: 8px;
    height: 3px;
    border-radius: 999px;
    background: linear-gradient(90deg, {LIA["primary"]}, {LIA["secondary"]});
    opacity: 0;
    transition: opacity 0.25s ease;
}}

.ai-analysis-button .stButton > button:hover::after {{
    opacity: 1;
}}

/* Date input styling */
.stDateInput > div > div {{
    background: #FFFFFF !important;
    border: 1px solid {LIA["border"]} !important;
    border-radius: 18px !important;
    color: {LIA["text_light"]} !important;
    box-shadow: none !important;
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

/* Alerts */
.stAlert {{
    background: #FFFFFF !important;
    border: 1px solid rgba(92, 201, 182, 0.18) !important;
    border-radius: 20px !important;
    box-shadow: 0 10px 20px rgba(92, 201, 182, 0.12),
                0 0 12px rgba(122, 92, 255, 0.14) !important;
}}

.stAlert [data-testid="stAlertContent"] {{
    color: {LIA["text_light"]} !important;
}}

/* Expander styling */
.streamlit-expanderHeader {{
    background: #FFFFFF !important;
    border: 1px solid {LIA["border"]} !important;
    border-radius: 18px !important;
    color: {LIA["text_light"]} !important;
}}

/* Scrollbar styling */
::-webkit-scrollbar {{
    width: 8px;
    height: 8px;
}}

::-webkit-scrollbar-track {{
    background: rgba(26, 43, 73, 0.08);
    border-radius: 16px;
}}

::-webkit-scrollbar-thumb {{
    background: {LIA["primary"]};
    border-radius: 16px;
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
    text-shadow: 0 0 10px rgba(92, 201, 182, 0.18);
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
        _cache_app_id = data_provider.meta_client.app_id if data_provider.meta_client else "no_app_id"
        _cache_breakdowns = _normalize_breakdowns_for_cache(())
        meta_data = _fetch_meta_cached(selected_period, meta_campaign_filter, custom_start_str, custom_end_str, "campaign", _cache_breakdowns, _cache_app_id)
        ga4_data = _fetch_ga4_cached(selected_period, custom_start_str, custom_end_str, ga4_campaign_filter)
        creative_data = _fetch_creative_cached(selected_period, meta_campaign_filter, custom_start_str, custom_end_str)
        trends_data = _fetch_trends_cached(selected_period, meta_campaign_filter, custom_start_str, custom_end_str)
        cycle_status = data_provider.get_cycle_status(selected_period, meta_data, creative_data)
        landing_events_card_data = data_provider.get_landing_events_card_data(selected_period, custom_start_str, custom_end_str)
except Exception as e:
    logger.error(f"Erro ao carregar dados do módulo Premium: {e}")
    meta_data = {
        **data_provider._empty_meta_metrics(),
        "_data_source": "error",
        "_requested_filter": meta_campaign_filter,
    }
    ga4_data = {
        "sessoes": 0, "usuarios": 0, "pageviews": 0,
        "taxa_engajamento": 0, "tempo_medio": "0m 0s",
        "delta_sessoes": 0, "delta_usuarios": 0, "delta_pageviews": 0,
        "delta_engajamento": 0, "_data_source": "error"
    }
    creative_data = {}
    trends_data = []
    landing_events_card_data = {"status": "error", "title": "Eventos (em desenvolvimento)", "message": "Integração GA4/Meta em configuração. Este bloco será ativado quando GA4_PROPERTY_ID e credenciais estiverem válidos.", "checklist": ["Adicionar a service account como Viewer na propriedade GA4", "Setar GA4_PROPERTY_ID", "Validar eventos da landing page"], "error": "Falha no carregamento de dados."}

# -----------------------------------------------------------------------------
# REFRESH BUTTON + LAST UPDATED TIMESTAMP
# -----------------------------------------------------------------------------
_refresh_cols = st.columns([5, 1, 1])
with _refresh_cols[1]:
    if st.button("Atualizar dados", key="btn_refresh_data"):
        st.cache_data.clear()
        st.rerun()
with _refresh_cols[2]:
    if st.button("Limpar cache", key="btn_clear_cache"):
        st.cache_data.clear()
        st.rerun()

_fetch_ts = meta_data.get("_fetch_timestamp")
if _fetch_ts:
    st.caption(f"Dados atualizados em: {_fetch_ts[:19].replace('T', ' ')} (SP)")
else:
    st.caption(f"Dados carregados em: {_now_sp()} (SP)")

st.caption(f"🔖 {get_build_stamp()}")

# -----------------------------------------------------------------------------
# SDK EVENTS — dados para uso interno (sem poluir a tela)
# -----------------------------------------------------------------------------
_diag = meta_data.get("_sdk_diagnostics", {})
_data_source = meta_data.get("_data_source", "unknown")
_sdk_installs = meta_data.get("instalacoes_sdk", 0)
_all_sdk_events = meta_data.get("_all_sdk_events", {})
_sdk_source = meta_data.get("_sdk_source", "none")
_sdk_errors = meta_data.get("_sdk_errors", [])
_sdk_debug = meta_data.get("_sdk_debug", {})

# Painel de diagnóstico SDK (apenas modo admin — colapsado por padrão)
if st.session_state.get("show_integration_settings") and _data_source in ("real", "real_no_filter"):
    with st.expander("🔧 Diagnóstico SDK (admin)", expanded=False):
        _SDK_EVENT_LABELS = {
            "fb_mobile_install": "App Installs",
            "fb_mobile_activate_app": "Activate App",
            "fb_mobile_content_view": "View Content",
            "fb_mobile_purchase": "Purchase",
            "fb_mobile_add_to_cart": "Add to Cart",
            "fb_mobile_complete_registration": "Complete Registration",
            "app_install": "App Install",
            "mobile_app_install": "Mobile App Install",
            "omni_app_install": "Omni App Install",
            "activate_app": "Activate App",
            "omni_activate_app": "Omni Activate App",
        }
        st.markdown(f"**Fonte dos dados SDK:** `{_sdk_source}`")
        if _all_sdk_events:
            for evt, count in sorted(_all_sdk_events.items(), key=lambda x: -x[1]):
                label = _SDK_EVENT_LABELS.get(evt, evt)
                st.markdown(f"- {label} (`{evt}`): **{count:,}**")
        elif _sdk_installs > 0:
            st.markdown(f"Instalações detectadas: **{_sdk_installs:,}**")
        if _sdk_errors:
            st.markdown("**Erros:**")
            for err in _sdk_errors:
                st.caption(f"⚠️ {err}")
        if _sdk_debug:
            st.markdown(f"App ID: `{_sdk_debug.get('app_id', 'N/A')}` | "
                        f"Período: `{_sdk_debug.get('period', 'N/A')}` | "
                        f"Probe OK: `{_sdk_debug.get('app_identity_ok', False)}`")
        if _diag and _diag.get("all_action_types"):
            st.markdown("**Action types do Ads Insights:**")
            for atype, count in sorted(_diag["all_action_types"].items()):
                marker = ""
                if atype in INSTALL_ACTION_TYPES:
                    marker = " ← INSTALL"
                elif atype in ACTIVATE_APP_ACTION_TYPES:
                    marker = " ← ACTIVATE"
                st.caption(f"`{atype}`: {count}{marker}")

# -----------------------------------------------------------------------------
# STATUS DO CICLO (COM CORUJA)
# -----------------------------------------------------------------------------
try:
    owl_img = f'<img src="data:image/png;base64,{logo_base64}" class="status-owl">' if logo_base64 else ''
except Exception as e:
    logger.error(f"Erro ao gerar imagem da coruja: {e}")
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
    # Indicador discreto de fonte de dados (apenas em modo admin)
    data_source = meta_data.get("_data_source", "unknown")
    if data_source == "real":
        st.caption(f"✅ Meta Ads conectado | Filtro: {meta_data.get('_filter_applied', 'Nenhum')}")
    elif data_source == "real_no_filter":
        st.caption(f"⚠️ Meta Ads: Sem dados para '{meta_data.get('_requested_filter')}'. Mostrando total da conta.")
    else:
        st.caption("💡 Dados de demonstração. Configure as credenciais no Streamlit Secrets.")

# =============================================================================
# SEÇÃO DE ANÁLISE COM IA (PRIMEIRA DOBRA)
# =============================================================================
st.markdown('<div class="section-title"><div class="section-icon">🤖</div> Análise com IA</div>', unsafe_allow_html=True)

# Verificar se a API key e AIAgent estão disponíveis
if AIAgent is None:
    st.markdown(f'''
    <div class="glass-card" style="padding: 20px; text-align: center;">
        <p style="color: {LIA["text_muted"]}; margin: 0;">
            ⚠️ IA Agent desativado (dependência OpenAI indisponível).
        </p>
    </div>
    ''', unsafe_allow_html=True)
elif Config.validate_openai_credentials():
    # Determinar o ciclo baseado na campanha selecionada
    cycle = campanha if campanha in ["Ciclo 1", "Ciclo 2"] else "Todos os Ciclos"

    # Botão para gerar análise
    st.markdown('<div class="ai-analysis-button">', unsafe_allow_html=True)
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
    st.markdown('</div>', unsafe_allow_html=True)

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

kpi_cards = build_meta_kpi_cards_payload(meta_data)

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
  <div class="section-title"><div class="section-icon">$</div> Resultados dos anúncios (Meta Ads)</div>
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
st.markdown('<div class="section-title"><div class="section-icon">*</div> Desempenho por anúncio</div>', unsafe_allow_html=True)

if len(creative_data) > 0:
    try:
        best_ctr_idx = creative_data["Taxa de cliques"].idxmax()
        best_ctr_name = str(creative_data.loc[best_ctr_idx, "Criativo"])[:22]

        st.markdown(f'''
        <div class="badge-row">
            <div class="badge badge-orange">Criativo campeão: {best_ctr_name}... ({creative_data.loc[best_ctr_idx, "Taxa de cliques"]:.2f}% taxa de cliques)</div>
        </div>
        ''', unsafe_allow_html=True)

        st.markdown('<div class="table-container">', unsafe_allow_html=True)
        st.markdown('<div class="table-header"><span class="table-header-title">Desempenho de cada anúncio</span></div>', unsafe_allow_html=True)

        # Mostrar todos os criativos, ordenados por CTR (campeão primeiro)
        creative_display = creative_data.sort_values('Taxa de cliques', ascending=False)
        creative_formatters = {
            "Valor gasto": lambda value: f"$ {value:,.2f}",
            "Exibições": lambda value: f"{value:,.0f}",
            "Cliques": lambda value: f"{value:,.0f}",
            "Taxa de cliques": lambda value: f"{value:.2f}%",
            "Custo por clique": lambda value: f"$ {value:,.2f}",
            "Custo por mil": lambda value: f"$ {value:,.2f}",
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
    <div class="empty-state" style="background:{LIA["bg_card"]};border-radius:20px;padding:32px;text-align:center;border:1px dashed {LIA["border"]};backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);">
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
    <span class="scope-text"><strong>Estamos acompanhando seus anúncios e o site.</strong> Aqui você vê o caminho completo: do anúncio até a instalação do app.</span>
</div>
''', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TENDENCIA TEMPORAL
# -----------------------------------------------------------------------------
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title"><div class="section-icon">~</div> Evolução ao longo do tempo</div>', unsafe_allow_html=True)

if isinstance(trends_data, pd.DataFrame) and not trends_data.empty and "Data" in trends_data.columns:
    try:
        st.markdown('<div class="chart-card trend-toggle">', unsafe_allow_html=True)
        st.markdown('<div class="section-title"><div class="section-icon">~</div> Cliques por dia</div>', unsafe_allow_html=True)

        trend_tabs = st.tabs(["Diário", "Semanal"])
        trend_daily = trends_data.copy()
        # Use explicit format to avoid parsing warnings (Data is in format "dd/mm")
        trend_daily["__date"] = pd.to_datetime(trend_daily["Data"], format="%d/%m", errors="coerce")
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
                fillcolor="rgba(92,201,182,0.2)"
            ))
            fig_daily.update_layout(
                height=260,
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(247,249,252,0)",
                plot_bgcolor="rgba(247,249,252,0)",
                xaxis=dict(showgrid=False, tickfont=dict(size=11, color=LIA["text_secondary"]), tickcolor=LIA["text_secondary"]),
                yaxis=dict(showgrid=True, gridcolor="rgba(92,201,182,0.12)", tickfont=dict(size=11, color=LIA["text_secondary"])),
                showlegend=False
            )
            st.plotly_chart(fig_daily, use_container_width=True)

        with trend_tabs[1]:
            weekly = trend_daily.dropna(subset=["__date"]).set_index("__date").resample("W-MON")["Cliques"].sum().reset_index()
            weekly["Label"] = weekly["__date"].dt.strftime("Sem %d/%m")
            if weekly.empty:
                st.markdown(f'''
                <div class="empty-state" style="background:{LIA["bg_card"]};border-radius:20px;padding:24px;text-align:center;border:1px dashed {LIA["border"]};">
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
                    fillcolor="rgba(122,92,255,0.18)"
                ))
                fig_weekly.update_layout(
                    height=260,
                    margin=dict(l=10, r=10, t=10, b=10),
                    paper_bgcolor="rgba(247,249,252,0)",
                    plot_bgcolor="rgba(247,249,252,0)",
                    xaxis=dict(showgrid=False, tickfont=dict(size=11, color=LIA["text_secondary"])),
                    yaxis=dict(showgrid=True, gridcolor="rgba(92,201,182,0.12)", tickfont=dict(size=11, color=LIA["text_secondary"])),
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
                fillcolor="rgba(92,201,182,0.16)"
            ))
            fig1.update_layout(
                title=dict(text="Cliques/Dia", font=dict(size=14, color=LIA["text_light"], family="Inter")),
                height=220, margin=dict(l=10, r=10, t=40, b=30),
                paper_bgcolor="rgba(247,249,252,0)", plot_bgcolor="rgba(247,249,252,0)",
                xaxis=dict(showgrid=False, tickfont=dict(size=11, color=LIA["text_secondary"]), showline=True, linecolor="rgba(92,201,182,0.2)"),
                yaxis=dict(showgrid=True, gridcolor="rgba(92,201,182,0.12)", tickfont=dict(size=11, color=LIA["text_secondary"]), showline=True, linecolor="rgba(92,201,182,0.2)"),
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
                fillcolor="rgba(122,92,255,0.16)"
            ))
            fig2.update_layout(
                title=dict(text="CTR/Dia (%)", font=dict(size=14, color=LIA["text_light"], family="Inter")),
                height=220, margin=dict(l=10, r=10, t=40, b=30),
                paper_bgcolor="rgba(247,249,252,0)", plot_bgcolor="rgba(247,249,252,0)",
                xaxis=dict(showgrid=False, tickfont=dict(size=11, color=LIA["text_secondary"]), showline=True, linecolor="rgba(92,201,182,0.2)"),
                yaxis=dict(showgrid=True, gridcolor="rgba(92,201,182,0.12)", tickfont=dict(size=11, color=LIA["text_secondary"]), showline=True, linecolor="rgba(92,201,182,0.2)"),
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
                fill="tozeroy", fillcolor="rgba(92,201,182,0.2)"
            ))
            fig3.update_layout(
                title=dict(text="CPC/Dia ($)", font=dict(size=14, color=LIA["text_light"], family="Inter")),
                height=220, margin=dict(l=10, r=10, t=40, b=30),
                paper_bgcolor="rgba(247,249,252,0)", plot_bgcolor="rgba(247,249,252,0)",
                xaxis=dict(showgrid=False, tickfont=dict(size=11, color=LIA["text_secondary"]), showline=True, linecolor="rgba(92,201,182,0.2)"),
                yaxis=dict(showgrid=True, gridcolor="rgba(92,201,182,0.12)", tickfont=dict(size=11, color=LIA["text_secondary"]), showline=True, linecolor="rgba(92,201,182,0.2)"),
                showlegend=False
            )
            st.plotly_chart(fig3, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Erro ao renderizar graficos: {e}")
        render_error_card("Graficos indisponiveis", "Estamos processando os dados de tendencia.")
else:
    st.markdown(f'''
    <div class="empty-state" style="background:{LIA["bg_card"]};border-radius:20px;padding:32px;text-align:center;border:1px dashed {LIA["border"]};backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);">
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
    st.markdown('<div class="section-title"><div class="section-icon">~</div> Cliques e taxa de cliques por dia</div>', unsafe_allow_html=True)
    if isinstance(trends_data, pd.DataFrame) and not trends_data.empty and "Data" in trends_data.columns:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=trends_data["Data"], y=trends_data["Cliques"], name="Cliques", mode="lines+markers", line=dict(color=LIA["primary"], width=3, shape='spline'), marker=dict(size=8, color=LIA["primary"]), fill="tozeroy", fillcolor="rgba(92,201,182,0.16)"))
        fig.add_trace(go.Scatter(x=trends_data["Data"], y=trends_data["CTR"], name="CTR %", yaxis="y2", mode="lines+markers", line=dict(color=LIA["success"], width=3, shape='spline'), marker=dict(size=8, color=LIA["success"])))
        fig.update_layout(
            yaxis2=dict(overlaying="y", side="right", range=[0, trends_data["CTR"].max() * 1.2] if trends_data["CTR"].max() > 0 else [0, 5], tickfont=dict(color=LIA["text_secondary"]), gridcolor="rgba(92,201,182,0.12)"),
            yaxis=dict(tickfont=dict(color=LIA["text_secondary"]), gridcolor="rgba(92,201,182,0.12)"),
            xaxis=dict(tickfont=dict(color=LIA["text_secondary"])),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color=LIA["text_light"])),
            height=350, margin=dict(l=0, r=0, t=30, b=0),
            paper_bgcolor="rgba(247,249,252,0)", plot_bgcolor="rgba(247,249,252,0)",
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown(f'''
        <div class="empty-state" style="background:{LIA["bg_card"]};border-radius:20px;padding:32px;text-align:center;border:1px dashed {LIA["border"]};">
            <p style="color:{LIA["text_secondary"]};margin:0;">Sem dados de tendência para o período selecionado.</p>
        </div>
    ''', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with cols[1]:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)

    # Determinar modo do funil com base nos dados disponíveis
    _has_install_events = int(meta_data.get("instalacoes_sdk", 0) or 0) > 0
    _has_store_clicks = int(meta_data.get("store_clicks_meta", 0) or 0) > 0

    if _has_install_events or _has_store_clicks:
        # Funil de instalação: campanha de app install
        st.markdown('<div class="section-title"><div class="section-icon">V</div> Caminho do usuário até a instalação</div>', unsafe_allow_html=True)
        store_clicks_meta = int(meta_data.get("store_clicks_meta", 0) or 0)
        instalacoes = int(meta_data.get("instalacoes_sdk", 0) or 0)
        funnel_labels = ["Viram o anúncio", "Clicaram no anúncio", "Foram para a loja do app", "Instalaram o app (SDK)"]
        funnel_values = [
            int(meta_data.get('impressoes', 0) or 0),
            int(meta_data.get('cliques_link', 0) or 0),
            store_clicks_meta,
            instalacoes,
        ]
        funnel_caption = "Funil de conversão · Mostra quantas pessoas passaram por cada etapa, desde ver o anúncio até instalar o app"
    else:
        # Funil de landing page: campanha de tráfego/conversão no site
        st.markdown('<div class="section-title"><div class="section-icon">V</div> Caminho do usuário até a ação no site</div>', unsafe_allow_html=True)

        # Buscar primary_cta_click do GA4 events
        _cta_clicks = 0
        try:
            _events_df = data_provider.get_events_data(
                period=selected_period,
                custom_start=custom_start_str,
                custom_end=custom_end_str,
                campaign_filter=ga4_campaign_filter,
            )
            if not _events_df.empty and "Nome do Evento" in _events_df.columns:
                _cta_rows = _events_df[_events_df["Nome do Evento"].str.contains("cta_click|primary_cta", case=False, na=False)]
                if not _cta_rows.empty:
                    # Extrair número da string formatada "10 (0.23%)"
                    raw = str(_cta_rows.iloc[0]["Contagem de Eventos"])
                    _cta_clicks = int(raw.replace(".", "").split("(")[0].strip().split()[0]) if raw else 0
        except Exception:
            _cta_clicks = 0

        ga4_sessions = int(ga4_data.get('sessoes', 0) or 0)
        funnel_labels = ["Viram o anúncio", "Clicaram no anúncio", "Visitaram o site", "Clicaram no CTA"]
        funnel_values = [
            int(meta_data.get('impressoes', 0) or 0),
            int(meta_data.get('cliques_link', 0) or 0),
            ga4_sessions,
            _cta_clicks,
        ]
        funnel_caption = "Funil de conversão · Mostra quantas pessoas passaram por cada etapa, desde ver o anúncio até clicar no CTA do site"

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
        paper_bgcolor="rgba(247,249,252,0)",
        plot_bgcolor="rgba(247,249,252,0)",
        font=dict(color=LIA["text_light"])
    )
    st.plotly_chart(fig_funnel, use_container_width=True)
    st.caption(funnel_caption)

    # Se sem installs em modo real, exibir nota discreta no admin
    if not _has_install_events and meta_data.get("_data_source") in ("real", "real_no_filter"):
        if st.session_state.get("show_integration_settings"):
            _no_app_id = not getattr(data_provider, 'meta_client', None) or not getattr(data_provider.meta_client, 'app_id', None)
            if _no_app_id:
                st.caption("ℹ️ Configure META_APP_ID nos Secrets para habilitar dados de instalação do SDK.")
            else:
                st.caption("ℹ️ Nenhum evento de instalação SDK detectado no período. Verifique o Meta Events Manager.")

    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# LANDING PAGE (GA4)
# -----------------------------------------------------------------------------
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title"><div class="section-icon">@</div> Comportamento no site</div>', unsafe_allow_html=True)

# Indicador de fonte de dados GA4 (discreto)
ga4_source = ga4_data.get("_data_source", "unknown")
ga4_filter = ga4_data.get("_campaign_filter", None)
if st.session_state.get("show_integration_settings"):
    if ga4_source == "real":
        st.caption(f"✅ GA4 conectado | Filtro: {ga4_filter if ga4_filter else 'Todas as campanhas'}")
    elif ga4_source == "partial":
        st.caption(f"⚠️ GA4: dados parciais | Filtro: {ga4_filter if ga4_filter else 'Todas as campanhas'}")
    elif ga4_source == "no_data":
        st.caption(f"⚠️ GA4 conectado, sem dados para '{ga4_filter}'. UTMs podem levar até 48h.")
    elif ga4_source == "mock":
        st.caption("💡 GA4: dados de demonstração. Configure credenciais nos Secrets.")

ga4_cards = [
    {"icon": "🌐", "label": "Visitas ao site", "value": f"{ga4_data['sessoes']:,.0f}", "delta": ga4_data['delta_sessoes']},
    {"icon": "👥", "label": "Visitantes únicos", "value": f"{ga4_data['usuarios']:,.0f}", "delta": ga4_data['delta_usuarios']},
    {"icon": "📄", "label": "Páginas visualizadas", "value": f"{ga4_data['pageviews']:,.0f}", "delta": ga4_data['delta_pageviews']},
    {"icon": "⚡", "label": "Taxa de engajamento", "value": f"{ga4_data['taxa_engajamento']:.1f}%", "delta": ga4_data['delta_engajamento']},
    {"icon": "⏱️", "label": "Tempo médio no site", "value": ga4_data['tempo_medio'], "delta": None, "suffix": ""},
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
            st.markdown('<div class="table-header"><span class="table-header-title">De onde vieram os visitantes (anúncios pagos)</span></div>', unsafe_allow_html=True)

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
            <div class="empty-state" style="background:{LIA["bg_card"]};border-radius:20px;padding:20px;text-align:center;border:1px dashed {LIA["border"]};backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);">
                <p style="color:{LIA["text_secondary"]};margin:0;">Nenhuma origem de tráfego paga encontrada no período.</p>
            </div>
        ''', unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Erro ao renderizar tabela de origem/midia: {e}")

with table_cols[1]:
    # Card: Eventos da Landing (GA4) com fallback seguro
    try:
        card_status = landing_events_card_data.get("status", "unavailable")
        if card_status == "ok":
            st.markdown('<div class="table-container">', unsafe_allow_html=True)
            st.markdown('<div class="table-header"><span class="table-header-title">Eventos da Landing (GA4)</span></div>', unsafe_allow_html=True)

            kpi_cols = st.columns(3)
            with kpi_cols[0]:
                st.metric("Total de eventos", f"{landing_events_card_data.get('kpi_total_events', 0):,}".replace(',', '.'))
            with kpi_cols[1]:
                st.metric("Usuários impactados", f"{landing_events_card_data.get('kpi_total_users', 0):,}".replace(',', '.'))
            with kpi_cols[2]:
                st.metric("Conversões GA4", f"{landing_events_card_data.get('kpi_total_conversions', 0):,.0f}".replace(',', '.'))

            table_df = landing_events_card_data.get("table", pd.DataFrame()).copy()
            if not table_df.empty:
                table_df = table_df.rename(columns={
                    "Evento": "Evento",
                    "Contagem": "Contagem",
                    "Usuários": "Usuários",
                    "Conversões": "Conversões",
                })
                st.dataframe(table_df, use_container_width=True, hide_index=True)

            if landing_events_card_data.get("has_key_events"):
                mapped = landing_events_card_data.get("key_event_totals", {})
                mapped_text = " | ".join([f"{k}: {v:,}".replace(',', '.') for k, v in mapped.items()])
                st.caption(f"Eventos-chave mapeados: {mapped_text}")
            else:
                st.caption("Conversões não configuradas no GA4 para os eventos-chave (generate_lead, form_submit, whatsapp_click, page_view).")

            if not landing_events_card_data.get("has_conversions"):
                st.caption("Conversões não configuradas no GA4 (métrica conversions = 0 no período).")

            if landing_events_card_data.get("landing_host_filter"):
                st.caption(f"Filtro de host da landing: {landing_events_card_data['landing_host_filter']}")
            if landing_events_card_data.get("date_range"):
                st.caption(f"Período GA4: {landing_events_card_data['date_range']}")

            st.markdown('</div>', unsafe_allow_html=True)
        elif card_status == "no_data":
            st.markdown('<div class="table-container">', unsafe_allow_html=True)
            st.markdown('<div class="table-header"><span class="table-header-title">Eventos da Landing (GA4)</span></div>', unsafe_allow_html=True)
            st.info(landing_events_card_data.get("message", "Sem dados no período."))
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="table-container">', unsafe_allow_html=True)
            st.markdown('<div class="table-header"><span class="table-header-title">Eventos (em desenvolvimento)</span></div>', unsafe_allow_html=True)
            st.markdown(
                "Integração GA4/Meta em configuração. Este bloco será ativado quando GA4_PROPERTY_ID e credenciais estiverem válidos."
            )
            checklist = landing_events_card_data.get("checklist", [
                "Adicionar a service account como Viewer na propriedade GA4",
                "Setar GA4_PROPERTY_ID",
                "Validar eventos da LP",
            ])
            for item in checklist:
                st.markdown(f"- [ ] {item}")

            error_msg = landing_events_card_data.get("error")
            if error_msg and st.session_state.get("show_integration_settings"):
                with st.expander("Detalhes técnicos (operador)", expanded=False):
                    st.code(str(error_msg))
            st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Erro ao renderizar card de eventos da landing: {e}")
st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown('''
<div class="footer glass-card">
    Dashboard Ciclo 2 - <a href="https://applia.ai" target="_blank">LIA App</a> - Atualizado em tempo real
</div>
''', unsafe_allow_html=True)

# Fechar camada de conteudo
st.markdown('</div>', unsafe_allow_html=True)
