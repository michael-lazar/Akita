import sys

if sys.version_info < (3, 4):
    sys.exit('Akita requires Python 3.4+')

from .akita import main

sys.exit(main())
