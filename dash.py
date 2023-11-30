import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

mod_color = {'Manter':'yellow','Remover':'red','Incluir':'green','flag':'Flag'}
ren = {'loja':'Loja','secao':'Seção','produto':'Produto','mod':'Ação','flag':'Flag'}
unren = {ren[key]:key for key in ren}
def load_data():
    df = pd.read_csv('modificacoes_mix.csv',sep = ';').rename(ren,axis = 1)
    df['Seção'] = df['Seção'].apply(lambda x: x.title())
    return df

def refilter():
    apply_changes()
    data = st.session_state.data
    loja = st.session_state.current_loja
    st.session_state.filtered_data = data.loc[data['Loja'] == loja]

def save_changes():
    apply_changes()
    st.session_state.data.rename(unren,axis = 1).to_csv('modificacoes_mix.csv',index = False,sep = ';')
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

with st.sidebar:
    st.selectbox('Loja',st.session_state.lojas,key = 'current_loja',on_change = refilter)
    st.radio('Menu',['Tabela','Gráfico','Flags'],key = 'menu',on_change = refilter)
    st.button('Salvar mudanças',on_click = save_changes)

h = 500
if st.session_state.menu == 'Tabela':
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
                    use_container_width = True,height = h,disabled = ('Loja','Seção','Produto','Ação'))
elif st.session_state.menu == 'Flags':
    df = st.session_state.data
    st.session_state.changes = st.data_editor(df.loc[df['Flag']],hide_index = True,
                    use_container_width = True,height = h,disabled = ('Loja','Seção','Produto','Ação'))
else:
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