#%%
import streamlit as st
import numpy as np



def set_page(title):
    
    st.set_page_config(
         page_title = title
        ,layout = "wide"
    )
    

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