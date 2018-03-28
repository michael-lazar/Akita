import os
import time
import curses
import logging
from datetime import datetime, timedelta
from contextlib import contextmanager

from .__version__ import __version__


_logger = logging.getLogger('akita')


class Display:
    """
    This class provides an interface for drawing text to the terminal and
    monitoring keyboard input using curses.

    All interaction with the terminal should be done within this class's
    context manager, which will setup/teardown the curses library for you.

    A large portion of this code is adapted from another project that I wrote,
    RTV (https://github.com/michael-lazar/rtv)
    """

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

    # Minimum screen size that will be attempted to render
    MIN_HEIGHT = 30
    MIN_WIDTH = 40

    def __init__(self, akita):
        self.akita = akita

        self.stdscr = None
        self.n_rows = None
        self.n_cols = None

    @contextmanager
    def curses_session(self):
        """
        Setup terminal and initialize curses. Most of this copied from
        curses.wrapper in order to convert the wrapper into a context manager.
        """

        try:
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
            yield

        finally:
            if self.stdscr:
                self.stdscr.keypad(0)
                curses.echo()
                curses.nocbreak()
                curses.endwin()

            self.stdscr = None

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

    def draw(self):
        if not self.stdscr:
            return

        self.stdscr.erase()

        self.n_rows, self.n_cols = self.stdscr.getmaxyx()
        if self.n_rows < self.MIN_HEIGHT or self.n_cols < self.MIN_WIDTH:
            self.add_line(self.stdscr, '(enlarge window)')
        else:
            self._draw_title()
            self._draw_info_box()
            self._draw_most_visited()
            self._draw_traffic_chart()
            self._draw_alerts()
            self._draw_footer()
        self.stdscr.touchwin()
        self.stdscr.refresh()

    def _draw_title(self):
        window = self.stdscr.derwin(1, self.n_cols, 0, 0)
        window.bkgd(' ', self.CYAN | curses.A_REVERSE | curses.A_BOLD)
        self.add_line(window, 'Akita HTTP Log Monitor', 0, 1)

        text = 'v{0}'.format(__version__)
        self.add_line(window, text, 0, self.n_cols - len(text) - 1)

    def _draw_info_box(self):
        window = self.stdscr.derwin(10, 30, 1, 0)
        window.border()
        self.add_line(window, ' Information ', 0, 2, attr=self.GREEN)

        metrics = self.akita.metrics

        uptime = int(time.time() - self.akita.start_time)
        text = str(timedelta(seconds=uptime))
        self.add_line(window, 'Uptime       : ', 1, 1, curses.A_BOLD)
        self.add_line(window, text, attr=self.CYAN)

        if metrics.last_seen:
            last_seen = '{:%H:%M:%S}'.format(metrics.last_seen)
        else:
            last_seen = '-'
        self.add_line(window, 'Last Seen    : ', 2, 1, curses.A_BOLD)
        self.add_line(window, str(last_seen), attr=self.CYAN)

        self.add_line(window, 'Parsed Lines : ', 3, 1, curses.A_BOLD)
        self.add_line(window, str(metrics.hit_total), attr=self.GREEN)

        self.add_line(window, 'Failed Lines : ', 4, 1, curses.A_BOLD)
        self.add_line(window, str(metrics.miss_total), attr=self.RED)

        text = '{}/s'.format(metrics.alert_metric.threshold)
        self.add_line(window, 'Alert Thresh : ', 5, 1, curses.A_BOLD)
        self.add_line(window, text, attr=self.MAGENTA)

        text = '{}s'.format(metrics.alert_metric.n_windows)
        self.add_line(window, 'Alert Window : ', 6, 1, curses.A_BOLD)
        self.add_line(window, text, attr=self.MAGENTA)

        self.add_line(window, '(press ctrl-c to quit)', 8, 1)

    def _draw_most_visited(self):
        window = self.stdscr.derwin(10,self.n_cols - 30, 1, 30)
        window.border()
        self.add_line(window, ' Most Visited ', 0, 2, attr=self.GREEN)

        n_rows, n_cols = window.getmaxyx()
        n_rows, n_cols = n_rows - 2, n_cols - 2  # Leave space for the borders

        text = '{:<15} {}'.format('URL Section', 'Hits/10s')
        self.add_line(window, text, 1, 1, attr=curses.A_BOLD)

        counter = self.akita.metrics.subpath_counter.total
        items = (x for x in counter.most_common(n_rows-3) if x[0] is not None)
        for row, (path, count) in enumerate(items, start=2):
            text = '{:<15} '.format('/' + path)
            self.add_line(window, text, row, 1, self.GREEN | curses.A_BOLD)
            self.add_line(window, str(count))

        total = counter.get(None, '-')
        text = '{:<15} {}'.format('All Sections', total)
        self.add_line(window, text, n_rows, 1, curses.A_BOLD)

    def _draw_traffic_chart(self):
        window = self.stdscr.derwin(10, self.n_cols, 11, 0)
        window.border()
        self.add_line(window, ' Traffic ', 0, 2, attr=self.GREEN)

        n_rows, n_cols = window.getmaxyx()
        n_rows, n_cols = n_rows - 2, n_cols - 2  # Leave space for the borders

        traffic = self.akita.metrics.traffic_counter
        status = 'current {}/s, avg {:.2f}/s, min {}/s, max {}/s'.format(
            traffic.history[0],
            traffic.total / len(traffic.history),
            '-' if traffic.min is None else traffic.min,
            '-' if traffic.max is None else traffic.max)
        self.add_line(window, status, n_rows, 2, attr=self.YELLOW | curses.A_BOLD)

        points = traffic.history
        y_max = max(4, max(points))
        for col, point in enumerate(points[:n_cols][::-1]):
            height = int((point / y_max * n_rows))
            window.vline(n_rows - height + 1, col + 1, '|', height-1)

    def _draw_alerts(self):
        window = self.stdscr.derwin(self.n_rows-22, self.n_cols, 21, 0)
        window.border()
        self.add_line(window, ' Alerts ', 0, 2, attr=self.GREEN)

        records = self.akita.message_queue
        n_rows, n_cols = window.getmaxyx()
        n_rows, n_cols = n_rows - 2, n_cols - 2  # Leave space for the borders

        color_map = {
            logging.DEBUG: self.GREEN,
            logging.INFO: self.CYAN,
            logging.WARNING: self.YELLOW,
            logging.ERROR: self.RED,
        }

        start = max(0, len(records) - n_rows)
        stop = len(records)
        for row, i in enumerate(range(start, stop), start=1):
            record = records[i]
            timestamp = datetime.fromtimestamp(record.created)
            text = '[{:%Y-%m-%d %H:%M:%S}] '.format(timestamp)
            self.add_line(window, text, row, 1)

            color = color_map.get(record.levelno, curses.A_NORMAL)
            text = str(record.msg) % record.args
            self.add_line(window, text, attr=color)

    def _draw_footer(self):
        window = self.stdscr.derwin(1, self.n_cols, self.n_rows - 1, 0)
        text = ' Watching {0}'.format(self.akita.log_file.name)
        self.add_line(window, text, attr=self.GREEN)
