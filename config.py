"""
Arquivo de configuração para credenciais e variáveis de ambiente
Suporta tanto variáveis de ambiente quanto Streamlit secrets
"""

import json
import os
from typing import Dict, Any, Optional

# Tentar importar streamlit para acessar secrets
try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False


class Config:
    """Classe de configuração centralizada para o dashboard LIA"""

    # Meta Ads
    META_ACCESS_TOKEN: Optional[str] = os.getenv("META_ACCESS_TOKEN")
    META_AD_ACCOUNT_ID: str = os.getenv("META_AD_ACCOUNT_ID", "393721042321443")

    # Google Analytics 4
    GA4_PROPERTY_ID: str = os.getenv("GA4_PROPERTY_ID", "487806406")
    GCP_CREDENTIALS_JSON: Optional[str] = os.getenv("GCP_CREDENTIALS_JSON")

    @staticmethod
    def _get_streamlit_secret(key: str, default: Any = None) -> Any:
        """Obtém um secret do Streamlit de forma segura"""
        if HAS_STREAMLIT:
            try:
                # st.secrets usa acesso por chave, não .get()
                if key in st.secrets:
                    return st.secrets[key]
                return default
            except Exception:
                return default
        return default

    @classmethod
    def get_meta_access_token(cls) -> Optional[str]:
        """Obtém o token de acesso do Meta"""
        # Primeiro tenta variável de ambiente
        if cls.META_ACCESS_TOKEN:
            return cls.META_ACCESS_TOKEN

        # Depois tenta Streamlit secrets
        return cls._get_streamlit_secret("META_ACCESS_TOKEN")

    @classmethod
    def get_meta_ad_account_id(cls) -> str:
        """Obtém o ID da conta de anúncios do Meta"""
        env_value = os.getenv("META_AD_ACCOUNT_ID")
        if env_value:
            return env_value

        return cls._get_streamlit_secret("META_AD_ACCOUNT_ID", cls.META_AD_ACCOUNT_ID)

    @classmethod
    def get_ga4_property_id(cls) -> str:
        """Obtém o ID da propriedade GA4"""
        env_value = os.getenv("GA4_PROPERTY_ID")
        if env_value:
            return env_value

        return cls._get_streamlit_secret("GA4_PROPERTY_ID", cls.GA4_PROPERTY_ID)

    @classmethod
    def get_ga4_credentials(cls) -> Dict[str, Any]:
        """
        Obtém credenciais do GA4

        Tenta obter de:
        1. Variável de ambiente GCP_CREDENTIALS_JSON (JSON string)
        2. Streamlit secrets (estrutura GCP_CREDENTIALS)

        Returns:
            Dicionário com credenciais da service account
        """
        # Tentar variável de ambiente primeiro
        if cls.GCP_CREDENTIALS_JSON:
            try:
                return json.loads(cls.GCP_CREDENTIALS_JSON)
            except json.JSONDecodeError:
                pass

        # Tentar Streamlit secrets
        if HAS_STREAMLIT:
            try:
                gcp_creds = st.secrets.get("GCP_CREDENTIALS")
                if gcp_creds:
                    # Converter AttrDict para dict normal
                    return dict(gcp_creds)
            except Exception:
                pass

        return {}

    @classmethod
    def validate_meta_credentials(cls) -> bool:
        """Valida se as credenciais do Meta estão disponíveis"""
        return bool(cls.get_meta_access_token())

    @classmethod
    def validate_ga4_credentials(cls) -> bool:
        """Valida se as credenciais do GA4 estão disponíveis"""
        creds = cls.get_ga4_credentials()
        required_keys = ['type', 'project_id', 'private_key', 'client_email']
        return all(key in creds for key in required_keys)

    @classmethod
    def validate_all_credentials(cls) -> Dict[str, bool]:
        """
        Valida todas as credenciais

        Returns:
            Dicionário com status de cada integração
        """
        return {
            'meta': cls.validate_meta_credentials(),
            'ga4': cls.validate_ga4_credentials(),
        }

    @classmethod
    def get_integration_status(cls) -> Dict[str, str]:
        """
        Obtém status das integrações para exibição

        Returns:
            Dicionário com status formatado
        """
        validation = cls.validate_all_credentials()

        return {
            'meta': 'Conectado' if validation['meta'] else 'Não configurado',
            'ga4': 'Conectado' if validation['ga4'] else 'Não configurado',
        }
