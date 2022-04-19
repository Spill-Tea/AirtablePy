"""
    AirtablePy/helpers.py

"""
# Python Dependencies
import pytest

from random import choices
from string import ascii_letters


# Global Variable
FAILURE = pytest.mark.xfail(raises=ValueError)


def random_key(length: int) -> str:
    return "".join(choices(ascii_letters, k=length))
