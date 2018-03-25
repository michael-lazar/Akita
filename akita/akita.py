"""
       / \      _-'
     _/|  \-''- _ /
__-' { |          \
    /             \
    /       "o.  |o }   Akita - An HTTP log monitoring tool
    |            \ ;             for humans and dogs alike
                  ',
       \_         __\
         ''-_    \.//
           / '-____'
          /
        _'
      _-'

"""

import os
import time
import curses
import logging
import argparse
import threading
from collections import deque
from contextlib import contextmanager

from pygtail import Pygtail

from .__version__ import __version__

__title__ = 'Akita'
__author__ = 'Michael Lazar'
__license__ = 'The MIT License (MIT)'
__copyright__ = '(c) 2018 Michael Lazar'


_logger = logging.getLogger(__name__)


def parse_cmdline():
    parser = argparse.ArgumentParser(
        prog='akita', description='A command line HTTP log monitoring tool')
    parser.add_argument('logfile', metavar='FILE', help='The logfile to monitor')
    parser.add_argument('-V', '--version', action='version', version='akita ' + __version__)
    return vars(parser.parse_args())


def tail_log(logfile):
    """
    Returns a generator that will yield new log line in the file, and will
    block while waiting for a new line to be available.
    """
    log_reader = Pygtail(logfile, offset_file=os.devnull)
    # log_reader._fh.seek(0, os.SEEK_END)  # Always start at the end of the file

    while True:
        try:
            yield next(log_reader)
        except StopIteration:
            time.sleep(0.05)


class ScrollBoxWidget:
    """
    Renders a scrolling text feed inside of a window.
    """

    def __init__(self, term, maxsize=100):
        self.term = term
        self.queue = deque([], maxsize)
        self.offset = 0

    def put_message(self, text):
        text = text.strip()
        self.queue.append(text)

    def draw(self, window):
        window.border()

        n_rows, n_cols = window.getmaxyx()
        n_rows -= 2  # For the top & bottom borders

        start = max(0, len(self.queue) - n_rows)
        stop = len(self.queue)
        for row, i in enumerate(range(start, stop), start=1):
            text = self.queue[i]
            self.term.add_line(window, text, row, 1)


class Terminal:
    """
    This class provides an interface for drawing text to the terminal and
    monitoring keyboard input using curses.

    All interaction with the terminal should be done within this class's
    context manager, which will setup/teardown the curses library for you.

    >>> with Terminal() as term:
    >>>     term.draw()
    >>>     term.getch()

    A large portion of this code is adapted from another project that I wrote,
    RTV (https://github.com/michael-lazar/rtv)
    """

    # Minimum screen size that will be attempted to render
    MIN_HEIGHT = 10
    MIN_WIDTH = 20

    # ASCII codes
    ESCAPE = 27
    RETURN = 10
    SPACE = 32

    # Curses color attributes, initialize as A_NORMAL which means
    # "use the terminal's default foreground & background")
    RED = curses.A_NORMAL
    GREEN = curses.A_NORMAL
    YELLOW = curses.A_NORMAL
    BLUE = curses.A_NORMAL
    MAGENTA = curses.A_NORMAL
    CYAN = curses.A_NORMAL
    WHITE = curses.A_NORMAL

    def __init__(self):
        self.stdscr = None
        self.lock = threading.Lock()

        self.scroll_box_widget = ScrollBoxWidget(self)

    def __enter__(self):
        self.setup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.teardown()

    def setup(self):
        """
        Setup terminal and initialize curses. Most of this copied from
        curses.wrapper in order to convert the wrapper into a context manager.
        """

        # Curses must wait for some time after the Escape key is pressed to
        # check if it is the beginning of an escape sequence indicating a
        # special key. The default wait time is 1 second, drop it down to
        # 25ms which should be sufficient for modern operating systems.
        # http://stackoverflow.com/questions/27372068
        os.environ['ESCDELAY'] = '25'

        # Initialize curses
        stdscr = curses.initscr()

        # Turn off echoing of keys, and enter cbreak mode, where no buffering
        # is performed on keyboard input
        curses.noecho()
        curses.cbreak()

        # In keypad mode, escape sequences for special keys (like the cursor
        # keys) will be interpreted and a special value like curses.KEY_LEFT
        # will be returned
        stdscr.keypad(1)

        # Start color, too.  Harmless if the terminal doesn't have color; user
        # can test with has_color() later on.  The try/catch works around a
        # minor bit of over-conscientiousness in the curses module -- the error
        # return from C start_color() is ignorable.
        try:
            curses.start_color()
            curses.use_default_colors()
            colors = {
                'RED': (curses.COLOR_RED, -1),
                'GREEN': (curses.COLOR_GREEN, -1),
                'YELLOW': (curses.COLOR_YELLOW, -1),
                'BLUE': (curses.COLOR_BLUE, -1),
                'MAGENTA': (curses.COLOR_MAGENTA, -1),
                'CYAN': (curses.COLOR_CYAN, -1),
                'WHITE': (curses.COLOR_WHITE, -1),
            }
            for index, (attr, code) in enumerate(colors.items(), start=1):
                curses.init_pair(index, code[0], code[1])
                setattr(self, attr, curses.color_pair(index))

        except Exception:
            _logger.warning('Curses failed to initialize color support')

        # Hide the blinking cursor
        try:
            curses.curs_set(0)
        except Exception:
            _logger.warning('Curses failed to initialize the cursor mode')

        self.stdscr = stdscr

    def teardown(self):
        """
        Release the terminal from curses and cleanup the screen.
        """

        if self.stdscr:
            self.stdscr.keypad(0)
            curses.echo()
            curses.nocbreak()
            curses.endwin()

        self.stdscr = None

    def getch(self):
        """
        Wait for a keypress and return the corresponding character code (int).
        """

        return self.stdscr.getch()

    def clear_input_queue(self):
        """
        Clear excessive input caused by the scroll wheel or holding down a key
        """

        with self.no_delay():
            while self.getch() != -1:
                continue

    @staticmethod
    @contextmanager
    def suspend():
        """
        Suspend curses in order to open another subprocess in the terminal.
        """

        try:
            curses.endwin()
            yield
        finally:
            curses.doupdate()

    @contextmanager
    def no_delay(self):
        """
        Temporarily turn off character delay mode. In this mode, getch will not
        block while waiting for input and will return -1 if no key has been
        pressed.
        """

        try:
            self.stdscr.nodelay(1)
            yield
        finally:
            self.stdscr.nodelay(0)

    @staticmethod
    def add_line(window, text, row=None, col=None, attr=None):
        """
        Unicode aware version of curses's built-in addnstr method.

        Safely draws a line of text on the window starting at position
        (row, col). Checks the boundaries of the window and cuts off the text
        if it exceeds the length of the window.
        """

        # The following arg combos must be supported to conform with addnstr
        # (window, text)
        # (window, text, attr)
        # (window, text, row, col)
        # (window, text, row, col, attr)
        cursor_row, cursor_col = window.getyx()
        row = row if row is not None else cursor_row
        col = col if col is not None else cursor_col

        max_rows, max_cols = window.getmaxyx()
        n_cols = max_cols - col - 1
        if n_cols <= 0:
            # Trying to draw outside of the screen bounds
            return

        # TODO: This makes the assumption that all unicode code points are a
        # single text character wide, which isn't always true
        text = text[:n_cols]

        try:
            params = [] if attr is None else [attr]
            window.addstr(row, col, text, *params)
        except curses.error as e:
            _logger.warning('add_line raised an exception')
            _logger.exception(str(e))

    @staticmethod
    def add_space(window):
        """
        Shortcut for adding a single space to a window at the current position
        """

        row, col = window.getyx()
        _, max_cols = window.getmaxyx()
        n_cols = max_cols - col - 1
        if n_cols <= 0:
            # Trying to draw outside of the screen bounds
            return

        window.addstr(row, col, ' ')

    def draw(self):
        """
        Refresh the screen and re-draw all windows.
        """

        # Lock to prevent multiple threads from attempting to draw at the
        # same time and corrupting the curses internal state.
        self.lock.acquire()

        n_rows, n_cols = self.stdscr.getmaxyx()
        if n_rows < self.MIN_HEIGHT or n_cols < self.MIN_WIDTH:
            return

        self.stdscr.erase()

        # Single line at the top of the screen
        window = self.stdscr.derwin(1, n_cols, 0, 0)
        self._draw_title(window)

        # Window for the rest of the screen
        window = self.stdscr.derwin(10, n_cols, n_rows-10, 0)
        self.scroll_box_widget.draw(window)

        # This is where the screen redraw actually happens
        self.stdscr.touchwin()
        self.stdscr.refresh()

        self.lock.release()

    def _draw_title(self, window):
        window.bkgd(' ', self.CYAN | curses.A_REVERSE | curses.A_BOLD)

        text = ' Akita v{0}'.format(__version__)
        self.add_line(window, text)

