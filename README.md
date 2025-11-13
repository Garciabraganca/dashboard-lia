# 📊 Dashboard LIA - Funil AIDA Premium + Tour Guiado 📖

Dashboard profissional para acompanhamento de campanhas Meta Ads do App LIA.

## ✨ NOVIDADE: Tour Guiado Pergaminho

**Agora com guia de apresentação integrado!**

O dashboard inclui um **tour guiado estilo pergaminho** que aparece no sidebar e funciona como um teleprompter durante sua apresentação. Você terá acesso a:

- 🎯 Dicas do que falar em cada seção
- 💡 Insights para destacar
- 📊 Explicação dos números
- 🎬 Scripts de apresentação
- ❓ Perguntas estratégicas para o cliente

**Veja o arquivo `TOUR_GUIADO_PERGAMINHO.md` para detalhes completos!**

---

## 🎨 Visual Premium

Este dashboard apresenta:
- ✅ Design moderno com gradientes e glassmorphism
- ✅ Todas as 4 etapas do funil AIDA completas
- ✅ Cards interativos com hover effects
- ✅ Gráficos elegantes com Plotly
- ✅ Badges coloridos de status
- ✅ Insights acionáveis em cada seção
- ✅ Seção de próximas ações

## 📦 Instalação Local

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Rodar o dashboard
streamlit run app_lia_premium.py
```

O dashboard abrirá em: `http://localhost:8501`

## 🌐 Deploy no Streamlit Cloud (GRÁTIS)

### Opção 1: Via GitHub

1. **Criar repositório no GitHub:**
   - Faça login no GitHub
   - Crie novo repositório "dashboard-lia"
   - Faça upload dos arquivos:
     - `app_lia_premium.py`
     - `requirements.txt`
     - `README.md`

2. **Deploy no Streamlit Cloud:**
   - Acesse: https://streamlit.io/cloud
   - Clique em "New app"
   - Conecte seu GitHub
   - Selecione o repositório "dashboard-lia"
   - Main file: `app_lia_premium.py`
   - Clique em "Deploy"

3. **Pronto!** Você terá uma URL tipo:
   ```
   https://dashboard-lia-andre.streamlit.app
   ```

### Opção 2: Deploy Direto

```bash
# 1. Instalar Streamlit CLI
pip install streamlit

# 2. Fazer login
streamlit login

# 3. Deploy
streamlit deploy app_lia_premium.py
```

## 🔧 Próximos Passos (Integração Real)

Após aprovação do cliente, integrar com dados reais:

### 1. Meta Ads API
```python
# Adicionar integração
from facebook_business.adobjects.adsinsights import AdsInsights
from facebook_business.api import FacebookAdsApi

# Conectar e buscar métricas reais
```

### 2. Google Analytics (Landing Page)
```python
# Métricas da LP
from google.analytics.data_v1beta import BetaAnalyticsDataClient
```

### 3. Firebase (App)
```python
# Métricas de instalação e onboarding
import firebase_admin
```

## 📊 Dados Mockados vs Reais

**Atualmente:** Dados do exemplo do briefing (100k → 3k → 900 → 300 → 120)

**Após integração:** Dados em tempo real das campanhas

## 🎯 Estrutura do Dashboard

1. **Resumo Executivo** - Cards com KPIs principais
2. **Evolução Semanal** - Gráfico de tendência
3. **Funil AIDA Visual** - Visão macro
4. **Etapa 1: Atenção** - Performance de criativos
5. **Etapa 2: Interesse** - Métricas da LP
6. **Etapa 3: Desejo** - Remarketing
7. **Etapa 4: Ação** - Instalações
8. **Distribuição Budget** - Onde o dinheiro foi gasto
9. **Próximas Ações** - Recomendações

## 💡 Dicas de Apresentação

1. **Abra em fullscreen** (F11 no navegador)
2. **Use tema dark** do navegador para melhor contraste
3. **Prepare narrativa** para cada seção
4. **Enfatize os insights** (alertas azuis)
5. **Mostre as próximas ações** no final

## 📞 Suporte

Para dúvidas sobre integração com Meta Ads API ou outras fontes de dados, consulte a documentação:

- Meta Ads API: https://developers.facebook.com/docs/marketing-apis
- Streamlit: https://docs.streamlit.io
- Plotly: https://plotly.com/python/

---

**Desenvolvido para:** Mutualcore - Projeto LIA  
**Gestor de Tráfego:** André Bragança  
**Período:** 3 meses (Validação H1)
