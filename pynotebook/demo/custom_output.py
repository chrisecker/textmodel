# -*- coding: latin-1 -*-


import sys
sys.path.insert(0, '..')

from pynotebook.nbview import TextModel, NBView, ScriptingCell
from pynotebook.textformat import fromtext
import wx




examples = r"""[In 0]:
from pynotebook.nbtexels import BitmapRGB, BitmapRGBA

[In 1]:
def output(obj, iserr=False):
    if isinstance(obj, wx.Bitmap):
        im = obj.ConvertToImage()
        return __output__(
            BitmapRGBA(im.GetData(), im.GetAlphaData(), 
            im.GetSize()), iserr)
        
    return __output__(obj, iserr)
[In 2]:
import wx
bmp = wx.ArtProvider.GetBitmap(wx.ART_WARNING, size=(128, 128))

[In 3]:
bmp
"""

def demo_00():
    app = wx.App(redirect=False)
    model = fromtext(examples, ScriptingCell=ScriptingCell)

    frame = wx.Frame(None)
    win = wx.Panel(frame, -1)
    view = NBView(win, -1, style=wx.SUNKEN_BORDER)
    view.model = model
    box = wx.BoxSizer(wx.VERTICAL)
    box.Add(view, 1, wx.ALL|wx.GROW, 1)
    win.SetSizer(box)
    win.SetAutoLayout(True)

    frame.Show()

    if 0:
        from pynotebook.wxtextview import testing
        testing.pyshell(locals())
    app.MainLoop()


if __name__ == '__main__':
    demo_00()
