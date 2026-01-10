"""
Agente de IA para análise de dados do dashboard usando OpenAI GPT
Usa requests diretamente para evitar problemas de proxy no Streamlit Cloud
"""

import logging
from typing import Dict, Any, Optional
import json
import requests

logger = logging.getLogger(__name__)


class AIAgent:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        Inicializa o agente de IA

        Args:
            api_key: Chave da API OpenAI
            model: Modelo a usar (gpt-4o-mini é mais barato, gpt-4o é mais potente)
        """
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.openai.com/v1/chat/completions"

    @staticmethod
    def is_available() -> bool:
        """Verifica se o agente está disponível"""
        return True

    def _build_system_prompt(self, cycle: str = "Ciclo 2") -> str:
        """Constrói o prompt do sistema para o agente baseado no ciclo"""

        base_prompt = """Você é a LIA, uma assistente especialista em marketing digital, análise de campanhas e otimização de conversão.
Seu papel é analisar os dados do dashboard e fornecer insights acionáveis.

IMPORTANTE: Todos os valores monetários apresentados estão em DÓLARES AMERICANOS (USD/$).
Ao mencionar valores na sua análise, use o símbolo $ e considere que são dólares.

"""

        if cycle == "Ciclo 2":
            # Ciclo 2: Foco em conversão, análise positiva, sem criticar landing page
            return base_prompt + """CONTEXTO: Estamos no CICLO 2 - FASE DE CONVERSÃO.
Nesta fase, a landing page já foi otimizada e estamos focados em escalar resultados.

DIRETRIZES IMPORTANTES PARA O CICLO 2:
- FOQUE SEMPRE NO LADO POSITIVO dos resultados
- NÃO critique a landing page - ela já está otimizada
- NÃO sugira mudanças na landing page
- Apresente os NÚMEROS DE FORMA OBJETIVA para que o gestor decida
- Destaque CONQUISTAS e RESULTADOS POSITIVOS
- Celebre métricas que estão performando bem
- Se algo não está ideal, apresente o dado sem julgamento negativo
- O gestor decide se precisa ajustar algo baseado nos números

Análise de Criativos:
- Identifique o criativo vencedor (melhor CTR + menor CPC)
- Explique O QUE faz esse criativo funcionar (gancho, promessa, emoção)
- Sugira como ESCALAR o sucesso do criativo vencedor

Formato da resposta:
- Use emojis para destacar pontos positivos
- Organize em seções claras
- Seja objetiva e apresente os dados
- Destaque as conquistas e resultados
- Tom otimista e celebratório
"""
        else:
            # Ciclo 1: Foco em tráfego e otimização da landing page
            return base_prompt + """CONTEXTO: Estamos no CICLO 1 - FASE DE TRÁFEGO.
Nesta fase, o foco é otimizar a landing page e os criativos para maximizar engajamento.

Diretrizes:
- Seja direta e objetiva
- Foque em insights que geram ação
- Use linguagem simples e acessível
- Destaque oportunidades de melhoria
- Alerte sobre problemas críticos
- Sugira próximos passos concretos

Análise de Landing Page (baseada nos dados do GA4):
- Avalie a taxa de engajamento e tempo médio na página
- Se o engajamento estiver baixo (<50%), sugira mudanças específicas na landing page
- Considere: headline, CTA, velocidade de carregamento, prova social, escassez, benefícios claros
- Relacione os dados de sessões vs usuários para identificar problemas de retenção

Análise de Criativos e Otimização:
- Identifique o criativo vencedor (melhor CTR + menor CPC)
- Analise O QUE faz esse criativo funcionar (gancho, promessa, visual, emoção)
- Sugira como adaptar a landing page para manter a CONSISTÊNCIA com o criativo vencedor
- A mensagem do anúncio deve ser refletida na landing page para aumentar conversão

Formato da resposta:
- Use emojis para destacar pontos importantes
- Organize em seções claras
- Priorize os insights mais relevantes
- Seja específico nas recomendações (não genérico)
"""

    def _format_data_for_analysis(self, meta_data: Dict, ga4_data: Dict,
                                   creative_data: Any = None,
                                   source_data: Any = None,
                                   events_data: Any = None) -> str:
        """Formata os dados do dashboard para análise"""

        data_text = f"""
## DADOS DO META ADS (Facebook/Instagram)
- Investimento: $ {meta_data.get('investimento', 0):,.2f}
- Impressões: {meta_data.get('impressoes', 0):,}
- Alcance: {meta_data.get('alcance', 0):,}
- Frequência: {meta_data.get('frequencia', 0):.2f}
- Cliques no Link: {meta_data.get('cliques_link', 0):,}
- CTR (Taxa de Cliques): {meta_data.get('ctr_link', 0):.2f}%
- CPC (Custo por Clique): $ {meta_data.get('cpc_link', 0):.2f}
- CPM (Custo por Mil): $ {meta_data.get('cpm', 0):.2f}

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
                data_text += f"- {row.get('Criativo', 'N/A')}: CTR {row.get('CTR', 0):.2f}%, CPC $ {row.get('CPC', 0):.2f}\n"

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
                period: str = "7d",
                cycle: str = "Ciclo 2") -> str:
        """
        Analisa os dados do dashboard e retorna insights

        Args:
            meta_data: Dados do Meta Ads
            ga4_data: Dados do GA4
            creative_data: DataFrame com performance dos criativos
            source_data: DataFrame com origens de tráfego
            events_data: DataFrame com eventos do GA4
            period: Período selecionado
            cycle: Ciclo atual (Ciclo 1 ou Ciclo 2)

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

            # Construir prompt do usuário baseado no ciclo
            if cycle == "Ciclo 2":
                user_prompt = f"""Analise os dados de campanha do período: {period_text}

{data_text}

IMPORTANTE: Comece sua análise identificando claramente que está analisando o **{cycle} - FASE DE CONVERSÃO**.

Por favor, forneça uma análise POSITIVA e OBJETIVA:
1. 🎯 **Resumo da Performance do {cycle}** (2-3 frases celebrando os resultados)
2. 🏆 **Destaques Positivos** - O que está funcionando muito bem
3. 📊 **Métricas em Números** - Apresente os dados de forma objetiva (sem julgamentos negativos)
4. 🌟 **Criativo Vencedor** - Qual criativo está performando melhor e POR QUE ele funciona
5. 🚀 **Oportunidades de Escala** - Como amplificar o que já está dando certo
6. 💡 **Próximos Passos** (máximo 3 ações para escalar resultados)

LEMBRE-SE: Foco no positivo! O gestor vai decidir se precisa ajustar algo baseado nos números.
"""
            else:
                user_prompt = f"""Analise os dados de campanha do período: {period_text}

{data_text}

IMPORTANTE: Comece sua análise identificando claramente que está analisando o **{cycle} - FASE DE TRÁFEGO**.

Por favor, forneça:
1. 🎯 **Resumo da Performance do {cycle}** (2-3 frases)
2. ✅ **O que está funcionando bem**
3. ⚠️ **Pontos de atenção**
4. 🏆 **Criativo Vencedor** - Identifique qual criativo está performando melhor e explique POR QUE ele funciona (qual gancho, emoção ou promessa está ressoando com o público)
5. 🏠 **Otimização da Landing Page** - Baseado nos dados do GA4 (engajamento, tempo na página) e no criativo vencedor, sugira mudanças ESPECÍFICAS para a landing page que mantenham consistência com o anúncio vencedor e aumentem o engajamento
6. 💡 **Próximos Passos** (máximo 3 ações prioritárias)
"""

            # Chamar API diretamente com requests
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self._build_system_prompt(cycle)},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1200
            }

            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code != 200:
                error_msg = response.json().get('error', {}).get('message', response.text)
                return f"❌ Erro da API OpenAI: {error_msg}"

            result = response.json()
            return result['choices'][0]['message']['content']

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
4. 🏆 **Criativo Vencedor** - Identifique qual criativo está performando melhor e explique POR QUE ele funciona (qual gancho, emoção ou promessa está ressoando com o público)
5. 🏠 **Otimização da Landing Page** - Baseado nos dados do GA4 (engajamento, tempo na página) e no criativo vencedor, sugira mudanças ESPECÍFICAS para a landing page que mantenham consistência com o anúncio vencedor e aumentem o engajamento
6. 💡 **Próximos Passos** (máximo 3 ações prioritárias)
"""

            stream = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._build_system_prompt()},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1200,
                stream=True
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Erro na análise de IA (stream): {e}")
            yield f"❌ Erro ao gerar análise: {str(e)}"
