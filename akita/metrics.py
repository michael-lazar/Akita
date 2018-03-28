import time
import logging
import threading
from collections import Counter


_logger = logging.getLogger('akita')


class SlidingWindowBase:
    """
    Data structure that keeps track of the total number of events that have
    occurred in a given time frame. Events are binned into time windows based
    on their timestamps, and the most recent N windows are kept in a rotating
    queue. This allows for monitoring the moving average of a time series
    data stream in real time.
    """

    # The data structure that will be used to accumulate events,
    # must support +/- operations.
    datatype = None

    def __init__(self, window_size=1, n_windows=10):
        """
        Params:
            window_size (int): The length of each event window, in seconds.
            n_windows (int): The number of windows kept in memory.
        """

        self.window_size = window_size
        self.n_windows = n_windows

        self.head = None

        # Note: I decided to use a plain list instead of a deque because
        # fast random access is more important than the cost of inserting at
        # the head of the list, the latter of which will only happen at most
        # once per window_size.
        self.history = [self.datatype() for _ in range(self.n_windows)]
        self.buffer = self.datatype()
        self.total = self.datatype()

        self.lock = threading.Lock()

    def flush(self, timestamp=None):
        """
        Re-align the head of the sliding window to the given timestamp.

        Params:
            timestamp (float): The time to align the head of the sliding
                window with, will default to the current time.
        """
        timestamp = time.time() if timestamp is None else timestamp
        window = timestamp - timestamp % self.window_size

        if self.head is None:
            # The first flush initializes the window
            self.head = window

        elif window > self.head:
            # Add the current buffer to the history window
            self._history_update(self.buffer)
            offset = int((window - self.head) // self.window_size)

            # Pad with zeros if the gap is larger than 1 window
            for _ in range(offset-1):
                self._history_update(self.datatype())

            self.buffer = self.datatype()
            self.head = window

    def _history_update(self, buffer):
        self.history.insert(0, buffer)
        self.total += buffer
        self.total -= self.history.pop()

    def add_point(self):
        """
        Add a time series event at the given timestamp.
        """
        raise NotImplementedError


class CounterMetric(SlidingWindowBase):
    """
    A sliding window that uses a integer to accumulate the number of events
    in each time increment.
    """

    datatype = int

    def __init__(self, window_size=1, n_windows=10):
        super().__init__(window_size, n_windows)

        self.min = None
        self.max = None

    def _history_update(self, buffer):
        super()._history_update(buffer)

        self.min = buffer if self.min is None else min(self.min, buffer)
        self.max = buffer if self.max is None else max(self.max, buffer)

    def add_point(self):
        self.buffer += 1


class AlertMetric(CounterMetric):
    """
    An extension of the CounterMetric that watches the avg. rate of events
    over the entire window, and returns an alert when the rate crosses a given
    threshold.
    """

    ALERT_START = 'start'
    ALERT_STOP = 'stop'

    def __init__(self, window_size=1, n_windows=120, threshold=10):
        super().__init__(window_size, n_windows)

        self.threshold = threshold
        self.triggered = False
        self.triggered_rate = None
        self.triggered_at = None

    def flush(self, timestamp=None):
        super().flush(timestamp=timestamp)

        if self.head is None or not self.history:
            return
        elif self.triggered_at and self.head - self.triggered_at < self.n_windows:
            # Not enough time has elapsed since the previous alert
            return

        rate = self.total * self.window_size / self.n_windows
        if not self.triggered and rate >= self.threshold:
            self.triggered = True
            self.triggered_at = self.head
            self.triggered_rate = rate
            return self.ALERT_START

        elif self.triggered and rate < self.threshold:
            self.triggered = False
            self.triggered_at = self.head
            self.triggered_rate = rate
            return self.ALERT_STOP


class TaggedCounterMetric(SlidingWindowBase):
    """
    A sliding window that uses a collections.Counter object to accumulate the
    number of points in each time increment. This allows ``tags`` to be
    associated with events, with counts being tracked separately for each tag.
    """

    datatype = Counter

    def add_point(self, tags=None):
        tags = tags or []
        for tag in tags:
            self.buffer[tag] += 1

        # None is a special tag that holds the combined total for all points
        self.buffer[None] += 1
