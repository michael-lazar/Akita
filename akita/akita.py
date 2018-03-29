import os
import time
import logging
import argparse
from weakref import proxy
from threading import Thread
from datetime import datetime
from collections import deque

from . import LOGO
from .__version__ import __version__
from .parser import HTTPLogParser
from .display import Display
from .metrics import AlertMetric, TaggedCounterMetric, CounterMetric


_logger = logging.getLogger('akita')


def parse_cmdline():
    parser = argparse.ArgumentParser(
        prog='akita', description=LOGO,
        usage='akita [--help] [--version] FILE',
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        'logfile', metavar='FILE', type=argparse.FileType(errors='replace'),
        help='A log file to watch, use "-" to pipe from stdin')
    parser.add_argument(
        '--alert-threshold', type=int, default=10,
        help='High traffic alert threshold, requests/second')
    parser.add_argument(
        '--alert-window', type=int, default=120,
        help='High traffic alert window, in seconds')
    parser.add_argument(
        '-V', '--version', action='version', version='akita ' + __version__)
    return parser.parse_args()


class CursesLogHandler(logging.Handler):
    """
    Custom logger that sends messages to a queue instead of writing them
    to a file or stream.
    """
    def __init__(self, message_queue):
        super().__init__()
        self.message_queue = message_queue

    def emit(self, record):
        self.message_queue.append(record)


class MetricsAggregator:
    """
    Aggregates all of the metrics and alerts used in Akita.
    """

    def __init__(self, alert_threshold, alert_window):
        self.hit_total = 0
        self.miss_total = 0
        self.last_seen = None
        self.last_flush = None

        self.subpath_counter = TaggedCounterMetric(1, 10)
        self.traffic_counter = CounterMetric(1, 240)
        self.alert_metric = AlertMetric(1, alert_window, alert_threshold)

    def add_point(self, http_data):
        self.hit_total += 1
        self.last_seen = datetime.now()

        self.alert_metric.add_point()
        self.traffic_counter.add_point()
        self.subpath_counter.add_point(tags=[http_data['subpath']])

    def add_error(self):
        self.miss_total += 1

    def flush(self):
        timestamp = time.time()
        if self.last_flush and timestamp - self.last_flush > 1:
            # If we're not keeping up with at least 1 flush/second, the
            # process is probably maxed out on resources.
            _logger.warning('Warning: Unable to keep up with log file')
        self.last_flush = timestamp

        self.traffic_counter.flush(timestamp=timestamp)
        self.subpath_counter.flush(timestamp=timestamp)

        alert = self.alert_metric.flush(timestamp=timestamp)
        if alert == AlertMetric.ALERT_START:
            _logger.error('High traffic generated an alert - hits = %.2f/s',
                          self.alert_metric.triggered_rate)
        elif alert == AlertMetric.ALERT_STOP:
            _logger.debug('Traffic has recovered from alert - hits = %.2f/s',
                          self.alert_metric.triggered_rate)


class Akita:

    def __init__(self, log_file, metrics):

        self.log_file = log_file
        self.start_time = None
        self.metrics = metrics

        self.http_parser = HTTPLogParser()
        self.display = Display(proxy(self))

        self.message_queue = deque(maxlen=200)

        self._stream_thread = Thread(target=self._run_stream_thread)
        self._stream_thread.daemon = True

        self._setup_logger()

    def _setup_logger(self):
        """
        Send application log messages to our custom event queue, so they
        can be displayed in the terminal window.
        """
        self.logger = logging.getLogger('akita')
        handler = CursesLogHandler(self.message_queue)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)

    def run_forever(self):
        """
        Loop and render the curses UI until a keyboard interrupt is raised.
        """
        self.start_time = time.time()
        self._stream_thread.start()

        self.logger.info('Starting stream monitor')
        with self.display.curses_session():
            while True:
                self.metrics.flush()
                self.display.draw()
                time.sleep(0.2)

    def _run_stream_thread(self):
        """
        Spin-off a thread to watch the log file for new lines.
        """

        if self.log_file.seekable():
            # Files are seekable, stdin streams aren't
            self.log_file.seek(0, os.SEEK_END)

        while True:
            try:
                line = self.log_file.readline()
                if line:
                    data = self.http_parser.parse(line)
                    self.metrics.add_point(data)
                else:
                    # At the end of the file, wait for more data
                    time.sleep(0.1)
            except Exception as e:
                # The line contained invalid or corrupt data
                # self.logger.error(e)
                self.metrics.add_error()


def main():
    """
    Program entry point
    """
    args = parse_cmdline()
    metrics = MetricsAggregator(
        alert_threshold=args.alert_threshold,
        alert_window=args.alert_window)

    akita = Akita(args.logfile, metrics)
    try:
        akita.run_forever()
    except KeyboardInterrupt:
        pass
