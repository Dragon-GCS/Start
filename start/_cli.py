from argparse import ArgumentParser


from .command import commands

def main():
    parser = ArgumentParser()
    subparser = parser.add_subparsers(title="Commands")
    for cmd in commands:
        command = subparser.add_parser(**cmd['cfg'])
        for arg in cmd["arguments"]:
            command.add_argument(*arg["flags"], **arg["kwargs"])
        command.set_defaults(func=cmd["func"])
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)

if __name__ == '__main__':
    main()