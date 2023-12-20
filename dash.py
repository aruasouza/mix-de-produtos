import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

mod_color = {'Manter':'yellow','Remover':'red','Incluir':'green'}
ren = {'loja':'Loja','secao':'Seção','produto':'Produto','mod':'Ação','flag':'Flag','ação original':'Ação Original'}
col_config_1 = {'Loja':None,'Código Loja':None,'Marca':None,'Flag':None,'Ação Original':None,
                                     'Faturamento':st.column_config.NumberColumn(format = 'R$ %.2f'),
                                     'Quantidade':st.column_config.NumberColumn(format = '%d'),
                                     '% Seção':st.column_config.NumberColumn(format = '%.2f'),
                                     'Ação':st.column_config.SelectboxColumn(options = ['Manter','Incluir','Remover'])}
col_config_2 = {'Loja':None,'Código Loja':None,'Marca':None,'Flag':None,'Ação Original':None,
                                     'Faturamento':st.column_config.NumberColumn(format = 'R$ %.2f'),
                                     'Quantidade':st.column_config.NumberColumn(format = '%d'),
                                     '% Seção':st.column_config.NumberColumn(format = '%.2f')}
col_config_3 = {'Loja':None,'Código Loja':None,'Marca':None,'Flag':None,
                                     'Faturamento':st.column_config.NumberColumn(format = 'R$ %.2f'),
                                     'Quantidade':st.column_config.NumberColumn(format = '%d'),
                                     '% Seção':st.column_config.NumberColumn(format = '%.2f'),
                                     'Ação':st.column_config.SelectboxColumn(options = ['Manter','Incluir','Remover'])}

unren = {ren[key]:key for key in ren}
def load_data():
    df = pd.read_csv('v2/viz_novo_metodo.csv',sep = ';').rename(ren,axis = 1)
    df['Código'] = df['Código'].astype(str)
    df['% Seção'] = df['% Seção'] * 100
    if 'Ação Original' not in df.columns:
        df['Ação Original'] = df['Ação']
    return df

def load_clusters():
    cluster_df = pd.read_csv('v2/clusters.csv',index_col=0)
    cluster_info = pd.read_csv('v2/clusterizacao_info.csv',index_col=0)
    return cluster_df,cluster_info

def load_marcas():
    df = pd.read_csv('v2/fat_marcas.csv')
    df['% Seção'] = df['% Seção'] * 100
    return df.drop('fat_sec',axis = 1)

def refilter():
    apply_changes()
    data = st.session_state.data
    loja = st.session_state.current_loja
    st.session_state.filtered_data = data.loc[data['Loja'] == loja]

def save_changes():
    apply_changes()
    st.session_state.data.rename(unren,axis = 1).to_csv('v2/viz_novo_metodo.csv',index = False,sep = ';')
    st.sidebar.success('Alterações salvas')

def reverse(x):
    if x == 'Remover':
        return 'Incluir'
    elif x == 'Incluir':
        return 'Remover'
    return x

def apply_changes():
    changes = st.session_state.changes['Ação']
    st.session_state.data.loc[changes.index,'Ação'] = changes

html = '''
<style>
.appview-container .main .block-container{
    padding-top: 30px;
    padding-left: 20px;
    padding-right: 20px;
}
.st-emotion-cache-1y4p8pa{
    max-width: None;
}
</style>
'''
st.set_page_config(page_title='Mix de Produtos Bistek', page_icon='🧴')
st.markdown(html,unsafe_allow_html=True)

if 'not_first_load' not in st.session_state:
    data = load_data()
    st.session_state.not_first_load = True
    st.session_state.data = data
    st.session_state.lojas = list(data['Loja'].unique())
    st.session_state.secoes = list(data['Seção'].unique())
    st.session_state.filtered_data = data.loc[data['Loja'] == st.session_state.lojas[0]]
    st.session_state.prod_map = data[['Produto','Seção']].drop_duplicates().set_index('Produto')['Seção']
    st.session_state.cluster_df,st.session_state.cluster_info = load_clusters()
    st.session_state.marcas_df = load_marcas()
    st.session_state.marcas = list(data['Marca'].unique())

with st.sidebar:
    st.selectbox('Loja',st.session_state.lojas,key = 'current_loja',on_change = refilter)
    st.radio('Menu',['Tabela','Gráfico','Mudanças','Marcas','Clusters'],key = 'menu',on_change = refilter)
    st.button('Salvar mudanças',on_click = save_changes)

h = 500
if st.session_state.menu == 'Tabela':
    st.caption(st.session_state.current_loja)
    df = st.session_state.filtered_data
    c1,c2 = st.columns(2)
    c1.selectbox('Seção',['Todas'] + st.session_state.secoes,key = 'current_secao',on_change = refilter)
    c2.selectbox('Ação',['Todas','Manter/Incluir','Manter','Incluir','Remover'],index = 1,key = 'acao',on_change = refilter)
    secao = st.session_state.current_secao
    acao = st.session_state.acao
    if secao != 'Todas':
        filt = df['Seção'] == secao
    else:
        filt = pd.Series([True] * len(df),df.index)
    if acao == 'Manter/Incluir':
        filt = filt & ((df['Ação'] == 'Manter') | (df['Ação'] == 'Incluir'))
    elif acao != 'Todas':
        filt = filt & (df['Ação'] == acao)
    df = df.loc[filt]
    st.session_state.changes = st.data_editor(df,hide_index = True,
                    use_container_width = True,height = h,disabled = ('Loja','Seção','Produto','Ação Original','Marca','Grupo',
                                                                      'Subgrupo','Faturamento','% Seção','Quantidade',
                                                                      'Código'),
                    column_config = col_config_1)
elif st.session_state.menu == 'Mudanças':
    df = st.session_state.data
    st.session_state.changes = st.data_editor(df.loc[df['Ação'] != df['Ação Original']],hide_index = True,
                    use_container_width = True,height = h,disabled = ('Loja','Seção','Produto','Ação Original','Marca','Grupo',
                                                                      'Subgrupo','Faturamento','% Seção','Quantidade',
                                                                      'Código'),
                    column_config = col_config_3)
elif st.session_state.menu == 'Gráfico':
    df = st.session_state.filtered_data
    loja = st.session_state.current_loja 
    prod_map = st.session_state.prod_map
    mod_map = df[['Produto','Ação']].drop_duplicates().set_index('Produto')['Ação']
    prods,secs = list(df['Produto'].unique()),list(df['Seção'].unique())
    labels = prods + secs + [loja]
    parents = [prod_map[p] for p in prods] + [loja] * len(secs) + ['']
    colors = [mod_color[mod_map[p]] for p in prods] + ['orange'] * len(secs) + ['white']

    fig = go.Figure(go.Treemap(
        labels = labels,
        parents = parents,
        marker_colors = colors
    ))
    fig.update_layout(margin = dict(t=25, l=10, r=10, b=10),template='simple_white',height = 600)
    st.plotly_chart(fig,use_container_width=True)
elif st.session_state.menu == 'Marcas':
    col1,col2 = st.columns(2)
    col1.selectbox('Seção',['Todas'] + st.session_state.secoes,key = 'sec_marca')
    col2.selectbox('Marca',['Todas'] + st.session_state.marcas,key = 'marca_marca')
    data = st.session_state.data
    marcas_df = st.session_state.marcas_df
    if st.session_state.sec_marca != 'Todas':
        marcas_df = marcas_df.loc[marcas_df['NOME SEÇÃO'] == st.session_state.sec_marca]
    if st.session_state.marca_marca != 'Todas':
        marcas_df = marcas_df.loc[marcas_df['MARCA'] == st.session_state.marca_marca]
    count = data[['Marca','Produto','Seção']].loc[data['Ação'] != 'Remover']\
        .drop_duplicates('Produto').groupby(['Marca','Seção']).count()
    marcas = marcas_df.join(count,on = ['MARCA','NOME SEÇÃO'])
    marcas['Produto'] = marcas['Produto'].fillna(0)
    marcas = marcas.rename({'NOME SEÇÃO':'Seção','MARCA':'Marca','Venda R$':'Faturamento','Produto':'Produtos'},axis = 1)\
        .sort_values('Produtos',ascending = False)
    st.dataframe(marcas,use_container_width=True,hide_index = True,column_config = {'Faturamento':
                                                                            st.column_config.NumberColumn(format = 'R$ %.2f'),
                                                                            '% Seção':
                                                                            st.column_config.NumberColumn(format = '%.2f')})
elif st.session_state.menu == 'Clusters':
    st.selectbox('Seção',st.session_state.secoes,key = 'secao_cluster')
    tab1,tab3 = st.tabs(['Tabela','Clusterização'])
    col1,col2 = tab1.columns(2)
    col1.selectbox('Cluster Tamanho',st.session_state.cluster_df[st.session_state.secao_cluster].unique(),key = 'cluster_size')
    red_cluster_df = st.session_state.cluster_df[st.session_state.cluster_df[st.session_state.secao_cluster] ==\
                                                 st.session_state.cluster_size]
    col2.selectbox('Cluster Demografia',red_cluster_df['cluster_dem'].unique(),key = 'cluster_dem')
    df = st.session_state.data
    representantes = red_cluster_df[red_cluster_df['cluster_dem'] == st.session_state.cluster_dem].index
    current_rep = representantes[0]
    df = df.loc[df['Seção'] == st.session_state.secao_cluster]
    df = df.loc[df['Código Loja'] == current_rep]
    df = df.loc[df['Ação'] != 'Remover']
    tab1.caption('Lojas: ' + ', '.join([str(x) for x in representantes]))
    tab1.dataframe(df,hide_index = True,column_config = col_config_2,
                 use_container_width = True)

    cluster_df = st.session_state.cluster_df
    info = st.session_state.cluster_info
    info = info[info['NOME SEÇÃO'] == st.session_state.secao_cluster].set_index('LOJA')
    cluster_df = cluster_df[[st.session_state.secao_cluster,'cluster_dem']].join(info).reset_index()\
        .rename({'index':'Loja'},axis = 1)
    cluster_df[st.session_state.secao_cluster] = cluster_df[st.session_state.secao_cluster].astype(str)
    fig = px.scatter(cluster_df.rename({st.session_state.secao_cluster:'Cluster Tamanho','FATURAMENTO':'Faturamento',
                                        'ESPACO':'Espaço','cluster_dem':'Cluster Demográfico'},axis = 1),
                     x = 'Faturamento',y = 'Espaço',
                     color = 'Cluster Tamanho',symbol="Cluster Demográfico", height=550,template='plotly',
                     hover_name = 'Loja')
    fig.update_traces(marker_size=10)
    fig.update_layout(showlegend=False)
    tab3.plotly_chart(fig,use_container_width=True,theme = None)