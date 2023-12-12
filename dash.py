import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

mod_color = {'Manter':'yellow','Remover':'red','Incluir':'green','flag':'Flag'}
ren = {'loja':'Loja','secao':'Seção','produto':'Produto','mod':'Ação','flag':'Flag'}
unren = {ren[key]:key for key in ren}
def load_data():
    df = pd.read_csv('v2/viz_novo_metodo.csv',sep = ';').rename(ren,axis = 1)
    if 'Flag' not in df.columns:
        df['Flag'] = False
    return df

def load_clusters():
    cluster_df = pd.read_csv('v2/cluster.csv').rename({'Venda R$':'Faturamento Limpeza (Normalizado)',
                                                       'largura_total':'Tamanho Limpeza (Normalizado)'},axis = 1)
    cluster_df['cluster_name'] = None
    for cluster in cluster_df['cluster'].unique():
        f = cluster_df['cluster'] == cluster
        name = ', '.join([str(x) for x in sorted(cluster_df.loc[f,'LOJA'])])
        cluster_df.loc[f,'cluster_name'] = name
    name_to_number = cluster_df[['cluster','cluster_name']].drop_duplicates().set_index('cluster_name')['cluster'].to_dict()
    return cluster_df,name_to_number

def load_repr():
    return pd.read_csv('v2/representantes.csv',index_col = 1)

def refilter():
    apply_changes()
    data = st.session_state.data
    loja = st.session_state.current_loja
    st.session_state.filtered_data = data.loc[data['Loja'] == loja]

def save_changes():
    apply_changes()
    st.session_state.data.rename(unren,axis = 1).to_csv('v2/viz_novo_metodo.csv',index = False,sep = ';')
    st.sidebar.success('Alterações salvas')

def apply_changes():
    changes = st.session_state.changes['Flag']
    st.session_state.data.loc[changes.index,'Flag'] = changes

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
    st.session_state.cluster_df,st.session_state.name_to_number = load_clusters()
    st.session_state.repr = load_repr()


with st.sidebar:
    st.selectbox('Loja',st.session_state.lojas,key = 'current_loja',on_change = refilter)
    st.radio('Menu',['Tabela','Gráfico','Flags','Marcas','Clusters'],key = 'menu',on_change = refilter)
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
    st.session_state.changes = st.data_editor(df.loc[filt],hide_index = True,
                    use_container_width = True,height = h,disabled = ('Loja','Seção','Produto','Ação','Marca','Grupo',
                                                                      'Subrupo','Faturamento','% Seção'),
                    column_config = {'Loja':None,'Código Loja':None})
elif st.session_state.menu == 'Flags':
    df = st.session_state.data
    st.session_state.changes = st.data_editor(df.loc[df['Flag']],hide_index = True,
                    use_container_width = True,height = h,disabled = ('Loja','Seção','Produto','Ação','Marca','Grupo',
                                                                      'Subrupo','Faturamento','% Seção'),
                    column_config = {'Código Loja':None})
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
    df = st.session_state.data
    marcas = df[['Marca','Faturamento']].groupby('Marca').sum()
    prods_por_marca = df[['Marca','Produto']].loc[df['Ação'] != 'Remover'].drop_duplicates('Produto').groupby('Marca').count()
    marcas = marcas.join(prods_por_marca).rename({'Produto':'Produtos na Rede'},axis = 1)\
        .sort_values('Produtos na Rede',ascending=False).reset_index().fillna(0)
    st.dataframe(marcas,use_container_width=True,hide_index = True)
elif st.session_state.menu == 'Clusters':
    tab1,tab3 = st.tabs(['Tabela','Clusterização'])
    tab1.selectbox('Cluster',st.session_state.cluster_df['cluster_name'].unique(),key = 'cluster_1')
    df = st.session_state.data
    rep = st.session_state.repr
    current_cluster = st.session_state.name_to_number[st.session_state.cluster_1]
    current_rep = rep.loc[current_cluster,'LOJA']
    df = df.loc[df['Código Loja'] == current_rep]
    df = df.loc[df['Ação'] != 'Remover']
    tab1.dataframe(df,hide_index = True,column_config = {'Loja':None,'Ação':None,'Código Loja':None,'Flag':None},
                 use_container_width = True)

    cluster_df = st.session_state.cluster_df
    cluster_df['cluster'] = cluster_df['cluster'].apply(str)
    fig = px.scatter(cluster_df.rename({'cluster':'Cluster'},axis = 1),
                     x = 'Faturamento Limpeza (Normalizado)',y = 'Tamanho Limpeza (Normalizado)',
                     color = 'Cluster',height=550,template='plotly')
    fig.update_traces(marker_size=10)
    fig.update_layout(showlegend=False)
    tab3.plotly_chart(fig,use_container_width=True,theme = None)