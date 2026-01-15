import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import json
from datetime import datetime
import time

# --- 1. CONFIGURAÇÃO DA PÁGINA (Deve ser a primeira linha executável) ---
st.set_page_config(page_title="Oráculo Master Pro", page_icon="🔮", layout="wide")

# --- 2. IMPORTS DOS MÓDULOS (Lógica e Design) ---
try:
    # Motores Matemáticos (Back-end)
    from motores.base import MotorBase
    from motores.mega_sena import MotorMegaSena
    from motores.lotofacil import MotorLotofacil
    # Novos Motores (Se o arquivo não existir, o try/except evita o crash)
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
    st.info("Verifique se as pastas 'motores' e 'interface' existem no GitHub.")
    st.stop()

# --- 3. INFRAESTRUTURA (Configuração e Conexão) ---

def get_config_url():
    """Busca o link do JSON nos Secrets"""
    try:
        return st.secrets["setup"]["url_config_json"]
    except Exception:
        st.error("⚠️ Erro: Link do JSON não encontrado na seção [setup] do secrets.toml.")
        st.stop()

@st.cache_data(ttl=600)
def load_config():
    """Baixa o JSON de Configuração do GitHub"""
    url = get_config_url()
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            st.error(f"Erro GitHub: Status {response.status_code}. Verifique se o repositório é Público.")
            return None
    except Exception as e:
        st.error(f"Erro de Conexão GitHub: {e}")
        return None

# Carrega a configuração global
CONFIG_GLOBAL = load_config()
if not CONFIG_GLOBAL: st.stop()

@st.cache_resource
def connect_google():
    """Autenticação com Google Sheets"""
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

# --- 4. FUNÇÕES OPERACIONAIS (Fábrica e CRUD) ---

def obter_motor(nome_loteria, df, config):
    """Factory Pattern: Retorna a classe especialista correta"""
    nome = nome_loteria.lower()
    
    # Roteamento Inteligente
    if "mega" in nome: 
        return MotorMegaSena(df, config)
    elif "facil" in nome or "fácil" in nome: 
        return MotorLotofacil(df, config)
    elif "quina" in nome and MotorQuina: 
        return MotorQuina(df, config)
    elif "dia" in nome and "sorte" in nome and MotorDiaDeSorte: 
        return MotorDiaDeSorte(df, config)
    elif "dupla" in nome and MotorDuplaSena: 
        return MotorDuplaSena(df, config)
    else: 
        # Fallback para o motor genérico se não tiver específico
        return MotorBase(df, config)

def get_data(conn, tab):
    """Lê os dados da planilha com tratamento de erro"""
    try:
        ws = conn.worksheet(tab)
        data = ws.get_all_values()
        if len(data) < 2: return None
        return pd.DataFrame(data[1:], columns=data[0])
    except: return None

def save_row(conn, tab, row):
    """Salva um novo palpite na aba"""
    try:
        try: ws = conn.worksheet(tab)
        except: 
            ws = conn.add_worksheet(title=tab, rows=1000, cols=10)
            ws.append_row(["Data", "Concurso Alvo", "Dezenas", "Estratégia", "Acertos", "Status"])
        ws.append_row(row)
        return True, "✅ Palpite registrado com sucesso na nuvem!"
    except Exception as e: return False, str(e)

def delete_rows(conn, tab, mode, val):
    """Gerencia a exclusão de registros"""
    try:
        ws = conn.worksheet(tab)
        data = ws.get_all_values()
        if len(data) < 2: return False, "Planilha vazia"
        
        header = data[0]
        rows = data[1:]
        df = pd.DataFrame(rows, columns=header)
        orig_len = len(df)
        
        if mode == "Limpar Tudo": df = df.iloc[0:0]
        elif mode == "Últimos N":
            try: df = df.iloc[:-int(val)]
            except: pass
        elif mode == "Por Concurso": df = df[df['Concurso Alvo'] != str(val)]
        
        ws.clear()
        ws.append_row(header)
        if not df.empty: ws.update('A2', df.values.tolist())
        return True, f"{orig_len - len(df)} registros removidos."
    except Exception as e: return False, str(e)

# --- 5. INICIALIZAÇÃO DA INTERFACE ---

conn = connect_google()
if not conn: st.stop()

# Injeta o CSS Global (Design Moderno e Animações)
st.markdown(CSS_ESTILO, unsafe_allow_html=True)

# --- BARRA LATERAL (MONITORAMENTO) ---
with st.sidebar:
    st.header("🔌 Status do Sistema")
    
    # Indicador GitHub
    status_gh = "ONLINE ✅" if CONFIG_GLOBAL else "OFFLINE ❌"
    bg_gh = "#dcfce7" if CONFIG_GLOBAL else "#fee2e2"
    border_gh = "#86efac" if CONFIG_GLOBAL else "#fca5a5"
    color_gh = "#166534" if CONFIG_GLOBAL else "#991b1b"
    
    st.markdown(f"""
    <div style='padding:12px; border-radius:8px; background-color:{bg_gh}; border:1px solid {border_gh}; color:{color_gh}; margin-bottom:10px; font-size:0.85rem'>
        <b>🐙 GitHub Config:</b><br>{status_gh}
    </div>""", unsafe_allow_html=True)

    # Indicador Google Sheets
    status_go = "CONECTADO ✅" if conn else "FALHA ❌"
    bg_go = "#dbeafe" if conn else "#fee2e2"
    border_go = "#93c5fd" if conn else "#fca5a5"
    color_go = "#1e40af" if conn else "#991b1b"

    st.markdown(f"""
    <div style='padding:12px; border-radius:8px; background-color:{bg_go}; border:1px solid {border_go}; color:{color_go}; font-size:0.85rem'>
        <b>📊 Google Sheets:</b><br>{status_go}
    </div>""", unsafe_allow_html=True)
    
    st.markdown("---")
    st.caption(f"Sincronização: {datetime.now().strftime('%H:%M:%S')}")

# --- CORPO PRINCIPAL ---
st.title("📊 Painel de Controle Oráculo")

# 1. DASHBOARD INTELIGENTE (GRID LAYOUT)
# Distribui os cards em colunas de 3 em 3 para visual moderno
COLS_PER_ROW = 3
loterias_items = list(CONFIG_GLOBAL["loterias"].items())

for i in range(0, len(loterias_items), COLS_PER_ROW):
    cols = st.columns(COLS_PER_ROW)
    for j in range(COLS_PER_ROW):
        if i + j < len(loterias_items):
            nome_lot, cfg = loterias_items[i + j]
            with cols[j]:
                # Busca dados rápidos para o card
                df_card = get_data(conn, cfg['aba_historico'])
                
                if df_card is not None and not df_card.empty:
                    # Instancia motor temporário para análise de sinal
                    motor_temp = obter_motor(nome_lot, df_card, cfg)
                    # Renderiza HTML moderno da pasta Interface
                    html_card = gerar_html_card(nome_lot, motor_temp)
                    st.markdown(html_card, unsafe_allow_html=True)
                else:
                    st.warning(f"{nome_lot}: Sincronizando...")

st.markdown("---")

# 2. CENTRAL DE OPERAÇÕES
st.subheader("🛠️ Central de Operações")

escolha = st.selectbox("Selecione a Loteria:", list(CONFIG_GLOBAL["loterias"].keys()))
cfg_atual = CONFIG_GLOBAL["loterias"][escolha]

# Carrega a base completa para operação
df_main = get_data(conn, cfg_atual['aba_historico'])

if df_main is not None and not df_main.empty:
    # Instancia o Motor Matemático Principal
    MotorAtivo = obter_motor(escolha, df_main, cfg_atual)
    
    tab_gerar, tab_gestao = st.tabs(["🎲 Gerador & Estratégia", "📂 Gestão de Palpites"])
    
    # --- ABA 1: GERADOR ---
    with tab_gerar:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Inteligência Ativa: {escolha}**")
            stats = MotorAtivo.get_stats()
            
            if stats['quentes']:
                st.caption(f"🔥 **Quentes:** {', '.join(map(str, stats['quentes'][:6]))}")
                st.caption(f"❄️ **Frios:** {', '.join(map(str, stats['frios'][:6]))}")
            
            estrategia = st.radio("Selecione a Estratégia:", ["Equilíbrio", "Tendência", "Mestre"])
            
            if st.button("🔮 Gerar Palpite Otimizado", type="primary"):
                # Executa a matemática do motor selecionado
                jogo_gerado = MotorAtivo.gerar_palpite(estrategia)
                st.session_state['jogo_atual'] = jogo_gerado
        
        with c2:
            st.markdown("**Resultado da Análise:**")
            if 'jogo_atual' in st.session_state:
                nums = st.session_state['jogo_atual']
                
                # Renderiza o visual de "Ticket" (Cupom)
                html_ticket = gerar_ticket_visual(escolha, nums)
                st.markdown(html_ticket, unsafe_allow_html=True)
                
                st.write("") 
                
                if st.button("💾 Gravar Palpite na Nuvem", use_container_width=True):
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
                    
                    with st.spinner("Conectando ao banco de dados..."):
                        ok, msg = save_row(conn, cfg_atual['aba_palpites'], row)
                        if ok: st.success(msg)
                        else: st.error(msg)

    # --- ABA 2: GESTÃO ---
    with tab_gestao:
        st.markdown(f"**Visualizando Aba:** `{cfg_atual['aba_palpites']}`")
        df_palp = get_data(conn, cfg_atual['aba_palpites'])
        
        if df_palp is not None:
            st.dataframe(df_palp.tail(10), use_container_width=True)
            st.caption(f"Exibindo os últimos 10 de {len(df_palp)} registros.")
            
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
                if st.button("🗑️ Executar Exclusão"):
                    with st.spinner("Processando exclusão..."):
                        ok, msg = delete_rows(conn, cfg_atual['aba_palpites'], modo_del, val_del)
                        if ok: 
                            st.success(msg)
                            time.sleep(1.5)
                            st.rerun()
                        else: st.error(msg)
        else:
            st.info("Nenhum histórico de palpites encontrado.")

else:
    st.info(f"Carregando base de dados da loteria {escolha}...")
