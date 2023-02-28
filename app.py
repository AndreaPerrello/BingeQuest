import pathlib

from iotech.microservice import startup

# Create the cache folder
pathlib.Path('.mycache').mkdir(parents=True, exist_ok=True)
# Create the app
app = startup.create_app('config', 'application.ini', ["core", "controller", "Controller"])

if __name__ == '__main__':
    startup.run_app(app)
