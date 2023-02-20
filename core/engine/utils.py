import datetime


def multi_format_date(string: str):
    if not string:
        return
    try:
        return datetime.datetime.strptime(string, "%H:%M:%S")
    except:
        try:
            return datetime.datetime.strptime(string, "%M:%S")
        except:
            pass
