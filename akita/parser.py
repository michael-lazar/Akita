import re
from datetime import datetime
from urllib.parse import urlparse


class HTTPLogParser:
    """
    Extracts information from HTTP log lines

    The log is assumed to be formatted according to the NCSA Combined
    Log format. This is compatible with the default Apache access logs
    and other popular HTTP servers

    References:
        https://en.wikipedia.org/wiki/Common_Log_Format
        https://gist.github.com/sumeetpareek/9644255
        https://github.com/rory/apache-log-parser
    """

    _parts = [
        r'(?P<host>\S+)',  # host %h
        r'\s+\S+',  # indent %l (unused)
        r'\s+(?P<user>\S+)',  # user %u
        r'\s+\[(?P<time>.+)\]',  # time %t
        r'\s+"(?P<request>.*)"',  # request "%r"
        r'\s+(?P<status>[0-9]+)',  # status %>s
        r'\s+(?P<size>\S+)',  # size %b (careful, can be '-')
        r'(\s+"(?P<referrer>.*?)")?',  # referrer "%{Referer}i"
        r'(\s+"(?P<agent>.*?)")?',  # user agent "%{User-agent}i"
        r'(\s+"(?P<cookies>.*?)")?',  # cookies "%{Cookies}i"
    ]
    pattern = re.compile(''.join(_parts) + r'\s*\Z')

    # [24/Mar/2018:23:05:09 -0400]
    date_fmt = "%d/%b/%Y:%H:%M:%S %z"

    @classmethod
    def parse(cls, line):
        data = cls.pattern.match(line).groupdict()
        data['raw'] = line

        # Convert some of the fields into native python objects
        request_parts = data['request'].split(' ')
        data['method'] = request_parts[0]
        data['path'] = request_parts[1]
        try:
            data['version'] = request_parts[2]
        except IndexError:
            data['version'] = 'HTTP/0.9'

        data['url_parts'] = urlparse(data['path'])
        data['subpath'] = data['url_parts'].path[1:].split('/')[0]

        data['datetime'] = datetime.strptime(data['time'], cls.date_fmt)
        data['timestamp'] = data['datetime'].timestamp()
        return data
