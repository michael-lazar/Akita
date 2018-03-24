import time
import pprint

import apache_log_parser

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
