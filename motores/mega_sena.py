from motores.base import MotorBase
import numpy as np

class MotorMegaSena(MotorBase):
    def gerar_palpite(self, estrategia):
        # 1. Pega a lógica básica do pai
        stats = self.get_stats()
        max_n = self.config['max_dezenas']
        size = self.config['tamanho_jogo']
        
        # 2. APLICAR LÓGICA EXCLUSIVA DA MEGA SENA
        # Exemplo: Filtrar para garantir equilíbrio de Quadrantes
        
        tentativas = 0
        while tentativas < 1000:
            # Gera um candidato usando lógica básica
            pool = stats['quentes'] + stats['frios']
            if len(pool) < size: pool = range(1, max_n + 1)
            
            candidato = np.random.choice(pool, size, replace=False)
            candidato.sort()
            
            # FILTRO 1: Não permitir mais que 2 números seguidos (ex: 10, 11, 12)
            if self._tem_sequencia(candidato):
                tentativas += 1
                continue
                
            # FILTRO 2: Soma das dezenas (entre 140 e 240 é o padrão da Mega)
            soma = sum(candidato)
            if not (140 <= soma <= 240):
                tentativas += 1
                continue
                
            return candidato
            
        # Se falhar muito, retorna um aleatório simples
        return sorted(np.random.choice(range(1, max_n+1), size, replace=False))

    def _tem_sequencia(self, jogo):
        """Verifica se tem 3 números seguidos"""
        for i in range(len(jogo) - 2):
            if jogo[i] == jogo[i+1] - 1 == jogo[i+2] - 2:
                return True
        return False
