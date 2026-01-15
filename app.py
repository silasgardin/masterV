# ... (imports normais: streamlit, pandas, gspread...) ...
import streamlit as st

# --- IMPORTS DO PROJETO ---
try:
    from motores.base import MotorBase
    from motores.mega_sena import MotorMegaSena
    from motores.lotofacil import MotorLotofacil
    
    # IMPORTA O DESIGN DA PASTA NOVA
    from interface.dashboard_cards import CSS_ESTILO, gerar_html_card
    
except ImportError as e:
    st.error(f"Erro de importação: {e}")
    st.stop()

# ... (funções load_config e connect_google mantêm-se iguais) ...
# ... (funções get_data, obter_motor mantêm-se iguais) ...

# --- INÍCIO DA INTERFACE ---
conn = connect_google()
if not conn: st.stop()

# 1. INJETA O CSS (Uma única vez)
st.markdown(CSS_ESTILO, unsafe_allow_html=True)

st.title("📊 Painel de Controle Oráculo")

# 2. RENDERIZA OS CARDS (Loop Limpo)
cols = st.columns(len(CONFIG_GLOBAL["loterias"]))

for i, (nome, cfg) in enumerate(CONFIG_GLOBAL["loterias"].items()):
    with cols[i]:
        df_temp = get_data(conn, cfg['aba_historico'])
        
        if df_temp is not None and not df_temp.empty:
            # Cria o motor
            motor = obter_motor(nome, df_temp, cfg)
            
            # CHAMA O ARQUIVO SEPARADO PARA DESENHAR
            html_final = gerar_html_card(nome, motor)
            
            # Exibe
            st.markdown(html_final, unsafe_allow_html=True)
        else:
            st.warning(f"Sem dados: {nome}")

# ... (Resto do código das abas de operação continua igual) ...
