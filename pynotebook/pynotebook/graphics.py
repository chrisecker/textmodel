# -*- coding:utf-8 -*-

#
# graphics.py
#


import wx
from .nbtexels import Graphics



class RGBColor: # Mathematicy style
    def __init__(self, r, g, b):
        self.color = (r, g, b)
        
    def draw(self, gc, state):
        gc.SetPen(wx.Pen(colour=self.color))


class LineColor: # wx style
    def __init__(self, color):
        self.color = color
        
    def draw(self, gc, state):
        pen = state["pen"]
        pen.SetColour(self.color)
        gc.SetPen(pen)


class Width: # XXX or LineWidth?
    def __init__(self, width):
        self.width = width
        
    def draw(self, gc, state):
        pen = state["pen"]
        pen.SetWidth(self.width)
        gc.SetPen(pen)

        
class FillColor:
    def __init__(self, color):
        self.color = color
        
    def draw(self, gc, state):
        brush = state["brush"]
        brush.SetColour(self.color)
        gc.SetBrush(brush) 


class Dot:
    def __init__(self, (x, y)):
        self.x = x
        self.y = y

    def draw(self, gc, state):
        gc.DrawEllipse(self.x-5, self.y-5, 10, 10)


class Line:
    def __init__(self, *points):
        self.points = tuple(points)

    def draw(self, gc, state):
        gc.DrawLines(self.points)


class Circle:
    def __init__(self, (x, y), r):
        self.x = x
        self.y = y
        self.r = r
        
    def draw(self, gc, state):
        r = self.r
        gc.DrawEllipse(self.x-r, self.y-r, 2*r, 2*r)


class Rectangle:
    def __init__(self, (x1, y1), (x2, y2)):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        
    def draw(self, gc, state):
        x = min(self.x1, self.x2)
        w = max(self.x1, self.x2)-x
        y = min(self.y1, self.y2)
        h = max(self.y1, self.y2)-y        
        gc.DrawRectangle(x, y, w, h) 


class Bitmap:
    def __init__(self, data, size):
        self.data = data
        self.size = size

    def draw(self, gc, state):
        w, h = self.size
        bitmap = wx.BitmapFromBuffer(w, h, self.data)
        gc.DrawBitmap(bitmap, 0, 0, w, h)


class Text:
    regname = 'GraphicsText'
    def __init__(self, text, point, align=(0, 0)):
        self.text = text
        self.point = point
        self.align = align
        
    def draw(self, gc, state):
        x, y = self.point
        w, h = gc.GetTextExtent(self.text)
        dx = 0.5*w*(self.align[0]-1)
        dy = 0.5*h*(self.align[1]-1)
        gc.DrawText(self.text, x+dx, y+dy)


class Translate:
    def __init__(self, offset):
        self.offset = offset
        
    def draw(self, gc, state):
        dx, dy = self.offset
        gc.Translate(dx, dy)


class Rotate:
    def __init__(self, angle):
        self.angle = angle
        
    def draw(self, gc, state):
        gc.Rotate(self.angle) 


class Scale:
    def __init__(self, fx, fy=None):
        if fy is None:
            fy = fx
        self.fx = fx
        self.fy = fy
        
    def draw(self, gc, state):
        gc.Scale(self.fx, self.fy) 



def _unscale_widths(l):
    if isinstance(l, list) or isinstance(l, tuple):
        r = []
        for obj in l:
            if isinstance(obj, Scale):
                r.append(Width(1.0/obj.fx))
                r.append(obj)
            else:
                r.append(_unscale_widths(obj))
        return r
    return l

    
def Sketch(l, *args, **kwds): # XXX highly experimental
    return Graphics(_unscale_widths(l), *args, **kwds)


def register_classes():
    from cerealizerformat import register
    import types
    for name, value in globals().items():
        if type(value) is types.ClassType:
            if hasattr(value, 'regname'):
                register(value, classname=value.regname)
            else:
                register(value)


def init_testing(redirect=True):
    import wx
    from .nbview import TextModel, NBView
    app = wx.App(redirect=redirect)
    model = TextModel('')

    frame = wx.Frame(None)
    win = wx.Panel(frame, -1)
    view = NBView(win, -1, style=wx.SUNKEN_BORDER)
    view.model = model
    box = wx.BoxSizer(wx.VERTICAL)
    box.Add(view, 1, wx.ALL|wx.GROW, 1)
    win.SetSizer(box)
    win.SetAutoLayout(True)

    frame.Show()
    return locals()

def test_00():
    "Graphics"
    from .nbview import mk_textmodel
    ns = init_testing(False)
    model = ns['model']
    model.insert(len(model), mk_textmodel(Graphics([Dot(0, 0)])))
    segments = [
        (0, 0), (0, 10), (10, 10), (10, 0)
    ]
    l = Line(*segments)
    model.insert(len(model), mk_textmodel(Graphics([l])))
    return ns


    
def demo_00():
    import wx
    from .wxtextview import testing
    ns = test_00()
    testing.pyshell(ns)
    py = ns['view']._clients._clients['direct python']
    py.namespace.update(
        dict(Graphics=Graphics, Dot=Dot, Line=Line))
    ns['app'].MainLoop()





