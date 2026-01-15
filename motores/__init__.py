# Este arquivo informa ao Python que esta pasta é um pacote de módulos.

# Importa as classes para facilitar o acesso pelo app.py
# O ponto (.) antes do nome significa "nesta mesma pasta"

from .base import MotorBase

# Envolvemos em try/except para o app não quebrar caso você ainda
# não tenha criado o arquivo de algum jogo específico.

try:
    from .mega_sena import MotorMegaSena
except ImportError:
    pass

try:
    from .lotofacil import MotorLotofacil
except ImportError:
    pass

# Quando criar novos motores (ex: quina.py), adicione aqui:
# try:
#     from .quina import MotorQuina
# except ImportError:
#     pass
