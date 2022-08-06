import colorama

RESET = colorama.Style.RESET_ALL

class Color(str):
    color: str
    def __init__(self, msg: str):
        self.msg = msg.strip(RESET).replace(RESET, RESET + self.color)
        print(self)

    def __str__(self) -> str:
        return f"{self.color}{self.msg}{RESET}"

    def __add__(self, other: str) -> str:
        return f"{self}{other}"

    def __radd__(self, other: str) -> str:
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