import pandas as pd

# --- CSS DO DASHBOARD (Design Claro) ---
CSS_ESTILO = """
<style>
    /* Container do Card */
    .card-loteria {
        background-color: #ffffff;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05); /* Sombra suave */
        padding: 24px;
        margin-bottom: 24px;
        border: 1px solid #f3f4f6;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    .card-loteria:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(59, 130, 246, 0.15);
        border-color: #bfdbfe;
    }

    /* Cabeçalho */
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 20px;
    }
    .card-title {
        font-size: 1.25rem;
        font-weight: 800;
        color: #111827; /* Cinza quase preto */
        margin: 0;
    }
    .card-conc {
        font-size: 0.85rem;
        color: #9ca3af;
        font-weight: 500;
    }
    
    /* Badge de Status */
    .status-badge {
        font-size: 0.7rem;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-acumulado { 
        background-color: #fffbeb; 
        color: #b45309; 
        border: 1px solid #fcd34d; 
    }
    .badge-normal { 
        background-color: #f9fafb; 
        color: #6b7280; 
        border: 1px solid #e5e7eb; 
    }

    /* Bolas */
    .balls-row {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 20px;
    }
    .ball-style {
        width: 36px;
        height: 36px;
        background: linear-gradient(145deg, #3b82f6, #2563eb);
        color: white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.95rem;
        box-shadow: 2px 2px 5px rgba(37, 99, 235, 0.2);
    }

    /* Rodapé com Ação */
    .card-action {
        background-color: #f8fafc;
        border-radius: 12px;
        padding: 12px;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .traffic-light {
        width: 14px;
        height: 14px;
        border-radius: 50%;
        flex-shrink: 0;
    }
    .light-go { background-color: #10b981; box-shadow: 0 0 10px rgba(16, 185, 129, 0.4); }
    .light-wait { background-color: #f59e0b; }
    
    .action-text {
        font-size: 0.9rem;
        font-weight: 700;
        line-height: 1.2;
    }
    .txt-go { color: #047857; }
    .txt-wait { color: #b45309; }
</style>
"""

def gerar_html_card(nome_loteria, motor):
    """
    Recebe o Motor Matemático (já carregado com dados) e retorna o HTML do card.
    """
    # 1. Extração de Dados do Motor
    txt_sinal, tipo_sinal = motor.analisar_sinal()
    
    try:
        if motor.df is not None and not motor.df.empty:
            last = motor.df.iloc[0]
            # Extrai números e converte para inteiro
            numeros = []
            for c in motor.cols:
                val = last.get(c)
                try: numeros.append(int(float(val)))
                except: pass
            
            concurso = last.get('Concurso', '---')
        else:
            numeros = []
            concurso = "---"
    except:
        numeros = []
        concurso = "Erro"

    # 2. Definição de Estilos Condicionais
    if "ACUMULADO" in txt_sinal or "ACUMULOU" in txt_sinal:
        badge_html = '<span class="status-badge badge-acumulado">Acumulou!</span>'
    else:
        badge_html = '<span class="status-badge badge-normal">Normal</span>'

    cor_luz = "light-go" if tipo_sinal == "go" else "light-wait"
    cor_texto = "txt-go" if tipo_sinal == "go" else "txt-wait"

    # Gera o HTML das bolinhas
    bolas_html = "".join([f'<div class="ball-style">{n}</div>' for n in numeros])

    # 3. Montagem do Bloco HTML
    return f"""
    <div class="card-loteria">
        <div class="card-header">
            <div>
                <h3 class="card-title">{nome_loteria}</h3>
                <div class="card-conc">Conc. {concurso}</div>
            </div>
            {badge_html}
        </div>
        
        <div class="balls-row">
            {bolas_html}
        </div>
        
        <div class="card-action">
            <div class="traffic-light {cor_luz}"></div>
            <div class="action-text {cor_texto}">
                {txt_sinal}
            </div>
        </div>
    </div>
    """
