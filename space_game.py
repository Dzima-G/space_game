import asyncio
import curses
import random
from fire_animation import fire
from curses_tools import draw_frame, read_controls

from itertools import cycle

TIC_TIMEOUT = 0.1


def get_frame(path_file_txt) -> str:
    """
    Reads a text file containing an animation frame
    """
    with open(path_file_txt, 'r', encoding='utf-8') as my_file:
        file_contents = my_file.read()
        return file_contents


def get_frame_size(frame: str) -> tuple[int, int]:
    """
    Return (height, width) — ship frame dimensions.
    """
    lines = frame.splitlines()
    height = len(lines)
    width = max(len(line) for line in lines)

    return height, width


def create_stars(
        canvas,
        rows: int,
        columns: int,
        ship_h: int,
        ship_w: int,
        ship_row: int,
        ship_col: int,
        count=150
) -> list:
    """
    Creates a list of coroutines for stars at random positions.
    """
    coroutines = []

    for _ in range(count):
        while True:
            star_row = random.randint(1, rows - 2)
            star_col = random.randint(1, columns - 2)

            if (star_row < ship_row or star_row >= ship_row + ship_h or
                    star_col < ship_col or star_col >= ship_col + ship_w):
                break

        coroutines.append(
            blink(
                canvas,
                star_row,
                star_col,
                symbol=random.choice('+*.:'),
                offset_tics=random.randint(1, 20)
            )
        )

    return coroutines


async def animate_spaceship(
        canvas,
        start_row: int,
        start_col: int,
        frames
):
    """
    Animates a spaceship animation.
    """
    row, col = start_row, start_col

    repeated_frames = []
    for frame in frames:
        repeated_frames.extend([frame, frame])

    frame_cycle = cycle(repeated_frames)

    while True:
        # reload frame
        current_frame = next(frame_cycle)
        frame_h, frame_w = get_frame_size(current_frame)

        # erase the old frame
        draw_frame(canvas, row, col, current_frame, negative=True)

        # control
        rows_dir, cols_dir, space_pressed = read_controls(canvas)
        new_row, new_col = row + rows_dir, col + cols_dir

        # checking boundaries
        max_y, max_x = canvas.getmaxyx()
        new_row = max(1, min(new_row, max_y - frame_h - 1))
        new_col = max(1, min(new_col, max_x - frame_w - 1))

        row, col = new_row, new_col

        current_frame = next(frame_cycle)

        draw_frame(canvas, row, col, current_frame)

        canvas.refresh()

        await asyncio.sleep(0)


async def blink(
        canvas,
        row: int,
        column: int,
        symbol='*',
        offset_tics: int = 0,
):
    while True:
        for i in range(offset_tics):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_DIM)
        for i in range(20):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for i in range(3):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for i in range(5):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for i in range(3):
            await asyncio.sleep(0)


def draw(canvas):
    canvas.border()
    curses.curs_set(False)  # hide cursor
    canvas.nodelay(True)  # do not wait for input

    rows, columns = canvas.getmaxyx()

    frames_paths = ['frames/rocket_frame_1.txt', 'frames/rocket_frame_2.txt']
    frames = [get_frame(path) for path in frames_paths]

    frame_h, frame_w = get_frame_size(frames[0])
    ship_row = (rows - frame_h) // 2
    ship_col = (columns - frame_w) // 2

    coroutines = []

    # star
    coroutines.extend(create_stars(canvas, rows, columns, ship_row, ship_col, frame_h, frame_w))

    # fire
    coroutines.append(fire(canvas, ship_row + frame_h // 2, ship_col + frame_w // 2))

    # spaceship
    coroutines.append(animate_spaceship(canvas, ship_row, ship_col, frames))

    while True:
        for coroutine in coroutines[:]:
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        curses.napms(100)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
