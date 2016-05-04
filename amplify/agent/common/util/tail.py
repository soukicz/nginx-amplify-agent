# -*- coding: utf-8 -*-
from os import stat

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev"]
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


# this one is used to store offset between objects' reloads
OFFSET_CACHE = {}


class FileTail(object):
    """
    Creates an iterable object that returns only unread lines.

    Based on some code of Pygtail
    pygtail - a python "port" of logtail2
    Copyright (C) 2011 Brad Greenlee <brad@footle.org>

    https://raw.githubusercontent.com/bgreenlee/pygtail/master/pygtail/core.py
    """

    def __init__(self, filename):
        self.filename = filename
        self._fh = None

        # open a file and seek to the end
        if self.filename not in OFFSET_CACHE:
            with open(self.filename, "r") as f:
                f.seek(0, 2)
                self._offset = OFFSET_CACHE[self.filename] = f.tell()
        else:
            self._offset = OFFSET_CACHE[self.filename]

        # save inode to determine rotations
        self._inode = stat(self.filename).st_ino

    def __del__(self):
        if self._filehandle():
            self._filehandle().close()

    def __iter__(self):
        return self

    def next(self):
        """
        Return the next line in the file, updating the offset.
        """
        try:
            line = self._get_next_line()
        except StopIteration:
            # we've reached the end of the file;
            self._update_offset()
            raise
        return line

    def _file_was_rotated(self):
        """
        Checks that file was rotated
        :return: bool
        """
        # wait for new file
        new_inode = self._inode
        while True:
            try:
                new_inode = stat(self.filename).st_ino
            except:
                pass
            else:
                break
        return new_inode != self._inode

    def __next__(self):
        """`__next__` is the Python 3 version of `next`"""
        return self.next()

    def readlines(self):
        """
        Read in all unread lines and return them as a list.
        """
        return [line for line in self]

    def _is_closed(self):
        if not self._fh:
            return True
        return self._fh.closed

    def _filehandle(self):
        """
        Return a filehandle to the file being tailed, with the position set
        to the current offset.
        """
        file_was_rotated = self._file_was_rotated()

        if not self._fh or self._is_closed() or file_was_rotated:
            if not self._is_closed():
                self._fh.close()

            if file_was_rotated:
                self._inode = stat(self.filename).st_ino
                self._offset = OFFSET_CACHE[self.filename] = 0

            self._fh = open(self.filename, "r")
            self._fh.seek(self._offset)
        return self._fh

    def _update_offset(self):
        self._offset = OFFSET_CACHE[self.filename] = self._filehandle().tell()

    def _get_next_line(self):
        line = self._filehandle().readline()
        self._update_offset()
        if not line:
            raise StopIteration
        return line.rstrip()
