# colorize demo

import sys
sys.path.insert(0, '..')
sys.path.insert(0, '../../textmodel')

from textmodel import TextModel
from wxtextview import WXTextView


import wx

app = wx.App(redirect = False)
frame = wx.Frame(None)
win = wx.Panel(frame, -1)
view = WXTextView(win, -1, style=wx.SUNKEN_BORDER)
box = wx.BoxSizer(wx.VERTICAL)
box.Add(view, 1, wx.ALL|wx.GROW, 1)
win.SetSizer(box)
win.SetAutoLayout(True)

from textmodel.textmodel import pycolorize
filename = '../wxtextview/textview.py'
rawtext = open(filename).read()
model = pycolorize(rawtext)
view.set_model(model)
frame.Show()
app.MainLoop()
