"""Lets you run the package with: python -m safety_eval ..."""

import sys

from safety_eval.cli import main

if __name__ == "__main__":
    sys.exit(main())
