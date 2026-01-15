import streamlit as st
import pandas as pd
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import requests
import json

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Oráculo Master | JSON Config", page_icon="🔮", layout="wide")

# --- 1. CARREGAR CONFIGURAÇÃO DO GITHUB (O CÉREBRO) ---
# Substitua este link pelo seu link RAW do arquivo config_loterias.json que você criou
URL_CONFIG_JSON = "https://raw.githubusercontent.com/SEU_USUARIO/SEU_REPO/main/config_loterias.json"

@st.cache_data(ttl=600) # Atualiza a config a cada 10 min
def carregar_configuracoes():
    try:
        response = requests.get(URL_CONFIG_JSON)
        response.raise_for_status()
        return json.loads(response.text)
    except Exception as e:
        st.error(f"Erro fatal ao ler configurações do GitHub: {e}")
        return None

# Carrega as configurações globais
GLOBAL_CONFIG = carregar_configuracoes()

if not GLOBAL_CONFIG:
    st.stop() # Para o app se não tiver config

SPREADSHEET_ID = GLOBAL_CONFIG["spreadsheet_id"]
MAPA_LOTERIAS = GLOBAL_CONFIG["loterias"]

# --- 2. CONEXÃO COM GOOGLE SHEETS ---
@st.cache_resource
def connect_google_sheets():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        # Pega as credenciais dos Segredos do Streamlit
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        return client.open_by_key(SPREADSHEET_ID)
    except Exception as e:
        st.error(f"Erro de Conexão com Google: {e}")
        return None

def load_sheet_data(tab_name):
    """Lê uma aba específica baseada no nome"""
    try:
        sh = connect_google_sheets()
        ws = sh.worksheet(tab_name)
        data = ws.get_all_values()
        if not data: return None
        return pd.DataFrame(data[1:], columns=data[0])
    except gspread.exceptions.WorksheetNotFound:
        st.warning(f"Aba '{tab_name}' não encontrada na planilha.")
        return None
    except Exception as e:
        st.error(f"Erro ao ler '{tab_name}': {e}")
        return None

def save_prediction(tab_name, row_data):
    """Salva o palpite na aba correta"""
    try:
        sh = connect_google_sheets()
        try:
            ws = sh.worksheet(tab_name)
        except gspread.exceptions.WorksheetNotFound:
            # Cria a aba se não existir
            ws = sh.add_worksheet(title=tab_name, rows=1000, cols=10)
            ws.append_row(["Data", "Concurso Alvo", "Dezenas", "Estratégia", "Acertos", "Status"])
            
        ws.append_row(row_data)
        return True, "Palpite salvo com sucesso!"
    except Exception as e:
        return False, str(e)

def batch_update_results(tab_name, updates):
    """Atualiza conferência em lote"""
    try:
        sh = connect_google_sheets()
        ws = sh.worksheet(tab_name)
        batch = []
        for u in updates:
            # Gspread usa linha, coluna (1-based)
            batch.append({'range': gspread.utils.rowcol_to_a1(u['row'], u['col']), 'values': [[u['val']]]})
        if batch:
            ws.batch_update(batch)
        return True
    except Exception as e:
        return False

# --- INTERFACE ---
st.title("🔮 Oráculo Master | Controle via GitHub")

# Menu Lateral Dinâmico (Vem do JSON)
loteria_selecionada = st.sidebar.selectbox("Escolha a Loteria:", list(MAPA_LOTERIAS.keys()))
config_atual = MAPA_LOTERIAS[loteria_selecionada]

# Informações de Debug no Sidebar
st.sidebar.markdown("---")
st.sidebar.caption("🔧 Configuração Carregada:")
st.sidebar.code(f"Histórico: {config_atual['aba_historico']}\nPalpites: {config_atual['aba_palpites']}\nMax: {config_atual['max_dezenas']}")

if st.sidebar.button("🔄 Atualizar Dados"):
    st.cache_data.clear()
    st.rerun()

# --- CARREGAR HISTÓRICO ---
df = load_sheet_data(config_atual['aba_historico'])

if df is not None:
    # Limpeza e Conversão de Colunas Numéricas (D1, D2...)
    cols_bolas = [c for c in df.columns if c.startswith('D') and any(char.isdigit() for char in c)]
    
    if cols_bolas:
        for c in cols_bolas:
            df[c] = pd.to_numeric(df[c], errors='coerce')
        
        tab1, tab2 = st.tabs(["🎲 Gerar Jogos", "✅ Conferir Resultados"])

        # --- ABA 1: GERADOR ---
        with tab1:
            st.subheader(f"Gerador: {loteria_selecionada}")
            
            # Análise Estatística Rápida
            numeros_validos = df[cols_bolas].values.flatten()
            numeros_validos = numeros_validos[~np.isnan(numeros_validos)]
            
            # Frequência
            contagem = pd.Series(numeros_validos).value_counts().reindex(range(1, config_atual['max_dezenas']+1), fill_value=0)
            
            # Quentes e Frios
            corte = config_atual['max_dezenas'] // 3
            quentes = contagem.sort_values(ascending=False).index[:corte].tolist()
            frios = contagem.sort_values(ascending=True).index[:corte].tolist()
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                estrategia = st.radio("Estratégia:", ["Equilíbrio (Frios+Neutros)", "Tendência (Quentes)", "Mestre (Híbrido)"])
                if st.button("🔮 Gerar Números"):
                    pool = []
                    if "Equilíbrio" in estrategia:
                        pool = frios + list(set(range(1, config_atual['max_dezenas']+1)) - set(quentes))
                    elif "Tendência" in estrategia:
                        pool = quentes
                    else:
                        pool = list(set(quentes + frios))
                    
                    # Garante pool mínimo
                    if len(pool) < config_atual['tamanho_jogo']: 
                        pool = range(1, config_atual['max_dezenas']+1)
                    
                    jogo = np.random.choice(pool, config_atual['tamanho_jogo'], replace=False)
                    jogo.sort()
                    st.session_state['jogo_temp'] = jogo
            
            with col_b:
                if 'jogo_temp' in st.session_state:
                    jogo = st.session_state['jogo_temp']
                    
                    # Renderizar Bolinhas
                    html = "".join([f"<span style='background:#2563eb; color:white; padding:8px; border-radius:50%; margin:3px; font-weight:bold; display:inline-block; width:35px; text-align:center'>{int(n)}</span>" for n in jogo])
                    st.markdown(html, unsafe_allow_html=True)
                    st.write("")
                    
                    if st.button("💾 Salvar na Aba de Palpites"):
                        # Define próximo concurso
                        try:
                            ult_conc = pd.to_numeric(df['Concurso'], errors='coerce').max()
                            prox_conc = int(ult_conc) + 1
                        except:
                            prox_conc = "Prox"
                        
                        linha = [
                            datetime.now().strftime("%d/%m/%Y"),
                            prox_conc,
                            str(list(jogo)),
                            estrategia,
                            "", 
                            "Pendente"
                        ]
                        
                        ok, msg = save_prediction(config_atual['aba_palpites'], linha)
                        if ok: st.success(f"Salvo em '{config_atual['aba_palpites']}'!")
                        else: st.error(msg)

        # --- ABA 2: CONFERIR ---
        with tab2:
            st.markdown(f"### Conferência: {config_atual['aba_palpites']}")
            if st.button("Verificar Acertos"):
                df_palpites = load_sheet_data(config_atual['aba_palpites'])
                
                if df_palpites is None or df_palpites.empty:
                    st.warning("Nenhum palpite encontrado nesta aba.")
                else:
                    updates = []
                    
                    for idx, row in df_palpites.iterrows():
                        status = row.get('Status', '')
                        if 'Pendente' in status or status == '':
                            target = row.get('Concurso Alvo')
                            try:
                                target = int(float(target))
                                # Busca no histórico
                                resultado = df[pd.to_numeric(df['Concurso'], errors='coerce') == target]
                                
                                if not resultado.empty:
                                    # Números sorteados
                                    sorteados = set(resultado[cols_bolas].values.flatten())
                                    sorteados = {x for x in sorteados if not np.isnan(x)}
                                    
                                    # Números jogados
                                    jogo_str = row['Dezenas'].replace('[','').replace(']','')
                                    meu_jogo = [float(x) for x in jogo_str.split(',')]
                                    
                                    acertos = len(set(meu_jogo).intersection(sorteados))
                                    
                                    # Log de atualização
                                    row_num = idx + 2 # Header ocupa linha 1
                                    updates.append({'row': row_num, 'col': 5, 'val': acertos})
                                    updates.append({'row': row_num, 'col': 6, 'val': 'Conferido'})
                            except:
                                pass
                    
                    if updates:
                        ok = batch_update_results(config_atual['aba_palpites'], updates)
                        if ok: 
                            st.success("Conferência realizada com sucesso!")
                            st.rerun()
                        else: st.error("Erro ao atualizar planilha.")
                    else:
                        st.info("Todos os jogos pendentes aguardam a realização do sorteio.")
                    
                    # Exibe Tabela
                    st.dataframe(df_palpites)

    else:
        st.error("Colunas de bolas (D1, D2...) não identificadas.")
else:
    st.warning("Aguardando carregamento da planilha...")
