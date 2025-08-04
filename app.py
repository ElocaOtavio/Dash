
import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="Eloca Dashboard", layout="wide")
st.title("📊 Dashboard de Relatórios Eloca")

# URLs e tokens (leitura via Streamlit Cloud secrets ou .env)
URL = os.getenv("ELOCA_URL")
HEADERS = {"DeskManager": os.getenv("DESKMANAGER_TOKEN")}
CSAT_URL = os.getenv("CSAT_URL")
CSAT_HEADER = {"DeskManager": os.getenv("CSAT_TOKEN")}

@st.cache_data(ttl=600)
def carregar_dados_eloca():
    r = requests.get(URL, headers=HEADERS)
    if r.ok:
        return pd.read_excel(BytesIO(r.content))
    else:
        st.error(f"Erro ao carregar Eloca: {r.status_code}")
        return pd.DataFrame()

@st.cache_data(ttl=600)
def carregar_dados_csat():
    r = requests.get(CSAT_URL, headers=CSAT_HEADER)
    if r.ok:
        return pd.read_excel(BytesIO(r.content))
    else:
        st.warning(f"Erro ao carregar CSAT: {r.status_code}")
        return pd.DataFrame()

df = carregar_dados_eloca()
df_csat = carregar_dados_csat()

# Filtros na sidebar
with st.sidebar:
    st.header("🔍 Filtros")
    if "Nome do Grupo" in df.columns:
        grupos = st.multiselect("Grupo", df["Nome do Grupo"].unique())
        if grupos:
            df = df[df["Nome do Grupo"].isin(grupos)]
    if "Data de Criação" in df.columns:
        df["Data de Criação"] = pd.to_datetime(df["Data de Criação"], errors="coerce")
        datas = st.date_input("Intervalo de Criação", [])
        if len(datas) == 2:
            df = df[(df["Data de Criação"] >= datas[0]) & (df["Data de Criação"] <= datas[1])]

# 👨‍🏫 Metas Individuais
if "Meta (min)" in df.columns and "Realizado (min)" in df.columns:
    metas = df.groupby("Analista")[["Realizado (min)"]].mean().reset_index()
    metas.rename(columns={"Realizado (min)": "Tempo Médio Realizado"}, inplace=True)
    st.subheader("🎯 Metas Individuais")
    st.table(metas)

# Resultados por área
st.subheader("📈 Resultados Área 1")
if "Área" in df.columns and "Tempo Útil até o segundo atendimento" in df.columns:
    res1 = df.groupby("Área")[["Tempo Útil até o segundo atendimento"]].mean().reset_index()
    st.bar_chart(res1.set_index("Área"))

st.subheader("📈 Resultados Área 2")
if "Categoria" in df.columns and "Tempo Útil até o segundo atendimento" in df.columns:
    res2 = df.groupby("Categoria")[["Tempo Útil até o segundo atendimento"]].mean().reset_index()
    st.bar_chart(res2.set_index("Categoria"))

# Gráficos individuais
st.subheader("📊 Gráfico-Individual_1: Evolução por Analista")
if "Analista" in df.columns and "Data de Criação" in df.columns:
    df3 = df.groupby(["Analista", pd.Grouper(key="Data de Criação", freq="MS")])["Tempo Útil até o segundo atendimento"].mean().reset_index()
    fig = px.line(df3, x="Data de Criação", y="Tempo Útil até o segundo atendimento", color="Analista")
    st.plotly_chart(fig)

st.subheader("📊 Gráfico-Individual_2: Ranking + CSAT")
if not df_csat.empty:
    df_csat["Resposta"] = df_csat["Atendimento - CES e CSAT - [ANALISTA] Como você avalia […]"].astype(str)
    df_csat["chamado"] = df_csat["Código do Chamado"]
    def pick_cs(row):
        grupo = df_csat[df_csat["Código do Chamado"] == row["Código do Chamado"]]
        bom_ou_otimo = grupo[grupo["Resposta"].str.startswith(("Bom", "Ótimo"), na=False)]
        if not bom_ou_otimo.empty:
            return bom_ou_otimo.iloc[0]
        else:
            return grupo.drop_duplicates("Código do Chamado").iloc[0]
    df_unique = df_csat.groupby("Código do Chamado", as_index=False).apply(pick_cs)
    df_rank = df_unique.groupby("Analista")["Resposta"].apply(lambda x: (x.str.startswith(("Bom", "Ótimo")).mean())).reset_index(name="CSAT")
    fig2 = px.bar(df_rank, x="Analista", y="CSAT", title="CSAT por Analista")
    st.plotly_chart(fig2)
