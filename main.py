import pathlib
import argparse

from iotech.microservice import startup

# Create the cache folder
pathlib.Path('.mycache').mkdir(parents=True, exist_ok=True)
# Create the app
app = startup.cmd_create_app(["core", "controller", "Controller"])


if __name__ == '__main__':
    startup.run_app(app)
