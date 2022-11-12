__all__ = ['Connect4Bot']

import copy
import random
from abc import ABC

from multibot import MultiBot

from flanabot import constants
from flanabot.models import ButtonsGroup, Message


# ----------------------------------------------------------------------------------------------------- #
# --------------------------------------------- CONNECT_4_BOT --------------------------------------------- #
# ----------------------------------------------------------------------------------------------------- #
class Connect4Bot(MultiBot, ABC):
    # ----------------------------------------------------------- #
    # -------------------- PROTECTED METHODS -------------------- #
    # ----------------------------------------------------------- #
    def _add_handlers(self):
        super()._add_handlers()

        self.register(self._on_connect_4, constants.KEYWORDS['connect_4'])

        self.register_button(self._on_connect_4_button_press, ButtonsGroup.CONNECT_4)

    def _ai_turn(self, message: Message) -> tuple[int, int]:
        board = message.contents['connect_4']['board']
        player_2_symbol = message.contents['connect_4']['player_2_symbol']
        player_1_symbol = message.contents['connect_4']['player_1_symbol']

        available_positions_ = self._available_positions(message)

        # check if ai can win
        for i, j in available_positions_:
            if player_2_symbol in self._check_winners(i, j, board, message):
                return self.insert_piece(j, player_2_symbol, message)

        # check if human can win
        for i, j in available_positions_:
            if player_1_symbol in self._check_winners(i, j, board, message):
                return self.insert_piece(j, player_2_symbol, message)

        # future possibility (above the play)
        banned_columns = set()
        for i, j in available_positions_:
            if i < 1:
                continue

            board_copy = copy.deepcopy(board)
            board_copy[i][j] = player_2_symbol
            winners = self._check_winners(i - 1, j, board_copy, message)
            if player_1_symbol in winners:
                banned_columns.add(j)
            elif player_2_symbol in winners:
                return self.insert_piece(j, player_2_symbol, message)

        allowed_positions = {j for _, j in available_positions_} - banned_columns
        return self.insert_piece(random.choice(list(allowed_positions)), player_2_symbol, message)

    @staticmethod
    def _available_positions(message: Message) -> list[tuple[int, int]]:
        board = message.contents['connect_4']['board']
        n_rows = message.contents['connect_4']['n_rows']
        n_columns = message.contents['connect_4']['n_columns']
        space_symbol = message.contents['connect_4']['space_symbol']

        available_positions = []
        for j in range(n_columns):
            i = n_rows - 1
            while i >= 0:
                if board[i][j] == space_symbol:
                    available_positions.append((i, j))
                    break
                i -= 1

        return available_positions

    async def _check_game_finished(self, i, j, message: Message) -> bool:
        board = message.contents['connect_4']['board']
        turns = message.contents['connect_4']['turn']
        max_turns = message.contents['connect_4']['max_turns']
        player_1_symbol = message.contents['connect_4']['player_1_symbol']
        player_2_id = message.contents['connect_4']['player_2_id']
        player_1_name = message.contents['connect_4']['player_1_name']
        player_2_name = message.contents['connect_4']['player_2_name']

        if board[i][j] in self._check_winners(i, j, board, message):
            if board[i][j] == player_1_symbol:
                name = player_1_name
            elif player_2_id == self.id:
                name = self.name
            else:
                name = player_2_name

            message.contents['connect_4']['is_active'] = False
            await self.edit(f"{self.format_board(board)}\nHa ganado {name}!!", message)
            return True

        if turns >= max_turns:
            message.contents['connect_4']['is_active'] = False
            await self.edit(f'{self.format_board(board)}\nEmpate.', message)
            return True

    @staticmethod
    def _check_winner_left(i, j, board, message: Message) -> str | None:
        n_columns = message.contents['connect_4']['n_columns']
        space_symbol = message.contents['connect_4']['space_symbol']

        if (
                (
                        2 < j and board[i][j - 3] == board[i][j - 2] == board[i][j - 1]
                        or
                        1 < j < n_columns - 1 and board[i][j - 2] == board[i][j - 1] == board[i][j + 1]
                )
                and
                board[i][j - 1] != space_symbol
        ):
            return board[i][j - 1]

    @staticmethod
    def _check_winner_right(i, j, board, message: Message) -> str | None:
        n_columns = message.contents['connect_4']['n_columns']
        space_symbol = message.contents['connect_4']['space_symbol']

        if (
                (
                        j < n_columns - 3 and board[i][j + 1] == board[i][j + 2] == board[i][j + 3]
                        or
                        0 < j < n_columns - 2 and board[i][j - 1] == board[i][j + 1] == board[i][j + 2]
                )
                and
                board[i][j + 1] != space_symbol
        ):
            return board[i][j + 1]

    @staticmethod
    def _check_winner_up(i, j, board, message: Message) -> str | None:
        n_rows = message.contents['connect_4']['n_rows']
        space_symbol = message.contents['connect_4']['space_symbol']

        if (
                (
                        2 < i and board[i - 3][j] == board[i - 2][j] == board[i - 1][j]
                        or
                        1 < i < n_rows - 1 and board[i - 2][j] == board[i - 1][j] == board[i + 1][j]
                )
                and
                board[i - 1][j] != space_symbol
        ):
            return board[i - 1][j]

    @staticmethod
    def _check_winner_down(i, j, board, message: Message) -> str | None:
        n_rows = message.contents['connect_4']['n_rows']
        space_symbol = message.contents['connect_4']['space_symbol']

        if (
                (
                        i < n_rows - 3 and board[i + 1][j] == board[i + 2][j] == board[i + 3][j]
                        or
                        0 < i < n_rows - 2 and board[i - 1][j] == board[i + 1][j] == board[i + 2][j]
                )
                and
                board[i + 1][j] != space_symbol
        ):
            return board[i + 1][j]

    @staticmethod
    def _check_winner_up_left(i, j, board, message: Message) -> str | None:
        n_rows = message.contents['connect_4']['n_rows']
        n_columns = message.contents['connect_4']['n_columns']
        space_symbol = message.contents['connect_4']['space_symbol']

        if (
                (
                        2 < i and 2 < j and board[i - 3][j - 3] == board[i - 2][j - 2] == board[i - 1][j - 1]
                        or
                        1 < i < n_rows - 1 and 1 < j < n_columns - 1 and board[i - 2][j - 2] == board[i - 1][j - 1] == board[i + 1][j + 1]

                )
                and
                board[i - 1][j - 1] != space_symbol
        ):
            return board[i - 1][j - 1]

    @staticmethod
    def _check_winner_up_right(i, j, board, message: Message) -> str | None:
        n_rows = message.contents['connect_4']['n_rows']
        n_columns = message.contents['connect_4']['n_columns']
        space_symbol = message.contents['connect_4']['space_symbol']

        if (
                (
                        2 < i and j < n_columns - 3 and board[i - 3][j + 3] == board[i - 2][j + 2] == board[i - 1][j + 1]
                        or
                        1 < i < n_rows - 1 and 0 < j < n_columns - 2 and board[i - 2][j + 2] == board[i - 1][j + 1] == board[i + 1][j - 1]
                )
                and
                board[i - 1][j + 1] != space_symbol
        ):
            return board[i - 1][j + 1]

    @staticmethod
    def _check_winner_down_right(i, j, board, message: Message) -> str | None:
        n_rows = message.contents['connect_4']['n_rows']
        n_columns = message.contents['connect_4']['n_columns']
        space_symbol = message.contents['connect_4']['space_symbol']

        if (
                (
                        i < n_rows - 3 and j < n_columns - 3 and board[i + 1][j + 1] == board[i + 2][j + 2] == board[i + 3][j + 3]
                        or
                        0 < i < n_rows - 2 and 0 < j < n_columns - 2 and board[i - 1][j - 1] == board[i + 1][j + 1] == board[i + 2][j + 2]
                )
                and
                board[i + 1][j + 1] != space_symbol
        ):
            return board[i + 1][j + 1]

    @staticmethod
    def _check_winner_down_left(i, j, board, message: Message) -> str | None:
        n_rows = message.contents['connect_4']['n_rows']
        n_columns = message.contents['connect_4']['n_columns']
        space_symbol = message.contents['connect_4']['space_symbol']

        if (
                (
                        i < n_rows - 3 and 2 < j and board[i + 1][j - 1] == board[i + 2][j - 2] == board[i + 3][j - 3]
                        or
                        0 < i < n_rows - 2 and 1 < j < n_columns - 1 and board[i - 1][j + 1] == board[i + 1][j - 1] == board[i + 2][j - 2]
                )
                and
                board[i + 1][j - 1] != space_symbol
        ):
            return board[i + 1][j - 1]

    def _check_winners(self, i, j, board, message: Message) -> set[str]:
        winners = set()

        if winner := self._check_winner_left(i, j, board, message):
            winners.add(winner)

        if winner := self._check_winner_up(i, j, board, message):
            winners.add(winner)
            if len(winners) == 2:
                return winners

        if winner := self._check_winner_right(i, j, board, message):
            winners.add(winner)
            if len(winners) == 2:
                return winners

        if winner := self._check_winner_down(i, j, board, message):
            winners.add(winner)
            if len(winners) == 2:
                return winners

        if winner := self._check_winner_up_left(i, j, board, message):
            winners.add(winner)
            if len(winners) == 2:
                return winners

        if winner := self._check_winner_up_right(i, j, board, message):
            winners.add(winner)
            if len(winners) == 2:
                return winners

        if winner := self._check_winner_down_right(i, j, board, message):
            winners.add(winner)
            if len(winners) == 2:
                return winners

        if winner := self._check_winner_down_left(i, j, board, message):
            winners.add(winner)

        return winners

    # ---------------------------------------------- #
    #                    HANDLERS                    #
    # ---------------------------------------------- #
    async def _on_connect_4(self, message: Message):
        if message.chat.is_group and not self.is_bot_mentioned(message):
            return

        n_rows = 6
        n_columns = 7
        player_1_symbol = 'o'
        player_2_symbol = 'x'
        space_symbol = ' '
        board = [[space_symbol for _ in range(n_columns)] for _ in range(n_rows)]
        player_1_id = message.author.id
        player_1_name = message.author.name.split('#')[0]
        try:
            user_2 = next(user for user in message.mentions if user.id != self.id)
        except StopIteration:
            player_2_id = self.id
            player_2_name = self.name.split('#')[0]
            text = self.format_board(board)
        else:
            player_2_id = user_2.id
            player_2_name = user_2.name.split('#')[0]
            text = f'{self.format_board(board)}\nTurno de {player_1_name}.'

        await self.send(
            text,
            message,
            buttons=self._distribute_buttons([str(n) for n in range(1, n_columns + 1)]),
            buttons_key=ButtonsGroup.CONNECT_4,
            contents={'connect_4': {
                'is_active': True,
                'n_rows': n_rows,
                'n_columns': n_columns,
                'player_1_symbol': player_1_symbol,
                'player_2_symbol': player_2_symbol,
                'space_symbol': space_symbol,
                'board': board,
                'player_1_id': player_1_id,
                'player_2_id': player_2_id,
                'player_1_name': player_1_name,
                'player_2_name': player_2_name,
                'turn': 0,
                'max_turns': n_rows * n_columns
            }}
        )

    async def _on_connect_4_button_press(self, message: Message):
        await self.accept_button_event(message)

        is_active = message.contents['connect_4']['is_active']
        player_1_symbol = message.contents['connect_4']['player_1_symbol']
        player_2_symbol = message.contents['connect_4']['player_2_symbol']
        space_symbol = message.contents['connect_4']['space_symbol']
        board = message.contents['connect_4']['board']
        player_1_id = message.contents['connect_4']['player_1_id']
        player_1_name = message.contents['connect_4']['player_1_name']
        player_2_id = message.contents['connect_4']['player_2_id']
        player_2_name = message.contents['connect_4']['player_2_name']
        turn = message.contents['connect_4']['turn']
        if turn % 2 == 0:
            current_player_id = player_1_id
            next_player_name = player_2_name
            current_player_symbol = player_1_symbol
        else:
            current_player_id = player_2_id
            next_player_name = player_1_name
            current_player_symbol = player_2_symbol
        presser_id = message.buttons_info.presser_user.id
        column_played = int(message.buttons_info.pressed_text) - 1

        if not is_active or board[0][column_played] != space_symbol or current_player_id != presser_id:
            return

        i, j = self.insert_piece(column_played, current_player_symbol, message)
        if await self._check_game_finished(i, j, message):
            return

        if player_2_id == self.id:
            i, j = self._ai_turn(message)
            text = self.format_board(board)
            if await self._check_game_finished(i, j, message):
                return
        else:
            text = f'{self.format_board(board)}\nTurno de {next_player_name}.'

        await self.edit(text, message)

    # -------------------------------------------------------- #
    # -------------------- PUBLIC METHODS -------------------- #
    # -------------------------------------------------------- #
    @staticmethod
    def format_board(board) -> str:
        if not board or not board[0]:
            return ''

        n_columns = len(board[0])
        return '\n'.join(
            (
                '<code>',
                f"╔{'╦'.join(('═════',) * n_columns)}╗",
                f"\n╠{'╬'.join(('═════',) * n_columns)}╣\n".join(f"║  {'  ║  '.join(row_elements)}  ║" for row_elements in board),
                f"╚{'╩'.join(('═════',) * n_columns)}╝",
                f" {' '.join(str(i).center(5) for i in range(1, n_columns + 1))} </code>"

            )
        )

    @staticmethod
    def insert_piece(j, symbol: str, message: Message) -> tuple[int, int]:
        board = message.contents['connect_4']['board']
        n_rows = message.contents['connect_4']['n_rows']
        space_symbol = message.contents['connect_4']['space_symbol']

        i = n_rows - 1
        while i >= 0:
            if board[i][j] == space_symbol:
                board[i][j] = symbol
                break
            i -= 1

        message.contents['connect_4']['turn'] += 1

        return i, j
