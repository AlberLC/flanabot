__all__ = ['Connect4Bot']

import asyncio
import copy
import random
from abc import ABC
from collections import defaultdict
from typing import Iterable

from flanautils import Media, MediaType, Source
from multibot import MultiBot

import connect_4_frontend
from flanabot import constants
from flanabot.models import ButtonsGroup, Message, Player


# ----------------------------------------------------------------------------------------------------- #
# --------------------------------------------- CONNECT_4_BOT --------------------------------------------- #
# ----------------------------------------------------------------------------------------------------- #
class Connect4Bot(MultiBot, ABC):
    # -------------------------------------------------------- #
    # ------------------- PROTECTED METHODS ------------------ #
    # -------------------------------------------------------- #
    def _add_handlers(self):
        super()._add_handlers()

        self.register(self._on_connect_4, constants.KEYWORDS['connect_4'])

        self.register(self._on_connect_4_vs_itself, (*constants.KEYWORDS['connect_4'], *constants.KEYWORDS['self']))

        self.register_button(self._on_connect_4_button_press, ButtonsGroup.CONNECT_4)

    def _ai_insert(
        self,
        current_player_num: int,
        next_player_num: int,
        board: list[list[int | None]]
    ) -> tuple[int, int]:
        available_positions_ = self._available_positions(board)

        # check if current player can win
        for i, j in available_positions_:
            if current_player_num in self._check_winners(i, j, board):
                return self.insert_piece(j, current_player_num, board)

        # check if next player can win
        for i, j in available_positions_:
            if next_player_num in self._check_winners(i, j, board):
                return self.insert_piece(j, current_player_num, board)

        # future possibility (above the move)
        next_player_winning_positions_above = []
        current_player_winning_positions_above = []
        for i, j in available_positions_:
            if i < 1:
                continue

            board_copy = copy.deepcopy(board)
            board_copy[i][j] = current_player_num
            winners = self._check_winners(i - 1, j, board_copy)
            if next_player_num in winners:
                next_player_winning_positions_above.append((i, j))
            elif current_player_num in winners:
                current_player_winning_positions_above.append((i, j))

        # check if after the current player moves, it will have 2 positions to win
        for i, j in available_positions_:
            if (i, j) in next_player_winning_positions_above:
                continue

            board_copy = copy.deepcopy(board)
            board_copy[i][j] = current_player_num
            if len(self._winning_positions(board_copy)[current_player_num]) >= 2:
                return self.insert_piece(j, current_player_num, board)

        # check if after the next player moves, he will have 2 positions to win
        for i, j in available_positions_:
            if (i, j) in current_player_winning_positions_above:
                continue

            board_copy = copy.deepcopy(board)
            board_copy[i][j] = next_player_num
            future_winning_positions = self._winning_positions(board_copy)[next_player_num]
            if len(future_winning_positions) < 2:
                continue

            if (i, j) not in next_player_winning_positions_above:
                return self.insert_piece(j, current_player_num, board)
            for i_2, j_2 in future_winning_positions:
                if (i_2, j_2) in available_positions_ and (i_2, j_2) not in next_player_winning_positions_above:
                    return self.insert_piece(j_2, current_player_num, board)

        good_positions = [pos for pos in available_positions_ if pos not in next_player_winning_positions_above and pos not in current_player_winning_positions_above]
        if good_positions:
            j = random.choice(self._best_moves(good_positions, current_player_num, board))[1]
        elif current_player_winning_positions_above:
            j = random.choice(self._best_moves(current_player_winning_positions_above, current_player_num, board))[1]
        else:
            j = random.choice(self._best_moves(next_player_winning_positions_above, current_player_num, board))[1]
        return self.insert_piece(j, current_player_num, board)

    async def _ai_turn(
        self,
        player_1: Player,
        player_2: Player,
        current_player: Player,
        next_player: Player,
        next_turn: int,
        delay: float,
        board: list[list[int | None]],
        message: Message
    ) -> bool:
        await asyncio.sleep(delay)
        i, j = self._ai_insert(current_player.number, next_player.number, board)
        if await self._check_game_finished(i, j, player_1, player_2, next_turn, board, message):
            return True

        return not await self.edit(
            Media(
                connect_4_frontend.make_image(board, next_player, highlight=(i, j)),
                MediaType.IMAGE,
                'png',
                Source.LOCAL
            ),
            message
        )

    @staticmethod
    def _available_positions(board: list[list[int | None]]) -> list[tuple[int, int]]:
        available_positions = []
        for j in range(constants.CONNECT_4_N_COLUMNS):
            for i in range(constants.CONNECT_4_N_ROWS - 1, -1, -1):
                if board[i][j] is None:
                    available_positions.append((i, j))
                    break

        return available_positions

    # noinspection DuplicatedCode
    @staticmethod
    def _best_moves(
        possible_positions: Iterable[tuple[int, int]],
        player_num: int,
        board: list[list[int | None]]
    ) -> list[tuple[int, int]]:
        best_moves = []
        max_points = float('-inf')

        for i, j in possible_positions:
            if 3 <= j <= constants.CONNECT_4_N_COLUMNS - 4:
                points = constants.CONNECT_4_CENTER_COLUMN_POINTS
            else:
                points = 0

            # left
            for j_left in range(j - 1, j - 4, -1):
                if j_left < 0:
                    points -= 1
                    break
                if board[i][j_left] is not None:
                    if board[i][j_left] == player_num:
                        points += 1
                    else:
                        points -= 1
                        break

            # right
            for j_right in range(j + 1, j + 4):
                if j_right >= constants.CONNECT_4_N_COLUMNS:
                    points -= 1
                    break
                if board[i][j_right] is not None:
                    if board[i][j_right] == player_num:
                        points += 1
                    else:
                        points -= 1
                        break

            # up
            for i_up in range(i - 1, i - 4, -1):
                if i_up < 0:
                    points -= 1
                    break
                if board[i_up][j] is not None:
                    if board[i_up][j] == player_num:
                        points += 1
                    else:
                        points -= 1
                        break

            # down
            for i_down in range(i + 1, i + 4):
                if i_down >= constants.CONNECT_4_N_ROWS:
                    points -= 1
                    break
                if board[i_down][j] is not None:
                    if board[i_down][j] == player_num:
                        points += 1
                    else:
                        points -= 1
                        break

            # up left
            for n in range(1, 4):
                i_up = i - n
                j_left = j - n
                if i_up < 0 or j_left < 0:
                    points -= 1
                    break
                if board[i_up][j_left] is not None:
                    if board[i_up][j_left] == player_num:
                        points += 1
                    else:
                        points -= 1
                        break

            # up right
            for n in range(1, 4):
                i_up = i - n
                j_right = j + n
                if i_up < 0 or j_right >= constants.CONNECT_4_N_COLUMNS:
                    points -= 1
                    break
                if board[i_up][j_right] is not None:
                    if board[i_up][j_right] == player_num:
                        points += 1
                    else:
                        points -= 1
                        break

            # down left
            for n in range(1, 4):
                i_down = i + n
                j_left = j - n
                if i_down >= constants.CONNECT_4_N_ROWS or j_left < 0:
                    points -= 1
                    break
                if board[i_down][j_left] is not None:
                    if board[i_down][j_left] == player_num:
                        points += 1
                    else:
                        points -= 1
                        break

            # down right
            for n in range(1, 4):
                i_down = i + n
                j_right = j + n
                if i_down >= constants.CONNECT_4_N_ROWS or j_right >= constants.CONNECT_4_N_COLUMNS:
                    points -= 1
                    break
                if board[i_down][j_right] is not None:
                    if board[i_down][j_right] == player_num:
                        points += 1
                    else:
                        points -= 1
                        break

            if points > max_points:
                best_moves = [(i, j)]
                max_points = points
            elif points == max_points:
                best_moves.append((i, j))

        return best_moves

    async def _check_game_finished(
        self,
        i: int,
        j: int,
        player_1: Player,
        player_2: Player,
        turn: int,
        board: list[list[int | None]],
        message: Message
    ) -> bool:
        if board[i][j] in self._check_winners(i, j, board):
            winner, loser = (player_1, player_2) if board[i][j] == player_1.number else (player_2, player_1)
            edit_kwargs = {'winner': winner, 'loser': loser, 'win_position': (i, j)}
        elif turn >= constants.CONNECT_4_N_ROWS * constants.CONNECT_4_N_COLUMNS:
            edit_kwargs = {'tie': True}
        else:
            return False

        try:
            message.data['connect_4']['is_active'] = False
        except KeyError:
            pass

        await self.edit(
            Media(
                connect_4_frontend.make_image(board, highlight=(i, j), **edit_kwargs),
                MediaType.IMAGE,
                'png',
                Source.LOCAL
            ),
            message,
            buttons=[]
        )

        return True

    @staticmethod
    def _check_winner_left(i: int, j: int, board: list[list[int | None]]) -> int | None:
        if (
                (
                        2 < j and board[i][j - 3] == board[i][j - 2] == board[i][j - 1]
                        or
                        1 < j < constants.CONNECT_4_N_COLUMNS - 1 and board[i][j - 2] == board[i][j - 1] == board[i][j + 1]
                )
                and
                board[i][j - 1] is not None
        ):
            return board[i][j - 1]

    @staticmethod
    def _check_winner_right(i: int, j: int, board: list[list[int | None]]) -> int | None:
        if (
                (
                        j < constants.CONNECT_4_N_COLUMNS - 3 and board[i][j + 1] == board[i][j + 2] == board[i][j + 3]
                        or
                        0 < j < constants.CONNECT_4_N_COLUMNS - 2 and board[i][j - 1] == board[i][j + 1] == board[i][j + 2]
                )
                and
                board[i][j + 1] is not None
        ):
            return board[i][j + 1]

    @staticmethod
    def _check_winner_up(i: int, j: int, board: list[list[int | None]]) -> int | None:
        if (
                (
                        2 < i and board[i - 3][j] == board[i - 2][j] == board[i - 1][j]
                        or
                        1 < i < constants.CONNECT_4_N_ROWS - 1 and board[i - 2][j] == board[i - 1][j] == board[i + 1][j]
                )
                and
                board[i - 1][j] is not None
        ):
            return board[i - 1][j]

    @staticmethod
    def _check_winner_down(i: int, j: int, board: list[list[int | None]]) -> int | None:
        if (
                (
                        i < constants.CONNECT_4_N_ROWS - 3 and board[i + 1][j] == board[i + 2][j] == board[i + 3][j]
                        or
                        0 < i < constants.CONNECT_4_N_ROWS - 2 and board[i - 1][j] == board[i + 1][j] == board[i + 2][j]
                )
                and
                board[i + 1][j] is not None
        ):
            return board[i + 1][j]

    @staticmethod
    def _check_winner_up_left(i: int, j: int, board: list[list[int | None]]) -> int | None:
        if (
                (
                        2 < i and 2 < j and board[i - 3][j - 3] == board[i - 2][j - 2] == board[i - 1][j - 1]
                        or
                        1 < i < constants.CONNECT_4_N_ROWS - 1 and 1 < j < constants.CONNECT_4_N_COLUMNS - 1 and board[i - 2][j - 2] == board[i - 1][j - 1] == board[i + 1][j + 1]

                )
                and
                board[i - 1][j - 1] is not None
        ):
            return board[i - 1][j - 1]

    @staticmethod
    def _check_winner_up_right(i: int, j: int, board: list[list[int | None]]) -> int | None:
        if (
                (
                        2 < i and j < constants.CONNECT_4_N_COLUMNS - 3 and board[i - 1][j + 1] == board[i - 2][j + 2] == board[i - 3][j + 3]
                        or
                        1 < i < constants.CONNECT_4_N_ROWS - 1 and 0 < j < constants.CONNECT_4_N_COLUMNS - 2 and board[i + 1][j - 1] == board[i - 1][j + 1] == board[i - 2][j + 2]
                )
                and
                board[i - 1][j + 1] is not None
        ):
            return board[i - 1][j + 1]

    @staticmethod
    def _check_winner_down_left(i: int, j: int, board: list[list[int | None]]) -> int | None:
        if (
                (
                        i < constants.CONNECT_4_N_ROWS - 3 and 2 < j and board[i + 3][j - 3] == board[i + 2][j - 2] == board[i + 1][j - 1]
                        or
                        0 < i < constants.CONNECT_4_N_ROWS - 2 and 1 < j < constants.CONNECT_4_N_COLUMNS - 1 and board[i + 2][j - 2] == board[i + 1][j - 1] == board[i - 1][j + 1]
                )
                and
                board[i + 1][j - 1] is not None
        ):
            return board[i + 1][j - 1]

    @staticmethod
    def _check_winner_down_right(i: int, j: int, board: list[list[int | None]]) -> int | None:
        if (
                (
                        i < constants.CONNECT_4_N_ROWS - 3 and j < constants.CONNECT_4_N_COLUMNS - 3 and board[i + 1][j + 1] == board[i + 2][j + 2] == board[i + 3][j + 3]
                        or
                        0 < i < constants.CONNECT_4_N_ROWS - 2 and 0 < j < constants.CONNECT_4_N_COLUMNS - 2 and board[i - 1][j - 1] == board[i + 1][j + 1] == board[i + 2][j + 2]
                )
                and
                board[i + 1][j + 1] is not None
        ):
            return board[i + 1][j + 1]

    def _check_winners(self, i: int, j: int, board: list[list[int | None]]) -> set[int]:
        winners = set()

        if winner := self._check_winner_left(i, j, board):
            winners.add(winner)

        if winner := self._check_winner_up(i, j, board):
            winners.add(winner)
            if len(winners) == 2:
                return winners

        if winner := self._check_winner_right(i, j, board):
            winners.add(winner)
            if len(winners) == 2:
                return winners

        if winner := self._check_winner_down(i, j, board):
            winners.add(winner)
            if len(winners) == 2:
                return winners

        if winner := self._check_winner_up_left(i, j, board):
            winners.add(winner)
            if len(winners) == 2:
                return winners

        if winner := self._check_winner_up_right(i, j, board):
            winners.add(winner)
            if len(winners) == 2:
                return winners

        if winner := self._check_winner_down_right(i, j, board):
            winners.add(winner)
            if len(winners) == 2:
                return winners

        if winner := self._check_winner_down_left(i, j, board):
            winners.add(winner)

        return winners

    def _winning_positions(self, board: list[list[int | None]]) -> defaultdict[int, list[tuple[int, int]]]:
        winning_positions: defaultdict[int, list[tuple[int, int]]] = defaultdict(list)
        for next_i, next_j in self._available_positions(board):
            for player_number in self._check_winners(next_i, next_j, board):
                winning_positions[player_number].append((next_i, next_j))

        return winning_positions

    # ---------------------------------------------- #
    #                    HANDLERS                    #
    # ---------------------------------------------- #
    async def _on_connect_4(self, message: Message):
        if message.chat.is_group and not self.is_bot_mentioned(message):
            return

        board = [[None for _ in range(constants.CONNECT_4_N_COLUMNS)] for _ in range(constants.CONNECT_4_N_ROWS)]

        player_1 = Player(message.author.id, message.author.name.split('#')[0], 1)
        try:
            user_2 = next(user for user in message.mentions if user.id != self.id)
        except StopIteration:
            player_2 = Player(self.id, self.name.split('#')[0], 2)
        else:
            player_2 = Player(user_2.id, user_2.name.split('#')[0], 2)

        await self.send(
            media=Media(connect_4_frontend.make_image(board, player_1), MediaType.IMAGE, 'png', Source.LOCAL),
            message=message,
            buttons=self.distribute_buttons([str(n) for n in range(1, constants.CONNECT_4_N_COLUMNS + 1)]),
            buttons_key=ButtonsGroup.CONNECT_4,
            data={
                'connect_4': {
                    'is_active': True,
                    'board': board,
                    'player_1': player_1.to_dict(),
                    'player_2': player_2.to_dict(),
                    'turn': 0
                }
            }
        )
        await self.delete_message(message)

    async def _on_connect_4_button_press(self, message: Message):
        await self.accept_button_event(message)

        connect_4_data = message.data['connect_4']

        is_active = connect_4_data['is_active']
        board = connect_4_data['board']
        player_1 = Player.from_dict(connect_4_data['player_1'])
        player_2 = Player.from_dict(connect_4_data['player_2'])

        if connect_4_data['turn'] % 2 == 0:
            current_player = player_1
            next_player = player_2
        else:
            current_player = player_2
            next_player = player_1
        presser_id = message.buttons_info.presser_user.id
        move_column = int(message.buttons_info.pressed_text) - 1

        if not is_active or current_player.id != presser_id or board[0][move_column] is not None:
            return
        connect_4_data['is_active'] = False

        i, j = self.insert_piece(move_column, current_player.number, board)
        connect_4_data['turn'] += 1
        if await self._check_game_finished(i, j, player_1, player_2, connect_4_data['turn'], board, message):
            return

        await self.edit(
            Media(
                connect_4_frontend.make_image(board, next_player, highlight=(i, j)),
                MediaType.IMAGE,
                'png',
                Source.LOCAL
            ),
            message
        )

        if player_2.id == self.id:
            connect_4_data['turn'] += 1
            if await self._ai_turn(
                    player_1,
                    player_2,
                    next_player,
                    current_player,
                    connect_4_data['turn'],
                    constants.CONNECT_4_AI_DELAY_SECONDS,
                    board,
                    message
            ):
                return

        connect_4_data['is_active'] = True

    async def _on_connect_4_vs_itself(self, message: Message):
        if message.chat.is_group and not self.is_bot_mentioned(message):
            return

        board = [[None for _ in range(constants.CONNECT_4_N_COLUMNS)] for _ in range(constants.CONNECT_4_N_ROWS)]

        player_1 = Player(self.id, self.name.split('#')[0], 1)
        player_2 = Player(self.id, self.name.split('#')[0], 2)
        current_player = player_1
        next_player = player_2
        turn = 0

        bot_message = await self.send(
            media=Media(connect_4_frontend.make_image(board, current_player), MediaType.IMAGE, 'png', Source.LOCAL),
            message=message
        )
        await self.delete_message(message)

        while True:
            turn += 1
            if await self._ai_turn(
                    player_1,
                    player_2,
                    current_player,
                    next_player,
                    turn,
                    constants.CONNECT_4_AI_DELAY_SECONDS / 2,
                    board,
                    bot_message
            ):
                break
            current_player, next_player = next_player, current_player

    # -------------------------------------------------------- #
    # -------------------- PUBLIC METHODS -------------------- #
    # -------------------------------------------------------- #
    @staticmethod
    def insert_piece(j: int, player_number: int, board: list[list[int | None]]) -> tuple[int, int] | None:
        for i in range(constants.CONNECT_4_N_ROWS - 1, -1, -1):
            if board[i][j] is None:
                board[i][j] = player_number
                return i, j
