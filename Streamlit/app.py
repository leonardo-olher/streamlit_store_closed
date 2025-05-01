#%%
# === LIBS ===
import streamlit as st
import pandas as pd

# === DATE ===
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

# === LOAD .ENV ===
from dotenv import load_dotenv; load_dotenv('.env')
from os import getenv

# === LOCAL LIBS ===
from Utils.Graficos import *
from Utils.Functions import *
from Utils.Data import *
from Utils.Login import *

# == | == | == | == | == |




# === NOME DA PAGINA ===
set_page('Inicio')

# == | == | == | == | == |




# === LOGIN ===
CLIENT_ID = getenv('GCP_CLIENT_ID')
CLIENT_SECRET = getenv('GCP_CLIENT_SECRET')
REDIRECT_URI = getenv('GCP_REDIRECT_URI')

# === PERSISTIR DADOS DE LOGIN ===
@st.cache_resource
def cache_login(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, code):
    token = get_token(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, code)
    return get_userinfo(token)

# === VERIFICAR SE FOI FEITO LOGIN COM GOOGLE ===
code = st.query_params.get('code')
if not code:
    is_valid_user, name, photo = False, None, None
    login(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)

else:
    try:
        is_valid_user, name, photo = cache_login(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, code)

    except:
        is_valid_user, name, photo = False, None, None
        login(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)

# == | == | == | == | == |




# == SE O USER FOR VALID, ENTÃO MOSTRAR GRAFICOS ==

if is_valid_user:
    
    # === BASE DE DADOS ATUALIZA CONFORME OS HORARIOS DE ATUALIZACAO ==
    @st.cache_data
    def get_data():

        # >> ACC SNOWFLAKE <<
        USR = getenv('SF_USER')
        PWD = getenv('SF_PWD')
        ACC = getenv('SF_ACC')
        DB  = getenv('SF_DB')
        SCH = getenv('SF_SCHEMA')
        WH  = getenv('SF_WAREHOUSE')

        df = snowflake(USR, PWD, ACC, WH, DB, SCH,
                        query = 'select * from daki_supply.analysis.predict_store_closed')

        up = last_update(df)
        dt1, dt2, dt3, dt_min = filtros_data(df)

        return df, up, dt1, dt2, dt3, dt_min


    df, updated_data, dts1, dts2, dts3, dt_min = get_data()

    # == / == / == / == / == / == / == /




    # === HOME ===
    display_user(name, photo)
    h1, h2 = st.columns([9,1])
    h1.subheader('Radar Graphics - Store Closed')
    h2.markdown(f'''<div style="text-align: right;">
                <b>Ultima Atualização</b>
                <br>
                <em>{datetime.strftime(updated_data, "%d/%m/%Y - %Hh%M")}</em>
                </div>
                <br><br>
                ''', unsafe_allow_html=True)

    st.logo('https://www.abcdacomunicacao.com.br/wp-content/uploads/Daki_logo.png', size='large')

    # == / == / == / == / == / == / == /



    # === FILTROS ===
    with st.container():
        f1, f2, f3, f4, f5, f6 = st.columns(6)

        with f1:

            dt1 = st.date_input(
                'Data (Grafico 1)'
                ,dts1
                ,dt_min     # MENOR DATA POSSIVEL DE FILTRAR
                ,dts3[1]    # MAIOR DATA POSSIVEL DE FILTRAR
                ,format="DD.MM.YYYY"
                ,key='data1')
            
            if len(dt1) == 2:
                dt1_filtro = dt1
            
            elif len(dt1) == 1:
                dt1_filtro = (dt1[0], dt1[0])
            
            else:
                dt1_filtro = dts1

        with f2:

            dt2 = st.date_input(
                'Data (Grafico 2)'
                ,dts2
                ,dt_min     # MENOR DATA POSSIVEL DE FILTRAR
                ,dts3[1]    # MAIOR DATA POSSIVEL DE FILTRAR
                ,format="DD.MM.YYYY"
                ,key='data2')
            
            if len(dt2) == 2:
                dt2_filtro = dt2
            
            elif len(dt2) == 1:
                dt2_filtro = (dt2[0], dt2[0])
            
            else:
                dt2_filtro = dts2

        with f3:
      
            dt3 = st.date_input(
                'Data (Grafico 3)'
                ,dts3
                ,dt_min     # MENOR DATA POSSIVEL DE FILTRAR
                ,dts3[1]    # MAIOR DATA POSSIVEL DE FILTRAR
                ,format="DD.MM.YYYY"
                ,key='data3')
        
            if len(dt3) == 2:
                dt3_filtro = dt3
            
            elif len(dt3) == 1:
                dt3_filtro = (dt3[0], dt3[0])
            
            else:
                dt3_filtro = dts3

        with f4:
            hubs = st.multiselect('Lojas', options=(df['HUB_CODE'] + ' - ' + df['HUB_NAME'] + ' [' + df['TAMANHO_LOJA'] + ']').unique(), key='hubs')
            hubs_except = st.toggle('Exceto', False, key='hubs_except')

            if hubs != []: # FILTRAR SE TIVER ALGUM HUB SELECIONADO
                
                if hubs_except:
                    hubs_filtro = df[~(df['HUB_CODE'] + ' - ' + df['HUB_NAME'] + ' [' + df['TAMANHO_LOJA'] + ']').isin(hubs)]['HUB_CODE'].unique().tolist()

                else:
                    hubs_filtro = df[(df['HUB_CODE'] + ' - ' + df['HUB_NAME'] + ' [' + df['TAMANHO_LOJA'] + ']').isin(hubs)]['HUB_CODE'].unique().tolist()

            else:
                hubs_filtro = df['HUB_CODE'].unique().tolist()

            
        with f5:
            cats = df['CAT_BLOQUEIO'].unique().tolist()
            for rm in ['GELADEIRA', 'FREEZER', 'FRESH GELADEIRA', 'FRESH FREEZER']: cats.remove(rm)
            cats.insert(1, 'GELADOS')

            cat_bloqueios = st.multiselect('Categorias', options=cats, key='cat_bloqueios')
            cat_bloqueios_except = st.toggle('Exceto', False, key='cat_bloqueios_except')

            if cat_bloqueios == []:
                cat_filtro = cats
            
            else:
                if not cat_bloqueios_except:
                    cat_filtro = cat_bloqueios

                else:
                    cat_filtro = [cat for cat in cats if not cat in cat_bloqueios]


        with f6:
            media = st.selectbox('Média', options=['Todas as Lojas', 'Lojas Criticas', 'Lojas Não Criticas', 'Desativar'], index=0, key='media')
            lojas_criticas_filtro = 30

            if media == 'Todas as Lojas':
                hubs_media_dt1 = hubs_media_dt2 = hubs_media_dt3 = df['HUB_CODE'].unique().tolist()

            elif media == 'Lojas Criticas' or media == 'Lojas Não Criticas':
                lojas_criticas_filtro = st.slider('% De Bloqueios', min_value=0.0, max_value=1.0, value=.3, step=0.01, format="%0.2f", key='lojas_criticas_filtro')
                hubs_media_dt1 = lojas_criticas_list(df, lojas_criticas_filtro, media, dt1_filtro)
                hubs_media_dt2 = lojas_criticas_list(df, lojas_criticas_filtro, media, dt2_filtro)
                hubs_media_dt3 = lojas_criticas_list(df, lojas_criticas_filtro, media, dt3_filtro)
            
            elif media == 'Desativar':
                hubs_media_dt1 = hubs_media_dt2 = hubs_media_dt3 = []

    st.divider()

    # == / == / == / == / == / == / == /



    # === SUBTITULO: DADOS HUB ===
    if len(hubs_filtro) == 1:
        title= ''
        hub_data = df[df['HUB_CODE'].isin(hubs_filtro)].iloc[0]
        title = f"{hub_data['HUB_CODE']} - {hub_data['HUB_NAME']} [{hub_data['M2']}M²] | "

    else:
        title = ''

    # == / == / == / == / == / == / == /



    # === CONTAINERS GRAFICOS ===

    for cat in cat_filtro:
        container_radares(df, title, rgb=cat_color(cat), cat=cat, dts_start=(dt1_filtro[0], dt2_filtro[0], dt3_filtro[0]), dts_end=(dt1_filtro[1], dt2_filtro[1], dt3_filtro[1]), hubs=hubs_filtro, hubs_media=(hubs_media_dt1, hubs_media_dt2, hubs_media_dt3))

    # == / == / == / == / == / == / == /

