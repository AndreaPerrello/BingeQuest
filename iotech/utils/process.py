import psutil


def is_running(process_name: str) -> bool:
    """
    Check if a process is running.
    :param process_name: Name of the process to check.
    :return: True if the process is running, False elsewhere.
    """
    for process in psutil.process_iter():
        if process.name() == process_name:
            return True
    return False


def kill(process_name: str):
    """
    Kill a process.
    :param process_name: Name of the process to kill.
    """
    for process in psutil.process_iter():
        if process.name() == process_name:
            process.kill()
