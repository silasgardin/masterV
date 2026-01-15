import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import json
from datetime import datetime

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Oráculo Master V12", page_icon="🔮", layout="wide")

# --- INICIALIZAÇÃO DE VARIÁVEIS DE SEGURANÇA ---
# Isso evita o NameError se algo falhar antes
df = None 
info_loteria = None

# --- IMPORTAÇÃO DO MOTOR (LOCAL) ---
try:
    from motor_matematico import OraculoBrain
    Brain = OraculoBrain()
except ImportError:
    st.error("ERRO CRÍTICO: O arquivo 'motor_matematico.py' não foi encontrado no seu GitHub.")
    st.stop()

# --- CARREGAR CONFIGURAÇÃO (JSON) ---
# ATENÇÃO: Verifique se este LINK está correto para o seu repositório
URL_CONFIG = "https://raw.githubusercontent.com/silasgardin/masterV/refs/heads/main/config_loterias.json"

@st.cache_data(ttl=600)
def load_config():
    try:
        response = requests.get(URL_CONFIG)
        if response.status_code != 200:
            st.error(f"Não foi possível ler o arquivo JSON no GitHub. Status: {response.status_code}")
            return None
        return json.loads(response.text)
    except Exception as e:
        st.error(f"Erro ao processar JSON: {e}")
        return None

CONFIG_GLOBAL = load_config()

# Se não conseguiu ler a configuração, para tudo aqui.
if not CONFIG_GLOBAL:
    st.warning("⚠️ Verifique se você editou a variável 'URL_CONFIG' na linha 27 do app.py com o seu link do GitHub.")
    st.stop()

# --- CONEXÃO COM GOOGLE SHEETS ---
@st.cache_resource
def connect_google():
    try:
        # Verifica se os segredos existem
        if "gcp_service_account" not in st.secrets:
            st.error("Segredos do Google (gcp_service_account) não encontrados no Streamlit.")
            return None
            
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), scope)
        return gspread.authorize(creds).open_by_key(CONFIG_GLOBAL["spreadsheet_id"])
    except Exception as e:
        st.error(f"Erro de Conexão com Google: {e}")
        return None

def get_data(tab):
    try:
        conn = connect_google()
        if not conn: return None
        ws = conn.worksheet(tab)
        data = ws.get_all_values()
        if not data: return None
        return pd.DataFrame(data[1:], columns=data[0])
    except gspread.exceptions.WorksheetNotFound:
        st.warning(f"Aba '{tab}' não encontrada na planilha. Verifique o nome no JSON.")
        return None
    except Exception as e:
        st.error(f"Erro ao ler '{tab}': {e}")
        return None

def save_prediction(tab, row):
    try:
        conn = connect_google()
        if not conn: return False, "Sem conexão"
        try: ws = conn.worksheet(tab)
        except: 
            ws = conn.add_worksheet(title=tab, rows=1000, cols=10)
            ws.append_row(["Data", "Concurso Alvo", "Dezenas", "Estratégia", "Acertos", "Status"])
        ws.append_row(row)
        return True, "Salvo!"
    except Exception as e: return False, str(e)

# --- INTERFACE PRINCIPAL ---
st.title("🔮 Oráculo Master | Arquitetura MVC")

# Menu Lateral
loterias = CONFIG_GLOBAL["loterias"]
escolha = st.sidebar.selectbox("Loteria:", list(loterias.keys()))
cfg_user = loterias[escolha]

# --- CARREGAMENTO DE DADOS (Aqui definimos o df) ---
with st.spinner(f"Carregando dados de {escolha}..."):
    df = get_data(cfg_user["aba_historico"])

# --- LÓGICA DO APP ---
# Só entra aqui se df foi carregado com sucesso (não é None e não está vazio)
if df is not None and not df.empty:
    
    # Chama o Motor Matemático
    info_loteria = Brain.detectar_configuracao(df)
    
    if info_loteria:
        # Dashboard de Sinal
        sinal_texto, sinal_tipo = Brain.analise_sinal_entrada(df, info_loteria)
        cor_sinal = "#10b981" if sinal_tipo == "go" else "#ef4444"
        
        st.markdown(f"""
        <div style="padding:20px; background:white; border-radius:10px; border-left:5px solid {cor_sinal}; box-shadow:0 2px 5px rgba(0,0,0,0.1); margin-bottom: 20px;">
            <h3 style="margin:0; color:#333">{escolha}</h3>
            <span style="font-size:1.2rem; font-weight:bold; color:{cor_sinal}">{sinal_texto}</span>
        </div>
        """, unsafe_allow_html=True)

        # Abas de Operação
        tab1, tab2 = st.tabs(["🎲 Gerador", "📊 Conferência"])
        
        # --- ABA GERADOR ---
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Parâmetros")
                # Cálculos estatísticos
                stats = Brain.calcular_estatisticas(df, info_loteria['cols'], info_loteria['max'])
                
                # Exibe resumo (Top 5)
                st.write(f"🔥 **Quentes:** {', '.join(map(str, stats['quentes'][:5]))}")
                st.write(f"❄️ **Frios:** {', '.join(map(str, stats['frios'][:5]))}")
                
                estrategia = st.radio("Estratégia:", ["Equilíbrio", "Tendência", "Mestre"])
                
                if st.button("🔮 Gerar Palpite", type="primary"):
                    todos_palpites = Brain.gerar_palpites(stats, info_loteria)
                    st.session_state['jogo_atual'] = todos_palpites[estrategia]
            
            with col2:
                st.subheader("Resultado")
                if 'jogo_atual' in st.session_state:
                    numeros = st.session_state['jogo_atual']
                    
                    # Render visual das bolas
                    html = "".join([f"<span style='background:#3b82f6; color:white; padding:8px; border-radius:50%; margin:3px; display:inline-block; width:35px; text-align:center; font-weight:bold'>{int(n)}</span>" for n in numeros])
                    st.markdown(html, unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    if st.button("💾 Salvar na Nuvem"):
                        try:
                            ult_conc = pd.to_numeric(df['Concurso'], errors='coerce').max()
                            prox = int(ult_conc) + 1
                        except: prox = "Prox"
                        
                        linha = [
                            datetime.now().strftime("%d/%m/%Y"),
                            prox,
                            str(numeros),
                            estrategia,
                            "", "Pendente"
                        ]
                        
                        with st.spinner("Salvando..."):
                            ok, msg = save_prediction(cfg_user["aba_palpites"], linha)
                            if ok: st.success(msg)
                            else: st.error(msg)

        # --- ABA CONFERÊNCIA ---
        with tab2:
            st.info(f"Visualizando palpites em: **{cfg_user['aba_palpites']}**")
            df_palp = get_data(cfg_user["aba_palpites"])
            
            if df_palp is not None and not df_palp.empty:
                st.dataframe(df_palp, use_container_width=True)
            else:
                st.warning("Ainda não há palpites salvos para esta loteria.")

    else:
        st.error("Não foi possível identificar as colunas de dezenas (D1, D2...) no histórico.")

elif df is None:
    # Se df é None, significa que get_data falhou (já mostrou erro acima) ou está carregando
    pass 

else:
    # Se df existe mas está vazio
    st.warning("A aba de histórico está vazia.")
