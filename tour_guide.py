# Componente de Tour Guiado Pergaminho para Dashboard LIA
import streamlit as st

# Conteúdo do tour
TOUR_SECTIONS = {
    'Início': {
        'icon': '🎯',
        'content': '''
**Bem-vindo ao Guia de Apresentação!**

Este tour vai te guiar em cada seção do dashboard.

**Como usar:**
1. Clique nas seções à esquerda
2. Leia as dicas de apresentação
3. Use durante a call com o cliente

💡 **Dica:** Mantenha este guia aberto em uma aba 
separada durante a apresentação!
'''
    },
    'KPIs': {
        'icon': '📊',
        'content': '''
**Resumo Executivo - O que falar:**

"Aqui temos as 5 métricas principais que vocês vão acompanhar."

**Card por card:**

⭐ **North Star (120)**
- "Nossa métrica norte: instalações"
- "Badge verde = meta batida"

💰 **CPI (R$ 15)**
- "R$ 15 por instalação"
- "Meta era R$ 20 - estamos 25% abaixo!"

📈 **Crescimento (+43%)**
- "Crescimento semana a semana"
- "Otimizações funcionando"

💵 **Investimento (R$ 1.800)**
- "Total investido no período"
- "Budget de R$ 5k - dentro do planejado"

📊 **ROI (A definir)**
- "Calculado após LTV por usuário"

💡 **Insight:** Todos indicadores com performance 
acima do esperado!
'''
    },
    'Funil': {
        'icon': '🪜',
        'content': '''
**Funil AIDA - O que destacar:**

"Este funil mostra toda a jornada do usuário."

**Etapa por etapa:**

🔵 **100k → 3k (3% CTR)**
- "CTR acima da média (1-2%)"
- "Criativos são atrativos"

🔵 **3k → 900 (30%)**
- "30% chegam na LP"
- "Anúncio entrega o que promete"

🔵 **900 → 300 (33%)**
- "1 em 3 clica em 'Baixar'"
- "LP converte MUITO bem"

🔵 **300 → 120 (40%)**
- "40% realmente instalam"
- "Acima do padrão (25-30%)"

💡 **Insight Chave:** Não há gargalo crítico! 
Todas etapas convertem bem. Isso é raro e 
indica que estamos atraindo o público certo.

🎯 **Oportunidade:** Aumentar impressões 
mantendo essa qualidade de conversão.
'''
    },
    'Atenção': {
        'icon': '👀',
        'content': '''
**Etapa 1: Atenção - Criativos**

"Aqui vemos qual mensagem gera mais cliques."

**Os 3 criativos:**

🚨 **Dor WhatsApp**
- CTR 1.3% | CPC R$ 0.85
- Performance média

💊 **Feature Remédios** ⭐
- CTR 1.5% | CPC R$ 0.73
- VENCEDOR em ambas métricas!
- Remédios é a feature âncora

💰 **Feature Despesas**
- CTR 1.1% | CPC R$ 0.92
- Menor performance

💡 **Insight:** "Feature Remédios" tem o MAIOR 
CTR E o MENOR CPC. Melhor dos dois mundos!

🎯 **Recomendação:**
1. Ampliar budget +50%
2. Criar variações A/B
3. Pausar "Despesas" temporariamente

📊 **Bônus:** Público 40-60 anos responde 
2.3x melhor. Horário 19h-22h tem 45% mais 
engajamento.
'''
    },
    'Interesse': {
        'icon': '🎯',
        'content': '''
**Etapa 2: Interesse - Landing Page**

"Vamos ver o que acontece na LP."

📊 **900 visitas**
- Total de pessoas na LP

⏱️ **2min 34s de duração**
- EXCELENTE! (média: 45s)
- Indica interesse genuíno

📉 **45% taxa de rejeição**
- Dentro do esperado
- 55% ficam e exploram

🎯 **33% conversão LP**
- 1 em 3 clica "Baixar"
- MUITO acima da média (20-25%)

💡 **Insight:** Combinar 2min 34s + 33% 
conversão é RARO. Significa:
- Página clara e estruturada
- Conteúdo relevante
- CTA bem posicionado
- Proposta de valor forte

📊 **Detalhe:** Seção "Remédios" teve 78% 
scroll depth. Valida que é a feature âncora!
'''
    },
    'Desejo': {
        'icon': '💎',
        'content': '''
**Etapa 3: Desejo - Remarketing**

"Nutrimos quem demonstrou interesse."

**3 públicos:**

🎯 **Visitantes LP**
- CTR 3.2% | 15 conversões

🎯 **Clicaram CTA** ⭐
- CTR 4.5% | 22 conversões
- MELHOR público!
- Já demonstraram intenção

📧 **E-mails (245)**
- CTR 2.8% | 12 conversões
- Recebem sequência de 3 emails

💡 **Por que funciona:** "Clicaram CTA" 
tem quase 2x mais CTR porque são pessoas 
que já demonstraram interesse claro!

📧 **Sequência de emails:**
1. (imediato) "Conheceu o LIA?"
2. (2 dias) "Case família Silva"
3. (5 dias) "Últimas vagas 3 meses grátis"

Taxa abertura: 28% (média: 18%)

🎯 **Otimização:** Carrossel de depoimentos 
aumentou conversão em 35%!
'''
    },
    'Ação': {
        'icon': '🚀',
        'content': '''
**Etapa 4: Ação - Instalações**

"A etapa final: instalações efetivas."

📱 **120 instalações**
- 75 Google Play (62.5%)
- 45 App Store (37.5%)

💰 **CPI Médio: R$ 15**
- Google: R$ 12.50 ⭐
- iOS: R$ 18.30
- 32% mais barato no Android

✅ **85% completaram onboarding**
- 102 de 120 usuários
- EXCEPCIONAL! (média: 45%)

💡 **Por que Google converte melhor?**
1. Instalação mais simples
2. Não exige Face/Touch ID
3. Menos fricção

💡 **85% onboarding é crítico:**
- Indica product-market fit
- App entrega o que promete
- Usuários veem valor imediato

📊 **Retenção:**
- D1: 68% (média: 45%)
- D7: 52% (média: 28%)

🎯 **Não estamos gerando instalações, 
estamos gerando USUÁRIOS ATIVOS!**
'''
    },
    'Próximas Ações': {
        'icon': '⚡',
        'content': '''
**Próximas Ações - O que falar:**

"Com base nos dados, identificamos as próximas ações."

**🚀 CURTO PRAZO (2 semanas)**

✅ Ampliar "Feature Remédios" +50%
   → +30 instalações/semana

✅ Testar "Dor WhatsApp" em vídeo
   → CTR de 1.3% para 2.5%

✅ Teste A/B no CTA da LP
   → +5pp conversão

✅ Lookalike dos 120 instaladores
   → -20% CPI

✅ Otimizar horários (19h-22h)
   → +15% eficiência

**📅 MÉDIO PRAZO (4-6 semanas)**

✅ Sequência 5 emails
✅ Retargeting específico iOS
✅ Testar "Feature Agenda"
✅ Expandir para Home Care
✅ Dashboard retenção D7/D30

💡 **Como apresentar:** "Não são sugestões 
abstratas - cada uma tem justificativa nos 
dados e impacto esperado mensurável."

🎯 **Pergunta final:** "Gostariam que eu 
priorizasse alguma dessas ações, ou seguimos 
com esse roadmap?"
'''
    },
    'Fechamento': {
        'icon': '🎉',
        'content': '''
**Como Fechar a Apresentação**

"Recapitulando:"

**✅ O QUE JÁ TEMOS:**
- Dashboard profissional
- Estrutura completa
- Roadmap de otimização

**🎯 PRÓXIMOS PASSOS:**
- Esta semana: Aprovação
- Semana 1: Setup + soft test
- Semana 2-4: Otimizações
- Mês 2-3: Execução roadmap

**💰 INVESTIMENTO:**
- Fee: R$ 2k/mês
- Mídia: Até R$ 5k/mês
- Total: R$ 21k (3 meses)
- Projeção: 400-500 instalações

**❓ PERGUNTAS:**
1. Dúvidas sobre metodologia?
2. Métrica específica?
3. Formato do dashboard ok?
4. Quando começamos?

**🤝 FECHAMENTO:**
"Tenho 7 anos em planos de saúde, 
nicho similar ao LIA. Sei o que ressoa 
com familiares de idosos. Vamos validar 
H1 juntos e destravar investimento!"

**🎯 CALL TO ACTION:**
"Podemos agendar call na próxima semana 
para finalizar e começar?"

**📧 FOLLOW-UP:**
- Link do dashboard
- PDF resumo
- Proposta comercial
- Cronograma detalhado
'''
    }
}

def render_tour_guide():
    """Renderiza o tour guiado no sidebar"""
    
    with st.sidebar:
        st.markdown("### 📖 Guia de Apresentação")
        st.markdown("---")
        
        # Seleção da seção
        secao = st.radio(
            "Navegue pelas seções:",
            list(TOUR_SECTIONS.keys()),
            label_visibility="collapsed"
        )
        
        # Exibir conteúdo da seção selecionada
        section_data = TOUR_SECTIONS[secao]
        
        st.markdown(f"## {section_data['icon']} {secao}")
        st.markdown(section_data['content'])
        
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; font-size: 0.8rem; color: #94a3b8;'>
            💡 Use este guia durante a apresentação<br/>
            📱 Funciona em qualquer dispositivo
        </div>
        """, unsafe_allow_html=True)
