import os
import importlib


def init(subparsers):
    commands = {}
    for module in os.listdir(os.path.dirname(__file__)):
        if module == '__init__.py' or module[-3:] != '.py':
            continue
        command_name = module[:-3]
        subparser = subparsers.add_parser(command_name)
        m = importlib.import_module("scripts." + command_name)
        m.init(subparser)
        commands[command_name] = m.run
    return commands
