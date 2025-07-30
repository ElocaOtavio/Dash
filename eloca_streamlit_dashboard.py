import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="Eloca Dashboard", layout="wide")
st.title("📊 Dashboard de Relatórios Eloca")

# Lê variáveis de ambiente (setadas como Secrets no Streamlit Cloud)
URL = os.getenv("ELOCA_URL")
HEADERS = {"DeskManager": os.getenv("DESKMANAGER_TOKEN")}
CSAT_URL = os.getenv("CSAT_URL")
CSAT_HEADER = {"DeskManager": os.getenv("CSAT_TOKEN")}

@st.cache_data(ttl=3600)
def carregar_dados():
    try:
        resposta = requests.get(URL, headers=HEADERS)
        if resposta.status_code == 200:
            excel = BytesIO(resposta.content)
            df = pd.read_excel(excel)
            return df
        else:
            st.error(f"Erro ao acessar os dados principais: {resposta.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao acessar dados principais: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def carregar_dados_csat():
    try:
        resposta = requests.get(CSAT_URL, headers=CSAT_HEADER)
        if resposta.status_code == 200:
            excel = BytesIO(resposta.content)
            df = pd.read_excel(excel)
            return df
        else:
            st.warning(f"Erro ao acessar dados de CSAT: {resposta.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.warning(f"Erro ao acessar dados de CSAT: {str(e)}")
        return pd.DataFrame()

# Carrega os dados principais e CSAT
df = carregar_dados()
df_csat = carregar_dados_csat()

if not df.empty:
    st.subheader("📄 Tabela de dados")
    st.dataframe(df, use_container_width=True)

    # Filtros dinâmicos
    with st.sidebar:
        st.header("🔍 Filtros")

        if 'Nome do Grupo' in df.columns:
            grupos = st.multiselect("Filtrar por Grupo", options=df['Nome do Grupo'].unique())
            if grupos:
                df = df[df['Nome do Grupo'].isin(grupos)]

        if 'Data de Criação' in df.columns:
            df['Data de Criação'] = pd.to_datetime(df['Data de Criação'], errors='coerce')
            datas = st.date_input("Filtrar por Data de Criação", [])
            if len(datas) == 2:
                df = df[(df['Data de Criação'] >= pd.to_datetime(datas[0])) & (df['Data de Criação'] <= pd.to_datetime(datas[1]))]

    # Cálculo de TMA, TME e TMR
    if {'Tempo Útil até o primeiro atendimento', 'Tempo Útil até o segundo atendimento'}.issubset(df.columns):
        df['TME'] = pd.to_numeric(df['Tempo Útil até o primeiro atendimento'], errors='coerce')
        df['TMA'] = pd.to_numeric(df['Tempo Útil até o segundo atendimento'], errors='coerce')
        df['TMR'] = df['TMA'] - df['TME']

        df_plot = df[['Data de Criação', 'TMA', 'TME', 'TMR']].copy()
        df_plot = df_plot.groupby('Data de Criação').mean(numeric_only=True).reset_index()

        st.subheader("📈 TMA, TME e TMR por Data de Criação")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_plot['Data de Criação'], y=df_plot['TMA'], name='Tma (Tempo Medio de Atendimento)', marker_color='mediumseagreen'))
        fig.add_trace(go.Bar(x=df_plot['Data de Criação'], y=df_plot['TME'], name='Tme (Tempo Medio de Espera)', marker_color='teal'))
        fig.add_trace(go.Scatter(x=df_plot['Data de Criação'], y=df_plot['TMR'], name='Tmr (Tempo Medio de Resolução)', mode='lines+markers', line=dict(color='darkorange')))

        fig.update_layout(barmode='group', xaxis_title='Data', yaxis_title='Tempo (min)', legend_title='Indicadores')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Colunas de tempo até atendimentos não encontradas para cálculo de TMA, TME e TMR.")

    # Verifica colunas numéricas adicionais
    colunas_numericas = df.select_dtypes(include='number').columns.tolist()
    if colunas_numericas:
        coluna = st.selectbox("Selecione a coluna para gráfico de barras simples:", colunas_numericas)
        fig = px.bar(df, x=df.index, y=coluna, title=f"Gráfico de {coluna}", labels={"index": "Linha"})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhuma coluna numérica encontrada para gerar gráfico adicional.")

# Dados CSAT (visualização básica inicial)
if not df_csat.empty:
    st.subheader("📄 Tabela de dados CSAT")
    st.dataframe(df_csat, use_container_width=True)
else:
    st.info("Dados de CSAT não carregados ou vazios.")
