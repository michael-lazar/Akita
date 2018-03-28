import os

import pytest

from akita.parser import HTTPLogParser


LOG_FILE = os.path.join(os.path.dirname(__file__), 'data', 'apache.log')

# http://publib.boulder.ibm.com/tividd/td/ITWSA/ITWSA_info45/en_US/HTML/guide/c-logs.html#common
LINE = '125.125.125.125 - dsmith [10/Oct/1999:21:15:05 +0500] "GET /index.html HTTP/1.0" 200 104'


@pytest.fixture()
def parser():
    return HTTPLogParser()


def test_parse_log_file(parser):
    with open(LOG_FILE) as fp:
        for line in fp:
            assert parser.parse(line)


def test_parse_common_log_format(parser):
    data = parser.parse(LINE)
    assert data['raw'] == LINE
    assert data['host'] == '125.125.125.125'
    assert data['user'] == 'dsmith'
    assert data['time'] == '10/Oct/1999:21:15:05 +0500'
    assert data['request'] == 'GET /index.html HTTP/1.0'
    assert data['status'] == '200'
    assert data['size'] == '104'
    assert data['method'] == 'GET'
    assert data['path'] == '/index.html'
    assert data['subpath'] == 'index.html'
    assert data['version'] == 'HTTP/1.0'
    assert data['timestamp'] == 939572105

    assert data['referrer'] is None
    assert data['agent'] is None
    assert data['cookies'] is None


def test_parse_combined_log_format(parser):
    line = LINE + ' "http://www.ibm.com/"'
    data = parser.parse(line)
    assert data['referrer'] == 'http://www.ibm.com/'
    assert data['agent'] is None
    assert data['cookies'] is None

    line += ' "Mozilla/4.05 [en] (WinNT; I)"'
    data = parser.parse(line)
    assert data['referrer'] == 'http://www.ibm.com/'
    assert data['agent'] == 'Mozilla/4.05 [en] (WinNT; I)'
    assert data['cookies'] is None

    line += ' "USERID=CustomerA;IMPID=01234"'
    data = parser.parse(line)
    assert data['referrer'] == 'http://www.ibm.com/'
    assert data['agent'] == 'Mozilla/4.05 [en] (WinNT; I)'
    assert data['cookies'] == 'USERID=CustomerA;IMPID=01234'
