# --- DASHBOARD DE CARTÕES ---
cols_dash = st.columns(len(CONFIG_GLOBAL["loterias"]))
for i, (nome_lot, cfg) in enumerate(CONFIG_GLOBAL["loterias"].items()):
    with cols_dash[i]:
        df_card = get_data(conn, cfg['aba_historico'])
        
        # SÓ CHAMA O MOTOR SE O DF EXISTIR
        if df_card is not None and not df_card.empty:
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
        else:
            # CARTÃO DE ERRO (CASO NÃO CARREGUE A ABA)
            st.markdown(f"""
            <div class="card-dashboard signal-wait" style="background:#fef2f2">
                <div style="font-size:0.9rem; color:#555">{nome_lot}</div>
                <div style="font-size:0.8rem; color:red">Dados Indisponíveis</div>
                <div style="margin-top:5px">⚠️</div>
            </div>
            """, unsafe_allow_html=True)
