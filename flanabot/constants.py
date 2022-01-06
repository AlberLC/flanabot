import datetime

import flanautils

AUTO_WEATHER_EVERY = datetime.timedelta(hours=6)
CHECK_MESSAGE_EVERY_SECONDS = datetime.timedelta(days=1).total_seconds()
CHECK_MUTES_EVERY_SECONDS = datetime.timedelta(hours=1).total_seconds()
CHECK_PUNISHMENTS_EVERY_SECONDS = datetime.timedelta(hours=1).total_seconds()
HEAT_PERIOD_SECONDS = datetime.timedelta(minutes=15).total_seconds()
MAX_PLACE_QUERY_LENGTH = 50
PUNISHMENT_INCREMENT_EXPONENT = 6
PUNISHMENTS_RESET = datetime.timedelta(weeks=6 * flanautils.WEEKS_IN_A_MONTH)
RECOVERY_DELETED_MESSAGE_BEFORE = datetime.timedelta(hours=1)
TIME_THRESHOLD_TO_MANUAL_UNMUTE = datetime.timedelta(days=3)
TIME_THRESHOLD_TO_MANUAL_UNPUNISH = datetime.timedelta(days=3)

BAD_PHRASES = (
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

BYE_PHRASES = ('Adiós.', 'adieu', 'adio', 'adioh', 'adios', 'adió', 'adiós', 'agur', 'bye', 'byyeeee', 'chao',
               'hasta la vista', 'hasta luego', 'hasta nunca', ' hasta pronto', 'hasta la próxima',
               'nos vemos', 'taluego')

HELLO_PHRASES = ('alo', 'aloh', 'buenas', 'Hola.', 'hello', 'hey', 'hi', 'hola', 'holaaaa', 'holaaaaaaa', 'ola',
                 'ola k ase', 'pa ti mi cola', 'saludos')

KEYWORDS = {
    'activate': ('activa', 'activar', 'activate', 'deja', 'dejale', 'devuelve', 'devuelvele', 'enable', 'encender',
                 'enciende', 'habilita', 'habilitar'),
    'bye': ('adieu', 'adio', 'adiooooo', 'adios', 'agur', 'buenas', 'bye', 'cama', 'chao', 'dias', 'farewell',
            'goodbye', 'hasta', 'luego', 'noches', 'pronto', 'taluego', 'taluegorl', 'tenga', 'vemos', 'vista', 'voy'),
    'change': ('alter', 'alternar', 'alternate', 'cambiar', 'change', 'default', 'defecto', 'edit', 'editar',
               'exchange', 'modificar', 'modify', 'permutar', 'predeterminado', 'shift', 'swap', 'switch', 'turn',
               'vary'),
    'config': ('ajustar', 'ajuste', 'ajustes', 'automatico', 'automatic', 'config', 'configs', 'configuracion',
               'configuration', 'default', 'defecto', 'setting', 'settings'),
    'covid_chart': ('case', 'caso', 'contagiado', 'contagio', 'corona', 'coronavirus', 'covid', 'covid19', 'death',
                    'disease', 'enfermedad', 'enfermos', 'fallecido', 'incidencia', 'jacovid', 'mascarilla', 'muerte',
                    'muerto', 'pandemia', 'sick', 'virus'),
    'currency_chart': ('argentina', 'bitcoin', 'cardano', 'cripto', 'crypto', 'criptodivisa', 'cryptodivisa',
                       'cryptomoneda', 'cryptocurrency', 'currency', 'dinero', 'divisa', 'ethereum', 'inversion',
                       'moneda', 'pasta'),
    'date': ('ayer', 'de', 'domingo', 'fin', 'finde', 'friday', 'hoy', 'jueves', 'lunes', 'martes', 'mañana',
             'miercoles', 'monday', 'pasado', 'sabado', 'saturday', 'semana', 'sunday', 'thursday', 'today', 'tomorrow',
             'tuesday', 'viernes', 'wednesday', 'week', 'weekend', 'yesterday'),
    'deactivate': ('apaga', 'apagar', 'deactivate', 'deactivate', 'desactivar', 'deshabilita', 'deshabilitar',
                   'disable', 'forbids', 'prohibe', 'quita', 'remove', 'return'),
    'hello': ('alo', 'aloh', 'buenas', 'dias', 'hello', 'hey', 'hi', 'hola', 'holaaaaaa', 'ola', 'saludos', 'tardes'),
    'help': ('ayuda', 'help'),
    'mute': ('calla', 'calle', 'cierra', 'close', 'mute', 'mutea', 'mutealo', 'noise', 'ruido', 'shut', 'silence',
             'silencia'),
    'negate': ('no', 'ocurra', 'ocurre'),
    'permission': ('permiso', 'permission'),
    'punish': ('acaba', 'aprende', 'ataca', 'atalo', 'azota', 'boss', 'castiga', 'castigo', 'condena', 'controla',
               'destroy', 'destroza', 'duro', 'ejecuta', 'enseña', 'escarmiento', 'execute', 'finish', 'fuck', 'fusila',
               'hell', 'humos', 'infierno', 'jefe', 'jode', 'learn', 'leccion', 'lesson', 'manda', 'purgatorio',
               'sancion', 'shoot', 'teach', 'termina', 'whip'),
    'reset': ('recover', 'recovery', 'recupera', 'reinicia', 'reset', 'resetea', 'restart'),
    'scraping': ('api', 'aqui', 'busca', 'contenido', 'content', 'descarga', 'descargar', 'download', 'envia', 'habia',
                 'media', 'redes', 'scrap', 'scraping', 'search', 'send', 'social', 'sociales', 'tenia', 'video',
                 'videos'),
    'show': ('actual', 'enseña', 'estado', 'how', 'is', 'muestra', 'show', 'como'),
    'song_info': ('aqui', 'cancion', 'data', 'datos', 'info', 'informacion', 'information', 'llama', 'media', 'name',
                  'nombre', 'sonaba', 'sonando', 'song', 'sono', 'sound', 'suena', 'title', 'titulo',
                  'video'),
    'sound': ('hablar', 'hable', 'micro', 'microfono', 'microphone', 'sonido', 'sound', 'talk', 'volumen'),
    'thanks': ('gracia', 'gracias', 'grasia', 'grasias', 'grax', 'thank', 'thanks', 'ty'),
    'unmute': ('desilencia', 'desmutea', 'desmutealo', 'unmute'),
    'unpunish': ('absolve', 'forgive', 'innocent', 'inocente', 'perdona', 'spare'),
    'weather_chart': ('atmosfera', 'atmosferico', 'calle', 'calor', 'caloret', 'clima', 'climatologia', 'cloud',
                      'cloudless', 'cloudy', 'cold', 'congelar', 'congelado', 'denbora', 'despejado', 'diluvio', 'frio',
                      'frost', 'hielo', 'humedad', 'llover', 'llueva', 'llueve', 'lluvia', 'nevada', 'nieva', 'nieve',
                      'nube', 'nubes', 'nublado', 'meteorologia', 'rain', 'snow', 'snowfall', 'snowstorm', 'sol',
                      'solano', 'storm', 'sun', 'temperatura', 'tempo', 'tiempo', 'tormenta', 've', 'ventisca',
                      'weather', 'wetter')
}
