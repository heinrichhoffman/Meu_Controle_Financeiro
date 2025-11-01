import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime
import os

# --- Configuração da Página ---
st.set_page_config(
    page_title="Meu Controle Financeiro",
    page_icon="💵", 
    layout="wide",
    initial_sidebar_state="auto"  # <-- MUDANÇA PARA OTIMIZAÇÃO MOBILE
)

# --- Constantes (Listas atualizadas com CAJU) ---
DB_NAME = "financeiro.db"

CATEGORIAS_RECEITA = [
    "Salário", "Freelance", "Investimentos", "Presente", "Conta Corrente", 
    "Caju", "Outros"
]
CATEGORIAS_DESPESA = [
    "Alimentação", "Transporte", "Lazer", "Saúde", "Educação", 
    "Compras", "Fatura Cartão", "Outros"
]
CARTOES = [
    "Nenhum (Débito/Dinheiro)", "Nubank", "Mercado Pago", "C6", 
    "Elo", "Azul", "Caju", "Outro"
]

# =====================================================================
# --- BANCO DE DADOS (SQLITE) ---
# =====================================================================

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Data TEXT NOT NULL,
        Categoria TEXT NOT NULL,
        Descricao TEXT,
        Valor REAL NOT NULL,
        Cartao TEXT DEFAULT 'N/A'
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS faturas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Cartao TEXT NOT NULL,
        MesAno TEXT NOT NULL,
        ValorFatura REAL NOT NULL
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orcamentos (
        Categoria TEXT PRIMARY KEY,
        Valor REAL NOT NULL
    )
    """)
    conn.commit()
    conn.close()

# --- Funções CRUD (Transações) ---
def save_transaction(data, categoria, descricao, valor, cartao):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO transacoes (Data, Categoria, Descricao, Valor, Cartao) VALUES (?, ?, ?, ?, ?)",
        (data, categoria, descricao, valor, cartao)
    )
    conn.commit()
    conn.close()

def load_transactions(start_date, end_date):
    conn = get_db_connection()
    query = "SELECT * FROM transacoes WHERE Data BETWEEN ? AND ? ORDER BY Data DESC"
    df = pd.read_sql_query(query, conn, params=(start_date, end_date))
    conn.close()
    if not df.empty:
        df['Data'] = pd.to_datetime(df['Data'])
    return df

def load_all_transactions():
    conn = get_db_connection()
    query = "SELECT * FROM transacoes ORDER BY Data DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    if not df.empty:
        df['Data'] = pd.to_datetime(df['Data'])
    return df

def delete_transaction(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM transacoes WHERE id = ?", (id,))
    conn.commit()
    conn.close()

def update_transaction(id, data, categoria, descricao, valor, cartao):
    conn = get_db_connection()
    conn.execute(
        """UPDATE transacoes 
           SET Data = ?, Categoria = ?, Descricao = ?, Valor = ?, Cartao = ?
           WHERE id = ?""",
        (data, categoria, descricao, valor, cartao, id)
    )
    conn.commit()
    conn.close()

# --- Funções CRUD (Faturas) ---
def save_fatura(cartao, mes_ano, valor):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO faturas (Cartao, MesAno, ValorFatura) VALUES (?, ?, ?)",
        (cartao, mes_ano, valor)
    )
    conn.commit()
    conn.close()

def load_faturas():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM faturas ORDER BY MesAno", conn)
    conn.close()
    return df

# --- Funções CRUD (Orçamentos) ---
def save_budget(categoria, valor):
    conn = get_db_connection()
    conn.execute(
        "INSERT OR REPLACE INTO orcamentos (Categoria, Valor) VALUES (?, ?)",
        (categoria, valor)
    )
    conn.commit()
    conn.close()

def load_budgets():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM orcamentos", conn)
    conn.close()
    return df

# --- Inicializa o DB ---
init_db()

# --- NOVO CSS OTIMIZADO PARA MOBILE (Flexbox + Media Query) ---
st.markdown("""
<style>
/* CSS para o container dos KPIs */
.kpi-container {
    display: flex;
    flex-wrap: wrap; /* <--- Permite que os cards "quebrem" para a linha de baixo */
    justify-content: space-around;
    gap: 20px; /* Espaço entre os cards */
}

/* CSS para os KPI Cards */
.kpi-card {
    background-color: #FFFFFF;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    text-align: center;
    
    /* --- Mágica do Flexbox --- */
    flex-grow: 1; /* Permite que o card cresça */
    flex-shrink: 1; /* Permite que o card encolha */
    flex-basis: 250px; /* Largura base de cada card. */
    
    min-width: 250px; /* Largura mínima antes de quebrar */
    max-width: 350px; /* Largura máxima */
    
    display: flex;
    flex-direction: column;
    justify-content: center;
    min-height: 130px;
}
.kpi-title {
    font-size: 16px;
    font-weight: 600;
    color: #5A5A5A;
    margin-bottom: 8px;
}
.kpi-value {
    font-size: 32px;
    font-weight: 700;
    color: #262730;
}
.kpi-value-positive { color: #28a745; }
.kpi-value-negative { color: #dc3545; }

/* --- Media Query para Telas Pequenas (Celulares) --- */
@media (max-width: 768px) {
    .kpi-card {
        flex-basis: 100%; /* Em celulares, cada card ocupa 100% da largura */
        min-height: 110px; /* Altura menor no mobile */
    }
    .kpi-value {
        font-size: 28px; /* Fonte um pouco menor no mobile */
    }
    .kpi-title {
        font-size: 15px;
    }
}
</style>
""", unsafe_allow_html=True)


# =====================================================================
# --- BARRA LATERAL (SIDEBAR) ---
# =====================================================================
st.sidebar.image("https://img.icons8.com/plasticine/100/000000/stack-of-money.png", width=100)
st.sidebar.title("Controle Financeiro PRO")
st.sidebar.markdown("---")
st.sidebar.header("Adicionar Transação ✍️")
tab_receita, tab_despesa = st.sidebar.tabs([" Receita ", " Despesa "])

with tab_receita:
    with st.form("form_receita", clear_on_submit=True):
        st.markdown("### Nova Receita")
        data_receita = st.date_input("Data", datetime.now(), key="data_rec")
        categoria_receita = st.selectbox("Categoria", CATEGORIAS_RECEITA, key="cat_rec")
        descricao_receita = st.text_input("Descrição", key="desc_rec")
        valor_receita = st.number_input("Valor (R$)", min_value=0.01, format="%.2f", step=0.01, key="val_rec")
        
        submit_receita = st.form_submit_button("Salvar Receita")
        if submit_receita:
            save_transaction(
                data_receita.strftime("%Y-%m-%d"), 
                categoria_receita, 
                descricao_receita, 
                valor_receita, 
                "N/A"
            )
            st.sidebar.success("Receita salva com sucesso!")
            st.rerun()

with tab_despesa:
    with st.form("form_despesa", clear_on_submit=True):
        st.markdown("### Nova Despesa")
        data_despesa = st.date_input("Data", datetime.now(), key="data_des")
        categoria_despesa = st.selectbox("Categoria", CATEGORIAS_DESPESA, key="cat_des")
        cartao_despesa = st.selectbox("Cartão", CARTOES, key="cartao_des")
        descricao_despesa = st.text_input("Descrição", key="desc_des")
        valor_despesa = st.number_input("Valor (R$)", min_value=0.01, format="%.2f", step=0.01, key="val_des")
        
        submit_despesa = st.form_submit_button("Salvar Despesa")
        if submit_despesa:
            save_transaction(
                data_despesa.strftime("%Y-%m-%d"), 
                categoria_despesa, 
                descricao_despesa, 
                valor_despesa * -1,
                cartao_despesa
            )
            st.sidebar.success("Despesa salva com sucesso!")
            st.rerun()

# =====================================================================
# --- ÁREA PRINCIPAL COM ABAS ---
# =====================================================================

st.title("Meu Dashboard de Controle Financeiro")

# --- ESTRUTURA DE NAVEGAÇÃO COM ABAS ---
tab_dash, tab_cartoes, tab_orcamento = st.tabs([
    "Dashboard Principal 📈", 
    "Cartões de Crédito 💳", 
    "Orçamento 🎯"
])


# =====================================================================
# --- PÁGINA 1: DASHBOARD PRINCIPAL ---
# =====================================================================
with tab_dash:
    today_dash = datetime.now() # Variável 'today' local para esta aba

    # --- 1. FILTROS DE DATA ---
    with st.container(border=True):
        st.header("Filtros 📅")
        col_f1, col_f2, col_f3 = st.columns(3)
        
        with col_f1:
            start_of_month = today_dash.replace(day=1)
            data_inicio = st.date_input("Data Início", start_of_month, key="dash_data_inicio")
        with col_f2:
            data_fim = st.date_input("Data Fim", today_dash, key="dash_data_fim")
        
        with col_f3:
            st.markdown("<br/>", unsafe_allow_html=True)
            if st.button("Filtrar Este Mês", key="dash_filtro_mes"):
                data_inicio = today_dash.replace(day=1)
                data_fim = today_dash
                st.rerun()

    df_transacoes = load_transactions(
        data_inicio.strftime("%Y-%m-%d"), 
        data_fim.strftime("%Y-%m-%d")
    )

    # --- 2. KPIs (Resumo Geral) ---
    st.header("Resumo Geral (Período Selecionado) 📈")
    if not df_transacoes.empty:
        receita = df_transacoes[df_transacoes['Valor'] > 0]['Valor'].sum()
        despesa = df_transacoes[
            (df_transacoes['Valor'] < 0) & 
            (df_transacoes['Categoria'] != 'Fatura Cartão')
        ]['Valor'].sum()
        saldo = receita + despesa
    else:
        receita = despesa = saldo = 0.0

    saldo_color_class = "kpi-value-positive" if saldo >= 0 else "kpi-value-negative"

    # --- NOVO LAYOUT HTML/CSS PARA OS KPIs ---
    # (Substitui o st.columns(3))
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-title">Receita Total 🟢</div>
            <div class="kpi-value kpi-value-positive">R$ {receita:,.2f}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Despesa Total 🔴</div>
            <div class="kpi-value kpi-value-negative">R$ {despesa:,.2f}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Saldo 🔵</div>
            <div class="kpi-value {saldo_color_class}">R$ {saldo:,.2f}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    # --- FIM DA MUDANÇA ---
    
    st.markdown("<br/>", unsafe_allow_html=True) 

    # --- 3. GRÁFICOS (Pizza) ---
    with st.container(border=True):
        st.header("Análise de Categorias 📊")
        col_g1, col_g2 = st.columns(2) # Em mobile, isto vai empilhar
        
        with col_g1:
            st.markdown("#### Distribuição de Despesas")
            df_despesas = df_transacoes[
                (df_transacoes['Valor'] < 0) & 
                (df_transacoes['Categoria'] != 'Fatura Cartão')
            ].copy()
            
            if df_despesas.empty:
                st.info("Nenhuma despesa no período.")
            else:
                df_agrupado_desp = df_despesas.groupby('Categoria')['Valor'].sum().abs().reset_index()
                fig_pizza_desp = px.pie(
                    df_agrupado_desp, names='Categoria', values='Valor', hole=0.3
                )
                fig_pizza_desp.update_layout(template="plotly_dark") 
                fig_pizza_desp.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pizza_desp, use_container_width=True)

        with col_g2:
            st.markdown("#### Distribuição de Receitas")
            df_receitas = df_transacoes[df_transacoes['Valor'] > 0].copy()
            
            if df_receitas.empty:
                st.info("Nenhuma receita no período.")
            else:
                df_agrupado_rec = df_receitas.groupby('Categoria')['Valor'].sum().reset_index()
                fig_pizza_rec = px.pie(
                    df_agrupado_rec, names='Categoria', values='Valor', hole=0.3
                )
                fig_pizza_rec.update_layout(template="plotly_dark")
                fig_pizza_rec.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pizza_rec, use_container_width=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # --- 4. GRÁFICO: Evolução Mensal ---
    with st.container(border=True):
        st.header("Evolução Mensal (Receita vs. Despesa) 💹")
        df_full = load_all_transactions()
        
        if df_full.empty:
            st.info("Nenhuma transação registrada ainda.")
        else:
            df_full['Data'] = pd.to_datetime(df_full['Data'])
            df_full['MesAno'] = df_full['Data'].dt.to_period('M').astype(str)
            
            df_despesas_filtradas = df_full[
                (df_full['Valor'] < 0) & 
                (df_full['Categoria'] != 'Fatura Cartão')
            ]
            
            df_receitas_evol = df_full[df_full['Valor'] > 0].groupby('MesAno')['Valor'].sum().reset_index()
            df_receitas_evol.rename(columns={'Valor': 'Receita'}, inplace=True)
            
            df_despesas_evol = df_despesas_filtradas.groupby('MesAno')['Valor'].sum().abs().reset_index()
            df_despesas_evol.rename(columns={'Valor': 'Despesa'}, inplace=True)
            
            df_evolucao = pd.merge(df_receitas_evol, df_despesas_evol, on='MesAno', how='outer').fillna(0)
            
            df_melted = df_evolucao.melt(
                id_vars='MesAno', 
                value_vars=['Receita', 'Despesa'], 
                var_name='Tipo', 
                value_name='Valor'
            )
            
            fig_evolucao = px.bar(
                df_melted,
                x='MesAno',
                y='Valor',
                color='Tipo',
                barmode='group',
                title="Receitas vs Despesas por Mês",
                color_discrete_map={'Receita': '#28a745', 'Despesa': '#dc3545'}
            )
            fig_evolucao.update_layout(template="plotly_dark")
            st.plotly_chart(fig_evolucao, use_container_width=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # --- 5. TABELA DE TRANSAÇÕES E GERENCIAMENTO (Excluir e Alterar) ---
    with st.container(border=True):
        st.header("Histórico e Gerenciamento de Transações 📑")
        
        if df_transacoes.empty:
            st.info("Nenhuma transação cadastrada no período.")
        else:
            df_display = df_transacoes.copy()
            df_display['Data'] = df_display['Data'].dt.strftime('%d/%m/%Y')
            df_display = df_display[['id', 'Data', 'Categoria', 'Descricao', 'Valor', 'Cartao']]
            df_display.set_index('id', inplace=True)
            
            st.dataframe(df_display, use_container_width=True)
            
            st.markdown("#### Gerenciar Lançamentos")
            
            def format_option(id):
                if id not in df_display.index:
                    return "Selecione..."
                row = df_display.loc[id]
                return f"ID: {id} | {row['Data']} | {row['Descricao']} (R$ {row['Valor']:.2f})"
            
            id_list = df_display.index.tolist()

            tab_excluir, tab_alterar = st.tabs([" Excluir Transação 🗑️", " Alterar Transação ✏️"])

            with tab_excluir:
                if not id_list:
                    st.warning("Nenhuma transação no período selecionado para excluir.")
                else:
                    id_para_excluir = st.selectbox(
                        "Selecione a transação para EXCLUIR:", 
                        id_list,
                        format_func=format_option,
                        key="excluir_select"
                    )
                    if st.button("Excluir Transação Selecionada", type="primary"):
                        try:
                            delete_transaction(id_para_excluir)
                            st.success(f"Transação ID {id_para_excluir} excluída com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao excluir: {e}")

            with tab_alterar:
                if not id_list:
                    st.warning("Nenhuma transação no período selecionado para alterar.")
                else:
                    id_para_alterar = st.selectbox(
                        "Selecione a transação para ALTERAR:", 
                        id_list,
                        format_func=format_option,
                        key="alterar_select"
                    )
                    
                    if id_para_alterar:
                        conn = get_db_connection()
                        transacao = conn.execute("SELECT * FROM transacoes WHERE id = ?", (id_para_alterar,)).fetchone()
                        conn.close()
                        
                        if transacao:
                            default_date = datetime.strptime(transacao['Data'], "%Y-%m-%d").date()
                            default_valor = transacao['Valor']
                            default_descricao = transacao['Descricao']
                            default_cartao = transacao['Cartao']
                            default_categoria = transacao['Categoria']
                            is_receita = default_valor > 0
                            
                            with st.form("form_alterar"):
                                st.subheader(f"Alterando Transação ID: {id_para_alterar}")
                                
                                novo_data = st.date_input("Data", value=default_date, key="edit_data")
                                novo_descricao = st.text_input("Descrição", value=default_descricao, key="edit_desc")
                                
                                if is_receita:
                                    try: default_cat_index = CATEGORIAS_RECEITA.index(default_categoria)
                                    except ValueError: default_cat_index = 0
                                    novo_categoria = st.selectbox("Categoria", CATEGORIAS_RECEITA, index=default_cat_index, key="edit_cat_rec")
                                    novo_valor = st.number_input("Valor (R$)", min_value=0.01, value=default_valor, format="%.2f", key="edit_val_rec")
                                    novo_cartao = "N/A"
                                
                                else: # É Despesa
                                    try: default_cat_index = CATEGORIAS_DESPESA.index(default_categoria)
                                    except ValueError: default_cat_index = 0
                                    novo_categoria = st.selectbox("Categoria", CATEGORIAS_DESPESA, index=default_cat_index, key="edit_cat_des")
                                    
                                    try: default_cartao_index = CARTOES.index(default_cartao)
                                    except ValueError: default_cartao_index = 0
                                    novo_cartao = st.selectbox("Cartão", CARTOES, index=default_cartao_index, key="edit_cartao")
                                    
                                    novo_valor = st.number_input("Valor (R$)", min_value=0.01, value=abs(default_valor), format="%.2f", key="edit_val_des")
                                
                                submit_alterar = st.form_submit_button("Salvar Alterações")
                                
                                if submit_alterar:
                                    if not is_receita: novo_valor = novo_valor * -1
                                        
                                    update_transaction(
                                        id_para_alterar, novo_data.strftime("%Y-%m-%d"),
                                        novo_categoria, novo_descricao, novo_valor, novo_cartao
                                    )
                                    st.success("Transação alterada com sucesso!")
                                    st.rerun()

# =====================================================================
# --- PÁGINA 2: CARTÕES DE CRÉDITO ---
# =====================================================================
with tab_cartoes:
    today_cartoes = datetime.now()
    
    MESES_LISTA = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    MESES_MAP = {
        "Janeiro": "01", "Fevereiro": "02", "Março": "03", "Abril": "04",
        "Maio": "05", "Junho": "06", "Julho": "07", "Agosto": "08",
        "Setembro": "09", "Outubro": "10", "Novembro": "11", "Dezembro": "12"
    }
    current_year = today_cartoes.year

    with st.container(border=True):
        st.header("Cadastrar Fatura Mensal ✍️")
        st.info("Registre o valor *total* da sua fatura de cada cartão para comparar no gráfico de barras.")
        
        cartoes_de_credito = [c for c in CARTOES if c not in ["Nenhum (Débito/Dinheiro)", "Caju"]]

        if not cartoes_de_credito:
            st.warning("Nenhum cartão de crédito cadastrado na lista 'CARTOES'.")
        else:
            with st.form("form_fatura", clear_on_submit=True):
                col_form1, col_form2, col_form3 = st.columns(3)
                with col_form1:
                    cartao_fatura = st.selectbox(
                        "Cartão", cartoes_de_credito, key="fatura_cartao"
                    )
                
                with col_form2:
                    col_mes, col_ano = st.columns(2)
                    with col_mes:
                        mes_selecionado = st.selectbox(
                            "Mês", MESES_LISTA, index=today_cartoes.month - 1, key="fatura_mes"
                        )
                    with col_ano:
                        ano_selecionado = st.number_input(
                            "Ano", min_value=2020, max_value=current_year + 5, value=current_year, key="fatura_ano"
                        )

                with col_form3:
                    valor_fatura = st.number_input("Valor Total (R$)", min_value=0.01, format="%.2f", step=0.01, key="fatura_valor")
                
                submit_fatura = st.form_submit_button("Salvar Fatura")
                if submit_fatura:
                    mes_num = MESES_MAP[mes_selecionado]
                    mes_ano = f"{ano_selecionado}-{mes_num}"
                    
                    save_fatura(cartao_fatura, mes_ano, valor_fatura)
                    st.success(f"Fatura de {cartao_fatura} ({mes_ano}) salva!")
                    st.rerun()

    st.markdown("<br/>", unsafe_allow_html=True)

    with st.container(border=True):
        st.header("Comparativo de Faturas 📊")
        df_faturas = load_faturas()
        if df_faturas.empty:
            st.info("Nenhuma fatura cadastrada para exibir o gráfico.")
        else:
            fig_barras = px.bar(
                df_faturas.sort_values(by="MesAno"), 
                x="MesAno", y="ValorFatura", color="Cartao",
                barmode="group", title="Valor Mensal das Faturas por Cartão"
            )
            fig_barras.update_layout(template="plotly_dark")
            st.plotly_chart(fig_barras, use_container_width=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.header("Histórico de Gastos no Cartão 📑")
        df_full_transacoes = load_all_transactions()
        
        df_gastos_cartao = df_full_transacoes[
            (df_full_transacoes['Valor'] < 0) & 
            (df_full_transacoes['Cartao'] != "Nenhum (Débito/Dinheiro)")
        ].copy()

        if df_gastos_cartao.empty:
            st.info("Nenhum gasto individual no cartão foi registrado (na aba 'Adicionar Despesa').")
        else:
            cartoes_usados = df_gastos_cartao['Cartao'].unique()
            cartao_selecionado = st.selectbox("Filtrar por cartão:", ["Todos"] + list(cartoes_usados))
            
            if cartao_selecionado != "Todos":
                df_gastos_cartao = df_gastos_cartao[df_gastos_cartao['Cartao'] == cartao_selecionado]

            df_gastos_cartao['Data'] = df_gastos_cartao['Data'].dt.strftime('%d/%m/%Y')
            st.dataframe(
                df_gastos_cartao[['Data', 'Categoria', 'Descricao', 'Valor', 'Cartao']].sort_values(by="Data", ascending=False),
                use_container_width=True
            )

# =====================================================================
# --- PÁGINA 3: ORÇAMENTO ---
# =====================================================================
with tab_orcamento:
    st.title("🎯 Orçamento Mensal")
    today_orcamento = datetime.now()

    with st.container(border=True):
        st.header("Definir Limite de Gasto ✍️")
        with st.form("form_orcamento", clear_on_submit=True):
            col_form1, col_form2 = st.columns(2)
            with col_form1:
                categorias_orcamento = [c for c in CATEGORIAS_DESPESA if c != 'Fatura Cartão']
                categoria = st.selectbox("Categoria", categorias_orcamento)
            with col_form2:
                valor = st.number_input("Limite Mensal (R$)", min_value=0.01, format="%.2f", step=0.01)
            
            submit_orcamento = st.form_submit_button("Salvar Orçamento")
            if submit_orcamento:
                save_budget(categoria, valor)
                st.success(f"Orçamento para '{categoria}' salvo como R$ {valor:,.2f}")
                st.rerun()

    st.markdown("<br/>", unsafe_allow_html=True)

    with st.container(border=True):
        st.header(f"Acompanhamento do Orçamento (Mês Atual: {today_orcamento.strftime('%B/%Y')})")
        
        df_orcamentos = load_budgets()
        
        if df_orcamentos.empty:
            st.info("Nenhum orçamento definido. Adicione limites no formulário acima.")
        else:
            start_of_month_str = today_orcamento.replace(day=1).strftime("%Y-%m-%d")
            end_of_month_str = today_orcamento.strftime("%Y-%m-%d")
            
            df_transacoes_mes = load_transactions(start_of_month_str, end_of_month_str)
            
            df_gastos_mes = df_transacoes_mes[
                (df_transacoes_mes['Valor'] < 0) & 
                (df_transacoes_mes['Categoria'] != 'Fatura Cartão')
            ].copy()
            
            if df_gastos_mes.empty:
                df_gastos_mes_sum = pd.DataFrame(columns=['Categoria', 'Gasto'])
            else:
                df_gastos_mes['Gasto'] = df_gastos_mes['Valor'].abs()
                df_gastos_mes_sum = df_gastos_mes.groupby('Categoria')['Gasto'].sum().reset_index()

            df_comparativo = pd.merge(
                df_orcamentos, 
                df_gastos_mes_sum, 
                on='Categoria', 
                how='left'
            )
            
            df_comparativo['Gasto'] = df_comparativo['Gasto'].fillna(0)
            df_comparativo['Restante'] = df_comparativo['Valor'] - df_comparativo['Gasto']
            df_comparativo['Progresso'] = (df_comparativo['Gasto'] / df_comparativo['Valor']).clip(0, 1)

            df_comparativo.rename(columns={'Valor': 'Orçado (R$)', 'Gasto': 'Gasto (R$)', 'Restante': 'Restante (R$)'}, inplace=True)

            st.dataframe(
                df_comparativo[['Categoria', 'Orçado (R$)', 'Gasto (R$)', 'Restante (R$)', 'Progresso']],
                use_container_width=True,
                column_config={
                    "Progresso": st.column_config.ProgressColumn(
                        "Progresso",
                        format="%.0f%%",
                        min_val=0,
                        max_val=1,
                    ),
                    "Orçado (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                    "Gasto (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                    "Restante (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                }
            )

            st.markdown("### Detalhes do Progresso")
            for index, row in df_comparativo.iterrows():
                st.markdown(f"**{row['Categoria']}** (Restante: R$ {row['Restante (R$)']:,.2f})")
                
                if row['Progresso'] >= 1.0:
                    st.error(f"Gasto: R$ {row['Gasto (R$)']:,.2f} de R$ {row['Orçado (R$)']:,.2f}")
                    st.progress(1.0)
                else:
                    st.success(f"Gasto: R$ {row['Gasto (R$)']:,.2f} de R$ {row['Orçado (R$)']:,.2f}")
                    st.progress(row['Progresso'])