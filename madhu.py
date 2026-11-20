"""Start Madhu: python madhu.py"""

import sys

if sys.version_info < (3, 10):
    sys.exit("Madhu needs Python 3.10 or newer. You have " + sys.version.split()[0] + ". Install a newer Python, then try again.")

from madhukit.cli import main  # noqa: E402

raise SystemExit(main())
