# config.py
import os
import multiprocessing

host = "0.0.0.0"
port = 5050
workers = 2 * multiprocessing.cpu_count() + 1
log_level = "debug"
reload = not os.environ.get("PRODUCTION")
