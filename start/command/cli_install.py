from argparse import Namespace


def install(args: Namespace):
    print(args)


config = {
    "cfg": {
        "name": "install",
        "help": "Install packages, usage compatibility with 'pip install'",
    },
    "arguments": [
        {
            "flags": ("packages", ),
            "kwargs": {
                "help": "package name or url of git repository"
            }
        }
    ],
    "func": install
}
