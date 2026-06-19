"""
Sistema de PDV - Cafeteria
Versão 6.0 — Carrinho de até 15 itens por venda.
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
# CSS
# =========================================================
st.markdown("""
<style>

.stApp { background-color: #F5ECD7; }

button[data-testid="collapsedControl"],
button[title="Close sidebar"],
[data-testid="stSidebarCollapseButton"] { display: none !important; }

section[data-testid="stSidebar"] {
    background-color: #6B4C35 !important;
    border-right: 3px solid #4e3526;
}
section[data-testid="stSidebar"] > div {
    padding-top: 1.5rem;
    padding-bottom: 1rem;
}
section[data-testid="stSidebar"] * {
    color: #F5ECD7 !important;
    font-family: 'Segoe UI', sans-serif;
}
section[data-testid="stSidebar"] .stButton > button {
    background-color: #8B6347 !important;
    color: #F5ECD7 !important;
    border: 1.5px solid #a07850 !important;
    border-radius: 10px !important;
    width: 100% !important;
    text-align: center !important;
    padding: 0.65rem 1rem !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    margin-bottom: 6px !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.15) !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background-color: #a07850 !important;
    border-color: #C4956A !important;
}
section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background-color: #4e3526 !important;
    border: 2px solid #C4956A !important;
    font-weight: 700 !important;
}

.stButton > button[kind="primary"] {
    background-color: #6B4C35 !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.65rem 1.2rem !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.15) !important;
    transition: all 0.2s ease !important;
}
.stButton > button[kind="primary"]:hover {
    background-color: #8B6347 !important;
    transform: translateY(-1px) !important;
}
.stButton > button[kind="secondary"] {
    background-color: #EDE0CC !important;
    color: #6B4C35 !important;
    border: 1.5px solid #C4956A !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}
.stButton > button[kind="secondary"]:hover {
    background-color: #D9C4A8 !important;
}

[data-testid="stMetric"] {
    background-color: #FDF6EC;
    border-radius: 12px;
    padding: 18px 20px;
    border: 1px solid #D9C4A8;
    border-left: 5px solid #C4956A;
    box-shadow: 0 2px 6px rgba(0,0,0,0.06);
}
[data-testid="stMetricLabel"] p {
    color: #8B6347 !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
[data-testid="stMetricValue"] {
    color: #4e3526 !important;
    font-weight: 800 !important;
    font-size: 1.7rem !important;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #FDF6EC !important;
    border: 1.5px solid #D9C4A8 !important;
    border-radius: 14px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07) !important;
    padding: 8px !important;
}

h1 { color: #4e3526 !important; font-weight: 800 !important; }
h2 { color: #6B4C35 !important; font-weight: 700 !important; }
h3 { color: #6B4C35 !important; font-weight: 600 !important; }

.stTabs [data-baseweb="tab-list"] {
    background-color: #EDE0CC;
    border-radius: 12px;
    padding: 5px;
    gap: 4px;
    border: 1px solid #D9C4A8;
}
.stTabs [data-baseweb="tab"] {
    color: #8B6347 !important;
    border-radius: 9px;
    font-weight: 500;
    padding: 6px 16px;
}
.stTabs [aria-selected="true"] {
    background-color: #6B4C35 !important;
    color: white !important;
    font-weight: 700 !important;
}

input, textarea,
[data-testid="stNumberInputContainer"] input {
    background-color: #FDF6EC !important;
    border-color: #C4956A !important;
    color: #4e3526 !important;
    border-radius: 9px !important;
}
[data-testid="stSelectbox"] > div > div {
    background-color: #FDF6EC !important;
    border-color: #C4956A !important;
    border-radius: 9px !important;
    color: #4e3526 !important;
}

[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #D9C4A8;
}

hr { border-color: #D9C4A8 !important; margin: 1rem 0 !important; }

/* ── Carrinho ── */
.carrinho-header {
    background: linear-gradient(135deg, #6B4C35, #8B6347);
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 10px;
    color: white !important;
    font-weight: 700;
    font-size: 1rem;
}
.item-carrinho {
    background: #FDF6EC;
    border: 1px solid #D9C4A8;
    border-radius: 10px;
    padding: 10px 14px;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.total-carrinho {
    background: linear-gradient(135deg, #4e3526, #6B4C35);
    border-radius: 12px;
    padding: 14px 18px;
    color: white !important;
    font-size: 1.1rem;
    font-weight: 700;
    margin-top: 10px;
    text-align: center;
}
.badge-itens {
    background: #C4956A;
    color: white;
    border-radius: 50%;
    padding: 2px 8px;
    font-size: 0.78rem;
    font-weight: 700;
    margin-left: 6px;
}

/* Zona de perigo */
.sidebar-logo {
    text-align: center;
    padding: 0.5rem 0 1.2rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.15);
    margin-bottom: 1.2rem;
}
.sidebar-logo .emoji   { font-size: 2.8rem; line-height: 1; }
.sidebar-logo .titulo  { font-size: 1.1rem; font-weight: 700; color: #F5ECD7 !important; margin-top: 6px; }
.sidebar-logo .sub     { font-size: 0.72rem; color: #C4956A !important; text-transform: uppercase; letter-spacing: 1.5px; }
.menu-label {
    font-size: 0.68rem; text-transform: uppercase; letter-spacing: 2px;
    color: #C4956A !important; padding: 0 0.2rem; margin-bottom: 0.4rem;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# CAMADA DE DADOS
# =========================================================

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            nome    TEXT    NOT NULL UNIQUE,
            preco   REAL    NOT NULL,
            estoque INTEGER NOT NULL DEFAULT 0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS vendas (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora       TEXT    NOT NULL,
            produto         TEXT    NOT NULL,
            quantidade      INTEGER NOT NULL,
            valor_unitario  REAL    NOT NULL,
            valor_total     REAL    NOT NULL,
            forma_pagamento TEXT    NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def carregar_produtos():
    conn = get_connection()
    df   = pd.read_sql_query("SELECT * FROM produtos ORDER BY nome", conn)
    conn.close()
    return df


def carregar_vendas():
    conn = get_connection()
    df   = pd.read_sql_query("SELECT * FROM vendas ORDER BY id DESC", conn)
    conn.close()
    return df


def registrar_venda_multipla(itens, forma_pagamento):
    """
    Registra uma lista de itens do carrinho em uma única transação.
    itens = [{"nome": str, "quantidade": int, "preco": float}, ...]
    Verifica estoque de TODOS antes de confirmar qualquer baixa.
    """
    conn = get_connection()
    cur  = conn.cursor()
    try:
        # 1ª passagem: valida estoque de todos os itens
        for item in itens:
            cur.execute("SELECT estoque FROM produtos WHERE nome = ?", (item["nome"],))
            row = cur.fetchone()
            if not row:
                return False, f"Produto '{item['nome']}' não encontrado."
            if row[0] < item["quantidade"]:
                return False, (
                    f"Estoque insuficiente para '{item['nome']}'. "
                    f"Disponível: {row[0]}, solicitado: {item['quantidade']}."
                )

        # 2ª passagem: grava vendas e dá baixa
        data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for item in itens:
            valor_total = round(item["quantidade"] * item["preco"], 2)
            cur.execute("""
                INSERT INTO vendas
                  (data_hora, produto, quantidade, valor_unitario, valor_total, forma_pagamento)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (data_hora, item["nome"], item["quantidade"],
                  item["preco"], valor_total, forma_pagamento))
            cur.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE nome = ?",
                (item["quantidade"], item["nome"])
            )

        conn.commit()
        total_geral = sum(i["quantidade"] * i["preco"] for i in itens)
        return True, f"Venda registrada com sucesso!  Total: R$ {total_geral:.2f}"

    except Exception as e:
        conn.rollback()
        return False, f"Erro ao registrar venda: {e}"
    finally:
        conn.close()


def cadastrar_produto(nome, preco, estoque):
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute("INSERT INTO produtos (nome, preco, estoque) VALUES (?, ?, ?)",
                    (nome, preco, estoque))
        conn.commit()
        return True, f"Produto '{nome}' cadastrado com sucesso!"
    except sqlite3.IntegrityError:
        return False, f"Já existe um produto chamado '{nome}'."
    finally:
        conn.close()


def remover_produto(produto_id):
    conn = get_connection()
    conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    conn.commit()
    conn.close()


def adicionar_estoque(produto_id, qtd):
    conn = get_connection()
    conn.execute("UPDATE produtos SET estoque = estoque + ? WHERE id = ?", (qtd, produto_id))
    conn.commit()
    conn.close()


def remover_estoque(produto_id, qtd):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT estoque FROM produtos WHERE id = ?", (produto_id,))
    atual = cur.fetchone()[0]
    if qtd > atual:
        conn.close()
        return False, f"Não é possível remover {qtd} — estoque atual: {atual}."
    conn.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", (qtd, produto_id))
    conn.commit()
    conn.close()
    return True, "Estoque atualizado com sucesso."


def resetar_vendas():
    conn = get_connection()
    conn.execute("DELETE FROM vendas")
    conn.execute("DELETE FROM sqlite_sequence WHERE name='vendas'")
    conn.commit()
    conn.close()


# =========================================================
# INICIALIZAÇÃO
# =========================================================
init_db()

LIMITE_CARRINHO = 15

for chave, padrao in [
    ("feedback_msg",         None),
    ("feedback_type",        None),
    ("confirmar_remocao_id", None),
    ("pagina",               "🛒 Registro de Vendas"),
    ("forma_pagamento",      "Pix"),
    ("reset_etapa",          0),
    # Carrinho: lista de dicts {nome, quantidade, preco}
    ("carrinho",             []),
]:
    if chave not in st.session_state:
        st.session_state[chave] = padrao


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown("""
        <div class="sidebar-logo">
            <div class="emoji">☕</div>
            <div class="titulo">Cafeteria PDV</div>
            <div class="sub">Sistema de Caixa</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="menu-label">Navegação</div>', unsafe_allow_html=True)

    for item in ["🛒 Registro de Vendas", "📦 Estoque", "📊 Relatório Financeiro"]:
        ativo = st.session_state.pagina == item
        if st.button(item, key=f"nav_{item}",
                     type="primary" if ativo else "secondary",
                     use_container_width=True):
            st.session_state.pagina = item
            st.rerun()

pagina = st.session_state.pagina


# =========================================================
# HELPER
# =========================================================
def mostrar_feedback():
    if st.session_state.feedback_msg:
        fn = st.success if st.session_state.feedback_type == "success" else st.error
        fn(st.session_state.feedback_msg)
        st.session_state.feedback_msg  = None
        st.session_state.feedback_type = None


# =========================================================
# PÁGINA 1 — REGISTRO DE VENDAS (com carrinho)
# =========================================================
if pagina == "🛒 Registro de Vendas":

    st.title("🛒 Registro de Vendas")
    mostrar_feedback()

    produtos_df = carregar_produtos()

    if produtos_df.empty:
        st.warning("⚠️ Nenhum produto cadastrado. Acesse **Estoque** para adicionar produtos.")
    else:
        # ── Layout: coluna esquerda (adicionar) | coluna direita (carrinho) ──
        col_esq, col_dir = st.columns([1, 1], gap="large")

        # ===================================================
        # COLUNA ESQUERDA — Seleção de produto
        # ===================================================
        with col_esq:
            with st.container(border=True):
                qtd_carrinho = len(st.session_state.carrinho)
                st.subheader(f"Adicionar Item")

                # Selectbox de produto
                opcoes = {
                    f"{r['nome']}  ·  R$ {r['preco']:.2f}": r
                    for _, r in produtos_df.iterrows()
                }
                escolha      = st.selectbox("🏷️ Produto", list(opcoes.keys()))
                produto      = opcoes[escolha]
                estoque_disp = int(produto["estoque"])
                preco_unit   = float(produto["preco"])

                # Quantidade já no carrinho para este produto
                qtd_ja_no_carrinho = sum(
                    i["quantidade"] for i in st.session_state.carrinho
                    if i["nome"] == produto["nome"]
                )
                estoque_restante = estoque_disp - qtd_ja_no_carrinho

                # Info de estoque disponível
                if estoque_disp == 0:
                    st.error("❌ Produto sem estoque.")
                elif estoque_restante <= 0:
                    st.warning("⚠️ Todo o estoque disponível já está no carrinho.")
                else:
                    if qtd_ja_no_carrinho > 0:
                        st.caption(f"ℹ️ Já no carrinho: {qtd_ja_no_carrinho} un.  |  Disponível para adicionar: {estoque_restante} un.")

                qtd_adicionar = st.number_input(
                    "📦 Quantidade",
                    min_value=1,
                    max_value=max(estoque_restante, 1),
                    value=1,
                    step=1,
                    disabled=(estoque_restante <= 0 or estoque_disp == 0)
                )

                # Subtotal do item a ser adicionado
                subtotal_item = preco_unit * qtd_adicionar
                st.metric("Subtotal do Item", f"R$ {subtotal_item:.2f}")

                # Botão de adicionar ao carrinho
                carrinho_cheio  = qtd_carrinho >= LIMITE_CARRINHO
                pode_adicionar  = estoque_disp > 0 and estoque_restante > 0 and not carrinho_cheio

                if carrinho_cheio:
                    st.warning(f"🛒 Limite de {LIMITE_CARRINHO} itens atingido. Confirme ou limpe o carrinho.")

                if st.button(
                    "➕ Adicionar ao Carrinho",
                    type="primary",
                    use_container_width=True,
                    disabled=not pode_adicionar
                ):
                    # Se o produto já existe no carrinho, soma a quantidade
                    encontrado = False
                    for item in st.session_state.carrinho:
                        if item["nome"] == produto["nome"]:
                            item["quantidade"] += int(qtd_adicionar)
                            encontrado = True
                            break
                    if not encontrado:
                        st.session_state.carrinho.append({
                            "nome":       produto["nome"],
                            "quantidade": int(qtd_adicionar),
                            "preco":      preco_unit,
                        })
                    st.rerun()

                st.markdown("---")

                # Forma de pagamento (fica na coluna esquerda, abaixo do seletor)
                st.markdown("**💳 Forma de Pagamento**")
                pagamentos = ["Pix", "Cartão de Débito", "Cartão de Crédito", "Dinheiro"]
                col_p1, col_p2 = st.columns(2)
                for i, forma in enumerate(pagamentos):
                    col = col_p1 if i % 2 == 0 else col_p2
                    with col:
                        ativo = st.session_state.forma_pagamento == forma
                        if st.button(forma, key=f"pag_{forma}",
                                     type="primary" if ativo else "secondary",
                                     use_container_width=True):
                            st.session_state.forma_pagamento = forma
                            st.rerun()

        # ===================================================
        # COLUNA DIREITA — Carrinho
        # ===================================================
        with col_dir:
            with st.container(border=True):

                # Cabeçalho do carrinho com contador de itens
                qtd_carrinho = len(st.session_state.carrinho)
                st.markdown(
                    f'<div class="carrinho-header">'
                    f'🛒 Carrinho &nbsp;<span class="badge-itens">'
                    f'{qtd_carrinho} / {LIMITE_CARRINHO}</span></div>',
                    unsafe_allow_html=True
                )

                if not st.session_state.carrinho:
                    st.info("Nenhum item adicionado ainda.\nSelecione um produto ao lado.")
                else:
                    # Lista de itens com botão de remover
                    for idx, item in enumerate(st.session_state.carrinho):
                        subtotal = item["quantidade"] * item["preco"]
                        c_nome, c_info, c_del = st.columns([3, 3, 1])

                        with c_nome:
                            st.markdown(f"**{item['nome']}**")
                            st.caption(f"R$ {item['preco']:.2f} / un.")

                        with c_info:
                            st.markdown(f"Qtd: **{item['quantidade']}**")
                            st.caption(f"Subtotal: R$ {subtotal:.2f}")

                        with c_del:
                            # Botão vermelho de remover item do carrinho
                            if st.button("✖", key=f"del_carrinho_{idx}",
                                         help="Remover item"):
                                st.session_state.carrinho.pop(idx)
                                st.rerun()

                        st.divider()

                    # Total geral
                    total_geral = sum(
                        i["quantidade"] * i["preco"]
                        for i in st.session_state.carrinho
                    )
                    st.markdown(
                        f'<div class="total-carrinho">'
                        f'💰 Total da Venda: R$ {total_geral:.2f}'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                    st.markdown("")

                    # Resumo: forma de pagamento selecionada
                    st.caption(
                        f"💳 Pagamento: **{st.session_state.forma_pagamento}**  |  "
                        f"🧾 {qtd_carrinho} tipo(s) de item"
                    )

                    st.markdown("")

                    # Botão confirmar venda
                    if st.button(
                        f"✅  Confirmar Venda  ·  R$ {total_geral:.2f}"
                        f"  via {st.session_state.forma_pagamento}",
                        type="primary",
                        use_container_width=True
                    ):
                        ok, msg = registrar_venda_multipla(
                            st.session_state.carrinho,
                            st.session_state.forma_pagamento
                        )
                        if ok:
                            # Limpa o carrinho após venda confirmada
                            st.session_state.carrinho = []
                        st.session_state.feedback_msg  = msg
                        st.session_state.feedback_type = "success" if ok else "error"
                        st.rerun()

                    # Botão limpar carrinho
                    if st.button("🗑️ Limpar Carrinho",
                                 use_container_width=True, type="secondary"):
                        st.session_state.carrinho = []
                        st.rerun()

        # ── Últimas 10 vendas ─────────────────────────────
        st.markdown("")
        with st.container(border=True):
            st.subheader("🕐 Últimas 10 Vendas")
            vendas_df = carregar_vendas()
            if vendas_df.empty:
                st.info("Nenhuma venda registrada ainda.")
            else:
                st.dataframe(
                    vendas_df.head(10)
                    [["data_hora","produto","quantidade","valor_total","forma_pagamento"]]
                    .rename(columns={
                        "data_hora":       "Data / Hora",
                        "produto":         "Produto",
                        "quantidade":      "Qtd.",
                        "valor_total":     "Total (R$)",
                        "forma_pagamento": "Pagamento",
                    }),
                    use_container_width=True, hide_index=True
                )


# =========================================================
# PÁGINA 2 — ESTOQUE
# =========================================================
elif pagina == "📦 Estoque":

    st.title("📦 Gestão de Estoque")
    mostrar_feedback()

    tab_lista, tab_novo = st.tabs(["📋 Produtos em Estoque", "➕ Cadastrar Novo Produto"])

    with tab_lista:
        produtos_df = carregar_produtos()
        if produtos_df.empty:
            st.info("Nenhum produto cadastrado. Use a aba ao lado para adicionar.")
        else:
            baixo = produtos_df[produtos_df["estoque"] <= 5]
            if not baixo.empty:
                st.warning("⚠️ Estoque crítico (≤ 5 un.): **" +
                           ", ".join(baixo["nome"].tolist()) + "**")
            st.markdown("")

            for _, row in produtos_df.iterrows():
                pid           = int(row["id"])
                nome          = row["nome"]
                preco         = float(row["preco"])
                estoque_atual = int(row["estoque"])

                with st.container(border=True):
                    col_info, col_acoes, col_del = st.columns([3, 5, 2])

                    with col_info:
                        st.markdown(f"**{nome}**")
                        st.caption(f"R$ {preco:.2f} / unidade")
                        if estoque_atual > 10:
                            st.markdown(f"🟢 **{estoque_atual} un.**")
                        elif estoque_atual > 0:
                            st.markdown(f"🟡 **{estoque_atual} un.**")
                        else:
                            st.markdown("🔴 **Sem estoque**")

                    with col_acoes:
                        st.markdown("**Ajustar estoque**")
                        ca, cb = st.columns(2)
                        with ca:
                            qtd_add = st.number_input(
                                "Adicionar", min_value=1, value=1, step=1,
                                key=f"add_{pid}", label_visibility="collapsed"
                            )
                            if st.button("➕ Adicionar", key=f"btn_add_{pid}",
                                         use_container_width=True, type="primary"):
                                adicionar_estoque(pid, int(qtd_add))
                                st.session_state.feedback_msg  = f"'{nome}': +{qtd_add} unidades."
                                st.session_state.feedback_type = "success"
                                st.rerun()
                        with cb:
                            qtd_rem = st.number_input(
                                "Remover", min_value=1, value=1, step=1,
                                key=f"rem_{pid}", label_visibility="collapsed"
                            )
                            if st.button("➖ Remover", key=f"btn_rem_{pid}",
                                         use_container_width=True, type="secondary"):
                                ok, msg = remover_estoque(pid, int(qtd_rem))
                                st.session_state.feedback_msg  = msg
                                st.session_state.feedback_type = "success" if ok else "error"
                                st.rerun()

                    with col_del:
                        st.markdown("**Remover produto**")
                        if st.session_state.confirmar_remocao_id == pid:
                            st.warning("Confirmar?")
                            cs, cn = st.columns(2)
                            with cs:
                                if st.button("✔", key=f"sim_{pid}",
                                             use_container_width=True, type="primary"):
                                    remover_produto(pid)
                                    st.session_state.confirmar_remocao_id = None
                                    st.session_state.feedback_msg  = f"'{nome}' removido."
                                    st.session_state.feedback_type = "success"
                                    st.rerun()
                            with cn:
                                if st.button("✖", key=f"nao_{pid}",
                                             use_container_width=True, type="secondary"):
                                    st.session_state.confirmar_remocao_id = None
                                    st.rerun()
                        else:
                            if st.button("🗑️ Excluir", key=f"del_{pid}",
                                         use_container_width=True, type="secondary"):
                                st.session_state.confirmar_remocao_id = pid
                                st.rerun()

    with tab_novo:
        with st.container(border=True):
            st.subheader("Novo Produto")
            with st.form("form_novo_produto", clear_on_submit=True):
                nome_novo = st.text_input("Nome do produto", placeholder="Ex: Cappuccino")
                cp, ce    = st.columns(2)
                with cp:
                    preco_novo = st.number_input("Preço (R$)", min_value=0.01,
                                                 step=0.50, format="%.2f", value=5.00)
                with ce:
                    estoque_novo = st.number_input("Estoque inicial",
                                                   min_value=0, step=1, value=0)
                if st.form_submit_button("✅ Cadastrar Produto", type="primary",
                                         use_container_width=True):
                    if not nome_novo.strip():
                        st.error("Informe o nome do produto.")
                    else:
                        ok, msg = cadastrar_produto(
                            nome_novo.strip(), float(preco_novo), int(estoque_novo)
                        )
                        st.session_state.feedback_msg  = msg
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
        vendas_df["data"]      = vendas_df["data_hora"].dt.date

        with st.container(border=True):
            st.markdown("**🗓️ Filtrar por período**")
            data_min = vendas_df["data"].min()
            data_max = vendas_df["data"].max()
            cd1, cd2 = st.columns(2)
            with cd1:
                data_inicio = st.date_input("De",  value=data_min,
                                            min_value=data_min, max_value=data_max)
            with cd2:
                data_fim = st.date_input("Até", value=data_max,
                                         min_value=data_min, max_value=data_max)

        df = vendas_df[
            (vendas_df["data"] >= data_inicio) &
            (vendas_df["data"] <= data_fim)
        ]

        st.markdown("---")

        faturamento  = df["valor_total"].sum()
        qtd_vendas   = len(df)
        ticket_medio = faturamento / qtd_vendas if qtd_vendas > 0 else 0

        c1, c2, c3 = st.columns(3)
        c1.metric("💰 Faturamento Total", f"R$ {faturamento:,.2f}")
        c2.metric("🧾 Número de Vendas",  str(qtd_vendas))
        c3.metric("📈 Ticket Médio",      f"R$ {ticket_medio:,.2f}")

        st.markdown("---")

        with st.container(border=True):
            st.subheader("💳 Recebimentos por Forma de Pagamento")
            resumo_pag = (
                df.groupby("forma_pagamento")["valor_total"]
                .agg(["sum","count"]).reset_index()
                .rename(columns={
                    "forma_pagamento":"Forma de Pagamento",
                    "sum":"Total Recebido (R$)", "count":"Nº de Vendas"
                })
                .sort_values("Total Recebido (R$)", ascending=False)
            )
            st.dataframe(resumo_pag, use_container_width=True, hide_index=True)

        st.markdown("")

        with st.container(border=True):
            st.subheader("🏆 Produtos Mais Vendidos")
            resumo_prod = (
                df.groupby("produto")
                .agg(Quantidade=("quantidade","sum"), Faturamento=("valor_total","sum"))
                .reset_index().rename(columns={"produto":"Produto"})
                .sort_values("Quantidade", ascending=False)
            )
            st.dataframe(resumo_prod, use_container_width=True, hide_index=True)

        st.markdown("")

        with st.container(border=True):
            st.subheader("📋 Histórico Detalhado")
            historico = (
                df[["data_hora","produto","quantidade",
                    "valor_unitario","valor_total","forma_pagamento"]]
                .rename(columns={
                    "data_hora":"Data / Hora","produto":"Produto",
                    "quantidade":"Qtd.","valor_unitario":"Vlr. Unit. (R$)",
                    "valor_total":"Vlr. Total (R$)","forma_pagamento":"Pagamento"
                })
                .sort_values("Data / Hora", ascending=False)
            )
            st.dataframe(historico, use_container_width=True, hide_index=True)

        st.markdown("")
        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="⬇️ Baixar relatório em CSV", data=csv,
            file_name=f"relatorio_{data_inicio}_a_{data_fim}.csv",
            mime="text/csv", use_container_width=True
        )

    # ── Zona de perigo ────────────────────────────────────
    st.markdown("---")
    st.markdown("---")

    with st.container(border=True):
        st.markdown("""
            <div style="background:linear-gradient(135deg,#8B3A2A,#6B2A1A);
                        border-radius:10px;padding:14px 18px;margin-bottom:12px;">
                <span style="color:white;font-size:1.05rem;font-weight:700;">
                    ⚠️ Zona de Perigo — Resetar Histórico de Vendas
                </span><br>
                <span style="color:#ffccc0;font-size:0.82rem;">
                    Apaga permanentemente todas as vendas.
                    Estoque e produtos <strong style="color:white">não</strong> serão afetados.
                </span>
            </div>
        """, unsafe_allow_html=True)

        etapa = st.session_state.reset_etapa

        if etapa == 0:
            if st.button("🗑️ Resetar Histórico de Vendas",
                         use_container_width=True, type="secondary"):
                st.session_state.reset_etapa = 1
                st.rerun()

        elif etapa == 1:
            st.warning("**1ª Confirmação** — Tem certeza? Esta ação não pode ser desfeita.")
            cs1, cn1 = st.columns(2)
            with cs1:
                if st.button("✔ Sim, quero resetar", key="r1",
                             use_container_width=True, type="primary"):
                    st.session_state.reset_etapa = 2
                    st.rerun()
            with cn1:
                if st.button("✖ Cancelar", key="r1n",
                             use_container_width=True, type="secondary"):
                    st.session_state.reset_etapa = 0
                    st.rerun()

        elif etapa == 2:
            st.error("**2ª Confirmação — Última chance!** Confirma o reset definitivo?")
            cs2, cn2 = st.columns(2)
            with cs2:
                if st.button("⚠️ Confirmar Reset", key="r2",
                             use_container_width=True, type="primary"):
                    resetar_vendas()
                    st.session_state.reset_etapa   = 0
                    st.session_state.feedback_msg  = "✅ Histórico resetado. Estoque e produtos mantidos."
                    st.session_state.feedback_type = "success"
                    st.rerun()
            with cn2:
                if st.button("✖ Cancelar", key="r2n",
                             use_container_width=True, type="secondary"):
                    st.session_state.reset_etapa = 0
                    st.rerun()

    mostrar_feedback()
