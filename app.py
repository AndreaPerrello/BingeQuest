import pathlib

from iotech.microservice import startup


if __name__ == '__main__':
    # Create the cache folder
    pathlib.Path('.mycache').mkdir(parents=True, exist_ok=True)
    # Create the app
    app = startup.cmd_create_app(["core", "controller", "Controller"])
    startup.run_app(app)
