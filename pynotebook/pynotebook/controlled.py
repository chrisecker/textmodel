# log method calls which lead to exceptions

import os
import sys
import traceback
import cPickle
from tempfile import mkdtemp

bk_stderr = sys.stderr

def store_exception(obj, name, args, kwds):
    dirname = mkdtemp(prefix="pnb_tmp")
    tb = traceback.format_exc()
    f = open(os.path.join(dirname, 'exception.txt'), 'wb')
    print >>f, tb
    f = open(os.path.join(dirname, 'call.pickle'), 'wb')
    l = (obj, name, args, kwds)
    cPickle.dump(l, f)
    print >>bk_stderr, tb
    print >>bk_stderr, "Stored details to file %s" % repr(dirname)


    
def controlled(f):
    def new_f(self, *args, **kwds):
        try:
            return f(self, *args, **kwds)
        except:
            store_exception(self.model, f.__name__, args, kwds)
            raise
    return new_f





