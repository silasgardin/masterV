# Arquivo: motores/__init__.py

# 1. Importa a Base (O Pai de todos)
from .base import MotorBase

# 2. Tenta importar os filhos (Especialistas)
# O try/except evita que o sistema quebre se você ainda não criou o arquivo de algum jogo.

try: from .mega_sena import MotorMegaSena
except ImportError: pass

try: from .lotofacil import MotorLotofacil
except ImportError: pass

try: from .quina import MotorQuina
except ImportError: pass

try: from .dia_de_sorte import MotorDiaDeSorte
except ImportError: pass

try: from .dupla_sena import MotorDuplaSena
except ImportError: pass

# Se criar Timemania ou Lotomania no futuro, adicione aqui:
# try: from .timemania import MotorTimemania
# except ImportError: pass
