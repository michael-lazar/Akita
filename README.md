<a href="https://pypi.python.org/pypi/akita/">
  <img alt="pypi" src="https://img.shields.io/pypi/v/akita.svg?label=version"/>
</a>
<a href="https://pypi.python.org/pypi/akita/">
  <img alt="python" src="https://img.shields.io/badge/python-3.4+-blue.svg"/>
</a>
<a href="https://travis-ci.org/michael-lazar/Akita">
  <img alt="travis-ci" src="https://travis-ci.org/michael-lazar/Akita.svg?branch=master"/>
</a>

# Akita

<p align="center">
<img alt="Demo" src="resources/demo.gif"/>
</p>

*Akita* is a local HTTP log monitoring tool that runs in your terminal. With Akita, you can view a summary of you webserver's activity in real-time. All servers that utilize the [Common Log Format](https://en.wikipedia.org/wiki/Common_Log_Format) are supported, including Apache and Nginx.

*Akita* is also a [breed of dog](https://en.wikipedia.org/wiki/Akita_(dog)) originating from the mountainous northern regions of Japan. Akitas are powerful working dogs known for their fierce loyalty to their owners. They're fearless guard dogs who won't back down from a challenge.

<p align="center">
<img alt="Akita" src="resources/akita_1.jpg" width="667px"/>
</p>

## Installation

Akita is available on [PyPI](https://pypi.python.org/pypi/akita/) and can be installed using pip:

```bash
# Requires python 3!
$ pip install akita
```

Alternatively, you can clone the repository and run the code directly:

```bash
$ git clone https://github.com/michael-lazar/Akita.git
$ cd Akita
$ python -m akita
```

## Usage

If you want to try running Akita but you don't have a webserver to point it to, you can use the [apache-loggen](https://github.com/tamtam180/apache_log_gen) command line tool to generate fake log data.

```bash
$ gem install apache-loggen
$ apache-loggen --rate=10 | akita -
```

## Options

```bash
$ akita --help
usage: akita [--help] [--version] FILE

       / \      _-'
     _/|  \-''- _ /
__-' { |         \
    /             \
    /      "o.  |o }        Akita - Terminal HTTP Log Monitoring
    |            \ ;
                  ',
       \_         __\
         ''-_    \.//
           / '-____'
          /
        _'
      _-'

positional arguments:
  FILE                  A log file to watch, use "-" to pipe from stdin

optional arguments:
  -h, --help            show this help message and exit
  --alert-threshold ALERT_THRESHOLD
                        High traffic alert threshold, requests/second
  --alert-window ALERT_WINDOW
                        High traffic alert window, in seconds
  -V, --version         show program's version number and exit
```

## Testing

This repository is continuously tested on [TravisCI](https://travis-ci.org/michael-lazar/Akita), but you can also run the test suite locally:

```bash
$ git clone https://github.com/michael-lazar/Akita.git
$ cd Akita
$ pip install .[test]  # Installs pytest if you don't already have it
$ env PYTHONPATH=. py.test -v
```

## License
This project is distributed under the [MIT](LICENSE) license.
