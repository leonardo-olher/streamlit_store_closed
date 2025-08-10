#%%
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pytz
import numpy as np
import pandas as pd
from Utils.supply_daki import connect_APIs as sup
import streamlit as st


# == TIMEZONE BRASIL ==
def tz():
    return pytz.timezone('America/Sao_Paulo')

# == | == | == | == | == |




# == DATA ATUAL ==
def current_date():
    return datetime.now(tz())

# == | == | == | == | == |




# == DADOS BUCKET ==
def base_bucket(envs):

    df = sup(envs, test_mode=True)\
        .bucket()\
        .read(file_bucket='STORECLOSED.PARQUET', close=True, ref=False)
        

    return df

# == | == | == | == | == |




# == ULTIMA ATUALIZACAO DA TABELA ==
def last_update(df):

    try: return np.max(df['ATUALIZACAO']).replace(tzinfo=tz()) - timedelta(hours=3)

    except: return datetime(2000,1,1,0,0,0,0,tzinfo=tz())

# == | == | == | == | == |




# == DATAS FILTROS ==
def filtros_data(df):

    dt_min = np.min(df['EFFECTIVE_DAY'])

    # == FILTRO 3 ==
    end_dt3 = np.max(df['EFFECTIVE_DAY'])
    start_dt3 = end_dt3 - timedelta(days=end_dt3.day-1)

    # == FILTRO 2 ==
    start_dt2 = start_dt3 - relativedelta(months=1)
    end_dt2 = start_dt2 + relativedelta(months=1) - timedelta(days=1)

    # == FILTRO 1 ==
    start_dt1 = start_dt3 - relativedelta(months=2)
    end_dt1 = start_dt1 + relativedelta(months=1) - timedelta(days=1)

    return (start_dt1, end_dt1), (start_dt2, end_dt2), (start_dt3, end_dt3), dt_min

# == | == | == | == | == |