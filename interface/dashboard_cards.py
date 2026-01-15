import pandas as pd
import textwrap # Importante para limpar a indentação

# --- CSS DO SUPER CARD ---
CSS_ESTILO = """
<style>
    /* Reset e Ajustes Gerais */
    .block-container { padding-top: 1rem !important; }
    #MainMenu, footer, header { visibility: hidden; }

    /* Card Principal */
    .card-loteria {
        background: #ffffff;
        border-radius: 16px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
        margin-bottom: 24px;
        display: flex;
        flex-direction: column;
        height: 100%;
        transition: transform 0.2s;
        overflow: hidden;
    }
    .card-loteria:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 20px rgba(0,0,0,0.1);
        border-color: #cbd5e1;
    }

    /* Topo */
    .card-header {
        padding: 12px 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #f8fafc;
        border-bottom: 1px solid #e2e8f0;
    }
    .loteria-title { font-size: 0.9rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; }
    .next-draw { background: #fff; border: 1px solid #cbd5e1; padding: 2px 8px; border-radius: 6px; font-size: 0.7rem; color: #64748b; font-weight: 600; }

    /* Área de Valor */
    .prize-section { padding: 20px 16px 10px; text-align: center; }
    .prize-label { font-size: 0.7rem; text-transform: uppercase; color: #94a3b8; letter-spacing: 1px; margin-bottom: 4px; }
    .prize-value { font-size: 1.6rem; font-weight: 900; color: #1e293b; line-height: 1; }
    
    /* Badges */
    .status-badge { display: inline-block; margin-top: 8px; font-size: 0.65rem; font-weight: 800; padding: 4px 10px; border-radius: 20px; text-transform: uppercase; }
    .bg-acumulado { background: #fff7ed; color: #ea580c; border: 1px solid #fdba74; }
    .bg-normal { background: #f1f5f9; color: #64748b; }

    /* Resultados */
    .last-result-section { padding: 10px 16px; text-align: center; flex-grow: 1; }
    .last-conc-info { font-size: 0.7rem; color: #cbd5e1; margin-bottom: 8px; }
    .balls-grid { display: flex; flex-wrap: wrap; justify-content: center; gap: 5px; }
    .ball-style { width: 30px; height: 30px; background: #f8fafc; border: 1px solid #e2e8f0; color: #475569; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.85rem; }
    .ball-mini { width: 26px; height: 26px; font-size: 0.75rem; }

    /* Rodapé IA */
    .ai-footer { padding: 12px 16px; display: flex; align-items: center; justify-content: space-between; border-top: 1px solid #e2e8f0; }
    .signal-go { background: #ecfdf5; border-top: 2px solid #10b981; }
    .signal-wait { background: #fffbeb; border-top: 2px solid #f59e0b; }
    .ai-text { font-size: 0.8rem; font-weight: 700; display: flex; align-items: center; gap: 8px; }
    .txt-go { color: #047857; } .txt-wait { color: #b45309; }
    
    .traffic-light { width: 12px; height: 12px; border-radius: 50%; }
    .light-green { background: #10b981; animation: pulse 2s infinite; }
    .light-yellow { background: #f59e0b; }
    
    @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); } 70% { box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); } 100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); } }

    /* Ticket */
    .ticket-container { background: #fff; border: 2px dashed #cbd5e1; border-radius: 12px; padding: 20px; text-align: center; margin-top: 10px; }
    .ball-ticket { width: 38px; height: 38px; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1.1rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
</style>
"""

def get_brand_color(nome):
    n = nome.lower()
    if "mega" in n: return "#1e40af"
    if "loto" in n: return "#9d174d"
    if "quina" in n: return "#4338ca"
    if "dupla" in n: return "#be123c"
    return "#334155"

def formatar_moeda(valor):
    try:
        v_str = str(valor).replace("R$", "").replace(".", "").replace(",", ".")
        return f"R$ {float(v_str):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except: return "R$ ---"

def gerar_html_card(nome_loteria, motor):
    cor_marca = get_brand_color(nome_loteria)
    txt_sinal, tipo_sinal = motor.analisar_sinal()
    
    # Extração de dados
    concurso, prox, premio, numeros = "--", "--", "Apurando...", []
    try:
        if motor.df is not None and not motor.df.empty:
            last = motor.df.iloc[0]
            concurso = str(last.get('Concurso', '--'))
            if concurso.isdigit(): prox = str(int(concurso) + 1)
            
            # Busca prêmio
            cols_premio = ['Estimativa Próximo', 'Prêmio Estimado', 'Valor Acumulado', 'Acumulado']
            for c in cols_premio:
                real_c = next((x for x in motor.df.columns if x.lower() == c.lower()), None)
                if real_c and str(last.get(real_c)).strip() not in ['0', '', '0,00']:
                    premio = formatar_moeda(last.get(real_c))
                    break
            
            for c in motor.cols:
                v = last.get(c)
                if v: numeros.append(int(float(v)))
    except: pass

    # Lógica Visual
    is_acumulado = "ACUMULADO" in txt_sinal
    badge = '<div class="status-badge bg-acumulado">ACUMULOU!</div>' if is_acumulado else '<div class="status-badge bg-normal">NORMAL</div>'
    if is_acumulado and premio in ["R$ ---", "Apurando..."]: premio = "PRÊMIO ALTO"

    ft_cls, txt_cls, l_cls, icon = ("signal-go", "txt-go", "light-green", "🚀") if tipo_sinal == "go" else ("signal-wait", "txt-wait", "light-yellow", "✋")
    
    css_bola = "ball-mini" if len(numeros) > 10 else "ball-style"
    html_bolas = "".join([f'<div class="{css_bola}">{n}</div>' for n in numeros])

    # AQUI ESTÁ A CORREÇÃO: Usamos dedent para remover espaços à esquerda
    html_template = f"""
    <div class="card-loteria">
        <div class="card-header">
            <div class="loteria-title" style="color: {cor_marca}">{nome_loteria}</div>
            <div class="next-draw">Próx: {prox}</div>
        </div>
        <div class="prize-section">
            <div class="prize-label">Estimativa de Prêmio</div>
            <div class="prize-value" style="color: {cor_marca}">{premio}</div>
            {badge}
        </div>
        <div class="last-result-section">
            <div class="last-conc-info">Último: {concurso}</div>
            <div class="balls-grid">
                {html_bolas}
            </div>
        </div>
        <div class="ai-footer {ft_cls}">
            <div class="ai-text {txt_cls}">
                <div class="traffic-light {l_cls}"></div>
                {icon} {txt_sinal}
            </div>
            <div style="font-size:0.7rem; color:#94a3b8;">MOTOR V.1</div>
        </div>
    </div>
    """
    
    # Remove a indentação para o Streamlit não achar que é código
    return textwrap.dedent(html_template)

def gerar_ticket_visual(nome_loteria, numeros):
    cor = get_brand_color(nome_loteria)
    html_bolas = "".join([f'<div class="ball-ticket" style="background:{cor}">{int(n)}</div>' for n in numeros])
    
    html = f"""
    <div class="ticket-container">
        <div style="text-transform:uppercase; color:#94a3b8; font-size:0.8rem; margin-bottom:10px">
            Palpite Gerado • {nome_loteria}
        </div>
        <div style="display:flex; flex-wrap:wrap; gap:8px; justify-content:center;">
            {html_bolas}
        </div>
    </div>
    """
    return textwrap.dedent(html)
