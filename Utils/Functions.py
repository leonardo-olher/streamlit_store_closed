#%%
import streamlit as st
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
import yaml
from math import ceil
from datetime import datetime, date
import numpy as np
import snowflake.connector as sf
from snowflake.connector.pandas_tools import write_pandas



def set_page(title):
    
    st.set_page_config(
         page_title = title
        ,layout = "wide"
    )



def set_filters(cols, type, data):

    options = {col: [] for col in cols}
    filtros = st.sidebar.multiselect(label='Adicionar Filtro', options=options.keys())
    rows = []
    n_cols = 6
    linhas = 0
    colunas = 0

    for _ in range(ceil(len(cols)/n_cols)):
        rows.append(st.columns(n_cols))


    for option in options.keys():

        if option in filtros:

            with rows[linhas][colunas]:

                with st.container():
                    
                    if type[cols.index(option)].strip() == 'multiselect':
                        options[option] = st.multiselect(label=option, options=sorted(data[option].unique().tolist()))
                        
                        if st.checkbox(f'{option}: Exceto'):
                            if options[option] != []: data = data[~data[option].isin(options[option])]
                        
                        else:
                            if options[option] != []: data = data[data[option].isin(options[option])]

                    elif type[cols.index(option)].strip() == 'date_input':
                        
                        dt_min = np.min(data[option])
                        dt_min = date(dt_min.year,1,1)
                        
                        dt_max = np.max(data[option])
                        dt_max = np.max([date(dt_max.year, dt_max.month, dt_max.day), datetime.now().date()], axis=0)
                        
                        options[option] = st.date_input(label=option, value=(dt_min, dt_max), min_value=dt_min, max_value=dt_max, format='DD/MM/YYYY')
                        
                        if st.checkbox(f'{option}: Exceto'):
                            if options[option] != []:
                                try:
                                    data = data[~((data[option] >= options[option][0]) & (data[option] <= options[option][1]))]
                                except:
                                    pass
                        
                        else:
                            if options[option] != []:
                                try:
                                    data = data[(data[option] >= options[option][0]) & (data[option] <= options[option][1])]
                                except:
                                    pass
                    
            if colunas+1 < n_cols:
                colunas += 1

            else:
                colunas = 0
                linhas += 1

    return data


def snowflake(usr, pwd, acc, wh, db, sch, query=None, prc=None):

    ctx = sf.connect(
             user = usr
            ,password = pwd
            ,account = acc
            ,warehouse = wh
            ,database = db
            ,schema = sch
        )
    
    if query != None:
        return ctx.cursor().execute(query).fetch_pandas_all()
    
    elif prc != None:
        return ctx.cursor().execute(prc)
    
    else:
        return None
    

def lojas_criticas_list(df, perc, filtro, dt):

    df = df[(df['EFFECTIVE_DAY'] >= dt[0]) & (df['EFFECTIVE_DAY'] <= dt[1])]
    df['COUNT'] = 1
    df['COUNT_STORE_CLOSED'] = np.where(df['NIVEL_STORE_CLOSED'] > 0, 1, 0)

    lojas_criticas = df\
        .groupby(['HUB_CODE'], as_index=False)\
        .agg({'COUNT':'sum','COUNT_STORE_CLOSED':'sum'})

    lojas_criticas['%STORE_CLOSED'] = lojas_criticas['COUNT_STORE_CLOSED'] / lojas_criticas['COUNT']

    if filtro == 'Lojas Criticas':
        lojas_criticas = lojas_criticas[lojas_criticas['%STORE_CLOSED'] > perc]
    
    else:
        lojas_criticas = lojas_criticas[(lojas_criticas['%STORE_CLOSED'] <= perc)]

    return lojas_criticas['HUB_CODE'].unique().tolist()