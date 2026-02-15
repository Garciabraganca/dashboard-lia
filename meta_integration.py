"""
Integração com Meta Ads API para obter dados de campanhas
"""

import json
import logging
import requests
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd

logger = logging.getLogger(__name__)


class MetaAdsIntegration:
    def __init__(self, access_token: str, ad_account_id: str, app_id: str = None):
        """
        Inicializa a integração com Meta Ads API

        Args:
            access_token: Token de acesso do Meta
            ad_account_id: ID da conta de anúncios (sem 'act_' prefix)
            app_id: ID do aplicativo Meta (para consultar eventos do SDK)
        """
        self.access_token = access_token
        self.ad_account_id = f"act_{ad_account_id}" if not ad_account_id.startswith("act_") else ad_account_id
        self.app_id = app_id
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

        Nota: Os períodos "last_Xd" incluem o dia de hoje.
        - "last_7d" = hoje e os 6 dias anteriores (7 dias no total)
        - "last_14d" = hoje e os 13 dias anteriores (14 dias no total)
        - "last_30d" = hoje e os 29 dias anteriores (30 dias no total)
        """
        if date_range == "custom" and custom_start and custom_end:
            return custom_start, custom_end

        today = datetime.now().date()

        if date_range == "last_7d":
            # Últimos 7 dias incluindo hoje: hoje - 6 dias até hoje
            start_date = today - timedelta(days=6)
            end_date = today
        elif date_range == "last_14d":
            # Últimos 14 dias incluindo hoje: hoje - 13 dias até hoje
            start_date = today - timedelta(days=13)
            end_date = today
        elif date_range == "last_30d":
            # Últimos 30 dias incluindo hoje: hoje - 29 dias até hoje
            start_date = today - timedelta(days=29)
            end_date = today
        elif date_range == "today":
            start_date = today
            end_date = today
        elif date_range == "yesterday":
            # Ontem: apenas o dia de ontem
            yesterday = today - timedelta(days=1)
            start_date = yesterday
            end_date = yesterday
        else:
            # Default: últimos 7 dias
            start_date = today - timedelta(days=6)
            end_date = today

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
                "inline_link_clicks",
                "ctr",
                "cpc",
                "cpm",
                "actions",
                "date_start"
            ]

        try:
            # Definir datas
            start_date_str, end_date_str = self._parse_date_range(date_range, custom_start, custom_end)

            # Buscar insights de todas as campanhas
            url = f"{self.base_url}/{self.ad_account_id}/insights"
            params = {
                "fields": ",".join(fields),
                "time_range": json.dumps({"since": start_date_str, "until": end_date_str}),
                "time_increment": "1",
                "level": "campaign",
                "action_breakdowns": "action_type",
                "limit": "500",
                "access_token": self.access_token
            }

            all_insights = []

            while url:
                response = requests.get(url, params=params if all_insights == [] else None)

                # Log detalhado para debug
                if response.status_code != 200:
                    error_data = response.json() if response.text else {}
                    error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                    error_code = error_data.get('error', {}).get('code', 'N/A')
                    print(f"Meta API Error {response.status_code}: Code={error_code}, Message={error_msg}")
                    print(f"URL: {url}")
                    print(f"Ad Account: {self.ad_account_id}")
                    break

                response.raise_for_status()

                data = response.json()
                insights = data.get("data", [])
                all_insights.extend(insights)

                # Verificar se há mais páginas
                url = data.get("paging", {}).get("next")
                params = None  # Próximas requisições usam a URL completa

            # Converter para DataFrame
            df = pd.DataFrame(all_insights)

            # Filtrar por nome da campanha se especificado
            if campaign_name_filter and not df.empty and 'campaign_name' in df.columns:
                df = df[df['campaign_name'].str.contains(campaign_name_filter, case=False, na=False)]

            # Converter valores numéricos
            numeric_fields = ['spend', 'impressions', 'reach', 'frequency', 'clicks', 'inline_link_clicks', 'ctr', 'cpc', 'cpm']
            for col in numeric_fields:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            return df

        except Exception as e:
            print(f"Erro ao obter insights do Meta: {str(e)}")
            return pd.DataFrame()

    def get_aggregated_insights(self, date_range: str = "last_7d", campaign_name_filter: str = None, custom_start: str = None, custom_end: str = None) -> dict:
        """
        Obtém insights AGREGADOS do período (sem breakdown diário).
        Importante para métricas como Reach que não podem ser somadas diariamente.

        Args:
            date_range: Período (last_7d, last_14d, last_30d, today, yesterday, custom)
            campaign_name_filter: Nome da campanha para filtrar (opcional)
            custom_start: Data de início personalizada (YYYY-MM-DD)
            custom_end: Data de fim personalizada (YYYY-MM-DD)

        Returns:
            Dict com métricas agregadas (reach, frequency, impressions, etc.)
        """
        fields = ["impressions", "reach", "frequency", "spend", "clicks", "ctr", "cpc", "cpm"]

        try:
            start_date_str, end_date_str = self._parse_date_range(date_range, custom_start, custom_end)

            # Buscar insights SEM time_increment para obter valores agregados
            url = f"{self.base_url}/{self.ad_account_id}/insights"
            params = {
                "fields": ",".join(fields),
                "time_range": json.dumps({"since": start_date_str, "until": end_date_str}),
                "level": "account",  # Nível de conta para agregação total
                "access_token": self.access_token
            }

            # Se há filtro de campanha, buscar por campanha e agregar
            if campaign_name_filter:
                params["level"] = "campaign"

            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            insights = data.get("data", [])

            if not insights:
                return {}

            # Se filtro de campanha, filtrar e agregar
            if campaign_name_filter:
                filtered = [i for i in insights if campaign_name_filter.lower() in i.get('campaign_name', '').lower()]
                if not filtered:
                    return {}

                # Se há múltiplas campanhas que match, agregar os dados
                if len(filtered) > 1:
                    # Somar métricas que podem ser somadas
                    total_impressions = sum(int(i.get("impressions", 0)) for i in filtered)
                    total_spend = sum(float(i.get("spend", 0)) for i in filtered)
                    total_clicks = sum(int(i.get("clicks", 0)) for i in filtered)

                    # Para reach: não podemos somar, usar o maior valor como estimativa
                    # (representa o alcance máximo, assumindo sobreposição de público)
                    max_reach = max(int(i.get("reach", 0)) for i in filtered)

                    # Calcular métricas derivadas
                    frequency = total_impressions / max_reach if max_reach > 0 else 0
                    ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
                    cpc = total_spend / total_clicks if total_clicks > 0 else 0
                    cpm = (total_spend / total_impressions * 1000) if total_impressions > 0 else 0

                    return {
                        "reach": max_reach,
                        "frequency": round(frequency, 2),
                        "impressions": total_impressions,
                        "spend": round(total_spend, 2),
                        "clicks": total_clicks,
                        "ctr": round(ctr, 2),
                        "cpc": round(cpc, 2),
                        "cpm": round(cpm, 2),
                    }
                else:
                    insight = filtered[0]
            else:
                insight = insights[0]

            return {
                "reach": int(insight.get("reach", 0)),
                "frequency": float(insight.get("frequency", 0)),
                "impressions": int(insight.get("impressions", 0)),
                "spend": float(insight.get("spend", 0)),
                "clicks": int(insight.get("clicks", 0)),
                "ctr": float(insight.get("ctr", 0)),
                "cpc": float(insight.get("cpc", 0)),
                "cpm": float(insight.get("cpm", 0)),
            }

        except Exception as e:
            print(f"Erro ao obter insights agregados do Meta: {str(e)}")
            return {}

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
                "time_range": json.dumps({"since": start_date_str, "until": end_date_str}),
                "level": "ad",
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

            # Buscar nomes reais dos anúncios (sem filtrar por status)
            # Importante: mostrar todos os criativos que tiveram performance no período,
            # independente do status atual (ativo, pausado, arquivado)
            if not df.empty and 'ad_id' in df.columns:
                try:
                    ad_ids = df['ad_id'].unique().tolist()
                    ad_names_map = {}
                    ad_status_map = {}
                    for ad_id in ad_ids:
                        ad_url = f"{self.base_url}/{ad_id}"
                        ad_params = {
                            "fields": "name,effective_status",
                            "access_token": self.access_token
                        }
                        ad_response = requests.get(ad_url, params=ad_params)
                        if ad_response.status_code == 200:
                            ad_data = ad_response.json()
                            ad_names_map[ad_id] = ad_data.get('name', df[df['ad_id'] == ad_id]['ad_name'].iloc[0])
                            ad_status_map[ad_id] = ad_data.get('effective_status', 'UNKNOWN')

                    # Substituir ad_name pelo nome real do anúncio
                    if ad_names_map and not df.empty:
                        df['ad_name'] = df['ad_id'].map(ad_names_map)
                        df['status'] = df['ad_id'].map(ad_status_map)
                except Exception as e:
                    print(f"Aviso: Não foi possível buscar nomes reais dos anúncios: {e}")

            # Converter valores numéricos
            numeric_fields = ['spend', 'impressions', 'clicks', 'ctr', 'cpc', 'cpm']
            for col in numeric_fields:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            return df

        except Exception as e:
            print(f"Erro ao obter insights de criativos: {str(e)}")
            return pd.DataFrame()

    def get_app_event_types(self) -> list:
        """
        Lista os tipos de evento disponíveis no app (via Meta SDK).
        Requer META_APP_ID configurado.

        Returns:
            Lista de nomes de eventos disponíveis, ou lista vazia se não configurado.
        """
        if not self.app_id:
            return []
        try:
            url = f"{self.base_url}/{self.app_id}/app_event_types"
            params = {"access_token": self.access_token}
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json().get("data", [])
            return [e.get("event_type") or e.get("name", "") for e in data]
        except Exception:
            return []

    def _query_app_event_aggregations(self, event_name: str, start_str: str, end_str: str) -> dict:
        """
        Consulta o endpoint app_event_aggregations para um evento específico.

        Returns:
            Dict com chaves: count (int), success (bool), error (str|None)
        """
        url = f"{self.base_url}/{self.app_id}/app_event_aggregations"
        params = {
            "aggregation_period": "day",
            "time_range": json.dumps({"since": start_str, "until": end_str}),
            "event_name": event_name,
            "access_token": self.access_token,
        }
        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                raw = response.json()
                data = raw.get("data", [])
                total = 0
                for day_data in data:
                    # Handle different response formats
                    val = day_data.get("value") or day_data.get("count") or 0
                    total += int(float(val))
                return {"count": total, "success": True, "error": None}
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error", {}).get("message", "Unknown error")
                error_code = error_data.get("error", {}).get("code", "N/A")
                logger.warning(
                    "app_event_aggregations failed for '%s': HTTP %d, code=%s, msg=%s",
                    event_name, response.status_code, error_code, error_msg,
                )
                return {"count": 0, "success": False, "error": f"HTTP {response.status_code}: {error_msg}"}
        except Exception as e:
            logger.warning("app_event_aggregations exception for '%s': %s", event_name, e)
            return {"count": 0, "success": False, "error": str(e)}

    def get_all_sdk_events(self, date_range: str = "last_7d", custom_start: str = None, custom_end: str = None) -> dict:
        """
        Busca TODOS os eventos SDK relevantes com contagens para o período.
        Retorna dados equivalentes ao que aparece no Events Manager do Facebook.

        Tenta buscar via app_event_aggregations (dados totais do SDK).
        Se falhar, faz fallback para Ads Insights no nível de conta (apenas atribuídos).

        Returns:
            Dict com chaves:
                events: dict[str, int] - mapa de evento → contagem
                source: str - endpoint que forneceu os dados
                errors: list[str] - erros encontrados durante consulta
                install_count: int - total de instalações encontradas
                activate_count: int - total de activate_app encontradas
        """
        result = {
            "events": {},
            "source": "none",
            "errors": [],
            "install_count": 0,
            "activate_count": 0,
        }

        if not self.app_id:
            result["source"] = "no_app_id"
            return result

        try:
            start_str, end_str = self._parse_date_range(date_range, custom_start, custom_end)
        except Exception as e:
            result["errors"].append(f"Date parse error: {e}")
            return result

        # Eventos SDK para consultar (nomes internos do Facebook SDK)
        sdk_event_names = [
            "fb_mobile_install",
            "fb_mobile_activate_app",
            "fb_mobile_content_view",
            "fb_mobile_purchase",
            "fb_mobile_add_to_cart",
            "fb_mobile_complete_registration",
        ]

        # PRIMÁRIO: Tentar app_event_aggregations para cada evento
        aggregations_worked = False
        for event_name in sdk_event_names:
            resp = self._query_app_event_aggregations(event_name, start_str, end_str)
            if resp["success"]:
                aggregations_worked = True
                if resp["count"] > 0:
                    result["events"][event_name] = resp["count"]
            elif resp["error"]:
                result["errors"].append(f"{event_name}: {resp['error']}")

        if aggregations_worked and result["events"]:
            result["source"] = "app_event_aggregations"
            result["install_count"] = result["events"].get("fb_mobile_install", 0)
            result["activate_count"] = result["events"].get("fb_mobile_activate_app", 0)
            logger.info(
                "SDK events from app_event_aggregations: %s", result["events"]
            )
            return result

        # FALLBACK: Usar Ads Insights no nível de CONTA (sem filtro de campanha)
        # para obter todos os action_types com contagens.
        # NOTA: Retorna apenas eventos ATRIBUÍDOS a anúncios.
        logger.warning(
            "app_event_aggregations unavailable or empty. "
            "Falling back to account-level Ads Insights (attributed events only)."
        )
        try:
            url = f"{self.base_url}/{self.ad_account_id}/insights"
            params = {
                "fields": "actions",
                "time_range": json.dumps({"since": start_str, "until": end_str}),
                "action_breakdowns": "action_type",
                "level": "account",
                "access_token": self.access_token,
            }
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json().get("data", [])

            # Coletar TODOS os action_types (não apenas installs)
            sdk_related_prefixes = (
                "app_install", "mobile_app_install", "omni_app_install",
                "fb_mobile_", "offsite_conversion.fb_mobile_",
                "app_custom_event.fb_mobile_", "activate_app",
                "omni_activate_app",
            )

            from meta_funnel import INSTALL_ACTION_TYPES, ACTIVATE_APP_ACTION_TYPES

            for row in data:
                for action in row.get("actions", []):
                    atype = action.get("action_type", "")
                    val = int(float(action.get("value", 0) or 0))
                    if val > 0 and (
                        atype in INSTALL_ACTION_TYPES
                        or atype in ACTIVATE_APP_ACTION_TYPES
                        or any(atype.startswith(p) for p in sdk_related_prefixes)
                    ):
                        result["events"][atype] = result["events"].get(atype, 0) + val

            if result["events"]:
                result["source"] = "ads_insights_account_level"
                # Somar instalações e activate_app
                for atype, val in result["events"].items():
                    if atype in INSTALL_ACTION_TYPES:
                        result["install_count"] += val
                    if atype in ACTIVATE_APP_ACTION_TYPES:
                        result["activate_count"] += val
                logger.info(
                    "SDK events from account-level Ads Insights (attributed only): %s",
                    result["events"],
                )
            else:
                result["errors"].append(
                    "Account-level Ads Insights returned no SDK-related action types"
                )

        except Exception as e:
            logger.error("Account-level Ads Insights fallback failed: %s", e)
            result["errors"].append(f"Ads Insights fallback: {e}")

        return result

    def get_sdk_installs(self, date_range: str = "last_7d", custom_start: str = None, custom_end: str = None, campaign_name_filter: str = None) -> dict:
        """
        Obtém instalações do app via Meta SDK - total de instalações reais do SDK.
        Usa get_all_sdk_events internamente e extrai a contagem de installs.

        Args:
            date_range: Período (last_7d, last_14d, last_30d, today, yesterday, custom)
            custom_start: Data de início personalizada (YYYY-MM-DD)
            custom_end: Data de fim personalizada (YYYY-MM-DD)
            campaign_name_filter: DEPRECATED - SDK installs são totais, não por campanha

        Returns:
            Dict com chaves: installs (int), source (str), event_types (list)
        """
        if campaign_name_filter is not None:
            warnings.warn(
                "campaign_name_filter parameter is deprecated for get_sdk_installs() "
                "as SDK events represent total installs, not campaign-specific attribution. "
                "This parameter will be ignored.",
                DeprecationWarning,
                stacklevel=2,
            )

        all_events = self.get_all_sdk_events(date_range, custom_start, custom_end)

        installs = all_events["install_count"]
        # Se não houver install events, usar activate_app como proxy
        if installs == 0 and all_events["activate_count"] > 0:
            logger.warning(
                "No install events found, using activate_app (%d) as proxy.",
                all_events["activate_count"],
            )
            installs = all_events["activate_count"]

        return {
            "installs": installs,
            "source": all_events["source"],
            "event_types": list(all_events["events"].keys()),
            "all_sdk_events": all_events["events"],
            "errors": all_events["errors"],
        }

    def get_total_app_installs(self, date_range: str = "last_7d", custom_start: str = None, custom_end: str = None, campaign_name_filter: str = None) -> int:
        """
        Obtém o total de instalações do app.
        Usa get_sdk_installs internamente.
        """
        sdk_data = self.get_sdk_installs(date_range, custom_start, custom_end, campaign_name_filter)
        return sdk_data["installs"]
