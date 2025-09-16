import asyncio
import curses
import random

from curses_tools import draw_frame, read_controls


def get_frame(path_file_txt) -> str:
    with open(path_file_txt, 'r', encoding='utf-8') as my_file:
        file_contents = my_file.read()
        return file_contents


def get_frame_size(frame: str) -> tuple[int, int]:
    lines = frame.splitlines()
    rows = len(lines)
    cols = max((len(line) for line in lines), default=0)
    return rows, cols


async def animate_spaceship(canvas, pos, frames: list):
    while True:
        for frame in frames:
            row, col = pos['row'], pos['col']
            draw_frame(canvas, row, col, frame)
            await asyncio.sleep(0.2)
            draw_frame(canvas, row, col, frame, negative=True)


async def fire(canvas, start_row, start_column, rows_speed=-0.9, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0.1)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def blink(canvas, row, column, symbol='*'):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        for i in range(20):
            await asyncio.sleep(random.uniform(0.05, 0.2))

        canvas.addstr(row, column, symbol)
        for i in range(3):
            await asyncio.sleep(random.uniform(0.05, 0.2))

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for i in range(5):
            await asyncio.sleep(random.uniform(0.05, 0.2))

        canvas.addstr(row, column, symbol)
        for i in range(3):
            await asyncio.sleep(random.uniform(0.05, 0.2))


async def draw(canvas, rows, columns, tic_timeout=0.1):
    curses.curs_set(False)
    canvas.border()
    canvas.nodelay(True)
    tasks = [
        asyncio.create_task(
            blink(
                canvas,
                random.randint(1, rows - 2),
                random.randint(1, columns - 2),
                symbol=random.choice('+*.:')
            )
        )
        for i in range(100)
    ]

    start_row, start_col = rows // 2, columns // 2
    frames_files_paths = ['rocket_frame_1.txt', 'rocket_frame_2.txt']
    frames = [get_frame(file_txt) for file_txt in frames_files_paths]

    ship_pos = {'row': start_row, 'col': start_col}
    frame_h, frame_w = get_frame_size(frames[0])

    ship_task = asyncio.create_task(animate_spaceship(canvas, ship_pos, frames))
    bullet_task = asyncio.create_task(fire(canvas, rows // 2, columns // 2 + 2))

    try:
        while True:
            canvas.refresh()

            rows_dir, cols_dir, space_pressed = read_controls(canvas)

            if rows_dir or cols_dir:
                new_row = ship_pos['row'] + rows_dir
                new_col = ship_pos['col'] + cols_dir

                max_row, max_col = rows - 1, columns - 1
                min_row, min_col = 1, 1
                max_row_allowed = max_row - frame_h
                max_col_allowed = max_col - frame_w

                ship_pos['row'] = max(min_row, min(new_row, max_row_allowed))
                ship_pos['col'] = max(min_col, min(new_col, max_col_allowed))

            await asyncio.sleep(tic_timeout)

    except KeyboardInterrupt:
        pass
    finally:
        for t in tasks:
            if not t.done():
                t.cancel()
        if 'ship_task' in locals() and not ship_task.done():
            ship_task.cancel()
        if 'bullet_task' in locals() and not bullet_task.done():
            bullet_task.cancel()

        await asyncio.gather(
            *tasks,
            *([ship_task] if 'ship_task' in locals() else []),
            *([bullet_task] if 'bullet_task' in locals() else []),
            return_exceptions=True
        )


def entry(canvas):
    rows, columns = canvas.getmaxyx()
    asyncio.run(draw(canvas, rows, columns))


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(entry)
