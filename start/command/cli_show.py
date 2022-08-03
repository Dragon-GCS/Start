from argparse import Namespace


def show(args: Namespace):
    print(args)


config = {
    "cfg": {
        "name": "show",
        "help": "",
    },
    "arguments": [],
    "func": show
}
