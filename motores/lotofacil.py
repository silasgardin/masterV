from motores.base import MotorBase
import numpy as np
import pandas as pd

class MotorLotofacil(MotorBase):
    def gerar_palpite(self, estrategia):
        # Na Lotofácil, a estratégia Mestre foca em repetir o padrão do último sorteio
        
        # 1. Pegar números do último concurso
        ultimos_nums = self.df.iloc[0][self.cols_bolas].dropna().astype(int).tolist()
        
        # 2. Definir quantos repetir (estatística diz que 9 é o mais comum)
        qtd_repetir = 9 
        
        # 3. Números que NÃO saíram no último (Ausentes)
        todos = set(range(1, 26))
        ausentes = list(todos - set(ultimos_nums))
        
        # Gerar Jogo
        repetidos = np.random.choice(ultimos_nums, qtd_repetir, replace=False)
        novos = np.random.choice(ausentes, 15 - qtd_repetir, replace=False)
        
        jogo = np.concatenate((repetidos, novos))
        return sorted(jogo)
