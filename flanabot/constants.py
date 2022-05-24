import datetime

import flanautils

AUTO_WEATHER_EVERY = datetime.timedelta(hours=6)
CHECK_PUNISHMENTS_EVERY_SECONDS = datetime.timedelta(hours=1).total_seconds()
HEAT_PERIOD_SECONDS = datetime.timedelta(minutes=15).total_seconds()
INSULT_PROBABILITY = 0.00166666667
MAX_PLACE_QUERY_LENGTH = 50
PUNISHMENT_INCREMENT_EXPONENT = 6
PUNISHMENTS_RESET = datetime.timedelta(weeks=6 * flanautils.WEEKS_IN_A_MONTH)
RECOVERY_DELETED_MESSAGE_BEFORE = datetime.timedelta(hours=1)
TIME_THRESHOLD_TO_MANUAL_UNPUNISH = datetime.timedelta(days=3)
SCRAPING_MESSAGE_WAITING_TIME = 0.1

BYE_PHRASES = ('Adiós.', 'adieu', 'adio', 'adioh', 'adios', 'adió', 'adiós', 'agur', 'bye', 'byyeeee', 'chao',
               'hasta la vista', 'hasta luego', 'hasta nunca', ' hasta pronto', 'hasta la próxima',
               'nos vemos', 'taluego')

HELLO_PHRASES = ('alo', 'aloh', 'buenas', 'Hola.', 'hello', 'hey', 'hi', 'hola', 'holaaaa', 'holaaaaaaa', 'ola',
                 'ola k ase', 'pa ti mi cola', 'saludos')
INSULTS = (
    'Cállate ya anda.',
    '¿Quién te ha preguntado?',
    '¿Tú eres así o te dan apagones cerebrales?',
    'Ante la duda mi dedo corazón te saluda.',
    'Enjoy cancer brain.',
    'Calla noob.',
    'Hablas tanta mierda que tu culo tiene envidia de tu boca.',
    'jAJjajAJjajAJjajAJajJAJajJA',
    'enjoy xd',
    'Reported.',
    'Baneito pa ti en breve.',
    'Despídete de tu cuenta.',
    'Flanagan es más guapo que tú.',
    'jajaj',
    'xd',
    'Hay un concurso de hostias y tienes todas las papeletas.',
    '¿Por qué no te callas?',
    'Das penilla.',
    'Deberían hacerte la táctica del C4.',
    'Te voy romper las pelotas.',
    'Más tonto y no naces.',
    'Eres más tonto que peinar bombillas.',
    'Eres más tonto que pellizcar cristales.',
    'Eres más malo que pegarle a un padre.'
)

KEYWORDS = {
    'covid_chart': ('case', 'caso', 'contagiado', 'contagio', 'corona', 'coronavirus', 'covid', 'covid19', 'death',
                    'disease', 'enfermedad', 'enfermos', 'fallecido', 'incidencia', 'jacovid', 'mascarilla', 'muerte',
                    'muerto', 'pandemia', 'sick', 'virus'),
    'currency_chart': ('argentina', 'bitcoin', 'cardano', 'cripto', 'crypto', 'criptodivisa', 'cryptodivisa',
                       'cryptomoneda', 'cryptocurrency', 'currency', 'dinero', 'divisa', 'ethereum', 'inversion',
                       'moneda', 'pasta'),
    'punish': ('acaba', 'aprende', 'ataca', 'atalo', 'azota', 'boss', 'castiga', 'castigo', 'condena', 'controla',
               'destroy', 'destroza', 'duro', 'ejecuta', 'enseña', 'escarmiento', 'execute', 'finish', 'fuck', 'fusila',
               'hell', 'humos', 'infierno', 'jefe', 'jode', 'learn', 'leccion', 'lesson', 'manda', 'purgatorio',
               'sancion', 'shoot', 'teach', 'termina', 'whip'),
    'scraping': ('api', 'aqui', 'busca', 'contenido', 'content', 'descarga', 'descargar', 'download', 'envia', 'habia',
                 'media', 'redes', 'scrap', 'scraping', 'search', 'send', 'social', 'sociales', 'tenia', 'video',
                 'videos'),
    'song_info': ('aqui', 'cancion', 'data', 'datos', 'info', 'informacion', 'information', 'llama', 'media', 'name',
                  'nombre', 'sonaba', 'sonando', 'song', 'sono', 'sound', 'suena', 'title', 'titulo',
                  'video'),
    'unpunish': ('absolve', 'forgive', 'innocent', 'inocente', 'perdona', 'spare'),
    'weather_chart': ('atmosfera', 'atmosferico', 'calle', 'calor', 'caloret', 'clima', 'climatologia', 'cloud',
                      'cloudless', 'cloudy', 'cold', 'congelar', 'congelado', 'denbora', 'despejado', 'diluvio', 'frio',
                      'frost', 'hielo', 'humedad', 'llover', 'llueva', 'llueve', 'lluvia', 'nevada', 'nieva', 'nieve',
                      'nube', 'nubes', 'nublado', 'meteorologia', 'rain', 'snow', 'snowfall', 'snowstorm', 'sol',
                      'solano', 'storm', 'sun', 'temperatura', 'tempo', 'tiempo', 'tormenta', 'ventisca', 'weather',
                      'wetter')
}

RECOVER_PHRASES = (
    'No hay nada que recuperar.',
    'Ya lo he recuperado y enviado, así que callate ya.',
    'Ya lo he recuperado y enviado, así que mejor estás antento antes de dar por culo.',
    'Ya lo he recuperado y enviado, no lo voy a hacer dos veces.',
    'Ya lo he recuperado y enviado. A ver si leemos más y jodemos menos.',
    'Ya lo he reenviado.'
)

SCRAPING_PHRASES = ('Analizando...', 'Buscando...', 'Hackeando internet... 👀', 'Rebuscando en la web...',
                    'Robando cosas...', 'Scrapeando...', 'Scraping...')
