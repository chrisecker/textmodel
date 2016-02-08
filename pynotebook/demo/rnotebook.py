# -*- coding: latin-1 -*-

import sys
if __name__ == '__main__':
    sys.path.insert(0, '../../textmodel')
    sys.path.insert(0, '../../wxtextview')
    sys.path.insert(0, '..')

import rpy2.robjects as robjects
from pynotebook.clients import Client
from pynotebook.nbstream import StreamRecorder
from pynotebook.nbtexels import Cell as _Cell
from pynotebook.nbview import TextModel, WXTextView

import wx




class RClient(Client):
    name = "rpy2 r"
    def __init__(self):
        self.r = robjects.r

    def __del__(self):
        pass #self.kill()

    def execute(self, inputfield, output):
        return self.run(inputfield.get_text(), output)

    def run(self, code, output):
        # XXX MISSING: redirect sys.stderr
        self.counter += 1
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
    
    def abort(self):
        pass


class Cell(_Cell):
    client_name = RClient.name



def test_00():
    "send"
    interpreter = RClient()

    stream = StreamRecorder()
    interpreter.run('1+2', stream.output)
    len(stream.messages) == 1
    stream.messages[-1] == False # no Error


def demo_00():
    app = wx.App(redirect=False)
    model = TextModel('')

    frame = wx.Frame(None)
    win = wx.Panel(frame, -1)
    view = WXTextView(win, -1, style=wx.SUNKEN_BORDER)
    view.Cell = Cell
    view._clients.register(RClient())
    view.model = model
    box = wx.BoxSizer(wx.VERTICAL)
    box.Add(view, 1, wx.ALL|wx.GROW, 1)
    win.SetSizer(box)
    win.SetAutoLayout(True)

    frame.Show()

    if 0:
        from wxtextview import testing
        testing.pyshell(locals())
    app.MainLoop()


if __name__ == '__main__':
    demo_00()

"""
numberWhite <- rhyper(30,4,5,3)
numberChipped <- rhyper(30,2,7,3)
smoothScatter(numberWhite,numberChipped,
             xlab="White Marbles",ylab="Chipped Marbles",main="Drawing Marbles")
"""
