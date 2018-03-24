import sys
import time
import pprint

import apache_log_parser
from datadog import ThreadStats
from datadog.threadstats.reporters import Reporter


class LocalReporter(Reporter):

    def flush_metrics(self, metrics):
        print(metrics)

    def flush_events(self, events):
        print(events)


class LocalThreadStats(ThreadStats):
    """
    The Data Dog ThreadStats class is hardcoded to broadcast events to a
    remote server like Statsd. In our case, we only want the data locally
    so we can display it on the console.
    """

    def start(self, *args, **kwargs):
        out = super().start(*args, **kwargs)
        self.reporter = LocalReporter()
        return out


stats = LocalThreadStats()
stats.start(flush_interval=1, roll_up_interval=1)
stats.increment('foo.bar')
time.sleep(5)

sys.exit(0)


# Using the W3C Common Log Format (https://en.wikipedia.org/wiki/Common_Log_Format)
# Also see https://httpd.apache.org/docs/2.4/logs.html
# TODO: compare with https://github.com/kevinsimard/http-monitoring-console/blob/master/src/monitoring/parser.py
line_parser = apache_log_parser.Parser('%h %l %u %t "%r" %>s %b')

# TODO: read unicode of bytes?
with open('/tmp/apache.log', 'r') as fp:
    fp.seek(0, 2)

    while True:
        line = fp.readline().strip()
        print(line)

        if not line:
            time.sleep(0.25)
            continue

        try:
            pprint.pprint(line_parser.parse(line))
        except Exception as e:
            print(e)

        print('')
