st.markdown("""
<style>
    /* Container do Card */
    .card-loteria {
        background-color: #ffffff;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid #f0f2f6;
        transition: transform 0.2s;
    }
    .card-loteria:hover {
        transform: translateY(-5px);
        border-color: #3b82f6;
    }

    /* Cabeçalho */
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
    }
    .card-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1f2937;
        margin: 0;
    }
    
    /* Badge de Status (Acumulado) */
    .badge {
        font-size: 0.75rem;
        padding: 4px 8px;
        border-radius: 12px;
        font-weight: 600;
        text-transform: uppercase;
    }
    .badge-acumulado { background-color: #fef3c7; color: #d97706; border: 1px solid #fcd34d; }
    .badge-normal { background-color: #f3f4f6; color: #6b7280; }

    /* As Bolas do Sorteio */
    .ball-container {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        justify-content: center;
        margin: 15px 0;
    }
    .ball {
        width: 32px;
        height: 32px;
        background: linear-gradient(135deg, #3b82f6, #2563eb);
        color: white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 0.9rem;
        box-shadow: 0 2px 4px rgba(37, 99, 235, 0.3);
    }

    /* Rodapé com o Sinal do Motor */
    .card-footer {
        margin-top: 15px;
        padding-top: 10px;
        border-top: 1px solid #e5e7eb;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .signal-indicator {
        width: 12px;
        height: 12px;
        border-radius: 50%;
    }
    .signal-green { background-color: #10b981; box-shadow: 0 0 8px #10b981; }
    .signal-yellow { background-color: #f59e0b; }
    
    .signal-text {
        font-size: 0.9rem;
        font-weight: 700;
    }
    .text-green { color: #059669; }
    .text-yellow { color: #d97706; }
</style>
""", unsafe_allow_html=True)
