# -*- coding: latin-1 -*-

"""
A simple notebook for the r language. Uses rpy2 for interfacing and 
pygments for colorization. 
"""

import sys
if __name__ == '__main__':
    sys.path.insert(0, '..')

from pynotebook.clients import Client
from pynotebook.pyclient import FakeFile
from pynotebook.nbstream import StreamRecorder
from pynotebook.nbtexels import ScriptingCell as _ScriptingCell
from pynotebook.nbview import TextModel, NBView
from pynotebook.textformat import fromtext
from pynotebook.textmodel import TextModel
from pynotebook.textmodel.texeltree import get_text, length

import wx

# we use rpy2 
import rpy2.robjects as robjects

# and pygments
from pygments.lexers import SLexer
from pygments.formatter import Formatter
from pygments import token as Token
from pygments import highlight

class TexelFormatter(Formatter):
    encoding = 'utf-8'
    def __init__(self, bgcolor):
        self.bgcolor = bgcolor

    def format(self, tokensource, outfile): 
        bgcolor = self.bgcolor
        self.model = model = TextModel()
        for token, text in tokensource:
            if token is Token.Keyword:
                style = dict(textcolor='red')
            elif token is Token.Literal.Number:
                style = dict(textcolor='blue')
            elif token is Token.Comment.Single:
                style = dict(textcolor='grey')
            elif token is Token.Text:
                style = dict(textcolor='black')
            elif token is Token.Literal.String:
                style = dict(textcolor='red')                    
            else:
                style = dict()
            style['bgcolor'] = bgcolor
            new = TextModel(text, **style)
            model.append(new)



class RClient(Client):
    name = "rpy2 r"
    def __init__(self):
        self.r = robjects.r

    def execute(self, inputfield, output):
        return self.run(get_text(inputfield), output)

    def run(self, code, output):
        self.counter += 1
        bkstdout, bkstderr = sys.stdout, sys.stderr
        sys.stdout = FakeFile(output)
        sys.stderr = FakeFile(lambda s: output(s, iserr=True))

        try:
            try:
                result = self.r(code)
            except ValueError, e:
                output(e, True)
            except Exception, e:
                output(e, True)
            else:
                output(result)
        except Exception, e:
            output(repr(e), True)
        finally:
            sys.stdout, sys.stderr = bkstdout, bkstderr
            sys.settrace(None)
    
    def complete(self, word, nmax=None):
        import rpy2.robjects 
        ri = rpy2.robjects.rinterface
        options = set()
        for env in (ri.baseenv, ri.globalenv): # XXX are there more envireonments??
            for name in env:
                if name.startswith(word):
                    options.add(name)
            if len(options) == nmax:
                break
        return options

    def colorize(self, inputtexel, styles=None, bgcolor='white'):
        text = get_text(inputtexel)
        assert len(text) == length(inputtexel)
        formatter = TexelFormatter(bgcolor)
        highlight(text, SLexer(), formatter)
        model = formatter.model
        while len(model) < length(inputtexel):
            # XXX when does this happen? What does it mean?
            model.insert_text(len(model), '\n')
        model = formatter.model[0:length(inputtexel)]
        assert len(model) == length(inputtexel)
        return model.texel




class ScriptingCell(_ScriptingCell):
    client_name = RClient.name



def test_00():
    "send"
    interpreter = RClient()

    stream = StreamRecorder()
    interpreter.run('1+2', stream.output)
    len(stream.messages) == 1
    stream.messages[-1] == False # no Error


examples = """[In 1]:
# Some R-Code

x <- c(1,2,3,4,5,6)   # Create ordered collection (vector)
y <- x^2              # Square the elements of x
print(y)              # print (vector) y
[In 0]:
# A simple plot 

plot(x, y)
[In 0]:
# A nice plot

numberWhite <- rhyper(30,4,5,3)
numberChipped <- rhyper(30,2,7,3)
smoothScatter(
    numberWhite,numberChipped,
    xlab="White Marbles",ylab="Chipped Marbles",
    main="Drawing Marbles")
"""

def demo_00():
    app = wx.App(redirect=False)
    model = fromtext(examples, ScriptingCell=ScriptingCell)

    frame = wx.Frame(None)
    win = wx.Panel(frame)
    view = NBView(win)
    view.ScriptingCell = ScriptingCell
    view._clients.register(RClient())
    view.model = model
    box = wx.BoxSizer(wx.VERTICAL)
    box.Add(view, 1, wx.ALL|wx.GROW, 1)
    win.SetSizer(box)
    win.SetAutoLayout(True)

    frame.Show()
    app.MainLoop()


if __name__ == '__main__':
    demo_00()

