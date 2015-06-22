# Little benchmark utility for textmodel and textview
#
# usage: 
# - write a function to benchmark, e.g. test_00
# - call python runtest.py --profile demo/benchmark.py test_00

import sys
sys.path.insert(0, '..')
sys.path.insert(0, '../../textmodel')


from textmodel import TextModel
from wxtextview import WXTextView
import wx

text = None
def create_text():
    # Create a long text
    global text
    text = TextModel()
    for i in range(10000):
        text.append(TextModel("Line %i: test test test test\n" % i))


def colorize():
    colors = 'white', 'lightgrey'
    n = 21
    i1 = 0
    i2 = n
    while i2<len(text):
        text.set_properties(i1, i2, bgcolor=colors[i1%2])
        i1 = i2
        i2 += n

frame = None
app = None
def create_view():
    global frame
    global app

    app = wx.App(False)
    frame = wx.Frame(None)
    view = WXTextView(frame, -1)
    view.model = text


create_text()
colorize()


def test_00(): # 10.7s
    create_text()

def test_01(): # 0.3s !!!
    # alternative way to create text
    t = ''
    for i in range(10000):
        t += "Line %i: test test test test\n" % i
    TextModel(t)

def test_02(): # 13.7s
    colorize()

def test_03(): # 3.1s
    create_view()

def demo_00():
    create_text()
    colorize()
    create_view()
    frame.Show()
    app.MainLoop()

