import datetime

import flanautils

AUTO_WEATHER_EVERY = datetime.timedelta(hours=6)
CHECK_PUNISHMENTS_EVERY_SECONDS = datetime.timedelta(hours=1).total_seconds()
FLOOD_2s_LIMIT = 4
FLOOD_7s_LIMIT = 7
HEAT_PERIOD_SECONDS = datetime.timedelta(minutes=15).total_seconds()
INSULT_PROBABILITY = 0.00166666667
MAX_PLACE_QUERY_LENGTH = 50
PUNISHMENT_INCREMENT_EXPONENT = 6
PUNISHMENTS_RESET = datetime.timedelta(weeks=6 * flanautils.WEEKS_IN_A_MONTH)
RECOVERY_DELETED_MESSAGE_BEFORE = datetime.timedelta(hours=1)
SCRAPING_MESSAGE_WAITING_TIME = 0.1

BYE_PHRASES = ('Adiós.', 'adieu', 'adio', 'adioh', 'adios', 'adió', 'adiós', 'agur', 'bye', 'byyeeee', 'chao',
               'hasta la vista', 'hasta luego', 'hasta nunca', ' hasta pronto', 'hasta la próxima',
               'nos vemos', 'taluego')

HELLO_PHRASES = ('alo', 'aloh', 'buenas', 'Hola.', 'hello', 'hey', 'hi', 'hola', 'holaaaa', 'holaaaaaaa', 'ola',
                 'ola k ase', 'pa ti mi cola', 'saludos')
INSULTS = (
    '._.',
    'aha',
    'Aléjate de mi.',
    'Ante la duda mi dedo corazón te saluda.',
    'Baneito pa ti en breve.',
    'Calla noob.',
    'Cansino.',
    'Cuéntame menos.',
    'Cuéntame más.',
    'Cállate ya anda.',
    'Cállate.',
    'Das penilla.',
    'De verdad. Estás para encerrarte.',
    'Deberían hacerte la táctica del C4.',
    'Despídete de tu cuenta.',
    'Déjame tranquilo.',
    'Enjoy cancer brain.',
    'Eres cortito, ¿eh?',
    'Eres más malo que pegarle a un padre.',
    'Eres más tonto que peinar bombillas.',
    'Eres más tonto que pellizcar cristales.',
    'Estás mal de la azotea.',
    'Estás mal de la cabeza.',
    'Flanagan es más guapo que tú.',
    'Hablas tanta mierda que tu culo tiene envidia de tu boca.',
    'Hay un concurso de hostias y tienes todas las papeletas.',
    'Loco.',
    'Más tonto y no naces.',
    'No eres muy avispado tú...',
    'Pesado.',
    'Qué bien, ¿eh?',
    'Que me dejes en paz.',
    'Qué pesado.',
    'Quita bicho.',
    'Reportaito mi arma.',
    'Reported.',
    'Retard.',
    'Te voy romper las pelotas.',
    'Tú... no estás muy bien, ¿no?',
    'Ya estamos otra vez...',
    'Ya estamos...',
    'enjoy xd',
    'jAJjajAJjajAJjajAJajJAJajJA',
    'jajaj',
    'o_O',
    'xd',
    '¿Otra vez tú?',
    '¿Pero cuándo te vas a callar?',
    '¿Por qué no te callas?',
    '¿Quién te ha preguntado?',
    '¿Qúe quieres?',
    '¿Te callas o te callo?',
    '¿Te imaginas que me interesa?',
    '¿Te quieres callar?',
    '¿Todo bien?',
    '¿Tú eres así o te dan apagones cerebrales?',
    '🖕',
    '😑',
    '🙄',
    '🤔',
    '🤨'
)

KEYWORDS = {
    'choose': ('choose', 'elige', 'escoge'),
    'covid_chart': ('case', 'caso', 'contagiado', 'contagio', 'corona', 'coronavirus', 'covid', 'covid19', 'death',
                    'disease', 'enfermedad', 'enfermos', 'fallecido', 'incidencia', 'jacovid', 'mascarilla', 'muerte',
                    'muerto', 'pandemia', 'sick', 'virus'),
    'currency_chart': ('argentina', 'bitcoin', 'cardano', 'cripto', 'crypto', 'criptodivisa', 'cryptodivisa',
                       'cryptomoneda', 'cryptocurrency', 'currency', 'dinero', 'divisa', 'ethereum', 'inversion',
                       'moneda', 'pasta'),
    'dice': ('dado', 'dice'),
    'poll': ('encuesta', 'poll', 'quiz'),
    'punish': ('acaba', 'aprende', 'ataca', 'atalo', 'azota', 'boss', 'castiga', 'castigo', 'condena', 'controla',
               'destroy', 'destroza', 'duro', 'ejecuta', 'enseña', 'escarmiento', 'execute', 'fuck', 'fusila', 'hell',
               'humos', 'infierno', 'jefe', 'jode', 'learn', 'leccion', 'lesson', 'manda', 'purgatorio', 'sancion',
               'shoot', 'teach', 'whip'),
    'random': ('aleatorio', 'azar', 'random'),
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

SCRAPING_PHRASES = ('Analizando...', 'Buscando...', 'Hackeando internet... 👀', 'Rebuscando en la web...',
                    'Robando cosas...', 'Scrapeando...', 'Scraping...')
