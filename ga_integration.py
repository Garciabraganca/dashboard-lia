"""
Integração com Google Analytics 4 API para obter dados de sessões e eventos
"""

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest,
    Dimension,
    Metric,
    DateRange,
)
from google.oauth2 import service_account
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
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

    def _get_date_range(self, date_range: str) -> tuple:
        """
        Calcula o período de datas com base no range especificado

        Args:
            date_range: Período (last_7d, last_14d, today, yesterday)

        Returns:
            Tupla com (start_date_str, end_date_str)
        """
        end_date = datetime.now()

        if date_range == "last_7d":
            start_date = end_date - timedelta(days=7)
        elif date_range == "last_14d":
            start_date = end_date - timedelta(days=14)
        elif date_range == "today":
            start_date = end_date.replace(hour=0, minute=0, second=0)
        elif date_range == "yesterday":
            start_date = (end_date - timedelta(days=1)).replace(hour=0, minute=0, second=0)
            end_date = end_date.replace(hour=0, minute=0, second=0)
        else:
            start_date = end_date - timedelta(days=7)

        return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

    def get_sessions_data(self, date_range: str = "last_7d") -> pd.DataFrame:
        """
        Obtém dados de sessões do GA4

        Args:
            date_range: Período (last_7d, last_14d, today, yesterday)

        Returns:
            DataFrame com dados de sessões
        """
        try:
            start_date_str, end_date_str = self._get_date_range(date_range)

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

    def get_events_data(self, date_range: str = "last_7d") -> pd.DataFrame:
        """
        Obtém dados de eventos do GA4

        Args:
            date_range: Período (last_7d, last_14d, today, yesterday)

        Returns:
            DataFrame com dados de eventos
        """
        try:
            start_date_str, end_date_str = self._get_date_range(date_range)

            # Criar requisição
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[DateRange(start_date=start_date_str, end_date=end_date_str)],
                dimensions=[
                    Dimension(name="date"),
                    Dimension(name="eventName"),
                ],
                metrics=[
                    Metric(name="eventCount"),
                    Metric(name="eventValue"),
                ],
            )

            # Executar requisição
            response = self.client.run_report(request)

            # Converter para DataFrame
            data = []
            for row in response.rows:
                data.append({
                    'date': row.dimension_values[0].value,
                    'event_name': row.dimension_values[1].value,
                    'event_count': int(row.metric_values[0].value),
                    'event_value': float(row.metric_values[1].value),
                })

            return pd.DataFrame(data)

        except Exception as e:
            logger.error(f"Erro ao obter eventos do GA4: {str(e)}")
            return pd.DataFrame()

    def get_aggregated_metrics(self, date_range: str = "last_7d") -> Dict[str, Any]:
        """
        Obtém métricas agregadas do GA4 para uso no dashboard

        Args:
            date_range: Período (last_7d, last_14d, today, yesterday)

        Returns:
            Dicionário com métricas agregadas
        """
        try:
            start_date_str, end_date_str = self._get_date_range(date_range)

            # Criar requisição para métricas agregadas
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[DateRange(start_date=start_date_str, end_date=end_date_str)],
                metrics=[
                    Metric(name="sessions"),
                    Metric(name="totalUsers"),
                    Metric(name="screenPageViews"),
                    Metric(name="engagementRate"),
                    Metric(name="averageSessionDuration"),
                ],
            )

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

    def get_source_medium_data(self, date_range: str = "last_7d") -> pd.DataFrame:
        """
        Obtém dados de origem/mídia do GA4

        Args:
            date_range: Período (last_7d, last_14d, today, yesterday)

        Returns:
            DataFrame com dados de origem/mídia
        """
        try:
            start_date_str, end_date_str = self._get_date_range(date_range)

            # Criar requisição
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[DateRange(start_date=start_date_str, end_date=end_date_str)],
                dimensions=[
                    Dimension(name="sessionSourceMedium"),
                ],
                metrics=[
                    Metric(name="sessions"),
                    Metric(name="totalUsers"),
                    Metric(name="engagementRate"),
                    Metric(name="averageSessionDuration"),
                ],
            )

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
            return df.sort_values('Sessoes', ascending=False).head(10)

        except Exception as e:
            logger.error(f"Erro ao obter dados de origem/mídia do GA4: {str(e)}")
            return pd.DataFrame()

    def _empty_metrics(self) -> Dict[str, Any]:
        """Retorna métricas vazias em caso de erro"""
        return {
            'sessoes': 0,
            'usuarios': 0,
            'pageviews': 0,
            'taxa_engajamento': 0,
            'tempo_medio': "0m 0s",
        }
