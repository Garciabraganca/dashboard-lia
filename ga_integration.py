"""
Integração com Google Analytics 4 API para obter dados de sessões e eventos
"""

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest,
    Dimension,
    Metric,
    DateRange,
    FilterExpression,
    Filter,
)
from google.oauth2 import service_account
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class GA4Integration:
    def __init__(self, credentials_json: Dict[str, Any], property_id: str):
        """
        Inicializa a integração com Google Analytics 4 API

        Args:
            credentials_json: Dicionário com credenciais da service account
            property_id: ID da propriedade GA4
        """
        self.property_id = property_id

        # Criar credenciais
        self.credentials = service_account.Credentials.from_service_account_info(
            credentials_json,
            scopes=['https://www.googleapis.com/auth/analytics.readonly']
        )

        # Inicializar cliente
        self.client = BetaAnalyticsDataClient(credentials=self.credentials)

    def _build_campaign_filter(self, campaign_filter: str) -> FilterExpression:
        """
        Cria filtro por campanha (utm_campaign) para as queries GA4

        Args:
            campaign_filter: Nome da campanha para filtrar (ex: "Ciclo 2")

        Returns:
            FilterExpression para usar na query
        """
        return FilterExpression(
            filter=Filter(
                field_name="sessionCampaignName",
                string_filter=Filter.StringFilter(
                    match_type=Filter.StringFilter.MatchType.CONTAINS,
                    value=campaign_filter,
                    case_sensitive=False
                )
            )
        )

    def _get_date_range(self, date_range: str, custom_start: str = None, custom_end: str = None) -> tuple:
        """
        Calcula o período de datas com base no range especificado

        Args:
            date_range: Período (last_7d, last_14d, last_30d, today, yesterday, custom)
            custom_start: Data de início personalizada (YYYY-MM-DD) - usado quando date_range="custom"
            custom_end: Data de fim personalizada (YYYY-MM-DD) - usado quando date_range="custom"

        Returns:
            Tupla com (start_date_str, end_date_str)
        """
        if date_range == "custom" and custom_start and custom_end:
            return custom_start, custom_end

        end_date = datetime.now()

        if date_range == "last_7d":
            start_date = end_date - timedelta(days=7)
        elif date_range == "last_14d":
            start_date = end_date - timedelta(days=14)
        elif date_range == "last_30d":
            start_date = end_date - timedelta(days=30)
        elif date_range == "today":
            start_date = end_date.replace(hour=0, minute=0, second=0)
        elif date_range == "yesterday":
            start_date = (end_date - timedelta(days=1)).replace(hour=0, minute=0, second=0)
            end_date = end_date.replace(hour=0, minute=0, second=0)
        else:
            start_date = end_date - timedelta(days=7)

        return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

    def get_sessions_data(self, date_range: str = "last_7d", custom_start: str = None, custom_end: str = None) -> pd.DataFrame:
        """
        Obtém dados de sessões do GA4

        Args:
            date_range: Período (last_7d, last_14d, last_30d, today, yesterday, custom)
            custom_start: Data de início personalizada (YYYY-MM-DD) - usado quando date_range="custom"
            custom_end: Data de fim personalizada (YYYY-MM-DD) - usado quando date_range="custom"

        Returns:
            DataFrame com dados de sessões
        """
        try:
            start_date_str, end_date_str = self._get_date_range(date_range, custom_start, custom_end)

            # Criar requisição
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[DateRange(start_date=start_date_str, end_date=end_date_str)],
                dimensions=[
                    Dimension(name="date"),
                    Dimension(name="sessionSourceMedium"),
                ],
                metrics=[
                    Metric(name="sessions"),
                    Metric(name="totalUsers"),
                    Metric(name="screenPageViews"),
                    Metric(name="engagementRate"),
                    Metric(name="bounceRate"),
                ],
            )

            # Executar requisição
            response = self.client.run_report(request)

            # Converter para DataFrame
            data = []
            for row in response.rows:
                data.append({
                    'date': row.dimension_values[0].value,
                    'source_medium': row.dimension_values[1].value,
                    'sessions': int(row.metric_values[0].value),
                    'users': int(row.metric_values[1].value),
                    'pageviews': int(row.metric_values[2].value),
                    'engagement_rate': float(row.metric_values[3].value),
                    'bounce_rate': float(row.metric_values[4].value),
                })

            return pd.DataFrame(data)

        except Exception as e:
            logger.error(f"Erro ao obter dados do GA4: {str(e)}")
            return pd.DataFrame()

    def get_events_data(self, date_range: str = "last_7d", custom_start: str = None, custom_end: str = None, campaign_filter: str = None) -> pd.DataFrame:
        """
        Obtém dados de eventos do GA4 com métricas detalhadas

        Args:
            date_range: Período (last_7d, last_14d, last_30d, today, yesterday, custom)
            custom_start: Data de início personalizada (YYYY-MM-DD) - usado quando date_range="custom"
            custom_end: Data de fim personalizada (YYYY-MM-DD) - usado quando date_range="custom"
            campaign_filter: Filtro por nome da campanha (utm_campaign)

        Returns:
            DataFrame com dados de eventos incluindo:
            - Nome do evento
            - Contagem de eventos (com % do total)
            - Total de usuários (com % do total)
            - Contagem de eventos por usuário ativo
            - Receita total
        """
        try:
            start_date_str, end_date_str = self._get_date_range(date_range, custom_start, custom_end)

            # Criar requisição com métricas detalhadas
            request_params = {
                "property": f"properties/{self.property_id}",
                "date_ranges": [DateRange(start_date=start_date_str, end_date=end_date_str)],
                "dimensions": [
                    Dimension(name="eventName"),
                ],
                "metrics": [
                    Metric(name="eventCount"),
                    Metric(name="totalUsers"),
                    Metric(name="eventCountPerUser"),
                    Metric(name="eventValue"),
                ],
            }

            # Adicionar filtro de campanha se especificado
            if campaign_filter:
                request_params["dimension_filter"] = self._build_campaign_filter(campaign_filter)

            request = RunReportRequest(**request_params)

            # Executar requisição
            response = self.client.run_report(request)

            # Converter para DataFrame
            data = []
            for row in response.rows:
                data.append({
                    'event_name': row.dimension_values[0].value,
                    'event_count': int(row.metric_values[0].value),
                    'total_users': int(row.metric_values[1].value),
                    'events_per_user': float(row.metric_values[2].value),
                    'event_value': float(row.metric_values[3].value),
                })

            df = pd.DataFrame(data)

            if not df.empty:
                # Calcular totais para percentuais
                total_events = df['event_count'].sum()
                total_users = df['total_users'].max()  # Usuários únicos totais

                # Adicionar colunas de percentual
                df['event_count_pct'] = (df['event_count'] / total_events * 100).round(2)
                df['users_pct'] = (df['total_users'] / total_users * 100).round(2) if total_users > 0 else 0

                # Ordenar por contagem de eventos (descendente)
                df = df.sort_values('event_count', ascending=False)

            return df

        except Exception as e:
            logger.error(f"Erro ao obter eventos do GA4: {str(e)}")
            return pd.DataFrame()

    def get_aggregated_metrics(self, date_range: str = "last_7d", custom_start: str = None, custom_end: str = None, campaign_filter: str = None) -> Dict[str, Any]:
        """
        Obtém métricas agregadas do GA4 para uso no dashboard

        Args:
            date_range: Período (last_7d, last_14d, last_30d, today, yesterday, custom)
            custom_start: Data de início personalizada (YYYY-MM-DD) - usado quando date_range="custom"
            custom_end: Data de fim personalizada (YYYY-MM-DD) - usado quando date_range="custom"
            campaign_filter: Filtro por nome da campanha (utm_campaign)

        Returns:
            Dicionário com métricas agregadas
        """
        try:
            start_date_str, end_date_str = self._get_date_range(date_range, custom_start, custom_end)

            # Criar requisição para métricas agregadas
            request_params = {
                "property": f"properties/{self.property_id}",
                "date_ranges": [DateRange(start_date=start_date_str, end_date=end_date_str)],
                "metrics": [
                    Metric(name="sessions"),
                    Metric(name="totalUsers"),
                    Metric(name="screenPageViews"),
                    Metric(name="engagementRate"),
                    Metric(name="averageSessionDuration"),
                ],
            }

            # Adicionar filtro de campanha se especificado
            if campaign_filter:
                request_params["dimension_filter"] = self._build_campaign_filter(campaign_filter)

            request = RunReportRequest(**request_params)

            # Executar requisição
            response = self.client.run_report(request)

            if response.rows:
                row = response.rows[0]
                avg_duration = float(row.metric_values[4].value)
                minutes = int(avg_duration // 60)
                seconds = int(avg_duration % 60)

                return {
                    'sessoes': int(row.metric_values[0].value),
                    'usuarios': int(row.metric_values[1].value),
                    'pageviews': int(row.metric_values[2].value),
                    'taxa_engajamento': float(row.metric_values[3].value) * 100,
                    'tempo_medio': f"{minutes}m {seconds}s",
                }

            return self._empty_metrics()

        except Exception as e:
            logger.error(f"Erro ao obter métricas agregadas do GA4: {str(e)}")
            return self._empty_metrics()

    def get_source_medium_data(self, date_range: str = "last_7d", custom_start: str = None, custom_end: str = None, campaign_filter: str = None) -> pd.DataFrame:
        """
        Obtém dados de origem/mídia do GA4

        Args:
            date_range: Período (last_7d, last_14d, last_30d, today, yesterday, custom)
            custom_start: Data de início personalizada (YYYY-MM-DD) - usado quando date_range="custom"
            custom_end: Data de fim personalizada (YYYY-MM-DD) - usado quando date_range="custom"
            campaign_filter: Filtro por nome da campanha (utm_campaign)

        Returns:
            DataFrame com dados de origem/mídia
        """
        try:
            start_date_str, end_date_str = self._get_date_range(date_range, custom_start, custom_end)

            # Criar requisição
            request_params = {
                "property": f"properties/{self.property_id}",
                "date_ranges": [DateRange(start_date=start_date_str, end_date=end_date_str)],
                "dimensions": [
                    Dimension(name="sessionSourceMedium"),
                ],
                "metrics": [
                    Metric(name="sessions"),
                    Metric(name="totalUsers"),
                    Metric(name="engagementRate"),
                    Metric(name="averageSessionDuration"),
                ],
            }

            # Adicionar filtro de campanha se especificado
            if campaign_filter:
                request_params["dimension_filter"] = self._build_campaign_filter(campaign_filter)

            request = RunReportRequest(**request_params)

            # Executar requisição
            response = self.client.run_report(request)

            # Converter para DataFrame
            data = []
            for row in response.rows:
                avg_duration = float(row.metric_values[3].value)
                minutes = int(avg_duration // 60)
                seconds = int(avg_duration % 60)

                data.append({
                    'Origem / Midia': row.dimension_values[0].value,
                    'Sessoes': int(row.metric_values[0].value),
                    'Usuarios': int(row.metric_values[1].value),
                    'Engajamento': f"{float(row.metric_values[2].value) * 100:.1f}%",
                    'Tempo Medio': f"{minutes}m {seconds:02d}s",
                })

            df = pd.DataFrame(data)
            if df.empty:
                return df
            return df.sort_values('Sessoes', ascending=False).head(10)

        except Exception as e:
            logger.error(f"Erro ao obter dados de origem/mídia do GA4: {str(e)}")
            return pd.DataFrame()

    def get_available_campaigns(self, date_range: str = "last_30d", custom_start: str = None, custom_end: str = None) -> pd.DataFrame:
        """
        Obtém lista de campanhas (utm_campaign) disponíveis no GA4
        Útil para diagnóstico e verificação de UTMs

        Args:
            date_range: Período (last_7d, last_14d, last_30d, today, yesterday, custom)
            custom_start: Data de início personalizada (YYYY-MM-DD)
            custom_end: Data de fim personalizada (YYYY-MM-DD)

        Returns:
            DataFrame com campanhas e suas sessões
        """
        try:
            start_date_str, end_date_str = self._get_date_range(date_range, custom_start, custom_end)

            # Criar requisição para listar campanhas
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[DateRange(start_date=start_date_str, end_date=end_date_str)],
                dimensions=[
                    Dimension(name="sessionCampaignName"),
                ],
                metrics=[
                    Metric(name="sessions"),
                    Metric(name="totalUsers"),
                ],
            )

            # Executar requisição
            response = self.client.run_report(request)

            # Converter para DataFrame
            data = []
            for row in response.rows:
                campaign_name = row.dimension_values[0].value
                # Ignorar campanhas vazias ou "(not set)"
                if campaign_name and campaign_name not in ['(not set)', '(direct)']:
                    data.append({
                        'campaign': campaign_name,
                        'sessions': int(row.metric_values[0].value),
                        'users': int(row.metric_values[1].value),
                    })

            df = pd.DataFrame(data)
            if not df.empty:
                df = df.sort_values('sessions', ascending=False)
            return df

        except Exception as e:
            logger.error(f"Erro ao obter campanhas do GA4: {str(e)}")
            return pd.DataFrame()

    def diagnose_utm_tracking(self, campaign_filter: str = None, date_range: str = "last_7d", custom_start: str = None, custom_end: str = None) -> Dict[str, Any]:
        """
        Diagnóstico completo do tracking de UTMs no GA4

        Args:
            campaign_filter: Nome da campanha para verificar
            date_range: Período
            custom_start: Data de início personalizada
            custom_end: Data de fim personalizada

        Returns:
            Dicionário com informações de diagnóstico
        """
        try:
            start_date_str, end_date_str = self._get_date_range(date_range, custom_start, custom_end)

            # 1. Verificar conexão básica (total de sessões)
            basic_request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[DateRange(start_date=start_date_str, end_date=end_date_str)],
                metrics=[
                    Metric(name="sessions"),
                ],
            )
            basic_response = self.client.run_report(basic_request)
            total_sessions = int(basic_response.rows[0].metric_values[0].value) if basic_response.rows else 0

            # 2. Obter campanhas disponíveis
            available_campaigns = self.get_available_campaigns(date_range, custom_start, custom_end)

            # 3. Verificar se o filtro específico existe
            filter_match = None
            sessions_with_filter = 0
            if campaign_filter and not available_campaigns.empty:
                # Buscar matches parciais (case insensitive)
                matches = available_campaigns[
                    available_campaigns['campaign'].str.lower().str.contains(campaign_filter.lower(), na=False)
                ]
                if not matches.empty:
                    filter_match = matches.to_dict('records')
                    sessions_with_filter = matches['sessions'].sum()

            # 4. Obter dados com o filtro aplicado
            if campaign_filter:
                filtered_metrics = self.get_aggregated_metrics(date_range, custom_start, custom_end, campaign_filter)
            else:
                filtered_metrics = None

            return {
                'connected': True,
                'date_range': f"{start_date_str} to {end_date_str}",
                'total_sessions': total_sessions,
                'available_campaigns': available_campaigns.to_dict('records') if not available_campaigns.empty else [],
                'campaign_filter_used': campaign_filter,
                'filter_matches': filter_match,
                'sessions_with_filter': sessions_with_filter,
                'filtered_metrics': filtered_metrics,
                'status': 'ok' if sessions_with_filter > 0 else 'no_data_for_filter'
            }

        except Exception as e:
            logger.error(f"Erro no diagnóstico GA4: {str(e)}")
            return {
                'connected': False,
                'error': str(e),
                'status': 'error'
            }

    def _empty_metrics(self) -> Dict[str, Any]:
        """Retorna métricas vazias em caso de erro"""
        return {
            'sessoes': 0,
            'usuarios': 0,
            'pageviews': 0,
            'taxa_engajamento': 0,
            'tempo_medio': "0m 0s",
        }
