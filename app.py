"""
Sistema de PDV (Ponto de Venda) e Controle Financeiro para Cafeteria
Versão 2.0 — Com gestão completa de estoque e interface aprimorada.
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
# CSS PERSONALIZADO — deixa a interface mais profissional
# =========================================================
st.markdown("""
    <style>
        /* Botão primário (verde) */
        div.stButton > button[kind="primary"] {
            background-color: #2e7d32;
            color: white;
            border: none;
            padding: 0.6rem 1.2rem;
            font-size: 1rem;
            border-radius: 8px;
            width: 100%;
        }
        div.stButton > button[kind="primary"]:hover {
            background-color: #1b5e20;
        }

        /* Botão secundário (cinza escuro) */
        div.stButton > button[kind="secondary"] {
            background-color: #37474f;
            color: white;
            border: none;
            border-radius: 8px;
            width: 100%;
        }
        div.stButton > button[kind="secondary"]:hover {
            background-color: #263238;
        }

        /* Card de métrica */
        [data-testid="stMetric"] {
            background-color: #f5f5f5;
            border-radius: 10px;
            padding: 12px 16px;
            border-left: 4px solid #2e7d32;
        }

        /* Cabeçalho da sidebar */
        section[data-testid="stSidebar"] .stRadio label {
            font-size: 1rem;
        }

        /* Tabela de últimas vendas */
        .vendas-recentes {
            background: #fafafa;
            border-radius: 10px;
            padding: 1rem;
            border: 1px solid #e0e0e0;
        }
    </style>
""", unsafe_allow_html=True)


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
    Inicializa o banco: cria tabelas se não existirem.
    Nenhum produto pré-cadastrado — o usuário cadastra os seus próprios.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            preco REAL NOT NULL,
            estoque INTEGER NOT NULL DEFAULT 0
        )
    """)

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
    conn.close()


def carregar_produtos():
    """Retorna DataFrame com todos os produtos."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM produtos ORDER BY nome", conn)
    conn.close()
    return df


def carregar_vendas():
    """Retorna DataFrame com histórico de vendas."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM vendas ORDER BY id DESC", conn)
    conn.close()
    return df


def registrar_venda(produto_nome, quantidade, preco_unitario, forma_pagamento):
    """Registra venda e dá baixa no estoque em uma única transação."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT estoque FROM produtos WHERE nome = ?", (produto_nome,))
        row = cursor.fetchone()
        if not row:
            return False, "Produto não encontrado."
        if row[0] < quantidade:
            return False, f"Estoque insuficiente. Disponível: {row[0]} unidade(s)."

        valor_total = round(quantidade * preco_unitario, 2)
        data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO vendas (data_hora, produto, quantidade, valor_unitario, valor_total, forma_pagamento)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (data_hora, produto_nome, quantidade, preco_unitario, valor_total, forma_pagamento))

        cursor.execute(
            "UPDATE produtos SET estoque = estoque - ? WHERE nome = ?",
            (quantidade, produto_nome)
        )
        conn.commit()
        return True, f"Venda registrada! Total: R$ {valor_total:.2f}"
    except Exception as e:
        conn.rollback()
        return False, f"Erro: {e}"
    finally:
        conn.close()


def cadastrar_produto(nome, preco, estoque):
    """Cadastra novo produto."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO produtos (nome, preco, estoque) VALUES (?, ?, ?)",
            (nome, preco, estoque)
        )
        conn.commit()
        return True, f"Produto '{nome}' cadastrado com sucesso!"
    except sqlite3.IntegrityError:
        return False, f"Já existe um produto com o nome '{nome}'."
    finally:
        conn.close()


def remover_produto(produto_id):
    """Remove um produto do estoque pelo ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    conn.commit()
    conn.close()


def ajustar_estoque(produto_id, novo_estoque):
    """Define manualmente a quantidade em estoque de um produto."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE produtos SET estoque = ? WHERE id = ?",
        (novo_estoque, produto_id)
    )
    conn.commit()
    conn.close()


def adicionar_estoque(produto_id, quantidade):
    """Soma quantidade ao estoque atual de um produto."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE produtos SET estoque = estoque + ? WHERE id = ?",
        (quantidade, produto_id)
    )
    conn.commit()
    conn.close()


def remover_estoque(produto_id, quantidade):
    """
    Remove quantidade do estoque manualmente.
    Retorna False se a quantidade pedida for maior que o estoque atual.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT estoque FROM produtos WHERE id = ?", (produto_id,))
    atual = cursor.fetchone()[0]
    if quantidade > atual:
        conn.close()
        return False, f"Não é possível remover {quantidade} — estoque atual é {atual}."
    cursor.execute(
        "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
        (quantidade, produto_id)
    )
    conn.commit()
    conn.close()
    return True, "Estoque atualizado."


# =========================================================
# INICIALIZAÇÃO
# =========================================================
init_db()

# Session state para mensagens de feedback
for key in ["feedback_msg", "feedback_type", "confirmar_remocao_id"]:
    if key not in st.session_state:
        st.session_state[key] = None


# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.title("☕ Cafeteria PDV")
st.sidebar.markdown("---")
pagina = st.sidebar.radio(
    "Menu",
    ["🛒 Registro de Vendas", "📦 Estoque", "📊 Relatório Financeiro"]
)
st.sidebar.markdown("---")
st.sidebar.caption(f"Banco: `{os.path.basename(DB_PATH)}`")


# =========================================================
# PÁGINA 1 — REGISTRO DE VENDAS
# =========================================================
if pagina == "🛒 Registro de Vendas":

    st.title("🛒 Registro de Vendas")

    # Exibe feedback da última ação
    if st.session_state.feedback_msg:
        fn = st.success if st.session_state.feedback_type == "success" else st.error
        fn(st.session_state.feedback_msg)
        st.session_state.feedback_msg = None
        st.session_state.feedback_type = None

    produtos_df = carregar_produtos()

    if produtos_df.empty:
        st.warning("⚠️ Nenhum produto cadastrado. Acesse **Estoque** para adicionar produtos.")
    else:
        # ---- Formulário de venda ----
        with st.container(border=True):
            st.subheader("Nova Venda")

            col1, col2 = st.columns([3, 2])

            with col1:
                # Monta a lista do selectbox com nome + preço
                opcoes = {
                    f"{r['nome']}  ·  R$ {r['preco']:.2f}": r
                    for _, r in produtos_df.iterrows()
                }
                escolha = st.selectbox("🏷️ Produto", list(opcoes.keys()))
                produto = opcoes[escolha]
                estoque_disp = int(produto["estoque"])
                preco_unit = float(produto["preco"])

            with col2:
                quantidade = st.number_input(
                    "📦 Quantidade",
                    min_value=1,
                    max_value=max(estoque_disp, 1),
                    value=1,
                    step=1,
                    disabled=(estoque_disp == 0)
                )

            # Formas de pagamento como botões de seleção visual
            st.markdown("**💳 Forma de Pagamento**")
            pagamentos = ["Pix", "Cartão de Débito", "Cartão de Crédito", "Dinheiro"]

            if "forma_pagamento" not in st.session_state:
                st.session_state.forma_pagamento = "Pix"

            cols_pag = st.columns(4)
            for i, forma in enumerate(pagamentos):
                with cols_pag[i]:
                    selecionado = st.session_state.forma_pagamento == forma
                    estilo = "primary" if selecionado else "secondary"
                    if st.button(forma, key=f"pag_{forma}", type=estilo):
                        st.session_state.forma_pagamento = forma
                        st.rerun()

            st.markdown("---")

            # Resumo do valor
            valor_total = preco_unit * quantidade
            col_r1, col_r2, col_r3 = st.columns(3)
            col_r1.metric("Preço unitário", f"R$ {preco_unit:.2f}")
            col_r2.metric("Quantidade", quantidade)
            col_r3.metric("💰 Total da Venda", f"R$ {valor_total:.2f}")

            st.markdown("")

            # Botão de confirmar
            if estoque_disp == 0:
                st.error("❌ Produto sem estoque disponível.")
            else:
                if st.button(
                    f"✅  Confirmar Venda · R$ {valor_total:.2f}  ({st.session_state.forma_pagamento})",
                    type="primary",
                    use_container_width=True
                ):
                    sucesso, msg = registrar_venda(
                        produto_nome=produto["nome"],
                        quantidade=int(quantidade),
                        preco_unitario=preco_unit,
                        forma_pagamento=st.session_state.forma_pagamento
                    )
                    st.session_state.feedback_msg = msg
                    st.session_state.feedback_type = "success" if sucesso else "error"
                    st.rerun()

        # ---- Últimas 10 vendas ----
        st.markdown("")
        st.subheader("🕐 Últimas 10 Vendas")

        vendas_df = carregar_vendas()
        if vendas_df.empty:
            st.info("Nenhuma venda registrada ainda.")
        else:
            ultimas = vendas_df.head(10)[
                ["data_hora", "produto", "quantidade", "valor_total", "forma_pagamento"]
            ].rename(columns={
                "data_hora": "Data/Hora",
                "produto": "Produto",
                "quantidade": "Qtd.",
                "valor_total": "Total (R$)",
                "forma_pagamento": "Pagamento"
            })
            st.dataframe(ultimas, use_container_width=True, hide_index=True)


# =========================================================
# PÁGINA 2 — ESTOQUE
# =========================================================
elif pagina == "📦 Estoque":

    st.title("📦 Gestão de Estoque")

    # Feedback
    if st.session_state.feedback_msg:
        fn = st.success if st.session_state.feedback_type == "success" else st.error
        fn(st.session_state.feedback_msg)
        st.session_state.feedback_msg = None
        st.session_state.feedback_type = None

    tab_lista, tab_novo = st.tabs(["📋 Produtos em Estoque", "➕ Cadastrar Novo Produto"])

    # ---- ABA 1: Lista de produtos ----
    with tab_lista:
        produtos_df = carregar_produtos()

        if produtos_df.empty:
            st.info("Nenhum produto cadastrado. Use a aba ao lado para adicionar.")
        else:
            # Alerta de estoque baixo
            baixo = produtos_df[produtos_df["estoque"] <= 5]
            if not baixo.empty:
                nomes_baixo = ", ".join(baixo["nome"].tolist())
                st.warning(f"⚠️ Estoque crítico (≤ 5 un.): **{nomes_baixo}**")

            st.markdown("---")

            # Renderiza cada produto em um card com ações
            for _, row in produtos_df.iterrows():
                pid = int(row["id"])
                nome = row["nome"]
                preco = float(row["preco"])
                estoque_atual = int(row["estoque"])

                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 3, 2])

                    with c1:
                        st.markdown(f"**{nome}**")
                        st.caption(f"R$ {preco:.2f} por unidade")

                    with c2:
                        # Indicador visual de estoque
                        cor = "🟢" if estoque_atual > 10 else ("🟡" if estoque_atual > 0 else "🔴")
                        st.markdown(f"{cor} **Estoque:** {estoque_atual} unidades")

                        # Botões de adicionar / remover quantidade
                        col_add, col_rem = st.columns(2)
                        with col_add:
                            qtd_add = st.number_input(
                                "Adicionar", min_value=1, value=1, step=1,
                                key=f"add_{pid}", label_visibility="collapsed"
                            )
                            if st.button("➕ Adicionar", key=f"btn_add_{pid}", use_container_width=True):
                                adicionar_estoque(pid, int(qtd_add))
                                st.session_state.feedback_msg = f"'{nome}': +{qtd_add} unidades adicionadas."
                                st.session_state.feedback_type = "success"
                                st.rerun()

                        with col_rem:
                            qtd_rem = st.number_input(
                                "Remover", min_value=1, value=1, step=1,
                                key=f"rem_{pid}", label_visibility="collapsed"
                            )
                            if st.button("➖ Remover", key=f"btn_rem_{pid}", use_container_width=True):
                                ok, msg = remover_estoque(pid, int(qtd_rem))
                                st.session_state.feedback_msg = msg
                                st.session_state.feedback_type = "success" if ok else "error"
                                st.rerun()

                    with c3:
                        st.markdown("")
                        st.markdown("")
                        # Botão de excluir o produto do sistema
                        if st.session_state.confirmar_remocao_id == pid:
                            # Pede confirmação antes de deletar
                            st.warning("Confirma exclusão?")
                            col_sim, col_nao = st.columns(2)
                            with col_sim:
                                if st.button("✔ Sim", key=f"sim_{pid}", use_container_width=True):
                                    remover_produto(pid)
                                    st.session_state.confirmar_remocao_id = None
                                    st.session_state.feedback_msg = f"'{nome}' removido do sistema."
                                    st.session_state.feedback_type = "success"
                                    st.rerun()
                            with col_nao:
                                if st.button("✖ Não", key=f"nao_{pid}", use_container_width=True):
                                    st.session_state.confirmar_remocao_id = None
                                    st.rerun()
                        else:
                            if st.button(
                                "🗑️ Excluir Produto",
                                key=f"del_{pid}",
                                use_container_width=True,
                                type="secondary"
                            ):
                                st.session_state.confirmar_remocao_id = pid
                                st.rerun()

    # ---- ABA 2: Cadastrar novo produto ----
    with tab_novo:
        st.subheader("Cadastrar Novo Produto")
        with st.form("form_novo_produto", clear_on_submit=True):
            nome_novo = st.text_input("Nome do produto", placeholder="Ex: Cappuccino")
            col_p, col_e = st.columns(2)
            with col_p:
                preco_novo = st.number_input(
                    "Preço (R$)", min_value=0.01, step=0.50,
                    format="%.2f", value=5.00
                )
            with col_e:
                estoque_novo = st.number_input(
                    "Estoque inicial (unidades)", min_value=0, step=1, value=0
                )

            if st.form_submit_button("✅ Cadastrar Produto", type="primary", use_container_width=True):
                if not nome_novo.strip():
                    st.error("Informe o nome do produto.")
                else:
                    ok, msg = cadastrar_produto(nome_novo.strip(), float(preco_novo), int(estoque_novo))
                    st.session_state.feedback_msg = msg
                    st.session_state.feedback_type = "success" if ok else "error"
                    st.rerun()


# =========================================================
# PÁGINA 3 — RELATÓRIO FINANCEIRO
# =========================================================
elif pagina == "📊 Relatório Financeiro":

    st.title("📊 Relatório Financeiro")

    vendas_df = carregar_vendas()

    if vendas_df.empty:
        st.info("Nenhuma venda registrada ainda. O relatório aparecerá assim que houver vendas.")
    else:
        vendas_df["data_hora"] = pd.to_datetime(vendas_df["data_hora"])
        vendas_df["data"] = vendas_df["data_hora"].dt.date

        # Filtro de período
        with st.container(border=True):
            st.markdown("**🗓️ Filtrar por período**")
            col_d1, col_d2 = st.columns(2)
            data_min = vendas_df["data"].min()
            data_max = vendas_df["data"].max()
            with col_d1:
                data_inicio = st.date_input("De", value=data_min, min_value=data_min, max_value=data_max)
            with col_d2:
                data_fim = st.date_input("Até", value=data_max, min_value=data_min, max_value=data_max)

        df = vendas_df[
            (vendas_df["data"] >= data_inicio) & (vendas_df["data"] <= data_fim)
        ]

        st.markdown("---")

        # Métricas principais
        faturamento = df["valor_total"].sum()
        qtd_vendas = len(df)
        ticket_medio = faturamento / qtd_vendas if qtd_vendas > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Faturamento Total", f"R$ {faturamento:.2f}")
        col2.metric("🧾 Nº de Vendas", qtd_vendas)
        col3.metric("📈 Ticket Médio", f"R$ {ticket_medio:.2f}")

        st.markdown("---")

        # Resumo por forma de pagamento
        st.subheader("💳 Recebimentos por Forma de Pagamento")
        resumo_pag = (
            df.groupby("forma_pagamento")["valor_total"]
            .agg(["sum", "count"])
            .reset_index()
            .rename(columns={
                "forma_pagamento": "Forma de Pagamento",
                "sum": "Total Recebido (R$)",
                "count": "Nº de Vendas"
            })
            .sort_values("Total Recebido (R$)", ascending=False)
        )
        st.dataframe(resumo_pag, use_container_width=True, hide_index=True)

        st.markdown("---")

        # Produtos mais vendidos
        st.subheader("🏆 Produtos Mais Vendidos")
        resumo_prod = (
            df.groupby("produto")
            .agg(Quantidade=("quantidade", "sum"), Faturamento=("valor_total", "sum"))
            .reset_index()
            .rename(columns={"produto": "Produto"})
            .sort_values("Quantidade", ascending=False)
        )
        st.dataframe(resumo_prod, use_container_width=True, hide_index=True)

        st.markdown("---")

        # Histórico detalhado
        st.subheader("📋 Histórico Detalhado")
        historico = (
            df[["data_hora", "produto", "quantidade", "valor_unitario", "valor_total", "forma_pagamento"]]
            .rename(columns={
                "data_hora": "Data/Hora",
                "produto": "Produto",
                "quantidade": "Qtd.",
                "valor_unitario": "Vlr. Unit. (R$)",
                "valor_total": "Vlr. Total (R$)",
                "forma_pagamento": "Pagamento"
            })
            .sort_values("Data/Hora", ascending=False)
        )
        st.dataframe(historico, use_container_width=True, hide_index=True)

        # Exportar CSV
        st.markdown("")
        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="⬇️ Baixar relatório em CSV",
            data=csv,
            file_name=f"relatorio_{data_inicio}_a_{data_fim}.csv",
            mime="text/csv",
            use_container_width=True
        )
