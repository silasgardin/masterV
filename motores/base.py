import pandas as pd
import numpy as np

class MotorBase:
    def __init__(self, df, config):
        self.df = df
        self.config = config
        self.cols_bolas = [c for c in df.columns if c.startswith('D') and c[1].isdigit()]

    def get_stats(self):
        """Estatística Básica (Comum a todos)"""
        todos_numeros = self.df[self.cols_bolas].values.flatten()
        todos_numeros = todos_numeros[~np.isnan(todos_numeros)]
        
        contagem = pd.Series(todos_numeros).value_counts().reindex(range(1, self.config['max_dezenas'] + 1), fill_value=0)
        
        corte = self.config['max_dezenas'] // 3
        return {
            "quentes": contagem.sort_values(ascending=False).index[:corte].tolist(),
            "frios": contagem.sort_values(ascending=True).index[:corte].tolist(),
            "frequencia": contagem
        }

    def gerar_palpite(self, estrategia="Equilíbrio"):
        """Gerador Genérico (Caso o jogo não tenha um específico)"""
        stats = self.get_stats()
        pool = []
        
        if "Tendência" in estrategia:
            pool = stats['quentes']
        else:
            pool = list(set(stats['quentes'] + stats['frios']))
            
        # Garante tamanho mínimo
        if len(pool) < self.config['tamanho_jogo']:
            pool = range(1, self.config['max_dezenas'] + 1)
            
        jogo = np.random.choice(pool, self.config['tamanho_jogo'], replace=False)
        return sorted(jogo)
