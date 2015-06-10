import sys
sys.path.insert(0, '..')
sys.path.insert(0, '../../textmodel')

from textmodel import TextModel
from wxtextview import WXTextView

import wx


model = TextModel(u'Hello World!')
model.set_properties(6, 11, fontsize=14)
model.set_properties(6, 11, bgcolor='yellow')

app = wx.App()
frame = wx.Frame(None)
view = WXTextView(frame, -1)
view.model = model

view.index = 5
view.selection = 0, 5

frame.Show()
app.MainLoop()
