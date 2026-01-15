import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import json
from datetime import datetime
import time

# --- 1. CONFIGURAÇÃO DA PÁGINA (Obrigatório ser a primeira linha) ---
st.set_page_config(page_title="Oráculo Master Pro", page_icon="🔮", layout="wide")

# --- 2. IMPORTS DOS MÓDULOS CUSTOMIZADOS ---
try:
    # Importa a Lógica Matemática (Back-end)
    from motores.base import MotorBase
    from motores.mega_sena import MotorMegaSena
    from motores.lotofacil import MotorLotofacil
    
    # Importa o Design Visual (Front-end)
    from interface.dashboard_cards import CSS_ESTILO, gerar_html_card

except ImportError as e:
    st.error(f"❌ Erro Crítico de Importação: {e}")
    st.info("Verifique se as pastas 'motores' e 'interface' existem no seu GitHub e contêm os arquivos '__init__.py'.")
    st.stop()

# --- 3. FUNÇÕES DE INFRAESTRUTURA ---

def get_config_url():
    """Busca o link do JSON dentro do secrets.toml"""
    try:
        return st.secrets["setup"]["url_config_json"]
    except Exception:
        st.error("⚠️ Configuração 'url_config_json' não encontrada na seção [setup] do secrets.toml.")
        st.stop()

@st.cache_data(ttl=600)
def load_config():
    """Baixa o arquivo de configuração do GitHub"""
    url = get_config_url()
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            st.error(f"Erro ao ler GitHub (Status {response.status_code}). Verifique se o repo é Público.")
            return None
    except Exception as e:
        st.error(f"Erro de conexão com GitHub: {e}")
        return None

# --- CARREGAMENTO DA CONFIGURAÇÃO ---
CONFIG_GLOBAL = load_config()
if not CONFIG_GLOBAL: st.stop()

@st.cache_resource
def connect_google():
    """Conecta à API do Google Sheets"""
    try:
        if "gcp_service_account" not in st.secrets:
            st.error("Credenciais do Google (gcp_service_account) ausentes nos Secrets.")
            return None
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), scope)
        return gspread.authorize(creds).open_by_key(CONFIG_GLOBAL["spreadsheet_id"])
    except Exception as e:
        st.error(f"Erro ao conectar no Google Sheets: {e}")
        return None

# --- 4. FUNÇÕES OPERACIONAIS (CRUD & LÓGICA) ---

def obter_motor(nome_loteria, df, config):
    """Fábrica de Motores: Retorna o especialista correto"""
    if nome_loteria == "Mega Sena": return MotorMegaSena(df, config)
    elif nome_loteria == "Lotofácil": return MotorLotofacil(df, config)
    else: return MotorBase(df, config)

def get_data(conn, tab):
    """Lê os dados de uma aba com segurança"""
    try:
        ws = conn.worksheet(tab)
        data = ws.get_all_values()
        if len(data) < 2: return None
        return pd.DataFrame(data[1:], columns=data[0])
    except: return None

def save_row(conn, tab, row):
    """Salva uma nova linha na aba especificada"""
    try:
        try: ws = conn.worksheet(tab)
        except: 
            ws = conn.add_worksheet(title=tab, rows=1000, cols=10)
            ws.append_row(["Data", "Concurso Alvo", "Dezenas", "Estratégia", "Acertos", "Status"])
        ws.append_row(row)
        return True, "Palpite registrado com sucesso!"
    except Exception as e: return False, str(e)

def delete_rows(conn, tab, mode, val):
    """Sistema avançado de exclusão de registros"""
    try:
        ws = conn.worksheet(tab)
        data = ws.get_all_values()
        if len(data) < 2: return False, "Planilha vazia"
        
        header = data[0]
        rows = data[1:]
        df = pd.DataFrame(rows, columns=header)
        original_count = len(df)
        
        if mode == "Limpar Tudo":
            df = df.iloc[0:0]
        elif mode == "Últimos N":
            try:
                n = int(val)
                if n > 0: df = df.iloc[:-n]
            except: pass
        elif mode == "Por Concurso":
            df = df[df['Concurso Alvo'] != str(val)]
            
        # Reescreve a aba (Limpa e Cola)
        ws.clear()
        ws.append_row(header)
        if not df.empty:
            ws.update('A2', df.values.tolist())
            
        return True, f"{original_count - len(df)} registros deletados."
    except Exception as e: return False, str(e)

# --- 5. INICIALIZAÇÃO DA INTERFACE ---

conn = connect_google()
if not conn: st.stop()

# Injeta o CSS Global (do arquivo interface/dashboard_cards.py)
st.markdown(CSS_ESTILO, unsafe_allow_html=True)

# --- BARRA LATERAL (STATUS) ---
with st.sidebar:
    st.header("🔌 Status do Sistema")
    
    # Status GitHub
    if CONFIG_GLOBAL:
        st.markdown(
            """<div style='padding:10px; border-radius:8px; background-color:#dcfce7; border:1px solid #86efac; color:#166534; margin-bottom:10px; font-size:0.9rem'>
            <b>🐙 GitHub Config:</b><br>ONLINE ✅</div>""", unsafe_allow_html=True)
    else:
        st.markdown(
            """<div style='padding:10px; border-radius:8px; background-color:#fee2e2; border:1px solid #fca5a5; color:#991b1b; margin-bottom:10px; font-size:0.9rem'>
            <b>🐙 GitHub Config:</b><br>OFFLINE ❌</div>""", unsafe_allow_html=True)

    # Status Google
    if conn:
        st.markdown(
            """<div style='padding:10px; border-radius:8px; background-color:#dbeafe; border:1px solid #93c5fd; color:#1e40af; font-size:0.9rem'>
            <b>📊 Google Sheets:</b><br>CONECTADO ✅</div>""", unsafe_allow_html=True)
    else:
         st.markdown(
            """<div style='padding:10px; border-radius:8px; background-color:#fee2e2; border:1px solid #fca5a5; color:#991b1b; font-size:0.9rem'>
            <b>📊 Google Sheets:</b><br>ERRO ❌</div>""", unsafe_allow_html=True)
    
    st.markdown("---")
    st.caption(f"Atualizado às: {datetime.now().strftime('%H:%M:%S')}")

# --- CORPO PRINCIPAL ---
st.title("📊 Painel de Controle Oráculo")

# 1. DASHBOARD (CARTÕES VISUAIS)
cols_dash = st.columns(len(CONFIG_GLOBAL["loterias"]))

for i, (nome_lot, cfg) in enumerate(CONFIG_GLOBAL["loterias"].items()):
    with cols_dash[i]:
        # Carrega dados rápidos
        df_card = get_data(conn, cfg['aba_historico'])
        
        # Blindagem: Só desenha se tiver dados
        if df_card is not None and not df_card.empty:
            # Instancia Motor e Gera HTML Visual
            motor_temp = obter_motor(nome_lot, df_card, cfg)
            html_card = gerar_html_card(nome_lot, motor_temp)
            st.markdown(html_card, unsafe_allow_html=True)
        else:
            # Card de Erro/Vazio
            st.warning(f"{nome_lot}: Aguardando dados...")

st.markdown("---")

# 2. ÁREA DE OPERAÇÃO
st.subheader("🛠️ Central de Operações")

escolha = st.selectbox("Selecione a Loteria:", list(CONFIG_GLOBAL["loterias"].keys()))
cfg_atual = CONFIG_GLOBAL["loterias"][escolha]

# Carrega Base Completa
df_main = get_data(conn, cfg_atual['aba_historico'])

if df_main is not None and not df_main.empty:
    # Instancia o Motor Especializado
    MotorAtivo = obter_motor(escolha, df_main, cfg_atual)
    
    tab_gerar, tab_gestao = st.tabs(["🎲 Motor Matemático", "📂 Gestão de Palpites"])
    
    # --- ABA GERADOR ---
    with tab_gerar:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Inteligência: {escolha}**")
            stats = MotorAtivo.get_stats()
            
            # Exibe estatísticas rápidas
            if stats['quentes']:
                st.caption(f"🔥 **Quentes:** {', '.join(map(str, stats['quentes'][:6]))}")
                st.caption(f"❄️ **Frios:** {', '.join(map(str, stats['frios'][:6]))}")
            
            estrategia = st.radio("Estratégia:", ["Equilíbrio", "Tendência", "Mestre"])
            
            if st.button("🔮 Gerar Palpite", type="primary"):
                # O Python executa a lógica do arquivo específico na pasta motores/
                jogo_gerado = MotorAtivo.gerar_palpite(estrategia)
                st.session_state['jogo_atual'] = jogo_gerado
        
        with c2:
            st.markdown("**Resultado Gerado:**")
            if 'jogo_atual' in st.session_state:
                nums = st.session_state['jogo_atual']
                
                # Renderiza bolinhas simples para conferência
                html_bolas = "".join([f"<span style='background:#4f46e5; color:white; padding:8px; border-radius:50%; margin:3px; display:inline-block; width:35px; text-align:center; font-weight:bold; box-shadow:0 2px 4px rgba(0,0,0,0.2)'>{int(n)}</span>" for n in nums])
                st.markdown(html_bolas, unsafe_allow_html=True)
                
                st.write("") # Espaçamento
                
                if st.button("💾 Gravar Palpite na Nuvem"):
                    try:
                        last = pd.to_numeric(df_main['Concurso'], errors='coerce').max()
                        target = int(last) + 1
                    except: target = "Prox"
                    
                    row = [
                        datetime.now().strftime("%d/%m/%Y"),
                        target,
                        str(nums),
                        estrategia,
                        "", "Pendente"
                    ]
                    
                    with st.spinner("Conectando ao Google Drive..."):
                        ok, msg = save_row(conn, cfg_atual['aba_palpites'], row)
                        if ok: st.success(msg)
                        else: st.error(msg)

    # --- ABA GESTÃO ---
    with tab_gestao:
        st.markdown(f"**Visualizando Aba:** `{cfg_atual['aba_palpites']}`")
        df_palp = get_data(conn, cfg_atual['aba_palpites'])
        
        if df_palp is not None:
            st.dataframe(df_palp.tail(10), use_container_width=True)
            st.caption(f"Total de registros: {len(df_palp)}")
            
            st.markdown("### 🗑️ Zona de Exclusão")
            st.warning("Atenção: Ações aqui são irreversíveis.")
            
            cd1, cd2 = st.columns([2, 1])
            with cd1:
                modo_del = st.selectbox("Critério de Exclusão:", ["Últimos N", "Por Concurso", "Limpar Tudo"])
                val_del = 0
                if modo_del == "Últimos N":
                    val_del = st.number_input("Quantidade para apagar:", min_value=1, value=1)
                elif modo_del == "Por Concurso":
                    val_del = st.text_input("Número do Concurso:")
            
            with cd2:
                st.write("")
                st.write("")
                if st.button("🗑️ Executar Exclusão"):
                    with st.spinner("Processando..."):
                        ok, msg = delete_rows(conn, cfg_atual['aba_palpites'], modo_del, val_del)
                        if ok: 
                            st.success(msg)
                            time.sleep(1.5)
                            st.rerun()
                        else: st.error(msg)
        else:
            st.info("Nenhum palpite encontrado nesta aba.")

else:
    st.info(f"Aguardando dados da loteria {escolha} (Aba: {cfg_atual['aba_historico']})...")
