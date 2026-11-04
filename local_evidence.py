"""Bounded local metadata reads; never wait for a FIFO writer or follow a leaf symlink."""
import json
import math
import os
import stat


def read_bytes(path, limit):
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise OSError('Evidence must be a regular file')
        return stream.read(limit + 1)  # Caller retains its existing oversize behavior.


def read_tail(path, limit):
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise OSError('Evidence must be a regular file')
        stream.seek(max(0, info.st_size - limit))
        return info.st_size, stream.read(limit)


def read_json(path, limit):
    raw = read_bytes(path, limit)
    if len(raw) > limit:
        raise ValueError('Evidence exceeds size limit')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON field')
            result[key] = value
        return result

    def reject(_):
        raise ValueError('Non-finite JSON number')

    def finite(value):
        result = float(value)
        if not math.isfinite(result):
            raise ValueError('JSON number overflow')
        return result

    return json.loads(raw, object_pairs_hook=unique, parse_constant=reject, parse_float=finite)
