# -*- coding: latin-1 -*-

# Runs module tests. 
#
# python runtests.py texmtodel/base.py
#

# TODO:
# - Commandline arguments --silent, --redirect

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
    bkstdout = sys.stdout
    bkstderr = sys.stderr

    def __init__(self, silent=False, redirect=True, profile=False):
        self.redirect = redirect
        self.silent = silent
        self.profile = profile
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
        if self.profile:
            from cProfile import runctx
            try:
                runctx("obj()", globals(), locals())
            except:
                ok = False
                tb = get_tb(1)
            finally:
                self.restore_io()
        else:
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

    
def test_library(modulname, silent=False, profile=False, names=()):
    import importlib
    library = importlib.import_module(modulname)

    if not names:
        names = []
        for name in dir(library):
            obj = getattr(library, name)
            if name.startswith('test_') and callable(obj):
                names.append(name)
        names.sort()

        
    hashes = '#' * ((60-len(filename))/2)
    print " %s %s %s" % (hashes, filename, hashes)
    tester = Tester(silent=silent, profile=profile)
    n_ok = 0
    n = 0
    for name in names:
        obj = getattr(library, name)
        n += 1
        ok = tester.test_callable(name, obj)
        if ok:
            n_ok += 1
    print "Number of tests:\t%i" % n
    print "Tests failed:   \t%i" % (n-n_ok)


import sys

profile = False
silent = False

for name in sys.argv:
    if name == '--silent':
        silent = True
        sys.argv.remove(name)
    elif name == '--profile':
        profile = True
        sys.argv.remove(name)
        

import textmodel
print "path=", textmodel.__path__
name = sys.argv[1]
print name
if name.lower().endswith('.py'):
    name = name[:-3]
filename = name.replace('/', '.')
fun_names = sys.argv[2:]
print "testing:", filename
#print "testing functions:", fun_names
test_library(filename, names=fun_names, silent=silent, profile=profile)
    
