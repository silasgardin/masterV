import pandas as pd
import numpy as np

class MotorBase:
    def __init__(self, df, config):
        self.df = df
        self.config = config
        
        # Identifica colunas D1, D2... ignorando colunas de Data ou Concurso
        self.cols = [c for c in df.columns if c.startswith('D') and any(char.isdigit() for char in c) and 'Data' not in c]

    def analisar_sinal(self):
        """Gera o sinal visual para o Dashboard (Verde/Amarelo)"""
        # Blindagem: Se não tem dados, retorna neutro
        if self.df is None or self.df.empty: 
            return "⚪ Aguardando", "neutral"
        
        try:
            # Pega a última linha (assumindo que é a mais recente)
            last_row = self.df.iloc[0]
            
            # Verifica se acumulou
            status = str(last_row.get('Status / Premiação', '')).upper()
            # Tenta pegar de outras colunas se o nome variar
            if not status: status = str(last_row.get('Status', '')).upper()
            
            if "ACUMULOU" in status or "ACUMULADO" in status:
                return "💰 ACUMULADO", "go"
            
            # Limpeza de Dados para Análise Matemática
            # Força conversão para números, ignorando erros
            nums = []
            for c in self.cols:
                val = last_row.get(c)
                try:
                    # Tenta converter para float
                    if val and str(val).strip():
                        nums.append(float(val))
                except:
                    continue
            
            if not nums: return "⚪ Erro Dados", "neutral"
            
            # Cálculo do Desvio
            media_esperada = (self.config['max_dezenas'] * self.config['tamanho_jogo']) / 2
            soma = sum(nums)
            desvio = abs(soma - media_esperada)
            
            # Se o resultado foi muito atípico (>40% de desvio), sugere correção
            if desvio > (media_esperada * 0.4): 
                return "🟢 CORREÇÃO PROVÁVEL", "go"
                
            return "🟡 NEUTRO", "wait"
            
        except Exception as e:
            return "⚠️ Erro", "neutral"

    def get_stats(self):
        """Calcula Quentes e Frios com tratamento de erro robusto"""
        # Blindagem contra base vazia
        if self.df is None or self.df.empty:
            return {"quentes": [], "frios": []}

        # [CORREÇÃO DO ERRO TYPEERROR AQUI]
        # 1. Seleciona apenas as colunas de bolas
        df_bolas = self.df[self.cols].copy()
        
        # 2. Força a conversão de TUDO para números. 
        # O que for texto inválido vira NaN (Not a Number)
        df_bolas = df_bolas.apply(pd.to_numeric, errors='coerce')
        
        # 3. Transforma em uma lista única
        todos = df_bolas.values.flatten()
        
        # 4. Remove os NaNs (agora funciona porque são float, não string)
        todos = todos[~np.isnan(todos)]
        
        # Se após limpar não sobrou nada, retorna vazio
        if len(todos) == 0:
             return {"quentes": [], "frios": []}

        # 5. Realiza a contagem
        contagem = pd.Series(todos).value_counts().reindex(range(1, self.config['max_dezenas']+1), fill_value=0)
        
        corte = self.config['max_dezenas'] // 3
        
        return {
            "quentes": contagem.sort_values(ascending=False).index[:corte].tolist(),
            "frios": contagem.sort_values(ascending=True).index[:corte].tolist()
        }

    def gerar_palpite(self, estrategia):
        """Gerador Genérico"""
        stats = self.get_stats()
        
        # Se não tem estatística (erro na base), gera aleatório
        if not stats['quentes']:
            pool = range(1, self.config['max_dezenas']+1)
            jogo = np.random.choice(pool, self.config['tamanho_jogo'], replace=False)
            return sorted(jogo)

        pool = []
        if estrategia == "Tendência": 
            pool = stats['quentes']
        elif estrategia == "Equilíbrio": 
            # Frios + Neutros (Neutros são Total - Quentes)
            todos = set(range(1, self.config['max_dezenas']+1))
            neutros = list(todos - set(stats['quentes']) - set(stats['frios']))
            pool = stats['frios'] + neutros
        else: 
            pool = stats['quentes'] + stats['frios'] # Mestre
        
        # Garante tamanho mínimo do pool
        if len(pool) < self.config['tamanho_jogo']: 
            pool = range(1, self.config['max_dezenas']+1)
        
        jogo = np.random.choice(pool, self.config['tamanho_jogo'], replace=False)
        return sorted(jogo)
