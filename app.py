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
        try:
            df = load_local_data()
            
        except:
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
            
            for rm in ['GELADEIRA', 'FREEZER', 'FRESH GELADEIRA', 'FRESH FREEZER']:
                
                try: cats.remove(rm)
                except: continue

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



df = load_local_data()
df2 = df.copy()

#%%

df = df2.copy()


hubs = ['SAO044']
hubs_media = ['SAO008']
dt_start = date(2025,2,1)
dt_end = date(2025,2,28)
dts_min_max = ((date(2025,2,1), date(2025,3,1), date(2025,4,1)), (date(2025,2,28), date(2025,3,31), date(2025,4,30)))
cat = 'SECOS'

# === FILTRO ===
df['CAT_BLOQUEIO'] = np.where(df['CAT_BLOQUEIO'].isin(['GELADEIRA','FREEZER','FRESH FREEZER','FRESH GELADEIRA']), 'GELADOS', df['CAT_BLOQUEIO'])
df = df[df['CAT_BLOQUEIO'] == cat]


# === AGRUPAR CATS GELADOS ===
if cat == 'GELADOS':

    # GROUP GELADOS
    cols = ['EFFECTIVE_DAY', 'DAY_WEEK', 'UF', 'HUB_CODE', 'HUB_NAME', 'M2', 'CAT_BLOQUEIO', 'TAMANHO_LOJA', 'DAY']

    groupby = {
        'MINUTOS_INICIO_RECEBIMENTO':'mean',
        'MINUTOS_INICIO_RECEBIMENTO_POND':'mean',
        'MINUTOS_RECEBIMENTO':'mean',
        'MINUTOS_RECEBIMENTO_POND':'mean',
        'MINUTOS_RECEBIMENTO_COMPLETO':'mean',
        'MINUTOS_RECEBIMENTO_POND_COMPLETO':'mean',
        'MIT_QTY':'sum',
        'PICKED_QTY':'sum',
        'PENDING_QTY_PER_M2':'sum',
        'CHANGED_QTY_PER_M2':'sum',
        'SKUS_POR_GELADEIRA':'sum',
        'SKUS_REPLENISH_POR_GELADEIRA':'sum',
        'SKUS_WITH_STOCK_PER_M2':'sum',
        'SKUS_REPLENISH_PER_M2':'sum',
        'STOCK_GMV_POR_GELADEIRA':'sum',
        'STOCK_KG_POR_GELADEIRA':'sum',
        'STOCK_COGS_PER_M2':'sum',
        'STOCK_QTY_PER_M2':'sum',
        'STOCK_KG_PER_M2':'sum',
        'COUNT_ORDERS_PER_M2':'sum',
        'UNITS_SOLD_PER_M2':'sum',
        # === DADOS TOOLTIPS === #
        'STOCK_COGS':'sum',
        'STOCK_GMV':'sum',
        'STOCK_QTY':'sum',
        'STOCK_KG':'sum',
        'SKUS_REPLENISHABLE':'sum',
        'SKUS_WITH_STOCK':'sum',
        'COUNT_ORDERS':'sum',
        'UNITS_SOLD':'sum',
        'COGS_SOLD':'sum',
        'GMV_SOLD':'sum',
        'PENDING_QTY':'sum',
        'CHANGED_QTY':'sum'
    }

    df = df\
        .groupby(cols, as_index=False)\
        .agg(groupby)
    


# === MINMAX TODOS PERIDOS FILTRADOS // DF RADAR VALORES DO GRAFICO ===
df_min_max1 = df[(df['EFFECTIVE_DAY'] >= dts_min_max[0][0]) & (df['EFFECTIVE_DAY'] <= dts_min_max[1][0])].copy()
df_min_max1['REF'] = 'DT1'

df_min_max2 = df[(df['EFFECTIVE_DAY'] >= dts_min_max[0][1]) & (df['EFFECTIVE_DAY'] <= dts_min_max[1][1])].copy()
df_min_max2['REF'] = 'DT2'

df_min_max3 = df[(df['EFFECTIVE_DAY'] >= dts_min_max[0][2]) & (df['EFFECTIVE_DAY'] <= dts_min_max[1][2])].copy()
df_min_max3['REF'] = 'DT3'

df_min_max = pd.concat([df_min_max1,df_min_max2,df_min_max3], axis=0)
del df_min_max1, df_min_max2, df_min_max3

df_radar = df[(df['EFFECTIVE_DAY'] >= dt_start) & (df['EFFECTIVE_DAY'] <= dt_end)].copy()



# === COLUNAS NECESSARIAS ===
index = ['HUB_CODE','CAT_BLOQUEIO']
cols_radar = ['MINUTOS_INICIO_RECEBIMENTO','MINUTOS_INICIO_RECEBIMENTO_POND','MINUTOS_RECEBIMENTO','PICKED_QTY'
            ,'MINUTOS_RECEBIMENTO_POND','MINUTOS_RECEBIMENTO_COMPLETO','MINUTOS_RECEBIMENTO_POND_COMPLETO'
            ,'PENDING_QTY_PER_M2','CHANGED_QTY_PER_M2','SKUS_POR_GELADEIRA','SKUS_REPLENISH_POR_GELADEIRA'
            ,'SKUS_WITH_STOCK_PER_M2','SKUS_REPLENISH_PER_M2','STOCK_GMV_POR_GELADEIRA','STOCK_KG_POR_GELADEIRA'
            ,'STOCK_COGS_PER_M2','STOCK_QTY_PER_M2','STOCK_KG_PER_M2','COUNT_ORDERS_PER_M2','UNITS_SOLD_PER_M2'
            ,'STOCK_COGS','STOCK_GMV','STOCK_QTY','STOCK_KG','SKUS_REPLENISHABLE','SKUS_WITH_STOCK','COUNT_ORDERS'
            ,'UNITS_SOLD','COGS_SOLD','GMV_SOLD','PENDING_QTY','CHANGED_QTY','MIT_QTY']


# === COLS EXCLUSIVAS GELADOS ===
cols_gelados = ['SKUS_POR_GELADEIRA','SKUS_REPLENISH_POR_GELADEIRA','STOCK_GMV_POR_GELADEIRA','STOCK_KG_POR_GELADEIRA']
if cat != 'GELADOS':
    cols_radar = [col for col in cols_radar if not col in cols_gelados]


# === REFAZER %MIT COM PERIODO FILTRADO ===
df_radar['MIT_PERC'] = df_radar['MIT_QTY'] / df_radar['PICKED_QTY']
df_min_max['MIT_PERC'] = df_min_max['MIT_QTY'] / df_min_max['PICKED_QTY']

cols_radar.remove('PICKED_QTY')
cols_radar.remove('MIT_QTY')
cols_radar.append('MIT_PERC')


# === NORMALIZACAO ===
df_radar = df_radar\
    .drop(['PICKED_QTY','MIT_QTY'], axis=1)\
    .melt(id_vars=index, value_vars=cols_radar)\
    .fillna(0)\
    .groupby(['HUB_CODE','CAT_BLOQUEIO','variable'], as_index=False)\
    .agg({'value':'mean'})


index.append('REF')
df_min_max = df_min_max\
    .drop(['PICKED_QTY','MIT_QTY'], axis=1)\
    .melt(id_vars=index, value_vars=cols_radar)\
    .fillna(0)\
    .groupby(['REF','HUB_CODE','CAT_BLOQUEIO','variable'], as_index=False)\
    .agg({'value':'mean'})\
    .groupby(['CAT_BLOQUEIO','variable'], as_index=False)\
    .agg(MAX=('value','max'),MIN=('value','min'))
index.remove('REF')

df_radar = df_radar.merge(right=df_min_max, on=['CAT_BLOQUEIO','variable'], how='left')
df_radar['value_norm'] = (df_radar['value'] - df_radar['MIN']) / (df_radar['MAX'] - df_radar['MIN'])



# === AGRUPAR VALORES EIXOS RADAR ===
backlog     = ['MINUTOS_INICIO_RECEBIMENTO','MINUTOS_INICIO_RECEBIMENTO_POND','MINUTOS_RECEBIMENTO','MINUTOS_RECEBIMENTO_POND','MINUTOS_RECEBIMENTO_COMPLETO','MINUTOS_RECEBIMENTO_POND_COMPLETO']
recebimento = ['PENDING_QTY_PER_M2','CHANGED_QTY_PER_M2']
sortimento  = ['SKUS_POR_GELADEIRA','SKUS_REPLENISH_POR_GELADEIRA','SKUS_WITH_STOCK_PER_M2','SKUS_REPLENISH_PER_M2']
estoque     = ['STOCK_GMV_POR_GELADEIRA','STOCK_KG_POR_GELADEIRA','STOCK_COGS_PER_M2','STOCK_QTY_PER_M2','STOCK_KG_PER_M2']
pedidos     = ['COUNT_ORDERS_PER_M2','UNITS_SOLD_PER_M2']
acc_estoque = ['MIT_PERC']


df_radar['CAT'] = np\
    .where(df_radar['variable'].isin(backlog), 'Backlog', np\
    .where(df_radar['variable'].isin(recebimento), 'Recebimento', np\
    .where(df_radar['variable'].isin(sortimento), 'Sortimento', np\
    .where(df_radar['variable'].isin(estoque), 'Estoque', np\
    .where(df_radar['variable'].isin(acc_estoque), 'Imprecisão Estoque', np\
    .where(df_radar['variable'].isin(pedidos), 'Pedidos', '-'))))))

index.append('CAT')

df_radar = df_radar[~((df_radar['variable'].isin(cols_gelados)) & (df_radar['CAT_BLOQUEIO'] != 'GELADOS'))]
df_temp = df_radar.groupby(index, as_index=False).agg(VALUE=('value_norm','mean'))
df_radar = df_radar.merge(right=df_temp, how='left', on=index)

index.append('VALUE')

df_radar = df_radar\
    .pivot_table(
        index=index,
        columns='variable',
        values='value'
    )\
    .reset_index()\
    .fillna(0)

index.remove('VALUE')
index.remove('CAT')

df_temp = df_radar.groupby(index, as_index=False)[cols_radar].max()

df_radar = df_radar\
    .drop(cols_radar, axis=1)\
    .merge(right=df_temp, how='left', on=index)

df_radar
# media = groupby_radarplot(df_radar[(df_radar['HUB_CODE'].isin(hubs_media)) & (df_radar['CAT'] != '-')], cat, cols_radar)
# hub_radar = groupby_radarplot(df_radar[(df_radar['HUB_CODE'].isin(hubs)) & (df_radar['CAT'] != '-')], cat, cols_radar)

# hub_radar