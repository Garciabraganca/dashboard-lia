import streamlit as st

TOUR_SECTIONS = {
    "intro": {
        "titulo": "👋 Bem-vindo ao Dashboard AIDA",
        "conteudo": """
        Este dashboard apresenta:
        
        **1. Case Real de Sucesso (Grupo Garcia):**
        - Campanha real de recrutamento
        - Métricas comprovadas
        - Resultados tangíveis
        
        **2. Estrutura AIDA (Exemplo App LIA):**
        - Modelo de funil aplicável
        - Projeções baseadas em briefing
        - Framework para outras campanhas
        
        Use o menu lateral para navegar!
        """
    },
    "case_real": {
        "titulo": "🧹 Case Real - Profissionais de Limpeza",
        "conteudo": """
        **Campanha de Recrutamento via Meta Ads**
        
        **Período:** Setembro a Novembro 2024
        
        **Resultados Comprovados:**
        - 55 leads gerados
        - R$ 385,58 investidos
        - CPL de R$ 7,01
        - Redução de 38,5% no CPL entre períodos
        - Crescimento de 193% em volume
        
        **Aprendizados:**
        - Otimização contínua funciona
        - Segmentação refinada reduz custos
        - Volume escala sem perder qualidade
        """
    },
    "projecao_lia": {
        "titulo": "📊 Projeção App LIA",
        "conteudo": """
        **Dados de Briefing - Exemplo de Aplicação**
        
        Este funil mostra como a metodologia AIDA seria aplicada ao App LIA:
        
        - 100k impressões
        - 3k cliques (CTR 3%)
        - 900 visitas à LP
        - 300 cliques no CTA
        - 120 instalações finais
        
        **Importante:** Estes são dados projetados para demonstrar a estrutura do funil, diferente do case real acima.
        """
    },
    "funil_aida": {
        "titulo": "🪜 Metodologia AIDA",
        "conteudo": """
        **As 4 Etapas do Funil:**
        
        1. **ATENÇÃO** - Impressões e alcance
           - Gerar visibilidade máxima
           - Segmentação precisa
        
        2. **INTERESSE** - Cliques e engajamento
           - Criativos que convertem
           - CTR acima da média
        
        3. **DESEJO** - Landing Page
           - Conteúdo persuasivo
           - Experiência otimizada
        
        4. **AÇÃO** - Conversão final
           - CTA claro
           - Processo sem fricção
        """
    },
    "metricas": {
        "titulo": "📈 Métricas-Chave",
        "conteudo": """
        **Indicadores Essenciais:**
        
        - **CPM**: Custo por mil impressões
        - **CTR**: Taxa de cliques
        - **CPC**: Custo por clique
        - **CPL/CPI**: Custo por lead/instalação
        - **Taxa de Conversão**: % em cada etapa
        
        **Benchmarks:**
        - CTR bom: > 2%
        - Taxa rejeição: < 50%
        - Tempo na página: > 2min
        """
    },
    "proximos_passos": {
        "titulo": "🚀 Próximos Passos",
        "conteudo": """
        **Ações Recomendadas:**
        
        **Curto Prazo (esta semana):**
        - Escalar criativos vencedores
        - Ativar remarketing
        
        **Médio Prazo (2 semanas):**
        - Expandir lookalikes
        - Testes A/B em LPs
        
        **Longo Prazo (mês):**
        - Aumentar budget gradualmente
        - Avaliar novos canais
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
