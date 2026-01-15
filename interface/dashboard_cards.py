import pandas as pd

# --- CSS INTELIGENTE (ADAPTÁVEL) ---
CSS_ESTILO = """
<style>
    /* --- ESTRUTURA BASE DO CARD --- */
    .card-loteria {
        background-color: #ffffff;
        border-radius: 16px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid #f0f2f5;
        transition: all 0.3s ease;
        position: relative;
    }
    .card-loteria:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.08);
    }

    /* --- CABEÇALHO --- */
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 15px;
        border-bottom: 1px solid #f0f2f5;
        padding-bottom: 10px;
    }
    .card-title {
        font-size: 1.1rem;
        font-weight: 800;
        color: #374151;
        margin: 0;
    }
    .card-conc {
        font-size: 0.75rem;
        color: #9ca3af;
        margin-top: 2px;
    }

    /* --- BADGES (Etiquetas) --- */
    .status-badge {
        font-size: 0.65rem;
        padding: 3px 8px;
        border-radius: 12px;
        font-weight: 700;
        text-transform: uppercase;
        display: inline-block;
    }
    .bg-acumulado { background-color: #fffbeb; color: #b45309; border: 1px solid #fcd34d; }
    .bg-normal { background-color: #f3f4f6; color: #9ca3af; }

    /* --- BOLAS (Design Adaptativo) --- */
    .balls-container {
        display: flex;
        flex-wrap: wrap;
        gap: 6px; /* Espaço entre as bolas */
        justify-content: center; /* Centraliza as bolas */
        margin: 15px 0;
    }

    /* Estilo Padrão (Mega Sena, Quina - Azul) */
    .ball-standard {
        width: 34px;
        height: 34px;
        background: linear-gradient(135deg, #3b82f6, #2563eb);
        color: white;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 0.9rem;
        box-shadow: 0 2px 5px rgba(37, 99, 235, 0.25);
    }

    /* Estilo Compacto (Lotofácil - Roxo) */
    .ball-loto {
        width: 28px; /* Menor para caber 15 */
        height: 28px;
        background: linear-gradient(135deg, #d946ef, #c026d3); /* Gradiente Roxo */
        color: white;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 0.8rem; /* Fonte menor */
        box-shadow: 0 2px 4px rgba(192, 38, 211, 0.25);
    }

    /* --- RODAPÉ (Sinal do Motor) --- */
    .card-footer {
        background-color: #f9fafb;
        margin: -20px -20px -20px -20px; /* Expande para as bordas */
        padding: 12px 20px;
        margin-top: 15px;
        border-radius: 0 0 16px 16px;
        display: flex; align-items: center; gap: 8px;
    }
    .dot { width: 10px; height: 10px; border-radius: 50%; }
    .dot-green { background-color: #10b981; box-shadow: 0 0 8px #10b981; }
    .dot-yellow { background-color: #f59e0b; }
    
    .footer-text { font-size: 0.85rem; font-weight: 700; }
    .txt-green { color: #047857; }
    .txt-yellow { color: #d97706; }
</style>
"""

def gerar_html_card(nome_loteria, motor):
    """
    Gera o HTML do card, adaptando o estilo se for Lotofácil ou Mega Sena.
    """
    # 1. Obter dados do Motor
    txt_sinal, tipo_sinal = motor.analisar_sinal()
    
    try:
        # Tenta ler a última linha com segurança
        if motor.df is not None and not motor.df.empty:
            last = motor.df.iloc[0]
            concurso = last.get('Concurso', '---')
            
            # Extrai números
            numeros = []
            for c in motor.cols:
                val = last.get(c)
                try: 
                    if val and str(val).strip():
                        numeros.append(int(float(val)))
                except: pass
        else:
            numeros = []
            concurso = "--"
    except:
        numeros = []
        concurso = "Erro"

    # 2. DEFINIR IDENTIDADE VISUAL (A Mágica acontece aqui)
    nome_limpo = nome_loteria.lower()
    
    if "lotof" in nome_limpo: # Detecta Lotofácil
        classe_bola = "ball-loto" # Usa a bola roxa e pequena
        cor_titulo = "#9d174d" # Um tom de vinho/roxo escuro para o título
    else:
        classe_bola = "ball-standard" # Usa a bola azul padrão
        cor_titulo = "#1e3a8a" # Azul escuro

    # 3. Lógica de Status (Acumulado)
    if "ACUMULADO" in txt_sinal or "ACUMULOU" in txt_sinal:
        badge = '<span class="status-badge bg-acumulado">Acumulou! 💰</span>'
    else:
        badge = '<span class="status-badge bg-normal">Normal</span>'

    # 4. Lógica do Sinal (Semáforo)
    classe_luz = "dot-green" if tipo_sinal == "go" else "dot-yellow"
    classe_txt = "txt-green" if tipo_sinal == "go" else "txt-yellow"

    # Gera HTML das bolas
    html_bolas = "".join([f'<div class="{classe_bola}">{n}</div>' for n in numeros])

    # 5. Retorna o HTML Montado
    return f"""
    <div class="card-loteria" style="border-top: 4px solid {cor_titulo}">
        <div class="card-header">
            <div>
                <div class="card-title" style="color:{cor_titulo}">{nome_loteria}</div>
                <div class="card-conc">Conc. {concurso}</div>
            </div>
            {badge}
        </div>
        
        <div class="balls-container">
            {html_bolas}
        </div>
        
        <div class="card-footer">
            <div class="dot {classe_luz}"></div>
            <div class="footer-text {classe_txt}">
                {txt_sinal}
            </div>
        </div>
    </div>
    """
    
