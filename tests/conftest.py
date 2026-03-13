import os
import sys


def _ensure_project_root_on_path() -> None:
    """
    Ensure the project root (containing the local `opt` package) is on sys.path.

    This makes imports like `from opt.torrent_bot ...` work both:
    - when running tests locally with just `pytest`,
    - and when running on the server, regardless of PYTHONPATH quirks.
    """

    # tests/ → project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if project_root not in sys.path:
        # Prepend so local code wins over any system-wide `opt` packages.
        sys.path.insert(0, project_root)


_ensure_project_root_on_path()

