from .base import MotorBase
import numpy as np
import pandas as pd

class MotorLotofacil(MotorBase):
    def gerar_palpite(self, estrategia):
        """
        Gera palpites específicos para Lotofácil baseados em repetição.
        Estratégia comum: Repetir 9 do anterior e pegar 6 ausentes.
        """
        
        # 1. SEGURANÇA: Se a base estiver vazia, usa o gerador aleatório do pai
        if self.df is None or self.df.empty:
            return super().gerar_palpite(estrategia)

        # 2. OBTER NÚMEROS DO ÚLTIMO CONCURSO (Com tratamento de erro)
        try:
            # Pega a primeira linha e apenas as colunas de dezenas (self.cols)
            # CORREÇÃO: Usamos self.cols (nome correto) em vez de self.cols_bolas
            linha_crua = self.df.iloc[0][self.cols]
            
            # Converte para números (força limpeza de strings)
            ultimos_nums = pd.to_numeric(linha_crua, errors='coerce').dropna().astype(int).tolist()
            
            # Se por algum motivo a leitura falhar (ex: planilha vazia), fallback
            if len(ultimos_nums) < 15:
                return super().gerar_palpite(estrategia)
                
        except Exception:
            return super().gerar_palpite(estrategia)

        # 3. LÓGICA DA LOTOFÁCIL (Padrão de Repetição)
        # A estatística diz que o mais comum é repetir 9 dezenas do concurso anterior.
        
        qtd_repetir = 9
        
        # Define o universo de bolas (1 a 25)
        todos_numeros = set(range(1, 26))
        
        # Define quem saiu (presentes) e quem não saiu (ausentes)
        presentes = set(ultimos_nums)
        ausentes = list(todos_numeros - presentes)
        presentes = list(presentes)
        
        # Estratégia MESTRE: Tenta seguir o padrão matemático de 9 repetidas
        if estrategia == "Mestre" or estrategia == "Equilíbrio":
            try:
                # Escolhe 9 dos que saíram
                p1 = np.random.choice(presentes, qtd_repetir, replace=False)
                # Escolhe 6 dos que NÃO saíram (15 - 9 = 6)
                p2 = np.random.choice(ausentes, 15 - qtd_repetir, replace=False)
                
                jogo = np.concatenate((p1, p2))
                return sorted(jogo)
            except ValueError:
                # Se não tiver números suficientes (ex: dados ruins), usa o pai
                return super().gerar_palpite(estrategia)
        
        # Estratégia TENDÊNCIA: Foca nos quentes (usa lógica do pai, mas ajustada)
        else:
            return super().gerar_palpite(estrategia)
