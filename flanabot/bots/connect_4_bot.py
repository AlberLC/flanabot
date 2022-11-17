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
    # ----------------------------------------------------------- #
    # -------------------- PROTECTED METHODS -------------------- #
    # ----------------------------------------------------------- #
    def _add_handlers(self):
        super()._add_handlers()

        self.register(self._on_connect_4, constants.KEYWORDS['connect_4'])

        self.register_button(self._on_connect_4_button_press, ButtonsGroup.CONNECT_4)

    def _ai_turn(self, message: Message) -> tuple[int, int]:
        board = message.contents['connect_4']['board']
        player_1 = Player.from_dict(message.contents['connect_4']['player_1'])
        player_2 = Player.from_dict(message.contents['connect_4']['player_2'])
        turn = message.contents['connect_4']['turn']

        available_positions_ = self._available_positions(board)

        # first move forced to center
        if turn <= 1:
            j = constants.CONNECT_4_N_COLUMNS // 2
            if (constants.CONNECT_4_N_ROWS - 1, j) in available_positions_:
                return self.insert_piece(j, player_2.number, message)
            else:
                return self.insert_piece(random.choice((j - 1, j + 1)), player_2.number, message)

        # check if ai can win
        for i, j in available_positions_:
            if player_2.number in self._check_winners(i, j, board):
                return self.insert_piece(j, player_2.number, message)

        # check if human can win
        for i, j in available_positions_:
            if player_1.number in self._check_winners(i, j, board):
                return self.insert_piece(j, player_2.number, message)

        # future possibility (above the play)
        human_winning_positions_above = []
        ai_winning_positions_above = []
        for i, j in available_positions_:
            if i < 1:
                continue
            board_copy = copy.deepcopy(board)
            board_copy[i][j] = player_2.number
            winners = self._check_winners(i - 1, j, board_copy)
            if player_1.number in winners:
                human_winning_positions_above.append((i, j))
            elif player_2.number in winners:
                ai_winning_positions_above.append((i, j))

        # check if after the ai plays, it will have 2 positions to win
        for i, j in available_positions_:
            if (i, j) in human_winning_positions_above:
                continue

            board_copy = copy.deepcopy(board)
            board_copy[i][j] = player_2.number
            if len(self._winning_positions(board_copy)[player_2.number]) >= 2:
                return self.insert_piece(j, player_2.number, message)

        # check if after the human plays, he will have 2 positions to win
        for i, j in available_positions_:
            board_copy = copy.deepcopy(board)
            board_copy[i][j] = player_1.number
            future_winning_positions = self._winning_positions(board_copy)[player_1.number]
            if len(future_winning_positions) < 2:
                continue
            if (i, j) not in human_winning_positions_above:
                return self.insert_piece(j, player_2.number, message)
            for i_2, j_2 in future_winning_positions:
                if (i_2, j_2) in available_positions_ and (i_2, j_2) not in human_winning_positions_above:
                    return self.insert_piece(j_2, player_2.number, message)

        good_positions = [pos for pos in available_positions_ if pos not in human_winning_positions_above and pos not in ai_winning_positions_above]
        if good_positions:
            j = random.choice(self._best_plays(good_positions, player_2.number, board))[1]
        elif ai_winning_positions_above:
            j = random.choice(self._best_plays(ai_winning_positions_above, player_2.number, board))[1]
        else:
            j = random.choice(self._best_plays(human_winning_positions_above, player_2.number, board))[1]
        return self.insert_piece(j, player_2.number, message)

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
    def _best_plays(
        possible_positions: Iterable[tuple[int, int]],
        player_num: int,
        board: list[list[int | None]]
    ) -> list[tuple[int, int]]:
        best_plays = []
        max_points = float('-inf')

        for i, j in possible_positions:
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
                best_plays = [(i, j)]
                max_points = points
            elif points == max_points:
                best_plays.append((i, j))

        return best_plays

    async def _check_game_finished(self, i: int, j: int, message: Message) -> bool:
        board = message.contents['connect_4']['board']
        turn = message.contents['connect_4']['turn']
        player_1 = Player.from_dict(message.contents['connect_4']['player_1'])
        player_2 = Player.from_dict(message.contents['connect_4']['player_2'])

        if board[i][j] in self._check_winners(i, j, board):
            player = player_1 if board[i][j] == player_1.number else player_2

            message.contents['connect_4']['is_active'] = False
            await self.edit(
                Media(
                    connect_4_frontend.make_image(board, player, highlight=(i, j), win_position=(i, j)),
                    MediaType.IMAGE,
                    'png',
                    Source.LOCAL
                ),
                message
            )
            return True

        if turn >= constants.CONNECT_4_N_ROWS * constants.CONNECT_4_N_COLUMNS:
            message.contents['connect_4']['is_active'] = False
            await self.edit(
                Media(
                    connect_4_frontend.make_image(board, highlight=(i, j), tie=True),
                    MediaType.IMAGE,
                    'png',
                    Source.LOCAL
                ),
                message
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
        winning_positions = defaultdict(list)
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
            contents={'connect_4': {
                'is_active': True,
                'board': board,
                'player_1': player_1.to_dict(),
                'player_2': player_2.to_dict(),
                'turn': 0
            }}
        )

    async def _on_connect_4_button_press(self, message: Message):
        await self.accept_button_event(message)

        is_active = message.contents['connect_4']['is_active']
        board = message.contents['connect_4']['board']
        player_1 = Player.from_dict(message.contents['connect_4']['player_1'])
        player_2 = Player.from_dict(message.contents['connect_4']['player_2'])
        turn = message.contents['connect_4']['turn']

        if turn % 2 == 0:
            current_player = player_1
            next_player = player_2
        else:
            current_player = player_2
            next_player = player_1
        presser_id = message.buttons_info.presser_user.id
        column_played = int(message.buttons_info.pressed_text) - 1

        if not is_active or board[0][column_played] is not None or current_player.id != presser_id:
            return

        i, j = self.insert_piece(column_played, current_player.number, message)
        if await self._check_game_finished(i, j, message):
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
            await asyncio.sleep(constants.CONNECT_4_AI_DELAY_SECONDS)
            i, j = self._ai_turn(message)
            if await self._check_game_finished(i, j, message):
                return
            await self.edit(
                Media(
                    connect_4_frontend.make_image(board, current_player, highlight=(i, j)),
                    MediaType.IMAGE,
                    'png',
                    Source.LOCAL
                ),
                message
            )

    # -------------------------------------------------------- #
    # -------------------- PUBLIC METHODS -------------------- #
    # -------------------------------------------------------- #
    @staticmethod
    def insert_piece(j: int, player_number: int, message: Message) -> tuple[int, int]:
        board = message.contents['connect_4']['board']

        i = constants.CONNECT_4_N_ROWS - 1
        while i >= 0:
            if board[i][j] is None:
                board[i][j] = player_number
                break
            i -= 1

        message.contents['connect_4']['turn'] += 1

        return i, j
