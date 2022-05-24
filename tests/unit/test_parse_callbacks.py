import os

import flanautils

os.environ |= flanautils.find_environment_variables('../.env')

import unittest
from typing import Iterable

from multibot import constants as multibot_constants
from flanabot.bots.flana_tele_bot import FlanaTeleBot


class TestParseCallbacks(unittest.TestCase):
    def _test_no_always_callbacks(self, phrases: Iterable[str], callback: callable):
        for i, phrase in enumerate(phrases):
            with self.subTest(phrase):
                callbacks = [registered_callback.callback for registered_callback in self.flana_tele_bot._parse_callbacks(phrase, multibot_constants.RATIO_REWARD_EXPONENT, multibot_constants.KEYWORDS_LENGHT_PENALTY, multibot_constants.MINIMUM_RATIO_TO_MATCH)
                             if not registered_callback.always]
                self.assertEqual(1, len(callbacks))
                self.assertEqual(callback, callbacks[0], f'\n\nExpected: {callback.__name__}\nActual:   {callbacks[0].__name__}')

    def setUp(self) -> None:
        self.flana_tele_bot = FlanaTeleBot()

    def test_on_bye(self):
        phrases = ['adios', 'taluego', 'adiooo', 'hasta la proxima', 'nos vemos', 'hasta la vista', 'hasta pronto']
        self._test_no_always_callbacks(phrases, self.flana_tele_bot._on_bye)

    def test_on_config_list_show(self):
        phrases = [
            'flanabot ajustes',
            'Flanabot ajustes',
            'Flanabot qué puedo ajustar?',
            'config',
            'configuracion',
            'configuración',
            'configuration'
        ]
        self._test_no_always_callbacks(phrases, self.flana_tele_bot._on_config_list_show)

    def test_on_covid_chart(self):
        phrases = [
            'cuantos contagios',
            'casos',
            'enfermos',
            'muerte',
            'pandemia',
            'enfermedad',
            'fallecidos',
            'mascarillas',
            'virus',
            'covid-19',
            'como va el covid',
            'lo peta el corona'
        ]
        self._test_no_always_callbacks(phrases, self.flana_tele_bot._on_covid_chart)

    def test_on_currency_chart(self):
        phrases = [
            'como van esos dineros',
            'critodivisa',
            'esas cryptos',
            'inversion',
            'moneda',
            'mas caro en argentina?',
            'el puto bitcoin',
            'divisa'
        ]
        self._test_no_always_callbacks(phrases, self.flana_tele_bot._on_currency_chart)

    def test_on_currency_chart_config_activate(self):
        phrases = ['activa el bitcoin automatico']
        self._test_no_always_callbacks(phrases, self.flana_tele_bot._on_currency_chart_config_activate)

    def test_on_currency_chart_config_change(self):
        phrases = ['cambia la config del bitcoin automatico']
        self._test_no_always_callbacks(phrases, self.flana_tele_bot._on_currency_chart_config_change)

    def test_on_currency_chart_config_deactivate(self):
        phrases = ['desactiva el bitcoin automatico']
        self._test_no_always_callbacks(phrases, self.flana_tele_bot._on_currency_chart_config_deactivate)

    def test_on_currency_chart_config_show(self):
        phrases = ['enseña el bitcoin automatico', 'como esta el bitcoin automatico', 'flanabot ajustes bitcoin']
        self._test_no_always_callbacks(phrases, self.flana_tele_bot._on_currency_chart_config_show)

    def test_on_delete(self):
        phrases = ['borra ese mensaje', 'borra ese mensaje puto', 'borra', 'borra el mensaje', 'borra eso', 'borres']
        self._test_no_always_callbacks(phrases, self.flana_tele_bot._on_delete)

    def test_on_delete_original_config_activate(self):
        phrases = [
            'activa el borrado automatico',
            'flanabot pon el auto delete activado',
            'flanabot activa el autodelete'
        ]
        self._test_no_always_callbacks(phrases, self.flana_tele_bot._on_delete_original_config_activate)

    def test_on_delete_original_config_change(self):
        phrases = ['cambia la config del borrado automatico']
        self._test_no_always_callbacks(phrases, self.flana_tele_bot._on_delete_original_config_change)

    def test_on_delete_original_config_deactivate(self):
        phrases = [
            'desactiva el borrado automatico',
            'flanabot pon el auto delete desactivado',
            'flanabot desactiva el autodelete'
        ]
        self._test_no_always_callbacks(phrases, self.flana_tele_bot._on_delete_original_config_deactivate)

    def test_on_delete_original_config_show(self):
        phrases = ['enseña el borrado automatico', 'como esta el borrado automatico', 'flanabot ajustes delete']
        self._test_no_always_callbacks(phrases, self.flana_tele_bot._on_delete_original_config_show)

    def test_on_hello(self):
        phrases = ['hola', 'hello', 'buenos dias', 'holaaaaaa', 'hi', 'holaaaaa', 'saludos', 'ola k ase']
        self._test_no_always_callbacks(phrases, self.flana_tele_bot._on_hello)

    def test_on_mute(self):
        phrases = [
            # 'silencia',
            # 'silencia al pavo ese',
            # 'calla a ese pesao',
            'haz que se calle',
            'quitale el microfono a ese',
            'quitale el micro',
            'quitale el sonido',
            'mutealo',
            'mutea',
            'mutea a ese'
        ]
        self._test_no_always_callbacks(phrases, self.flana_tele_bot._on_mute)

    def test_on_new_message_default(self):
        phrases = [
            'asdqwergf',
            'ytk8',
            'htr',
            'hmj',
            'aaaaaaa'
        ]
        self._test_no_always_callbacks(phrases, self.flana_tele_bot._on_new_message_default)

    def test_on_no_delete_original(self):
        phrases = [
            'no obrres',
            'no borres el original',
            'no borres',
            'no borres el oringal',
            'no oringial',
            'Alberto, [30/11/2021 5:59]\nno borres el original',
            'no borrres el original',
            'no borra ese mensaje',
            'no borres el original joder'
        ]
        self._test_no_always_callbacks(phrases, self.flana_tele_bot._on_no_delete_original)

    def test_on_punish(self):
        phrases = [
            'acaba con el',
            'destrozalo',
            'ataca',
            'acaba',
            'acaba con',
            'termina con el',
            'acabaq con su sufri,iento',
            'acaba con ese apvo',
            'castigalo',
            'castiga a',
            'castiga',
            'enseña quien manda'
        ]
        self._test_no_always_callbacks(phrases, self.flana_tele_bot._on_punish)

    def test_on_scraping(self):
        phrases = [
            'scraping',
            'descarga lo que hay ahi',
            'descarga lo que hubiera ahi',
            'que habia ahi?',
            'que habia ahi',
            'que media habia',
            'descarga el video',
            'descarga la media',
            'descarga',
            'busca',
            'busca y descarga',
            'descarga el contenido'
        ]
        self._test_no_always_callbacks(phrases, self.flana_tele_bot._on_scraping)

    def test_on_scraping_config_activate(self):
        phrases = ['activa el scraping automatico', 'activa el scraping']
        self._test_no_always_callbacks(phrases, self.flana_tele_bot._on_scraping_config_activate)

    def test_on_scraping_config_change(self):
        phrases = ['cambia la config del scraping']
        self._test_no_always_callbacks(phrases, self.flana_tele_bot._on_scraping_config_change)

    def test_on_scraping_config_deactivate(self):
        phrases = ['desactiva el scraping automatico']
        self._test_no_always_callbacks(phrases, self.flana_tele_bot._on_scraping_config_deactivate)

    def test_on_scraping_config_show(self):
        phrases = ['enseña el scraping automatico', 'como esta el scraping automatico', 'flanabot ajustes scraping']
        self._test_no_always_callbacks(phrases, self.flana_tele_bot._on_scraping_config_show)

    def test_on_song_info(self):
        phrases = [
            'que sonaba ahi',
            'suena ahi',
            'que suena',
            'nombre de la cancion',
            'nombre cancion',
            'que cancion suena ahi',
            'sonaba',
            'informacion de la cancion',
            'info de la cancion',
            'titulo',
            'nombre',
            'titulo de la cancion',
            'como se llama esa cancion',
            'como se llama',
            'como se llama la cancion',
            'la cancion que suena en el video',
            'suena en el video',
            'suena'
        ]
        self._test_no_always_callbacks(phrases, self.flana_tele_bot._on_song_info)

    def test_on_unmute(self):
        phrases = [
            'desmutealo',
            'quitale el mute',
            'devuelvele el sonido',
            'quitale el silencio',
            'desilencialo',
            'dejale hablar',
            'unmute'
        ]
        self._test_no_always_callbacks(phrases, self.flana_tele_bot._on_unmute)

    def test_on_unpunish(self):
        phrases = [
            'perdonalo',
            'perdona a',
            'illo quitale a @flanagan el castigo',
            'quita castigo',
            'devuelve los permisos'
        ]
        self._test_no_always_callbacks(phrases, self.flana_tele_bot._on_unpunish)

    def test_on_weather_chart(self):
        phrases = [
            'que calor',
            'llovera',
            'que lluvia ni que',
            'que probabilidad hay de que llueva',
            'que tiempo hara',
            'solano',
            'sol',
            'temperatura',
            'humedad',
            'que tiempo hara mañana',
            'que tiempo hara manana',
            'que tiempo hace en malaga',
            'que tiempo hace en calle larios',
            'tiempo rusia',
            'hara mucho calor en egipto este fin de semana?',
            'pfff no ve que frio ahi en oviedo este finde'
        ]
        self._test_no_always_callbacks(phrases, self.flana_tele_bot._on_weather_chart)

    def test_on_weather_chart_config_activate(self):
        phrases = ['activa el tiempo automatico', 'activa el tiempo']
        self._test_no_always_callbacks(phrases, self.flana_tele_bot._on_weather_chart_config_activate)

    def test_on_weather_chart_config_change(self):
        phrases = ['cambia la config del tiempo']
        self._test_no_always_callbacks(phrases, self.flana_tele_bot._on_weather_chart_config_change)

    def test_on_weather_chart_config_deactivate(self):
        phrases = ['desactiva el tiempo automatico']
        self._test_no_always_callbacks(phrases, self.flana_tele_bot._on_weather_chart_config_deactivate)

    def test_on_weather_chart_config_show(self):
        phrases = ['enseña el tiempo automatico', 'como esta el tiempo automatico', 'flanabot ajustes tiempo']
        self._test_no_always_callbacks(phrases, self.flana_tele_bot._on_weather_chart_config_show)
