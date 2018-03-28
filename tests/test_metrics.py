from collections import Counter

from akita.metrics import CounterMetric, TaggedCounterMetric, AlertMetric


def test_counter_metric():

    metric = CounterMetric(window_size=2, n_windows=5)
    assert len(metric.history) == 5
    assert metric.total == 0
    assert metric.min is None
    assert metric.max is None

    metric.flush(timestamp=0)
    assert metric.history == [0, 0, 0, 0, 0]

    metric.add_point()
    metric.flush(timestamp=2.1)
    assert metric.history == [1, 0, 0, 0, 0]

    metric.add_point()
    metric.flush(timestamp=3.4)
    assert metric.history == [1, 0, 0, 0, 0]

    metric.flush(timestamp=4.9)
    assert metric.history == [1, 1, 0, 0, 0]

    metric.flush(timestamp=6.0)
    assert metric.history == [0, 1, 1, 0, 0]

    metric.add_point()
    metric.add_point()
    metric.add_point()
    metric.flush(timestamp=12.3)
    assert metric.history == [0, 0, 3, 0, 1]

    assert metric.total == 4
    assert metric.min == 0
    assert metric.max == 3


def test_tagged_counter_metric():

    metric = TaggedCounterMetric(window_size=2, n_windows=5)
    assert len(metric.history) == 5
    assert sum(metric.total.values()) == 0

    metric.flush(timestamp=0)
    assert metric.total == Counter()

    metric.add_point(tags=['foo', 'bar'])
    metric.flush(timestamp=2.1)
    assert metric.history[0] == Counter({'foo': 1, 'bar': 1, None: 1})

    metric.add_point(tags=['foo'])
    metric.flush(timestamp=4.0)
    assert metric.history[0] == Counter({'foo': 1, None: 1})

    metric.add_point()
    metric.add_point(tags=['bar'])
    metric.add_point(tags=['buzz'])
    metric.flush(timestamp=6.3)
    assert metric.history[0] == Counter({'bar': 1, 'buzz': 1, None: 3})

    assert metric.total == Counter({'foo': 2, 'bar': 2, 'buzz': 1, None: 5})


def test_alert_metric():

    metric = AlertMetric(window_size=1, n_windows=20, threshold=5)

    alert = metric.flush(timestamp=0)
    assert alert is None

    # 20 points / 20 windows = 1/sec average
    for _ in range(20):
        metric.add_point()
    alert = metric.flush(timestamp=2)
    assert alert is None

    alert = metric.flush(timestamp=6)
    assert alert is None

    # (80 + 20) points / 20 windows = 5/sec average
    # Average is above threshold, so the next flush() should trigger an alert
    for _ in range(80):
        metric.add_point()
    alert = metric.flush(timestamp=8.4)
    assert alert == metric.ALERT_START
    assert metric.triggered
    assert metric.triggered_at == 8
    assert metric.triggered_rate == 5

    # Even though the original 20 points have been removed from the total,
    # it hasn't been 20s since the original alert, so the STOP event won't
    # be triggered yet.
    alert = metric.flush(timestamp=22)
    assert alert is None
    assert metric.total == 80

    # Now it has been 20+ seconds, so the STOP event is triggered
    alert = metric.flush(timestamp=28)
    assert alert == metric.ALERT_STOP
    assert not metric.triggered
    assert metric.triggered_at == 28
