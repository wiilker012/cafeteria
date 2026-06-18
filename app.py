"""
Sistema de PDV - Cafeteria
Versão 3.0 — Paleta terrosa, sidebar com botões, métricas corrigidas.
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
# CSS — Paleta terrosa/pastel + correção das métricas
# =========================================================
st.markdown("""
<style>
    /* ---- Paleta de cores ---- */
    :root {
        --marrom-escuro:   #6B4C35;
        --marrom-medio:    #8B6347;
        --marrom-claro:    #C4956A;
        --creme:           #F5ECD7;
        --bege:            #EDE0CC;
        --areia:           #D9C4A8;
        --terracota:       #B5714E;
        --terracota-claro: #D4906E;
        --verde-sage:      #7A8C6E;
        --branco-quente:   #FDF6EC;
        --texto-escuro:    #3E2A1A;
        --texto-medio:     #6B4C35;
    }

    /* ---- Fundo geral ---- */
    .stApp {
        background-color: var(--branco-quente);
    }

    /* ---- Sidebar ---- */
    section[data-testid="stSidebar"] {
        background-color: var(--marrom-escuro) !important;
    }
    section[data-testid="stSidebar"] * {
        color: var(--creme) !important;
    }

    /* ---- Botões da sidebar ---- */
    section[data-testid="stSidebar"] .stButton > button {
        background-color: rgba(255,255,255,0.08);
        color: var(--creme) !important;
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 8px;
        width: 100%;
        text-align: left;
        padding: 0.6rem 1rem;
        font-size: 0.95rem;
        margin-bottom: 4px;
        transition: background 0.2s;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background-color: rgba(255,255,255,0.18) !important;
        border-color: var(--areia) !important;
    }

    /* Botão ativo na sidebar */
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background-color: var(--marrom-claro) !important;
        color: white !important;
        border-color: var(--marrom-claro) !important;
        font-weight: bold;
    }

    /* ---- Botão primário (confirmar venda etc.) ---- */
    .stButton > button[kind="primary"] {
        background-color: var(--marrom-escuro) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-size: 1rem;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: var(--marrom-medio) !important;
    }

    /* ---- Botão secundário ---- */
    .stButton > button[kind="secondary"] {
        background-color: var(--bege) !important;
        color: var(--texto-escuro) !important;
        border: 1px solid var(--areia) !important;
        border-radius: 8px;
    }
    .stButton > button[kind="secondary"]:hover {
        background-color: var(--areia) !important;
    }

    /* ---- MÉTRICAS — corrigidas para funcionar em tema claro e escuro ---- */
    [data-testid="stMetric"] {
        background-color: var(--creme);
        border-radius: 12px;
        padding: 16px 20px;
        border-left: 5px solid var(--marrom-claro);
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }
    [data-testid="stMetricLabel"] p {
        color: var(--marrom-medio) !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
    }
    [data-testid="stMetricValue"] {
        color: var(--marrom-escuro) !important;
        font-weight: 800 !important;
        font-size: 1.6rem !important;
    }

    /* ---- Containers / cards ---- */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: var(--creme) !important;
        border: 1px solid var(--areia) !important;
        border-radius: 12px !important;
    }

    /* ---- Títulos ---- */
    h1, h2, h3 {
        color: var(--marrom-escuro) !important;
    }

    /* ---- Tabs ---- */
    .stTabs [data-baseweb="tab-list"] {
        background-color: var(--bege);
        border-radius: 10px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        color: var(--marrom-medio) !important;
        border-radius: 8px;
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--marrom-escuro) !important;
        color: white !important;
    }

    /* ---- Inputs ---- */
    input, textarea, select,
    [data-testid="stNumberInputContainer"] input {
        background-color: var(--branco-quente) !important;
        border-color: var(--areia) !important;
        color: var(--texto-escuro) !important;
        border-radius: 8px !important;
    }

    /* ---- Selectbox ---- */
    [data-testid="stSelectbox"] > div > div {
        background-color: var(--branco-quente) !important;
        border-color: var(--areia) !important;
        border-radius: 8px !important;
        color: var(--texto-escuro) !important;
    }

    /* ---- Dataframe ---- */
    [data-testid="stDataFrame"] {
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid var(--areia);
    }

    /* ---- Alertas ---- */
    [data-testid="stAlert"] {
        border-radius: 10px;
    }

    /* ---- Divider ---- */
    hr {
        border-color: var(--areia) !important;
    }
</style>
""", unsafe_allow_html=True)


# =========================================================
# CAMADA DE DADOS (SQLite)
# =========================================================

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
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
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM produtos ORDER BY nome", conn)
    conn.close()
    return df


def carregar_vendas():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM vendas ORDER BY id DESC", conn)
    conn.close()
    return df


def registrar_venda(produto_nome, quantidade, preco_unitario, forma_pagamento):
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
        return True, f"✅ Venda registrada! Total: R$ {valor_total:.2f}"
    except Exception as e:
        conn.rollback()
        return False, f"Erro: {e}"
    finally:
        conn.close()


def cadastrar_produto(nome, preco, estoque):
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
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    conn.commit()
    conn.close()


def adicionar_estoque(produto_id, quantidade):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE produtos SET estoque = estoque + ? WHERE id = ?",
        (quantidade, produto_id)
    )
    conn.commit()
    conn.close()


def remover_estoque(produto_id, quantidade):
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
    return True, "Estoque atualizado com sucesso."


# =========================================================
# INICIALIZAÇÃO
# =========================================================
init_db()

# Session state
for key, default in [
    ("feedback_msg", None),
    ("feedback_type", None),
    ("confirmar_remocao_id", None),
    ("pagina", "🛒 Registro de Vendas"),
    ("forma_pagamento", "Pix"),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# =========================================================
# SIDEBAR — botões clicáveis de navegação
# =========================================================
with st.sidebar:
    st.markdown("## ☕ Cafeteria PDV")
    st.markdown("---")

    paginas = [
        ("🛒 Registro de Vendas", "🛒 Registro de Vendas"),
        ("📦 Estoque",            "📦 Estoque"),
        ("📊 Relatório Financeiro","📊 Relatório Financeiro"),
    ]

    for label, valor in paginas:
        tipo = "primary" if st.session_state.pagina == valor else "secondary"
        if st.button(label, key=f"nav_{valor}", type=tipo, use_container_width=True):
            st.session_state.pagina = valor
            st.rerun()

    st.markdown("---")
    st.caption(f"Banco: `{os.path.basename(DB_PATH)}`")

pagina = st.session_state.pagina


# =========================================================
# PÁGINA 1 — REGISTRO DE VENDAS
# =========================================================
if pagina == "🛒 Registro de Vendas":

    st.title("🛒 Registro de Vendas")

    if st.session_state.feedback_msg:
        fn = st.success if st.session_state.feedback_type == "success" else st.error
        fn(st.session_state.feedback_msg)
        st.session_state.feedback_msg = None
        st.session_state.feedback_type = None

    produtos_df = carregar_produtos()

    if produtos_df.empty:
        st.warning("⚠️ Nenhum produto cadastrado. Acesse **Estoque** para adicionar produtos.")
    else:
        with st.container(border=True):
            st.subheader("Nova Venda")

            col1, col2 = st.columns([3, 2])
            with col1:
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

            # Formas de pagamento como botões visuais
            st.markdown("**💳 Forma de Pagamento**")
            pagamentos = ["Pix", "Cartão de Débito", "Cartão de Crédito", "Dinheiro"]
            cols_pag = st.columns(4)
            for i, forma in enumerate(pagamentos):
                with cols_pag[i]:
                    tipo = "primary" if st.session_state.forma_pagamento == forma else "secondary"
                    if st.button(forma, key=f"pag_{forma}", type=tipo, use_container_width=True):
                        st.session_state.forma_pagamento = forma
                        st.rerun()

            st.markdown("---")

            valor_total = preco_unit * quantidade
            col_r1, col_r2, col_r3 = st.columns(3)
            col_r1.metric("Preço Unitário", f"R$ {preco_unit:.2f}")
            col_r2.metric("Quantidade", str(quantidade))
            col_r3.metric("💰 Total da Venda", f"R$ {valor_total:.2f}")

            st.markdown("")

            if estoque_disp == 0:
                st.error("❌ Produto sem estoque disponível.")
            else:
                if st.button(
                    f"✅  Confirmar Venda  ·  R$ {valor_total:.2f}  ({st.session_state.forma_pagamento})",
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

    # Últimas 10 vendas
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

    if st.session_state.feedback_msg:
        fn = st.success if st.session_state.feedback_type == "success" else st.error
        fn(st.session_state.feedback_msg)
        st.session_state.feedback_msg = None
        st.session_state.feedback_type = None

    tab_lista, tab_novo = st.tabs(["📋 Produtos em Estoque", "➕ Cadastrar Novo Produto"])

    with tab_lista:
        produtos_df = carregar_produtos()

        if produtos_df.empty:
            st.info("Nenhum produto cadastrado. Use a aba ao lado para adicionar.")
        else:
            baixo = produtos_df[produtos_df["estoque"] <= 5]
            if not baixo.empty:
                nomes_baixo = ", ".join(baixo["nome"].tolist())
                st.warning(f"⚠️ Estoque crítico (≤ 5 un.): **{nomes_baixo}**")

            st.markdown("---")

            for _, row in produtos_df.iterrows():
                pid = int(row["id"])
                nome = row["nome"]
                preco = float(row["preco"])
                estoque_atual = int(row["estoque"])

                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 4, 2])

                    with c1:
                        st.markdown(f"**{nome}**")
                        st.caption(f"R$ {preco:.2f} por unidade")

                    with c2:
                        cor = "🟢" if estoque_atual > 10 else ("🟡" if estoque_atual > 0 else "🔴")
                        st.markdown(f"{cor} **Estoque:** {estoque_atual} unidades")

                        col_add, col_rem = st.columns(2)
                        with col_add:
                            qtd_add = st.number_input(
                                "Qtd", min_value=1, value=1, step=1,
                                key=f"add_{pid}", label_visibility="collapsed"
                            )
                            if st.button("➕ Adicionar", key=f"btn_add_{pid}", use_container_width=True):
                                adicionar_estoque(pid, int(qtd_add))
                                st.session_state.feedback_msg = f"'{nome}': +{qtd_add} unidades adicionadas."
                                st.session_state.feedback_type = "success"
                                st.rerun()

                        with col_rem:
                            qtd_rem = st.number_input(
                                "Qtd", min_value=1, value=1, step=1,
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
                        if st.session_state.confirmar_remocao_id == pid:
                            st.warning("Confirmar exclusão?")
                            cs, cn = st.columns(2)
                            with cs:
                                if st.button("✔ Sim", key=f"sim_{pid}", use_container_width=True):
                                    remover_produto(pid)
                                    st.session_state.confirmar_remocao_id = None
                                    st.session_state.feedback_msg = f"'{nome}' removido do sistema."
                                    st.session_state.feedback_type = "success"
                                    st.rerun()
                            with cn:
                                if st.button("✖ Não", key=f"nao_{pid}", use_container_width=True):
                                    st.session_state.confirmar_remocao_id = None
                                    st.rerun()
                        else:
                            if st.button("🗑️ Excluir", key=f"del_{pid}",
                                         use_container_width=True, type="secondary"):
                                st.session_state.confirmar_remocao_id = pid
                                st.rerun()

    with tab_novo:
        st.subheader("Cadastrar Novo Produto")
        with st.form("form_novo_produto", clear_on_submit=True):
            nome_novo = st.text_input("Nome do produto", placeholder="Ex: Cappuccino")
            col_p, col_e = st.columns(2)
            with col_p:
                preco_novo = st.number_input("Preço (R$)", min_value=0.01,
                                             step=0.50, format="%.2f", value=5.00)
            with col_e:
                estoque_novo = st.number_input("Estoque inicial", min_value=0,
                                               step=1, value=0)
            if st.form_submit_button("✅ Cadastrar Produto", type="primary",
                                     use_container_width=True):
                if not nome_novo.strip():
                    st.error("Informe o nome do produto.")
                else:
                    ok, msg = cadastrar_produto(nome_novo.strip(),
                                                float(preco_novo), int(estoque_novo))
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
        st.info("Nenhuma venda registrada ainda.")
    else:
        vendas_df["data_hora"] = pd.to_datetime(vendas_df["data_hora"])
        vendas_df["data"] = vendas_df["data_hora"].dt.date

        with st.container(border=True):
            st.markdown("**🗓️ Filtrar por período**")
            col_d1, col_d2 = st.columns(2)
            data_min = vendas_df["data"].min()
            data_max = vendas_df["data"].max()
            with col_d1:
                data_inicio = st.date_input("De", value=data_min,
                                            min_value=data_min, max_value=data_max)
            with col_d2:
                data_fim = st.date_input("Até", value=data_max,
                                         min_value=data_min, max_value=data_max)

        df = vendas_df[
            (vendas_df["data"] >= data_inicio) & (vendas_df["data"] <= data_fim)
        ]

        st.markdown("---")

        # Métricas
        faturamento  = df["valor_total"].sum()
        qtd_vendas   = len(df)
        ticket_medio = faturamento / qtd_vendas if qtd_vendas > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Faturamento Total", f"R$ {faturamento:,.2f}")
        col2.metric("🧾 Número de Vendas",  str(qtd_vendas))
        col3.metric("📈 Ticket Médio",      f"R$ {ticket_medio:,.2f}")

        st.markdown("---")

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

        st.subheader("📋 Histórico Detalhado")
        historico = (
            df[["data_hora", "produto", "quantidade",
                "valor_unitario", "valor_total", "forma_pagamento"]]
            .rename(columns={
                "data_hora":        "Data/Hora",
                "produto":          "Produto",
                "quantidade":       "Qtd.",
                "valor_unitario":   "Vlr. Unit. (R$)",
                "valor_total":      "Vlr. Total (R$)",
                "forma_pagamento":  "Pagamento"
            })
            .sort_values("Data/Hora", ascending=False)
        )
        st.dataframe(historico, use_container_width=True, hide_index=True)

        st.markdown("")
        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="⬇️ Baixar relatório em CSV",
            data=csv,
            file_name=f"relatorio_{data_inicio}_a_{data_fim}.csv",
            mime="text/csv",
            use_container_width=True
        )
