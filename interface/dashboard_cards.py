import pandas as pd

# --- CSS MODERNIZADO ---
CSS_ESTILO = """
<style>
    /* Reset e Ajustes Gerais */
    .block-container { padding-top: 2rem !important; }
    #MainMenu, footer, header { visibility: hidden; }

    /* Animações */
    @keyframes pulse-border {
        0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
        100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }

    /* Card Principal */
    .card-loteria {
        background: #ffffff;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.05);
        border: 1px solid #f1f5f9;
        margin-bottom: 25px;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        height: 100%;
    }
    .card-loteria:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        border-color: #cbd5e1;
    }

    /* Topo Colorido */
    .card-top {
        padding: 15px 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: white;
        font-weight: bold;
    }
    .loteria-name { font-size: 1.1rem; letter-spacing: 0.5px; text-transform: uppercase; }
    .next-conc { 
        font-size: 0.75rem; 
        background: rgba(255,255,255,0.2); 
        padding: 4px 10px; 
        border-radius: 12px;
    }

    /* Corpo */
    .card-body {
        padding: 20px;
        text-align: center;
        flex-grow: 1;
    }
    .status-pill {
        display: inline-block;
        font-size: 0.7rem;
        font-weight: 800;
        text-transform: uppercase;
        padding: 5px 12px;
        border-radius: 20px;
        margin-bottom: 10px;
        letter-spacing: 1px;
    }
    .st-acumulado { background: #fff7ed; color: #c2410c; border: 1px solid #fdba74; }
    .st-normal { background: #f8fafc; color: #64748b; border: 1px solid #e2e8f0; }

    .prize-value {
        font-size: 1.8rem;
        font-weight: 800;
        color: #1e293b;
        margin-bottom: 5px;
    }
    .prize-label { font-size: 0.8rem; color: #94a3b8; margin-bottom: 20px; }

    /* Bolas */
    .balls-wrapper {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 6px;
        margin-top: 10px;
    }
    .ball-display {
        width: 32px; height: 32px;
        background: #f1f5f9;
        color: #334155;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 0.9rem;
        border: 1px solid #e2e8f0;
    }
    .ball-sm { width: 28px; height: 28px; font-size: 0.8rem; }

    /* Rodapé */
    .card-foot {
        background: #f8fafc;
        padding: 12px 20px;
        border-top: 1px solid #e2e8f0;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .ai-signal { display: flex; align-items: center; gap: 8px; font-size: 0.85rem; font-weight: 700; }
    .dot-pulse { width: 10px; height: 10px; border-radius: 50%; }
    
    .sig-go { color: #059669; }
    .dot-go { background: #10b981; animation: pulse-border 2s infinite; }
    
    .sig-wait { color: #d97706; }
    .dot-wait { background: #f59e0b; }
    
    /* Ticket */
    .ticket-container {
        background: #fff; border: 2px dashed #cbd5e1; border-radius: 12px;
        padding: 20px; text-align: center; margin-top: 10px;
    }
    .ball-ticket {
        width: 40px; height: 40px; color: white; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-weight: 800; font-size: 1.1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
</style>
"""

def get_style(nome):
    n = nome.lower()
    if "lotof" in n: return "#9d174d", "ball-sm" # Roxo
    if "mega" in n: return "#1e40af", ""         # Azul
    if "quina" in n: return "#4338ca", ""        # Roxo/Azul
    return "#475569", ""

def formatar_moeda(valor):
    try:
        v_str = str(valor).replace("R$", "").replace(".", "").replace(",", ".")
        v_float = float(v_str)
        return f"R$ {v_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return str(valor)

def gerar_html_card(nome_loteria, motor):
    # 1. Dados Básicos
    txt_sinal, tipo_sinal = motor.analisar_sinal()
    cor_header, classe_bola = get_style(nome_loteria)
    
    concurso_atual = "--"
    prox_concurso = "--"
    premio_display = "Apurando..."
    numeros = []
    
    try:
        if motor.df is not None and not motor.df.empty:
            last = motor.df.iloc[0]
            concurso_atual = str(last.get('Concurso', '--'))
            try: prox_concurso = str(int(concurso_atual) + 1)
            except: prox_concurso = "Prox"

            colunas_premio = ['Prêmio Estimado', 'Estimativa Próximo', 'Valor Acumulado', 'Acumulado']
            for col in colunas_premio:
                if col in last:
                    val = last.get(col)
                    if val and str(val).strip() not in ['0', '0,00', '']:
                        premio_display = formatar_moeda(val)
                        break
            
            for c in motor.cols:
                val = last.get(c)
                try: 
                    if val and str(val).strip(): numeros.append(int(float(val)))
                except: pass
    except: pass

    status_class = "st-normal"
    status_text = "SORTEIO REALIZADO"
    if "ACUMULADO" in txt_sinal or "ACUMULOU" in txt_sinal:
        status_class = "st-acumulado"
        status_text = "ACUMULOU! 💰"
        if premio_display == "Apurando...": premio_display = "Prêmio Milionário"

    dot_class = "dot-go" if tipo_sinal == "go" else "dot-wait"
    txt_class = "sig-go" if tipo_sinal == "go" else "sig-wait"
    html_bolas = "".join([f'<div class="ball-display {classe_bola}">{n}</div>' for n in numeros])

    # CORREÇÃO DO ERRO: REMOVENDO ESPAÇOS E LINHAS EM BRANCO DO HTML
    return f"""<div class="card-loteria"><div class="card-top" style="background: {cor_header}"><div class="loteria-name">{nome_loteria}</div><div class="next-conc">Próx: {prox_concurso}</div></div><div class="card-body"><div class="status-pill {status_class}">{status_text}</div><div class="prize-value">{premio_display}</div><div class="prize-label">Estimativa para o prêmio</div><div style="font-size:0.75rem; color:#ccc; margin-bottom:5px">Último: {concurso_atual}</div><div class="balls-wrapper">{html_bolas}</div></div><div class="card-foot"><div class="ai-signal {txt_class}"><div class="dot-pulse {dot_class}"></div>{txt_sinal}</div><div style="font-size:1.2rem">🤖</div></div></div>"""

def gerar_ticket_visual(nome_loteria, numeros):
    cor, _ = get_style(nome_loteria)
    html_bolas = "".join([f'<div class="ball-ticket" style="background:{cor}">{int(n)}</div>' for n in numeros])
    return f"""<div class="ticket-container"><div style="text-transform:uppercase; color:#94a3b8; font-size:0.8rem; margin-bottom:10px">Palpite Gerado • {nome_loteria}</div><div style="display:flex; flex-wrap:wrap; gap:8px; justify-content:center;">{html_bolas}</div></div>"""
