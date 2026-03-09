import datetime
from collections import defaultdict

from multibot import Platform

from models.enums import Exchange, PaymentMethod

AUDIT_LOG_AGE = datetime.timedelta(hours=1)
AUDIT_LOG_LIMIT = 5
AUTO_WEATHER_EVERY = datetime.timedelta(hours=6)
BTC_OFFERS_DEFAULT_LIMIT = 5
BTC_OFFERS_WEBSOCKET_RETRY_DELAY_SECONDS = datetime.timedelta(hours=1).total_seconds()
CHECK_CLIENT_CONNECTIONS_EVERY_SECONDS = datetime.timedelta(minutes=1).total_seconds()
CHECK_PUNISHMENTS_EVERY_SECONDS = datetime.timedelta(hours=1).total_seconds()
CONNECT_4_AI_DELAY_SECONDS = 1
CONNECT_4_CENTER_COLUMN_POINTS = 2
CONNECT_4_N_COLUMNS = 7
CONNECT_4_N_ROWS = 6
FLANASERVER_BASE_URL = 'https://flanaserver.duckdns.org'
FLANASERVER_FILE_EXPIRATION_SECONDS = datetime.timedelta(days=3).total_seconds()
FLOOD_2s_LIMIT = 2
FLOOD_7s_LIMIT = 4
HEAT_FIRST_LEVEL = -1
HEAT_PERIOD_SECONDS = datetime.timedelta(minutes=15).total_seconds()
HELP_MINUTES_LIMIT = 1
INSTAGRAM_BAN_SLEEP = datetime.timedelta(days=1)
INSULT_PROBABILITY = 0.00166666667
MAX_PLACE_QUERY_LENGTH = 50
PUNISHMENT_INCREMENT_EXPONENT = 6
PUNISHMENTS_RESET_TIME = datetime.timedelta(weeks=2)
RECOVERY_DELETED_MESSAGE_BEFORE = datetime.timedelta(hours=1)
SCRAPING_TIMEOUT_SECONDS = 20
SPAM_CHANNELS_LIMIT = 2
SPAM_DELETION_DELAY = datetime.timedelta(seconds=5)
SPAM_TIME_RANGE = datetime.timedelta(hours=1)
STEAM_ALL_APPS_ENDPOINT = 'https://api.steampowered.com/ISteamApps/GetAppList/v2'
STEAM_APP_ENDPOINT_TEMPLATE = 'https://store.steampowered.com/api/appdetails?appids={ids}&cc={country_code}&filters=price_overview'
STEAM_APP_IDS_FOR_SCRAPE_COUNTRIES = (400, 620, 730, 210970, 252490, 292030, 427520, 1712350)
STEAM_DB_URL = 'https://steamdb.info'
STEAM_EXCHANGERATE_API_ENDPOINT_TEMPLATE = 'https://v6.exchangerate-api.com/v6/{api_key}/latest/EUR'
STEAM_IDS_BATCH = 750
STEAM_LAST_APPS = 1500
STEAM_MAX_CONCURRENT_REQUESTS = 10
STEAM_MOST_URLS = (
    'https://store.steampowered.com/charts/topselling/global',
    'https://store.steampowered.com/charts/mostplayed'
)
STEAM_RANDOM_APPS = 1000
STEAM_REGION_CODE_MAPPING = {'eu': 'EUR', 'ru': 'RUB', 'pk': 'USD', 'ua': 'UAH', 'za': 'ZAR', 'vn': 'VND', 'tw': 'TWD',
                             'id': 'IDR', 'my': 'MYR', 'ar': 'USD', 'tr': 'USD', 'ph': 'PHP', 'in': 'INR', 'cn': 'CNY',
                             'br': 'BRL', 'sa': 'SAR', 'th': 'THB', 'pe': 'PEN', 'cl': 'CLP', 'kw': 'KWD', 'az': 'USD',
                             'kz': 'KZT', 'co': 'COP', 'mx': 'MXN', 'qa': 'QAR', 'sg': 'SGD', 'jp': 'JPY', 'uy': 'UYU',
                             'ae': 'AED', 'kr': 'KRW', 'hk': 'HKD', 'cr': 'CRC', 'nz': 'NZD', 'ca': 'CAD', 'au': 'AUD',
                             'il': 'ILS', 'us': 'USD', 'no': 'NOK', 'uk': 'GBP', 'pl': 'PLN', 'ch': 'CHF'}
YADIO_API_ENDPOINT = 'https://api.yadio.io/exrates/EUR'

BANNED_POLL_PHRASES = (
    'Deja de dar por culo {presser_name} que no puedes votar aqui',
    'No es pesao {presser_name}, que no tienes permitido votar aqui',
    'Deja de pulsar botones que no puedes votar aqui {presser_name}',
    '{presser_name} deja de intentar votar aqui que no puedes',
    'Te han prohibido votar aquí {presser_name}.',
    'No puedes votar aquí, {presser_name}.'
)

BYE_PHRASES = ('Adiós.', 'adio', 'adioh', 'adios', 'adió', 'adiós', 'agur', 'bye', 'byyeeee', 'chao', 'hasta la vista',
               'hasta luego', 'hasta nunca', ' hasta pronto', 'hasta la próxima', 'nos vemos', 'taluego')

CHANGEABLE_ROLES = defaultdict(
    lambda: defaultdict(list),
    {
        Platform.DISCORD: defaultdict(
            list,
            {
                360868977754505217: [881238165476741161, 991454395663401072, 1033098591725699222, 1176639571677696173],
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
    'btc_offers_exchanges': {
        Exchange.HODLHODL: ('hodlhodl',),
        Exchange.LNP2PBOT: ('lnp2pBot',),
        Exchange.ROBOSATS: ('robosats',)
    },
    'btc_offers_payment_methods': {
        PaymentMethod.BIZUM: ('bizum',),
        PaymentMethod.CREDIT_CARD: ('credit', 'credito'),
        PaymentMethod.HALCASH: ('cajero', 'efectivo', 'halcash'),
        PaymentMethod.INSTANT_SEPA: ('instant sepa', 'instantanea sepa', 'instantaneo sepa', 'sepa instant',
                                     'sepa instantanea', 'sepa instantaneo'),  # check INSTANT_SEPA before SEPA
        PaymentMethod.PAYPAL: ('paypal',),
        PaymentMethod.REVOLUT: ('revolut',),
        PaymentMethod.SEPA: ('sepa',),
        PaymentMethod.WISE: ('wise',)
    },
    'choose': ('choose', 'elige', 'escoge'),
    'connect_4': (('conecta', 'connect', 'ralla', 'raya'), ('4', 'cuatro', 'four')),
    'dice': ('dado', 'dice'),
    'eur': ('eur', 'euro', 'euros', '€'),
    'force': ('force', 'forzar', 'fuerza'),
    'money': ('bitcoin', 'btc', 'cripto', 'criptomoneda', 'crypto', 'cryptocurrency', 'currency', 'currency', 'dinero',
              'divisa', 'moneda', 'money', 'precio', 'price', 'satoshi'),
    'multiple_answer': ('multi', 'multi-answer', 'multiple', 'multirespuesta'),
    'notify': ('alert', 'alertame', 'alertar', 'avisame', 'avisar', 'aviso', 'inform', 'informame', 'informar',
               'notificacion', 'notificame', 'notificar', 'notification'),
    'offer': ('oferta', 'offer', 'orden', 'order', 'post', 'publicacion'),
    'poll': ('encuesta', 'quiz', 'votacion', 'votar', 'voting'),
    'premium': ('%', 'premium', 'prima'),
    'punish': ('acaba', 'aprende', 'ataca', 'atalo', 'azota', 'beating', 'boss', 'castiga', 'castigo', 'condena',
               'controla', 'destroy', 'destroza', 'duro', 'ejecuta', 'enseña', 'escarmiento', 'execute', 'fuck',
               'fusila', 'hell', 'humos', 'infierno', 'jefe', 'jode', 'learn', 'leccion', 'lesson', 'manda', 'paliza',
               'purgatorio', 'purgatory', 'sancion', 'shoot', 'teach', 'whip'),
    'region': ('countries', 'country', 'pais', 'paises', 'region', 'regiones', 'regions', 'zona', 'zonas', 'zone',
               'zones'),
    'scraping': ('busca', 'contenido', 'content', 'descarga', 'descargar', 'descargues', 'download', 'envia', 'scrap',
                 'scrapea', 'scrapees', 'scraping', 'search', 'send'),
    'self': (('contigo', 'contra', 'ti'), ('mismo', 'ti')),
    'song_info': ('cancion', 'data', 'datos', 'info', 'informacion', 'information', 'sonaba', 'sonando', 'song', 'sono',
                  'sound', 'suena'),
    'tunnel': ('canal', 'channel', 'tunel', 'tunnel'),
    'unpunish': ('absolve', 'forgive', 'innocent', 'inocente', 'perdona', 'spare'),
    'until': ('hasta', 'until'),
    'usd': ('$', 'dolar', 'dolares', 'dollar', 'dollars', 'usd'),
    'vote': ('vote', 'voto'),
    'weather': ('atmosfera', 'atmosferico', 'calle', 'calor', 'caloret', 'clima', 'climatologia', 'cloud', 'cloudless',
                'cloudy', 'cold', 'congelar', 'congelado', 'denbora', 'despejado', 'diluvio', 'frio', 'frost', 'hielo',
                'humedad', 'llover', 'llueva', 'llueve', 'lluvia', 'nevada', 'nieva', 'nieve', 'nube', 'nubes',
                'nublado', 'meteorologia', 'rain', 'snow', 'snowfall', 'snowstorm', 'sol', 'solano', 'storm', 'sun',
                'temperatura', 'tempo', 'tiempo', 'tormenta', 'ventisca', 'weather', 'wetter')
}

SCRAPING_PHRASES = ('Analizando...', 'Buscando...', 'Hackeando internet... 👀', 'Rebuscando en la web...',
                    'Robando cosas...', 'Scrapeando...', 'Scraping...')
