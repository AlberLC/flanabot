import logging
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler('flanabot.log')
handler.setLevel(logging.INFO)
logger.addHandler(handler)


def get_fecha_hoy():
    return datetime.now().strftime('%d/%m/%Y %H:%M:%S:%f')


def imprimir_evento(texto, *args):
    texto_salida = f'{get_fecha_hoy()} - {texto.format(*args)}'
    print(texto_salida)
    logger.info(texto_salida)
