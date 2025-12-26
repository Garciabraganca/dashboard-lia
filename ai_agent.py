"""
Agente de IA para análise de dados do dashboard usando OpenAI GPT
"""

import logging
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)

# Importação condicional do OpenAI
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    OpenAI = None


class AIAgent:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        Inicializa o agente de IA

        Args:
            api_key: Chave da API OpenAI
            model: Modelo a usar (gpt-4o-mini é mais barato, gpt-4o é mais potente)
        """
        if not HAS_OPENAI:
            raise ImportError("O módulo 'openai' não está instalado. Execute: pip install openai")

        self.client = OpenAI(api_key=api_key)
        self.model = model

    @staticmethod
    def is_available() -> bool:
        """Verifica se o módulo OpenAI está disponível"""
        return HAS_OPENAI

    def _build_system_prompt(self) -> str:
        """Constrói o prompt do sistema para o agente"""
        return """Você é a LIA, uma assistente especialista em marketing digital e análise de campanhas.
Seu papel é analisar os dados do dashboard e fornecer insights acionáveis.

Diretrizes:
- Seja direta e objetiva
- Foque em insights que geram ação
- Use linguagem simples e acessível
- Destaque oportunidades de melhoria
- Alerte sobre problemas críticos
- Sugira próximos passos concretos

Formato da resposta:
- Use emojis para destacar pontos importantes
- Organize em seções claras
- Priorize os insights mais relevantes
- Mantenha a resposta concisa (máximo 300 palavras)
"""

    def _format_data_for_analysis(self, meta_data: Dict, ga4_data: Dict,
                                   creative_data: Any = None,
                                   source_data: Any = None,
                                   events_data: Any = None) -> str:
        """Formata os dados do dashboard para análise"""

        data_text = f"""
## DADOS DO META ADS (Facebook/Instagram)
- Investimento: R$ {meta_data.get('investimento', 0):,.2f}
- Impressões: {meta_data.get('impressoes', 0):,}
- Alcance: {meta_data.get('alcance', 0):,}
- Frequência: {meta_data.get('frequencia', 0):.2f}
- Cliques no Link: {meta_data.get('cliques_link', 0):,}
- CTR (Taxa de Cliques): {meta_data.get('ctr_link', 0):.2f}%
- CPC (Custo por Clique): R$ {meta_data.get('cpc_link', 0):.2f}
- CPM (Custo por Mil): R$ {meta_data.get('cpm', 0):.2f}

Variações vs período anterior:
- CTR: {meta_data.get('delta_ctr', 0):+.2f}pp
- CPC: {meta_data.get('delta_cpc', 0):+.1f}%
- Cliques: {meta_data.get('delta_cliques', 0):+.1f}%

## DADOS DO GA4 (Landing Page)
- Sessões: {ga4_data.get('sessoes', 0):,}
- Usuários: {ga4_data.get('usuarios', 0):,}
- Pageviews: {ga4_data.get('pageviews', 0):,}
- Taxa de Engajamento: {ga4_data.get('taxa_engajamento', 0):.1f}%
- Tempo Médio: {ga4_data.get('tempo_medio', 'N/A')}
"""

        # Adicionar dados de criativos se disponível
        if creative_data is not None and len(creative_data) > 0:
            data_text += "\n## PERFORMANCE DOS CRIATIVOS\n"
            for _, row in creative_data.head(5).iterrows():
                data_text += f"- {row.get('Criativo', 'N/A')}: CTR {row.get('CTR', 0):.2f}%, CPC R$ {row.get('CPC', 0):.2f}\n"

        # Adicionar dados de origem/mídia se disponível
        if source_data is not None and len(source_data) > 0:
            data_text += "\n## ORIGENS DE TRÁFEGO (TOP 3)\n"
            for _, row in source_data.head(3).iterrows():
                data_text += f"- {row.get('Origem / Midia', 'N/A')}: {row.get('Sessoes', 0)} sessões, {row.get('Engajamento', 'N/A')} engajamento\n"

        # Adicionar dados de eventos se disponível
        if events_data is not None and len(events_data) > 0:
            data_text += "\n## EVENTOS GA4 (TOP 5)\n"
            for _, row in events_data.head(5).iterrows():
                data_text += f"- {row.get('Nome do Evento', 'N/A')}: {row.get('Contagem de Eventos', 'N/A')}\n"

        return data_text

    def analyze(self, meta_data: Dict, ga4_data: Dict,
                creative_data: Any = None,
                source_data: Any = None,
                events_data: Any = None,
                period: str = "7d") -> str:
        """
        Analisa os dados do dashboard e retorna insights

        Args:
            meta_data: Dados do Meta Ads
            ga4_data: Dados do GA4
            creative_data: DataFrame com performance dos criativos
            source_data: DataFrame com origens de tráfego
            events_data: DataFrame com eventos do GA4
            period: Período selecionado

        Returns:
            String com análise e recomendações
        """
        try:
            # Formatar dados
            data_text = self._format_data_for_analysis(
                meta_data, ga4_data, creative_data, source_data, events_data
            )

            # Mapear período para texto
            period_text = {
                "today": "hoje",
                "yesterday": "ontem",
                "7d": "últimos 7 dias",
                "14d": "últimos 14 dias",
                "30d": "últimos 30 dias",
                "custom": "período personalizado"
            }.get(period, period)

            # Construir prompt do usuário
            user_prompt = f"""Analise os dados de campanha do período: {period_text}

{data_text}

Por favor, forneça:
1. 🎯 **Resumo da Performance** (2-3 frases)
2. ✅ **O que está funcionando bem**
3. ⚠️ **Pontos de atenção**
4. 💡 **Recomendações de ação** (máximo 3)
"""

            # Chamar API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._build_system_prompt()},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Erro na análise de IA: {e}")
            return f"❌ Erro ao gerar análise: {str(e)}"

    def analyze_stream(self, meta_data: Dict, ga4_data: Dict,
                       creative_data: Any = None,
                       source_data: Any = None,
                       events_data: Any = None,
                       period: str = "7d"):
        """
        Versão streaming da análise (para resposta em tempo real)

        Yields:
            Chunks de texto conforme são gerados
        """
        try:
            data_text = self._format_data_for_analysis(
                meta_data, ga4_data, creative_data, source_data, events_data
            )

            period_text = {
                "today": "hoje",
                "yesterday": "ontem",
                "7d": "últimos 7 dias",
                "14d": "últimos 14 dias",
                "30d": "últimos 30 dias",
                "custom": "período personalizado"
            }.get(period, period)

            user_prompt = f"""Analise os dados de campanha do período: {period_text}

{data_text}

Por favor, forneça:
1. 🎯 **Resumo da Performance** (2-3 frases)
2. ✅ **O que está funcionando bem**
3. ⚠️ **Pontos de atenção**
4. 💡 **Recomendações de ação** (máximo 3)
"""

            stream = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._build_system_prompt()},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=800,
                stream=True
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Erro na análise de IA (stream): {e}")
            yield f"❌ Erro ao gerar análise: {str(e)}"
