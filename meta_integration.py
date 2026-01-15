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

    def verify_connection(self) -> Dict[str, Any]:
        """
        Verifica a conexão com a API Meta Ads

        Returns:
            Dicionário com status da conexão:
            - connected: bool - se a conexão foi bem sucedida
            - message: str - mensagem descritiva do status
            - account_info: dict - informações da conta (se conectado)
            - error_code: str - código do erro (se houver)
            - error_details: str - detalhes do erro (se houver)
        """
        result = {
            "connected": False,
            "message": "",
            "account_info": {},
            "error_code": None,
            "error_details": None
        }

        # Verificar se token está configurado
        if not self.access_token:
            result["message"] = "Token de acesso não configurado"
            result["error_code"] = "NO_TOKEN"
            return result

        # Verificar se account_id está configurado
        if not self.ad_account_id:
            result["message"] = "ID da conta de anúncios não configurado"
            result["error_code"] = "NO_ACCOUNT_ID"
            return result

        try:
            # Fazer chamada para obter informações da conta
            url = f"{self.base_url}/{self.ad_account_id}"
            params = {
                "fields": "id,name,account_status,currency,timezone_name,business_name",
                "access_token": self.access_token
            }

            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()

                # Mapear status da conta
                account_status_map = {
                    1: "ACTIVE",
                    2: "DISABLED",
                    3: "UNSETTLED",
                    7: "PENDING_RISK_REVIEW",
                    8: "PENDING_SETTLEMENT",
                    9: "IN_GRACE_PERIOD",
                    100: "PENDING_CLOSURE",
                    101: "CLOSED",
                    201: "ANY_ACTIVE",
                    202: "ANY_CLOSED"
                }

                status_code = data.get("account_status", 0)
                status_name = account_status_map.get(status_code, f"UNKNOWN ({status_code})")

                result["connected"] = True
                result["message"] = "Conexão estabelecida com sucesso"
                result["account_info"] = {
                    "id": data.get("id", "").replace("act_", ""),
                    "name": data.get("name", "N/A"),
                    "business_name": data.get("business_name", "N/A"),
                    "status": status_name,
                    "status_code": status_code,
                    "currency": data.get("currency", "N/A"),
                    "timezone": data.get("timezone_name", "N/A")
                }
            else:
                error_data = response.json() if response.text else {}
                error = error_data.get('error', {})
                error_msg = error.get('message', 'Erro desconhecido')
                error_code = error.get('code', 'N/A')
                error_type = error.get('type', 'N/A')

                result["message"] = f"Erro na API Meta: {error_msg}"
                result["error_code"] = str(error_code)
                result["error_details"] = f"Type: {error_type}, Code: {error_code}"

                # Mensagens amigáveis para erros comuns
                if error_code == 190:
                    result["message"] = "Token de acesso inválido ou expirado"
                elif error_code == 100:
                    result["message"] = "ID da conta de anúncios inválido ou sem permissão"
                elif error_code == 17:
                    result["message"] = "Limite de requisições excedido (rate limit)"

        except requests.exceptions.Timeout:
            result["message"] = "Timeout na conexão com a API Meta"
            result["error_code"] = "TIMEOUT"
            result["error_details"] = "A requisição excedeu o tempo limite de 30 segundos"

        except requests.exceptions.ConnectionError as e:
            result["message"] = "Erro de conexão com a API Meta"
            result["error_code"] = "CONNECTION_ERROR"
            result["error_details"] = str(e)

        except Exception as e:
            result["message"] = f"Erro inesperado: {str(e)}"
            result["error_code"] = "UNKNOWN_ERROR"
            result["error_details"] = str(e)

        return result

    def _parse_date_range(self, date_range: str, custom_start: str = None, custom_end: str = None) -> tuple:
        """
        Converte o período para datas de início e fim

        Args:
            date_range: Período (last_7d, last_14d, today, yesterday, custom)
            custom_start: Data de início personalizada (YYYY-MM-DD)
            custom_end: Data de fim personalizada (YYYY-MM-DD)

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

    def get_campaigns(self, date_range: str = "last_7d", custom_start: str = None, custom_end: str = None) -> pd.DataFrame:
        """
        Obtém dados de campanhas do Meta Ads

        Args:
            date_range: Período (last_7d, last_14d, last_30d, today, yesterday, custom)
            custom_start: Data de início personalizada (YYYY-MM-DD) - usado quando date_range="custom"
            custom_end: Data de fim personalizada (YYYY-MM-DD) - usado quando date_range="custom"

        Returns:
            DataFrame com dados das campanhas
        """
        try:
            # Definir datas com base no período
            start_date_str, end_date_str = self._parse_date_range(date_range, custom_start, custom_end)

            # Buscar campanhas (removido filtro de apenas ativas para ver histórico)
            url = f"{self.base_url}/{self.ad_account_id}/campaigns"
            params = {
                "fields": "id,name,status,effective_status",
                # "filtering": "[{'field':'effective_status','operator':'IN','value':['ACTIVE']}]",
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

    def get_ad_insights(self, date_range: str = "last_7d", fields: List[str] = None, campaign_name_filter: str = None, custom_start: str = None, custom_end: str = None) -> pd.DataFrame:
        """
        Obtém insights de anúncios do Meta

        Args:
            date_range: Período (last_7d, last_14d, last_30d, today, yesterday, custom)
            fields: Lista de campos a recuperar
            campaign_name_filter: Nome da campanha para filtrar (opcional)
            custom_start: Data de início personalizada (YYYY-MM-DD) - usado quando date_range="custom"
            custom_end: Data de fim personalizada (YYYY-MM-DD) - usado quando date_range="custom"

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
            start_date_str, end_date_str = self._parse_date_range(date_range, custom_start, custom_end)

            # Buscar insights apenas de campanhas ATIVAS
            url = f"{self.base_url}/{self.ad_account_id}/insights"
            params = {
                "fields": ",".join(fields),
                "time_range": f"{{'since':'{start_date_str}','until':'{end_date_str}'}}",
                "time_increment": "1",
                "level": "campaign",
                # "filtering": "[{'field':'campaign.effective_status','operator':'IN','value':['ACTIVE']}]",
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

    def get_creative_insights(self, date_range: str = "last_7d", campaign_name_filter: str = None, custom_start: str = None, custom_end: str = None) -> pd.DataFrame:
        """
        Obtém insights por criativo/anúncio do Meta

        Args:
            date_range: Período (last_7d, last_14d, last_30d, today, yesterday, custom)
            campaign_name_filter: Nome da campanha para filtrar (opcional)
            custom_start: Data de início personalizada (YYYY-MM-DD) - usado quando date_range="custom"
            custom_end: Data de fim personalizada (YYYY-MM-DD) - usado quando date_range="custom"

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
            start_date_str, end_date_str = self._parse_date_range(date_range, custom_start, custom_end)

            # Buscar insights no nível de anúncio
            url = f"{self.base_url}/{self.ad_account_id}/insights"
            params = {
                "fields": ",".join(fields),
                "time_range": f"{{'since':'{start_date_str}','until':'{end_date_str}'}}",
                "level": "ad",
                # "filtering": "[{'field':'ad.effective_status','operator':'IN','value':['ACTIVE']}]",
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
