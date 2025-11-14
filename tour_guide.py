import streamlit as st

# Definição das seções do tour
TOUR_SECTIONS = {
    "intro": {
        "titulo": "👋 Bem-vindo ao Dashboard AIDA",
        "conteudo": """
        Este dashboard apresenta a estrutura completa do **Funil AIDA** aplicada às campanhas de tráfego do Grupo Garcia.
        
        **O que você verá:**
        - 📊 Resumo executivo do App LIA
        - 🧹 Case real de recrutamento
        - 📈 Evolução semanal de métricas
        - 🪜 Funil AIDA completo
        - 💡 Insights e próximos passos
        
        Use este menu lateral para navegar pelas explicações de cada seção!
        """
    },
    "resumo": {
        "titulo": "🎯 Resumo Executivo",
        "conteudo": """
        **North Star Metric:** Instalações do app (120 total)
        
        **Principais KPIs:**
        - CPI (Custo por Instalação): R$ 15,00
        - Crescimento: +43% vs período anterior
        - Investimento total: R$ 1.800
        - ROI: Aguardando dados de LTV
        
        Estes indicadores mostram a eficiência da campanha em converter investimento em resultados concretos.
        """
    },
    "case": {
        "titulo": "🧹 Case Real",
        "conteudo": """
        **Campanha de Recrutamento - Profissionais de Limpeza**
        
        **Resultados:**
        - Total de leads: 55
        - CPL médio: R$ 7,01
        - Redução de CPL: 38,5% (2º ciclo vs 1º ciclo)
        - Crescimento de leads: +193% entre períodos
        
        **Aprendizados:**
        - Otimização contínua reduz custos
        - Volume escala sem perder eficiência
        - Segmentação refinada melhora qualidade
        """
    },
    "evolucao": {
        "titulo": "📈 Evolução Semanal",
        "conteudo": """
        **Crescimento Consistente:**
        - S1: 10 instalações
        - S2: 18 instalações (+80%)
        - S3: 24 instalações (+33%)
        - S4: 28 instalações (+17%)
        - S5: 40 instalações (+43%)
        
        O gráfico mostra aceleração nas últimas semanas, indicando maturação da campanha e otimização dos criativos.
        """
    },
    "funil": {
        "titulo": "🪜 Funil AIDA",
        "conteudo": """
        **Estrutura do Funil:**
        
        1. **Atenção** (Impressões): 100.000
        2. **Interesse** (Cliques): 3.000 (3% CTR)
        3. **Desejo** (Visitas LP): 900 (30% conversão)
        4. **Ação** (Instalações): 120 (13% conversão final)
        
        **Taxa de conversão total:** 0,12% (dentro da média para apps)
        
        Cada etapa é otimizada para maximizar o avanço ao próximo nível.
        """
    },
    "proximos": {
        "titulo": "🚀 Próximos Passos",
        "conteudo": """
        **Recomendações Estratégicas:**
        
        1. **Testar novos criativos** baseados no vencedor
        2. **Expandir lookalike** do público warm
        3. **Ativar remarketing** para visitantes
        4. **A/B test na LP** para aumentar conversão
        5. **Escalar budget** nos melhores segmentos
        
        Com estas ações, projetamos 30-50% de melhoria no CPI e volume.
        """
    }
}

def render_tour_guide():
    """Renderiza o tour guiado na sidebar"""
    with st.sidebar:
        st.markdown("### 📜 Tour Guiado")
        st.markdown("---")
        
        # Seleção da seção
        secao_atual = st.radio(
            "Escolha uma seção:",
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
        st.markdown("💡 **Dica:** Role a página para ver cada seção em detalhes!")
