import streamlit as st
import pandas as pd
# ... (imports de conexão Google/Github iguais ao anterior) ...

# --- IMPORTAÇÃO DOS MOTORES ---
from motores.base import MotorBase
from motores.mega_sena import MotorMegaSena
from motores.lotofacil import MotorLotofacil
# from motores.quina import MotorQuina (Faria depois)

# --- FÁBRICA DE MOTORES ---
def obter_motor(nome_loteria, df, config):
    """Seleciona o especialista correto"""
    if nome_loteria == "Mega Sena":
        return MotorMegaSena(df, config)
    elif nome_loteria == "Lotofácil":
        return MotorLotofacil(df, config)
    else:
        # Se não tiver motor específico, usa o genérico
        return MotorBase(df, config)

# ... (Código de carregar JSON e Google Sheets igual) ...

# --- DENTRO DA INTERFACE ---
if df is not None:
    # INSTANCIA O MOTOR CORRETO
    Brain = obter_motor(loteria_selecionada, df, config_atual)
    
    # Agora usamos o Brain específico
    with tab1:
        # ...
        if st.button("Gerar Palpite"):
            # O método gerar_palpite agora é inteligente!
            # Se for Mega, ele checa soma e sequência.
            # Se for Lotofácil, ele checa repetidas.
            jogo = Brain.gerar_palpite(estrategia)
            st.session_state['jogo'] = jogo
