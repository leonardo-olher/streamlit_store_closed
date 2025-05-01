import plotly.graph_objects as go
import numpy as np
import streamlit as st
from datetime import datetime
import pandas as pd

def groupby_radarplot(df, cat, cols):

    cols.append('VALUE')

    df = df\
        .loc[(df['CAT_BLOQUEIO'] == cat)]\
        .groupby(['CAT_BLOQUEIO','CAT'], as_index=False)\
        .agg({col: 'mean' for col in cols})\
        .sort_values('CAT')
    
    df = df[df['CAT'] != '-']
    
    return df


def data_radar(df, hubs, hubs_media, cat, dt_start, dt_end, dts_min_max=None):

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


    media = groupby_radarplot(df_radar[(df_radar['HUB_CODE'].isin(hubs_media)) & (df_radar['CAT'] != '-')], cat, cols_radar)
    hub_radar = groupby_radarplot(df_radar[(df_radar['HUB_CODE'].isin(hubs)) & (df_radar['CAT'] != '-')], cat, cols_radar)

    return hub_radar, media



def customdata_radar(df):

    customdata = []
    for i, row in enumerate(df['CAT']):
        
        if row == 'Backlog':
            customdata.append((row, np.round(df['VALUE'].iloc[i],2), f"""<br>
Horas p/ Iniciar Recebimento: <b>{df['MINUTOS_INICIO_RECEBIMENTO'].iloc[i]/60:,.2f}</b><br>
Horas p/ Finalizar Recebimento: <b>{df['MINUTOS_RECEBIMENTO'].iloc[i]/60:,.2f}</b><br>
"""
            ))

        elif row == 'Recebimento':
            customdata.append((row, np.round(df['VALUE'].iloc[i],2), f"""<br>
TOs Qty Pendentes por M² Diario: <b>{round(df['PENDING_QTY'].iloc[i]):,.0f}</b><br>
TOs Qty Recebidas por M² Diario: <b>{round(df['CHANGED_QTY'].iloc[i]):,.0f}</b>
"""
            ))

        elif row == 'Sortimento':
            customdata.append((row, np.round(df['VALUE'].iloc[i],2), f"""<br>
SKUs com Estoque: <b>{round(df['SKUS_WITH_STOCK'].iloc[i]):,.0f}</b><br>
SKUs Replenishable: <b>{round(df['SKUS_REPLENISHABLE'].iloc[i]):,.0f}</b>
"""
            ))


        elif row == 'Estoque':
            customdata.append((row, np.round(df['VALUE'].iloc[i],2), f"""<br>
Estoque QTY: <b>{round(df['STOCK_QTY'].iloc[i]):,.0f}</b><br>
Estoque COGS: <b>R${round(df['STOCK_COGS'].iloc[i]):,.0f}</b><br>
Estoque GMV: <b>R${round(df['STOCK_GMV'].iloc[i]):,.0f}</b>
"""
            ))

        elif row == 'Pedidos':
            customdata.append((row, np.round(df['VALUE'].iloc[i],2), f"""<br>
Numero de Pedidos: <b>{round(df['COUNT_ORDERS'].iloc[i]):,.0f}</b><br>
Quantidade Vendida: <b>{round(df['UNITS_SOLD'].iloc[i]):,.0f}</b>
"""
            ))

        elif row == 'Imprecisão Estoque':
            customdata.append((row, np.round(df['VALUE'].iloc[i],2), f"""<br>
MIT%: <b>{round(df['MIT_PERC'].iloc[i]*100,2):,.2f}</b>
"""
            ))

    return customdata


def radar(df, rgb, cat, dt_start, hubs, hubs_media, dt_end, dts_min_max):

    df, media = data_radar(df, hubs, hubs_media, cat, dt_start, dt_end, dts_min_max)
    df = df.sort_values('CAT')
    media = media.sort_values('CAT')

    customdata = customdata_radar(df)
    try: customdata += [customdata[0]]
    except: pass

    customdata_media = customdata_radar(media)
    try: customdata_media += [customdata_media[0]]
    except: pass

    # Criando o gráfico de radar
    fig = go.Figure()
    try:
        r_media = media['VALUE'].tolist() + [media['VALUE'].iloc[0]]
        theta_media = media['CAT'].tolist() + [media['CAT'].iloc[0]]

    except:
        r_media = []
        theta_media = []

    fig.add_trace(go.Scatterpolar(
        r=r_media,
        theta=theta_media,
        fill='toself',
        name='Média',
        marker=dict(color=f'rgba(150, 150, 150, 1)', size=12),
        line=dict(color=f'rgba(150, 150, 150, 1)', width=1, shape='linear'),
        customdata=customdata_media
    ))
    rgb_cat = f'rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 1)'
    fig.add_trace(go.Scatterpolar(
        r=df['VALUE'].tolist() + [df['VALUE'].iloc[0]],
        theta=df['CAT'].tolist() + [df['CAT'].iloc[0]],
        fill='toself',
        name='Lojas',
        marker=dict(color=rgb_cat, size=12),
        line=dict(color=rgb_cat, width=2, shape='linear'),
        customdata=customdata
    ))

    fig.update_traces(
        hoverlabel=dict(bgcolor='white', font_size=16),
        hovertemplate=
        f"<span style='color:{rgb_cat}'>"
        "<b>%{theta}: %{customdata[1]} (Normalizado)</b><br>"
        "%{customdata[2]}<br>"
        "</span>"
        "<extra></extra>"
    )

    dt_start = datetime.strftime(dt_start, '%d/%m')
    dt_end = datetime.strftime(dt_end, '%d/%m')
    
    fig.update_layout(
        dragmode=False,
        polar=dict(
            bgcolor='rgba(0, 0, 0, 0)',
            angularaxis=dict(
                rotation=90,
                direction='clockwise',
                tickfont=dict(
                    size=16
                )
            ),
            radialaxis=dict(
                visible=True,
                showticklabels=False,
                range=[0, 1]
            )),
        showlegend=False,
        # title={'text': f'{dt_start} - {dt_end}',
        #        'x': .5,
        #        'xanchor':'center',
        #        'font':{
        #            'color':f'rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 1)',
        #            'size':12
        #         }
        #     }
    )

    return fig


def container_radares(df, title, rgb, cat, dts_start, dts_end, hubs, hubs_media):

    with st.container():
        
        st.markdown(f'<div style="text-align: center;"><h3>{title}{cat}</h3></div>', unsafe_allow_html=True)
        g1, g2, g3 = st.columns(3)

        with g1:
            st.plotly_chart(radar(df, rgb=(rgb[0], rgb[1], rgb[2]), cat=cat, dt_start=dts_start[0], dt_end=dts_end[0], hubs=hubs, hubs_media=hubs_media[0], dts_min_max=(dts_start, dts_end)), config=config_radars(), key=f'{cat}_radar_1')
            _, mid1, _ = st.columns([10,80,10])
            mid1.plotly_chart(bars(df, cat, hubs, dt_start=dts_start[0], dt_end=dts_end[0]), config={'displayModeBar': False}, key=f'{cat}_bar_1', use_container_width=False)

        with g2:
            st.plotly_chart(radar(df, rgb=(rgb[0], rgb[1], rgb[2]), cat=cat, dt_start=dts_start[1], dt_end=dts_end[1], hubs=hubs, hubs_media=hubs_media[1], dts_min_max=(dts_start, dts_end)), config=config_radars(), key=f'{cat}_radar_2')
            _, mid2, _ = st.columns([10,80,10])
            mid2.plotly_chart(bars(df, cat, hubs, dt_start=dts_start[1], dt_end=dts_end[1]), config={'displayModeBar': False}, key=f'{cat}_bar_2', use_container_width=False)

        with g3:
            st.plotly_chart(radar(df, rgb=(rgb[0], rgb[1], rgb[2]), cat=cat, dt_start=dts_start[2], dt_end=dts_end[2], hubs=hubs, hubs_media=hubs_media[2], dts_min_max=(dts_start, dts_end)), config=config_radars(), key=f'{cat}_radar_3')
            _, mid3, _ = st.columns([10,80,10])
            mid3.plotly_chart(bars(df, cat, hubs, dt_start=dts_start[2], dt_end=dts_end[2]), config={'displayModeBar': False}, key=f'{cat}_bar_3', use_container_width=False)

    st.divider()


def data_barplots(df, cat, hubs, dt_start, dt_end):
    gelados = ['FREEZER', 'GELADEIRA', 'FRESH FREEZER', 'FRESH GELADEIRA']
    df['CAT_BLOQUEIO'] = np.where(df['CAT_BLOQUEIO'].isin(gelados), 'GELADOS', df['CAT_BLOQUEIO'])

    df = df[(df['CAT_BLOQUEIO'] == cat) & (df['HUB_CODE'].isin(hubs)) & (df['EFFECTIVE_DAY'] >= dt_start) & (df['EFFECTIVE_DAY'] <= dt_end)].copy()

    df['GROUP'] = '-'
    df['COUNT'] = 1
    df['COUNT_BLOQUEIOS'] = np.where(df['NIVEL_STORE_CLOSED'] > 0, 1, 0)
    cols = ['IS_VALID_OOS', 'IS_OOS', 'COUNT', 'COUNT_BLOQUEIOS', 'WASTE_COGS', 'COGS_SOLD', 'STOCK_QTY', 'AVG_SALES']

    df = df.groupby('GROUP', as_index=False)[cols].sum()

    df['OOS'] = df['IS_OOS'] / df['IS_VALID_OOS'] * 100
    df['DSI'] = df['STOCK_QTY'] / df['AVG_SALES']
    df['STORE CLOSED'] = df['COUNT_BLOQUEIOS'] / df['COUNT'] * 100
    df['WASTE'] = df['WASTE_COGS'] / df['COGS_SOLD'] * -100

    df = df[['OOS', 'STORE CLOSED', 'WASTE', 'DSI']]
    
    df = df\
        .transpose()\
        .reset_index()\
        .rename(columns={0:'VALUE', 'index': 'METRICS'})
    
    df['MAX'] = np.where(df['METRICS'] == 'DSI', 30, 100)
    df['DUMMY'] = 1

    df['PERC_BAR'] = df['VALUE'] / df['MAX']

    df['SORT'] = np\
        .where(df['METRICS'] == 'OOS', 1, np\
        .where(df['METRICS'] == 'DSI', 2, np\
        .where(df['METRICS'] == 'STORE CLOSED', 3, np\
        .where(df['METRICS'] == 'WASTE', 4, 5))))
    
    df = df.sort_values('SORT')

    return df


def cat_color(cat):

    rgbs = {
        'SECOS': (235, 107, 107),
        'GELADOS': (103, 146, 160),
        'HORTI E OVOS': (94, 188, 94),
        'PAES': (119, 60, 0),
        'SALA CLIMATIZADA': (168, 127, 168)
    }

    try: rgb = rgbs[cat]
    except: rgb = (10, 10, 10)

    return rgb


def bars(df, cat, hub, dt_start, dt_end):
    
    bar_plot = data_barplots(df, cat, hub, dt_start, dt_end)
    color = cat_color(cat)

    fig = go\
        .Figure()\
        .add_trace(
            go.Bar(
                x=bar_plot['METRICS'],
                y=bar_plot['DUMMY'],
                marker_color='rgba(255, 255, 255, .07)',
                hoverinfo='skip'
            )
        )\
        .add_trace(
            go.Bar(
                x=bar_plot['METRICS'],
                y=bar_plot['PERC_BAR'],
                marker_color=f'rgba({color[0]}, {color[1]}, {color[2]}, 1)',
                hoverinfo='skip',
                text=[f'{v:,.2f}' for v in bar_plot['VALUE']],
                textposition='outside',
                textfont=dict(
                    color=f'rgba({color[0]}, {color[1]}, {color[2]}, 1)',
                    size=16, 
                )
            )
        )\
        .update_layout(
            barmode='overlay'
            ,dragmode=False
            ,showlegend=False
            ,yaxis=dict(
                showticklabels=False,
                showgrid=False,
                zeroline=False
            )
            ,xaxis=dict(
                showgrid=False,
                zeroline=False
            )
            ,height = 300
        )
    
    return fig


def config_radars():

    config = {
    "modeBarButtonsToRemove": [
        'zoom2d', 'pan2d', 'select2d', 'lasso2d',
        'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d',
        'hoverClosestCartesian', 'hoverCompareCartesian',
        'toggleSpikelines', 'toImage'
    ],
    "displaylogo": False  # remove o logo do Plotly
    }

    return config