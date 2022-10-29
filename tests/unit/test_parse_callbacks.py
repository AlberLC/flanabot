import os

import flanautils

os.environ |= flanautils.find_environment_variables('../.env')

import unittest
from typing import Iterable

from flanabot.bots.flana_tele_bot import FlanaTeleBot


class TestParseCallbacks(unittest.TestCase):
    def _test_no_always_callbacks(self, phrases: Iterable[str], callback: callable):
        for i, phrase in enumerate(phrases):
            with self.subTest(phrase):
                callbacks = [registered_callback.callback for registered_callback in self.flana_tele_bot._parse_callbacks(phrase, self.flana_tele_bot._registered_callbacks)
                             if not registered_callback.always]
                self.assertEqual(1, len(callbacks))
                self.assertEqual(callback, callbacks[0], f'\n\nExpected: {callback.__name__}\nActual:   {callbacks[0].__name__}')

    def setUp(self) -> None:
        self.flana_tele_bot = FlanaTeleBot()

    def test_on_bye(self):
        phrases = ['adios', 'taluego', 'adiooo', 'hasta la proxima', 'nos vemos', 'hasta la vista', 'hasta pronto']
        self._test_no_always_callbacks(phrases, self.flana_tele_bot._on_bye)

    def test_on_config(self):
        phrases = [
            'flanabot ajustes',
            'Flanabot ajustes',
            'Flanabot qué puedo ajustar?',
            'config',
            'configuracion',
            'configuración',
            'configuration'
        ]
        self._test_no_always_callbacks(phrases, self.flana_tele_bot._on_config)

    def test_on_delete(self):
        phrases = ['borra ese mensaje', 'borra ese mensaje puto', 'borra', 'borra el mensaje', 'borra eso', 'borres']
        self._test_no_always_callbacks(phrases, self.flana_tele_bot._on_delete)

    def test_on_hello(self):
        phrases = ['hola', 'hello', 'buenos dias', 'holaaaaaa', 'hi', 'holaaaaa', 'saludos', 'ola k ase']
        self._test_no_always_callbacks(phrases, self.flana_tele_bot._on_hello)

    def test_on_mute(self):
        phrases = [
            'silencia',
            'silencia al pavo ese',
            'calla a ese pesao',
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
        self._test_no_always_callbacks(phrases, self.flana_tele_bot._on_weather)
