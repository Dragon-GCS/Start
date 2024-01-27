import sys
from typing import TextIO, Union

import colorama

RESET = colorama.Style.RESET_ALL


class Color:
    """An wrapper class for colorama that allows for easy colorization of text."""

    color: str
    out: TextIO = sys.stdout

    def __init__(self, msg: Union[str, "Color"], display: bool = True):
        # remove the reset code from the end of the message
        # add color code after each reset code in the message
        self.msg = str(msg).removesuffix(RESET).replace(RESET, RESET + self.color)
        if display:
            print(self, file=self.out)

    def __repr__(self) -> str:
        return f"{self.color}{self.msg}{RESET}"

    def __add__(self, other: Union[str, "Color"]) -> str:
        return f"{self}{other}"

    def __radd__(self, other: Union[str, "Color"]) -> str:
        return f"{other}{self}"


class Success(Color):
    color: str = colorama.Fore.GREEN


class Error(Color):
    color: str = colorama.Fore.RED
    out = sys.stderr


class Detail(Color):
    color: str = colorama.Fore.YELLOW


class Warn(Color):
    color: str = colorama.Fore.BLUE


class Prompt(Color):
    color: str = colorama.Fore.MAGENTA


class Info(Color):
    color: str = colorama.Fore.CYAN
