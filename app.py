import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import json
from datetime import datetime
import time

# --- 1. CONFIGURAÇÃO DA PÁGINA (Deve ser a primeira coisa do Streamlit) ---
st.set_page_config(page_title="Oráculo Master Pro", page_icon="🔮", layout="wide")

# --- 2. IMPORTS DOS MÓDULOS (Motores e Design) ---
try:
    # Motores Matemáticos
    from motores.base import MotorBase
    from motores.mega_sena import MotorMegaSena
    from motores.lotofacil import MotorLotofacil
    
    # Design dos Cartões
    from interface.dashboard_cards import CSS_ESTILO, gerar_html_card

except ImportError as e:
    st.error(f"❌ Erro de Importação: {e}")
    st.info("Verifique se as pastas 'motores' e 'interface' existem no GitHub.")
    st.stop()

# --- 3. DEFINIÇÃO DAS FUNÇÕES (Primeiro ensinamos o Python, depois usamos) ---

def get_config_url():
    """Busca o link do JSON nos Secrets"""
    try:
        return st.secrets["setup"]["url_config_json"]
    except:
        st.error("⚠️ Erro: Link do JSON não encontrado no secrets.toml (seção [setup]).")
        st.stop()

@st.cache_data(ttl=600)
def load_config():
    """Baixa o JSON do GitHub"""
    url = get_config_url()
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            st.error(f"Erro GitHub: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Erro Conexão Config: {e}")
        return None

# --- 4. CARREGAMENTO DA CONFIGURAÇÃO (Agora podemos chamar a função) ---
CONFIG_GLOBAL = load_config()

# Se falhar a config, para o app aqui.
if not CONFIG_GLOBAL:
    st.stop()

# --- 5. DEFINIÇÃO DA CONEXÃO GOOGLE ---

@st.cache_resource
def connect_google():
    try:
        if "gcp_service_account" not in st.secrets:
            st.error("Secrets do Google não encontrados.")
            return None
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), scope)
        return gspread.authorize(creds).open_by_key(CONFIG_GLOBAL["spreadsheet_id"])
    except Exception as e:
        st.error(f"Erro Google Sheets: {e}")
        return None

# Funções Auxiliares (CRUD)
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
        except: 
            ws = conn.add_worksheet(title=tab, rows=1000, cols=10)
            ws.append_row(["Data", "Concurso Alvo", "Dezenas", "Estratégia", "Acertos", "Status"])
        ws.append_row(row)
        return True, "Salvo com sucesso!"
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
        
        ws.clear()
        ws.append_row(header)
        if not df.empty: ws.update('A2', df.values.tolist())
        return True, f"{orig - len(df)} deletados."
    except Exception as e: return False, str(e)

def obter_motor(nome, df, config):
    if nome == "Mega Sena": return MotorMegaSena(df, config)
    elif nome == "Lotofácil": return MotorLotofacil(df, config)
    else: return MotorBase(df, config)

# --- 6. EXECUÇÃO DO APP (Agora sim conectamos) ---

# Conecta ao Google
conn = connect_google()
if not conn: st.stop()

# Aplica o CSS do arquivo de interface
st.markdown(CSS_ESTILO, unsafe_allow_html=True)

st.title("📊 Painel de Controle Oráculo")

# --- DASHBOARD DE CARTÕES ---
cols = st.columns(len(CONFIG_GLOBAL["loterias"]))

for i, (nome, cfg) in enumerate(CONFIG_GLOBAL["loterias"].items()):
    with cols[i]:
        df_card = get_data(conn, cfg['aba_historico'])
        
        # Só desenha se tiver dados
        if df_card is not None and not df_card.empty:
            motor = obter_motor(nome, df_card, cfg)
            # Chama a função visual da pasta interface
            html_card = gerar_html_card(nome, motor)
            st.markdown(html_card, unsafe_allow_html=True)
        else:
            # Card de erro simples
            st.warning(f"{nome}: Sem dados")

st.markdown("---")

# --- ÁREA DE OPERAÇÃO ---
escolha = st.selectbox("Selecione a Loteria:", list(CONFIG_GLOBAL["loterias"].keys()))
cfg_atual = CONFIG_GLOBAL["loterias"][escolha]

df_main = get_data(conn, cfg_atual['aba_historico'])

if df_main is not None and not df_main.empty:
    MotorAtivo = obter_motor(escolha, df_main, cfg_atual)
    
    tab1, tab2 = st.tabs(["🎲 Gerador Matemático", "📂 Gestão"])
    
    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader(f"Análise: {escolha}")
            stats = MotorAtivo.get_stats()
            st.caption(f"🔥 Quentes: {stats['quentes'][:5]}")
            st.caption(f"❄️ Frios: {stats['frios'][:5]}")
            
            strat = st.radio("Estratégia:", ["Equilíbrio", "Tendência", "Mestre"])
            
            if st.button("🔮 Gerar Palpite", type="primary"):
                jogo = MotorAtivo.gerar_palpite(strat)
                st.session_state['jogo_temp'] = jogo
        
        with c2:
            st.subheader("Resultado")
            if 'jogo_temp' in st.session_state:
                nums = st.session_state['jogo_temp']
                
                # Renderiza bolas simples para o resultado (ou use HTML customizado se preferir)
                html_res = "".join([f"<span style='background:#2563eb; color:white; padding:8px; border-radius:50%; margin:3px; display:inline-block; width:35px; text-align:center; font-weight:bold'>{int(n)}</span>" for n in nums])
                st.markdown(html_res, unsafe_allow_html=True)
                st.write("")
                
                if st.button("💾 Salvar na Nuvem"):
                    try:
                        ult = pd.to_numeric(df_main['Concurso'], errors='coerce').max()
                        prox = int(ult) + 1
                    except: prox = "Prox"
                    
                    row = [datetime.now().strftime("%d/%m/%Y"), prox, str(nums), strat, "", "Pendente"]
                    with st.spinner("Gravando..."):
                        ok, msg = save_row(conn, cfg_atual['aba_palpites'], row)
                        if ok: st.success(msg)
                        else: st.error(msg)
    
    with tab2:
        st.markdown(f"**Gestão:** `{cfg_atual['aba_palpites']}`")
        df_palp = get_data(conn, cfg_atual['aba_palpites'])
        
        if df_palp is not None:
            st.dataframe(df_palp.tail(5), use_container_width=True)
            
            cd1, cd2 = st.columns([2, 1])
            with cd1:
                modo = st.selectbox("Critério:", ["Últimos N", "Por Concurso", "Limpar Tudo"])
                val = 0
                if modo == "Últimos N": val = st.number_input("Qtd:", 1, 100, 1)
                elif modo == "Por Concurso": val = st.text_input("Concurso:")
            with cd2:
                st.write("")
                st.write("")
                if st.button("🗑️ Deletar"):
                    ok, msg = delete_rows(conn, cfg_atual['aba_palpites'], modo, val)
                    if ok: st.success(msg); time.sleep(1); st.rerun()
                    else: st.error(msg)
        else:
            st.info("Nenhum palpite salvo.")

else:
    st.warning("Carregando dados...")
