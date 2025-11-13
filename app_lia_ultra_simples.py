import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard LIA", page_icon="📊", layout="wide")

st.title("📊 Dashboard LIA - Funil AIDA")
st.success("✅ Dashboard no ar! Versão inicial funcionando.")

# Dados de exemplo
df = pd.DataFrame({
    "Semana": ["S1", "S2", "S3", "S4", "S5"],
    "Instalações": [10, 18, 24, 28, 40],
})

st.subheader("📈 Evolução Semanal de Instalações")
fig = px.line(df, x="Semana", y="Instalações", markers=True)
st.plotly_chart(fig, use_container_width=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Instalações Totais", "120", "+40%")
with col2:
    st.metric("CPI Médio", "R$ 15,00", "-25%")
with col3:
    st.metric("Crescimento", "+43%", "vs anterior")

st.info("💡 Dashboard completo será adicionado em breve com todas as etapas do funil AIDA!")
