import random
import time

from discord.ext.commands import Bot
from discord import TextChannel

from flana_commands import clear
from utilidades import get_fecha_hoy, imprimir_evento

ID_MENSAJE_ROLES = 588465566172315657
ID_CANAL_ROLES = 589051644583477258
ID = {
    'amir': 225353238822649856,
    'flanagan': 359060940848758794,
    'gorrino': 276680217479741440,
    'jose': 225963293515317248,
    'ale': 360475067009728517,
    'fernando': 234335032062246913,
    'repu': 252458980062789632,
    'silex': 363396342434758666
}


class FlanaBot(Bot):
    TOKEN = 'NTg4NDM0MDMyMzcxNjk1NjE3.XQFFLQ.gy_s0rLG8UCNR4Duua9oeI5A1ek'
    PREFIJO_COMANDOS = '!'

    def __init__(self):
        super().__init__(command_prefix=self.PREFIJO_COMANDOS)
        self.puede_contestar = True
        self.insultos_generales = (
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
            'Deberían hacerte la táctica del C4.'
        )
        self.insultos_hombre = (
            *self.insultos_generales,
            'Te voy romper las pelotas.',
            'Más tonto y no naces.',
            'Eres más tonto que peinar bombillas.',
            'Eres más tonto que pellizar cristales.',
            'Eres más malo que pegarle a un padre.'
        )
        self.insultos_mujer = (
            *self.insultos_generales,
            'Más tonta y no naces.',
            'Eres más tonta que peinar bombillas.',
            'Eres más tonta que pellizar cristales.',
            'Eres más mala que pegarle a un padre.',
        )
        self.insultos_repu = (
            *self.insultos_mujer,
            'Podemita asquerosa',
            '¿Estás más gorda hoy?',
            'Repu, mata a ese.'
        )
        self.insultos_gorrino = (
            *self.insultos_hombre,
            'Pues me trincas el pepino.',
            'Te pasas gorrino.'
        )

        self.add_command(clear)

    async def on_ready(self):
        print()
        print(f"BOT ACTIVADO - Logeado como {self.user.name} (id={self.user.id}) - {get_fecha_hoy()}")
        print('------')
        # canal = self.get_channel(ID_CANAL_ROLES)
        # await canal.send('Mensaje')
        # await canal.last_message.add_reaction('🏃')

    async def on_message(self, message):
        if not message.content or message.author.bot:
            return
        if message.content[0] == self.PREFIJO_COMANDOS:
            await self.process_commands(message)
            return

        texto = '''Autor: {} (id={})
                             Mensaje: "{}" (id={})'''
        imprimir_evento(texto, message.author, message.author.id, message.clean_content, message.id)

        channel = message.channel
        respuesta = None
        if self.user.id in [mention.id for mention in message.mentions] or not random.randint(0, 50):
            # if message.author.id in (ID['amir'], ID['jose'], ID['fernando'], ID['ale'], ID['silex']):
            #     respuesta = random.choice(self.insultos_hombre)
            if message.author.id == ID['repu']:
                respuesta = random.choice(self.insultos_repu)
            elif message.author.id == ID['gorrino']:
                respuesta = random.choice(self.insultos_gorrino)
            elif message.author.id != ID['flanagan']:
                if random.randint(0, 20):
                    respuesta = random.choice(self.insultos_hombre)
                else:
                    respuesta = random.choice(self.insultos_mujer)

        if respuesta and self.puede_contestar:
            async with channel.typing():
                self.puede_contestar = False
                time.sleep(random.randint(1, 3))
            await message.channel.send(respuesta)
            self.puede_contestar = True

    # @client.event
    # async def on_ready():
    #    Channel = client.get_channel('YOUR_CHANNEL_ID')
    #    Text= "YOUR_MESSAGE_HERE"
    #    Moji = await client.send_message(Channel, Text)
    #    await client.add_reaction(Moji, emoji='🏃')
    # @client.event
    # async def on_reaction_add(reaction, user):
    #    Channel = client.get_channel('YOUR_CHANNEL_ID')
    #    if reaction.message.channel.id != Channel
    #    return
    #    if reaction.emoji == "🏃":
    #      Role = discord.utils.get(user.server.roles, name="YOUR_ROLE_NAME_HERE")
    #      await client.add_roles(user, Role)

    def run(self):
        super().run(self.TOKEN)
