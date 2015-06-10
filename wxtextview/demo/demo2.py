import sys
sys.path.insert(0, '..')
sys.path.insert(0, '../../textmodel')


from textmodel import TextModel
from wxtextview import WXTextView

import wx
app = wx.App()


model = TextModel(u'Hello World!')
model.set_properties(6, 11, fontsize=14)
model.set_properties(0, 11, bgcolor='yellow')

instructions = """

You can edit this text as you like. Undo
is ctrl-z and redo ctrl-r. The second
window displays exactly the same text and
follows the changes.

"""

model.insert(len(model), TextModel(instructions))

# display the texmodel in a view
frame = wx.Frame(None)
view = WXTextView(frame, -1)
view.model = model
frame.Show()

# set cursor and selection
view.index = 5
view.selection = 0, 5

# display the same textmodel in a second view
frame2 = wx.Frame(None)
view2 = WXTextView(frame2, -1)
view2.model = model
frame2.Show()

app.MainLoop()

