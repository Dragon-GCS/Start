import colorama

from typing import Union

RESET = colorama.Style.RESET_ALL


class Color:

    color: str

    def __init__(self, msg: str, display: bool = True):
        self.msg = msg.removesuffix(RESET).replace(RESET, RESET + self.color)
        if display:
            print(self)

    def __str__(self) -> str:
        return f"{self.color}{self.msg}{RESET}"

    def __add__(self, other: Union[str, "Color"]) -> str:
        return f"{self}{other}"

    def __radd__(self, other: Union[str, "Color"]) -> str:
        return f"{other}{self}"


class Success(Color):
    color: str = colorama.Fore.GREEN


class Error(Color):
    color: str = colorama.Fore.RED


class Detail(Color):
    color: str = colorama.Fore.YELLOW


class Warn(Color):
    color: str = colorama.Fore.BLUE


class Prompt(Color):
    color: str = colorama.Fore.MAGENTA


class Info(Color):
    color: str = colorama.Fore.CYAN
