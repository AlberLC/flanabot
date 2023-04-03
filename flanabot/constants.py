import datetime
from collections import defaultdict

from multibot import Platform

AUDIT_LOG_AGE = datetime.timedelta(hours=1)
AUDIT_LOG_LIMIT = 5
AUTO_WEATHER_EVERY = datetime.timedelta(hours=6)
CHECK_PUNISHMENTS_EVERY_SECONDS = datetime.timedelta(hours=1).total_seconds()
CONNECT_4_AI_DELAY_SECONDS = 1
CONNECT_4_CENTER_COLUMN_POINTS = 2
CONNECT_4_N_COLUMNS = 7
CONNECT_4_N_ROWS = 6
FLOOD_2s_LIMIT = 2
FLOOD_7s_LIMIT = 4
HEAT_PERIOD_SECONDS = datetime.timedelta(minutes=15).total_seconds()
HELP_MINUTES_LIMIT = 1
INSTAGRAM_BAN_SLEEP = datetime.timedelta(days=1)
INSULT_PROBABILITY = 0.00166666667
MAX_PLACE_QUERY_LENGTH = 50
PUNISHMENT_INCREMENT_EXPONENT = 6
PUNISHMENTS_RESET_TIME = datetime.timedelta(weeks=2)
RECOVERY_DELETED_MESSAGE_BEFORE = datetime.timedelta(hours=1)
SCRAPING_TIMEOUT_SECONDS = 10

BYE_PHRASES = ('Adiós.', 'adio', 'adioh', 'adios', 'adió', 'adiós', 'agur', 'bye', 'byyeeee', 'chao', 'hasta la vista',
               'hasta luego', 'hasta nunca', ' hasta pronto', 'hasta la próxima', 'nos vemos', 'taluego')

CHANGEABLE_ROLES = defaultdict(
    lambda: defaultdict(list),
    {
        Platform.DISCORD: defaultdict(
            list,
            {
                360868977754505217: [881238165476741161, 991454395663401072, 1033098591725699222],
                862823584670285835: [976660580939202610, 984269640752590868]
            }
        )
    }
)

DISCORD_HEAT_NAMES = [
    'Canal Fresquito',
    'Canal Templaillo',
    'Canal Calentito',
    'Canal Caloret',
    'Canal Caliente',
    'Canal Olor a Vasco',
    'Canal Verano Cordobés al Sol',
    'Canal Al rojo vivo',
    'Canal Ardiendo',
    'Canal INFIERNO'
]

DISCORD_HOT_CHANNEL_IDS = {
    'A': 493529846027386900,
    'B': 493529881125060618,
    'C': 493530483045564417,
    'D': 829032476949217302,
    'E': 829032505645596742
}

HELLO_PHRASES = ('alo', 'aloh', 'buenas', 'Hola.', 'hello', 'hey', 'hi', 'hola', 'holaaaa', 'holaaaaaaa', 'ola',
                 'ola k ase', 'pa ti mi cola', 'saludos')

INSULTS = ('._.', 'aha', 'Aléjate de mi.', 'Ante la duda mi dedo corazón te saluda.', 'Baneito pa ti en breve.',
           'Calla noob.', 'Cansino.', 'Cuéntame menos.', 'Cuéntame más.', 'Cállate ya anda.', 'Cállate.',
           'Das penilla.', 'De verdad. Estás para encerrarte.', 'Deberían hacerte la táctica del C4.',
           'Despídete de tu cuenta.', 'Déjame tranquilo.', 'Enjoy cancer brain.', 'Eres cortito, ¿eh?',
           'Eres más malo que pegarle a un padre.', 'Eres más tonto que peinar bombillas.',
           'Eres más tonto que pellizcar cristales.', 'Estás mal de la azotea.', 'Estás mal de la cabeza.',
           'Flanagan es más guapo que tú.', 'Hablas tanta mierda que tu culo tiene envidia de tu boca.',
           'Hay un concurso de hostias y tienes todas las papeletas.', 'Loco.', 'Más tonto y no naces.',
           'No eres muy avispado tú...', 'Pesado.', 'Qué bien, ¿eh?', 'Que me dejes en paz.', 'Qué pesado.',
           'Quita bicho.', 'Reportaito mi arma.', 'Reported.', 'Retard.', 'Te voy romper las pelotas.',
           'Tú... no estás muy bien, ¿no?', 'Ya estamos otra vez...', 'Ya estamos...', 'enjoy xd',
           'jAJjajAJjajAJjajAJajJAJajJA', 'jajaj', 'o_O', 'xd', '¿Otra vez tú?', '¿Pero cuándo te vas a callar?',
           '¿Por qué no te callas?', '¿Quién te ha preguntado?', '¿Qué quieres?', '¿Te callas o te callo?',
           '¿Te imaginas que me interesa?', '¿Te quieres callar?', '¿Todo bien?',
           '¿Tú eres así o te dan apagones cerebrales?', '🖕', '😑', '🙄', '🤔', '🤨')

KEYWORDS = {
    'choose': ('choose', 'elige', 'escoge'),
    'connect_4': (('conecta', 'connect', 'ralla', 'raya'), ('4', 'cuatro', 'four')),
    'covid_chart': ('case', 'caso', 'contagiado', 'contagio', 'corona', 'coronavirus', 'covid', 'covid19', 'death',
                    'disease', 'enfermedad', 'enfermos', 'fallecido', 'incidencia', 'jacovid', 'mascarilla', 'muerte',
                    'muerto', 'pandemia', 'sick', 'virus'),
    'currency_chart': ('argentina', 'bitcoin', 'cardano', 'cripto', 'crypto', 'criptodivisa', 'cryptodivisa',
                       'cryptomoneda', 'cryptocurrency', 'currency', 'dinero', 'divisa', 'ethereum', 'inversion',
                       'moneda', 'pasta'),
    'dice': ('dado', 'dice'),
    'force': ('force', 'forzar', 'fuerza'),
    'multiple_answer': ('multi', 'multi-answer', 'multiple', 'multirespuesta'),
    'poll': ('encuesta', 'quiz'),
    'punish': ('acaba', 'aprende', 'ataca', 'atalo', 'azota', 'beating', 'boss', 'castiga', 'castigo', 'condena',
               'controla', 'destroy', 'destroza', 'duro', 'ejecuta', 'enseña', 'escarmiento', 'execute', 'fuck',
               'fusila', 'hell', 'humos', 'infierno', 'jefe', 'jode', 'learn', 'leccion', 'lesson', 'manda', 'paliza',
               'purgatorio', 'purgatory', 'sancion', 'shoot', 'teach', 'whip'),
    'random': ('aleatorio', 'azar', 'random'),
    'scraping': ('busca', 'contenido', 'content', 'descarga', 'descargar', 'descargues', 'download', 'envia', 'scrap',
                 'scrapea', 'scrapees', 'scraping', 'search', 'send'),
    'self': (('contigo', 'contra', 'ti'), ('mismo', 'ti')),
    'song_info': ('cancion', 'data', 'datos', 'info', 'informacion', 'information', 'sonaba', 'sonando', 'song', 'sono',
                  'sound', 'suena'),
    'tunnel': ('canal', 'channel', 'tunel', 'tunnel'),
    'unpunish': ('absolve', 'forgive', 'innocent', 'inocente', 'perdona', 'spare'),
    'vote': ('votacion', 'votar', 'vote', 'voting', 'voto'),
    'weather': ('atmosfera', 'atmosferico', 'calle', 'calor', 'caloret', 'clima', 'climatologia', 'cloud', 'cloudless',
                'cloudy', 'cold', 'congelar', 'congelado', 'denbora', 'despejado', 'diluvio', 'frio', 'frost', 'hielo',
                'humedad', 'llover', 'llueva', 'llueve', 'lluvia', 'nevada', 'nieva', 'nieve', 'nube', 'nubes',
                'nublado', 'meteorologia', 'rain', 'snow', 'snowfall', 'snowstorm', 'sol', 'solano', 'storm', 'sun',
                'temperatura', 'tempo', 'tiempo', 'tormenta', 'ventisca', 'weather', 'wetter')
}

SCRAPING_PHRASES = ('Analizando...', 'Buscando...', 'Hackeando internet... 👀', 'Rebuscando en la web...',
                    'Robando cosas...', 'Scrapeando...', 'Scraping...')
