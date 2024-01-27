import sys
import io
from contextlib import contextmanager
from start.logger import Color


@contextmanager
def capture_output():
    captured_output = io.StringIO()
    _stdout = sys.stdout
    _out = Color.out
    Color.out = captured_output
    sys.stdout = captured_output
    yield captured_output
    sys.stdout = _stdout
    Color.out = _out
