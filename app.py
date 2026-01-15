import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import json
from datetime import datetime
import time

# --- 1. CONFIGURAÇÃO DA PÁGINA (Deve ser a primeira linha) ---
st.set_page_config(page_title="Oráculo Master Pro", page_icon="🔮", layout="wide")

# --- 2. IMPORTS DOS MÓDULOS ---
try:
    # Motores Matemáticos (Back-end)
    from motores.base import MotorBase
    from motores.mega_sena import MotorMegaSena
    from motores.lotofacil import MotorLotofacil
    
    # Importação Segura dos Novos Motores (Evita crash se arquivo não existir)
    try: from motores.quina import MotorQuina
    except ImportError: MotorQuina = None
    try: from motores.dia_de_sorte import MotorDiaDeSorte
    except ImportError: MotorDiaDeSorte = None
    try: from motores.dupla_sena import MotorDuplaSena
    except ImportError: MotorDuplaSena = None
    
    # Interface Visual (Front-end)
    from interface.dashboard_cards import CSS_ESTILO, gerar_html_card, gerar_ticket_visual

except ImportError as e:
    st.error(f"❌ Erro Crítico de Importação: {e}")
    st.stop()

# --- 3. INFRAESTRUTURA ---

def get_config_url():
    try: return st.secrets["setup"]["url_config_json"]
    except: st.error("⚠️ Configuração 'url_config_json' não encontrada nos secrets."); st.stop()

@st.cache_data(ttl=600)
def load_config():
    try:
        response = requests.get(get_config_url())
        if response.status_code == 200: return json.loads(response.text)
        return None
    except: return None

CONFIG_GLOBAL = load_config()
if not CONFIG_GLOBAL: st.stop()

@st.cache_resource
def connect_google():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), scope)
        return gspread.authorize(creds).open_by_key(CONFIG_GLOBAL["spreadsheet_id"])
    except Exception as e:
        st.error(f"Erro Google Sheets: {e}")
        return None

# --- NOVO: BUSCADOR DE API PÚBLICA ---
@st.cache_data(ttl=3600)
def buscar_premio_api(nome_loteria):
    """Busca o valor atualizado na API Pública (se configurada)"""
    try:
        if "api" not in st.secrets: return None
        url_base = st.secrets["api"]["url_base"]
        
        slugs = {
            "Mega Sena": "megasena", "Lotofácil": "lotofacil", "Quina": "quina",
            "Lotomania": "lotomania", "Timemania": "timemania", 
            "Dupla Sena": "duplasena", "Dia de Sorte": "diadesorte"
        }
        slug = slugs.get(nome_loteria)
        if not slug: return None
        
        resp = requests.get(f"{url_base}/{slug}", timeout=4)
        if resp.status_code == 200:
            d = resp.json()
            # Tenta pegar estimativa ou acumulado
            val = d.get("valorEstimadoProximoConcurso", 0)
            if val == 0: val = d.get("valorAcumuladoProximoConcurso", 0)
            return val
    except: pass
    return None

# --- 4. FACTORY & CRUD ---

def obter_motor(nome, df, cfg):
    n = nome.lower()
    if "mega" in n: return MotorMegaSena(df, cfg)
    elif "facil" in n or "fácil" in n: return MotorLotofacil(df, cfg)
    elif "quina" in n and MotorQuina: return MotorQuina(df, cfg)
    elif "dia" in n and "sorte" in n and MotorDiaDeSorte: return MotorDiaDeSorte(df, cfg)
    elif "dupla" in n and MotorDuplaSena: return MotorDuplaSena(df, cfg)
    else: return MotorBase(df, cfg)

def get_data(conn, tab):
    try:
        ws = conn.worksheet(tab)
        data = ws.get_all_values()
        if len(data) < 2: return None
        return pd.DataFrame(data[1:], columns=data[0])
    except: return None

def save_row(conn, tab, row):
    try:
        try: ws = conn.worksheet(tab)
        except: ws = conn.add_worksheet(title=tab, rows=1000, cols=10); ws.append_row(["Data", "Concurso Alvo", "Dezenas", "Estratégia", "Acertos", "Status"])
        ws.append_row(row)
        return True, "✅ Sucesso!"
    except Exception as e: return False, str(e)

def delete_rows(conn, tab, mode, val):
    try:
        ws = conn.worksheet(tab)
        data = ws.get_all_values()
        if len(data) < 2: return False, "Vazio"
        header, rows = data[0], data[1:]
        df = pd.DataFrame(rows, columns=header)
        orig = len(df)
        if mode == "Limpar Tudo": df = df.iloc[0:0]
        elif mode == "Últimos N": df = df.iloc[:-int(val)]
        elif mode == "Por Concurso": df = df[df['Concurso Alvo'] != str(val)]
        ws.clear(); ws.append_row(header)
        if not df.empty: ws.update('A2', df.values.tolist())
        return True, f"{orig - len(df)} apagados."
    except Exception as e: return False, str(e)

# --- 5. INTERFACE PRINCIPAL ---

conn = connect_google()
if not conn: st.stop()

st.markdown(CSS_ESTILO, unsafe_allow_html=True)

# SIDEBAR STATUS
with st.sidebar:
    st.header("🔌 Conectividade")
    st.markdown(f"<div style='padding:10px; border-radius:8px; background:#dcfce7; border:1px solid #86efac; color:#166534; margin-bottom:10px'><b>🐙 GitHub:</b> ONLINE ✅</div>", unsafe_allow_html=True)
    status_go = "CONECTADO ✅" if conn else "ERRO ❌"
    color_go = "#dbeafe" if conn else "#fee2e2"
    st.markdown(f"<div style='padding:10px; border-radius:8px; background:{color_go}; border:1px solid #93c5fd; color:#1e40af;'><b>📊 Google Sheets:</b> {status_go}</div>", unsafe_allow_html=True)
    st.markdown("---")
    st.caption(f"Atualizado: {datetime.now().strftime('%H:%M')}")

# DASHBOARD
st.title("📊 Painel de Controle Oráculo")

COLS_PER_ROW = 3
items = list(CONFIG_GLOBAL["loterias"].items())

for i in range(0, len(items), COLS_PER_ROW):
    cols = st.columns(COLS_PER_ROW)
    for j in range(COLS_PER_ROW):
        if i + j < len(items):
            nome_lot, cfg = items[i + j]
            with cols[j]:
                # 1. Busca Planilha
                df_card = get_data(conn, cfg['aba_historico'])
                # 2. Busca API (Opcional)
                valor_api = buscar_premio_api(nome_lot)
                
                if df_card is not None and not df_card.empty:
                    motor_temp = obter_motor(nome_lot, df_card, cfg)
                    # Gera Card com valor da API se existir
                    html = gerar_html_card(nome_lot, motor_temp, valor_api)
                    st.markdown(html, unsafe_allow_html=True)
                else:
                    st.warning(f"{nome_lot}: Sincronizando...")

st.markdown("---")

# ÁREA DE OPERAÇÃO
st.subheader("🛠️ Central de Operações")
escolha = st.selectbox("Selecione a Loteria:", list(CONFIG_GLOBAL["loterias"].keys()))
cfg_atual = CONFIG_GLOBAL["loterias"][escolha]
df_main = get_data(conn, cfg_atual['aba_historico'])

if df_main is not None and not df_main.empty:
    MotorAtivo = obter_motor(escolha, df_main, cfg_atual)
    tab1, tab2 = st.tabs(["🎲 Gerador", "📂 Gestão"])
    
    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Análise: {escolha}**")
            stats = MotorAtivo.get_stats()
            if stats['quentes']: st.caption(f"🔥 Quentes: {', '.join(map(str, stats['quentes'][:6]))}")
            strat = st.radio("Estratégia:", ["Equilíbrio", "Tendência", "Mestre"])
            if st.button("🔮 Gerar Palpite", type="primary"):
                st.session_state['jogo'] = MotorAtivo.gerar_palpite(strat)
        with c2:
            st.markdown("**Palpite Gerado:**")
            if 'jogo' in st.session_state:
                nums = st.session_state['jogo']
                st.markdown(gerar_ticket_visual(escolha, nums), unsafe_allow_html=True)
                st.write("")
                if st.button("💾 Salvar na Nuvem", use_container_width=True):
                    try: targ = int(df_main['Concurso'].max()) + 1
                    except: targ = "Prox"
                    row = [datetime.now().strftime("%d/%m/%Y"), targ, str(nums), strat, "", "Pendente"]
                    with st.spinner("Salvando..."):
                        ok, msg = save_row(conn, cfg_atual['aba_palpites'], row)
                        if ok: st.success(msg)
                        else: st.error(msg)

    with tab2:
        df_p = get_data(conn, cfg_atual['aba_palpites'])
        if df_p is not None:
            st.dataframe(df_p.tail(10), use_container_width=True)
            cd1, cd2 = st.columns([2,1])
            with cd1:
                modo = st.selectbox("Critério:", ["Últimos N", "Por Concurso", "Limpar Tudo"])
                val = st.number_input("Qtd:", 1, 100, 1) if modo == "Últimos N" else st.text_input("Concurso:") if modo == "Por Concurso" else 0
            with cd2:
                st.write(""); st.write("")
                if st.button("🗑️ Excluir"):
                    ok, msg = delete_rows(conn, cfg_atual['aba_palpites'], modo, val)
                    if ok: st.success(msg); time.sleep(1); st.rerun()
                    else: st.error(msg)
        else: st.info("Sem histórico.")
else:
    st.info(f"Carregando {escolha}...")
