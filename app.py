import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import json
from datetime import datetime
import time

# --- 1. IMPORTAÇÃO DOS MOTORES (LÓGICA MATEMÁTICA) ---
# O try/except evita que o app quebre se você ainda não tiver criado todos os arquivos
try:
    from motores.base import MotorBase
    from motores.mega_sena import MotorMegaSena
    from motores.lotofacil import MotorLotofacil
    # Adicione aqui novos jogos conforme criar os arquivos na pasta motores/
    # from motores.quina import MotorQuina 
except ImportError as e:
    st.error(f"❌ ERRO CRÍTICO DE IMPORTAÇÃO: {e}")
    st.info("Verifique se a pasta 'motores' existe e contém os arquivos 'base.py', 'mega_sena.py', etc.")
    st.stop()

# --- 2. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Oráculo Master Pro", page_icon="🔮", layout="wide")

# CSS para os Cartões do Dashboard
st.markdown("""
<style>
    .card-dashboard {
        padding: 15px; border-radius: 10px; border: 1px solid #e5e7eb;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center;
        transition: transform 0.2s; background: white;
    }
    .card-dashboard:hover { transform: translateY(-3px); border-color: #3b82f6; }
    .signal-go { border-left: 5px solid #10b981; }
    .signal-wait { border-left: 5px solid #ef4444; }
    .big-number { font-size: 1.2rem; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 3. FÁBRICA DE MOTORES (FACTORY PATTERN) ---
def obter_motor(nome_loteria, df, config):
    """
    Decide qual classe usar baseada no nome da loteria.
    Se não houver específica, usa a MotorBase.
    """
    if nome_loteria == "Mega Sena":
        return MotorMegaSena(df, config)
    elif nome_loteria == "Lotofácil":
        return MotorLotofacil(df, config)
    # elif nome_loteria == "Quina": return MotorQuina(df, config)
    else:
        return MotorBase(df, config)

# --- 4. FUNÇÕES DE INFRAESTRUTURA (CONFIG E CONEXÃO) ---

def get_config_url():
    """Busca o link do JSON dentro do secrets.toml"""
    try:
        return st.secrets["setup"]["url_config_json"]
    except Exception:
        st.error("⚠️ Configuração 'url_config_json' não encontrada no secrets.toml.")
        st.stop()

@st.cache_data(ttl=600)
def load_config():
    url = get_config_url()
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            st.error(f"Erro ao ler GitHub: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return None

CONFIG_GLOBAL = load_config()
if not CONFIG_GLOBAL: st.stop()

@st.cache_resource
def connect_google():
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

# Funções CRUD (Create, Read, Delete)
def get_data(conn, tab):
    try:
        ws = conn.worksheet(tab)
        data = ws.get_all_values()
        if len(data) < 2: return None
        return pd.DataFrame(data[1:], columns=data[0])
    except: return None # Retorna None se a aba não existir ou der erro

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
            
        # Reescreve a aba
        ws.clear()
        ws.append_row(header)
        if not df.empty:
            ws.update('A2', df.values.tolist())
            
        return True, f"{original_count - len(df)} registros deletados."
    except Exception as e: return False, str(e)

# --- 5. INTERFACE DO USUÁRIO (VIEW) ---

conn = connect_google()
if not conn: st.stop()

st.title("📊 Oráculo Master | Dashboard")

# --- DASHBOARD DE CARTÕES ---
# Carrega todas as loterias rapidamente para mostrar o status
cols_dash = st.columns(len(CONFIG_GLOBAL["loterias"]))
for i, (nome_lot, cfg) in enumerate(CONFIG_GLOBAL["loterias"].items()):
    with cols_dash[i]:
        df_card = get_data(conn, cfg['aba_historico'])
        
        # Instancia o motor correto só para pegar o sinal
        motor_temp = obter_motor(nome_lot, df_card, cfg)
        sinal_txt, sinal_tipo = motor_temp.analisar_sinal()
        
        css_class = "signal-go" if sinal_tipo == "go" else "signal-wait"
        icon = "🟢" if sinal_tipo == "go" else "🟡"
        
        st.markdown(f"""
        <div class="card-dashboard {css_class}">
            <div style="font-size:0.9rem; color:#555">{nome_lot}</div>
            <div class="big-number">{sinal_txt}</div>
            <div style="margin-top:5px">{icon}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# --- ÁREA DE OPERAÇÃO ---
st.subheader("🛠️ Área de Operação")
escolha = st.selectbox("Selecione a Loteria:", list(CONFIG_GLOBAL["loterias"].keys()))
cfg_atual = CONFIG_GLOBAL["loterias"][escolha]

# Carrega Dados Completos
df_main = get_data(conn, cfg_atual['aba_historico'])

if df_main is not None:
    # >>> PONTO CHAVE: Instancia o Motor Especializado <<<
    MotorAtivo = obter_motor(escolha, df_main, cfg_atual)
    
    tab_gerar, tab_gestao = st.tabs(["🎲 Motor Matemático", "📂 Gestão de Palpites"])
    
    # --- ABA 1: GERAR ---
    with tab_gerar:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Análise: {escolha}**")
            stats = MotorAtivo.get_stats()
            st.caption(f"🔥 Quentes: {', '.join(map(str, stats['quentes'][:5]))}")
            st.caption(f"❄️ Frios: {', '.join(map(str, stats['frios'][:5]))}")
            
            estrategia = st.radio("Estratégia:", ["Equilíbrio", "Tendência", "Mestre"])
            
            if st.button("🔮 Acionar Motor de Cálculo", type="primary"):
                # O Python executa a lógica específica do arquivo na pasta motores/
                jogo_gerado = MotorAtivo.gerar_palpite(estrategia)
                st.session_state['jogo_atual'] = jogo_gerado
        
        with c2:
            st.markdown("**Resultado:**")
            if 'jogo_atual' in st.session_state:
                nums = st.session_state['jogo_atual']
                # Renderiza bolinhas
                html = "".join([f"<span style='background:#2563eb; color:white; padding:8px; border-radius:50%; margin:3px; display:inline-block; width:35px; text-align:center; font-weight:bold'>{int(n)}</span>" for n in nums])
                st.markdown(html, unsafe_allow_html=True)
                
                st.write("")
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
                    
                    with st.spinner("Gravando..."):
                        ok, msg = save_row(conn, cfg_atual['aba_palpites'], row)
                        if ok: st.success(msg)
                        else: st.error(msg)

    # --- ABA 2: GESTÃO ---
    with tab_gestao:
        st.write(f"Gerenciando aba: **{cfg_atual['aba_palpites']}**")
        df_palp = get_data(conn, cfg_atual['aba_palpites'])
        
        if df_palp is not None:
            st.dataframe(df_palp.tail(10), use_container_width=True)
            st.caption(f"Total de registros: {len(df_palp)}")
            
            st.markdown("### 🗑️ Zona de Exclusão")
            cd1, cd2 = st.columns([2, 1])
            with cd1:
                modo_del = st.selectbox("Critério:", ["Últimos N", "Por Concurso", "Limpar Tudo"])
                val_del = 0
                if modo_del == "Últimos N":
                    val_del = st.number_input("Quantidade:", min_value=1, value=1)
                elif modo_del == "Por Concurso":
                    val_del = st.text_input("Número do Concurso:")
            
            with cd2:
                st.write("")
                st.write("")
                if st.button("Deletar Registros"):
                    with st.spinner("Deletando..."):
                        ok, msg = delete_rows(conn, cfg_atual['aba_palpites'], modo_del, val_del)
                        if ok: 
                            st.success(msg)
                            time.sleep(1)
                            st.rerun()
                        else: st.error(msg)
        else:
            st.info("Nenhum palpite salvo ainda.")

else:
    st.warning("Carregando histórico ou aba não encontrada...")
