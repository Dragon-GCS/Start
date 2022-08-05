import colorama


RESET = colorama.Style.RESET_ALL

class Color(str):
    color: str
    def __init__(self, msg: str):
        self.msg = msg.strip(RESET).replace(RESET, RESET + self.color)

    def __str__(self) -> str:
        return f"{self.color}{self.msg}{RESET}"

    def __add__(self, other: str) -> str:
        return f"{self}{other}"

    def __radd__(self, other: str) -> str:
        return f"{other}{self}"


class Green(Color):
    color: str = colorama.Fore.GREEN


class Red(Color):
    color: str = colorama.Fore.RED


class Yellow(Color):
    color: str = colorama.Fore.YELLOW

class Blue(Color):
    color: str = colorama.Fore.BLUE


class Magenta(Color):
    color: str = colorama.Fore.MAGENTA

class Cyan(Color):
    color: str = colorama.Fore.CYAN