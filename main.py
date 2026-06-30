"""Compatibility launcher for the Swiss SIA Compliance Checker.

The production implementation lives in :mod:`swiss_sia.app`. This wrapper is
kept at the repository root so existing VE script shortcuts and manual runs keep
working.
"""

from swiss_sia.app import main


if __name__ == "__main__":
    main()

