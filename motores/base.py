import pandas as pd
import numpy as np

class MotorBase:
    def __init__(self, df, config):
        self.df = df
        self.config = config
        self.cols = []

        # BLINDAGEM: Só tenta ler colunas se df existir
        if self.df is not None and not self.df.empty:
            # Detecta colunas D1, D2... ignorando 'Data'
            self.cols = [c for c in df.columns if c.startswith('D') and any(char.isdigit() for char in c) and 'Data' not in c]

    def analisar_sinal(self):
        """Gera o sinal visual para o Dashboard"""
        # Se não tem dados, retorna Neutro sem quebrar
        if self.df is None or self.df.empty: 
            return "⚪ Sem Dados", "neutral"
        
        try:
            last_row = self.df.iloc[0]
            status = str(last_row.get('Status / Premiação', '')).upper()
            
            if "ACUMULOU" in status or "ACUMULADO" in status:
                return "💰 ACUMULADO", "go"
            
            nums = [float(last_row[c]) for c in self.cols if pd.notnull(last_row[c])]
            if not nums: return "⚪ Erro Leitura", "neutral"
            
            media_esperada = (self.config['max_dezenas'] * self.config['tamanho_jogo']) / 2
            soma = sum(nums)
            desvio = abs(soma - media_esperada)
            
            if desvio > (media_esperada * 0.4):
                return "🟢 CORREÇÃO PROVÁVEL", "go"
                
            return "🟡 NEUTRO", "wait"
        except Exception:
            return "⚠️ Erro Dados", "neutral"

    def get_stats(self):
        if self.df is None or self.df.empty:
            return {"quentes": [], "frios": []}

        todos = self.df[self.cols].values.flatten()
        todos = todos[~np.isnan(todos)]
        contagem = pd.Series(todos).value_counts().reindex(range(1, self.config['max_dezenas']+1), fill_value=0)
        corte = self.config['max_dezenas'] // 3
        return {
            "quentes": contagem.sort_values(ascending=False).index[:corte].tolist(),
            "frios": contagem.sort_values(ascending=True).index[:corte].tolist()
        }

    def gerar_palpite(self, estrategia):
        stats = self.get_stats()
        # Se não tem estatística (base vazia), gera aleatório puro
        if not stats['quentes']:
            pool = range(1, self.config['max_dezenas']+1)
            jogo = np.random.choice(pool, self.config['tamanho_jogo'], replace=False)
            return sorted(jogo)

        pool = []
        if estrategia == "Tendência": pool = stats['quentes']
        elif estrategia == "Equilíbrio": pool = stats['frios'] + list(set(range(1, self.config['max_dezenas']+1)) - set(stats['quentes']))
        else: pool = stats['quentes'] + stats['frios']
        
        if len(pool) < self.config['tamanho_jogo']: pool = range(1, self.config['max_dezenas']+1)
        
        jogo = np.random.choice(pool, self.config['tamanho_jogo'], replace=False)
        return sorted(jogo)
