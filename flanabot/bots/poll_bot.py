__all__ = ['PollBot']

import math
import random
import re
from abc import ABC
from typing import Iterable

import flanautils
import pymongo
from multibot import MultiBot, admin, constants as multibot_constants

from flanabot import constants
from flanabot.models import ButtonsGroup, Message


# ---------------------------------------------------------------------------------------------------- #
# --------------------------------------------- POLL_BOT --------------------------------------------- #
# ---------------------------------------------------------------------------------------------------- #
class PollBot(MultiBot, ABC):
    # ----------------------------------------------------------- #
    # -------------------- PROTECTED METHODS -------------------- #
    # ----------------------------------------------------------- #
    def _add_handlers(self):
        super()._add_handlers()

        self.register(self._on_choose, constants.KEYWORDS['choose'], priority=2)
        self.register(self._on_choose, constants.KEYWORDS['random'], priority=2)
        self.register(self._on_choose, (constants.KEYWORDS['choose'], constants.KEYWORDS['random']), priority=2)

        self.register(self._on_delete_all_votes, (multibot_constants.KEYWORDS['deactivate'], multibot_constants.KEYWORDS['all'], constants.KEYWORDS['vote']))
        self.register(self._on_delete_all_votes, (multibot_constants.KEYWORDS['delete'], multibot_constants.KEYWORDS['all'], constants.KEYWORDS['vote']))

        self.register(self._on_delete_votes, (multibot_constants.KEYWORDS['deactivate'], constants.KEYWORDS['vote']))
        self.register(self._on_delete_votes, (multibot_constants.KEYWORDS['delete'], constants.KEYWORDS['vote']))

        self.register(self._on_dice, constants.KEYWORDS['dice'])

        self.register(self._on_poll, constants.KEYWORDS['poll'], priority=2)

        self.register(self._on_poll_multi, (constants.KEYWORDS['poll'], constants.KEYWORDS['multiple_answer']), priority=2)

        self.register(self._on_stop_poll, multibot_constants.KEYWORDS['deactivate'])
        self.register(self._on_stop_poll, (multibot_constants.KEYWORDS['deactivate'], constants.KEYWORDS['poll']))
        self.register(self._on_stop_poll, multibot_constants.KEYWORDS['stop'])
        self.register(self._on_stop_poll, (multibot_constants.KEYWORDS['stop'], constants.KEYWORDS['poll']))

        self.register(self._on_voting_ban, (multibot_constants.KEYWORDS['deactivate'], multibot_constants.KEYWORDS['permission'], constants.KEYWORDS['vote']))

        self.register(self._on_voting_unban, (multibot_constants.KEYWORDS['activate'], multibot_constants.KEYWORDS['permission'], constants.KEYWORDS['vote']))

        self.register_button(self._on_poll_button_press, ButtonsGroup.POLL)

    @staticmethod
    def _get_options(text: str, discarded_words: Iterable = ()) -> list[str]:
        options = (option for option in text.split() if not flanautils.cartesian_product_string_matching(option.lower(), discarded_words, min_score=multibot_constants.PARSE_CALLBACKS_MIN_SCORE_DEFAULT))
        text = ' '.join(options)

        conjunctions = [f' {conjunction} ' for conjunction in flanautils.CommonWords.get('conjunctions')]
        if any(char in text for char in (',', ';', *conjunctions)):
            conjunction_parts = [f'(?:[,;]*{conjunction}[,;]*)+' for conjunction in conjunctions]
            options = re.split(f"{'|'.join(conjunction_parts)}|[,;]+", text)
            return [option.strip() for option in options if option]
        else:
            return text.split()

    async def _get_poll_message(self, message: Message) -> Message | None:
        if poll_message := message.replied_message:
            if poll_message.data.get('poll') is None:
                return
            return poll_message
        elif (
                (message.chat.is_private or self.is_bot_mentioned(message))
                and
                flanautils.cartesian_product_string_matching(message.text, constants.KEYWORDS['poll'], min_score=multibot_constants.PARSE_CALLBACKS_MIN_SCORE_DEFAULT)
                and
                (poll_message := self.Message.find_one({'data.poll.is_active': True}, sort_keys=(('date', pymongo.DESCENDING),)))
        ):
            return await self.get_message(poll_message.chat.id, poll_message.id)
        else:
            return

    async def _update_poll_buttons(self, message: Message):
        if message.data['poll']['is_multiple_answer']:
            total_votes = len({option_vote[0] for option_votes in message.data['poll']['votes'].values() if option_votes for option_vote in option_votes})
        else:
            total_votes = sum(len(option_votes) for option_votes in message.data['poll']['votes'].values())

        if total_votes:
            buttons = []
            for option, option_votes in message.data['poll']['votes'].items():
                ratio = f'{len(option_votes)}/{total_votes}'
                names = f"({', '.join(option_vote[1] for option_vote in option_votes)})" if option_votes else ''
                buttons.append(f'{option} ➜ {ratio} {names}')
        else:
            buttons = list(message.data['poll']['votes'].keys())

        await self.edit(self.distribute_buttons(buttons, vertically=True), message)

    # ---------------------------------------------- #
    #                    HANDLERS                    #
    # ---------------------------------------------- #
    async def _on_choose(self, message: Message):
        if message.chat.is_group and not self.is_bot_mentioned(message):
            return

        discarded_words = {
            *constants.KEYWORDS['choose'],
            *constants.KEYWORDS['random'],
            self.name.lower(), f'<@{self.id}>',
            'entre', 'between'
        }

        if options := self._get_options(message.text, discarded_words):
            for i in range(1, len(options) - 1):
                try:
                    n1 = flanautils.cast_number(options[i - 1])
                except ValueError:
                    try:
                        n1 = flanautils.words_to_numbers(options[i - 1], ignore_no_numbers=False)
                    except KeyError:
                        continue
                try:
                    n2 = flanautils.cast_number(options[i + 1])
                except ValueError:
                    try:
                        n2 = flanautils.words_to_numbers(options[i + 1], ignore_no_numbers=False)
                    except KeyError:
                        continue
                if options[i] in ('al', 'to'):
                    await self.send(random.randint(math.ceil(n1), math.floor(n2)), message)
                    return
            await self.send(random.choice(options), message)
        else:
            await self.send(random.choice(('¿Que elija el qué?', '¿Y las opciones?', '?', '🤔')), message)

    async def _on_delete_all_votes(self, message: Message):
        await self._on_delete_votes(message, all_=True)

    @admin(send_negative=True)
    async def _on_delete_votes(self, message: Message, all_=False):
        if message.chat.is_group and not self.is_bot_mentioned(message) or not (poll_message := await self._get_poll_message(message)):
            return

        await self.delete_message(message)

        if all_:
            for option_name, option_votes in poll_message.data['poll']['votes'].items():
                poll_message.data['poll']['votes'][option_name].clear()
        else:
            for user in await self._find_users_to_punish(message):
                for option_name, option_votes in poll_message.data['poll']['votes'].items():
                    poll_message.data['poll']['votes'][option_name] = [option_vote for option_vote in option_votes if option_vote[0] != user.id]

        await self._update_poll_buttons(poll_message)

    async def _on_dice(self, message: Message):
        if message.chat.is_group and not self.is_bot_mentioned(message):
            return

        if top_number := flanautils.sum_numbers_in_text(message.text):
            await self.send(random.randint(1, math.floor(top_number)), message)
        else:
            await self.send(random.choice(('¿De cuántas caras?', '¿Y el número?', '?', '🤔')), message)

    async def _on_poll(self, message: Message, is_multiple_answer=False):
        if message.chat.is_group and not self.is_bot_mentioned(message):
            return

        await self.delete_message(message)

        discarded_words = {*constants.KEYWORDS['poll'], *constants.KEYWORDS['multiple_answer'], self.name.lower(), f'<@{self.id}>'}
        if final_options := [f'{option[0].upper()}{option[1:]}' for option in self._get_options(message.text, discarded_words)]:
            await self.send(
                f"Encuesta {'multirespuesta ' if is_multiple_answer else ''}en curso...",
                self.distribute_buttons(final_options, vertically=True),
                message,
                buttons_key=ButtonsGroup.POLL,
                data={'poll': {
                    'is_active': True,
                    'is_multiple_answer': is_multiple_answer,
                    'votes': {option: [] for option in final_options},
                    'banned_users_tries': {}
                }}
            )
        else:
            await self.send(random.choice(('¿Y las opciones?', '?', '🤔')), message)

    async def _on_poll_button_press(self, message: Message):
        await self.accept_button_event(message)
        if not message.data['poll']['is_active']:
            return

        presser_id = message.buttons_info.presser_user.id
        presser_name = message.buttons_info.presser_user.name.split('#')[0]
        if (presser_id_str := str(presser_id)) in message.data['poll']['banned_users_tries']:
            message.data['poll']['banned_users_tries'][presser_id_str] += 1
            message.save()
            if message.data['poll']['banned_users_tries'][presser_id_str] == 3:
                await self.send(random.choice((
                    f'Deja de dar por culo {presser_name} que no puedes votar aqui',
                    f'No es pesao {presser_name}, que no tienes permitido votar aqui',
                    f'Deja de pulsar botones que no puedes votar aqui {presser_name}',
                    f'{presser_name} deja de intentar votar aqui que no puedes',
                    f'Te han prohibido votar aquì {presser_name}.',
                    f'No puedes votar aquí, {presser_name}.'
                )), reply_to=message)
            return

        option_name = results[0] if (results := re.findall('(.*?) ➜.+', message.buttons_info.pressed_text)) else message.buttons_info.pressed_text
        selected_option_votes = message.data['poll']['votes'][option_name]

        if [presser_id, presser_name] in selected_option_votes:
            selected_option_votes.remove([presser_id, presser_name])
        else:
            if not message.data['poll']['is_multiple_answer']:
                for option_votes in message.data['poll']['votes'].values():
                    try:
                        option_votes.remove([presser_id, presser_name])
                    except ValueError:
                        pass
                    else:
                        break
            selected_option_votes.append((presser_id, presser_name))

        await self._update_poll_buttons(message)

    async def _on_poll_multi(self, message: Message):
        await self._on_poll(message, is_multiple_answer=True)

    async def _on_stop_poll(self, message: Message):
        if not (poll_message := await self._get_poll_message(message)):
            return

        winners = []
        max_votes = 1
        for option, votes in poll_message.data['poll']['votes'].items():
            if len(votes) > max_votes:
                winners = [option]
                max_votes = len(votes)
            elif len(votes) == max_votes:
                winners.append(option)

        match winners:
            case [_, _, *_]:
                winners = [f'<b>{winner}</b>' for winner in winners]
                text = f"Encuesta finalizada. Los ganadores son: {flanautils.join_last_separator(winners, ', ', ' y ')}."
            case [winner]:
                text = f'Encuesta finalizada. Ganador: <b>{winner}</b>.'
            case _:
                text = 'Encuesta finalizada.'

        poll_message.data['poll']['is_active'] = False

        await self.edit(text, poll_message)
        if not message.replied_message:
            await self.send(text, reply_to=poll_message)

    @admin(send_negative=True)
    async def _on_voting_ban(self, message: Message):
        if message.chat.is_group and not self.is_bot_mentioned(message) or not (poll_message := await self._get_poll_message(message)):
            return

        await self.delete_message(message)

        for user in await self._find_users_to_punish(message):
            if str(user.id) not in poll_message.data['poll']['banned_users_tries']:
                poll_message.data['poll']['banned_users_tries'][str(user.id)] = 0
        poll_message.save()

    @admin(send_negative=True)
    async def _on_voting_unban(self, message: Message):
        if message.chat.is_group and not self.is_bot_mentioned(message) or not (poll_message := await self._get_poll_message(message)):
            return

        await self.delete_message(message)

        for user in await self._find_users_to_punish(message):
            try:
                del poll_message.data['poll']['banned_users_tries'][str(user.id)]
            except KeyError:
                pass
        poll_message.save()

    # -------------------------------------------------------- #
    # -------------------- PUBLIC METHODS -------------------- #
    # -------------------------------------------------------- #