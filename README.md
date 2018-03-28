<a href="https://pypi.python.org/pypi/akita/">
  <img alt="pypi" src="https://img.shields.io/pypi/v/akita.svg?label=version"/>
</a>
<a href="https://pypi.python.org/pypi/akita/">
  <img alt="python" src="https://img.shields.io/badge/python-3.4+-blue.svg"/>
</a>
<a href="https://travis-ci.org/michael-lazar/akita">
  <img alt="travis-ci" src="https://travis-ci.org/michael-lazar/Akita.svg?branch=master"/>
</a>

# Akita

An HTTP log monitoring tool for your terminal

## Installation

Akita is available on [PyPI](https://pypi.python.org/pypi/akita/) and can be installed using pip:

```bash
# Requires python 3!
pip install akita
```

Alternatively, you can clone the repository and run the code directly:

```bash
git clone https://github.com/michael-lazar/Akita.git
cd Akita
python -m akita
```

## Options

```
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

## License
This project is distributed under the [MIT](LICENSE) license.
