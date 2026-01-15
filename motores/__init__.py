# Exporta as classes para facilitar o acesso
from .base import MotorBase

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

try: from .lotomania import MotorLotomania
except ImportError: pass
