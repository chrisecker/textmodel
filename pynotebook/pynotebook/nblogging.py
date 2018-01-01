# -*- coding: latin-1 -*-

# Simple logging facility. It allows to record and replay everything
# the user enters. Logging is ment for debugging. It will be removed
# once all errors are fixed :-)

import os
from tempfile import mkdtemp

_buffer = []

def log(object, descr, *args):
    # Log a change of an object. 
    _buffer.append((object, descr)+args)


def logged(f):
    def new_f(self, *args, **kwds):
        log(self, f.__name__, args, kwds)
        return f(self, *args)
    return new_f


def get_log(object):
    for l in _buffer:
        if l[0] is object:
            yield l


def write_log(filename, object):
    import cPickle
    f = open(filename, 'wb')
    l = list(get_log(object))
    cPickle.dump(l, f)
    

def load_log(filename):
    import cPickle
    return cPickle.load(open(filename, 'rb'))
    

class TemporaryDirectory(object):
    # http://stackoverflow.com/questions/19296146/tempfile-temporarydirectory-
    # context-manager-in-python-2-7
    def __init__(self, suffix="", prefix="tmp", dir=None):
        self._closed = False
        self.name = mkdtemp(suffix, prefix, dir)

    def cleanup(self):
        if self.name and not self._closed:
            try:
                self._rmtree(self.name)
            except (TypeError, AttributeError) as ex:
                return
            self._closed = True

    def __del__(self):
        self.cleanup()

    _listdir = staticmethod(os.listdir)
    _path_join = staticmethod(os.path.join)
    _isdir = staticmethod(os.path.isdir)
    _islink = staticmethod(os.path.islink)
    _remove = staticmethod(os.remove)
    _rmdir = staticmethod(os.rmdir)

    def _rmtree(self, path):
        for name in self._listdir(path):
            fullname = self._path_join(path, name)
            try:
                isdir = self._isdir(fullname) and not self._islink(fullname)
            except OSError:
                isdir = False
            if isdir:
                self._rmtree(fullname)
            else:
                try:
                    self._remove(fullname)
                except OSError:
                    pass
        try:
            self._rmdir(path)
        except OSError:
            pass


def gen_logfile(path, ext):
    files = os.listdir(path)
    i = 0
    while 1:
        name = '%.4i.%s' % (i, ext)
        if not name in files:
            return os.path.join(path, name)
        i += 1
