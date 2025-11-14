import streamlit as st

TOUR_SECTIONS = {
    "intro": {
        "titulo": "👋 Bem-vindo ao Dashboard AIDA",
        "conteudo": """
        Este dashboard apresenta:

        **1. Metodologia AIDA Completa**
        - Framework aplicável a qualquer campanha
        - Estrutura: Atenção → Interesse → Desejo → Ação

        **2. Projeção e Exemplos**
        - Dados projetados do App LIA
        - Funil completo detalhado

        **3. Case Real de Sucesso**
        - Campanha Bradesco (Grupo Garcia)
        - Resultados comprovados

        Use o menu lateral para navegar!
        """
    },
    "metodologia_aida": {
        "titulo": "💡 Como Aplicamos a Metodologia AIDA",
        "conteudo": """
        **Framework AIDA:**

        **A**tenção → **I**nteresse → **D**esejo → **A**ção

        Esta é a estrutura usada em TODAS as campanhas:

        - ✅ Segmentação precisa
        - ✅ Criativos testados
        - ✅ LPs otimizadas
        - ✅ Conversão maximizada

        **Resultado:** Campanhas previsíveis e escaláveis.
        """
    },
    "projecao_lia": {
        "titulo": "📱 EXEMPLO • Projeção App LIA",
        "conteudo": """
        **Dados de Briefing - Exemplo de Aplicação**

        ⚠️ **IMPORTANTE:** Projeções baseadas no briefing do App LIA.
        Esta seção demonstra como o framework seria aplicado.

        **North Star:** 120 instalações projetadas
        **CPI:** R$ 15,00 estimado
        **Budget:** R$ 1.800 (5 semanas)

        Dados projetados para demonstrar a estrutura do funil.
        """
    },
    "funil_aida": {
        "titulo": "🪜 Estrutura Completa do Funil AIDA",
        "conteudo": """
        **Visão macro das 4 etapas:**

        - 100k impressões
        - 3k cliques (CTR 3%)
        - 900 visitas à LP (30% conversão)
        - 300 cliques no CTA (33% conversão)
        - 120 instalações finais (40% conversão)

        Cada etapa tem métricas específicas de conversão.
        """
    },
    "etapa_atencao": {
        "titulo": "👁️ 1. ATENÇÃO • Impressões & Alcance",
        "conteudo": """
        **Primeira etapa do funil:**

        - 📊 100.000 impressões
        - 👥 75.000 alcance único
        - 💰 CPM: R$ 8,20
        - 📈 Frequência: 1,33x

        **Objetivo:** Gerar visibilidade máxima com segmentação precisa.
        """
    },
    "etapa_interesse": {
        "titulo": "🖱️ 2. INTERESSE • Cliques & Engajamento",
        "conteudo": """
        **Segunda etapa do funil:**

        - 🖱️ 3.000 cliques
        - 📊 CTR: 3,0%
        - 💵 CPC: R$ 0,80

        **Criativos testados:**
        - Dor do WhatsApp (melhor performer)
        - Feature Remédios
        - Feature Despesas

        **Objetivo:** Criativos que geram engajamento e cliques qualificados.
        """
    },
    "etapa_desejo": {
        "titulo": "🎯 3. DESEJO • Landing Page",
        "conteudo": """
        **Terceira etapa do funil:**

        - 🌐 900 visitas na LP
        - ⏱️ 2m 34s tempo médio
        - 🚪 45% taxa de rejeição
        - 🖱️ 300 cliques no CTA

        **Objetivo:** Conteúdo persuasivo que gera desejo de conversão.
        """
    },
    "etapa_acao": {
        "titulo": "📲 4. AÇÃO • Instalações",
        "conteudo": """
        **Quarta e última etapa:**

        - 📲 120 instalações totais
        - 💰 CPI: R$ 15,00
        - 📊 Taxa conversão: 40%

        **Distribuição:**
        - Google Play: 75 instalações
        - App Store: 45 instalações

        **Objetivo:** Conversão final sem fricção.
        """
    },
    "remarketing": {
        "titulo": "🔄 Remarketing • Reengajamento",
        "conteudo": """
        **Estratégias de reengajamento:**

        - Visitantes LP: 900 pessoas (CTR 3,2%)
        - Clicaram CTA: 300 pessoas (CTR 4,5%)
        - E-mails coletados: 245 pessoas (CTR 2,8%)

        **Objetivo:** Reengajar quem demonstrou interesse.
        """
    },
    "lookalike": {
        "titulo": "🎯 Lookalike • Expansão",
        "conteudo": """
        **Expansão de públicos:**

        - **Warm** (Engajou): 45 instalações (R$ 12,50)
        - **Cold** (Lançamento): 52 instalações (R$ 18,00)
        - **Retargeting** (Abandonou): 23 instalações (R$ 10,20)

        **Objetivo:** Escalar alcance mantendo qualidade.
        """
    },
    "proximos_passos": {
        "titulo": "🚀 Próximos Passos • Plano de Ação",
        "conteudo": """
        **Ações Recomendadas:**

        **Alta Prioridade:**
        - 📊 Criar variações do criativo vencedor
        - 💰 Escalar budget em +30%

        **Média Prioridade:**
        - 🎯 Expandir lookalike 3%
        - 🔄 Ativar retargeting
        - 🧪 A/B test na headline da LP

        Todas com prazos definidos e impacto esperado.
        """
    },
    "case_real": {
        "titulo": "✅ CASE REAL • Campanha Bradesco",
        "conteudo": """
        **Campanha Bradesco - Captação de Profissionais**

        **Cliente:** Grupo Garcia Seguradoras
        **Período:** Setembro a Novembro 2024
        **Status:** ✅ Campanha finalizada com sucesso

        **Resultados Comprovados:**
        - 296 leads gerados
        - R$ 6.180,09 investidos
        - CPL médio de R$ 20,88
        - Redução de 23,7% no CPL entre períodos
        - Crescimento de 129% em volume de leads

        **Aprendizados:**
        - Otimização contínua funciona em escala
        - Segmentação refinada reduz custos
        - Volume escala mantendo qualidade
        - ROI positivo comprovado
        """
    }
}

def render_tour_guide():
    """Renderiza o tour guiado na sidebar"""
    with st.sidebar:
        st.markdown("### 📜 Guia do Dashboard")
        st.markdown("---")
        
        # Seleção da seção
        secao_atual = st.radio(
            "Navegue pelas seções:",
            options=list(TOUR_SECTIONS.keys()),
            format_func=lambda x: TOUR_SECTIONS[x]["titulo"],
            key="tour_section_selector"
        )
        
        st.markdown("---")
        
        # Exibir conteúdo da seção selecionada
        secao = TOUR_SECTIONS[secao_atual]
        st.markdown(f"## {secao['titulo']}")
        st.markdown(secao["conteudo"])
        
        st.markdown("---")
        st.caption("💡 Role a página para ver cada seção em detalhes!")
