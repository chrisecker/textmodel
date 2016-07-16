# -*- coding: latin-1 -*-

from .clients import Client, Aborted
from .nbstream import StreamRecorder
from .textmodel.texeltree import get_text, length

import sys
import traceback
import rlcompleter
import types



class FakeFile:
    encoding = 'UTF-8'
    def __init__(self, fun):
        self.fun = fun

    def write(self, s):
        self.fun(s)



class PythonClient(Client):
    name = 'direct python'
    can_abort = True
    aborted = False

    def __init__(self, namespace=None):
        if namespace is None:
            namespace = {}
        self.namespace = namespace
        self.init()

    def init(self):
        source = """
from pynotebook import nbtexels


def has_classname(obj, classname):
    "returns True if $obj$ is an instance of a class with name $classname$"
    s = "<class '%s'>" % classname
    try:
        return str(obj.__class__) == s
    except AttributeError:
        return False

def output(obj, iserr=False):
    __output__(__transform__(obj, iserr), iserr)

def __transform__(obj, iserr):
    if has_classname(obj, "matplotlib.figure.Figure"):
        obj.canvas.draw()
        data = obj.canvas.tostring_rgb()
        size = obj.canvas.get_width_height()
        return nbtexels.BitmapRGB(data, size)
        
    return obj
        """
        code = compile(source, "init", 'exec')
        ans = eval(code, self.namespace)
        self.namespace["ans"] = ans
        
    def abort(self):
        self.aborted = True

    def trace_fun(self, *args):
        if self.aborted:
            self.aborted = False
            raise Aborted()

    def execute(self, inputfield, output):
        source = get_text(inputfield)
        self.namespace['__output__'] = output
        self.counter += 1
        name = 'In[%s]' % self.counter
        bkstdout, bkstderr = sys.stdout, sys.stderr
        stdout = sys.stdout = FakeFile(lambda s:self.namespace['output'](s))
        stderr = sys.stderr = FakeFile(lambda s:self.namespace['output'](s, iserr=True))
        self.ok = False
        self.expression = False
        try:
            try:
                try:
                    code = compile(source, name, 'eval')
                    self.expression = True
                except SyntaxError:
                    sys.settrace(self.trace_fun)
                    code = compile(source, name, 'exec')
                ans = eval(code, self.namespace)
                self.namespace['ans'] = ans
                self.ok = True
            except Exception, e:
                self.show_traceback(name)
                self.namespace['ans'] = None
            if self.expression and self.ok:
                ans = self.namespace['ans']
                # Note that we do not output the repr() of ans but ans
                # itself. This allow us to do substitutions,
                # e.g. replace matplotlib figures by their graphical
                # representation.
                try:
                    self.namespace['output'](ans)
                except Exception, e:
                    self.show_traceback(name)
        finally:
            sys.stdout, sys.stderr = bkstdout, bkstderr
            sys.settrace(None)

    def show_syntaxerror(self, filename):
        # stolen from "idle" by  G. v. Rossum
        type, value, sys.last_traceback = sys.exc_info()
        sys.last_type = type
        sys.last_value = value
        if filename and type is SyntaxError:
            # Work hard to stuff the correct filename in the exception
            try:
                msg, (dummy_filename, lineno, offset, line) = value
            except:
                # Not the format we expect; leave it alone
                pass
            else:
                # Stuff in the right filename
                try:
                    # Assume SyntaxError is a class exception
                    value = SyntaxError(msg, (filename, lineno, offset, line))
                except:
                    # If that failed, assume SyntaxError is a string
                    value = msg, (filename, lineno, offset, line)

        info = traceback.format_exception_only(type, value)
        sys.stderr.write(''.join(info))

    def show_traceback(self, filename):
        if type(sys.exc_value) == types.InstanceType:
            args = sys.exc_value.args
        else:
            args = sys.exc_value

        traceback.print_tb(sys.exc_traceback.tb_next, None)
        self.show_syntaxerror(filename)  

    def complete(self, word, nmax=None):
        completer = rlcompleter.Completer(self.namespace)
        options = set()
        i = 0
        while True:
            option = completer.complete(word, i)
            i += 1
            if option is None or len(options) == nmax:
                break
            option = option.replace('(', '') # I don't like the bracket
            options.add(option)
        return options

    def colorize(self, inputtexel):
        text = get_text(inputtexel)

        # XXX The pycolorize function was only ment for benchmarking
        # the textmodel. Here, we should use an optimized variant
        # instead.
        from .textmodel.textmodel import pycolorize
        try:
            colorized = pycolorize(text).texel
        except Exception, e:
            return inputtexel
        assert length(colorized) == length(inputtexel)
        return colorized


def test_00():
    "execute"
    client = PythonClient()
    assert 'output' in client.namespace

    stream = StreamRecorder()
    client.execute("12+2", stream.output)
    assert client.namespace['ans'] == 14
    assert stream.messages == [(14, False)]

    stream = StreamRecorder()
    client.execute("12+(", stream.output)
    assert 'SyntaxError' in str(stream.messages)
    assert client.namespace['ans'] == None

    stream = StreamRecorder()
    client.execute("asdasds", stream.output)
    assert stream.messages == [
        ('  File "In[3]", line 1, in <module>\n', True), 
        ("NameError: name 'asdasds' is not defined\n", True)]

    stream = StreamRecorder()
    client.execute("a=1", stream.output)
    assert client.namespace['ans'] == None
    assert stream.messages == []

    stream = StreamRecorder()
    client.execute("a", stream.output)
    assert client.namespace['ans'] == 1
    assert stream.messages == [(1, False)]

    stream = StreamRecorder()
    client.execute("a+1", stream.output)
    assert client.namespace['ans'] == 2
    assert stream.messages == [(2, False)]

    stream = StreamRecorder()
    client.execute("print a", stream.output)
    assert stream.messages == [('1', False), ('\n', False)]
    
def test_01():
    "complete"
    client = PythonClient()
    assert client.complete('a') == ('abs(', 'all(', 'and', 'ans', 'any(', 
                                    'apply(', 'as', 'assert')
    assert client.complete('ba') == ('basestring(',)
    assert client.complete('cl') == ('class',)
    assert client.complete('class') == ('class', 'classmethod(')

def test_02():
    "abort"
    namespace = dict()
    client = PythonClient(namespace)
    stream = StreamRecorder()
    namespace['client'] = client
    client.execute("""
for i in range(10):
    print i
    if i>5:
        client.abort() # emulate a ctrl-c
    """, stream.output)
    assert 'Aborted' in str(stream.messages)
    
