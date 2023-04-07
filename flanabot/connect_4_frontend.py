import io
import math
import random
from typing import Sequence

import cairo

from flanabot import constants
from flanabot.models.player import Player

SIZE_MULTIPLIER = 1
LEFT_MARGIN = 20
TOP_MARGIN = 20
CELL_LENGTH = 100 * SIZE_MULTIPLIER
NUMBERS_HEIGHT = 30 * SIZE_MULTIPLIER
TEXT_HEIGHT = 70 * SIZE_MULTIPLIER
NUMBERS_X_INITIAL_POSITION = LEFT_MARGIN + CELL_LENGTH / 2 - 8 * SIZE_MULTIPLIER
NUMBERS_Y_POSITION = TOP_MARGIN + CELL_LENGTH * constants.CONNECT_4_N_ROWS + 40 * SIZE_MULTIPLIER
TEXT_POSITION = (LEFT_MARGIN, TOP_MARGIN + CELL_LENGTH * constants.CONNECT_4_N_ROWS + NUMBERS_HEIGHT + 70 * SIZE_MULTIPLIER)
SURFACE_WIDTH = LEFT_MARGIN * 2 + CELL_LENGTH * constants.CONNECT_4_N_COLUMNS
SURFACE_HEIGHT = TOP_MARGIN * 2 + CELL_LENGTH * constants.CONNECT_4_N_ROWS + NUMBERS_HEIGHT + TEXT_HEIGHT

CIRCLE_RADIUS = 36 * SIZE_MULTIPLIER
CROSS_LINE_WIDTH = 24 * SIZE_MULTIPLIER
FONT_SIZE = 32 * SIZE_MULTIPLIER
TABLE_LINE_WIDTH = 4 * SIZE_MULTIPLIER

BLUE = (66 / 255, 135 / 255, 245 / 255)
BACKGROUND_COLOR = (49 / 255, 51 / 255, 56 / 255)
GRAY = (200 / 255, 200 / 255, 200 / 255)
HIGHLIGHT_COLOR = (104 / 255, 107 / 255, 113 / 255)
RED = (255 / 255, 70 / 255, 70 / 255)
PLAYER_1_COLOR = BLUE
PLAYER_2_COLOR = RED


def center_point(board_position: Sequence[int]) -> tuple[float, float]:
    return LEFT_MARGIN + (board_position[1] + 0.5) * CELL_LENGTH, TOP_MARGIN + (board_position[0] + 0.5) * CELL_LENGTH


def draw_circle(board_position: Sequence[int], radius: float, color: tuple[float, float, float], context: cairo.Context):
    context.set_source_rgba(*color)
    context.arc(*center_point(board_position), radius, 0, 2 * math.pi)
    context.fill()


def draw_line(
    board_position_start: Sequence[int],
    board_position_end: Sequence[int],
    line_width: float,
    color: tuple[float, float, float],
    context: cairo.Context
):
    context.set_line_width(line_width)
    context.set_line_cap(cairo.LINE_CAP_ROUND)
    context.set_source_rgba(*color)
    context.move_to(*center_point(board_position_start))
    context.line_to(*center_point(board_position_end))
    context.stroke()


def draw_table(line_width: float, color: tuple[float, float, float], context: cairo.Context):
    context.set_line_width(line_width)
    context.set_line_cap(cairo.LINE_CAP_ROUND)
    context.set_source_rgba(*color)

    x = LEFT_MARGIN
    y = TOP_MARGIN
    for _ in range(constants.CONNECT_4_N_ROWS + 1):
        context.move_to(x, y)
        context.line_to(x + CELL_LENGTH * constants.CONNECT_4_N_COLUMNS, y)
        context.stroke()
        y += CELL_LENGTH

    x = LEFT_MARGIN
    y = TOP_MARGIN
    for _ in range(constants.CONNECT_4_N_COLUMNS + 1):
        context.move_to(x, y)
        context.line_to(x, y + CELL_LENGTH * constants.CONNECT_4_N_ROWS)
        context.stroke()
        x += CELL_LENGTH


def draw_text(
    text: str,
    point: Sequence[float],
    color: tuple[float, float, float],
    font_size: float,
    italic: bool,
    context: cairo.Context
):
    context.move_to(*point)
    context.set_source_rgba(*color)
    context.select_font_face("Sans", cairo.FONT_SLANT_ITALIC if italic else cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    context.set_font_size(font_size)
    context.show_text(text)


def draw_winner_lines(
    win_position: Sequence[int],
    board: list[list[int | None]],
    color: tuple[float, float, float],
    context: cairo.Context
):
    i, j = win_position
    player_number = board[i][j]

    # horizontal
    j_a = j - 1
    while j_a >= 0 and board[i][j_a] == player_number:
        j_a -= 1
    j_b = j + 1
    while j_b < constants.CONNECT_4_N_COLUMNS and board[i][j_b] == player_number:
        j_b += 1
    if abs(j_a - j) + abs(j_b - j) - 1 >= 4:
        draw_line((i, j_a + 1), (i, j_b - 1), CROSS_LINE_WIDTH, color, context)

    # vertical
    i_a = i - 1
    while i_a >= 0 and board[i_a][j] == player_number:
        i_a -= 1
    i_b = i + 1
    while i_b < constants.CONNECT_4_N_ROWS and board[i_b][j] == player_number:
        i_b += 1
    if abs(i_a - i) + abs(i_b - i) - 1 >= 4:
        draw_line((i_a + 1, j), (i_b - 1, j), CROSS_LINE_WIDTH, color, context)

    # diagonal 1
    i_a = i - 1
    j_a = j - 1
    while i_a >= 0 and j_a >= 0 and board[i_a][j_a] == player_number:
        i_a -= 1
        j_a -= 1
    i_b = i + 1
    j_b = j + 1
    while i_b < constants.CONNECT_4_N_ROWS and j_b < constants.CONNECT_4_N_COLUMNS and board[i_b][j_b] == player_number:
        i_b += 1
        j_b += 1
    if abs(i_a - i) + abs(i_b - i) - 1 >= 4:
        draw_line((i_a + 1, j_a + 1), (i_b - 1, j_b - 1), CROSS_LINE_WIDTH, color, context)

    # diagonal 2
    i_a = i - 1
    j_a = j + 1
    while i_a >= 0 and j_a < constants.CONNECT_4_N_COLUMNS and board[i_a][j_a] == player_number:
        i_a -= 1
        j_a += 1
    i_b = i + 1
    j_b = j - 1
    while i_b < constants.CONNECT_4_N_ROWS and j_b >= 0 and board[i_b][j_b] == player_number:
        i_b += 1
        j_b -= 1
    if abs(i_a - i) + abs(i_b - i) - 1 >= 4:
        draw_line((i_a + 1, j_a - 1), (i_b - 1, j_b + 1), CROSS_LINE_WIDTH, color, context)


def highlight_cell(
    board_position: Sequence[int],
    color: tuple[float, float, float],
    context: cairo.Context
):
    x, y = top_left_point(board_position)
    context.move_to(x, y)
    x += CELL_LENGTH
    context.line_to(x, y)
    y += CELL_LENGTH
    context.line_to(x, y)
    x -= CELL_LENGTH
    context.line_to(x, y)
    context.close_path()
    context.set_source_rgba(*color)
    context.fill()


def make_image(
    board: list[list[int | None]],
    next_turn_player: Player = None,
    winner: Player = None,
    loser: Player = None,
    highlight=None,
    win_position: Sequence[int] = None,
    tie=False
) -> bytes:
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, SURFACE_WIDTH, SURFACE_HEIGHT)
    context = cairo.Context(surface)

    paint_background(BACKGROUND_COLOR, context)
    if highlight:
        highlight_cell(highlight, HIGHLIGHT_COLOR, context)
    draw_table(TABLE_LINE_WIDTH, GRAY, context)
    write_numbers(GRAY, context)
    for i in range(constants.CONNECT_4_N_ROWS):
        for j in range(constants.CONNECT_4_N_COLUMNS):
            match board[i][j]:
                case 1:
                    draw_circle((i, j), CIRCLE_RADIUS, PLAYER_1_COLOR, context)
                case 2:
                    draw_circle((i, j), CIRCLE_RADIUS, PLAYER_2_COLOR, context)

    if tie:
        write_tie(context)
    elif winner:
        player_color = PLAYER_1_COLOR if winner.number == 1 else PLAYER_2_COLOR
        draw_winner_lines(win_position, board, player_color, context)
        write_winner(winner, loser, context)
    else:
        write_player_turn(next_turn_player.name, PLAYER_1_COLOR if next_turn_player.number == 1 else PLAYER_2_COLOR, context)

    buffer = io.BytesIO()
    surface.write_to_png(buffer)

    return buffer.getvalue()


def paint_background(color: tuple[float, float, float], context: cairo.Context):
    context.set_source_rgba(*color)
    context.paint()


def top_left_point(board_position: Sequence[int]) -> tuple[float, float]:
    return LEFT_MARGIN + board_position[1] * CELL_LENGTH, TOP_MARGIN + board_position[0] * CELL_LENGTH


def write_numbers(color: tuple[float, float, float], context: cairo.Context):
    x = NUMBERS_X_INITIAL_POSITION
    for j in range(constants.CONNECT_4_N_COLUMNS):
        draw_text(str(j + 1), (x, NUMBERS_Y_POSITION), color, FONT_SIZE, italic=False, context=context)
        x += CELL_LENGTH


def write_player_turn(name: str, color: tuple[float, float, float], context: cairo.Context):
    text = 'Turno de '
    point = TEXT_POSITION
    draw_text(text, point, GRAY, FONT_SIZE, True, context)

    point = (point[0] + context.text_extents(text).width + 9 * SIZE_MULTIPLIER, point[1])
    draw_text(name, point, color, FONT_SIZE, True, context)

    point = (point[0] + context.text_extents(name).width, point[1])
    draw_text('.', point, GRAY, FONT_SIZE, True, context)


def write_tie(context: cairo.Context):
    draw_text(f"Empate{random.choice(('.', ' :c', ' :/', ' :s'))}", TEXT_POSITION, GRAY, FONT_SIZE, True, context)


def write_winner(winner: Player, loser: Player, context: cairo.Context):
    winner_color, loser_color = (PLAYER_1_COLOR, PLAYER_2_COLOR) if winner.number == 1 else (PLAYER_2_COLOR, PLAYER_1_COLOR)

    point = TEXT_POSITION
    draw_text(winner.name, point, winner_color, FONT_SIZE, True, context)

    text = ' le ha ganado a '
    point = (point[0] + context.text_extents(winner.name).width + 3 * SIZE_MULTIPLIER, point[1])
    draw_text(text, point, GRAY, FONT_SIZE, True, context)

    point = (point[0] + context.text_extents(text).width + 10 * SIZE_MULTIPLIER, point[1])
    draw_text(loser.name, point, loser_color, FONT_SIZE, True, context)

    point = (point[0] + context.text_extents(loser.name).width + 3 * SIZE_MULTIPLIER, point[1])
    draw_text('!!!', point, GRAY, FONT_SIZE, True, context)
