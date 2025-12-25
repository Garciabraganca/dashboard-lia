"""
Integração com Meta Ads API para obter dados de campanhas
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd


class MetaAdsIntegration:
    def __init__(self, access_token: str, ad_account_id: str):
        """
        Inicializa a integração com Meta Ads API

        Args:
            access_token: Token de acesso do Meta
            ad_account_id: ID da conta de anúncios (sem 'act_' prefix)
        """
        self.access_token = access_token
        self.ad_account_id = f"act_{ad_account_id}" if not ad_account_id.startswith("act_") else ad_account_id
        self.base_url = "https://graph.facebook.com/v21.0"

    def get_campaigns(self, date_range: str = "last_7d") -> pd.DataFrame:
        """
        Obtém dados de campanhas do Meta Ads

        Args:
            date_range: Período (last_7d, last_14d, today, yesterday)

        Returns:
            DataFrame com dados das campanhas
        """
        try:
            # Definir datas com base no período
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

            # Formatar datas
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")

            # Buscar apenas campanhas ATIVAS
            url = f"{self.base_url}/{self.ad_account_id}/campaigns"
            params = {
                "fields": "id,name,status,effective_status",
                "filtering": "[{'field':'effective_status','operator':'IN','value':['ACTIVE']}]",
                "access_token": self.access_token
            }

            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            campaigns = data.get("data", [])

            # Converter para DataFrame
            df = pd.DataFrame(campaigns)

            # Converter valores numéricos
            numeric_columns = ['spend', 'impressions', 'reach', 'frequency', 'clicks', 'ctr', 'cpc', 'cpm']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            return df

        except Exception as e:
            print(f"Erro ao obter campanhas do Meta: {str(e)}")
            return pd.DataFrame()

    def get_ad_insights(self, date_range: str = "last_7d", fields: List[str] = None, campaign_name_filter: str = None) -> pd.DataFrame:
        """
        Obtém insights de anúncios do Meta

        Args:
            date_range: Período (last_7d, last_14d, today, yesterday)
            fields: Lista de campos a recuperar
            campaign_name_filter: Nome da campanha para filtrar (opcional)

        Returns:
            DataFrame com dados de insights
        """
        if fields is None:
            fields = [
                "campaign_id",
                "campaign_name",
                "spend",
                "impressions",
                "reach",
                "frequency",
                "clicks",
                "ctr",
                "cpc",
                "cpm",
                "date_start"
            ]

        try:
            # Definir datas
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

            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")

            # Buscar insights apenas de campanhas ATIVAS
            url = f"{self.base_url}/{self.ad_account_id}/insights"
            params = {
                "fields": ",".join(fields),
                "time_range": f"{{'since':'{start_date_str}','until':'{end_date_str}'}}",
                "time_increment": "1",
                "level": "campaign",
                "filtering": "[{'field':'campaign.effective_status','operator':'IN','value':['ACTIVE']}]",
                "access_token": self.access_token
            }

            response = requests.get(url, params=params)

            # Log detalhado para debug
            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                error_code = error_data.get('error', {}).get('code', 'N/A')
                print(f"Meta API Error {response.status_code}: Code={error_code}, Message={error_msg}")
                print(f"URL: {url}")
                print(f"Ad Account: {self.ad_account_id}")

            response.raise_for_status()

            data = response.json()
            insights = data.get("data", [])

            # Converter para DataFrame
            df = pd.DataFrame(insights)

            # Filtrar por nome da campanha se especificado
            if campaign_name_filter and not df.empty and 'campaign_name' in df.columns:
                df = df[df['campaign_name'].str.contains(campaign_name_filter, case=False, na=False)]

            # Converter valores numéricos
            numeric_fields = ['spend', 'impressions', 'reach', 'frequency', 'clicks', 'ctr', 'cpc', 'cpm']
            for col in numeric_fields:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            return df

        except Exception as e:
            print(f"Erro ao obter insights do Meta: {str(e)}")
            return pd.DataFrame()

    def get_creative_insights(self, date_range: str = "last_7d", campaign_name_filter: str = None) -> pd.DataFrame:
        """
        Obtém insights por criativo/anúncio do Meta

        Args:
            date_range: Período (last_7d, last_14d, today, yesterday)
            campaign_name_filter: Nome da campanha para filtrar (opcional)

        Returns:
            DataFrame com dados de criativos
        """
        fields = [
            "ad_id",
            "ad_name",
            "campaign_name",
            "spend",
            "impressions",
            "clicks",
            "ctr",
            "cpc",
            "cpm"
        ]

        try:
            # Definir datas
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

            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")

            # Buscar insights no nível de anúncio
            url = f"{self.base_url}/{self.ad_account_id}/insights"
            params = {
                "fields": ",".join(fields),
                "time_range": f"{{'since':'{start_date_str}','until':'{end_date_str}'}}",
                "level": "ad",
                "filtering": "[{'field':'ad.effective_status','operator':'IN','value':['ACTIVE']}]",
                "access_token": self.access_token
            }

            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            insights = data.get("data", [])

            df = pd.DataFrame(insights)

            # Filtrar por campanha se especificado
            if campaign_name_filter and not df.empty and 'campaign_name' in df.columns:
                df = df[df['campaign_name'].str.contains(campaign_name_filter, case=False, na=False)]

            # Converter valores numéricos
            numeric_fields = ['spend', 'impressions', 'clicks', 'ctr', 'cpc', 'cpm']
            for col in numeric_fields:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            return df

        except Exception as e:
            print(f"Erro ao obter insights de criativos: {str(e)}")
            return pd.DataFrame()
