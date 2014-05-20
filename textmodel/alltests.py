# -*- coding: latin-1 -*-


# TODO:
# - Commandline-Argumente --silent, --redirect
# - Testen von Dateien

import sys
import types
import traceback
import StringIO
import inspect



def get_tb(skip=0):
    type, value, tb = sys.exc_info()
    entries = traceback.format_tb(tb)[skip:]
    msg = traceback.format_exc().splitlines()[-1]
    return ''.join(entries)+msg


class Tester:
    def __init__(self, silent=False, redirect=True):
        self.redirect = redirect
        self.silent = silent
        self.bkstdout = sys.stdout
        self.bkstderr = sys.stderr
        self.reset_buffer()

    def reset_buffer(self):
        self.stdoutbuffer = StringIO.StringIO()
        self.stderrbuffer = StringIO.StringIO()
        
    def redirect_io(self):
        #print "stdout:", sys.stdout
        assert sys.stdout is self.bkstdout
        assert sys.stderr is self.bkstderr
        sys.stdout = self.stdoutbuffer
        sys.stderr = self.stderrbuffer
        
    def restore_io(self):
        #assert sys.stdout is self.stdoutbuffer
        #assert sys.stderr is self.stderrbuffer
        sys.stdout = self.bkstdout
        sys.stderr = self.bkstderr
        #self.bkstdout.write("stdout: %s\n" % repr(sys.stdout))

    def test_callable(self, name, obj):
        doc = getattr(obj, '__doc__', '') or ''
        text = '> %s: %s' % (name, doc)
        text += '.'*(60-len(text))
        print text,
        if self.redirect:
            self.reset_buffer()
            self.redirect_io()        
        ok = True
        try:
            obj()
        except:
            ok = False
            tb = get_tb(1)
        finally:
            self.restore_io()
        if ok:
            print "ok"
            if not self.redirect:
                return
            if self.silent:
                return
            if self.stdoutbuffer.len:
                print "stdout:"
                print self.stdoutbuffer.getvalue()
            if self.stderrbuffer.len:
                print "stderr:"                
                print self.stderrbuffer.getvalue()
                
        else:
            if self.stdoutbuffer.len:
                print "stdout:"
                print self.stdoutbuffer.getvalue()
            if self.stderrbuffer.len:
                print "stderr:"                
                print self.stderrbuffer.getvalue()
            print "error"
            print tb
        return ok

    
def test_00():
    "output"
    print 123+432

def test_01():
    "exception"
    print 1/0

def _devel():
    tester = Tester()
    tester.test_callable("test_00", test_00)
    tester.test_callable("test_01", test_01)


def dotests(silent=False):
    """Kann aus Modulen aufgerufen werden. Durchsucht den aktuellen Namespace
nach test-objekten. Namen von testobjekten können als sys.argv übergeben 
werden. Ansonsten werden alle Objekte, deren Name mit 'test_'-anfängt getestet.
"""

    # Den Namespace des Aufrufers ermitteln
    stack = inspect.stack()
    frame, filename = stack[1][0:2]
    namespace = frame.f_locals

    if len(sys.argv) > 1:
        names = sys.argv[1:]
    else:
        names = []
        for name, obj in namespace.items():
            if name.startswith('test_') and callable(obj):
                names.append(name)
        names.sort()

        
    hashes = '#' * ((60-len(filename))/2)
    print " %s %s %s" % (hashes, filename, hashes)
    tester = Tester(silent=silent)
    n_ok = 0
    n = 0
    for name in names:
        obj = namespace[name]
        n += 1
        ok = tester.test_callable(name, obj)
        if ok:
            n_ok += 1
    print "Anzahl Tests:\t%i" % n
    print "Misslungen:\t%i" % (n-n_ok)
    

#_devel()
#dotests(silent=True)


