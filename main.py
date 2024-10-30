import streamlit as st
import pandas as pd
import locale as lo
from datetime import datetime, timedelta
import gspread as gs
from oauth2client.service_account import ServiceAccountCredentials

json = {
    "type": "service_account",
    "project_id": st.secrets['project_id'],
    "private_key_id": st.secrets['KEY'],
    "private_key": st.secrets['private_key'],
    "client_email": st.secrets['client_email'],
    "client_id": st.secrets['client_id'],
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/case-693%40digital-layout-402513.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
    }

scope = ['https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'] 
credentials = ServiceAccountCredentials.from_json_keyfile_dict(
    json, scope)
client = gs.authorize(credentials)

BASE_STREAMLIT = client.open_by_key(st.secrets['bases']) 


def fmt_num(valor, tipo, casas=0): # Função para formatar números.
    if isinstance(valor,str):
        return ''
    if tipo == 'REAL':
        return lo.format_string(f"R$ %0.{casas}f",valor,grouping=True)
    if tipo == 'CUBAGEM':
        return "{:,.1f}".format(valor).replace(',', 'X').replace('.', ',').replace('X', '.')
    if tipo == 'NORMAL':
        return "{:,.0f}".format(valor).replace(',', 'X').replace('.', ',').replace('X', '.')
    if tipo == "PORCENTAGEM":
        return f"{{:.{casas}%}}".format(valor).replace('.',',')

st.set_page_config(
    page_title="Base Carteira",
    page_icon=":chart_with_upwards_trend:",
    layout="wide", 
    initial_sidebar_state="auto",
)

st.title('Bem vindo')

st.write('Carteira Liberados')

if 'carteira' not in st.session_state and 'estoque' not in st.session_state and 'faturados' not in st.session_state and 'Black_2022' not in st.session_state:

    base = BASE_STREAMLIT.worksheet('CARTEIRA')
    base = base.get_values('A2:AC')
    df = pd.DataFrame(base)
    df.columns = ['NUMPEDVEN','TPNOTA','TIPO_PEDIDO','CODFILTRANSFFAT','CANAL_VENDAS','CODMODAL','DESCRICAO','MODALIDADE','DESCRICAOROTA','DATA_APROVACAO','DTPEDIDO','DTENTREGA','PREVENTREGA','DTLIBFAT_MOD','FAMILIA','FILORIG','STATUS','ITEM','LINHA','NUMLOTE','NUMPEDCOMP','QTCOMP','PRECOUNIT','CUB_UNIT','STATUS_OPERACAO','SITUACAO','STATUS_OPERACAO_GERENCIAL','CUBTOTAL','VALTOTAL']
    df['CODFILTRANSFFAT'] = df['CODFILTRANSFFAT'].astype(str)
    df['VALTOTAL'] = df['VALTOTAL'].str.replace(',','.').astype(float)
    df['CUBTOTAL'] = df['CUBTOTAL'].str.replace(',', '.').astype(float)
    df = df.sort_values('NUMPEDVEN')
    deparamodais = pd.read_excel('de_para_modais.xlsx','Modais')
    deparamodais = deparamodais.astype(str)
    deparafiliais = pd.read_excel('de_para_modais.xlsx','Filiais')
    deparafiliais = deparafiliais.astype(str)
    deparafiliais['Cód'] = deparafiliais['Cód'].astype(str)
    st.session_state['carteira'] = df_union


df_filter = st.session_state['carteira']

status = df_filter.groupby('STATUS').agg({'QTCOMP': 'sum', 'CUBTOTAL': 'sum'}).head(10)
status.loc['Total'] = status.sum()
status['CUBTOTAL'] = status['CUBTOTAL'].apply(fmt_num, tipo='CUBAGEM', casas=1)
status['QTCOMP'] = status['QTCOMP'].apply(fmt_num, tipo='NORMAL')
status = status.reset_index()
status.columns = ['Status', 'Peças', 'Cubagem']


top_familia = df_filter.groupby('FAMILIA').agg({'QTCOMP': 'sum', 'CUBTOTAL': 'sum'}).sort_values('CUBTOTAL', ascending=False).head(10)
top_familia['CUBTOTAL'] = top_familia['CUBTOTAL'].apply(fmt_num, tipo='CUBAGEM', casas=1)
top_familia['QTCOMP'] = top_familia['QTCOMP'].apply(fmt_num, tipo='NORMAL')
top_familia = top_familia.reset_index()
top_familia.columns = ['Familias', 'Peças', 'Cubagem']

carteira_dias = df_filter['CUBTOTAL'].sum()
val = {'Tipo':['Carteira Atual', 'Capacidade', 'Dias Em Carteira'], 'Valores':[fmt_num(carteira_dias, tipo='CUBAGEM'), '975', fmt_num(carteira_dias/975, tipo='CUBAGEM', casas=2)]}
carteira_dias = pd.DataFrame(val)

df_filter['QTCOMP'] = df_filter['QTCOMP'].astype(float) 
dinamica_pecas = pd.pivot_table(df_filter, values='QTCOMP', index='Filial', columns='Modal Master', aggfunc='sum', fill_value=0)    
dinamica_pecas['Total'] = dinamica_pecas.sum(axis=1)
dinamica_pecas = dinamica_pecas.sort_values('Total', ascending=False).applymap(fmt_num, tipo='NORMAL')

dinamica_cub = pd.pivot_table(df_filter, values='CUBTOTAL', index='Filial', columns='Modal Master', aggfunc='sum', fill_value=0)
dinamica_cub['Total'] = dinamica_cub.sum(axis=1)
dinamica_cub = dinamica_cub.sort_values('Total', ascending=False).applymap(fmt_num, tipo='CUBAGEM', casas=1)


col1, col2, col3 = st.columns(3)

col1.dataframe(status, hide_index=True)
col3.dataframe(top_familia, hide_index=True)
col1.dataframe(carteira_dias, hide_index=True)

colun1, colun2 = st.columns(2)
colun1.write('Modais por Filial Peças.')
colun1.dataframe(dinamica_pecas)
colun2.write('Modais por Filial Cubagem.')
colun2.dataframe(dinamica_cub)
