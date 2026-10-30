"""Bounded local metadata reads; never wait for a FIFO writer or follow a leaf symlink."""
import os
import stat


def read_bytes(path, limit):
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise OSError('Evidence must be a regular file')
        return stream.read(limit + 1)  # Caller retains its existing oversize behavior.
