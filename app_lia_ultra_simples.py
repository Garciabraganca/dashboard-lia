import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(
    page_title="Dashboard LIA",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"  # Sidebar aberta no desktop
)

# Aviso para quem acessar pelo celular
st.info(
    "📱 **Se estiver no celular (iOS ou Android)**, toque no ícone ☰ no canto superior esquerdo "
    "para abrir o menu lateral e acessar o **Guia de Apresentação**."
)

# Título
st.title("📊 Dashboard LIA - Funil AIDA")
st.success("✅ Dashboard no ar! Versão inicial funcionando.")

# Dados de exemplo
df = pd.DataFrame({
    "Semana": ["S1", "S2", "S3", "S4", "S5"],
    "Instalações": [10, 18, 24, 28, 40],
})

# Gráfico de evolução
st.subheader("📈 Evolução Semanal de Instalações")
fig = px.line(df, x="Semana", y="Instalações", markers=True)
st.plotly_chart(fig, use_container_width=True)

# Métricas
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Instalações Totais", "120", "+40%")
with col2:
    st.metric("CPI Médio", "R$ 15,00", "-25%")
with col3:
    st.metric("Crescimento", "+43%", "vs anterior")

# Aviso para expansão futura
st.info("💡 Dashboard completo será adicionado em breve com todas as etapas do funil AIDA!")
