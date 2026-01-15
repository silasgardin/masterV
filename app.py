import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import json
from datetime import datetime
import time

# --- 1. CONFIGURAÇÃO DA PÁGINA (TEM QUE SER A PRIMEIRA LINHA DO STREAMLIT) ---
st.set_page_config(page_title="Oráculo Master Pro", page_icon="🔮", layout="wide")

# --- 2. IMPORTAÇÃO DOS MOTORES ---
try:
    from motores.base import MotorBase
    from motores.mega_sena import MotorMegaSena
    from motores.lotofacil import MotorLotofacil
    # from motores.quina import MotorQuina (Ative quando criar o arquivo)
except ImportError as e:
    st.error(f"❌ ERRO CRÍTICO: Não foi possível importar os motores. Detalhe: {e}")
    st.stop()

# --- 3. FUNÇÕES DE CARREGAMENTO (CONFIG & GOOGLE) ---

def get_config_url():
    """Pega o link do JSON nos segredos"""
    try:
        return st.secrets["setup"]["url_config_json"]
    except:
        st.error("⚠️ Link do JSON não encontrado no secrets.toml (seção [setup]).")
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
            st.error(f"Erro ao ler GitHub (Status {response.status_code}). Verifique se o repo é Público ou o Token.")
            return None
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return None

# >>> AQUI É O PONTO CRÍTICO: Carregamos a config ANTES de usar <<<
CONFIG_GLOBAL = load_config()

if not CONFIG_GLOBAL:
    st.warning("Aguardando configuração...")
    st.stop()

@st.cache_resource
def connect_google():
    """Conecta na Planilha"""
    try:
        if "gcp_service_account" not in st.secrets:
            st.error("Credenciais do Google ausentes nos Secrets.")
            return None
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), scope)
        return gspread.authorize(creds).open_by_key(CONFIG_GLOBAL["spreadsheet_id"])
    except Exception as e:
        st.error(f"Erro ao conectar no Google Sheets: {e}")
        return None

# --- 4. FUNÇÕES DE APOIO (CRUD) ---

def obter_motor(nome_loteria, df, config):
    if nome_loteria == "Mega Sena": return MotorMegaSena(df, config)
    elif nome_loteria == "Lotofácil": return MotorLotofacil(df, config)
    else: return MotorBase(df, config)

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
        return True, "Palpite Salvo!"
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

# --- 5. INTERFACE (AGORA SIM PODEMOS DESENHAR) ---

# CSS
st.markdown("""
<style>
    .card-dash { padding:15px; border-radius:10px; border:1px solid #ddd; background:white; text-align:center; box-shadow:0 2px 5px rgba(0,0,0,0.05); }
    .sig-go { border-left:5px solid #10b981; }
    .sig-wait { border-left:5px solid #ef4444; }
    .ball { display:inline-block; width:30px; height:30px; line-height:30px; border-radius:50%; background:#2563eb; color:white; font-weight:bold; margin:2px; text-align:center; }
</style>
""", unsafe_allow_html=True)

conn = connect_google()
if not conn: st.stop()

st.title("📊 Oráculo Master | Dashboard")

# --- DASHBOARD (LOOP) ---
# Agora CONFIG_GLOBAL já existe, então não vai dar erro
cols = st.columns(len(CONFIG_GLOBAL["loterias"]))

for i, (nome, cfg) in enumerate(CONFIG_GLOBAL["loterias"].items()):
    with cols[i]:
        df_card = get_data(conn, cfg['aba_historico'])
        
        # Blindagem: Só processa se tiver dados
        if df_card is not None and not df_card.empty:
            motor = obter_motor(nome, df_card, cfg)
            txt, tipo = motor.analisar_sinal()
            style = "sig-go" if tipo == "go" else "sig-wait"
            ico = "🟢" if tipo == "go" else "🟡"
            
            st.markdown(f"""
            <div class="card-dash {style}">
                <div style="font-size:0.85rem; color:#555">{nome}</div>
                <div style="font-weight:bold; font-size:1.1rem; margin:5px 0">{txt}</div>
                <div>{ico}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning(f"{nome}: Sem dados")

st.markdown("---")

# --- ÁREA DE OPERAÇÃO ---
escolha = st.selectbox("Selecione a Loteria:", list(CONFIG_GLOBAL["loterias"].keys()))
cfg_atual = CONFIG_GLOBAL["loterias"][escolha]

df_main = get_data(conn, cfg_atual['aba_historico'])

if df_main is not None and not df_main.empty:
    Motor = obter_motor(escolha, df_main, cfg_atual)
    
    tab1, tab2 = st.tabs(["🎲 Gerador Matemático", "📂 Gestão de Palpites"])
    
    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader(f"Análise: {escolha}")
            stats = Motor.get_stats()
            st.caption(f"🔥 Quentes: {stats['quentes'][:5]}...")
            st.caption(f"❄️ Frios: {stats['frios'][:5]}...")
            
            strat = st.radio("Estratégia:", ["Equilíbrio", "Tendência", "Mestre"])
            
            if st.button("🔮 Gerar Palpite", type="primary"):
                jogo = Motor.gerar_palpite(strat)
                st.session_state['jogo_temp'] = jogo
        
        with c2:
            st.subheader("Resultado")
            if 'jogo_temp' in st.session_state:
                nums = st.session_state['jogo_temp']
                html = "".join([f"<div class='ball'>{n}</div>" for n in nums])
                st.markdown(html, unsafe_allow_html=True)
                st.write("")
                
                if st.button("💾 Salvar na Nuvem"):
                    try: 
                        ult = pd.to_numeric(df_main['Concurso'], errors='coerce').max()
                        prox = int(ult) + 1
                    except: prox = "Prox"
                    
                    row = [datetime.now().strftime("%d/%m/%Y"), prox, str(nums), strat, "", "Pendente"]
                    with st.spinner("Salvando..."):
                        ok, msg = save_row(conn, cfg_atual['aba_palpites'], row)
                        if ok: st.success(msg)
                        else: st.error(msg)

    with tab2:
        st.markdown(f"**Gestão:** `{cfg_atual['aba_palpites']}`")
        df_palp = get_data(conn, cfg_atual['aba_palpites'])
        
        if df_palp is not None:
            st.dataframe(df_palp.tail(5), use_container_width=True)
            
            c_del1, c_del2 = st.columns([2, 1])
            with c_del1:
                modo = st.selectbox("Apagar:", ["Últimos N", "Por Concurso", "Limpar Tudo"])
                val = 0
                if modo == "Últimos N": val = st.number_input("Qtd:", 1, 100, 1)
                elif modo == "Por Concurso": val = st.text_input("Concurso:")
