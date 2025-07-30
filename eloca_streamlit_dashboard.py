import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px
import os

st.set_page_config(page_title="Eloca Dashboard", layout="wide")
st.title("📊 Dashboard de Relatórios Eloca")

# Lê variáveis de ambiente (setadas como Secrets no Streamlit Cloud)
URL = os.getenv("ELOCA_URL")
HEADERS = {"DeskManager": os.getenv("DESKMANAGER_TOKEN")}

@st.cache_data(ttl=3600)  # cache por 1h
def carregar_dados():
    try:
        resposta = requests.get(URL, headers=HEADERS)
        if resposta.status_code == 200:
            excel = BytesIO(resposta.content)
            df = pd.read_excel(excel)
            return df
        else:
            st.error(f"Erro ao acessar os dados: {resposta.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro: {str(e)}")
        return pd.DataFrame()

# Carrega os dados
df = carregar_dados()

if not df.empty:
    st.subheader("📄 Tabela de dados")
    st.dataframe(df, use_container_width=True)

    colunas_numericas = df.select_dtypes(include='number').columns.tolist()
    if colunas_numericas:
        coluna = st.selectbox("Selecione a coluna para gerar gráfico de barras:", colunas_numericas)
        fig = px.bar(df, x=df.index, y=coluna, title=f"Gráfico de {coluna}", labels={"index": "Linha"})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhuma coluna numérica encontrada para gerar gráfico.")
else:
    st.warning("Nenhum dado disponível. Verifique a URL ou as credenciais.")
