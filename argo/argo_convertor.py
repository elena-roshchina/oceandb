from datetime import datetime, date, time, timedelta, timezone


def read_strings_with_full_value(data, key):
    result = []
    n = data.dimensions['N_PROF'].size
    for i in range(0, n):
        res = ''
        for item in data.variables[key][i][:]:
            s = str(item)[2:3]
            if len(s) == 0:
                s = ' '
            res += s
        result.append(res)
    return result


def read_char_with_full_value(data, key):
    result = []
    n = data.dimensions['N_PROF'].size
    for i in range(0, n):
        s = str(data.variables[key][i])[2:3]
        result.append(s)
    return result


def read_datetime_with_full_value(data, key):
    result = ''
    for item in data.variables[key][:]:
        s = str(item)[2:3]
        result += s
    d = datetime(int(result[0:4]), int(result[4:6]), int(result[6:8]),
                 hour=int(result[8:10]), minute=int(result[10:12]), second=int(result[12:]),
                 tzinfo=timezone.utc)
    return d