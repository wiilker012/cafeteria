"""
Sistema de PDV (Ponto de Venda) e Controle Financeiro para Cafeteria
Autor: Desenvolvido com Streamlit + SQLite
Descrição: Registro de vendas, controle de estoque e relatório financeiro.
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os

# =========================================================
# CONFIGURAÇÕES GERAIS
# =========================================================
st.set_page_config(
    page_title="PDV Cafeteria",
    page_icon="☕",
    layout="wide"
)

DB_PATH = "cafeteria.db"


# =========================================================
# CAMADA DE DADOS (SQLite)
# =========================================================

def get_connection():
    """Cria e retorna uma conexão com o banco SQLite."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """
    Inicializa o banco de dados: cria as tabelas (caso não existam)
    e popula o estoque inicial apenas na primeira execução.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Tabela de produtos / estoque
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            preco REAL NOT NULL,
            estoque INTEGER NOT NULL
        )
    """)

    # Tabela de vendas (histórico)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TEXT NOT NULL,
            produto TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            valor_unitario REAL NOT NULL,
            valor_total REAL NOT NULL,
            forma_pagamento TEXT NOT NULL
        )
    """)

    conn.commit()

    # Verifica se já existem produtos cadastrados.
    # Se não, cadastra o estoque inicial padrão (apenas na 1ª execução).
    cursor.execute("SELECT COUNT(*) FROM produtos")
    total_produtos = cursor.fetchone()[0]

    if total_produtos == 0:
        estoque_inicial = [
            ("Café Expresso", 5.00, 100),
            ("Café com Leite", 7.00, 80),
            ("Pão de Queijo", 6.50, 50),
            ("Bolo (fatia)", 8.00, 30),
            ("Suco Natural", 9.00, 40),
            ("Croissant", 10.00, 25),
        ]
        cursor.executemany(
            "INSERT INTO produtos (nome, preco, estoque) VALUES (?, ?, ?)",
            estoque_inicial
        )
        conn.commit()

    conn.close()


def carregar_produtos():
    """Retorna um DataFrame com todos os produtos e estoque atual."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM produtos ORDER BY nome", conn)
    conn.close()
    return df


def carregar_vendas():
    """Retorna um DataFrame com o histórico completo de vendas."""
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM vendas ORDER BY id DESC", conn
    )
    conn.close()
    return df


def registrar_venda(produto_nome, quantidade, preco_unitario, forma_pagamento):
    """
    Registra uma nova venda no banco e dá baixa no estoque.
    Operação feita dentro de uma transação para garantir consistência:
    só confirma se a venda E a baixa de estoque derem certo.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Verifica estoque atual antes de confirmar (evita estoque negativo
        # caso duas abas/usuários tentem vender ao mesmo tempo)
        cursor.execute(
            "SELECT estoque FROM produtos WHERE nome = ?", (produto_nome,)
        )
        estoque_atual = cursor.fetchone()[0]

        if estoque_atual < quantidade:
            conn.close()
            return False, f"Estoque insuficiente. Disponível: {estoque_atual} unidade(s)."

        valor_total = round(quantidade * preco_unitario, 2)
        data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Insere a venda no histórico
        cursor.execute("""
            INSERT INTO vendas (data_hora, produto, quantidade, valor_unitario, valor_total, forma_pagamento)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (data_hora, produto_nome, quantidade, preco_unitario, valor_total, forma_pagamento))

        # Dá baixa no estoque
        cursor.execute("""
            UPDATE produtos SET estoque = estoque - ? WHERE nome = ?
        """, (quantidade, produto_nome))

        conn.commit()
        conn.close()
        return True, f"Venda registrada com sucesso! Total: R$ {valor_total:.2f}"

    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Erro ao registrar venda: {e}"


def atualizar_estoque_produto(produto_id, novo_estoque):
    """Atualiza manualmente o estoque de um produto (reposição)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE produtos SET estoque = ? WHERE id = ?",
        (novo_estoque, produto_id)
    )
    conn.commit()
    conn.close()


def cadastrar_produto(nome, preco, estoque):
    """Cadastra um novo produto no sistema."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO produtos (nome, preco, estoque) VALUES (?, ?, ?)",
            (nome, preco, estoque)
        )
        conn.commit()
        sucesso = True
        msg = f"Produto '{nome}' cadastrado com sucesso!"
    except sqlite3.IntegrityError:
        sucesso = False
        msg = f"Já existe um produto chamado '{nome}'."
    conn.close()
    return sucesso, msg


# =========================================================
# INICIALIZAÇÃO DO BANCO (executa uma única vez por processo)
# =========================================================
init_db()


# =========================================================
# SESSION STATE
# =========================================================
# Guarda mensagens de feedback (sucesso/erro) entre reruns do Streamlit,
# evitando que a mensagem suma ou que o formulário "trave" após o submit.
if "feedback_msg" not in st.session_state:
    st.session_state.feedback_msg = None
if "feedback_type" not in st.session_state:
    st.session_state.feedback_type = None


# =========================================================
# INTERFACE - SIDEBAR
# =========================================================
st.sidebar.title("☕ Cafeteria PDV")
pagina = st.sidebar.radio(
    "Navegação",
    ["🛒 Registrar Venda", "📦 Estoque", "📊 Relatório Financeiro"]
)

st.sidebar.markdown("---")
st.sidebar.caption(f"Banco de dados: `{os.path.abspath(DB_PATH)}`")


# =========================================================
# PÁGINA 1 - REGISTRAR VENDA
# =========================================================
if pagina == "🛒 Registrar Venda":
    st.title("🛒 Registro de Vendas")

    # Exibe mensagem de feedback da última ação, se houver
    if st.session_state.feedback_msg:
        if st.session_state.feedback_type == "success":
            st.success(st.session_state.feedback_msg)
        else:
            st.error(st.session_state.feedback_msg)
        # Limpa a mensagem após exibir, para não persistir indefinidamente
        st.session_state.feedback_msg = None
        st.session_state.feedback_type = None

    produtos_df = carregar_produtos()

    if produtos_df.empty:
        st.warning("Nenhum produto cadastrado. Vá até a aba 'Estoque' para cadastrar produtos.")
    else:
        col1, col2 = st.columns([2, 1])

        with col1:
            # Selectbox com produto + preço para facilitar a visualização
            opcoes_produtos = {
                f"{row['nome']} — R$ {row['preco']:.2f} (estoque: {row['estoque']})": row
                for _, row in produtos_df.iterrows()
            }
            escolha = st.selectbox("Produto", list(opcoes_produtos.keys()))
            produto_selecionado = opcoes_produtos[escolha]

            estoque_disponivel = int(produto_selecionado["estoque"])

            quantidade = st.number_input(
                "Quantidade",
                min_value=1,
                max_value=max(estoque_disponivel, 1),
                value=1,
                step=1,
                disabled=(estoque_disponivel == 0)
            )

            forma_pagamento = st.selectbox(
                "Forma de Pagamento",
                ["Pix", "Cartão", "Dinheiro"]
            )

        with col2:
            preco_unitario = float(produto_selecionado["preco"])
            valor_total = preco_unitario * quantidade

            st.metric("Valor Unitário", f"R$ {preco_unitario:.2f}")
            st.metric("Valor Total da Venda", f"R$ {valor_total:.2f}")

        st.markdown("---")

        if estoque_disponivel == 0:
            st.error("Produto sem estoque disponível para venda.")
        else:
            if st.button("✅ Confirmar Venda", type="primary", use_container_width=True):
                sucesso, mensagem = registrar_venda(
                    produto_nome=produto_selecionado["nome"],
                    quantidade=int(quantidade),
                    preco_unitario=preco_unitario,
                    forma_pagamento=forma_pagamento
                )
                # Guarda o resultado no session_state e força um rerun.
                # Isso garante que o estoque exibido na tela seja atualizado
                # imediatamente, sem duplicar a venda em cliques acidentais.
                st.session_state.feedback_msg = mensagem
                st.session_state.feedback_type = "success" if sucesso else "error"
                st.rerun()

    st.markdown("---")
    st.subheader("Últimas vendas registradas")
    vendas_df = carregar_vendas()
    if not vendas_df.empty:
        st.dataframe(
            vendas_df.head(10),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Nenhuma venda registrada ainda.")


# =========================================================
# PÁGINA 2 - ESTOQUE
# =========================================================
elif pagina == "📦 Estoque":
    st.title("📦 Controle de Estoque")

    tab1, tab2 = st.tabs(["Estoque Atual", "Cadastrar Novo Produto"])

    # --- Aba 1: Visualizar e repor estoque ---
    with tab1:
        produtos_df = carregar_produtos()

        if produtos_df.empty:
            st.info("Nenhum produto cadastrado ainda.")
        else:
            st.dataframe(
                produtos_df.rename(columns={
                    "id": "ID", "nome": "Produto", "preco": "Preço (R$)", "estoque": "Estoque"
                }),
                use_container_width=True,
                hide_index=True
            )

            # Alerta visual para produtos com estoque baixo
            baixo_estoque = produtos_df[produtos_df["estoque"] <= 10]
            if not baixo_estoque.empty:
                nomes = ", ".join(baixo_estoque["nome"].tolist())
                st.warning(f"⚠️ Estoque baixo (≤10 un.) para: {nomes}")

            st.markdown("---")
            st.subheader("Repor / Ajustar estoque")

            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                produto_para_ajustar = st.selectbox(
                    "Selecione o produto",
                    produtos_df["nome"].tolist(),
                    key="ajuste_produto"
                )
            linha = produtos_df[produtos_df["nome"] == produto_para_ajustar].iloc[0]

            with col2:
                quantidade_adicionar = st.number_input(
                    "Adicionar ao estoque",
                    min_value=0,
                    value=0,
                    step=1,
                    key="ajuste_quantidade"
                )
            with col3:
                st.write("")  # alinhamento vertical do botão
                st.write("")
                if st.button("➕ Repor Estoque", use_container_width=True):
                    novo_estoque = int(linha["estoque"]) + int(quantidade_adicionar)
                    atualizar_estoque_produto(int(linha["id"]), novo_estoque)
                    st.success(f"Estoque de '{produto_para_ajustar}' atualizado para {novo_estoque} unidades.")
                    st.rerun()

    # --- Aba 2: Cadastrar novo produto ---
    with tab2:
        with st.form("form_novo_produto", clear_on_submit=True):
            nome_novo = st.text_input("Nome do produto")
            preco_novo = st.number_input("Preço (R$)", min_value=0.01, step=0.50, format="%.2f")
            estoque_novo = st.number_input("Estoque inicial", min_value=0, step=1)

            enviado = st.form_submit_button("Cadastrar Produto")

            if enviado:
                if not nome_novo.strip():
                    st.error("Informe o nome do produto.")
                else:
                    sucesso, msg = cadastrar_produto(nome_novo.strip(), float(preco_novo), int(estoque_novo))
                    if sucesso:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)


# =========================================================
# PÁGINA 3 - RELATÓRIO FINANCEIRO
# =========================================================
elif pagina == "📊 Relatório Financeiro":
    st.title("📊 Relatório Financeiro")

    vendas_df = carregar_vendas()

    if vendas_df.empty:
        st.info("Nenhuma venda registrada ainda. O relatório aparecerá aqui assim que houver vendas.")
    else:
        # Converte a coluna de data para filtragem
        vendas_df["data_hora"] = pd.to_datetime(vendas_df["data_hora"])
        vendas_df["data"] = vendas_df["data_hora"].dt.date

        # --- Filtro de período ---
        col_f1, col_f2 = st.columns(2)
        data_min = vendas_df["data"].min()
        data_max = vendas_df["data"].max()

        with col_f1:
            data_inicio = st.date_input("Data inicial", value=data_min, min_value=data_min, max_value=data_max)
        with col_f2:
            data_fim = st.date_input("Data final", value=data_max, min_value=data_min, max_value=data_max)

        df_filtrado = vendas_df[
            (vendas_df["data"] >= data_inicio) & (vendas_df["data"] <= data_fim)
        ]

        st.markdown("---")

        # --- Métricas principais ---
        faturamento_total = df_filtrado["valor_total"].sum()
        qtd_vendas = len(df_filtrado)
        ticket_medio = faturamento_total / qtd_vendas if qtd_vendas > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Faturamento Total", f"R$ {faturamento_total:.2f}")
        col2.metric("🧾 Nº de Vendas", qtd_vendas)
        col3.metric("📈 Ticket Médio", f"R$ {ticket_medio:.2f}")

        st.markdown("---")

        # --- Resumo por forma de pagamento ---
        st.subheader("Recebimentos por Forma de Pagamento")

        resumo_pagamento = (
            df_filtrado.groupby("forma_pagamento")["valor_total"]
            .sum()
            .reset_index()
            .rename(columns={"forma_pagamento": "Forma de Pagamento", "valor_total": "Total (R$)"})
            .sort_values("Total (R$)", ascending=False)
        )

        col_a, col_b = st.columns([1, 1])
        with col_a:
            st.dataframe(resumo_pagamento, use_container_width=True, hide_index=True)
        with col_b:
            st.bar_chart(resumo_pagamento.set_index("Forma de Pagamento"))

        st.markdown("---")

        # --- Produtos mais vendidos ---
        st.subheader("Produtos Mais Vendidos (por quantidade)")
        resumo_produtos = (
            df_filtrado.groupby("produto")
            .agg(Quantidade=("quantidade", "sum"), Faturamento=("valor_total", "sum"))
            .reset_index()
            .rename(columns={"produto": "Produto"})
            .sort_values("Quantidade", ascending=False)
        )
        st.dataframe(resumo_produtos, use_container_width=True, hide_index=True)

        st.markdown("---")

        # --- Histórico completo de vendas no período ---
        st.subheader("Histórico Detalhado de Vendas")
        st.dataframe(
            df_filtrado[["data_hora", "produto", "quantidade", "valor_unitario", "valor_total", "forma_pagamento"]]
            .rename(columns={
                "data_hora": "Data/Hora", "produto": "Produto", "quantidade": "Qtd.",
                "valor_unitario": "Valor Unit. (R$)", "valor_total": "Valor Total (R$)",
                "forma_pagamento": "Pagamento"
            })
            .sort_values("Data/Hora", ascending=False),
            use_container_width=True,
            hide_index=True
        )

        # --- Exportar relatório em CSV ---
        csv = df_filtrado.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="⬇️ Baixar relatório em CSV",
            data=csv,
            file_name=f"relatorio_vendas_{data_inicio}_a_{data_fim}.csv",
            mime="text/csv"
        )
