import pandas as pd

# --- CSS DO SUPER CARD (Visual de Investimento) ---
CSS_ESTILO = """
<style>
    /* Reset Básico */
    .block-container { padding-top: 1rem !important; }
    #MainMenu, footer, header { visibility: hidden; }

    /* --- ESTRUTURA DO CARD --- */
    .card-loteria {
        background: #ffffff;
        border-radius: 16px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02), 0 10px 15px rgba(0,0,0,0.03);
        border: 1px solid #e2e8f0;
        margin-bottom: 24px;
        overflow: hidden; /* Mantém tudo dentro das bordas arredondadas */
        display: flex;
        flex-direction: column;
        height: 100%;
        transition: transform 0.2s;
    }
    .card-loteria:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        border-color: #cbd5e1;
    }

    /* --- 1. CABEÇALHO (Nome e Concurso) --- */
    .card-header {
        padding: 12px 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #f8fafc;
        border-bottom: 1px solid #e2e8f0;
    }
    .loteria-title {
        font-size: 0.95rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .next-draw {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.7rem;
        color: #64748b;
        font-weight: 600;
    }

    /* --- 2. ÁREA DE VALOR (O Grande Destaque) --- */
    .prize-section {
        padding: 20px 16px 10px 16px;
        text-align: center;
    }
    .prize-label {
        font-size: 0.7rem;
        text-transform: uppercase;
        color: #94a3b8;
        letter-spacing: 1px;
        margin-bottom: 4px;
    }
    .prize-value {
        font-size: 1.8rem;
        font-weight: 900;
        color: #1e293b;
        line-height: 1;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    .status-badge {
        display: inline-block;
        margin-top: 8px;
        font-size: 0.65rem;
        font-weight: 800;
        padding: 4px 10px;
        border-radius: 20px;
        text-transform: uppercase;
    }
    .bg-acumulado { background: #fff7ed; color: #ea580c; border: 1px solid #fdba74; }
    .bg-normal { background: #f1f5f9; color: #64748b; }

    /* --- 3. ÚLTIMO RESULTADO (Bolas) --- */
    .last-result-section {
        padding: 10px 16px;
        text-align: center;
        flex-grow: 1; /* Empurra o rodapé para baixo */
    }
    .last-conc-info { font-size: 0.7rem; color: #cbd5e1; margin-bottom: 8px; }
    .balls-grid {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 5px;
    }
    .ball-style {
        width: 30px; height: 30px;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        color: #475569;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 0.85rem;
    }
    /* Estilo para Lotofácil (menor) */
    .ball-mini { width: 26px; height: 26px; font-size: 0.75rem; }

    /* --- 4. RODAPÉ DE INTELIGÊNCIA (O Motor) --- */
    .ai-footer {
        padding: 12px 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-top: 1px solid #e2e8f0;
    }
    
    /* Cores do Sinal */
    .signal-go { background: #ecfdf5; border-top: 2px solid #10b981; }
    .signal-wait { background: #fffbeb; border-top: 2px solid #f59e0b; }

    .ai-text {
        font-size: 0.8rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .txt-go { color: #047857; }
    .txt-wait { color: #b45309; }

    .traffic-light {
        width: 12px; height: 12px; border-radius: 50%;
        box-shadow: 0 0 0 2px rgba(255,255,255,0.8);
    }
    .light-green { background: #10b981; animation: pulse-green 2s infinite; }
    .light-yellow { background: #f59e0b; }

    /* Animação de Pulso */
    @keyframes pulse-green {
        0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
        100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
    
    /* Ticket */
    .ticket-container {
        background: #fff; border: 2px dashed #cbd5e1; border-radius: 12px;
        padding: 20px; text-align: center; margin-top: 10px;
    }
    .ball-ticket {
        width: 38px; height: 38px; color: white; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-weight: 800; font-size: 1.1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
</style>
"""

# --- AUXILIARES ---
def get_brand_color(nome):
    n = nome.lower()
    if "mega" in n: return "#1e40af" # Azul
    if "loto" in n: return "#9d174d" # Roxo
    if "quina" in n: return "#4338ca" # Índigo
    if "dupla" in n: return "#be123c" # Vermelho
    return "#334155" # Cinza

def formatar_moeda(valor):
    """
    Formata qualquer número ou texto de dinheiro para o padrão R$ X.XXX.XXX
    """
    try:
        # Limpa o texto (tira R$, espaços, pontos)
        v_clean = str(valor).replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
        v_float = float(v_clean)
        
        # Formata para padrão brasileiro
        if v_float > 1000000:
            # Se for milhões, arredonda para facilitar leitura
            return f"R$ {v_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        else:
            return f"R$ {v_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ ---"

# --- GERADOR HTML ---
def gerar_html_card(nome_loteria, motor):
    """
    Gera o Card Completo com Valor, Status e Sinal
    """
    cor_marca = get_brand_color(nome_loteria)
    
    # 1. Analisar Sinal do Motor
    txt_sinal, tipo_sinal = motor.analisar_sinal()
    
    # 2. Extração de Dados (Com fallback seguro)
    concurso_atual = "--"
    prox_conc = "--"
    premio_txt = "Apurando..."
    numeros = []
    
    if motor.df is not None and not motor.df.empty:
        try:
            last = motor.df.iloc[0]
            concurso_atual = str(last.get('Concurso', '--'))
            
            # Tenta calcular próximo concurso
            if concurso_atual.isdigit():
                prox_conc = str(int(concurso_atual) + 1)
            
            # --- LÓGICA DE CAÇA AO TESOURO (Busca o Prêmio) ---
            # Lista de possíveis nomes de coluna na planilha
            colunas_possiveis = [
                'Estimativa Próximo', 'Prêmio Estimado', 
                'Valor Acumulado', 'Acumulado', 'Prêmio'
            ]
            
            for col in colunas_possiveis:
                # Procura ignorando maiúsculas/minúsculas
                col_real = next((c for c in motor.df.columns if c.lower() == col.lower()), None)
                if col_real:
                    val = str(last.get(col_real, '0'))
                    # Só aceita se não for zero ou vazio
                    if val.strip() not in ['0', '0,00', '', '0.00']:
                        premio_txt = formatar_moeda(val)
                        break
            
            # Números sorteados
            for c in motor.cols:
                val = last.get(c)
                try: 
                    if val and str(val).strip(): numeros.append(int(float(val)))
                except: pass
        except: pass

    # 3. Definição Visual Baseada em Status
    is_acumulado = "ACUMULA" in txt_sinal or "ACUMULO" in str(motor.df.iloc[0].values).upper() if motor.df is not None else False
    
    if is_acumulado:
        badge_html = '<div class="status-badge bg-acumulado">ACUMULOU!</div>'
        if premio_txt == "R$ ---" or premio_txt == "Apurando...": 
            premio_txt = "PRÊMIO ALTO" # Fallback se não achar valor
    else:
        badge_html = '<div class="status-badge bg-normal">SORTEIO REALIZADO</div>'

    # 4. Definição Visual do Rodapé (Sinal)
    if tipo_sinal == "go":
        footer_class = "signal-go"
        txt_class = "txt-go"
        light_class = "light-green"
        icon = "🚀" # Foguete para entrada
    else:
        footer_class = "signal-wait"
        txt_class = "txt-wait"
        light_class = "light-yellow"
        icon = "✋" # Mão para espera

    # Ajuste bolas (menores para Loto/Mania)
    css_bola = "ball-mini" if len(numeros) > 10 else "ball-style"
    
    html_bolas = "".join([f'<div class="{css_bola}">{n}</div>' for n in numeros])

    # 5. MONTAGEM FINAL
    return f"""
    <div class="card-loteria">
        <div class="card-header">
            <div class="loteria-title" style="color: {cor_marca}">{nome_loteria}</div>
            <div class="next-draw">Próx: {prox_conc}</div>
        </div>

        <div class="prize-section">
            <div class="prize-label">Estimativa de Prêmio</div>
            <div class="prize-value" style="color: {cor_marca}">{premio_txt}</div>
            {badge_html}
        </div>

        <div class="last-result-section">
            <div class="last-conc-info">Último: {concurso_atual}</div>
            <div class="balls-grid">
                {html_bolas}
            </div>
        </div>

        <div class="ai-footer {footer_class}">
            <div class="ai-text {txt_class}">
                <div class="traffic-light {light_class}"></div>
                {icon} {txt_sinal}
            </div>
            <div style="font-size:0.7rem; color:#94a3b8; font-weight:600;">MOTOR V.1</div>
        </div>
    </div>
    """

def gerar_ticket_visual(nome_loteria, numeros):
    cor = get_brand_color(nome_loteria)
    html_bolas = "".join([f'<div class="ball-ticket" style="background:{cor}">{int(n)}</div>' for n in numeros])
    return f"""
    <div class="ticket-container">
        <div style="text-transform:uppercase; color:#94a3b8; font-size:0.8rem; margin-bottom:10px">
            Palpite Gerado • {nome_loteria}
        </div>
        <div style="display:flex; flex-wrap:wrap; gap:8px; justify-content:center;">
            {html_bolas}
        </div>
    </div>
    """
