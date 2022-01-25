import os
import importlib


COMMANDS = {}
for filename in os.listdir(os.path.dirname(__file__)):
    if filename == '__init__.py' or filename[-3:] != '.py':
        continue
    cmd = filename[:-3]
    module = importlib.import_module("commands." + cmd)
    COMMANDS[cmd] = module.run
