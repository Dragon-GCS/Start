import sys
import io
from contextlib import contextmanager

@contextmanager
def capture_output():
    captured_output = io.StringIO()
    sys.stdout = captured_output
    yield captured_output
    sys.stdout = sys.__stdout__
