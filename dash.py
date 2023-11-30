import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

mod_color = {'Manter':'yellow','Remover':'red','Incluir':'green'}
def load_data():
    df = pd.read_csv('modificacoes_mix.csv',sep = ';')
    df['secao'] = df['secao'].apply(lambda x: x.title())
    return df

def refilter():
    data = st.session_state.data
    loja = st.session_state.current_loja
    st.session_state.filtered_data = data.loc[data['loja'] == loja]

def flag():
    row = st.session_state.row
    st.session_state.data.loc[row,'flag'] = not st.session_state.data.loc[row,'flag']
    refilter()
    st.sidebar.info(f'Flag da linha {st.session_state.row} modificada')

def remove_all():
    st.session_state.data['flag'] = False
    refilter()
    st.sidebar.info('Todas as flags foram removidas')

def save_changes():
    st.session_state.data.to_csv('modificacoes_mix.csv',index = False,sep = ';')
    st.sidebar.success('Alterações salvas')

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
    st.session_state.lojas = list(data['loja'].unique())
    st.session_state.secoes = list(data['secao'].unique())
    st.session_state.filtered_data = data.loc[data['loja'] == st.session_state.lojas[0]]
    st.session_state.prod_map = data[['produto','secao']].drop_duplicates().set_index('produto')['secao']

with st.sidebar:
    st.toggle('Visualizar gráfico',key = 'toggle')
    st.selectbox('Loja',st.session_state.lojas,key = 'current_loja',on_change = refilter)
    st.header('Inserir ou remover flag')
    st.number_input('Linha',min_value = 0,max_value = st.session_state.data.index[-1],value = 0,key = 'row')
    c1,c2 = st.columns(2)
    c1.button('Inserir/remover',on_click = flag)
    c2.button('Limpar flags',on_click = remove_all)
    st.button('Salvar mudaças',on_click = save_changes)

if not st.session_state.toggle:
    ren = {'loja':'Loja','secao':'Seção','produto':'Produto','mod':'Ação'}
    df = st.session_state.filtered_data
    c1,c2 = st.columns(2)
    c1.selectbox('Seção',['Todas'] + st.session_state.secoes,key = 'current_secao')
    c2.selectbox('Ação',['Todas','Manter/Incluir','Manter','Incluir','Remover'],index = 1,key = 'acao')
    secao = st.session_state.current_secao
    acao = st.session_state.acao
    h = 500
    if secao != 'Todas':
        filt = df['secao'] == secao
    else:
        filt = pd.Series([True] * len(df),df.index)
    if acao == 'Manter/Incluir':
        filt = filt & ((df['mod'] == 'Manter') | (df['mod'] == 'Incluir'))
    elif acao != 'Todas':
        filt = filt & (df['mod'] == acao)
    st.dataframe(df.loc[filt].rename(ren,axis = 1)\
                    .style.apply(lambda row: ['background-color: yellow' if row['flag'] else ''] * len(row),axis = 1),
                    use_container_width = True,height = h,column_config = {'flag':None})
else:
    df = st.session_state.filtered_data
    loja = st.session_state.current_loja
    prod_map = st.session_state.prod_map
    mod_map = df[['produto','mod']].drop_duplicates().set_index('produto')['mod']
    prods,secs = list(df['produto'].unique()),list(df['secao'].unique())
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