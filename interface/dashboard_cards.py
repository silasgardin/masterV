import pandas as pd

# --- DESIGN SYSTEM AVANÇADO ---
CSS_ESTILO = """
<style>
    /* --- 1. LIMPEZA GERAL (Whitelabel) --- */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .block-container {
        padding-top: 2rem !important; /* Sobe o conteúdo */
    }

    /* --- 2. ANIMAÇÕES (Pulse) --- */
    @keyframes pulse-green {
        0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
        100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
    
    @keyframes pulse-yellow {
        0% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.7); }
        70% { box-shadow: 0 0 0 6px rgba(245, 158, 11, 0); }
        100% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0); }
    }

    /* --- 3. CARDS DO DASHBOARD --- */
    .card-loteria {
        background-color: #ffffff;
        border-radius: 16px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid #f0f2f5;
        transition: all 0.3s ease;
    }
    .card-loteria:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.08);
    }

    /* Cabeçalho do Card */
    .card-header {
        display: flex; justify-content: space-between; align-items: flex-start;
        margin-bottom: 15px; border-bottom: 1px solid #f0f2f5; padding-bottom: 10px;
    }
    .card-title { font-size: 1.1rem; font-weight: 800; margin: 0; }
    .card-conc { font-size: 0.75rem; color: #9ca3af; }

    /* Badges */
    .status-badge { font-size: 0.65rem; padding: 3px 8px; border-radius: 12px; font-weight: 700; text-transform: uppercase; }
    .bg-acumulado { background-color: #fffbeb; color: #b45309; border: 1px solid #fcd34d; }
    .bg-normal { background-color: #f3f4f6; color: #9ca3af; }

    /* Bolas do Dashboard (Pequenas) */
    .balls-container { display: flex; flex-wrap: wrap; gap: 5px; justify-content: center; margin: 15px 0; }
    
    .ball-dash {
        width: 28px; height: 28px;
        color: white; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 0.8rem;
    }

    /* Rodapé com Luzes */
    .card-footer {
        background-color: #f9fafb; margin: -20px; padding: 12px 20px;
        margin-top: 15px; border-radius: 0 0 16px 16px;
        display: flex; align-items: center; gap: 10px;
    }
    .dot { width: 10px; height: 10px; border-radius: 50%; }
    
    /* Aplica a animação */
    .dot-green { background-color: #10b981; animation: pulse-green 2s infinite; }
    .dot-yellow { background-color: #f59e0b; animation: pulse-yellow 2s infinite; }
    
    .footer-text { font-size: 0.85rem; font-weight: 700; }
    .txt-green { color: #047857; }
    .txt-yellow { color: #d97706; }

    /* --- 4. O TICKET GERADO (NOVO!) --- */
    .ticket-container {
        background-color: #fff;
        border: 2px dashed #cbd5e1;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        margin-top: 10px;
        position: relative;
    }
    .ticket-header {
        font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; color: #64748b; margin-bottom: 10px;
    }
    .ticket-balls {
        display: flex; flex-wrap: wrap; gap: 8px; justify-content: center;
    }
    .ball-ticket {
        width: 40px; height: 40px;
        color: white; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-weight: 800; font-size: 1.1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
</style>
"""

def get_cores(nome_loteria):
    """Define as cores baseadas na marca da loteria"""
    nome = nome_loteria.lower()
    if "lotof" in nome: # Lotofácil (Roxo)
        return "#9d174d", "linear-gradient(135deg, #d946ef, #c026d3)"
    elif "quina" in nome: # Quina (Azul Escuro/Roxo)
        return "#4338ca", "linear-gradient(135deg, #6366f1, #4338ca)"
    elif "mega" in nome: # Mega (Verde/Azul)
        return "#1e3a8a", "linear-gradient(135deg, #3b82f6, #2563eb)"
    else: # Padrão
        return "#374151", "linear-gradient(135deg, #6b7280, #4b5563)"

def gerar_html_card(nome_loteria, motor):
    """Gera o Card do Dashboard"""
    txt_sinal, tipo_sinal = motor.analisar_sinal()
    cor_texto, gradiente_bola = get_cores(nome_loteria)

    try:
        if motor.df is not None and not motor.df.empty:
            last = motor.df.iloc[0]
            concurso = last.get('Concurso', '--')
            numeros = []
            for c in motor.cols:
                val = last.get(c)
                try: 
                    if val and str(val).strip(): numeros.append(int(float(val)))
                except: pass
        else:
            numeros = []; concurso = "--"
    except: numeros = []; concurso = "Erro"

    # HTML Components
    if "ACUMULADO" in txt_sinal or "ACUMULOU" in txt_sinal:
        badge = '<span class="status-badge bg-acumulado">Acumulou! 💰</span>'
    else:
        badge = '<span class="status-badge bg-normal">Normal</span>'

    classe_luz = "dot-green" if tipo_sinal == "go" else "dot-yellow"
    classe_txt = "txt-green" if tipo_sinal == "go" else "txt-yellow"

    html_bolas = "".join([f'<div class="ball-dash" style="background:{gradiente_bola}">{n}</div>' for n in numeros])

    return f"""
    <div class="card-loteria" style="border-top: 4px solid {cor_texto}">
        <div class="card-header">
            <div>
                <div class="card-title" style="color:{cor_texto}">{nome_loteria}</div>
                <div class="card-conc">Conc. {concurso}</div>
            </div>
            {badge}
        </div>
        <div class="balls-container">{html_bolas}</div>
        <div class="card-footer">
            <div class="dot {classe_luz}"></div>
            <div class="footer-text {classe_txt}">{txt_sinal}</div>
        </div>
    </div>
    """

def gerar_ticket_visual(nome_loteria, numeros):
    """
    NOVO: Gera um visual de 'Bilhete Impresso' para o palpite gerado.
    """
    cor_texto, gradiente_bola = get_cores(nome_loteria)
    
    html_bolas = "".join([f'<div class="ball-ticket" style="background:{gradiente_bola}">{int(n)}</div>' for n in numeros])
    
    return f"""
    <div class="ticket-container">
        <div class="ticket-header">Palpite Gerado • {nome_loteria}</div>
        <div class="ticket-balls">
            {html_bolas}
        </div>
        <div style="margin-top:10px; font-size:0.7rem; color:#94a3b8;">
            Estratégia Matemática Aplicada
        </div>
    </div>
    """
