# -*- coding: latin-1 -*-

from .clients import Client, Aborted
from .nbstream import StreamRecorder
from pynotebook.textmodel.textmodel import TextModel
from pynotebook.textmodel.texeltree import Text, grouped, get_text, NL, length, dump, \
    iter_childs
from pynotebook.textmodel.styles import create_style

import sys
import traceback
import rlcompleter
import types
import token, tokenize, keyword
import io


debug = 0

def join(elements, sep):
    # helper
    if len(elements)>1:
        return [elements[0], sep] + join(elements[1:], sep)
    return list(elements)


def mk_breaklist(texel, i0=0):
    # helper
    if not texel.weights[2]: return ()
    if texel.is_group or texel.is_container:
        r = []
        for i1, i2, child in iter_childs(texel):
            r += mk_breaklist(child, i1+i0)
        return r
    return [i0+length(texel)]


def pycolorize(texel, styles=None, bgcolor='#FFFFFF'):
    model = TextModel()
    model.texel = grouped([texel, NL]) # the NL is needed by
                                       # tokenizer. We have to remove
                                       # it in the end
    position2index = model.position2index
    text = get_text(model.texel)
    instream = io.StringIO(text).readline

    _KEYWORD = token.NT_OFFSET + 1
    _TEXT    = token.NT_OFFSET + 2

    _colors = {
        token.NUMBER:       '#0080C0',
        token.OP:           '#0000C0',
        token.STRING:       '#004080',
        tokenize.COMMENT:   '#008000',
        token.NAME:         '#000000',
        token.ERRORTOKEN:   '#FF8080',
        _KEYWORD:           '#C00000',
        None:               '#000000', # everything else
        #_TEXT:              
    }

    if styles is not None:
        _styles = styles
    else:
        _styles = {}
        for key, fgcolor in _colors.items():
            _styles[key] = create_style(bgcolor=bgcolor, textcolor=fgcolor)

    class TokenEater:
        ai = 0
        breaks = [0]+mk_breaklist(model.texel)
        l = []
        def moveto(self, i, style=_styles[None]):
            # move index to $i$ and create texels the text between $ai$ and $i$
            ai = self.ai
            if i<ai: 
                raise IndexError
            if i == ai:
                return
            t = [Text(t, style) for t in text[ai:i].split('\n')]
            self.l.extend([x for x in join(t, NL) if length(x)])
            self.ai = i
            
        def __call__(self, toktype, toktext, (srow,scol), (erow,ecol), line):
            if token.LPAR <= toktype and toktype <= token.OP:
                toktype = token.OP
            elif toktype == token.NAME and keyword.iskeyword(toktext):
                toktype = _KEYWORD
                
            i1 = self.breaks[srow-1]+scol
            i2 = self.breaks[erow-1]+ecol
            if debug:
                assert i1 == position2index(srow-1, scol)
                assert i2 == position2index(erow-1, ecol)
            try:
                style = _styles[toktype]
            except:
                style = _styles[None]
            self.moveto(i1)
            self.moveto(i2, style=style)

    eater = TokenEater()
    try:
        tokenize.tokenize(instream, eater)
    except (tokenize.TokenError, IndentationError):
        pass

    eater.moveto(len(text))
    return grouped(eater.l[:-1]) # note that we are stripping of the last NL


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

    def _execute(self, text, output):
        # for debugging
        model = TextModel(text)
        self.execute(model.texel, output)

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

    def colorize(self, inputtexel, styles=None, bgcolor='white'):
        
        if 0:
            # The pycolorize function was ment for benchmarking the
            # textmodel. It is quite inefficient. Here, we should use
            # an optimized variant instead.
            text = get_text(inputtexel).encode('utf-8')
            from .textmodel.textmodel import pycolorize as _pycolorize
            try:
                colorized = _pycolorize(text, 'utf-8').texel
            except:
                return inputtexel
        else:
            colorized = pycolorize(inputtexel, styles=styles, bgcolor=bgcolor)
            
        try:
            assert length(colorized) == length(inputtexel)
        except:
            print "colorized:"
            dump(colorized)
            print "input"
            dump(inputtexel)
            return inputtexel
        return colorized




def test_00():
    "execute"
    client = PythonClient()
    assert 'output' in client.namespace

    stream = StreamRecorder()
    client._execute("12+2", stream.output)
    assert client.namespace['ans'] == 14
    assert stream.messages == [(14, False)]

    stream = StreamRecorder()
    client._execute("12+(", stream.output)
    assert 'SyntaxError' in str(stream.messages)
    assert client.namespace['ans'] == None

    stream = StreamRecorder()
    client._execute("asdasds", stream.output)
    assert stream.messages == [
        ('  File "In[3]", line 1, in <module>\n', True), 
        ("NameError: name 'asdasds' is not defined\n", True)]

    stream = StreamRecorder()
    client._execute("a=1", stream.output)
    assert client.namespace['ans'] == None
    assert stream.messages == []

    stream = StreamRecorder()
    client._execute("a", stream.output)
    assert client.namespace['ans'] == 1
    assert stream.messages == [(1, False)]

    stream = StreamRecorder()
    client._execute("a+1", stream.output)
    assert client.namespace['ans'] == 2
    assert stream.messages == [(2, False)]

    stream = StreamRecorder()
    client._execute("print a", stream.output)
    assert stream.messages == [('1', False), ('\n', False)]
    
def test_01():
    "complete"
    client = PythonClient()
    assert client.complete('a') == set(['abs', 'all', 'and', 'ans', 'any', 
                                        'apply', 'as', 'assert'])
    assert client.complete('ba') == set(['basestring'])
    assert client.complete('cl') == set(['classmethod', 'class'])
    assert client.complete('class') == set(['class', 'classmethod'])

def test_02():
    "abort"
    namespace = dict()
    client = PythonClient(namespace)
    stream = StreamRecorder()
    namespace['client'] = client
    client._execute("""
for i in range(10):
    print i
    if i>5:
        client.abort() # emulate a ctrl-c
    """, stream.output)
    assert 'Aborted' in str(stream.messages)
    
def test_03():
    "colorize"
    client = PythonClient()
    textmodel = TextModel("""
for i in range(10):
    print i""")
    client.colorize(textmodel.texel)


def test_04():
    "colorize (2)"
    client = PythonClient()    
    text = u"# Die Integralzeichen sind in vielen Unicode-Fonts enthalten. Z.B. "\
    u"FONTFAMILY_ROMAN. Sieht leider alles sehr ähnlich aus. Schöner ist z.B. wasy10. "\
    u"Der Font ist aber nicht auf allen Plattformen enthalten. Symbol dürfte enthalten"\
    u" sein, enthält aber nicht das Mittelstück.\n"
    u"# https://de.wikipedia.org/wiki/Integralzeichen  "
    textmodel = TextModel(text)
    client.colorize(textmodel.texel)

def test_05():
    "colorize (3)"
    from pynotebook.textmodel import textmodel
    text = open(textmodel.__file__.replace('.pyc', '.py')).read()
    textmodel = TextModel(text)
    client = PythonClient()    
    client.colorize(textmodel.texel)
    
def benchmark():
    from pynotebook.textmodel import texeltree
    text = open(texeltree.__file__.replace('.pyc', '.py')).read()
    textmodel = TextModel(text)
    client = PythonClient()    
    from cProfile import runctx 
    runctx("client.colorize(textmodel.texel)", globals(), locals())
