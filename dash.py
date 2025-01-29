import pandas as pd
import plotly.express as px
import streamlit as st
import json
import requests
from datetime import datetime

# Configuração da página
st.set_page_config(
    layout='wide',
    page_title='Dashboard Incêndio Florestal',
    initial_sidebar_state='expanded'
)

# Aplicando estilo CSS personalizado
st.markdown("""
    <style>
        .main {
            padding: 1rem;
        }
        .stMetric {
            padding: 1rem;
            border-radius: 0.5rem;
        }
    </style>
""", unsafe_allow_html=True)

# Carregando dados
@st.cache_data
def load_data():
    url = "Kaggle - Forest Fires.csv"
    df = pd.read_csv(url, encoding='latin-1')
    
    # Mapeando nomes dos meses para valores numéricos
    month_map = {
        "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4,
        "Maio": 5, "Junho": 6, "Julho": 7, "Agosto": 8,
        "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12
    }
    df['month'] = df['month'].map(month_map)
    
    # Verifica se a coluna 'day' existe
    if 'day' in df.columns:
        df['date'] = pd.to_datetime(df[['year', 'month', 'day']])
    else:
        df['date'] = pd.to_datetime(df[['year', 'month']].assign(day=1))
    
    return df

@st.cache_data
def load_geojson():
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    return requests.get(url).json()

df = load_data()
brazil_states = load_geojson()

# Sidebar com filtros
st.sidebar.header('Filtros')

# Filtro de ano
anos = sorted(df['year'].unique())
ano_selecionado = st.sidebar.slider(
    'Selecione o período',
    min_value=min(anos),
    max_value=max(anos),
    value=(min(anos), max(anos))
)

# Filtro de estado
estados = sorted(df['state'].unique())
estados_selecionados = st.sidebar.multiselect(
    'Selecione os estados',
    estados,
    default=estados
)

# Filtro de mês
meses = sorted(df['month'].unique())
meses_selecionados = st.sidebar.multiselect(
    'Selecione os meses',
    meses,
    default=meses
)

# Aplicando filtros
df_filtered = df[
    (df['year'].between(ano_selecionado[0], ano_selecionado[1])) &
    (df['state'].isin(estados_selecionados)) &
    (df['month'].isin(meses_selecionados))
]

# Título principal
st.title('Monitoramento de Incêndios Florestais no Brasil 🌳 ')
st.markdown(f'Período: {ano_selecionado[0]} a {ano_selecionado[1]}')

# Métricas principais
col1, col2, col3 = st.columns(3)
with col1:
    total_incendios = df_filtered['number'].sum()
    st.metric('Total de Incêndios 🔥 ', f'{total_incendios:,.0f}')

with col2:
    media_anual = total_incendios / len(df_filtered['year'].unique())
    st.metric('Média de Incêndios por Ano 📊 ', f'{media_anual:,.0f}')

with col3:
    max_mes = df_filtered.groupby('month')['number'].sum().idxmax()
    st.metric('Mês com Mais Incêndios 📆 ', f'{max_mes}')

st.divider()

# Gráficos
col_left, col_right = st.columns(2)

with col_left:
    # Tendência temporal
    df_temporal = df_filtered.groupby('year')['number'].sum().reset_index()
    fig_temporal = px.line(
        df_temporal,
        x='year',
        y='number',
        title='Evolução Anual dos Incêndios',
        labels={'number': 'Número de Incêndios', 'year': 'Ano'},
        line_shape='linear'
    )
    fig_temporal.update_traces(line_color='red')
    st.plotly_chart(fig_temporal, use_container_width=True)


with col_right:
    # Mapa coroplético
    df_estados = df_filtered.groupby('state')['number'].sum().reset_index()
    fig_mapa = px.choropleth(
        df_estados,
        geojson=brazil_states,
        locations='state',
        featureidkey='properties.name',
        color='number',
        color_continuous_scale='Reds',
        scope="south america",
        labels={'number': 'Número de Incêndios'},
        title='Distribuição Geográfica dos Incêndios'
    )
    
    fig_mapa.update_geos(
        showcoastlines=True,
        coastlinecolor="Black",
        showland=True,
        landcolor="lightgray",
        showlakes=True,
        lakecolor="Blue",
        showcountries=True,
        countrycolor="Black"
    )
    
    fig_mapa.update_layout(
        margin={"r":0,"t":30,"l":0,"b":0},
        height=600
    )
    
    st.plotly_chart(fig_mapa, use_container_width=True)

col_left1, col_right1 = st.columns(2)

with col_left1: 
    # Distribuição mensal
    df_mensal = df_filtered.groupby(['month', 'year'])['number'].sum().reset_index()
    fig_mensal = px.bar(
        df_mensal,
        x='month',
        y='number',
        color='year',
        title='Distribuição Mensal dos Incêndios',
        labels={'number': 'Número de Incêndios', 'month': 'Mês'},
        color_continuous_scale=px.colors.sequential.Reds
    )
    st.plotly_chart(fig_mensal, use_container_width=True)

with col_right1:
    # Distribuição por estado
    df_estados = df_estados.sort_values('number', ascending=True)
    fig_bar_estado = px.bar(
        df_estados,
        x='number',
        y='state',
        title='Número de Incêndios por Estado',
        labels={'number': 'Numero de Incêndios', 'state': 'Estado'}
    )
    fig_bar_estado.update_traces(marker_color='red')
    st.plotly_chart(fig_bar_estado, use_container_width=True)
# Análise adicional
st.divider()
st.subheader('Análise Detalhada por Estado 📈 ')

# Tabela com estatísticas por estado
df_stats = df_filtered.groupby('state').agg({
    'number': ['sum', 'mean', 'max']
}).round(2)
df_stats.columns = ['Total de Incêndios', 'Média de Incêndios', 'Máximo de Incêndios']
df_stats = df_stats.sort_values('Total de Incêndios', ascending=False)
st.dataframe(df_stats, use_container_width=True)